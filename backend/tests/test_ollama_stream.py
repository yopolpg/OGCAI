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

@pytest.mark.asyncio
async def test_heavy_model_vram_fallback_and_compound_interest_chat():
    """
    Regression test for CUDA_Host buffer OOM on 4GB VRAM systems when routing to deepseek-coder-v2:16b
    on compound interest simulation queries.
    """
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    user_prompt = "ช่วยคำนวณและจำลองการเติบโตของเงินทุน เงินต้น 100,000 บาท ออมเพิ่มเดือนละ 5,000 บาท ผลตอบแทน 8% ต่อปี เป็นเวลา 5 ปี"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        async with client.stream("POST", "/api/chat/stream", json={"message": user_prompt}) as res:
            assert res.status_code == 200
            lines = []
            async for line in res.aiter_lines():
                if line:
                    lines.append(line)

            joined = "\n".join(lines)
            assert "event: error" not in joined
            assert "event: token" in joined
            assert "event: done" in joined
            assert "/api/cache/charts/chart_" in joined
