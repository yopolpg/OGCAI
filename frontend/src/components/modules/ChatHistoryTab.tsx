import React from 'react';
import { MessageSquare, Plus, Trash2, Pin, Clock } from 'lucide-react';
import { Conversation } from '../../types';

interface ChatHistoryTabProps {
  conversations: Conversation[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  onDeleteConversation: (id: string) => void;
}

export const ChatHistoryTab: React.FC<ChatHistoryTabProps> = ({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation
}) => {
  return (
    <div className="flex flex-col h-full">
      {/* New Chat Button */}
      <button
        onClick={onNewConversation}
        className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white font-medium text-xs shadow-lg shadow-cyan-600/20 transition-all mb-3"
      >
        <Plus className="w-4 h-4" />
        <span>เริ่มการสนทนาใหม่</span>
      </button>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
        {conversations.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-xs">
            <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-40" />
            <p>ยังไม่มีประวัติการสนทนา</p>
          </div>
        ) : (
          conversations.map((c) => {
            const isActive = activeConversationId === c.id;
            return (
              <div
                key={c.id}
                onClick={() => onSelectConversation(c.id)}
                className={`group flex items-center justify-between p-2.5 rounded-xl text-xs cursor-pointer transition-all ${
                  isActive
                    ? 'bg-slate-800/90 text-cyan-300 border border-cyan-500/30'
                    : 'text-slate-300 hover:bg-slate-800/50 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-2.5 overflow-hidden flex-1">
                  <MessageSquare className={`w-3.5 h-3.5 flex-shrink-0 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                  <div className="truncate">
                    <p className="truncate font-medium">{c.title || 'การสนทนาใหม่'}</p>
                    <span className="text-[10px] text-slate-400 flex items-center gap-1">
                      <Clock className="w-2.5 h-2.5" />
                      {(() => {
                        if (!c.updated_at) return 'เมื่อสักครู่';
                        const d = new Date(c.updated_at);
                        return isNaN(d.getTime()) ? 'เมื่อสักครู่' : d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                      })()}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity ml-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteConversation(c.id);
                    }}
                    className="p-1 rounded hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 transition-colors"
                    title="ลบการสนทนา"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
