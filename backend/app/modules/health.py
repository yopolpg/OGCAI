import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import HabitLog
from app.db.repository import DatabaseRepository
from app.services.sandbox_service import sandbox_service

logger = logging.getLogger("ogcai.health_module")

class HealthModule:
    def __init__(self):
        self.default_habits = [
            "ดื่มน้ำ 2-3 ลิตร",
            "ออกกำลังกาย 30 นาที",
            "อ่านหนังสือ/เรียนรู้ทักษะ 20 นาที",
            "เดิน 8,000 ก้าว",
            "เข้านอนก่อน 23:00"
        ]

    async def log_habit_entry(
        self,
        session: AsyncSession,
        habit_name: str,
        status: str = "completed",
        date_str: Optional[str] = None,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Log a habit completion status for a specific date."""
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        # Check if already logged today
        stmt = select(HabitLog).where(HabitLog.habit_name == habit_name, HabitLog.date == date_str)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.status = status
            existing.notes = notes
            await session.flush()
            habit = existing
        else:
            habit = await DatabaseRepository.log_habit(
                session=session,
                habit_name=habit_name,
                date=date_str,
                status=status,
                notes=notes
            )
        
        return {
            "id": habit.id,
            "habit_name": habit.habit_name,
            "date": habit.date,
            "status": habit.status,
            "notes": habit.notes
        }

    async def get_habit_streaks(self, session: AsyncSession, habit_name: str) -> Dict[str, Any]:
        """
        Calculate consecutive streak and completion rate for a given habit.
        """
        stmt = select(HabitLog).where(HabitLog.habit_name == habit_name).order_by(desc(HabitLog.date))
        result = await session.execute(stmt)
        logs = list(result.scalars().all())

        if not logs:
            return {
                "habit_name": habit_name,
                "current_streak": 0,
                "total_completed": 0,
                "completion_rate_30d_pct": 0.0,
                "history": []
            }

        log_dict = {l.date: l.status for l in logs}
        
        # Calculate Current Streak
        current_streak = 0
        check_date = datetime.now().date()
        
        # If today is not logged yet, check starting from yesterday
        today_str = check_date.strftime("%Y-%m-%d")
        if today_str not in log_dict or log_dict[today_str] != "completed":
            check_date -= timedelta(days=1)

        while True:
            d_str = check_date.strftime("%Y-%m-%d")
            if log_dict.get(d_str) == "completed":
                current_streak += 1
                check_date -= timedelta(days=1)
            else:
                break

        # Calculate 30-Day Completion Rate
        start_30d = (datetime.now().date() - timedelta(days=30)).strftime("%Y-%m-%d")
        logs_30d = [l for l in logs if l.date >= start_30d]
        completed_30d = sum(1 for l in logs_30d if l.status == "completed")
        rate_30d = round((completed_30d / 30) * 100, 1)

        total_completed = sum(1 for l in logs if l.status == "completed")

        return {
            "habit_name": habit_name,
            "current_streak": current_streak,
            "total_completed": total_completed,
            "completed_last_30d": completed_30d,
            "completion_rate_30d_pct": rate_30d,
            "history": [{"date": l.date, "status": l.status} for l in logs[:14]]
        }

    def generate_daily_routine(
        self,
        wake_time: str = "07:00",
        sleep_time: str = "23:00",
        workout_slot: str = "evening",  # "morning" or "evening"
        focus_goal: str = "Productive Coding & Health"
    ) -> Dict[str, Any]:
        """
        Generate an optimized daily time-blocking schedule based on chronotype and goals.
        """
        routine_schedule = [
            {"time": "07:00 - 07:30", "activity": "☀️ ตื่นนอน ดื่มน้ำ 1 แก้วใหญ่ ยืดเหยียดร่างกาย รับแสงแดดยามเช้า", "energy": "Medium"},
            {"time": "07:30 - 08:30", "activity": "🍳 ทานมื้อเช้าที่มีโปรตีนสูง + วางแผน To-Do 3 อย่างสำคัญของวัน", "energy": "High"},
            {"time": "08:30 - 12:00", "activity": "🚀 Deep Work Block #1: โฟกัสงานยาก งานตรรกะ หรือการเขียนโค้ด (ปิดเสียงแจ้งเตือน)", "energy": "Peak"},
            {"time": "12:00 - 13:00", "activity": "🥗 ทานมื้อเที่ยงที่มีสารอาหารครบถ้วน + พักสายตา เดินย่อย 15 นาที", "energy": "Medium"},
            {"time": "13:00 - 16:30", "activity": "💻 Deep Work Block #2: งานประสานงาน แก้ไขปัญหา หรือประชุม", "energy": "Medium-High"},
            {"time": "16:30 - 17:30", "activity": "🏋️ Workout & Cardio: ออกกำลังกาย 30-45 นาที หรือเดินเร็ว", "energy": "High"},
            {"time": "17:30 - 19:00", "activity": "🍲 ทานมื้อเย็น + พักผ่อน สังสรรค์กับครอบครัวหรือเพื่อน", "energy": "Medium"},
            {"time": "19:00 - 21:00", "activity": "📚 Study & Skill Up: อ่านหนังสือ, ศึกษาเทคโนโลยีใหม่, ทบทวน Flashcards", "energy": "High"},
            {"time": "21:00 - 22:30", "activity": "🧘 Wind-down Routine: ลดการใช้จอมือถือ/แสงสีฟ้า, ฟังเพลงสบายๆ, จดบันทึก Journal", "energy": "Low"},
            {"time": "22:30 - 23:00", "activity": "🌙 เตรียมตัวนอน ห้องมืดและเย็น เพื่อการหลับลึกอย่างมีคุณภาพ", "energy": "Rest"}
        ]

        return {
            "wake_time": wake_time,
            "sleep_time": sleep_time,
            "focus_goal": focus_goal,
            "schedule": routine_schedule,
            "wellness_tips": [
                "ดื่มน้ำอย่างน้อย 500ml ทันทีหลังตื่นนอนเพื่อกระตุ้นระบบเผาผลาญ",
                "ใช้เทคนิค Pomodoro (50 นาทีทำงาน / 10 นาทีพักสายตา)",
                "งดคาเฟอีนหลัง 14:00 เพื่อคุณภาพการนอนหลับลึก (Deep Sleep)"
            ]
        }

health_module = HealthModule()
