import pytest
import pytest_asyncio
from app.services.ollama_service import ollama_service
from app.config import settings

@pytest.mark.asyncio
async def test_ollama_health():
    health = await ollama_service.check_health()
    assert health["status"] == "healthy"
    assert health["models_count"] > 0

@pytest.mark.asyncio
async def test_ollama_list_models():
    models = await ollama_service.list_models()
    assert len(models) > 0
    model_names = [m.name for m in models]
    # Verify key models are recognized
    assert any("qwen" in name or "llama" in name or "phi" in name for name in model_names)

@pytest.mark.asyncio
async def test_ollama_fast_chat_stream():
    # Use qwen2.5:3b for quick test
    chunks = []
    async for chunk in ollama_service.stream_chat(
        messages=[{"role": "user", "content": "Say hello in 2 words"}],
        model=settings.FAST_WORKER_MODEL,
        temperature=0.1
    ):
        if chunk.get("content"):
            chunks.append(chunk["content"])
        if chunk.get("done"):
            break
            
    assert len(chunks) > 0
    full_text = "".join(chunks)
    assert len(full_text.strip()) > 0
