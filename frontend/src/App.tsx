import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  VoiceOrb,
  ModeSelector,
  ModeInfo,
  ChatInterface,
  TextInput,
  UsageStats,
  ConversationHistory,
  GoogleSignIn
} from './components';
import { api, setAuthToken, getAuthToken, AuthUser } from './services/api';
import { useHumeVoice } from './hooks/useHumeVoice';
import { useBrowserSpeech } from './hooks/useBrowserSpeech';
import { Mode, Message, Conversation } from './types';
import { Sparkles, History, Plus, LogOut, Brain, Mic } from 'lucide-react';

// Get from environment or config
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';
const HUME_API_KEY = import.meta.env.VITE_HUME_API_KEY || '';

function App() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const [mode, setMode] = useState<Mode>('auto');
  const [isProcessing, setIsProcessing] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [humeEnabled, setHumeEnabled] = useState(true);

  // Hume voice integration (with emotion analysis)
  const {
    isListening: isHumeListening,
    isProcessing: isHumeProcessing,
    toggleListening: toggleHumeListening
  } = useHumeVoice({
    apiKey: HUME_API_KEY,
    onResult: (result) => {
      if (result.transcript && result.transcript !== '[Voice input received - please type your message]') {
        handleSendMessage(result.transcript, {
          primaryEmotion: result.primaryEmotion,
          emotions: result.emotions.reduce((acc, e) => ({ ...acc, [e.name]: e.score }), {}),
        });
      }
    },
    onError: (errorMsg) => {
      setError(errorMsg);
      setTimeout(() => setError(null), 3000);
    },
  });

  // Browser speech recognition (no emotion analysis)
  const {
    isListening: isBrowserListening,
    toggleListening: toggleBrowserListening,
  } = useBrowserSpeech({
    onResult: (transcript) => {
      handleSendMessage(transcript);
    },
    onError: (errorMsg) => {
      setError(errorMsg);
      setTimeout(() => setError(null), 3000);
    },
  });

  // Derived state for voice
  const isListening = humeEnabled ? isHumeListening : isBrowserListening;
  const isVoiceProcessing = humeEnabled ? isHumeProcessing : false;
  const toggleListening = humeEnabled ? toggleHumeListening : toggleBrowserListening;

  // Check for existing auth on mount
  useEffect(() => {
    const checkAuth = async () => {
      if (getAuthToken()) {
        try {
          const userData = await api.getMe();
          setUser(userData);
          // Load preferences
          try {
            const prefs = await api.getPreferences();
            setHumeEnabled(prefs.hume_enabled);
          } catch {
            // Use default if preferences not available
          }
        } catch {
          setAuthToken(null);
        }
      }
      setIsAuthLoading(false);
    };
    checkAuth();
  }, []);

  // Create conversation when user logs in
  useEffect(() => {
    if (user && !conversation) {
      createNewConversation();
    }
  }, [user]);

  // Save preference when humeEnabled changes
  const handleToggleHume = async () => {
    const newValue = !humeEnabled;
    setHumeEnabled(newValue);
    try {
      await api.updatePreferences({
        hume_enabled: newValue,
        voice_mode: newValue ? 'hume' : 'browser'
      });
    } catch (err) {
      console.error('Failed to save preference:', err);
    }
  };

  const handleGoogleSuccess = useCallback(async (credential: string) => {
    try {
      console.log('🔍 Google Sign-In successful, authenticating with backend...');
      const response = await api.googleAuth(credential);
      console.log('✅ Backend authentication successful');
      setAuthToken(response.access_token);
      setUser(response.user);
      setError(null);
      // Load preferences after login
      try {
        const prefs = await api.getPreferences();
        setHumeEnabled(prefs.hume_enabled);
      } catch {
        // Use default
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Authentication failed';
      console.error('❌ Authentication error:', errorMsg);
      setError(errorMsg);
      setTimeout(() => setError(null), 5000);
    }
  }, []);

  const handleGoogleError = useCallback((errorMsg: string) => {
    console.error('❌ Google Sign-In error:', errorMsg);
    setError(errorMsg);
    setTimeout(() => setError(null), 5000);
  }, []);

  const handleLogout = () => {
    setAuthToken(null);
    setUser(null);
    setConversation(null);
    setMessages([]);
  };

  const createNewConversation = async () => {
    try {
      const conv = await api.createConversation(undefined, mode);
      setConversation(conv);
      setMessages([]);
    } catch (err) {
      console.error('Failed to create conversation:', err);
    }
  };

  const loadConversation = async (id: number) => {
    try {
      const conv = await api.getConversation(id);
      setConversation(conv);
      setMessages(conv.messages);
      setMode(conv.mode as Mode);
    } catch (err) {
      console.error('Failed to load conversation:', err);
    }
  };

  const handleSendMessage = async (content: string, emotionData?: Record<string, any>) => {
    if (!conversation) return;

    setIsProcessing(true);
    setError(null);

    // Add user message optimistically
    const tempUserMsg: Message = {
      id: Date.now(),
      role: 'user',
      content,
      emotion_data: emotionData,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, tempUserMsg]);

    try {
      const response = await api.sendMessage(conversation.id, content, mode);
      setMessages(prev => [...prev.slice(0, -1), tempUserMsg, response]);
    } catch (err) {
      console.error('Failed to send message:', err);
      setError(err instanceof Error ? err.message : 'Failed to send message');
      // Remove optimistic message on error
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setIsProcessing(false);
    }
  };

  // Show loading state
  if (isAuthLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <Sparkles className="w-12 h-12 text-catalyst-500 mx-auto mb-4 animate-pulse" />
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  // Show login if not authenticated
  if (!user) {
    return (
      <div className="h-screen flex flex-col items-center justify-center bg-gray-900 p-4">
        <div className="text-center mb-8">
          <Sparkles className="w-16 h-16 text-catalyst-500 mx-auto mb-4" />
          <h1 className="text-3xl font-bold mb-2">Catalyst</h1>
          <p className="text-gray-400 max-w-md">
            Your AI-powered smart journal. Voice-first, privacy-focused journaling with emotional intelligence.
          </p>
        </div>
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 max-w-md">
            <p className="text-sm">{error}</p>
            <p className="text-xs text-red-300 mt-2">Check the browser console (F12) for more details</p>
          </div>
        )}
        <GoogleSignIn
          onSuccess={handleGoogleSuccess}
          clientId={GOOGLE_CLIENT_ID}
          onError={handleGoogleError}
        />
      </div>
    );
  }

  const voiceAvailable = humeEnabled ? !!HUME_API_KEY : true;

  return (
    <div className="h-screen flex flex-col bg-gray-900">
      {/* Header */}
      <header className="flex items-center justify-between p-4 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-catalyst-500" />
          <h1 className="text-xl font-bold">Catalyst</h1>
        </div>

        <div className="flex items-center gap-2">
          {/* Hume Toggle */}
          {HUME_API_KEY && (
            <button
              onClick={handleToggleHume}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${
                humeEnabled
                  ? 'bg-catalyst-600 text-white'
                  : 'bg-gray-700 text-gray-300'
              }`}
              title={humeEnabled ? 'Emotion analysis ON' : 'Emotion analysis OFF'}
            >
              {humeEnabled ? (
                <>
                  <Brain className="w-4 h-4" />
                  <span className="hidden sm:inline">Emotions</span>
                </>
              ) : (
                <>
                  <Mic className="w-4 h-4" />
                  <span className="hidden sm:inline">Voice Only</span>
                </>
              )}
            </button>
          )}

          <UsageStats />
          <button
            onClick={createNewConversation}
            className="p-2 text-gray-400 hover:text-white transition-colors"
            title="New conversation"
          >
            <Plus className="w-5 h-5" />
          </button>
          <button
            onClick={() => setShowHistory(true)}
            className="p-2 text-gray-400 hover:text-white transition-colors"
            title="History"
          >
            <History className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2 ml-2 pl-2 border-l border-gray-700">
            {user.picture && (
              <img
                src={user.picture}
                alt={user.name}
                className="w-8 h-8 rounded-full"
              />
            )}
            <button
              onClick={handleLogout}
              className="p-2 text-gray-400 hover:text-white transition-colors"
              title="Sign out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Error message */}
      {error && (
        <div className="mx-4 mt-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Mode Selector */}
      <div className="flex flex-col items-center gap-2 p-4">
        <ModeSelector currentMode={mode} onModeChange={setMode} />
        <ModeInfo mode={mode} />
      </div>

      {/* Chat Area */}
      {messages.length > 0 ? (
        <ChatInterface messages={messages} isLoading={isProcessing || isVoiceProcessing} />
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center p-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center max-w-md"
          >
            {voiceAvailable && (
              <VoiceOrb
                isListening={isListening}
                isProcessing={isProcessing || isVoiceProcessing}
                mode={mode}
                onToggle={toggleListening}
                humeEnabled={humeEnabled}
              />
            )}
            <p className="mt-8 text-gray-400">
              {voiceAvailable
                ? `Start speaking or type below${humeEnabled ? ' (with emotion analysis)' : ''}`
                : 'Type below to begin your journal entry'}
            </p>
          </motion.div>
        </div>
      )}

      {/* Show voice orb inline when there are messages */}
      {messages.length > 0 && voiceAvailable && (
        <div className="flex justify-center py-4">
          <VoiceOrb
            isListening={isListening}
            isProcessing={isProcessing || isVoiceProcessing}
            mode={mode}
            onToggle={toggleListening}
            humeEnabled={humeEnabled}
          />
        </div>
      )}

      {/* Text Input */}
      <TextInput onSend={(msg) => handleSendMessage(msg)} disabled={isProcessing || isVoiceProcessing} />

      {/* Conversation History Panel */}
      <ConversationHistory
        isOpen={showHistory}
        onClose={() => setShowHistory(false)}
        onSelectConversation={loadConversation}
        currentConversationId={conversation?.id}
      />
    </div>
  );
}

export default App;
