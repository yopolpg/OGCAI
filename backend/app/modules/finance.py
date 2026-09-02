import re
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import FinanceTransaction
from app.services.sandbox_service import sandbox_service

logger = logging.getLogger("ogcai.finance_module")

class FinanceModule:
    def __init__(self):
        # Category Mapping Keywords
        self.category_keywords = {
            "food": ["กาแฟ", "ข้าว", "อาหาร", "กิน", "ส้มตำ", "บุฟเฟต์", "ชาเขียว", "ขนม", "มื้อเย็น", "มื้อเที่ยง", "delivery", "food"],
            "transport": ["น้ำมัน", "bts", "mrt", "แท็กซี่", "grab", "ค่ารถ", "ทางด่วน", "ที่จอดรถ", "ตั๋วเครื่องบิน", "transport"],
            "bills": ["ค่าเน็ต", "ค่าไฟ", "ค่าน้ำ", "ค่าโทรศัพท์", "ค่าคอนโด", "ค่าเช่า", "ประกัน", "ค่าบัตร", "utilities", "bills"],
            "shopping": ["ซื้อของ", "เสื้อผ้า", "shopee", "lazada", "ห้าง", "ของใช้", "เครื่องสำอาง", "shopping"],
            "entertainment": ["ดูหนัง", "เกม", "netflix", "spotify", "เที่ยว", "สังสรรค์", "entertainment"],
            "salary": ["เงินเดือน", "โบนัส", "รายได้", "รับจ้าง", "freelance", "ปันผล", "กำไร", "salary", "income"],
            "investment": ["ซื้อกองทุน", "หุ้น", "crypto", "ทองคำ", "ออมเงิน", "ฝากประจำ", "investment", "saving"]
        }

    def parse_transaction_text(self, text: str) -> Dict[str, Any]:
        """
        Parse natural language expense/income in Thai or English into structured transaction data.
        Example: 'จ่ายค่ากาแฟ 65 บาท' -> {'type': 'expense', 'amount': 65.0, 'category': 'food', 'description': 'ค่ากาแฟ'}
        """
        cleaned_text = text.strip()
        
        # 1. Extract Amount (handles commas like 1,500.50)
        amount_match = re.search(r"(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:บาท|฿|k|บ\.)?", cleaned_text)
        amount = 0.0
        if amount_match:
            raw_amt = amount_match.group(1).replace(",", "")
            try:
                amount = float(raw_amt)
            except ValueError:
                amount = 0.0

        # 2. Determine Transaction Type (income, saving, expense)
        tx_type = "expense"
        if any(w in cleaned_text for w in ["เงินเดือน", "ได้เงิน", "รายรับ", "โอนเข้า", "รับเงิน", "รายได้", "ปันผล", "income", "salary"]):
            tx_type = "income"
        elif any(w in cleaned_text for w in ["ออมเงิน", "ฝากเงิน", "เก็บเงิน", "ซื้อกองทุน", "saving", "invest"]):
            tx_type = "saving"

        # 3. Determine Category
        category = "general"
        for cat, keywords in self.category_keywords.items():
            if any(kw in cleaned_text.lower() for kw in keywords):
                category = cat
                break

        # 4. Extract Description
        description = cleaned_text
        # Strip common trailing tags
        description = re.sub(r"\s*\d+(?:,\d+)*(?:\.\d+)?\s*(?:บาท|฿|k|บ\.)?", "", description).strip()
        if not description:
            description = f"รายการ {category}"

        today_str = datetime.now().strftime("%Y-%m-%d")

        return {
            "type": tx_type,
            "amount": amount,
            "category": category,
            "description": description,
            "date": today_str
        }

    async def get_monthly_summary(self, session: AsyncSession, year_month: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate financial summary for a given month (YYYY-MM).
        """
        if not year_month:
            year_month = datetime.now().strftime("%Y-%m")

        stmt = select(FinanceTransaction).where(FinanceTransaction.date.startswith(year_month))
        result = await session.execute(stmt)
        transactions = list(result.scalars().all())

        total_income = 0.0
        total_expense = 0.0
        total_saving = 0.0
        category_breakdown: Dict[str, float] = {}

        for tx in transactions:
            if tx.type == "income":
                total_income += tx.amount
            elif tx.type == "saving":
                total_saving += tx.amount
            else:
                total_expense += tx.amount
                category_breakdown[tx.category] = category_breakdown.get(tx.category, 0.0) + tx.amount

        net_balance = total_income - total_expense - total_saving
        savings_rate = round(((total_saving + max(0, net_balance)) / total_income * 100), 1) if total_income > 0 else 0.0

        # Generate Expense Breakdown Pie Chart if there are expenses
        chart_info = None
        if category_breakdown:
            chart_info = sandbox_service.generate_dark_chart(
                chart_type="pie",
                data={
                    "labels": list(category_breakdown.keys()),
                    "values": list(category_breakdown.values())
                },
                title=f"สัดส่วนค่าใช้จ่ายประจำเดือน ({year_month})"
            )

        return {
            "month": year_month,
            "total_transactions": len(transactions),
            "total_income": round(total_income, 2),
            "total_expense": round(total_expense, 2),
            "total_saving": round(total_saving, 2),
            "net_balance": round(net_balance, 2),
            "savings_rate_pct": savings_rate,
            "category_breakdown": {k: round(v, 2) for k, v in category_breakdown.items()},
            "chart": chart_info
        }

    def calculate_compound_growth(
        self,
        principal: float,
        monthly_contribution: float,
        annual_rate_pct: float,
        years: int
    ) -> Dict[str, Any]:
        """
        Simulate compound interest and generate a visual growth chart.
        """
        calc_result = sandbox_service.calculate_compound_interest(
            principal=principal,
            monthly_contribution=monthly_contribution,
            annual_rate_pct=annual_rate_pct,
            years=years
        )

        chart_info = sandbox_service.generate_dark_chart(
            chart_type="compound_interest",
            data=calc_result["yearly_breakdown"],
            title=f"แผนจำลองการเติบโตของเงินทุน ({years} ปี, ผลตอบแทน {annual_rate_pct}% ต่อปี)",
            xlabel="ระยะเวลา (ปี)",
            ylabel="มูลค่าพอร์ตสะสม (บาท)"
        )

        calc_result["chart"] = chart_info
        return calc_result

    def calculate_50_30_20_budget(self, monthly_income: float) -> Dict[str, Any]:
        """
        Calculate 50/30/20 Budgeting rule breakdown.
        """
        needs = monthly_income * 0.50
        wants = monthly_income * 0.30
        savings = monthly_income * 0.20

        chart_info = sandbox_service.generate_dark_chart(
            chart_type="bar",
            data={
                "labels": ["สิ่งที่จำเป็น (Needs 50%)", "ความต้องการ (Wants 30%)", "เงินออม/ลงทุน (Savings 20%)"],
                "values": [needs, wants, savings]
            },
            title="การจัดสรรงบประมาณตามหลัก 50/30/20 Rule",
            ylabel="จำนวนเงิน (บาท)"
        )

        return {
            "monthly_income": monthly_income,
            "needs_50_pct": round(needs, 2),
            "wants_30_pct": round(wants, 2),
            "savings_20_pct": round(savings, 2),
            "recommendations": {
                "needs": "ค่าใช้จ่ายจำเป็น: ค่าเช่า/ผ่อนบ้าน, ค่าน้ำไฟ, ค่าเน็ต, อาหารมื้อหลัก, ประกันสุขภาพ, ค่าเดินทาง",
                "wants": "ความสุขส่วนตัว: ทานอาหารนอกบ้าน, ช้อปปิ้ง, กิจกรรมพักผ่อน, ดูหนัง, ของเล่น/งานอดิเรก",
                "savings": "สร้างความมั่งคั่ง: กองทุนสำรองฉุกเฉิน 6 เดือน, DCA กองทุนรวม/หุ้น, ฝากประจำ, เงินออมเพื่อเกษียณ"
            },
            "chart": chart_info
        }

finance_module = FinanceModule()
