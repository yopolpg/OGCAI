import json
import logging
import asyncio
from typing import Optional, List, Dict, Any

from app.config import settings
from app.services.ollama_service import ollama_service
from app.db.database import AsyncSessionLocal
from app.db.repository import DatabaseRepository

logger = logging.getLogger("ogcai.memory_worker")

class MemoryWorker:
    def __init__(self):
        self.model = settings.FAST_WORKER_MODEL  # qwen2.5:3b

    async def extract_and_save_facts(self, user_message: str, assistant_message: Optional[str] = None):
        """
        Background worker task that analyzes conversation to extract long-term user profile facts.
        """
        # Skip if message is too short or trivial greeting
        if len(user_message.strip()) < 15:
            return

        prompt = f"""You are a personal AI memory assistant. Analyze the user's message to extract enduring facts, preferences, goals, work details, or constraints about the USER.

User message: "{user_message}"
{f'Assistant reply: "{assistant_message[:200]}"' if assistant_message else ''}

Extract only CLEAR facts about the user. Return a JSON array of objects with keys:
- "key": A short snake_case identifier (e.g., "user_name", "profession", "tech_stack", "health_goal", "favorite_topic", "daily_budget")
- "value": The extracted fact value in concise Thai or English
- "category": One of "personal", "preference", "goal", "constraint", "health"
- "confidence": Float between 0.7 and 1.0

If no enduring personal facts are mentioned, return an empty array: []

Return ONLY the JSON array, no extra commentary:"""

        try:
            res = await ollama_service.generate(
                prompt=prompt,
                model=self.model,
                temperature=0.1,
                format_json=True
            )
            raw_text = res.get("response", "").strip()
            if not raw_text or raw_text == "[]":
                return

            # Parse JSON
            facts: List[Dict[str, Any]] = json.loads(raw_text)
            if not isinstance(facts, list) or not facts:
                return

            # Save facts to database
            async with AsyncSessionLocal() as session:
                for fact in facts:
                    key = fact.get("key")
                    value = fact.get("value")
                    category = fact.get("category", "general")
                    confidence = float(fact.get("confidence", 0.9))

                    if key and value:
                        await DatabaseRepository.set_profile_fact(
                            session=session,
                            key=key,
                            value=str(value),
                            category=category,
                            confidence=confidence
                        )
                        logger.info(f"Memory Worker extracted fact: {key} = {value} ({category})")
                await session.commit()

        except Exception as e:
            logger.debug(f"Memory extraction skipped or encountered minor issue: {e}")

    def trigger_background_extraction(self, user_message: str, assistant_message: Optional[str] = None):
        """Trigger fact extraction non-blockingly."""
        asyncio.create_task(self.extract_and_save_facts(user_message, assistant_message))

memory_worker = MemoryWorker()
