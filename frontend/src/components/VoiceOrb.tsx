import { motion } from 'framer-motion';
import { Mic, MicOff, Brain } from 'lucide-react';
import { Mode, MODES } from '../types';

interface VoiceOrbProps {
  isListening: boolean;
  isProcessing: boolean;
  mode: Mode;
  onToggle: () => void;
  humeEnabled?: boolean;
}

export function VoiceOrb({ isListening, isProcessing, mode, onToggle, humeEnabled = false }: VoiceOrbProps) {
  const modeConfig = MODES.find(m => m.id === mode)!;

  return (
    <div className="flex flex-col items-center gap-4">
      <motion.button
        onClick={onToggle}
        disabled={isProcessing}
        className={`relative w-32 h-32 rounded-full bg-gradient-to-br ${modeConfig.color}
          flex items-center justify-center shadow-lg
          ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:scale-105'}
          transition-transform`}
        animate={isListening ? {
          scale: [1, 1.1, 1],
          boxShadow: [
            '0 0 20px rgba(255, 255, 255, 0.2)',
            '0 0 40px rgba(255, 255, 255, 0.4)',
            '0 0 20px rgba(255, 255, 255, 0.2)',
          ],
        } : {}}
        transition={{ repeat: Infinity, duration: 2 }}
      >
        {/* Outer ring animation */}
        {isListening && (
          <>
            <motion.div
              className="absolute inset-0 rounded-full border-2 border-white/30"
              animate={{ scale: [1, 1.5], opacity: [0.5, 0] }}
              transition={{ repeat: Infinity, duration: 1.5 }}
            />
            <motion.div
              className="absolute inset-0 rounded-full border-2 border-white/30"
              animate={{ scale: [1, 1.5], opacity: [0.5, 0] }}
              transition={{ repeat: Infinity, duration: 1.5, delay: 0.5 }}
            />
          </>
        )}

        {/* Hume indicator badge */}
        {humeEnabled && (
          <div className="absolute -top-1 -right-1 w-6 h-6 bg-purple-500 rounded-full flex items-center justify-center shadow-lg">
            <Brain className="w-3.5 h-3.5 text-white" />
          </div>
        )}

        {/* Icon */}
        {isListening ? (
          <Mic className="w-12 h-12 text-white" />
        ) : (
          <MicOff className="w-12 h-12 text-white/80" />
        )}
      </motion.button>

      <p className="text-sm text-gray-400">
        {isProcessing
          ? 'Processing...'
          : isListening
            ? (humeEnabled ? 'Listening (with emotions)...' : 'Listening...')
            : 'Tap to speak'}
      </p>
    </div>
  );
}
