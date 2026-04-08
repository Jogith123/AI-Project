'use client';

import { useSnakeWebSocket } from '@/hooks/useSnakeWebSocket';
import GameBoard from '@/components/GameBoard';
import Rankings from '@/components/Rankings';
import Header from '@/components/Header';

const WS_URL = 'ws://localhost:8000/ws';

export default function Home() {
  const { gameState, connected } = useSnakeWebSocket(WS_URL);

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: '#050509' }}>
      <Header
        connected={connected}
        tick={gameState?.tick ?? 0}
        snakeCount={gameState?.snakes.length ?? 0}
      />

      <main className="flex flex-1 items-start justify-center gap-8 p-6 flex-wrap">
        <GameBoard gameState={gameState} />
        <Rankings snakes={gameState?.snakes ?? []} />
      </main>

      {/* Footer */}
      <footer className="text-center py-3 text-xs text-slate-700 border-t border-[#1a1a2e]">
        AI Snake Arena · 15 autonomous agents · A★ Pathfinding
      </footer>
    </div>
  );
}
