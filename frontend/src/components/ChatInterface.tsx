import { useRef, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Message } from '../types';
import { Bot, User, Edit2, Trash2, Volume2, Check, X } from 'lucide-react';
import { api } from '../services/api';

interface ChatInterfaceProps {
  messages: Message[];
  isLoading: boolean;
  onMessageUpdate?: (messageId: number, content: string) => void;
  onMessageDelete?: (messageId: number) => void;
}

export function ChatInterface({ messages, isLoading, onMessageUpdate, onMessageDelete }: ChatInterfaceProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editContent, setEditContent] = useState('');
  const [playingAudio, setPlayingAudio] = useState<number | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleEdit = async (messageId: number) => {
    try {
      await api.editMessage(messageId, editContent);
      onMessageUpdate?.(messageId, editContent);
      setEditingId(null);
    } catch (err) {
      console.error('Failed to edit message:', err);
    }
  };

  const handleDelete = async (messageId: number) => {
    if (!confirm('Delete this message?')) return;
    try {
      await api.deleteMessage(messageId);
      onMessageDelete?.(messageId);
    } catch (err) {
      console.error('Failed to delete message:', err);
    }
  };

  const playAudio = (messageId: number) => {
    const audio = new Audio(api.getMessageAudio(messageId));
    audio.onplay = () => setPlayingAudio(messageId);
    audio.onended = () => setPlayingAudio(null);
    audio.onerror = () => setPlayingAudio(null);
    audio.play();
  };

  const playTTS = async (messageId: number, text: string) => {
    try {
      setPlayingAudio(messageId);
      const audioUrl = await api.textToSpeech(text);
      const audio = new Audio(audioUrl);
      audio.onended = () => {
        setPlayingAudio(null);
        URL.revokeObjectURL(audioUrl);
      };
      audio.onerror = () => {
        setPlayingAudio(null);
        URL.revokeObjectURL(audioUrl);
      };
      audio.play();
    } catch (err) {
      console.error('TTS playback failed:', err);
      setPlayingAudio(null);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      <AnimatePresence>
        {messages.map((message) => (
          <motion.div
            key={message.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {message.role === 'assistant' && (
              <div className="w-8 h-8 rounded-full bg-catalyst-600 flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4" />
              </div>
            )}

            <div className="group relative">
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-catalyst-600 text-white'
                    : 'bg-gray-800 text-gray-100'
                }`}
              >
                {editingId === message.id ? (
                  <div className="space-y-2">
                    <textarea
                      value={editContent}
                      onChange={(e) => setEditContent(e.target.value)}
                      className="w-full bg-gray-700 rounded p-2 text-white"
                      rows={3}
                    />
                    <div className="flex gap-2">
                      <button onClick={() => handleEdit(message.id)} className="p-1 hover:bg-gray-600 rounded">
                        <Check className="w-4 h-4" />
                      </button>
                      <button onClick={() => setEditingId(null)} className="p-1 hover:bg-gray-600 rounded">
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <p className="whitespace-pre-wrap">{message.content}</p>
                    {message.ai_provider && (
                      <p className="text-xs text-gray-400 mt-2">
                        via {message.ai_provider}
                        {message.tokens_used && ` • ${message.tokens_used} tokens`}
                      </p>
                    )}
                  </>
                )}
              </div>

              {/* Action buttons for user messages */}
              {message.role === 'user' && editingId !== message.id && (
                <div className="absolute -top-2 right-0 hidden group-hover:flex gap-1 bg-gray-700 rounded p-1">
                  {(message as any).audio_file_path && (
                    <button
                      onClick={() => playAudio(message.id)}
                      className={`p-1 hover:bg-gray-600 rounded ${playingAudio === message.id ? 'text-catalyst-400' : ''}`}
                    >
                      <Volume2 className="w-3 h-3" />
                    </button>
                  )}
                  <button
                    onClick={() => {
                      setEditingId(message.id);
                      setEditContent(message.content);
                    }}
                    className="p-1 hover:bg-gray-600 rounded"
                  >
                    <Edit2 className="w-3 h-3" />
                  </button>
                  <button
                    onClick={() => handleDelete(message.id)}
                    className="p-1 hover:bg-gray-600 rounded text-red-400"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              )}

              {/* TTS button for assistant messages */}
              {message.role === 'assistant' && (
                <div className="absolute -top-2 left-0 hidden group-hover:flex gap-1 bg-gray-700 rounded p-1">
                  <button
                    onClick={() => playTTS(message.id, message.content)}
                    className={`p-1 hover:bg-gray-600 rounded ${playingAudio === message.id ? 'text-catalyst-400 animate-pulse' : ''}`}
                    disabled={playingAudio === message.id}
                    title="Play with TTS"
                  >
                    <Volume2 className="w-3 h-3" />
                  </button>
                </div>
              )}
            </div>

            {message.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center flex-shrink-0">
                <User className="w-4 h-4" />
              </div>
            )}
          </motion.div>
        ))}
      </AnimatePresence>

      {isLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex gap-3"
        >
          <div className="w-8 h-8 rounded-full bg-catalyst-600 flex items-center justify-center">
            <Bot className="w-4 h-4" />
          </div>
          <div className="bg-gray-800 rounded-2xl px-4 py-3">
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        </motion.div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
