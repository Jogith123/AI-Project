'use client';

import React, { useMemo } from 'react';
import type { GameState, SnakeData } from '@/hooks/useSnakeWebSocket';

// 15 unique neon/vibrant colors — one per snake
const SNAKE_COLORS: string[] = [
  '#00ff88', // 0  vivid green
  '#ff6b6b', // 1  coral red
  '#4ecdc4', // 2  teal
  '#ffe66d', // 3  yellow
  '#a29bfe', // 4  lavender
  '#fd79a8', // 5  pink
  '#74b9ff', // 6  sky blue
  '#55efc4', // 7  mint
  '#fdcb6e', // 8  amber
  '#e17055', // 9  burnt orange
  '#6c5ce7', // 10 purple
  '#00cec9', // 11 cyan
  '#e84393', // 12 magenta
  '#0984e3', // 13 ocean blue
  '#b2bec3', // 14 silver
];

const DIM = 0.35; // body brightness multiplier

function dimColor(hex: string): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${DIM})`;
}

interface CellInfo {
  type: 'wall' | 'food' | 'head' | 'body' | 'empty';
  snakeId?: number;
}

interface GameBoardProps {
  gameState: GameState | null;
}

export default function GameBoard({ gameState }: GameBoardProps) {
  const SIZE = gameState?.size ?? 20;

  // Build a lookup map: "row,col" -> CellInfo
  const cellMap = useMemo<Map<string, CellInfo>>(() => {
    const map = new Map<string, CellInfo>();
    if (!gameState) return map;

    const { snakes, food } = gameState;

    // Mark food
    map.set(`${food.row},${food.col}`, { type: 'food' });

    // Mark snake bodies and heads (iterate in reverse ranking so top snake renders on top)
    for (const snake of [...snakes].reverse()) {
      for (let i = 0; i < snake.body.length; i++) {
        const [r, c] = snake.body[i];
        const isHead = i === snake.body.length - 1;
        map.set(`${r},${c}`, {
          type: isHead ? 'head' : 'body',
          snakeId: snake.id,
        });
      }
    }

    return map;
  }, [gameState]);

  const cells = useMemo(() => {
    const result: CellInfo[] = [];
    for (let r = 0; r < SIZE; r++) {
      for (let c = 0; c < SIZE; c++) {
        const isWall = r === 0 || r === SIZE - 1 || c === 0 || c === SIZE - 1;
        if (isWall) {
          result.push({ type: 'wall' });
        } else {
          result.push(cellMap.get(`${r},${c}`) ?? { type: 'empty' });
        }
      }
    }
    return result;
  }, [cellMap, SIZE]);

  function getCellStyle(cell: CellInfo): React.CSSProperties {
    switch (cell.type) {
      case 'wall':
        return { backgroundColor: '#1e1e3a', borderColor: '#2a2a4a' };
      case 'food':
        return { backgroundColor: '#fbbf24', borderColor: '#f59e0b', borderRadius: '50%' };
      case 'head': {
        const color = SNAKE_COLORS[cell.snakeId! % SNAKE_COLORS.length];
        return {
          backgroundColor: color,
          borderColor: color,
          borderRadius: '30%',
          boxShadow: `0 0 8px 2px ${color}88`,
        };
      }
      case 'body': {
        const color = SNAKE_COLORS[cell.snakeId! % SNAKE_COLORS.length];
        return {
          backgroundColor: dimColor(color),
          borderColor: 'transparent',
          borderRadius: '20%',
        };
      }
      default:
        return { backgroundColor: '#07070f', borderColor: '#0f0f1e' };
    }
  }

  return (
    <div className="flex flex-col items-center gap-3">
      <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-widest">
        Game Board — {SIZE}×{SIZE}
      </h2>

      {!gameState ? (
        <div className="flex items-center justify-center w-[440px] h-[440px] rounded-xl border border-[#1a1a2e] bg-[#0d0d1a]">
          <div className="text-center">
            <div className="text-4xl mb-3 animate-bounce">🐍</div>
            <p className="text-slate-400 text-sm">Waiting for backend…</p>
            <p className="text-slate-600 text-xs mt-1">Make sure python app.py is running</p>
          </div>
        </div>
      ) : (
        <div
          className="rounded-xl overflow-hidden border border-[#1a1a2e] shadow-2xl"
          style={{
            display: 'grid',
            gridTemplateColumns: `repeat(${SIZE}, 1fr)`,
            gap: '1px',
            backgroundColor: '#0a0a14',
            padding: '2px',
            width: 'min(480px, 90vw)',
            height: 'min(480px, 90vw)',
          }}
        >
          {cells.map((cell, idx) => (
            <div
              key={idx}
              className={`transition-colors duration-75 border ${
                cell.type === 'food' ? 'cell-food' : ''
              } ${cell.type === 'head' ? 'cell-head' : ''}`}
              style={getCellStyle(cell)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
