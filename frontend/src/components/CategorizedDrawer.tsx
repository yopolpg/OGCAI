import React, { useState } from 'react';
import { MessageSquare, DollarSign, Activity, GraduationCap, Database, ChevronLeft, ChevronRight } from 'lucide-react';
import { ChatHistoryTab } from './modules/ChatHistoryTab';
import { FinanceTab } from './modules/FinanceTab';
import { HealthTab } from './modules/HealthTab';
import { StudyTab } from './modules/StudyTab';
import { VaultMemoryTab } from './modules/VaultMemoryTab';
import { Conversation } from '../types';

interface CategorizedDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  conversations: Conversation[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  onDeleteConversation: (id: string) => void;
}

export const CategorizedDrawer: React.FC<CategorizedDrawerProps> = ({
  isOpen,
  onClose,
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation
}) => {
  const [activeTab, setActiveTab] = useState<'chat' | 'finance' | 'health' | 'study' | 'vault'>('chat');

  const tabs = [
    { id: 'chat', label: 'แชท', icon: MessageSquare, color: 'text-cyan-400', activeBg: 'bg-cyan-950/60 border-cyan-800' },
    { id: 'finance', label: 'การเงิน', icon: DollarSign, color: 'text-emerald-400', activeBg: 'bg-emerald-950/60 border-emerald-800' },
    { id: 'health', label: 'สุขภาพ', icon: Activity, color: 'text-rose-400', activeBg: 'bg-rose-950/60 border-rose-800' },
    { id: 'study', label: 'การเรียน', icon: GraduationCap, color: 'text-purple-400', activeBg: 'bg-purple-950/60 border-purple-800' },
    { id: 'vault', label: 'ความจำ/Vault', icon: Database, color: 'text-amber-400', activeBg: 'bg-amber-950/60 border-amber-800' },
  ];

  if (!isOpen) return null;

  return (
    <aside className="w-80 md:w-96 h-[calc(100vh-4rem)] border-r border-slate-800/80 bg-slate-950/80 backdrop-blur-2xl flex flex-col flex-shrink-0 z-30 animate-in slide-in-from-left duration-200">
      {/* 5 Categorized Module Tabs */}
      <div className="flex border-b border-slate-800/80 p-2 gap-1 overflow-x-auto">
        {tabs.map((t) => {
          const Icon = t.icon;
          const isActive = activeTab === t.id;
          return (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id as any)}
              className={`flex-1 flex flex-col items-center gap-1 py-1.5 px-2 rounded-xl text-[10px] font-medium transition-all ${
                isActive
                  ? `${t.activeBg} ${t.color} border shadow-lg`
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border border-transparent'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span className="truncate">{t.label}</span>
            </button>
          );
        })}
      </div>

      {/* Drawer Content */}
      <div className="flex-1 p-3 overflow-hidden">
        {activeTab === 'chat' && (
          <ChatHistoryTab
            conversations={conversations}
            activeConversationId={activeConversationId}
            onSelectConversation={onSelectConversation}
            onNewConversation={onNewConversation}
            onDeleteConversation={onDeleteConversation}
          />
        )}
        {activeTab === 'finance' && <FinanceTab />}
        {activeTab === 'health' && <HealthTab />}
        {activeTab === 'study' && <StudyTab />}
        {activeTab === 'vault' && <VaultMemoryTab />}
      </div>
    </aside>
  );
};
