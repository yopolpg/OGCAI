import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from app.modules.health import health_module
from app.db.database import AsyncSessionLocal

@pytest.mark.asyncio
async def test_habit_logging_and_streaks():
    async with AsyncSessionLocal() as session:
        habit_title = "ออกกำลังกาย 30 นาที"
        
        # Log past 3 days consecutive
        d1 = (datetime.now().date() - timedelta(days=2)).strftime("%Y-%m-%d")
        d2 = (datetime.now().date() - timedelta(days=1)).strftime("%Y-%m-%d")
        d3 = datetime.now().date().strftime("%Y-%m-%d")

        await health_module.log_habit_entry(session, habit_title, status="completed", date_str=d1)
        await health_module.log_habit_entry(session, habit_title, status="completed", date_str=d2)
        await health_module.log_habit_entry(session, habit_title, status="completed", date_str=d3)
        await session.commit()

        stats = await health_module.get_habit_streaks(session, habit_title)
        assert stats["current_streak"] >= 3
        assert stats["total_completed"] >= 3

def test_daily_routine_generation():
    routine = health_module.generate_daily_routine(
        wake_time="06:30",
        sleep_time="22:30",
        focus_goal="Fullstack Development"
    )
    assert routine["wake_time"] == "06:30"
    assert len(routine["schedule"]) >= 5
    assert "wellness_tips" in routine
