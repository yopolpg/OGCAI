import pytest
import pytest_asyncio
from app.modules.finance import finance_module
from app.db.database import AsyncSessionLocal
from app.db.repository import DatabaseRepository

def test_nlp_transaction_parsing():
    # 1. Expense parsing
    p1 = finance_module.parse_transaction_text("จ่ายค่ากาแฟสตาร์บัคส์ 185 บาท")
    assert p1["type"] == "expense"
    assert p1["amount"] == 185.0
    assert p1["category"] == "food"

    # 2. Income parsing
    p2 = finance_module.parse_transaction_text("เงินเดือนเข้า 55,000 บาท")
    assert p2["type"] == "income"
    assert p2["amount"] == 55000.0
    assert p2["category"] == "salary"

    # 3. Saving parsing
    p3 = finance_module.parse_transaction_text("ซื้อกองทุนรวมออมเงิน 10000")
    assert p3["type"] == "saving"
    assert p3["amount"] == 10000.0
    assert p3["category"] == "investment"

def test_50_30_20_budget_calculation():
    budget = finance_module.calculate_50_30_20_budget(monthly_income=50000.0)
    assert budget["needs_50_pct"] == 25000.0
    assert budget["wants_30_pct"] == 15000.0
    assert budget["savings_20_pct"] == 10000.0
    assert "chart" in budget
    assert budget["chart"]["success"] is True

@pytest.mark.asyncio
async def test_monthly_summary_aggregation():
    async with AsyncSessionLocal() as session:
        # Add test transactions
        await DatabaseRepository.add_transaction(session, "income", 60000.0, "salary", "เงินเดือน", "2026-08-01")
        await DatabaseRepository.add_transaction(session, "expense", 12000.0, "bills", "ค่าคอนโด", "2026-08-05")
        await DatabaseRepository.add_transaction(session, "expense", 8500.0, "food", "ค่าอาหาร", "2026-08-10")
        await DatabaseRepository.add_transaction(session, "saving", 15000.0, "investment", "DCA หุ้น", "2026-08-15")
        await session.commit()

        summary = await finance_module.get_monthly_summary(session, year_month="2026-08")
        assert summary["total_income"] >= 60000.0
        assert summary["total_expense"] >= 20500.0
        assert summary["total_saving"] >= 15000.0
        assert summary["savings_rate_pct"] > 0
