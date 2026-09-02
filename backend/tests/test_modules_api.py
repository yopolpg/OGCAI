import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_modules_api_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Test Sandbox Execution API
        sandbox_res = await client.post("/api/modules/sandbox/execute", json={
            "code": "print(sum([1, 2, 3, 4, 5]))"
        })
        assert sandbox_res.status_code == 200
        assert sandbox_res.json()["stdout"] == "15"

        # 2. Test Chart Generation API
        chart_res = await client.post("/api/modules/sandbox/chart", json={
            "chart_type": "bar",
            "data": {"labels": ["A", "B"], "values": [10, 20]},
            "title": "Test Chart"
        })
        assert chart_res.status_code == 200
        assert "image_url" in chart_res.json()

        # 3. Test Finance Parse & Transaction API
        parse_res = await client.post("/api/modules/finance/parse", json={
            "text": "จ่ายค่าบิลไฟฟ้า 1450 บาท"
        })
        assert parse_res.status_code == 200
        assert parse_res.json()["amount"] == 1450.0

        tx_res = await client.post("/api/modules/finance/transaction", json={
            "type": "expense",
            "amount": 1450.0,
            "category": "bills",
            "description": "ค่าบิลไฟฟ้า"
        })
        assert tx_res.status_code == 200
        assert tx_res.json()["id"] is not None

        # 4. Test Finance Compound Growth API
        growth_res = await client.post("/api/modules/finance/compound-growth", json={
            "principal": 50000,
            "monthly_contribution": 3000,
            "annual_rate_pct": 8.0,
            "years": 3
        })
        assert growth_res.status_code == 200
        assert "final_balance" in growth_res.json()

        # 5. Test Health Routine & Habit API
        habit_res = await client.post("/api/modules/health/habit/log", json={
            "habit_name": "ดื่มน้ำ 2 ลิตร",
            "status": "completed"
        })
        assert habit_res.status_code == 200

        routine_res = await client.post("/api/modules/health/routine", json={
            "wake_time": "06:00",
            "sleep_time": "22:00"
        })
        assert routine_res.status_code == 200
        assert len(routine_res.json()["schedule"]) > 0

        # 6. Test Study Roadmap API
        study_res = await client.post("/api/modules/study/roadmap", json={
            "topic": "Python Data Science",
            "weeks": 2
        })
        assert study_res.status_code == 200
        assert "weeks" in study_res.json()
