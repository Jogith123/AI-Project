'use client';

import { useState, useEffect, useRef, useCallback } from 'react';

export interface SnakeData {
  id: number;
  length: number;
  body: number[][];
}

export interface GameState {
  tick: number;
  size: number;
  food: { row: number; col: number };
  snakes: SnakeData[];
}

interface UseSnakeWebSocketReturn {
  gameState: GameState | null;
  connected: boolean;
}

export function useSnakeWebSocket(url: string): UseSnakeWebSocketReturn {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const retryTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        if (retryTimer.current) clearTimeout(retryTimer.current);
      };

      ws.onmessage = (event) => {
        try {
          const data: GameState = JSON.parse(event.data);
          setGameState(data);
        } catch {
          // ignore malformed frames
        }
      };

      ws.onerror = () => {
        ws.close();
      };

      ws.onclose = () => {
        setConnected(false);
        wsRef.current = null;
        // Auto-reconnect after 2 s
        retryTimer.current = setTimeout(connect, 2000);
      };
    } catch {
      retryTimer.current = setTimeout(connect, 2000);
    }
  }, [url]);

  useEffect(() => {
    connect();
    return () => {
      if (retryTimer.current) clearTimeout(retryTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { gameState, connected };
}
