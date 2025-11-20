import { Conversation, ConversationSummary, Message, UsageStats } from '../types';

const API_BASE = '/api';

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export const api = {
  // Conversations
  createConversation: (title?: string, mode: string = 'auto') =>
    fetchAPI<Conversation>('/conversations/', {
      method: 'POST',
      body: JSON.stringify({ title, mode }),
    }),

  listConversations: (skip = 0, limit = 20) =>
    fetchAPI<ConversationSummary[]>(`/conversations/?skip=${skip}&limit=${limit}`),

  getConversation: (id: number) =>
    fetchAPI<Conversation>(`/conversations/${id}`),

  deleteConversation: (id: number) =>
    fetchAPI<void>(`/conversations/${id}`, { method: 'DELETE' }),

  // Messages
  sendMessage: (
    conversationId: number,
    content: string,
    mode: string,
    overrideProvider?: string
  ) =>
    fetchAPI<Message>(`/conversations/${conversationId}/messages`, {
      method: 'POST',
      body: JSON.stringify({
        content,
        mode,
        override_provider: overrideProvider,
      }),
    }),

  // Usage Stats
  getUsageStats: (days = 30) =>
    fetchAPI<UsageStats>(`/conversations/stats/usage?days=${days}`),

  // Weekly Synthesis
  getWeeklySynthesis: () =>
    fetchAPI<any>('/synthesis/weekly'),
};
