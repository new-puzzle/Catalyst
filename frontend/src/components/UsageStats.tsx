import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { DollarSign, MessageSquare, TrendingUp } from 'lucide-react';
import { api } from '../services/api';
import { UsageStats as UsageStatsType } from '../types';

export function UsageStats() {
  const [stats, setStats] = useState<UsageStatsType | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (isOpen) {
      api.getUsageStats(30).then(setStats).catch(console.error);
    }
  }, [isOpen]);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-2 text-gray-400 hover:text-white transition-colors"
      >
        <TrendingUp className="w-5 h-5" />
      </button>

      {isOpen && stats && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute right-0 top-12 w-64 bg-gray-800 rounded-xl p-4 shadow-xl z-50"
        >
          <h3 className="font-semibold mb-3">Usage Stats</h3>

          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-green-500" />
              <span className="text-sm text-gray-400">Total Cost:</span>
              <span className="ml-auto font-mono">${stats.total_cost.toFixed(4)}</span>
            </div>

            <div className="flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-blue-500" />
              <span className="text-sm text-gray-400">Messages:</span>
              <span className="ml-auto font-mono">{stats.total_messages}</span>
            </div>

            <div className="border-t border-gray-700 pt-3">
              <p className="text-xs text-gray-500 mb-2">By Provider:</p>
              {Object.entries(stats.by_provider).map(([provider, cost]) => (
                <div key={provider} className="flex justify-between text-sm">
                  <span className="text-gray-400 capitalize">{provider}</span>
                  <span className="font-mono">${cost.toFixed(4)}</span>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
