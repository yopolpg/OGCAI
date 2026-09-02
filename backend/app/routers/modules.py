from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.repository import DatabaseRepository
from app.services.sandbox_service import sandbox_service
from app.modules.finance import finance_module
from app.modules.health import health_module
from app.modules.study import study_module

router = APIRouter(prefix="/api/modules", tags=["specialized_modules"])

# ----------------- Request Schemas -----------------
class SandboxExecuteRequest(BaseModel):
    code: str
    timeout: Optional[float] = 5.0

class ChartGenerateRequest(BaseModel):
    chart_type: str  # "line", "bar", "pie", "compound_interest"
    data: Dict[str, Any]
    title: str
    xlabel: Optional[str] = ""
    ylabel: Optional[str] = ""

class FinanceParseRequest(BaseModel):
    text: str

class FinanceAddTransactionRequest(BaseModel):
    type: str = "expense"  # expense, income, saving
    amount: float
    category: str = "general"
    description: Optional[str] = ""
    date: Optional[str] = None

class CompoundInterestRequest(BaseModel):
    principal: float
    monthly_contribution: Optional[float] = 0.0
    annual_rate_pct: float
    years: int

class BudgetRuleRequest(BaseModel):
    monthly_income: float

class HabitLogRequest(BaseModel):
    habit_name: str
    status: Optional[str] = "completed"
    date: Optional[str] = None
    notes: Optional[str] = ""

class RoutineGenerateRequest(BaseModel):
    wake_time: Optional[str] = "07:00"
    sleep_time: Optional[str] = "23:00"
    focus_goal: Optional[str] = "Productive Coding & Health"

class RoadmapGenerateRequest(BaseModel):
    topic: str
    weeks: Optional[int] = 4
    target_level: Optional[str] = "Beginner to Intermediate"

class FlashcardsGenerateRequest(BaseModel):
    content: str
    count: Optional[int] = 5

class QuizGenerateRequest(BaseModel):
    topic: str
    count: Optional[int] = 3

# ================= 1. Sandbox Precision Tool =================
@router.post("/sandbox/execute")
async def execute_python_code(req: SandboxExecuteRequest):
    """Execute Python code in isolated sandbox subprocess."""
    result = sandbox_service.execute_python(code=req.code, timeout=req.timeout or 5.0)
    return result

@router.post("/sandbox/chart")
async def generate_chart(req: ChartGenerateRequest):
    """Generate dark-glass modern chart PNG."""
    result = sandbox_service.generate_dark_chart(
        chart_type=req.chart_type,
        data=req.data,
        title=req.title,
        xlabel=req.xlabel or "",
        ylabel=req.ylabel or ""
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Chart creation failed"))
    return result

# ================= 2. Personal Finance Module =================
@router.post("/finance/parse")
async def parse_finance_text(req: FinanceParseRequest):
    """NLP parsing of natural language text into financial transaction."""
    parsed = finance_module.parse_transaction_text(req.text)
    return parsed

@router.post("/finance/transaction")
async def add_transaction(req: FinanceAddTransactionRequest, db: AsyncSession = Depends(get_db)):
    """Save a financial transaction to SQLite database."""
    from datetime import datetime
    date_str = req.date or datetime.now().strftime("%Y-%m-%d")
    tx = await DatabaseRepository.add_transaction(
        session=db,
        tx_type=req.type,
        amount=req.amount,
        category=req.category,
        description=req.description or "",
        date=date_str
    )
    return {
        "id": tx.id,
        "type": tx.type,
        "amount": tx.amount,
        "category": tx.category,
        "description": tx.description,
        "date": tx.date
    }

@router.get("/finance/summary")
async def get_finance_summary(month: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    """Retrieve monthly financial breakdown, savings rate and chart."""
    summary = await finance_module.get_monthly_summary(session=db, year_month=month)
    return summary

@router.post("/finance/compound-growth")
async def calculate_compound_growth(req: CompoundInterestRequest):
    """Calculate compound growth and generate visual projection chart."""
    result = finance_module.calculate_compound_growth(
        principal=req.principal,
        monthly_contribution=req.monthly_contribution or 0.0,
        annual_rate_pct=req.annual_rate_pct,
        years=req.years
    )
    return result

@router.post("/finance/budget-50-30-20")
async def get_budget_allocation(req: BudgetRuleRequest):
    """Calculate 50/30/20 budget recommendation."""
    result = finance_module.calculate_50_30_20_budget(monthly_income=req.monthly_income)
    return result

# ================= 3. Health & Habits Module =================
@router.get("/health/habits")
async def list_habits(db: AsyncSession = Depends(get_db)):
    """List all saved habit names from database."""
    saved_habits = await DatabaseRepository.list_habit_names(db)
    # Combine default habits with saved habits
    all_habits = list(dict.fromkeys(health_module.default_habits + saved_habits))
    return {"habits": all_habits}

@router.post("/health/habit/log")
async def log_habit(req: HabitLogRequest, db: AsyncSession = Depends(get_db)):
    """Log habit status for today or a specific date."""
    result = await health_module.log_habit_entry(
        session=db,
        habit_name=req.habit_name,
        status=req.status or "completed",
        date_str=req.date,
        notes=req.notes or ""
    )
    return result

@router.get("/health/habit/streaks")
async def get_habit_streaks(habit_name: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Get streak count and 30-day completion rate for a habit."""
    stats = await health_module.get_habit_streaks(session=db, habit_name=habit_name)
    return stats

@router.delete("/health/habit")
async def delete_habit(habit_name: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Delete a habit and all its log history."""
    await DatabaseRepository.delete_habit_logs(db, habit_name)
    return {"status": "deleted", "habit_name": habit_name}

@router.post("/health/routine")
async def generate_daily_routine(req: RoutineGenerateRequest):
    """Generate time-blocking daily routine schedule."""
    routine = health_module.generate_daily_routine(
        wake_time=req.wake_time or "07:00",
        sleep_time=req.sleep_time or "23:00",
        focus_goal=req.focus_goal or "Productive Coding & Health"
    )
    return routine

# ================= 4. Study & Roadmap Module =================
@router.post("/study/roadmap")
async def generate_study_roadmap(req: RoadmapGenerateRequest):
    """Generate milestone skill learning roadmap."""
    roadmap = await study_module.generate_skill_roadmap(
        topic=req.topic,
        total_weeks=req.weeks or 4,
        target_level=req.target_level or "Beginner to Intermediate"
    )
    return roadmap

@router.post("/study/flashcards")
async def generate_study_flashcards(req: FlashcardsGenerateRequest):
    """Generate Q&A flashcards for spaced repetition."""
    flashcards = await study_module.generate_flashcards(
        content_or_topic=req.content,
        count=req.count or 5
    )
    return {"flashcards": flashcards, "total": len(flashcards)}

@router.post("/study/quiz")
async def generate_study_quiz(req: QuizGenerateRequest):
    """Generate multiple choice quiz questions with answer explanations."""
    quiz = await study_module.generate_quiz(topic=req.topic, count=req.count or 3)
    return {"quiz": quiz, "total": len(quiz)}
