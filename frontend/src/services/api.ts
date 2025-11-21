import { Conversation, ConversationSummary, Message, UsageStats } from '../types';

const API_BASE = '/api';

// Token management
let authToken: string | null = localStorage.getItem('catalyst_token');

export function setAuthToken(token: string | null) {
  authToken = token;
  if (token) {
    localStorage.setItem('catalyst_token', token);
  } else {
    localStorage.removeItem('catalyst_token');
  }
}

export function getAuthToken(): string | null {
  return authToken;
}

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  const url = `${API_BASE}${endpoint}`;
  console.log('📤 API Request:', {
    method: options?.method || 'GET',
    url,
    endpoint
  });

  try {
    const response = await fetch(url, {
      headers,
      ...options,
    });

    console.log('📥 API Response:', {
      status: response.status,
      statusText: response.statusText,
      url
    });

    if (response.status === 401) {
      setAuthToken(null);
      throw new Error('Unauthorized - session expired');
    }

    if (!response.ok) {
      let errorDetail = response.statusText;
      try {
        const errorData = await response.json();
        errorDetail = errorData.detail || errorData.message || response.statusText;
      } catch {
        // If response is not JSON, use statusText
      }
      
      console.error('❌ API Error:', {
        status: response.status,
        statusText: response.statusText,
        detail: errorDetail,
        url
      });
      
      throw new Error(errorDetail);
    }

    return response.json();
  } catch (error) {
    console.error('❌ API Fetch Failed:', error);
    throw error;
  }
}

export interface AuthUser {
  id: number;
  email: string;
  name: string;
  picture: string | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export const api = {
  // Auth
  googleAuth: (token: string) => {
    console.log('🔍 Sending Google token to backend...');
    console.log('📊 Token length:', token.length);
    
    // Decode JWT payload to see aud field
    try {
      const parts = token.split('.');
      if (parts.length === 3) {
        const payload = JSON.parse(atob(parts[1]));
        console.log('📋 Token payload - aud:', payload.aud);
        console.log('📋 Token payload - email:', payload.email);
      }
    } catch (e) {
      console.warn('⚠️  Could not decode token:', e);
    }
    
    return fetchAPI<AuthResponse>('/auth/google', {
      method: 'POST',
      body: JSON.stringify({ token }),
    });
  },

  getMe: () => fetchAPI<AuthUser>('/auth/me'),

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
    fetchAPI<{ status: string }>(`/conversations/${id}`, { method: 'DELETE' }),

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

  // Message management
  editMessage: (messageId: number, content: string) =>
    fetchAPI<{ id: number; content: string; updated_at: string }>(`/messages/${messageId}`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    }),

  deleteMessage: (messageId: number) =>
    fetchAPI<{ status: string; id: number }>(`/messages/${messageId}`, {
      method: 'DELETE',
    }),

  getMessageAudio: (messageId: number) =>
    `${API_BASE}/messages/${messageId}/audio`,

  createJournalEntry: (conversationId: number, content: string) =>
    fetchAPI<any>(`/messages/${conversationId}/journal`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    }),

  // User preferences
  getPreferences: () =>
    fetchAPI<{ hume_enabled: boolean; voice_mode: string }>('/auth/preferences'),

  updatePreferences: (preferences: { hume_enabled: boolean; voice_mode: string }) =>
    fetchAPI<{ status: string; preferences: any }>('/auth/preferences', {
      method: 'PUT',
      body: JSON.stringify(preferences),
    }),
};
