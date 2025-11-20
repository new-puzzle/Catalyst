import { motion } from 'framer-motion';
import { Mic, MicOff } from 'lucide-react';
import { Mode, MODES } from '../types';

interface VoiceOrbProps {
  isListening: boolean;
  isProcessing: boolean;
  mode: Mode;
  onToggle: () => void;
}

export function VoiceOrb({ isListening, isProcessing, mode, onToggle }: VoiceOrbProps) {
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

        {/* Icon */}
        {isListening ? (
          <Mic className="w-12 h-12 text-white" />
        ) : (
          <MicOff className="w-12 h-12 text-white/80" />
        )}
      </motion.button>

      <p className="text-sm text-gray-400">
        {isProcessing ? 'Processing...' : isListening ? 'Listening...' : 'Tap to speak'}
      </p>
    </div>
  );
}
