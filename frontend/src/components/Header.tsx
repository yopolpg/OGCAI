import React, { useState } from 'react';
import { Bot, Sparkles, ChevronDown, Check, Menu, X, Cpu, ShieldCheck, Zap } from 'lucide-react';
import { ModelInfo } from '../types';

interface HeaderProps {
  models: ModelInfo[];
  selectedModel: string | null; // null = Auto Routing
  activeModelName?: string;
  onSelectModel: (model: string | null) => void;
  isDrawerOpen: boolean;
  onToggleDrawer: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  models,
  selectedModel,
  activeModelName,
  onSelectModel,
  isDrawerOpen,
  onToggleDrawer
}) => {
  const [isModelDropdownOpen, setIsModelDropdownOpen] = useState(false);

  const getBadgeStyle = (modelName?: string) => {
    if (!modelName) return { dot: 'bg-emerald-400', text: 'text-emerald-400', border: 'border-emerald-500/30', bg: 'bg-emerald-950/40' };
    if (modelName.includes('deepseek') || modelName.includes('16b')) {
      return { dot: 'bg-purple-400', text: 'text-purple-400', border: 'border-purple-500/30', bg: 'bg-purple-950/40' };
    }
    if (modelName.includes('llama') || modelName.includes('8b')) {
      return { dot: 'bg-amber-400', text: 'text-amber-400', border: 'border-amber-500/30', bg: 'bg-amber-950/40' };
    }
    if (modelName.includes('phi')) {
      return { dot: 'bg-sky-400', text: 'text-sky-400', border: 'border-sky-500/30', bg: 'bg-sky-950/40' };
    }
    return { dot: 'bg-emerald-400', text: 'text-emerald-400', border: 'border-emerald-500/30', bg: 'bg-emerald-950/40' };
  };

  const badge = getBadgeStyle(selectedModel || activeModelName);

  return (
    <header className="h-16 border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-xl px-4 md:px-6 flex items-center justify-between sticky top-0 z-40">
      {/* Brand & Left Info */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleDrawer}
          className="p-2 rounded-xl text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 transition-colors"
          title="แถบเครื่องมือ & ประวัติ"
        >
          {isDrawerOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>

        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-base tracking-wide bg-gradient-to-r from-cyan-400 to-indigo-300 bg-clip-text text-transparent">
                OGCAI
              </span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-950/80 border border-cyan-800/50 text-cyan-300 font-mono">
                LOCAL 100%
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">Personal Everything Copilot</p>
          </div>
        </div>
      </div>

      {/* Center / Right: Active Model Badge & Modal Selector */}
      <div className="flex items-center gap-3 relative">
        <div className="relative">
          <button
            onClick={() => setIsModelDropdownOpen(!isModelDropdownOpen)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium transition-all ${badge.bg} ${badge.border} hover:border-slate-600`}
          >
            <span className={`w-2 h-2 rounded-full ${badge.dot} animate-pulse`} />
            <span className={badge.text}>
              {selectedModel ? `Manual: ${selectedModel}` : `Auto: ${activeModelName || 'Qwen 2.5 Coder 7B'}`}
            </span>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </button>

          {/* Model Selector Dropdown Modal */}
          {isModelDropdownOpen && (
            <div className="absolute right-0 mt-2 w-72 bg-slate-900/95 border border-slate-800 rounded-2xl shadow-2xl backdrop-blur-2xl p-2 z-50 animate-in fade-in slide-in-from-top-2">
              <div className="px-3 py-2 border-b border-slate-800/80 mb-1">
                <p className="text-xs font-semibold text-slate-200">เลือกโมเดลการประมวลผล</p>
                <p className="text-[11px] text-slate-400">ระบบ Auto-Switching จะเลือกโมเดลที่เก่งที่สุดให้อัตโนมัติ</p>
              </div>

              {/* Auto Routing Option */}
              <button
                onClick={() => {
                  onSelectModel(null);
                  setIsModelDropdownOpen(false);
                }}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs transition-colors ${
                  selectedModel === null ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30' : 'text-slate-300 hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Zap className="w-4 h-4 text-cyan-400" />
                  <div className="text-left">
                    <p className="font-semibold">⚡ Dynamic Auto-Routing</p>
                    <p className="text-[10px] text-slate-400">สลับโมเดลตาม Intent อัตโนมัติ (~0ms)</p>
                  </div>
                </div>
                {selectedModel === null && <Check className="w-4 h-4 text-cyan-400" />}
              </button>

              <div className="my-1.5 border-t border-slate-800/60" />
              <p className="px-3 py-1 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Manual Override (เลือกเอง)</p>

              {/* Models List */}
              {models.map((m) => {
                const isSelected = selectedModel === m.name;
                return (
                  <button
                    key={m.name}
                    onClick={() => {
                      onSelectModel(m.name);
                      setIsModelDropdownOpen(false);
                    }}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs transition-colors ${
                      isSelected ? 'bg-indigo-500/15 text-indigo-300 border border-indigo-500/30' : 'text-slate-300 hover:bg-slate-800/60'
                    }`}
                  >
                    <div className="flex items-center gap-2 text-left">
                      <Cpu className="w-3.5 h-3.5 text-slate-400" />
                      <div>
                        <span className="font-medium">{m.name}</span>
                        <span className="text-[10px] text-slate-400 ml-1.5">({m.size_formatted})</span>
                      </div>
                    </div>
                    {isSelected && <Check className="w-3.5 h-3.5 text-indigo-400" />}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
