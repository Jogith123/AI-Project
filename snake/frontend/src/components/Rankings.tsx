'use client';

import React from 'react';
import type { SnakeData } from '@/hooks/useSnakeWebSocket';

const SNAKE_COLORS: string[] = [
  '#00ff88', '#ff6b6b', '#4ecdc4', '#ffe66d', '#a29bfe',
  '#fd79a8', '#74b9ff', '#55efc4', '#fdcb6e', '#e17055',
  '#6c5ce7', '#00cec9', '#e84393', '#0984e3', '#b2bec3',
];

interface RankingsProps {
  snakes: SnakeData[];
}

export default function Rankings({ snakes }: RankingsProps) {
  const maxLength = Math.max(...snakes.map((s) => s.length), 1);

  return (
    <div className="flex flex-col gap-3 w-64 shrink-0">
      <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-widest">
        🏆 Live Rankings
      </h2>

      <div className="bg-[#0d0d1a] border border-[#1a1a2e] rounded-xl p-3 flex flex-col gap-1.5 overflow-y-auto max-h-[520px]">
        {snakes.length === 0 && (
          <p className="text-slate-500 text-sm text-center py-4">
            Waiting for snakes…
          </p>
        )}

        {snakes.map((snake, rank) => {
          const color = SNAKE_COLORS[snake.id % SNAKE_COLORS.length];
          const barWidth = `${(snake.length / maxLength) * 100}%`;
          const medals = ['🥇', '🥈', '🥉'];
          const medal = rank < 3 ? medals[rank] : `#${rank + 1}`;

          return (
            <div
              key={snake.id}
              className="flex flex-col gap-1 px-3 py-2 rounded-lg bg-[#0a0a14] border border-[#1a1a2e] hover:border-[#2a2a4a] transition-colors"
            >
              {/* Row: rank + name + score */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xs w-5 text-center">{medal}</span>
                  <span
                    className="w-2.5 h-2.5 rounded-full shrink-0"
                    style={{ backgroundColor: color, boxShadow: `0 0 6px ${color}` }}
                  />
                  <span className="text-sm font-medium text-slate-200">
                    Snake {snake.id}
                  </span>
                </div>
                <span
                  className="text-sm font-bold font-mono"
                  style={{ color }}
                >
                  {snake.length}
                </span>
              </div>

              {/* Progress bar */}
              <div className="h-1.5 rounded-full bg-[#1a1a2e] overflow-hidden">
                <div
                  className="rank-bar h-full rounded-full"
                  style={{
                    width: barWidth,
                    backgroundColor: color,
                    boxShadow: `0 0 4px ${color}`,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="bg-[#0d0d1a] border border-[#1a1a2e] rounded-xl p-3 text-xs text-slate-500 space-y-1.5">
        <p className="font-semibold text-slate-400 mb-2">Legend</p>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-sm bg-[#fbbf24] shadow-[0_0_6px_#fbbf24]" />
          <span>Food (A* target)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-sm bg-[#00ff88] shadow-[0_0_6px_#00ff88]" />
          <span>Snake head</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-sm bg-[#1a3a2a]" />
          <span>Snake body</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-sm bg-[#1e1e3a]" />
          <span>Wall</span>
        </div>
      </div>
    </div>
  );
}
