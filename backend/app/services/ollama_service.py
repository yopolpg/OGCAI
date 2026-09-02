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
        keep_alive: str = "15m"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream chat response token-by-token from Ollama.
        Yields dicts with {'content': token, 'done': False} and final {'done': True, 'stats': ...}
        """
        client = await self.get_client()
        
        # Prepare payload
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)
        
        payload = {
            "model": model,
            "messages": formatted_messages,
            "stream": True,
            "keep_alive": keep_alive,
            "options": {
                "temperature": temperature
            }
        }
        
        try:
            async with client.stream("POST", "/api/chat", json=payload, timeout=settings.OLLAMA_TIMEOUT_SECONDS) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    yield {
                        "error": f"Ollama error {response.status_code}: {error_text.decode('utf-8', errors='ignore')}",
                        "done": True
                    }
                    return

                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        msg = chunk.get("message", {})
                        token = msg.get("content", "")
                        done = chunk.get("done", False)
                        
                        yield {
                            "content": token,
                            "done": done,
                            "model": model,
                            "total_duration": chunk.get("total_duration"),
                            "eval_count": chunk.get("eval_count")
                        }
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Streaming error with model {model}: {e}")
            yield {
                "error": f"Streaming failed: {str(e)}",
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
        """Non-streaming text generation helper (used by fast router classifier)."""
        client = await self.get_client()
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        if system_prompt:
            payload["system"] = system_prompt
        if format_json:
            payload["format"] = "json"
            
    async def warmup_models(self, models: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Preload models into VRAM during system startup with keep_alive to eliminate cold-start latency.
        """
        target_models = models or [settings.DEFAULT_MODEL, settings.FAST_WORKER_MODEL]
        client = await self.get_client()
        status = {}
        
        for model_name in target_models:
            try:
                # Issue empty generation with keep_alive to preload into VRAM
                res = await client.post(
                    "/api/generate",
                    json={
                        "model": model_name,
                        "prompt": "",
                        "keep_alive": settings.OLLAMA_KEEP_ALIVE
                    },
                    timeout=15.0
                )
                status[model_name] = res.status_code == 200
                logger.info(f"Model VRAM Warmup ({model_name}): {'Ready' if res.status_code == 200 else 'Failed'}")
            except Exception as e:
                logger.warning(f"Model VRAM Warmup failed for {model_name}: {e}")
                status[model_name] = False
                
        return status

ollama_service = OllamaService()
