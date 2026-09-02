import pytest
import pytest_asyncio
from pathlib import Path
from app.db.database import init_db, AsyncSessionLocal, backup_database
from app.db.repository import DatabaseRepository
from app.config import settings

@pytest.mark.asyncio
async def test_database_init_and_crud():
    await init_db()
    
    async with AsyncSessionLocal() as session:
        # 1. Test Conversation & Messages
        conv = await DatabaseRepository.create_conversation(session, title="บทสนทนาทดสอบ")
        assert conv.id is not None
        assert conv.title == "บทสนทนาทดสอบ"
        
        msg1 = await DatabaseRepository.add_message(
            session=session,
            conversation_id=conv.id,
            role="user",
            content="สวัสดีครับ มีคำถามเรื่องการเงิน",
            intent_category="general"
        )
        assert msg1.id is not None
        
        msg2 = await DatabaseRepository.add_message(
            session=session,
            conversation_id=conv.id,
            role="assistant",
            content="ยินดีให้คำปรึกษาครับ ต้องการวางแผนด้านใด",
            model="qwen2.5-coder:7b"
        )
        assert msg2.id is not None
        await session.commit()

        # Retrieve conversation with messages
        fetched_conv = await DatabaseRepository.get_conversation(session, conv.id)
        assert fetched_conv is not None
        assert len(fetched_conv.messages) == 2

        # 2. Test User Profile Facts
        fact = await DatabaseRepository.set_profile_fact(
            session=session,
            key="user_name",
            value="สมชาย",
            category="personal"
        )
        assert fact.key == "user_name"
        assert fact.value == "สมชาย"
        await session.commit()

        context_str = await DatabaseRepository.get_profile_context_string(session)
        assert "user_name: สมชาย" in context_str

        # 3. Test Starred Knowledge
        starred = await DatabaseRepository.create_starred_knowledge(
            session=session,
            title="สูตรคำนวณดอกเบี้ยทบต้น",
            content="A = P(1 + r/n)^(nt)",
            tags="finance,math"
        )
        assert starred.id is not None
        await session.commit()

        starred_list = await DatabaseRepository.list_starred_knowledge(session)
        assert len(starred_list) >= 1

def test_database_backup():
    backup_path = backup_database()
    assert backup_path != ""
    assert Path(backup_path).exists()
