import operator
import random
import time
import sys
import json
import threading
import asyncio

sys.setrecursionlimit(5000)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

choices = ['a', 'w', 's', 'd']
SIZE = 20       # Size of the map
SLEEP = 0.08    # Slowed down so the frontend is watchable
DEBUG = False

board = [['0' for _ in range(SIZE)] for _ in range(SIZE)]
snakes = []
food_row: int = 1
food_col: int = 1

# ── Shared WebSocket game state ─────────────────────────────────────────────
_game_state: dict = {
    "tick": 0,
    "size": SIZE,
    "food": {"row": 0, "col": 0},
    "snakes": []
}
_state_lock = threading.Lock()
_tick: int = 0

# ── FastAPI app ──────────────────────────────────────────────────────────────
app_server = FastAPI()
app_server.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_ws_clients: set = set()


@app_server.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    _ws_clients.add(websocket)
    try:
        while True:
            with _state_lock:
                data = json.dumps(_game_state)
            await websocket.send_text(data)
            await asyncio.sleep(0.05)   # ~20 fps stream to browser
    except Exception:
        pass
    finally:
        _ws_clients.discard(websocket)


def _update_game_state():
    global _tick
    _tick += 1
    with _state_lock:
        _game_state["tick"] = _tick
        _game_state["food"] = {"row": food_row, "col": food_col}
        _game_state["snakes"] = [
            {
                "id": s.id,
                "length": s.length,
                "body": [list(pos) for pos in s.body],
            }
            for s in sorted(snakes, key=lambda x: x.length, reverse=True)
        ]


# ── Snake class ──────────────────────────────────────────────────────────────

class Snake:
    def __init__(self, id):
        self.id = id
        self.key: str = 'd'
        self.last_key = ''
        self.body = []
        self.paths = []
        self.final_path = []
        self.length = 1
        self.temp_len = self.length
        self._set_snake_head()

    def _set_snake_head(self):
        self.row = random.randint(1, SIZE - 2)
        self.col = random.randint(1, SIZE - 2)
        while board[self.row][self.col] in ['#', 'P']:
            self.row = random.randint(1, SIZE - 2)
            self.col = random.randint(1, SIZE - 2)
        board[self.row][self.col] = 'P'
        self.body.append((self.row, self.col))

    def _set_key_with_ai(self):
        next_pos = self._find_path()
        if next_pos is None:
            return
        new_row = next_pos[0]
        new_col = next_pos[1]
        if new_row > self.row:
            self.key = 's'
        elif new_row < self.row:
            self.key = 'w'
        elif new_col > self.col:
            self.key = 'd'
        else:
            self.key = 'a'

    def _set_key_randomly(self):
        self.key = random.choice(choices)
        while (self.last_key == 'w' and self.key == 's') or \
              (self.last_key == 'a' and self.key == 'd') or \
              (self.last_key == 's' and self.key == 'w') or \
              (self.last_key == 'd' and self.key == 'a'):
            self.key = random.choice(choices)

    def run(self):
        try:
            self._set_key_with_ai()
        except RecursionError:
            self._set_key_randomly()

        self.last_key = self.key
        switcher = {
            'w': self._go_up,
            'a': self._go_left,
            's': self._go_down,
            'd': self._go_right,
        }
        switcher[self.key]()

        # Clean A* path dots from board
        for i in range(SIZE):
            for j in range(SIZE):
                if board[i][j] == '.':
                    board[i][j] = ' '

    def _go_up(self):
        if check_for_wall(self.row - 1, self.col):
            return
        if check_for_body(self.row - 1, self.col):
            return
        self.row -= 1
        self._check_for_food()
        self._move()
        time.sleep(SLEEP)

    def _go_left(self):
        if check_for_wall(self.row, self.col - 1):
            return
        if check_for_body(self.row, self.col - 1):
            return
        self.col -= 1
        self._check_for_food()
        self._move()
        time.sleep(SLEEP)

    def _go_down(self):
        if check_for_wall(self.row + 1, self.col):
            return
        if check_for_body(self.row + 1, self.col):
            return
        self.row += 1
        self._check_for_food()
        self._move()
        time.sleep(SLEEP)

    def _go_right(self):
        if check_for_wall(self.row, self.col + 1):
            return
        if check_for_body(self.row, self.col + 1):
            return
        self.col += 1
        self._check_for_food()
        self._move()
        time.sleep(SLEEP)

    def _check_for_food(self):
        if board[self.row][self.col] == '*':
            self.length += 1
            set_food()

    def _move(self):
        head = self.body[-1]
        board[head[0]][head[1]] = 'p'

        if self.temp_len == self.length:
            self.body.reverse()
            last = self.body.pop()
            board[last[0]][last[1]] = ' '
            self.body.reverse()
        else:
            self.temp_len = self.length

        self.body.append((self.row, self.col))
        board[self.row][self.col] = 'P'

    def _find_path(self):
        self.paths.clear()
        self.final_path.clear()
        self.a_star(self.row, self.col)
        next_pos = self.final_pos(food_row, food_col)
        return next_pos

    def _calc_h_cost(self, row: int, col: int):
        global food_row, food_col
        return abs(food_row - row) + abs(food_col - col)

    def _calc_g_cost(self, row: int, col: int):
        return abs(row - self.row) + abs(col - self.col)

    def _calc_f_cost(self, row: int, col: int):
        return 2 * self._calc_h_cost(row, col) + self._calc_g_cost(row, col)

    def final_pos(self, row, col):
        global food_row, food_col
        states = [(-1, 0), (0, -1), (0, 1), (1, 0)]
        for index in range(len(states)):
            new_row = row + states[index][0]
            new_col = col + states[index][1]
            if 0 <= new_row < SIZE and 0 <= new_col < SIZE:
                if board[new_row][new_col] in ['.', 'P']:
                    self.final_path.append((self._calc_g_cost(row, col), new_row, new_col))

        self.final_path.sort(key=operator.itemgetter(0))

        try:
            new_row = self.final_path[0][1]
            new_col = self.final_path[0][2]
        except IndexError:
            return None

        if self.final_path[0][0] == 0:
            return (food_row, food_col)
        elif self._calc_g_cost(new_row, new_col) == 1:
            return (new_row, new_col)
        else:
            self.final_path.reverse()
            self.final_path.pop()
            return self.final_pos(new_row, new_col)

    def a_star(self, row: int, col: int):
        states = [(-1, 0), (0, -1), (0, 1), (1, 0)]
        for _ in range(len(states)):
            new_row = row + states[_][0]
            new_col = col + states[_][1]
            try:
                new_location = board[new_row][new_col]
                if new_location not in ['p', 'P', '#', '.', '*']:
                    self.paths.append((self._calc_f_cost(new_row, new_col), new_row, new_col))
            except IndexError:
                continue

        self.paths.sort(key=operator.itemgetter(0))
        try:
            new_row = self.paths[0][1]
            new_col = self.paths[0][2]
        except IndexError:
            return

        if self._calc_h_cost(new_row, new_col) == 1:
            board[new_row][new_col] = '.'
            return
        else:
            self.paths.reverse()
            self.paths.pop()
            board[new_row][new_col] = '.'
            return self.a_star(new_row, new_col)


# ── Board helpers ────────────────────────────────────────────────────────────

def set_walls():
    global board
    for i in range(SIZE):
        for j in range(SIZE):
            board[i][j] = '#' if i in [0, SIZE - 1] or j in [0, SIZE - 1] else ' '


def set_food():
    global food_row, food_col
    food_row = random.randint(1, SIZE - 2)
    food_col = random.randint(1, SIZE - 2)
    while board[food_row][food_col] in ['#', 'P', 'p']:
        food_row = random.randint(1, SIZE - 2)
        food_col = random.randint(1, SIZE - 2)
    board[food_row][food_col] = '*'


def check_for_wall(row: int, col: int) -> bool:
    try:
        return board[row][col] == '#'
    except IndexError:
        return True


def check_for_body(row: int, col: int) -> bool:
    return board[row][col] == 'p'


# ── Game loop (runs in a background thread) ─────────────────────────────────

def _game_loop():
    set_walls()
    for sid in range(15):
        snakes.append(Snake(sid))
    set_food()
    while True:
        for snake in snakes:
            _update_game_state()
            snake.run()


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    t = threading.Thread(target=_game_loop, daemon=True)
    t.start()
    print("🐍  Snake WebSocket server  →  ws://localhost:8000/ws")
    uvicorn.run(app_server, host="0.0.0.0", port=8000, log_level="warning")


if __name__ == '__main__':
    main()
