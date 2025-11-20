import { motion } from 'framer-motion';
import { Mode, MODES } from '../types';

interface ModeSelectorProps {
  currentMode: Mode;
  onModeChange: (mode: Mode) => void;
}

export function ModeSelector({ currentMode, onModeChange }: ModeSelectorProps) {
  return (
    <div className="flex gap-2 p-2 bg-gray-800/50 rounded-xl">
      {MODES.map((mode) => (
        <motion.button
          key={mode.id}
          onClick={() => onModeChange(mode.id)}
          className={`relative px-4 py-2 rounded-lg text-sm font-medium transition-colors
            ${currentMode === mode.id
              ? 'text-white'
              : 'text-gray-400 hover:text-gray-200'
            }`}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          {currentMode === mode.id && (
            <motion.div
              layoutId="activeMode"
              className={`absolute inset-0 bg-gradient-to-r ${mode.color} rounded-lg`}
              initial={false}
              transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
            />
          )}
          <span className="relative flex items-center gap-2">
            <span>{mode.icon}</span>
            <span className="hidden sm:inline">{mode.name}</span>
          </span>
        </motion.button>
      ))}
    </div>
  );
}

export function ModeInfo({ mode }: { mode: Mode }) {
  const modeConfig = MODES.find(m => m.id === mode)!;

  return (
    <div className="text-center">
      <p className="text-sm text-gray-400">{modeConfig.description}</p>
      <p className="text-xs text-gray-500 mt-1">
        Powered by <span className="text-catalyst-400">{modeConfig.provider}</span>
      </p>
    </div>
  );
}
