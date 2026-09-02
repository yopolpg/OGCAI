import React, { useState, useEffect } from 'react';
import { Activity, CheckCircle2, Flame, Clock, Plus, Trash2, Sparkles, RefreshCw, Sun, Moon, Target } from 'lucide-react';
import { api } from '../../services/api';
import { DailyRoutineData, HabitStreakData } from '../../types';

export const HealthTab: React.FC = () => {
  const [habits, setHabits] = useState<string[]>([
    "ดื่มน้ำ 2-3 ลิตร",
    "ออกกำลังกาย 30 นาที",
    "อ่านหนังสือ/เรียนรู้ 20 นาที",
    "เดิน 8,000 ก้าว",
    "เข้านอนก่อน 23:00"
  ]);
  const [habitStreaks, setHabitStreaks] = useState<Record<string, HabitStreakData>>({});
  const [newHabit, setNewHabit] = useState('');
  const [loadingHabits, setLoadingHabits] = useState(false);

  // Daily Routine State
  const [wakeTime, setWakeTime] = useState('07:00');
  const [sleepTime, setSleepTime] = useState('23:00');
  const [focusGoal, setFocusGoal] = useState('เขียนโปรแกรม & สุขภาพ');
  const [routine, setRoutine] = useState<DailyRoutineData | null>(null);
  const [loadingRoutine, setLoadingRoutine] = useState(false);

  const getTodayDateString = () => {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const loadAllHabits = async () => {
    setLoadingHabits(true);
    try {
      // 1. Fetch distinct habit names
      const res = await api.getHabitsList();
      const habitList = res.habits && res.habits.length > 0 ? res.habits : habits;
      setHabits(habitList);

      // 2. Fetch streaks for each habit
      const streakMap: Record<string, HabitStreakData> = {};
      for (const h of habitList) {
        try {
          const stats = await api.getHabitStreaks(h);
          streakMap[h] = stats;
        } catch (e) {
          // ignore
        }
      }
      setHabitStreaks(streakMap);
    } catch (e) {
      console.error('Failed to load habits:', e);
    } finally {
      setLoadingHabits(false);
    }
  };

  useEffect(() => {
    loadAllHabits();

    // Load saved routine from localStorage
    const savedRoutine = localStorage.getItem('ogcai_daily_routine');
    if (savedRoutine) {
      try {
        setRoutine(JSON.parse(savedRoutine));
      } catch (e) {
        // ignore
      }
    }
  }, []);

  const handleToggleHabit = async (habitName: string) => {
    const todayStr = getTodayDateString();
    const current = habitStreaks[habitName];
    const todayLog = current?.history?.find((h) => h.date === todayStr);
    const isCompletedToday = todayLog ? todayLog.status === 'completed' : false;

    // Optimistic UI Update
    const newStatus = isCompletedToday ? 'missed' : 'completed';
    try {
      await api.logHabit({
        habit_name: habitName,
        status: newStatus,
        date: todayStr
      });
      // Refresh streaks
      const updatedStats = await api.getHabitStreaks(habitName);
      setHabitStreaks((prev) => ({ ...prev, [habitName]: updatedStats }));
    } catch (e) {
      console.error('Failed to toggle habit:', e);
    }
  };

  const handleAddHabit = async () => {
    if (!newHabit.trim()) return;
    const habitName = newHabit.trim();
    if (!habits.includes(habitName)) {
      try {
        // Log initial creation for today
        await api.logHabit({
          habit_name: habitName,
          status: 'missed',
          date: getTodayDateString()
        });
        setHabits([...habits, habitName]);
        setNewHabit('');
        const stats = await api.getHabitStreaks(habitName);
        setHabitStreaks((prev) => ({ ...prev, [habitName]: stats }));
      } catch (e) {
        console.error('Failed to add habit:', e);
      }
    }
  };

  const handleDeleteHabit = async (habitName: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.deleteHabit(habitName);
      setHabits(habits.filter((h) => h !== habitName));
      const newMap = { ...habitStreaks };
      delete newMap[habitName];
      setHabitStreaks(newMap);
    } catch (e) {
      console.error('Failed to delete habit:', e);
    }
  };

  const handleGenerateRoutine = async () => {
    setLoadingRoutine(true);
    try {
      const data = await api.generateDailyRoutine({
        wake_time: wakeTime,
        sleep_time: sleepTime,
        focus_goal: focusGoal
      });
      setRoutine(data);
      localStorage.setItem('ogcai_daily_routine', JSON.stringify(data));
    } catch (e) {
      console.error('Failed to generate routine:', e);
    } finally {
      setLoadingRoutine(false);
    }
  };

  const todayStr = getTodayDateString();

  return (
    <div className="space-y-4 text-xs overflow-y-auto pr-1 h-full">
      {/* 1. Habit Tracker Section */}
      <div className="glass-card p-3.5 rounded-xl border border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <Activity className="w-4 h-4 text-emerald-400" />
            <p className="font-semibold text-slate-200">Habit Tracker (เช็คพฤติกรรมวันนี้)</p>
          </div>
          <button
            onClick={loadAllHabits}
            className="text-slate-400 hover:text-cyan-300 p-1"
            title="รีเฟรชข้อมูล"
          >
            <RefreshCw className={`w-3 h-3 ${loadingHabits ? 'animate-spin' : ''}`} />
          </button>
        </div>

        <div className="space-y-1.5">
          {habits.map((habit) => {
            const streakData = habitStreaks[habit];
            const todayLog = streakData?.history?.find((h) => h.date === todayStr);
            const isDoneToday = todayLog ? todayLog.status === 'completed' : false;
            const streakCount = streakData?.current_streak || 0;

            return (
              <div
                key={habit}
                onClick={() => handleToggleHabit(habit)}
                className={`group flex items-center justify-between p-2.5 rounded-xl cursor-pointer transition-all ${
                  isDoneToday
                    ? 'bg-emerald-950/40 border border-emerald-500/40 text-emerald-100 shadow-sm'
                    : 'bg-slate-900/60 border border-slate-800/80 text-slate-300 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center gap-2.5 flex-1 min-w-0">
                  <CheckCircle2
                    className={`w-4 h-4 flex-shrink-0 transition-colors ${
                      isDoneToday ? 'text-emerald-400 fill-emerald-500/20' : 'text-slate-600 group-hover:text-slate-400'
                    }`}
                  />
                  <span className={`truncate text-xs ${isDoneToday ? 'line-through text-slate-400 font-medium' : 'font-medium'}`}>
                    {habit}
                  </span>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  {/* Streak Badge */}
                  <div
                    className={`flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                      streakCount > 0
                        ? 'text-amber-300 bg-amber-950/50 border-amber-800/50'
                        : 'text-slate-500 bg-slate-800/40 border-slate-700/40'
                    }`}
                    title={`ต่อเนื่อง ${streakCount} วัน (สำเร็จ ${streakData?.completion_rate_30d_pct || 0}% ใน 30 วัน)`}
                  >
                    <Flame className={`w-3 h-3 ${streakCount > 0 ? 'text-amber-400' : 'text-slate-500'}`} />
                    <span>{streakCount} วัน</span>
                  </div>

                  {/* Delete Habit Button */}
                  <button
                    onClick={(e) => handleDeleteHabit(habit, e)}
                    className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-rose-400 transition-opacity"
                    title="ลบนิสัยนี้"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Add Habit Input */}
        <div className="flex gap-1.5 pt-1">
          <input
            type="text"
            placeholder="เพิ่มเป้าหมายนิสัยใหม่..."
            value={newHabit}
            onChange={(e) => setNewHabit(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAddHabit()}
            className="flex-1 glass-input px-2.5 py-1.5 rounded-lg text-xs"
          />
          <button
            onClick={handleAddHabit}
            disabled={!newHabit.trim()}
            className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white font-medium transition-all"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* 2. Daily Routine Time-blocking Section */}
      <div className="glass-card p-3.5 rounded-xl border border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-cyan-400" />
            <p className="font-semibold text-slate-200">ตารางเวลาชีวิตประจำวัน (Daily Routine)</p>
          </div>
        </div>

        {/* Routine Inputs */}
        <div className="grid grid-cols-2 gap-2 bg-slate-900/60 p-2.5 rounded-xl border border-slate-800/80">
          <div>
            <label className="text-[10px] text-slate-400 flex items-center gap-1 mb-1">
              <Sun className="w-2.5 h-2.5 text-amber-400" /> เวลาตื่นนอน
            </label>
            <input
              type="text"
              value={wakeTime}
              onChange={(e) => setWakeTime(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleGenerateRoutine()}
              className="w-full glass-input px-2 py-1 rounded text-xs"
            />
          </div>
          <div>
            <label className="text-[10px] text-slate-400 flex items-center gap-1 mb-1">
              <Moon className="w-2.5 h-2.5 text-indigo-400" /> เวลาเข้านอน
            </label>
            <input
              type="text"
              value={sleepTime}
              onChange={(e) => setSleepTime(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleGenerateRoutine()}
              className="w-full glass-input px-2 py-1 rounded text-xs"
            />
          </div>
          <div className="col-span-2">
            <label className="text-[10px] text-slate-400 flex items-center gap-1 mb-1">
              <Target className="w-2.5 h-2.5 text-cyan-400" /> เป้าหมายหลักประจำวัน
            </label>
            <input
              type="text"
              value={focusGoal}
              onChange={(e) => setFocusGoal(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleGenerateRoutine()}
              placeholder="เช่น เขียนโปรแกรม, อ่านหนังสือ, ดูแลสุขภาพ..."
              className="w-full glass-input px-2 py-1 rounded text-xs"
            />
          </div>
        </div>

        <button
          onClick={handleGenerateRoutine}
          disabled={loadingRoutine}
          className="w-full py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white font-medium text-xs shadow-lg shadow-cyan-600/20 transition-all flex items-center justify-center gap-1.5"
        >
          {loadingRoutine ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>กำลังวางแผนตารางเวลา...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-3.5 h-3.5" />
              <span>✨ สร้างและบันทึกตารางเวลาชีวิต</span>
            </>
          )}
        </button>

        {/* Schedule Viewer */}
        {routine ? (
          <div className="space-y-1.5 mt-2 max-h-80 overflow-y-auto pr-1">
            <div className="flex items-center justify-between text-[10px] text-slate-400 px-1">
              <span>ตารางเวลาที่บันทึกไว้ ({routine.schedule?.length || 0} ช่วงเวลา):</span>
              <span className="text-cyan-300">ตื่น {routine.wake_time} • นอน {routine.sleep_time}</span>
            </div>

            {routine.schedule?.map((item, idx) => (
              <div
                key={idx}
                className="p-2 rounded-lg bg-slate-900/80 border border-slate-800 flex items-start gap-2 hover:border-slate-700 transition-colors"
              >
                <span className="text-[10px] font-mono text-cyan-300 whitespace-nowrap bg-cyan-950/70 px-1.5 py-0.5 rounded border border-cyan-800/40">
                  {item.time}
                </span>
                <div className="flex-1">
                  <p className="text-[11px] text-slate-200 leading-snug">{item.activity}</p>
                </div>
                {item.energy && (
                  <span className="text-[9px] px-1 py-0.5 rounded bg-slate-800 text-slate-400 flex-shrink-0">
                    {item.energy}
                  </span>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-center py-3 text-slate-500 text-[11px]">
            คลิก 'สร้างและบันทึกตารางเวลาชีวิต' เพื่อเริ่มวางแผน Time-blocking ประจำวัน
          </p>
        )}
      </div>
    </div>
  );
};
