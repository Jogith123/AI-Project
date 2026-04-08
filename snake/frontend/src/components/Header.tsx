'use client';

import React from 'react';

interface HeaderProps {
  connected: boolean;
  tick: number;
  snakeCount: number;
}

export default function Header({ connected, tick, snakeCount }: HeaderProps) {
  return (
    <header className="w-full border-b border-[#1a1a2e] bg-[#0d0d1a] px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Title */}
        <div className="flex items-center gap-3">
          <span className="text-3xl">🐍</span>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">
              AI Snake Arena
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              A★ Pathfinding · {snakeCount} autonomous agents
            </p>
          </div>
        </div>

        {/* Stats */}
        <div className="flex items-center gap-6">
          <div className="text-right hidden sm:block">
            <p className="text-xs text-slate-500 uppercase tracking-widest">Tick</p>
            <p className="text-lg font-mono font-bold text-[#00ff88]">
              {tick.toLocaleString()}
            </p>
          </div>

          {/* Connection badge */}
          <div
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold border transition-all duration-300 ${
              connected
                ? 'bg-emerald-950 border-emerald-700 text-emerald-400'
                : 'bg-red-950 border-red-700 text-red-400'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                connected ? 'bg-emerald-400 animate-pulse' : 'bg-red-500'
              }`}
            />
            {connected ? 'Connected' : 'Reconnecting…'}
          </div>
        </div>
      </div>
    </header>
  );
}
