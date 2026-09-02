import pytest
import pytest_asyncio
from app.services.memory_worker import memory_worker
from app.db.database import AsyncSessionLocal
from app.db.repository import DatabaseRepository

@pytest.mark.asyncio
async def test_memory_worker_fact_extraction():
    test_user_msg = "ผมชื่อธนกร ตอนนี้ทำงานเป็น Software Engineer เขียนภาษา Python และตั้งเป้าจะออมเงินเดือนละ 15,000 บาท"
    
    # Run extraction directly
    await memory_worker.extract_and_save_facts(user_message=test_user_msg)

    # Verify extracted facts in database
    async with AsyncSessionLocal() as session:
        facts = await DatabaseRepository.get_all_profile_facts(session)
        assert len(facts) > 0
        fact_keys = [f.key.lower() for f in facts]
        # At least one relevant fact should be recognized
        assert any("name" in k or "profession" in k or "tech" in k or "saving" in k or "goal" in k for k in fact_keys)
