import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_api_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "online"
        assert "ollama" in data
        assert data["ollama"]["status"] == "healthy"

@pytest.mark.asyncio
async def test_api_models_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/models")
        assert res.status_code == 200
        models = res.json()
        assert isinstance(models, list)
        assert len(models) > 0
        assert "name" in models[0]
        assert "badge_color" in models[0]

@pytest.mark.asyncio
async def test_api_route_diagnostic():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test Math/Code Routing
        res = await client.post("/api/route", json={
            "message": "คำนวณดอกเบี้ยทบต้น 5% ต่อปี"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["intent_category"] == "heavy_logic"
        assert "deepseek" in data["selected_model"]

        # Test Life Advice Routing
        res2 = await client.post("/api/route", json={
            "message": "รู้สึกเครียดเรื่องงาน ขอคำปรึกษาและเป้าหมายชีวิตหน่อย"
        })
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["intent_category"] == "advisor"
        assert "llama" in data2["selected_model"]

@pytest.mark.asyncio
async def test_api_chat_stream():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        async with client.stream("POST", "/api/chat/stream", json={
            "message": "ตอบสั้นๆ ว่าพร้อมทำงาน",
            "model": "qwen2.5:3b"
        }) as res:
            assert res.status_code == 200
            assert "text/event-stream" in res.headers.get("content-type", "")
            
            events = []
            async for line in res.aiter_lines():
                if line:
                    events.append(line)
            
            assert len(events) > 0
            # Verify metadata and token events are present
            combined = "\n".join(events)
            assert "event: metadata" in combined
            assert "event: token" in combined
