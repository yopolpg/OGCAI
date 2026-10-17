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
        Generate an optimized dynamic daily time-blocking schedule based on user wake/sleep times and goals.
        """
        def parse_mins(t_str: str) -> int:
            try:
                parts = t_str.strip().split(":")
                return int(parts[0]) * 60 + int(parts[1])
            except Exception:
                return 7 * 60

        def fmt_mins(m: int) -> str:
            m = m % 1440
            return f"{m // 60:02d}:{m % 60:02d}"

        wake_m = parse_mins(wake_time)
        sleep_m = parse_mins(sleep_time)
        
        # Calculate awake duration in minutes
        awake_m = (sleep_m - wake_m) if sleep_m > wake_m else (1440 - wake_m + sleep_m)
        if awake_m < 360:  # Safety check: at least 6 hours awake
            awake_m = 960  # default 16 hours
            sleep_m = (wake_m + awake_m) % 1440

        schedule = []
        cur = wake_m

        if workout_slot == "morning":
            # Morning workout path
            t_workout = min(45, int(awake_m * 0.05))
            schedule.append({
                "time": f"{fmt_mins(cur)} - {fmt_mins(cur + t_workout)}",
                "activity": f"🏃 Morning Workout & Hydration: ออกกำลังกาย 30-40 นาที + ดื่มน้ำ 1 แก้วใหญ่",
                "energy": "High"
            })
            cur += t_workout

            t_prep = min(45, int(awake_m * 0.05))
            schedule.append({
                "time": f"{fmt_mins(cur)} - {fmt_mins(cur + t_prep)}",
                "activity": f"🍳 อาหารเช้าโปรตีนสูง & จัดลำดับ 3 งานสำคัญประจำวัน ({focus_goal})",
                "energy": "High"
            })
            cur += t_prep
        else:
            # Morning wake & light stretch path
            t_wake = min(30, int(awake_m * 0.04))
            schedule.append({
                "time": f"{fmt_mins(cur)} - {fmt_mins(cur + t_wake)}",
                "activity": f"☀️ ตื่นนอน ดื่มน้ำ 1 แก้วใหญ่ ยืดเหยียดร่างกาย รับแสงแดดยามเช้า",
                "energy": "Medium"
            })
            cur += t_wake

            t_prep = min(60, int(awake_m * 0.06))
            schedule.append({
                "time": f"{fmt_mins(cur)} - {fmt_mins(cur + t_prep)}",
                "activity": f"🍳 อาหารเช้า & วางแผนเป้าหมาย Focus: {focus_goal}",
                "energy": "High"
            })
            cur += t_prep

        # Deep Work Block 1
        t_work1 = max(120, int(awake_m * 0.22))
        schedule.append({
            "time": f"{fmt_mins(cur)} - {fmt_mins(cur + t_work1)}",
            "activity": f"🚀 Deep Work Block #1: โฟกัสสูงสุดกับ {focus_goal} (ตัดสิ่งรบกวน, เทคนิค Pomodoro)",
            "energy": "Peak"
        })
        cur += t_work1

        # Lunch Break
        t_lunch = min(60, int(awake_m * 0.06))
        schedule.append({
            "time": f"{fmt_mins(cur)} - {fmt_mins(cur + t_lunch)}",
            "activity": f"🥗 อาหารกลางวัน & พักสายตา ผ่อนคลายสมอง (งดทำงานหน้าจอ)",
            "energy": "Medium"
        })
        cur += t_lunch

        # Deep Work Block 2
        t_work2 = max(120, int(awake_m * 0.20))
        schedule.append({
            "time": f"{fmt_mins(cur)} - {fmt_mins(cur + t_work2)}",
            "activity": f"💻 Deep Work Block #2: งานวิเคราะห์และพัฒนา ({focus_goal})",
            "energy": "Medium-High"
        })
        cur += t_work2

        # Evening workout if scheduled for evening
        if workout_slot != "morning":
            t_workout_eve = min(60, int(awake_m * 0.07))
            schedule.append({
                "time": f"{fmt_mins(cur)} - {fmt_mins(cur + t_workout_eve)}",
                "activity": f"🏋️ Workout & Cardio: ออกกำลังกาย 45 นาที วิ่ง/บอดี้เวท ผ่อนคลายความเครียด",
                "energy": "High"
            })
            cur += t_workout_eve

        # Dinner
        t_dinner = min(60, int(awake_m * 0.07))
        schedule.append({
            "time": f"{fmt_mins(cur)} - {fmt_mins(cur + t_dinner)}",
            "activity": f"🍲 อาหารเย็นเบาๆ สังสรรค์และพักผ่อนกับครอบครัว/กิจกรรมที่ชอบ",
            "energy": "Medium"
        })
        cur += t_dinner

        # Skill Growth & Personal Review
        remaining_before_winddown = max(45, (sleep_m - cur - 60) if sleep_m > cur else 60)
        schedule.append({
            "time": f"{fmt_mins(cur)} - {fmt_mins(cur + remaining_before_winddown)}",
            "activity": f"📚 Personal Growth & Review: ทบทวน Flashcards, สรุปสิ่งที่ได้เรียนรู้วันนี้",
            "energy": "Medium-High"
        })
        cur += remaining_before_winddown

        # Wind-down
        schedule.append({
            "time": f"{fmt_mins(cur)} - {fmt_mins(sleep_m)}",
            "activity": f"🌙 Wind-down Routine & Sleep Prep: ปิดหน้าจอแสงสีฟ้า นั่งสมาธิหรืออ่านหนังสือ พร้อมนอนที่ {sleep_time}",
            "energy": "Rest"
        })

        return {
            "wake_time": wake_time,
            "sleep_time": sleep_time,
            "focus_goal": focus_goal,
            "schedule": schedule,
            "wellness_tips": [
                "ดื่มน้ำอย่างน้อย 500ml ทันทีหลังตื่นนอนเพื่อกระตุ้นระบบเผาผลาญ",
                "ใช้เทคนิค Pomodoro (50 นาทีทำงาน / 10 นาทีพักสายตา)",
                "งดคาเฟอีนล่วงหน้าอย่างน้อย 6-8 ชั่วโมงก่อนเวลานอนเพื่อคุณภาพการนอนหลับลึก (Deep Sleep)"
            ]
        }

health_module = HealthModule()
