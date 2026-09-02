import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Star, Copy, Check, Sparkles, Paperclip, AlertCircle, RefreshCw } from 'lucide-react';
import { Message, RouteDecision } from '../types';
import { api } from '../services/api';

interface ChatWorkspaceProps {
  messages: Message[];
  isStreaming: boolean;
  streamingContent: string;
  streamingRouteInfo: RouteDecision | null;
  onSendMessage: (text: string) => void;
  onSelectSuggestion: (prompt: string) => void;
}

export const ChatWorkspace: React.FC<ChatWorkspaceProps> = ({
  messages,
  isStreaming,
  streamingContent,
  streamingRouteInfo,
  onSendMessage,
  onSelectSuggestion
}) => {
  const [inputText, setInputText] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [starredIds, setStarredIds] = useState<Set<string>>(new Set());
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const suggestionChips = [
    { label: '💰 สรุปรายรับ-จ่ายเดือนนี้', prompt: 'ช่วยสรุปสถานะการเงิน รายรับ รายจ่าย และคำนวณอัตราการออมประจำเดือนนี้ให้หน่อย' },
    { label: '📈 จำลองดอกเบี้ยทบต้น 5 ปี', prompt: 'ช่วยคำนวณและจำลองการเติบโตของเงินทุน เงินต้น 100,000 บาท ออมเพิ่มเดือนละ 5,000 บาท ผลตอบแทน 8% ต่อปี เป็นเวลา 5 ปี' },
    { label: '🩺 วางตารางเวลาชีวิตประจำวัน', prompt: 'ช่วยวางตารางเวลาชีวิตประจำวัน (Daily Routine) สไตล์ Time-blocking สำหรับคนทำงานเขียนโปรแกรมและต้องการดูแลสุขภาพ' },
    { label: '🎓 สร้าง Roadmap เรียนรู้', prompt: 'ช่วยสร้างแผนการเรียนรู้ (Milestone Roadmap) สำหรับทักษะ FastAPI และ SQLite WAL ในเวลา 3 สัปดาห์' },
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent]);

  const handleSend = () => {
    if (!inputText.trim() || isStreaming) return;
    const textToSend = inputText;
    setInputText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.focus();
    }
    onSendMessage(textToSend);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleStar = async (msg: Message) => {
    try {
      await api.toggleStarMessage(msg.id);
      const newSet = new Set(starredIds);
      if (newSet.has(msg.id)) newSet.delete(msg.id);
      else newSet.add(msg.id);
      setStarredIds(newSet);
    } catch (e) {
      console.error(e);
    }
  };

  const getModelBadge = (modelName?: string, intent?: string) => {
    if (!modelName) return null;
    let color = 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60';
    if (modelName.includes('deepseek') || modelName.includes('16b')) {
      color = 'bg-purple-950/60 text-purple-300 border-purple-800/60';
    } else if (modelName.includes('llama') || modelName.includes('8b')) {
      color = 'bg-amber-950/60 text-amber-300 border-amber-800/60';
    } else if (modelName.includes('phi')) {
      color = 'bg-sky-950/60 text-sky-300 border-sky-800/60';
    }

    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border text-[10px] font-mono font-medium ${color}`}>
        <span className="w-1.5 h-1.5 rounded-full bg-current" />
        {modelName}
      </span>
    );
  };

  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-4rem)] bg-gradient-to-b from-[#090d16] via-[#0b1120] to-[#090d16] relative overflow-hidden">
      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 space-y-6 max-w-4xl mx-auto w-full">
        {messages.length === 0 && !isStreaming ? (
          <div className="flex flex-col items-center justify-center h-full min-h-[60vh] text-center max-w-md mx-auto animate-in fade-in duration-300">
            <div className="w-16 h-16 rounded-3xl bg-gradient-to-tr from-cyan-500/20 via-indigo-500/20 to-purple-500/20 border border-cyan-500/30 flex items-center justify-center shadow-2xl mb-4 glow-cyan">
              <Sparkles className="w-8 h-8 text-cyan-400" />
            </div>
            <h2 className="text-xl font-bold text-slate-100 mb-2">ยินดีต้อนรับสู่ OGCAI</h2>
            <p className="text-xs text-slate-400 leading-relaxed mb-6">
              ผู้ช่วยอัจฉริยะส่วนตัว 100% Local ทำงานบนเครื่องของคุณเอง สลับโมเดลอัตโนมัติตามความเชี่ยวชาญ พร้อมคลังความจำและการเงิน สุขภาพ การเรียนรู้
            </p>

            {/* Quick Suggestion Chips */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full text-left">
              {suggestionChips.map((chip, idx) => (
                <button
                  key={idx}
                  onClick={() => onSelectSuggestion(chip.prompt)}
                  className="glass-card p-3 rounded-xl text-xs hover:border-cyan-500/50 hover:bg-slate-800/80 transition-all text-slate-300"
                >
                  {chip.label}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => {
            const isUser = msg.role === 'user';
            const isStarred = starredIds.has(msg.id) || msg.is_starred;
            return (
              <div
                key={msg.id}
                className={`flex gap-3 text-xs md:text-sm animate-in fade-in ${isUser ? 'justify-end' : 'justify-start'}`}
              >
                {!isUser && (
                  <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-600 to-indigo-600 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-md shadow-cyan-600/20">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                )}

                <div
                  className={`group relative max-w-[85%] md:max-w-[75%] rounded-2xl p-4 transition-all ${
                    isUser
                      ? 'bg-slate-800 text-slate-100 border border-slate-700/80'
                      : 'glass-panel text-slate-200 border border-slate-800/80'
                  }`}
                >
                  {/* Model Tag Header for Assistant */}
                  {!isUser && (
                    <div className="flex items-center justify-between gap-2 mb-2 pb-1.5 border-b border-slate-800/60">
                      <div className="flex items-center gap-2">
                        {getModelBadge(msg.model, msg.intent_category)}
                      </div>
                      <div className="flex items-center gap-1 opacity-60 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() => handleStar(msg)}
                          className={`p-1 rounded hover:bg-slate-800 transition-colors ${
                            isStarred ? 'text-amber-400' : 'text-slate-400 hover:text-amber-400'
                          }`}
                          title={isStarred ? 'ยกเลิกการ Star' : 'บันทึกลงคลังความรู้ถาวร'}
                        >
                          <Star className={`w-3.5 h-3.5 ${isStarred ? 'fill-amber-400' : ''}`} />
                        </button>
                        <button
                          onClick={() => handleCopy(msg.id, msg.content)}
                          className="p-1 rounded text-slate-400 hover:text-cyan-300 hover:bg-slate-800 transition-colors"
                          title="คัดลอกข้อความ"
                        >
                          {copiedId === msg.id ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Message Content */}
                  <div className="whitespace-pre-wrap leading-relaxed break-words font-normal">
                    {msg.content}
                  </div>
                </div>

                {isUser && (
                  <div className="w-8 h-8 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center flex-shrink-0 mt-0.5 text-slate-300">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            );
          })
        )}

        {/* Live SSE Streaming Bubble */}
        {isStreaming && (
          <div className="flex gap-3 text-xs md:text-sm animate-in fade-in justify-start">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-600 to-indigo-600 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-md shadow-cyan-600/20">
              <Bot className="w-4 h-4 text-white" />
            </div>

            <div className="glass-panel text-slate-200 border border-slate-800/80 rounded-2xl p-4 max-w-[85%] md:max-w-[75%]">
              {streamingRouteInfo && (
                <div className="flex items-center gap-2 mb-2 pb-1.5 border-b border-slate-800/60">
                  {getModelBadge(streamingRouteInfo.selected_model, streamingRouteInfo.intent_category)}
                  <span className="text-[10px] text-slate-400 truncate">{streamingRouteInfo.reason}</span>
                </div>
              )}

              <div className="whitespace-pre-wrap leading-relaxed break-words font-normal">
                {streamingContent || 'กำลังประมวลผลคำตอบ...'}
                <span className="streaming-cursor" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Bottom Input Area */}
      <div className="p-4 md:p-6 bg-gradient-to-t from-slate-950 via-slate-950/90 to-transparent">
        <div className="max-w-4xl mx-auto">
          <div className="glass-panel p-2 rounded-2xl border border-slate-800 shadow-2xl flex items-end gap-2 focus-within:border-cyan-500/50 transition-all">
            <textarea
              ref={textareaRef}
              rows={1}
              placeholder="พิมพ์คำถาม หรือสั่งให้ AI คำนวณ, วางแผน, เขียนโค้ด (Enter เพื่อส่ง, Shift+Enter ขึ้นบรรทัดใหม่)..."
              value={inputText}
              onChange={(e) => {
                setInputText(e.target.value);
                e.target.style.height = 'auto';
                e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
              }}
              onKeyDown={handleKeyDown}
              disabled={isStreaming}
              className="flex-1 bg-transparent border-0 focus:ring-0 text-slate-100 placeholder-slate-500 text-xs md:text-sm px-3 py-2 resize-none max-h-40 outline-none"
            />

            <button
              onClick={handleSend}
              disabled={!inputText.trim() || isStreaming}
              className="p-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 disabled:opacity-30 text-white shadow-lg shadow-cyan-500/20 transition-all flex-shrink-0"
              title="ส่งข้อความ"
            >
              {isStreaming ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </button>
          </div>

          <p className="text-center text-[10px] text-slate-500 mt-2">
            OGCAI Core Engine • 100% Local Inference • ข้อมูลทั้งหมดปลอดภัยและไม่ถูกส่งออกนอกเครื่อง
          </p>
        </div>
      </div>
    </div>
  );
};
