import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  VoiceOrb,
  ModeSelector,
  ModeInfo,
  ChatInterface,
  TextInput,
  UsageStats
} from './components';
import { api } from './services/api';
import { Mode, Message, Conversation } from './types';
import { Sparkles, History, Plus } from 'lucide-react';

function App() {
  const [mode, setMode] = useState<Mode>('auto');
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversation, setConversation] = useState<Conversation | null>(null);

  // Create initial conversation
  useEffect(() => {
    createNewConversation();
  }, []);

  const createNewConversation = async () => {
    try {
      const conv = await api.createConversation(undefined, mode);
      setConversation(conv);
      setMessages([]);
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
  };

  const handleSendMessage = async (content: string) => {
    if (!conversation) return;

    setIsProcessing(true);

    // Add user message optimistically
    const tempUserMsg: Message = {
      id: Date.now(),
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, tempUserMsg]);

    try {
      const response = await api.sendMessage(conversation.id, content, mode);
      setMessages(prev => [...prev.slice(0, -1), tempUserMsg, response]);
    } catch (error) {
      console.error('Failed to send message:', error);
      // Remove optimistic message on error
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setIsProcessing(false);
    }
  };

  const handleVoiceToggle = () => {
    // TODO: Integrate with Hume AI for voice input
    setIsListening(!isListening);

    if (isListening) {
      // Simulate voice input for demo
      setTimeout(() => {
        handleSendMessage("This is a simulated voice input. Real voice integration with Hume AI would capture actual speech.");
      }, 1000);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-900">
      {/* Header */}
      <header className="flex items-center justify-between p-4 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-catalyst-500" />
          <h1 className="text-xl font-bold">Catalyst</h1>
        </div>

        <div className="flex items-center gap-2">
          <UsageStats />
          <button
            onClick={createNewConversation}
            className="p-2 text-gray-400 hover:text-white transition-colors"
            title="New conversation"
          >
            <Plus className="w-5 h-5" />
          </button>
          <button
            className="p-2 text-gray-400 hover:text-white transition-colors"
            title="History"
          >
            <History className="w-5 h-5" />
          </button>
        </div>
      </header>

      {/* Mode Selector */}
      <div className="flex flex-col items-center gap-2 p-4">
        <ModeSelector currentMode={mode} onModeChange={setMode} />
        <ModeInfo mode={mode} />
      </div>

      {/* Chat Area */}
      {messages.length > 0 ? (
        <ChatInterface messages={messages} isLoading={isProcessing} />
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center p-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center max-w-md"
          >
            <VoiceOrb
              isListening={isListening}
              isProcessing={isProcessing}
              mode={mode}
              onToggle={handleVoiceToggle}
            />
            <p className="mt-8 text-gray-400">
              Start speaking or type below to begin your journal entry
            </p>
          </motion.div>
        </div>
      )}

      {/* Show voice orb inline when there are messages */}
      {messages.length > 0 && (
        <div className="flex justify-center py-4">
          <VoiceOrb
            isListening={isListening}
            isProcessing={isProcessing}
            mode={mode}
            onToggle={handleVoiceToggle}
          />
        </div>
      )}

      {/* Text Input */}
      <TextInput onSend={handleSendMessage} disabled={isProcessing} />
    </div>
  );
}

export default App;
