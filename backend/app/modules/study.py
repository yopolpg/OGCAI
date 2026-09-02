import json
import logging
from typing import Dict, Any, List, Optional

from app.config import settings
from app.services.ollama_service import ollama_service

logger = logging.getLogger("ogcai.study_module")

class StudyModule:
    def __init__(self):
        self.model = settings.DEFAULT_MODEL  # qwen2.5-coder:7b

    async def generate_skill_roadmap(
        self,
        topic: str,
        total_weeks: int = 4,
        target_level: str = "Beginner to Intermediate"
    ) -> Dict[str, Any]:
        """
        Generate a structured milestone learning roadmap for a topic or skill.
        """
        prompt = f"""You are an expert curriculum designer. Create a clear, practical, week-by-week learning roadmap for:
Topic: "{topic}"
Duration: {total_weeks} weeks
Level: "{target_level}"

Return a JSON object with:
- "topic": "{topic}"
- "summary": A 1-2 sentence overview of the goal in Thai
- "weeks": Array of week objects, each containing:
    - "week_number": Integer (1, 2, ...)
    - "title": Week title in Thai
    - "core_concepts": Array of 3-4 concept strings
    - "hands_on_project": A mini project or exercise string for this week
    - "key_resources": Array of 2 suggested resources/topics to search

Return ONLY valid JSON matching this schema, no markdown codeblocks or commentary:"""

        try:
            res = await ollama_service.generate(
                prompt=prompt,
                model=self.model,
                temperature=0.3,
                format_json=True
            )
            raw = res.get("response", "").strip()
            data = json.loads(raw)
            return data
        except Exception as e:
            logger.warning(f"AI Roadmap generation failed, using fallback template: {e}")
            # Fallback structured roadmap template
            return {
                "topic": topic,
                "summary": f"แผนการเรียนรู้ทักษะ {topic} แบบเข้มข้นในระยะเวลา {total_weeks} สัปดาห์",
                "weeks": [
                    {
                        "week_number": i,
                        "title": f"สัปดาห์ที่ {i}: รากฐานและการลงมือปฏิบัติ ({topic})",
                        "core_concepts": [
                            f"ทำความเข้าใจโครงสร้างหลักของ {topic}",
                            f"ทบทวนไวยากรณ์และหลักการทำงานที่สำคัญ",
                            f"การจัดการข้อผิดพลาดและ Best Practices"
                        ],
                        "hands_on_project": f"สร้างมินิโปรเจกต์ทดลองชิ้นที่ {i}",
                        "key_resources": ["Official Documentation", "Interactive Practice Tutorials"]
                    }
                    for i in range(1, total_weeks + 1)
                ]
            }

    async def generate_flashcards(self, content_or_topic: str, count: int = 5) -> List[Dict[str, str]]:
        """
        Generate spaced-repetition Q&A flashcards from study notes or a topic.
        """
        prompt = f"""Create {count} high-yield study flashcards from the following content or topic:
Content: "{content_or_topic[:1000]}"

Return a JSON array of objects with keys:
- "front": Clear question or concept term (in Thai/English)
- "back": Concise, accurate explanation and key takeaway (in Thai)

Return ONLY a JSON array or object containing "flashcards" list:"""

        try:
            res = await ollama_service.generate(
                prompt=prompt,
                model=self.model,
                temperature=0.2,
                format_json=True
            )
            raw = res.get("response", "").strip()
            data = json.loads(raw)
            
            if isinstance(data, list) and len(data) > 0:
                return data
            elif isinstance(data, dict):
                # Check for common wrapper keys
                for key in ["flashcards", "cards", "items", "data"]:
                    if key in data and isinstance(data[key], list) and len(data[key]) > 0:
                        return data[key]
                # If dict has front and back directly
                if "front" in data and "back" in data:
                    return [data]

            # Fallback if empty
            return [
                {
                    "front": f"ประเด็นสำคัญของ {content_or_topic[:30]}",
                    "back": "ทบทวนแนวคิดหลัก ไวยากรณ์ และการนำไปประยุกต์ใช้งานจริง"
                }
            ]
        except Exception as e:
            logger.error(f"Flashcard generation error: {e}")
            return [
                {
                    "front": f"แนวคิดหลักของ {content_or_topic[:30]}",
                    "back": "ทบทวนประเด็นสำคัญและฝึกปฏิบัติเพื่อเพิ่มความเข้าใจอย่างลึกซึ้ง"
                }
            ]

    async def generate_quiz(self, topic: str, count: int = 3) -> List[Dict[str, Any]]:
        """
        Generate multiple-choice quiz questions with options and explanations.
        """
        prompt = f"""Generate {count} multiple-choice quiz questions to test knowledge on:
Topic: "{topic}"

Return a JSON array of objects with keys:
- "question": The question text in Thai
- "options": Array of exactly 4 choice strings
- "correct_index": Integer (0, 1, 2, or 3) indicating the correct answer
- "explanation": Brief explanation in Thai why this answer is correct

Return ONLY a JSON array or object containing "quiz" list:"""

        try:
            res = await ollama_service.generate(
                prompt=prompt,
                model=self.model,
                temperature=0.2,
                format_json=True
            )
            raw = res.get("response", "").strip()
            data = json.loads(raw)

            if isinstance(data, list) and len(data) > 0:
                return data
            elif isinstance(data, dict):
                for key in ["quiz", "questions", "items", "data"]:
                    if key in data and isinstance(data[key], list) and len(data[key]) > 0:
                        return data[key]
                if "question" in data and "options" in data:
                    return [data]

            # Fallback quiz questions
            return [
                {
                    "question": f"ข้อใดอธิบายหลักการทำงานของ {topic} ได้ถูกต้องที่สุด?",
                    "options": [
                        "เป็นระบบที่รองรับการทำงานแบบ Asynchronous ประสิทธิภาพสูง",
                        "เป็นโปรแกรมจัดการไฟล์เอกสารแบบดั้งเดิม",
                        "เป็นระบบฐานข้อมูลแบบไม่บันทึกความจำ",
                        "เป็นส่วนขยายของระบบปฏิบัติการที่ไม่เกี่ยวกับ AI"
                    ],
                    "correct_index": 0,
                    "explanation": f"{topic} เป็นเทคโนโลยีสมัยใหม่ที่ออกแบบมาเพื่อการประมวลผลที่รวดเร็วและมีประสิทธิภาพสูง"
                }
            ]
        except Exception as e:
            logger.error(f"Quiz generation error: {e}")
            return [
                {
                    "question": f"ข้อใดคือจุดเด่นหลักของ {topic}?",
                    "options": [
                        "ความรวดเร็วและประสิทธิภาพสูง",
                        "การทำงานแบบ Synchronous เท่านั้น",
                        "ไม่รองรับภาษาไทย",
                        "ไม่มีคำตอบที่ถูกต้อง"
                    ],
                    "correct_index": 0,
                    "explanation": "ระบบถูกออกแบบมาเพื่อความเร็วและความสามารถในการขยายตัว"
                }
            ]

study_module = StudyModule()
