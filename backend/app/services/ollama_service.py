import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
# pyrefly: ignore [missing-import]
import httpx

from app.config import settings
from app.schemas.chat import ModelDetails

logger = logging.getLogger("ogcai.ollama_service")

class OllamaService:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.client: Optional[httpx.AsyncClient] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self.last_active_model: Optional[str] = None
        # Models >=16B (8.9GB+) exceed 4GB GPU VRAM + Windows page-locked CUDA_Host buffer limits
        self._unusable_models: set[str] = {"deepseek-coder-v2:16b"}

    async def get_client(self) -> httpx.AsyncClient:
        """Get or initialize the persistent async HTTP client tied to the current event loop."""
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        if self.client is None or self.client.is_closed or (current_loop and self._loop != current_loop):
            if self.client and not self.client.is_closed:
                try:
                    await self.client.aclose()
                except Exception:
                    pass
            self._loop = current_loop
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(settings.OLLAMA_TIMEOUT_SECONDS, connect=5.0)
            )
        return self.client

    async def close(self):
        """Close the HTTP client gracefully."""
        if self.client and not self.client.is_closed:
            await self.client.aclose()
            self.client = None
            self._loop = None

    async def unload_other_models(self, target_model: str):
        """
        Free GPU VRAM by unloading any currently loaded models in Ollama other than target_model.
        Prevents CUDA_Host buffer allocation failures on 4GB VRAM GPUs.
        """
        client = await self.get_client()
        try:
            res = await client.get("/api/ps", timeout=3.0)
            if res.status_code != 200:
                return
            running = res.json().get("models", [])
            for m in running:
                loaded_name = m.get("name", "")
                if loaded_name and loaded_name != target_model:
                    logger.info(f"Unloading '{loaded_name}' from VRAM before loading '{target_model}'...")
                    await client.post(
                        "/api/generate",
                        json={"model": loaded_name, "prompt": "", "keep_alive": 0},
                        timeout=5.0
                    )
        except Exception as e:
            logger.debug(f"VRAM unload check skipped: {e}")

    def _get_fallback_chain(self, primary_model: str) -> List[str]:
        """
        Build an ordered list of candidate models starting with primary_model,
        falling back to models that fit within 4GB VRAM / system commit limits.
        """
        candidates = [
            primary_model,
            settings.DEFAULT_MODEL,      # qwen2.5-coder:7b
            settings.ADVISOR_MODEL,      # llama3.1:8b
            settings.FALLBACK_MODEL,     # phi3.5:latest (2.2 GB - fits 100% in 4GB VRAM)
            settings.FAST_WORKER_MODEL,  # qwen2.5:3b (1.9 GB - fits 100% in 4GB VRAM)
        ]
        ordered: List[str] = []
        for m in candidates:
            if m and m not in ordered and m not in self._unusable_models:
                ordered.append(m)
        if not ordered:
            ordered = [settings.FAST_WORKER_MODEL, settings.FALLBACK_MODEL]
        return ordered

    async def check_health(self) -> Dict[str, Any]:
        """Check Ollama server health and connection status."""
        client = await self.get_client()
        try:
            res = await client.get("/api/tags")
            if res.status_code == 200:
                data = res.json()
                models = [m.get("name") for m in data.get("models", [])]
                return {
                    "status": "healthy",
                    "ollama_url": self.base_url,
                    "models_count": len(models),
                    "models": models
                }
            return {
                "status": "unhealthy",
                "ollama_url": self.base_url,
                "error": f"HTTP {res.status_code}"
            }
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return {
                "status": "offline",
                "ollama_url": self.base_url,
                "error": str(e)
            }

    async def list_models(self) -> List[ModelDetails]:
        """Get list of available Ollama models with category and UI badges."""
        client = await self.get_client()
        try:
            res = await client.get("/api/tags")
            if res.status_code != 200:
                return []
            
            raw_models = res.json().get("models", [])
            result: List[ModelDetails] = []
            
            for m in raw_models:
                name = m.get("name", "")
                size = m.get("size", 0)
                size_gb = round(size / (1024 ** 3), 2)
                
                # Determine category & badge color
                category = "general"
                badge = "green"
                if "deepseek" in name or "16b" in name:
                    category = "heavy_logic"
                    badge = "purple"
                elif "llama" in name or "8b" in name:
                    category = "advisor"
                    badge = "yellow"
                elif "3b" in name:
                    category = "fast"
                    badge = "gray"
                elif "phi" in name:
                    category = "fallback"
                    badge = "blue"
                
                result.append(ModelDetails(
                    name=name,
                    size_bytes=size,
                    size_formatted=f"{size_gb} GB",
                    modified_at=m.get("modified_at"),
                    category=category,
                    badge_color=badge,
                    is_available=True
                ))
            return result
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return []

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        keep_alive: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream chat response token-by-token from Ollama with automatic VRAM eviction
        and graceful fallback if a large model fails to allocate CUDA_Host / VRAM buffers.
        """
        client = await self.get_client()
        
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)
        
        fallback_chain = self._get_fallback_chain(model)
        last_error = ""

        for attempt_idx, candidate_model in enumerate(fallback_chain):
            if attempt_idx > 0:
                await self.unload_other_models(candidate_model)

            payload = {
                "model": candidate_model,
                "messages": formatted_messages,
                "stream": True,
                "keep_alive": keep_alive or settings.OLLAMA_KEEP_ALIVE,
                "options": {
                    "temperature": temperature,
                    "num_ctx": 2048
                }
            }

            try:
                async with client.stream("POST", "/api/chat", json=payload, timeout=settings.OLLAMA_TIMEOUT_SECONDS) as response:
                    if response.status_code != 200:
                        error_bytes = await response.aread()
                        error_str = error_bytes.decode("utf-8", errors="ignore")
                        last_error = f"Ollama error {response.status_code}: {error_str}"
                        logger.warning(
                            f"Model '{candidate_model}' failed (HTTP {response.status_code}): {error_str[:200]}. "
                            f"Attempting next fallback model..."
                        )
                        if "alloc" in error_str.lower() or "buffer" in error_str.lower() or "memory" in error_str.lower():
                            self._unusable_models.add(candidate_model)
                        continue

                    # Successfully connected and streaming!
                    self.last_active_model = candidate_model
                    if candidate_model != model:
                        yield {
                            "type": "model_fallback",
                            "original_model": model,
                            "fallback_model": candidate_model,
                            "reason": f"สลับจาก {model} เป็น {candidate_model} อัตโนมัติ (ปรับให้เหมาะกับ VRAM ในเครื่อง)"
                        }

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            if "error" in chunk:
                                last_error = str(chunk["error"])
                                break
                            msg = chunk.get("message", {})
                            token = msg.get("content", "")
                            done = chunk.get("done", False)
                            
                            yield {
                                "content": token,
                                "done": done,
                                "model": candidate_model,
                                "total_duration": chunk.get("total_duration"),
                                "eval_count": chunk.get("eval_count")
                            }
                            if done:
                                return
                        except json.JSONDecodeError:
                            continue
                    # If stream ended cleanly without done=True
                    return
            except Exception as e:
                last_error = f"Streaming failed: {str(e)}"
                logger.warning(f"Streaming exception with model {candidate_model}: {e}. Trying fallback...")
                client = await self.get_client()
                continue

        logger.error(f"All models in fallback chain failed. Last error: {last_error}")
        yield {
            "error": last_error or "ไม่สามารถเชื่อมต่อหรือโหลดโมเดลจาก Ollama ได้",
            "done": True
        }

    async def generate(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        format_json: bool = False
    ) -> Dict[str, Any]:
        """Non-streaming text generation helper with automatic fallback on memory errors."""
        client = await self.get_client()
        fallback_chain = self._get_fallback_chain(model)
        last_error = ""

        for attempt_idx, candidate_model in enumerate(fallback_chain):
            if attempt_idx > 0:
                await self.unload_other_models(candidate_model)

            payload: Dict[str, Any] = {
                "model": candidate_model,
                "prompt": prompt,
                "stream": False,
                "keep_alive": settings.OLLAMA_KEEP_ALIVE,
                "options": {
                    "temperature": temperature,
                    "num_ctx": 2048
                }
            }
            if system_prompt:
                payload["system"] = system_prompt
            if format_json:
                payload["format"] = "json"

            try:
                res = await client.post("/api/generate", json=payload, timeout=settings.OLLAMA_TIMEOUT_SECONDS)
                if res.status_code == 200:
                    self.last_active_model = candidate_model
                    return res.json()
                err_text = res.text
                last_error = f"Ollama error {res.status_code}: {err_text}"
                logger.warning(f"Ollama generate failed on {candidate_model} ({res.status_code}), trying fallback...")
                if "alloc" in err_text.lower() or "buffer" in err_text.lower():
                    self._unusable_models.add(candidate_model)
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Ollama generate exception with {candidate_model}: {e}")
                client = await self.get_client()

        logger.error(f"Ollama generate exhausted all fallbacks: {last_error}")
        return {"response": "", "error": last_error}
            
    async def warmup_models(self, models: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Preload primary model into VRAM during system startup with num_ctx=2048.
        Only preloads a single model on 4GB VRAM systems to avoid VRAM fragmentation.
        """
        target_models = models[:1] if models else [settings.FAST_WORKER_MODEL]
        client = await self.get_client()
        status = {}
        
        for model_name in target_models:
            try:
                res = await client.post(
                    "/api/generate",
                    json={
                        "model": model_name,
                        "prompt": "",
                        "keep_alive": settings.OLLAMA_KEEP_ALIVE,
                        "options": {"num_ctx": 2048}
                    },
                    timeout=15.0
                )
                status[model_name] = res.status_code == 200
                if res.status_code == 200:
                    self.last_active_model = model_name
                logger.info(f"Model VRAM Warmup ({model_name}): {'Ready' if res.status_code == 200 else 'Failed'}")
            except Exception as e:
                logger.warning(f"Model VRAM Warmup failed for {model_name}: {e}")
                status[model_name] = False
                
        return status

ollama_service = OllamaService()
