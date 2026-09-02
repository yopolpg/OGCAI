import re
import logging
from typing import Optional, List, Tuple
from app.config import settings
from app.schemas.chat import RouteDecision
from app.services.ollama_service import ollama_service

logger = logging.getLogger("ogcai.router_service")

class RouterService:
    def __init__(self):
        # Tier 1 Regex Patterns
        self.advisor_patterns = [
            r"ปรึกษา", r"ชีวิต", r"สุขภาพจิต", r"กำลังใจ", r"เหนื่อย", r"เครียด",
            r"ความสัมพันธ์", r"เป้าหมายชีวิต", r"ปรัชญา", r"จิตวิทยา", r"อารมณ์",
            r"mindset", r"habit", r"routine", r"life advice", r"coaching",
            r"feeling", r"motivation", r"meditation", r"wellbeing", r"burnout",
            r"ดูแลตัวเอง", r"ตารางเวลาชีวิต", r"ปรับทัศนคติ"
        ]
        
        self.heavy_logic_patterns = [
            r"คำนวณ.*(สูตร|ดอกเบี้ย|แคลคูลัส|สถิติ|สมการ|อนุพันธ์|อินทิกรัล)",
            r"ดอกเบี้ยทบต้น", r"algorithm", r"data structure", r"deep logic",
            r"optimize.*code", r"refactor.*architecture", r"complex regex",
            r"sql optimization", r"matrix multiplication", r"eigenvalue",
            r"linear programming", r"dynamic programming", r"ast analysis",
            r"ความซับซ้อนเชิงเวลา", r"time complexity", r"big o notation",
            r"พิสูจน์.*ทางคณิตศาสตร์", r"คณิตศาสตร์ขั้นสูง"
        ]
        
        self.code_math_symbols = [
            r"```[a-zA-Z0-9_\-]+", r"\bdef\s+[a-zA-Z_]", r"\bclass\s+[a-zA-Z_]",
            r"\bfunction\s+[a-zA-Z_]", r"\bSELECT\s+.+\s+FROM\b",
            r"\\int|\\sum|\\frac|\\partial|\\sqrt"
        ]

    def _tier1_rule_match(self, text: str) -> Optional[Tuple[str, str, str, float]]:
        """
        Tier 1 Rule-based Regex Matching (0ms latency).
        Returns (model_name, category, reason, confidence) if matched, else None.
        """
        lower_text = text.lower()
        
        # 1. Check Heavy Logic / Complex Coding & Math
        for pattern in self.heavy_logic_patterns:
            if re.search(pattern, lower_text, re.IGNORECASE):
                return (
                    settings.HEAVY_LOGIC_MODEL,
                    "heavy_logic",
                    f"Tier 1 Match: ตรวจพบโจทย์เชิงตรรกะ/คณิตศาสตร์ขั้นสูง ('{pattern}')",
                    0.95
                )
                
        # Check code/math symbols
        for pattern in self.code_math_symbols:
            if re.search(pattern, text):
                return (
                    settings.HEAVY_LOGIC_MODEL,
                    "heavy_logic",
                    f"Tier 1 Match: ตรวจพบโครงสร้างโค้ดหรือสัญลักษณ์สูตรเฉพาะ ('{pattern}')",
                    0.90
                )

        # 2. Check Advisor / Life Coaching / Philosophy / Mental Health
        for pattern in self.advisor_patterns:
            if re.search(pattern, lower_text, re.IGNORECASE):
                return (
                    settings.ADVISOR_MODEL,
                    "advisor",
                    f"Tier 1 Match: ตรวจพบหัวข้อคำปรึกษา/เป้าหมายชีวิต/สุขภาพ ('{pattern}')",
                    0.90
                )

        return None

    async def _tier2_fast_classifier(self, text: str) -> Tuple[str, str, str, float]:
        """
        Tier 2 Lightweight AI Classification using fast qwen2.5:3b (~50-100ms).
        """
        classifier_prompt = f"""Classify the user intent into exactly ONE category:
- ADVISOR: Personal life advice, mental health, habit planning, philosophy, emotional support.
- HEAVY_LOGIC: Advanced mathematics, algorithm design, heavy logic puzzles, complex code debugging.
- GENERAL: Everyday conversation, general Thai questions, factual queries, writing, translation, general coding.

User message: "{text[:300]}"

Respond ONLY with the category name (ADVISOR, HEAVY_LOGIC, or GENERAL):"""

        try:
            res = await ollama_service.generate(
                prompt=classifier_prompt,
                model=settings.FAST_WORKER_MODEL,
                temperature=0.1
            )
            raw_output = res.get("response", "").strip().upper()
            
            if "HEAVY_LOGIC" in raw_output:
                return (
                    settings.HEAVY_LOGIC_MODEL,
                    "heavy_logic",
                    "Tier 2 Fast AI: จำแนกเป็นหมวดหมู่งานตรรกะ/คณิตศาสตร์เชิงลึก",
                    0.85
                )
            elif "ADVISOR" in raw_output:
                return (
                    settings.ADVISOR_MODEL,
                    "advisor",
                    "Tier 2 Fast AI: จำแนกเป็นหมวดหมู่คำปรึกษาและการวางแผนชีวิต",
                    0.85
                )
            else:
                return (
                    settings.DEFAULT_MODEL,
                    "general",
                    "Tier 2 Fast AI: จำแนกเป็นหมวดหมู่การสนทนาและงานประจำวันทั่วไป",
                    0.80
                )
        except Exception as e:
            logger.warning(f"Tier 2 classification failed, falling back to default: {e}")
            return (
                settings.DEFAULT_MODEL,
                "general",
                "Fallback: ใช้โมเดลมาตรฐานเนื่องจากระบบ Fast AI ขัดข้อง",
                0.70
            )

    async def route_message(self, message: str, manual_model: Optional[str] = None) -> RouteDecision:
        """
        Select the optimal model for a message.
        Supports Manual Override, Tier 1 Regex Matrix, and Tier 2 Fast AI Classifier.
        """
        # 1. Manual Override Mode
        if manual_model and manual_model.strip():
            target_model = manual_model.strip()
            return RouteDecision(
                selected_model=target_model,
                routing_mode="manual",
                intent_category="general",
                reason=f"Manual Override: ผู้ใช้กำหนดโมเดลเป็น '{target_model}' โดยตรง",
                confidence=1.0,
                tier_used="manual_override"
            )

        # 2. Tier 1 Regex Rule Match (~0ms)
        tier1_result = self._tier1_rule_match(message)
        if tier1_result:
            model_name, category, reason, confidence = tier1_result
            return RouteDecision(
                selected_model=model_name,
                routing_mode="auto",
                intent_category=category, # type: ignore
                reason=reason,
                confidence=confidence,
                tier_used="tier1_regex"
            )

        # 3. Tier 2 Fast AI Classifier (~50-100ms)
        # If the message is short and simple, use Default directly to save latency
        if len(message.strip()) <= 30:
            return RouteDecision(
                selected_model=settings.DEFAULT_MODEL,
                routing_mode="auto",
                intent_category="general",
                reason="Default Auto: ข้อความสั้น/สนทนาทั่วไป ตอบสนองรวดเร็วด้วยโมเดลหลัก",
                confidence=0.90,
                tier_used="tier1_regex"
            )

        # Run Tier 2 Classifier
        model_name, category, reason, confidence = await self._tier2_fast_classifier(message)
        return RouteDecision(
            selected_model=model_name,
            routing_mode="auto",
            intent_category=category, # type: ignore
            reason=reason,
            confidence=confidence,
            tier_used="tier2_classifier"
        )

router_service = RouterService()
