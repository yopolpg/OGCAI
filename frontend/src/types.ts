export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  model?: string;
  intent_category?: string;
  is_starred?: boolean;
  timestamp: string;
}

export interface Conversation {
  id: string;
  title: string;
  is_pinned?: boolean;
  created_at: string;
  updated_at: string;
  messages?: Message[];
}

export interface ModelInfo {
  name: string;
  size_formatted: string;
  category: 'general' | 'advisor' | 'heavy_logic' | 'fast' | 'fallback';
  badge_color: 'green' | 'yellow' | 'purple' | 'blue' | 'gray';
  is_available: boolean;
}

export interface RouteDecision {
  selected_model: string;
  routing_mode: 'auto' | 'manual';
  intent_category: string;
  reason: string;
  confidence: number;
  tier_used: string;
}

export interface UserProfileItem {
  id: number;
  key: string;
  value: string;
  category: string;
  confidence: number;
  updated_at: string;
}

export interface StarredKnowledgeItem {
  id: string;
  message_id?: string;
  title: string;
  summary: string;
  tags: string;
  content: string;
  created_at: string;
}

export interface VaultFileItem {
  name: string;
  relative_path: string;
  size_bytes: number;
  size_kb: number;
  modified_at: number;
}

export interface FinanceSummaryData {
  month: string;
  total_income: number;
  total_expense: number;
  total_saving: number;
  net_balance: number;
  savings_rate_pct: number;
  category_breakdown: Record<string, number>;
  chart?: {
    success: boolean;
    image_url: string;
  };
}

export interface HabitStreakData {
  habit_name: string;
  current_streak: number;
  total_completed: number;
  completed_last_30d: number;
  completion_rate_30d_pct: number;
  history: { date: string; status: string }[];
}

export interface RoutineItem {
  time: string;
  activity: string;
  energy: string;
}

export interface DailyRoutineData {
  wake_time: string;
  sleep_time: string;
  focus_goal: string;
  schedule: RoutineItem[];
  wellness_tips: string[];
}

export interface RoadmapWeek {
  week_number: number;
  title: string;
  core_concepts: string[];
  hands_on_project: string;
  key_resources: string[];
}

export interface RoadmapData {
  topic: string;
  summary: string;
  weeks: RoadmapWeek[];
}

export interface FlashcardItem {
  front: string;
  back: string;
}

export interface QuizQuestionItem {
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
}
