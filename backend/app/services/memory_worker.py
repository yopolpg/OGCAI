import re
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

    def _fast_regex_extract(self, text: str) -> List[Dict[str, Any]]:
        """
        Zero-VRAM, 0ms rule-based extraction of clear user profile facts in Thai/English.
        Prevents unnecessary GPU model swaps on 4GB VRAM systems.
        """
        extracted: List[Dict[str, Any]] = []

        # 1. Name extraction
        name_match = re.search(r"(?:ผมชื่อ|ฉันชื่อ|เราชื่อ|ชื่อเล่นชื่อ|my name is)\s*([^\s,.\n]{2,25})", text, re.IGNORECASE)
        if name_match:
            extracted.append({
                "key": "user_name",
                "value": name_match.group(1).strip(),
                "category": "personal",
                "confidence": 0.95
            })

        # 2. Profession / Role
        job_match = re.search(r"(?:ทำงานเป็น|อาชีพเป็น|เป็นตำแหน่ง|work as a|working as)\s*([A-Za-zก-๙0-9\s\-/]{3,35}?)(?=\s+(?:เขียน|ใช้|และ|ที่|ครับ|ค่ะ)|[,.\n]|$)", text, re.IGNORECASE)
        if job_match:
            extracted.append({
                "key": "profession",
                "value": job_match.group(1).strip(),
                "category": "personal",
                "confidence": 0.90
            })

        # 3. Tech stack / Programming language
        tech_match = re.search(r"(?:เขียนภาษา|ใช้ภาษา|ถนัดภาษา|tech stack คือ)\s*([A-Za-z0-9,/\s+#.\-]{2,35}?)(?=\s+(?:และ|ตั้งเป้า|อยู่|ครับ|ค่ะ)|[,.\n]|$)", text, re.IGNORECASE)
        if tech_match:
            extracted.append({
                "key": "tech_stack",
                "value": tech_match.group(1).strip(),
                "category": "preference",
                "confidence": 0.90
            })

        # 4. Savings / Financial Goal
        save_match = re.search(r"(?:ตั้งเป้า.*ออมเงิน|ออมเงินเดือนละ|เป้าหมายการออม)\s*([0-9,]+(?:\s*บาท)?)", text, re.IGNORECASE)
        if save_match:
            extracted.append({
                "key": "saving_goal",
                "value": save_match.group(1).strip(),
                "category": "goal",
                "confidence": 0.95
            })

        return extracted

    async def extract_and_save_facts(self, user_message: str, assistant_message: Optional[str] = None):
        """
        Background worker task that analyzes conversation to extract long-term user profile facts.
        Uses zero-VRAM regex extraction first, and reuses the active VRAM model if LLM extraction is needed.
        """
        if len(user_message.strip()) < 15:
            return

        facts: List[Dict[str, Any]] = self._fast_regex_extract(user_message)

        # Only call LLM if regex found nothing AND message clearly contains personal profile indicators
        personal_indicators = ["ผมชื่อ", "ฉันชื่อ", "ทำงาน", "อาชีพ", "ตั้งเป้า", "ชอบ", "แพ้", "เป้าหมายของผม", "เป้าหมายของฉัน"]
        if not facts and any(ind in user_message for ind in personal_indicators):
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
                # Reuse currently loaded model in VRAM if available to avoid swapping models on 4GB GPU
                target_model = ollama_service.last_active_model or self.model
                res = await ollama_service.generate(
                    prompt=prompt,
                    model=target_model,
                    temperature=0.1,
                    format_json=True
                )
                raw_text = res.get("response", "").strip()
                if raw_text and raw_text != "[]":
                    parsed = json.loads(raw_text)
                    if isinstance(parsed, list):
                        facts.extend(parsed)
                    elif isinstance(parsed, dict) and "key" in parsed and "value" in parsed:
                        facts.append(parsed)
            except Exception as e:
                logger.debug(f"LLM memory extraction skipped: {e}")

        if not facts:
            return

        try:
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
            logger.debug(f"Memory save encountered minor issue: {e}")

    def trigger_background_extraction(self, user_message: str, assistant_message: Optional[str] = None):
        """Trigger fact extraction non-blockingly."""
        asyncio.create_task(self.extract_and_save_facts(user_message, assistant_message))

memory_worker = MemoryWorker()
