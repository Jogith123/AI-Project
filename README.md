# 🐍 AI Snake Arena — Complete Project Documentation

## Overview

**AI Snake Arena** is a real-time multi-agent simulation where **15 autonomous AI-controlled snakes** compete on a shared 20×20 grid. Each snake independently navigates toward food using the **A* (A-Star) pathfinding algorithm**. The simulation runs on a Python/FastAPI backend and is visualized live in a Next.js browser frontend via WebSockets.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      PYTHON BACKEND                          │
│                                                              │
│  ┌──────────────┐   ┌───────────────────────────────────┐   │
│  │  Game Loop   │──▶│  15 × Snake (A* AI Agent)         │   │
│  │  (Thread)    │   │  - a_star()  - _calc_f_cost()     │   │
│  │              │   │  - final_pos() - _calc_h_cost()   │   │
│  └──────────────┘   └───────────────────────────────────┘   │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────┐   _game_state dict (JSON)                 │
│  │  FastAPI     │──────────────────────────────────────────▶│
│  │  WebSocket   │   ws://localhost:8000/ws                   │
│  │  /ws         │   ~20 fps broadcast                        │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
                          │  WebSocket
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    NEXT.JS FRONTEND                          │
│                                                              │
│  useSnakeWebSocket hook  ──▶  GameState (React state)       │
│                                   │                         │
│                    ┌──────────────┴───────────────┐         │
│                    ▼                              ▼         │
│             GameBoard.tsx                  Rankings.tsx     │
│         (20×20 pixel grid)           (live leaderboard)    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend Language** | Python 3.x | Core game logic & AI |
| **Web Framework** | FastAPI | WebSocket server endpoint |
| **ASGI Server** | Uvicorn | Runs the FastAPI app |
| **Concurrency** | `threading` + `asyncio` | Game loop runs in parallel thread |
| **Frontend Framework** | Next.js 16 (App Router) | React-based UI |
| **Language** | TypeScript | Type-safe frontend code |
| **Styling** | Tailwind CSS | Utility-based design system |
| **Communication** | WebSocket (`ws://`) | Real-time state streaming |

---

## 🤖 Core Algorithm — A* (A-Star) Pathfinding

Each snake uses A* to find the shortest path from its current head position to the food. This is the most important algorithm in the project.

### What is A*?

A* is a **best-first graph search algorithm** that finds the optimal path by evaluating nodes using a combination of actual cost from start and estimated cost to goal.

### The Three Cost Functions

#### 1. H-Cost (Heuristic Cost) — [_calc_h_cost(row, col)](file:///c:/Users/Asus/OneDrive/Desktop/AI%20Project/snake/app.py#214-217)
Estimates the distance from a candidate cell to the **food** using **Manhattan Distance**:

$$H = |food\_row - row| + |food\_col - col|$$

```python
def _calc_h_cost(self, row: int, col: int):
    return abs(food_row - row) + abs(food_col - col)
```

> **Why Manhattan?** The snake can only move in 4 directions (up, down, left, right) — no diagonals. Manhattan distance is the perfect heuristic for grid movement.

#### 2. G-Cost (Actual Cost) — [_calc_g_cost(row, col)](file:///c:/Users/Asus/OneDrive/Desktop/AI%20Project/snake/app.py#218-220)
Measures the distance from the **snake's current head** to a candidate cell:

$$G = |row - head\_row| + |col - head\_col|$$

```python
def _calc_g_cost(self, row: int, col: int):
    return abs(row - self.row) + abs(col - self.col)
```

#### 3. F-Cost (Total Score) — [_calc_f_cost(row, col)](file:///c:/Users/Asus/OneDrive/Desktop/AI%20Project/snake/app.py#221-223)
The final priority score used to rank which cell to explore next. The food heuristic is **weighted 2×** to make the snake more aggressively goal-directed:

$$F = 2 \times H + G$$

```python
def _calc_f_cost(self, row: int, col: int):
    return 2 * self._calc_h_cost(row, col) + self._calc_g_cost(row, col)
```

> **Design Choice:** Weighting H by 2 makes this a **Weighted A\*** (also called Greedy-biased A\*). It trades strict optimality for faster convergence — making the snake more focused on reaching food quickly rather than finding the mathematically perfect path.

---

### A* Execution Flow

```
a_star(head_row, head_col)
    │
    ├── Look at all 4 neighbors: UP, DOWN, LEFT, RIGHT
    │   States: [(-1,0), (0,-1), (0,1), (1,0)]
    │
    ├── For each valid neighbor (not wall/body/food/already-visited):
    │   └── Compute F = 2H + G, add to self.paths list
    │
    ├── Sort paths by F-cost (ascending — lowest score = best)
    │
    ├── Pick best cell, mark it '.' on board
    │
    └── If H-cost to best cell == 1 (adjacent to food): STOP
        Else: recurse into best cell → a_star(new_row, new_col)
```

After A* marks the path, [final_pos()](file:///c:/Users/Asus/OneDrive/Desktop/AI%20Project/snake/app.py#224-250) **traces back** from the food to find the **first step** the snake should take:

```
final_pos(food_row, food_col)
    │
    ├── Check all 4 neighbors of food for '.' markers (A* path dots)
    │   or 'P' (snake head itself)
    │
    ├── Sort by G-cost (distance to head) ascending
    │
    ├── If G-cost == 0: head is already adjacent → return food pos
    ├── If G-cost == 1: this neighbor is the next step → return it
    └── Else: recurse → final_pos(neighbor) until G==1
```

### Fallback: Random Movement

If A* causes a `RecursionError` (the grid is too congested), the snake falls back to **random movement** — picking any valid direction that doesn't immediately reverse:

```python
def run(self):
    try:
        self._set_key_with_ai()   # Try A*
    except RecursionError:
        self._set_key_randomly()  # Fallback
```

---

## 🐍 Snake Agent — State Machine

### Board Symbols

| Symbol | Meaning |
|---|---|
| `#` | Wall (border) |
| `*` | Food |
| `P` | Snake head |
| `p` | Snake body segment |
| `.` | A* path marker (temporary) |
| ` ` | Empty cell |

### Body Movement Logic ([_move](file:///c:/Users/Asus/OneDrive/Desktop/AI%20Project/snake/app.py#192-206))

The tail-removal system implements the classic Snake game mechanic:

- If `temp_len == length` (no food eaten): remove the **last body segment** from the board
- If `temp_len < length` (food just eaten): skip removal — snake grows by 1

```python
def _move(self):
    head = self.body[-1]
    board[head[0]][head[1]] = 'p'          # Old head becomes body

    if self.temp_len == self.length:        # No growth
        last = self.body.pop(0)             # Remove tail
        board[last[0]][last[1]] = ' '
    else:
        self.temp_len = self.length         # Acknowledge growth

    self.body.append((self.row, self.col))  # New head
    board[self.row][self.col] = 'P'
```

---

## ⚙️ Backend — [app.py](file:///c:/Users/Asus/OneDrive/Desktop/AI%20Project/snake/app.py)

### Game Loop (Background Thread)

```
Thread: _game_loop()
    │
    ├── set_walls()      → Mark border cells as '#'
    ├── Create 15 Snake agents (id 0–14)
    ├── set_food()       → Place first food randomly
    │
    └── while True:
            for each snake:
                _update_game_state()   ← snapshot for WebSocket
                snake.run()            ← AI step + board update
```

### WebSocket Broadcasting

- **Endpoint:** `ws://localhost:8000/ws`
- **Protocol:** FastAPI WebSocket, CORS open (`*`)
- **Frame rate:** ~20 fps (50ms sleep per frame)
- **Payload per frame (JSON):**

```json
{
  "tick": 1042,
  "size": 20,
  "food": { "row": 7, "col": 13 },
  "snakes": [
    { "id": 3, "length": 9, "body": [[5,4],[5,5],[5,6],...] },
    { "id": 11, "length": 7, "body": [[12,8],[12,9],...] }
  ]
}
```

Snakes in the payload are **sorted by length descending** — the longest snake is first.

### Thread Safety

The game state dictionary is protected by a `threading.Lock()`:

```python
_state_lock = threading.Lock()

# Game thread writes:
with _state_lock:
    _game_state["snakes"] = [...]

# WebSocket coroutine reads:
with _state_lock:
    data = json.dumps(_game_state)
```

---

## 🌐 Frontend — Next.js

### File Structure

```
src/
├── app/
│   ├── page.tsx          ← Root page; wires WebSocket → components
│   ├── layout.tsx        ← Global HTML wrapper
│   └── globals.css       ← Global styles
├── components/
│   ├── GameBoard.tsx     ← 20×20 grid renderer
│   ├── Rankings.tsx      ← Live leaderboard with progress bars
│   └── Header.tsx        ← Connection status, tick counter
└── hooks/
    └── useSnakeWebSocket.ts  ← WebSocket client + auto-reconnect
```

### [useSnakeWebSocket](file:///c:/Users/Asus/OneDrive/Desktop/AI%20Project/snake/frontend/src/hooks/useSnakeWebSocket.ts#23-73) Hook

Custom React hook that manages the WebSocket connection lifecycle:

| Feature | Implementation |
|---|---|
| **Auto-connect** | Opens WebSocket on mount |
| **Auto-reconnect** | On close/error, retries after **2 seconds** |
| **State parsing** | JSON.parse on every incoming message |
| **Cleanup** | Closes socket and clears timers on unmount |

### [GameBoard](file:///c:/Users/Asus/OneDrive/Desktop/AI%20Project/snake/frontend/src/components/GameBoard.tsx#43-155) Component

Renders the 20×20 grid using CSS Grid:

- Builds a `cellMap` using `useMemo` — a `Map<"row,col", CellInfo>` for O(1) lookup
- Each cell is styled based on type: [wall](file:///c:/Users/Asus/OneDrive/Desktop/AI%20Project/snake/app.py#282-287), [food](file:///c:/Users/Asus/OneDrive/Desktop/AI%20Project/snake/app.py#289-297), [head](file:///c:/Users/Asus/OneDrive/Desktop/AI%20Project/snake/app.py#94-102), [body](file:///c:/Users/Asus/OneDrive/Desktop/AI%20Project/snake/app.py#306-308), `empty`
- Snake heads have a **glowing neon box-shadow** effect
- Snake bodies use [dimColor()](file:///c:/Users/Asus/OneDrive/Desktop/AI%20Project/snake/frontend/src/components/GameBoard.tsx#27-33) which applies **35% opacity** (`DIM = 0.35`) to the snake's color

```typescript
function dimColor(hex: string): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${DIM})`;  // DIM = 0.35
}
```

### [Rankings](file:///c:/Users/Asus/OneDrive/Desktop/AI%20Project/snake/frontend/src/components/Rankings.tsx#16-102) Component

Live leaderboard with animated progress bars:

- Sorted by length (descending) — backend sends pre-sorted
- Bar width formula: [(snake.length / maxLength) * 100%](file:///c:/Users/Asus/OneDrive/Desktop/AI%20Project/snake/app.py#126-146)
- Top 3 get medal emojis: 🥇 🥈 🥉
- Each snake has a unique neon color assigned by `snake.id % 15`

---

## 📊 Data Flow Summary

```
[Python Game Thread]
        │  every ~80ms (SLEEP=0.08s)
        ▼
[_game_state dict]  ←── _update_game_state() locks & writes
        │
        │  every 50ms (asyncio.sleep(0.05))
        ▼
[WebSocket /ws]  ──── broadcasts JSON to all connected clients
        │
        │  WebSocket message event
        ▼
[useSnakeWebSocket]  ──── setGameState(parsed JSON)
        │
        │  React re-render (useMemo recalculates cells)
        ▼
[GameBoard + Rankings]  ──── pixels updated on screen (~20 fps)
```

---

## 🚀 How to Run

### Requirements

```bash
pip install fastapi uvicorn
# Node.js + npm required for frontend
```

### Start Backend
```bash
cd "AI Project/snake"
python app.py
# Output: 🐍  Snake WebSocket server  →  ws://localhost:8000/ws
```

### Start Frontend
```bash
cd "AI Project/snake/frontend"
npm run dev
# Output: ✓ Ready at http://localhost:3000
```

### Open in Browser
Navigate to **http://localhost:3000**

---

## 🎯 Key Design Decisions

| Decision | Reason |
|---|---|
| **Weighted A* (2H + G)** | Faster, more food-focused navigation over strict optimality |
| **Manhattan distance heuristic** | Perfect for 4-directional grid movement |
| **RecursionError fallback** | A* can stack-overflow in congested grids; random move prevents crash |
| **Threading for game loop** | Game loop is blocking; asyncio WebSocket needs its own event loop |
| **`useMemo` for cell rendering** | Avoids re-rendering every cell on every tick |
| **Auto-reconnect in WebSocket hook** | Frontend stays alive even if backend restarts |
| **15 snakes, `sys.setrecursionlimit(5000)`** | Allows A* to trace long paths without Python's default limit |

---

## 📐 Algorithm Complexity

| Operation | Complexity |
|---|---|
| A* per snake per tick | O(N²) in worst case (N = grid cells = 20×20 = 400) |
| Board cell lookup | O(1) — 2D array indexing |
| `cellMap` build (frontend) | O(S × L) — S snakes, L body length |
| Rankings sort | Already sorted by backend |

---

*Built with Python + FastAPI + Next.js · 15 autonomous A* agents · Real-time WebSocket streaming*
