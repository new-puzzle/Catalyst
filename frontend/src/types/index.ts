export type Mode = 'auto' | 'architect' | 'simulator' | 'scribe';

export type AIProvider = 'gemini' | 'deepseek' | 'claude';

export interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  ai_provider?: AIProvider;
  tokens_used?: number;
  cost?: number;
  emotion_data?: Record<string, number>;
  created_at: string;
}

export interface Conversation {
  id: number;
  title?: string;
  mode: Mode;
  created_at: string;
  messages: Message[];
}

export interface ConversationSummary {
  id: number;
  title?: string;
  mode: Mode;
  created_at: string;
  message_count: number;
}

export interface UsageStats {
  period: string;
  total_cost: number;
  by_provider: Record<string, number>;
  total_messages: number;
}

export interface ModeConfig {
  id: Mode;
  name: string;
  icon: string;
  description: string;
  provider: AIProvider;
  color: string;
}

export const MODES: ModeConfig[] = [
  {
    id: 'auto',
    name: 'Auto',
    icon: '✨',
    description: 'Daily journaling & quick thoughts',
    provider: 'gemini',
    color: 'from-blue-500 to-cyan-500',
  },
  {
    id: 'architect',
    name: 'Architect',
    icon: '🏗️',
    description: 'Goal setting & planning',
    provider: 'deepseek',
    color: 'from-purple-500 to-pink-500',
  },
  {
    id: 'simulator',
    name: 'Simulator',
    icon: '🎭',
    description: 'Practice conversations',
    provider: 'claude',
    color: 'from-orange-500 to-red-500',
  },
  {
    id: 'scribe',
    name: 'Scribe',
    icon: '✍️',
    description: 'Polish your writing',
    provider: 'claude',
    color: 'from-green-500 to-emerald-500',
  },
];
