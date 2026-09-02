import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    Conversation, Message, UserProfile,
    StarredKnowledge, FinanceTransaction, HabitLog
)

logger = logging.getLogger("ogcai.repository")

class DatabaseRepository:
    # ------------------ Conversations & Messages ------------------
    @staticmethod
    async def create_conversation(session: AsyncSession, title: str = "การสนทนาใหม่") -> Conversation:
        conv = Conversation(title=title)
        session.add(conv)
        await session.flush()
        return conv

    @staticmethod
    async def get_conversation(session: AsyncSession, conv_id: str) -> Optional[Conversation]:
        stmt = select(Conversation).options(selectinload(Conversation.messages)).where(Conversation.id == conv_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_conversations(session: AsyncSession, limit: int = 50) -> List[Conversation]:
        stmt = select(Conversation).order_by(desc(Conversation.is_pinned), desc(Conversation.updated_at)).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_conversation_title(session: AsyncSession, conv_id: str, new_title: str) -> bool:
        stmt = update(Conversation).where(Conversation.id == conv_id).values(title=new_title)
        res = await session.execute(stmt)
        return res.rowcount > 0

    @staticmethod
    async def delete_conversation(session: AsyncSession, conv_id: str) -> bool:
        stmt = delete(Conversation).where(Conversation.id == conv_id)
        res = await session.execute(stmt)
        return res.rowcount > 0

    @staticmethod
    async def add_message(
        session: AsyncSession,
        conversation_id: str,
        role: str,
        content: str,
        model: Optional[str] = None,
        intent_category: Optional[str] = None,
        metadata_json: Optional[str] = None
    ) -> Message:
        # Ensure conversation exists
        conv = await session.get(Conversation, conversation_id)
        if not conv:
            conv = Conversation(id=conversation_id, title=content[:30] if role == "user" else "การสนทนาใหม่")
            session.add(conv)
            await session.flush()

        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            model=model,
            intent_category=intent_category,
            metadata_json=metadata_json
        )
        session.add(msg)
        await session.flush()
        return msg

    @staticmethod
    async def get_messages(session: AsyncSession, conversation_id: str, limit: int = 100) -> List[Message]:
        stmt = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.timestamp).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def toggle_star_message(session: AsyncSession, message_id: str) -> Optional[Message]:
        msg = await session.get(Message, message_id)
        if msg:
            msg.is_starred = not msg.is_starred
            await session.flush()
        return msg

    # ------------------ User Profile Memory ------------------
    @staticmethod
    async def set_profile_fact(
        session: AsyncSession,
        key: str,
        value: str,
        category: str = "general",
        confidence: float = 1.0
    ) -> UserProfile:
        stmt = select(UserProfile).where(UserProfile.key == key)
        result = await session.execute(stmt)
        profile_item = result.scalar_one_or_none()

        if profile_item:
            profile_item.value = value
            profile_item.category = category
            profile_item.confidence = confidence
        else:
            profile_item = UserProfile(
                key=key,
                value=value,
                category=category,
                confidence=confidence
            )
            session.add(profile_item)

        await session.flush()
        return profile_item

    @staticmethod
    async def get_all_profile_facts(session: AsyncSession) -> List[UserProfile]:
        stmt = select(UserProfile).order_by(UserProfile.category, UserProfile.key)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_profile_context_string(session: AsyncSession) -> str:
        facts = await DatabaseRepository.get_all_profile_facts(session)
        if not facts:
            return ""
        lines = ["[ข้อมูลและบริบทส่วนตัวของผู้ใช้ (Long-term Profile)]"]
        for f in facts:
            lines.append(f"- {f.key}: {f.value} (ความเชื่อมั่น: {int(f.confidence*100)}%)")
        return "\n".join(lines)

    @staticmethod
    async def delete_profile_fact(session: AsyncSession, fact_id: int) -> bool:
        stmt = delete(UserProfile).where(UserProfile.id == fact_id)
        res = await session.execute(stmt)
        return res.rowcount > 0

    # ------------------ Starred Knowledge Base ------------------
    @staticmethod
    async def create_starred_knowledge(
        session: AsyncSession,
        title: str,
        content: str,
        summary: str = "",
        tags: str = "",
        message_id: Optional[str] = None
    ) -> StarredKnowledge:
        item = StarredKnowledge(
            message_id=message_id,
            title=title,
            tags=tags,
            summary=summary,
            content=content
        )
        session.add(item)
        await session.flush()
        return item

    @staticmethod
    async def list_starred_knowledge(session: AsyncSession, limit: int = 50) -> List[StarredKnowledge]:
        stmt = select(StarredKnowledge).order_by(desc(StarredKnowledge.created_at)).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def delete_starred_knowledge(session: AsyncSession, item_id: str) -> bool:
        stmt = delete(StarredKnowledge).where(StarredKnowledge.id == item_id)
        res = await session.execute(stmt)
        return res.rowcount > 0

    # ------------------ Finance & Habit Logs ------------------
    @staticmethod
    async def add_transaction(
        session: AsyncSession,
        tx_type: str,
        amount: float,
        category: str,
        description: str,
        date: str
    ) -> FinanceTransaction:
        tx = FinanceTransaction(
            type=tx_type,
            amount=amount,
            category=category,
            description=description,
            date=date
        )
        session.add(tx)
        await session.flush()
        return tx

    @staticmethod
    async def log_habit(
        session: AsyncSession,
        habit_name: str,
        date: str,
        status: str = "completed",
        notes: str = ""
    ) -> HabitLog:
        habit = HabitLog(
            habit_name=habit_name,
            date=date,
            status=status,
            notes=notes
        )
        session.add(habit)
        await session.flush()
        return habit

    @staticmethod
    async def list_habit_names(session: AsyncSession) -> List[str]:
        stmt = select(HabitLog.habit_name).distinct()
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def delete_habit_logs(session: AsyncSession, habit_name: str) -> bool:
        from sqlalchemy import delete
        stmt = delete(HabitLog).where(HabitLog.habit_name == habit_name)
        await session.execute(stmt)
        await session.flush()
        return True
