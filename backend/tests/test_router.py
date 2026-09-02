import pytest
import pytest_asyncio
from app.services.router_service import router_service
from app.config import settings

@pytest.mark.asyncio
async def test_manual_override():
    decision = await router_service.route_message(
        message="สวัสดีครับ",
        manual_model="llama3.1:8b"
    )
    assert decision.selected_model == "llama3.1:8b"
    assert decision.routing_mode == "manual"
    assert decision.tier_used == "manual_override"

@pytest.mark.asyncio
async def test_tier1_heavy_logic_math():
    decision = await router_service.route_message(
        message="ช่วยคำนวณสูตรดอกเบี้ยทบต้นเงินฝาก 100,000 บาท 5 ปีให้หน่อย"
    )
    assert decision.selected_model == settings.HEAVY_LOGIC_MODEL
    assert decision.intent_category == "heavy_logic"
    assert decision.tier_used == "tier1_regex"

@pytest.mark.asyncio
async def test_tier1_heavy_logic_coding():
    decision = await router_service.route_message(
        message="ช่วย optimize code dynamic programming ตัวนี้ให้หน่อย\n```python\ndef solve(): pass\n```"
    )
    assert decision.selected_model == settings.HEAVY_LOGIC_MODEL
    assert decision.intent_category == "heavy_logic"

@pytest.mark.asyncio
async def test_tier1_advisor_life():
    decision = await router_service.route_message(
        message="ช่วงนี้รู้สึกหมดไฟ เครียด และเหนื่อยกับงานมาก ขอคำปรึกษาและวิธีปรับ mindset หน่อย"
    )
    assert decision.selected_model == settings.ADVISOR_MODEL
    assert decision.intent_category == "advisor"
    assert decision.tier_used == "tier1_regex"

@pytest.mark.asyncio
async def test_default_short_general():
    decision = await router_service.route_message(
        message="สวัสดีตอนเช้าครับ"
    )
    assert decision.selected_model == settings.DEFAULT_MODEL
    assert decision.intent_category == "general"
