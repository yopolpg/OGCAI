import {
  Conversation,
  ModelInfo,
  RouteDecision,
  UserProfileItem,
  StarredKnowledgeItem,
  VaultFileItem,
  FinanceSummaryData,
  HabitStreakData,
  DailyRoutineData,
  RoadmapData,
  FlashcardItem,
  QuizQuestionItem
} from '../types';

const API_BASE = (typeof window !== 'undefined' && window.location.port === '5173') 
  ? 'http://127.0.0.1:8000/api' 
  : '/api';

export const api = {
  // System & Models
  async getHealth() {
    const res = await fetch(`${API_BASE}/health`);
    return res.json();
  },

  async getModels(): Promise<ModelInfo[]> {
    const res = await fetch(`${API_BASE}/models`);
    return res.json();
  },

  // Streaming Chat via SSE
  async streamChat({
    message,
    conversationId,
    model,
    onMetadata,
    onToken,
    onDone,
    onError
  }: {
    message: string;
    conversationId?: string;
    model?: string;
    onMetadata?: (meta: RouteDecision) => void;
    onToken?: (token: string) => void;
    onDone?: (stats: any) => void;
    onError?: (err: string) => void;
  }) {
    try {
      const response = await fetch(`${API_BASE}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          conversation_id: conversationId,
          model: model || undefined
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP Error ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      if (!reader) throw new Error('ReadableStream not supported');

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        let currentEvent = '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('event:')) {
            currentEvent = trimmed.replace('event:', '').trim();
          } else if (trimmed.startsWith('data:')) {
            const dataStr = trimmed.replace('data:', '').trim();
            try {
              const parsed = JSON.parse(dataStr);
              if (currentEvent === 'metadata' && onMetadata) {
                onMetadata(parsed);
              } else if (currentEvent === 'token' && onToken) {
                onToken(parsed.content || '');
              } else if (currentEvent === 'done' && onDone) {
                onDone(parsed);
              } else if (currentEvent === 'error' && onError) {
                onError(parsed.error || 'Unknown streaming error');
              }
            } catch (e) {
              // Ignore parse error on partial chunks
            }
          }
        }
      }
    } catch (err: any) {
      if (onError) onError(err.message || 'Failed to stream chat');
    }
  },

  // Conversations
  async listConversations(): Promise<Conversation[]> {
    const res = await fetch(`${API_BASE}/conversations`);
    return res.json();
  },

  async createConversation(title?: string): Promise<Conversation> {
    const res = await fetch(`${API_BASE}/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title })
    });
    return res.json();
  },

  async getConversation(id: string): Promise<Conversation> {
    const res = await fetch(`${API_BASE}/conversations/${id}`);
    return res.json();
  },

  async deleteConversation(id: string): Promise<boolean> {
    const res = await fetch(`${API_BASE}/conversations/${id}`, { method: 'DELETE' });
    return res.ok;
  },

  // Star message
  async toggleStarMessage(messageId: string) {
    const res = await fetch(`${API_BASE}/messages/${messageId}/star`, { method: 'POST' });
    return res.json();
  },

  // User Profile
  async getUserProfile(): Promise<UserProfileItem[]> {
    const res = await fetch(`${API_BASE}/profile`);
    return res.json();
  },

  async setUserProfileFact(key: string, value: string, category: string = 'general') {
    const res = await fetch(`${API_BASE}/profile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key, value, category })
    });
    return res.json();
  },

  async deleteUserProfileFact(id: number) {
    const res = await fetch(`${API_BASE}/profile/${id}`, { method: 'DELETE' });
    return res.ok;
  },

  // Starred Knowledge Base
  async getStarredKnowledge(): Promise<StarredKnowledgeItem[]> {
    const res = await fetch(`${API_BASE}/starred`);
    return res.json();
  },

  async deleteStarredKnowledge(id: string) {
    const res = await fetch(`${API_BASE}/starred/${id}`, { method: 'DELETE' });
    return res.ok;
  },

  // Vault Files & Search
  async getVaultFiles(): Promise<{ total_files: number; files: VaultFileItem[] }> {
    const res = await fetch(`${API_BASE}/vault/files`);
    return res.json();
  },

  async searchVault(query: string, topK: number = 3) {
    const res = await fetch(`${API_BASE}/vault/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, top_k: topK })
    });
    return res.json();
  },

  async indexVault() {
    const res = await fetch(`${API_BASE}/vault/index`, { method: 'POST' });
    return res.json();
  },

  async uploadVaultFile(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/vault/upload`, {
      method: 'POST',
      body: formData
    });
    return res.json();
  },

  // Finance Module
  async parseFinanceText(text: string) {
    const res = await fetch(`${API_BASE}/modules/finance/parse`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    return res.json();
  },

  async addFinanceTransaction(data: { type: string; amount: number; category: string; description?: string; date?: string }) {
    const res = await fetch(`${API_BASE}/modules/finance/transaction`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return res.json();
  },

  async getFinanceSummary(month?: string): Promise<FinanceSummaryData> {
    const url = month ? `${API_BASE}/modules/finance/summary?month=${month}` : `${API_BASE}/modules/finance/summary`;
    const res = await fetch(url);
    return res.json();
  },

  async calculateCompoundGrowth(data: { principal: number; monthly_contribution: number; annual_rate_pct: number; years: number }) {
    const res = await fetch(`${API_BASE}/modules/finance/compound-growth`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return res.json();
  },

  async calculate503020Budget(monthlyIncome: number) {
    const res = await fetch(`${API_BASE}/modules/finance/budget-50-30-20`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ monthly_income: monthlyIncome })
    });
    return res.json();
  },

  // Health Module
  async getHabitsList(): Promise<{ habits: string[] }> {
    const res = await fetch(`${API_BASE}/modules/health/habits`);
    return res.json();
  },

  async logHabit(data: { habit_name: string; status?: string; date?: string; notes?: string }) {
    const res = await fetch(`${API_BASE}/modules/health/habit/log`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return res.json();
  },

  async getHabitStreaks(habitName: string): Promise<HabitStreakData> {
    const res = await fetch(`${API_BASE}/modules/health/habit/streaks?habit_name=${encodeURIComponent(habitName)}`);
    return res.json();
  },

  async deleteHabit(habitName: string) {
    const res = await fetch(`${API_BASE}/modules/health/habit?habit_name=${encodeURIComponent(habitName)}`, {
      method: 'DELETE'
    });
    return res.json();
  },

  async generateDailyRoutine(data?: { wake_time?: string; sleep_time?: string; focus_goal?: string }): Promise<DailyRoutineData> {
    const res = await fetch(`${API_BASE}/modules/health/routine`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data || {})
    });
    return res.json();
  },

  // Study Module
  async generateStudyRoadmap(data: { topic: string; weeks?: number; target_level?: string }): Promise<RoadmapData> {
    const res = await fetch(`${API_BASE}/modules/study/roadmap`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return res.json();
  },

  async generateFlashcards(data: { content: string; count?: number }): Promise<{ flashcards: FlashcardItem[] }> {
    const res = await fetch(`${API_BASE}/modules/study/flashcards`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return res.json();
  },

  async generateQuiz(data: { topic: string; count?: number }): Promise<{ quiz: QuizQuestionItem[] }> {
    const res = await fetch(`${API_BASE}/modules/study/quiz`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return res.json();
  }
};
