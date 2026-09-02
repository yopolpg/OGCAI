import React, { useState } from 'react';
import { GraduationCap, Map, BookOpen, HelpCircle, Check, X, RotateCw, Sparkles } from 'lucide-react';
import { api } from '../../services/api';
import { RoadmapData, FlashcardItem, QuizQuestionItem } from '../../types';

export const StudyTab: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState<'roadmap' | 'flashcards' | 'quiz'>('roadmap');

  // Roadmap State
  const [topic, setTopic] = useState('Python Asyncio & Web API');
  const [weeks, setWeeks] = useState(3);
  const [roadmap, setRoadmap] = useState<RoadmapData | null>(null);
  const [loadingRoadmap, setLoadingRoadmap] = useState(false);

  // Flashcards State
  const [flashcardTopic, setFlashcardTopic] = useState('FastAPI & Database');
  const [flashcards, setFlashcards] = useState<FlashcardItem[]>([]);
  const [currentCardIdx, setCurrentCardIdx] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [loadingCards, setLoadingCards] = useState(false);

  // Quiz State
  const [quizTopic, setQuizTopic] = useState('SQL & SQLite WAL');
  const [quizQuestions, setQuizQuestions] = useState<QuizQuestionItem[]>([]);
  const [userAnswers, setUserAnswers] = useState<Record<number, number>>({});
  const [loadingQuiz, setLoadingQuiz] = useState(false);

  const handleGenerateRoadmap = async () => {
    setLoadingRoadmap(true);
    try {
      const data = await api.generateStudyRoadmap({ topic, weeks: Number(weeks) });
      setRoadmap(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingRoadmap(false);
    }
  };

  const handleGenerateFlashcards = async () => {
    setLoadingCards(true);
    try {
      const data = await api.generateFlashcards({ content: flashcardTopic, count: 4 });
      setFlashcards(data.flashcards || []);
      setCurrentCardIdx(0);
      setIsFlipped(false);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingCards(false);
    }
  };

  const handleGenerateQuiz = async () => {
    setLoadingQuiz(true);
    setUserAnswers({});
    try {
      const data = await api.generateQuiz({ topic: quizTopic, count: 3 });
      setQuizQuestions(data.quiz || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingQuiz(false);
    }
  };

  return (
    <div className="flex flex-col h-full space-y-3 text-xs">
      {/* Sub-tab Navigation */}
      <div className="flex bg-slate-900/80 p-1 rounded-xl border border-slate-800">
        <button
          onClick={() => setActiveSubTab('roadmap')}
          className={`flex-1 py-1.5 rounded-lg font-medium transition-all ${
            activeSubTab === 'roadmap' ? 'bg-cyan-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          🗺️ Roadmap
        </button>
        <button
          onClick={() => setActiveSubTab('flashcards')}
          className={`flex-1 py-1.5 rounded-lg font-medium transition-all ${
            activeSubTab === 'flashcards' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          🗂️ Flashcards
        </button>
        <button
          onClick={() => setActiveSubTab('quiz')}
          className={`flex-1 py-1.5 rounded-lg font-medium transition-all ${
            activeSubTab === 'quiz' ? 'bg-purple-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          📝 Quiz
        </button>
      </div>

      <div className="flex-1 overflow-y-auto pr-1">
        {/* TAB 1: Skill Roadmap */}
        {activeSubTab === 'roadmap' && (
          <div className="space-y-3">
            <div className="glass-card p-3 rounded-xl border border-slate-800 space-y-2">
              <p className="font-semibold text-slate-200">สร้างแผนการเรียนรู้ (Milestone Roadmap)</p>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="ทักษะหรือหัวข้อที่ต้องการเรียน..."
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleGenerateRoadmap()}
                  className="flex-1 glass-input px-2.5 py-1.5 rounded-lg text-xs"
                />
                <select
                  value={weeks}
                  onChange={(e) => setWeeks(Number(e.target.value))}
                  className="glass-input px-2 py-1.5 rounded-lg text-xs"
                >
                  <option value={2}>2 สัปดาห์</option>
                  <option value={3}>3 สัปดาห์</option>
                  <option value={4}>4 สัปดาห์</option>
                </select>
              </div>
              <button
                onClick={handleGenerateRoadmap}
                disabled={loadingRoadmap}
                className="w-full py-1.5 rounded-lg bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 text-white font-medium shadow-md transition-all"
                title="สร้าง Roadmap (กด Enter)"
              >
                {loadingRoadmap ? 'กำลังออกแบบ Roadmap...' : '✨ สร้าง Roadmap'}
              </button>
            </div>

            {roadmap && (
              <div className="space-y-2">
                <p className="text-[11px] text-slate-400 px-1">{roadmap.summary}</p>
                {roadmap.weeks?.map((w) => (
                  <div key={w.week_number} className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1.5">
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800 flex items-center justify-center font-bold text-[10px]">
                        {w.week_number}
                      </span>
                      <p className="font-semibold text-slate-200">{w.title}</p>
                    </div>
                    <ul className="list-disc list-inside text-[11px] text-slate-400 space-y-0.5 pl-1">
                      {w.core_concepts?.map((c, i) => (
                        <li key={i}>{c}</li>
                      ))}
                    </ul>
                    {w.hands_on_project && (
                      <div className="mt-1 p-1.5 rounded bg-indigo-950/40 border border-indigo-800/40 text-[10px] text-indigo-300">
                        🔨 Project: {w.hands_on_project}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 2: Flashcards */}
        {activeSubTab === 'flashcards' && (
          <div className="space-y-3">
            <div className="glass-card p-3 rounded-xl border border-slate-800 space-y-2">
              <p className="font-semibold text-slate-200">สกัด Flashcards สำหรับทบทวน</p>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="ระบุหัวข้อหรือวางเนื้อหาที่ต้องการทบทวน..."
                  value={flashcardTopic}
                  onChange={(e) => setFlashcardTopic(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleGenerateFlashcards()}
                  className="flex-1 glass-input px-2.5 py-1.5 rounded-lg text-xs"
                />
                <button
                  onClick={handleGenerateFlashcards}
                  disabled={loadingCards}
                  className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium"
                  title="สกัดการ์ด (กด Enter)"
                >
                  {loadingCards ? '...' : 'สร้าง'}
                </button>
              </div>
            </div>

            {flashcards.length > 0 && (
              <div className="space-y-2.5">
                {/* Flip Card */}
                <div
                  onClick={() => setIsFlipped(!isFlipped)}
                  className="h-44 p-4 rounded-2xl glass-card border border-indigo-500/40 flex flex-col justify-between cursor-pointer hover:border-indigo-400 transition-all text-center select-none"
                >
                  <div className="flex justify-between text-[10px] text-slate-500">
                    <span>การ์ดที่ {currentCardIdx + 1} จาก {flashcards.length}</span>
                    <span className="flex items-center gap-1 text-indigo-400">
                      <RotateCw className="w-3 h-3" /> คลิกเพื่อพลิกคำตอบ
                    </span>
                  </div>

                  <div className="my-auto">
                    {isFlipped ? (
                      <p className="text-emerald-400 font-semibold text-sm animate-in fade-in">
                        {flashcards[currentCardIdx]?.back}
                      </p>
                    ) : (
                      <p className="text-slate-100 font-medium text-sm animate-in fade-in">
                        {flashcards[currentCardIdx]?.front}
                      </p>
                    )}
                  </div>

                  <div className="text-[10px] text-slate-400 font-mono">
                    {isFlipped ? '✅ คำเฉลย/คำอธิบาย' : '❓ คำถาม/แนวคิด'}
                  </div>
                </div>

                {/* Card Controls */}
                <div className="flex justify-between gap-2">
                  <button
                    disabled={currentCardIdx === 0}
                    onClick={() => {
                      setCurrentCardIdx(currentCardIdx - 1);
                      setIsFlipped(false);
                    }}
                    className="flex-1 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-30 text-slate-300"
                  >
                    ⬅️ ก่อนหน้า
                  </button>
                  <button
                    disabled={currentCardIdx === flashcards.length - 1}
                    onClick={() => {
                      setCurrentCardIdx(currentCardIdx + 1);
                      setIsFlipped(false);
                    }}
                    className="flex-1 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-30 text-slate-300"
                  >
                    ถัดไป ➡️
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 3: Quiz */}
        {activeSubTab === 'quiz' && (
          <div className="space-y-3">
            <div className="glass-card p-3 rounded-xl border border-slate-800 space-y-2">
              <p className="font-semibold text-slate-200">แบบทดสอบวัดความเข้าใจ (Quiz)</p>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="หัวข้อที่ต้องการทำ Quiz..."
                  value={quizTopic}
                  onChange={(e) => setQuizTopic(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleGenerateQuiz()}
                  className="flex-1 glass-input px-2.5 py-1.5 rounded-lg text-xs"
                />
                <button
                  onClick={handleGenerateQuiz}
                  disabled={loadingQuiz}
                  className="px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-medium"
                  title="เริ่ม Quiz (กด Enter)"
                >
                  {loadingQuiz ? '...' : 'เริ่ม Quiz'}
                </button>
              </div>
            </div>

            {quizQuestions.map((q, qIdx) => {
              const selectedAnswer = userAnswers[qIdx];
              return (
                <div key={qIdx} className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
                  <p className="font-semibold text-slate-200">
                    ข้อที่ {qIdx + 1}: {q.question}
                  </p>

                  <div className="space-y-1">
                    {q.options?.map((opt, oIdx) => {
                      const isChosen = selectedAnswer === oIdx;
                      const isCorrect = q.correct_index === oIdx;
                      let btnStyle = 'bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700';

                      if (selectedAnswer !== undefined) {
                        if (isCorrect) btnStyle = 'bg-emerald-950/60 border-emerald-500/50 text-emerald-300';
                        else if (isChosen && !isCorrect) btnStyle = 'bg-rose-950/60 border-rose-500/50 text-rose-300';
                      }

                      return (
                        <button
                          key={oIdx}
                          disabled={selectedAnswer !== undefined}
                          onClick={() => setUserAnswers({ ...userAnswers, [qIdx]: oIdx })}
                          className={`w-full text-left p-2 rounded-lg border text-[11px] transition-all flex items-center justify-between ${btnStyle}`}
                        >
                          <span>{opt}</span>
                          {selectedAnswer !== undefined && isCorrect && <Check className="w-3.5 h-3.5 text-emerald-400" />}
                          {selectedAnswer !== undefined && isChosen && !isCorrect && <X className="w-3.5 h-3.5 text-rose-400" />}
                        </button>
                      );
                    })}
                  </div>

                  {selectedAnswer !== undefined && (
                    <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800/80 text-[10px] text-cyan-300">
                      💡 คำอธิบาย: {q.explanation}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
