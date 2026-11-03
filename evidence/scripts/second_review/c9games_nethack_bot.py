#!/usr/bin/env python3
"""Explorer agent: answer prompts, pray when dying, fight what is adjacent, walk to the downstairs, otherwise explore."""
import random
from collections import deque

from nle import nethack
from nle.nethack import ACTIONS, CompassDirection, MiscAction, MiscDirection, Command

_L = list(ACTIONS)


def _i(k):
    return _L.index(k)


DIRS = [(0, -1, _i(CompassDirection.N)), (1, 0, _i(CompassDirection.E)), (0, 1, _i(CompassDirection.S)),
        (-1, 0, _i(CompassDirection.W)), (1, -1, _i(CompassDirection.NE)), (1, 1, _i(CompassDirection.SE)),
        (-1, 1, _i(CompassDirection.SW)), (-1, -1, _i(CompassDirection.NW))]
YES = _i(CompassDirection.NW)  # the 'y' key
DOWN = _i(MiscDirection.DOWN)
MORE = _i(MiscAction.MORE)
ESC = _i(Command.ESC)
PRAY = _i(Command.PRAY)
SEARCH = _i(Command.SEARCH)
BROWN = 3
S = {"depth": None, "visited": set(), "blocked": set(), "stairs": None, "last": None, "pos": None,
     "last_pray": -1000, "idle": 0, "target": None}


def _walkable(ch, color):
    if ch in (32, ord("}"), ord("`"), ord("^")):
        return False
    if ch in (ord("|"), ord("-")):
        return color == BROWN
    return True


def _is_door(ch, color):
    return color == BROWN and ch in (ord("+"), ord("|"), ord("-"))


def _bfs(x0, y0, chars, colors, glyphs, goal):
    seen = {(x0, y0): None}
    q = deque([(x0, y0)])
    door0 = None
    while q:
        x, y = q.popleft()
        if (x, y) != (x0, y0) and goal(x, y):
            while seen[(x, y)] != (x0, y0):
                x, y = seen[(x, y)]
            return x, y
        door = _is_door(chars[y, x], colors[y, x])
        for dx, dy, _ in DIRS:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < 79 and 0 <= ny < 21) or (nx, ny) in seen or (nx, ny) in S["blocked"]:
                continue
            ch, col = chars[ny, nx], colors[ny, nx]
            if not _walkable(ch, col) or nethack.glyph_is_monster(glyphs[ny, nx]):
                continue
            if dx and dy and (door or _is_door(ch, col)):
                continue
            seen[(nx, ny)] = (x, y)
            q.append((nx, ny))
    return None


def get_action(obs, info, step):
    misc = obs["misc"]
    bl = obs["blstats"]
    x, y = int(bl[0]), int(bl[1])
    if misc[2]:
        return MORE
    if misc[0]:
        if S["last"] == PRAY:
            S["last"] = YES
            return YES
        if S["target"]:
            S["blocked"].add(S["target"])
        S["last"] = ESC
        return ESC
    if misc[1]:
        S["last"] = ESC
        return ESC
    chars, colors, glyphs = obs["chars"], obs["colors"], obs["glyphs"]
    depth = (int(bl[23]), int(bl[24]))
    if depth != S["depth"]:
        S.update(depth=depth, visited=set(), blocked=set(), stairs=None, idle=0, pos=None, target=None)
    if S["target"] and S["pos"] == (x, y) and S["last"] not in (PRAY, SEARCH, DOWN, YES, ESC):
        msg = bytes(obs["message"]).split(b"\0")[0]
        if b"You " not in msg or b"locked" in msg or b"stuck" in msg:
            S["blocked"].add(S["target"])
    S["visited"].add((x, y))
    S["pos"] = (x, y)
    S["target"] = None
    hp, maxhp, turn = int(bl[10]), max(1, int(bl[11])), int(bl[20])
    if (hp * 5 < maxhp or hp < 6 or int(bl[21]) >= 3) and turn - S["last_pray"] > 1000:
        S["last_pray"] = turn
        S["last"] = PRAY
        return PRAY
    for dx, dy, act in DIRS:
        nx, ny = x + dx, y + dy
        if 0 <= nx < 79 and 0 <= ny < 21 and (nx, ny) not in S["blocked"]:
            g = glyphs[ny, nx]
            if nethack.glyph_is_monster(g) and not nethack.glyph_is_pet(g):
                S["last"] = act
                S["target"] = (nx, ny)
                return act
    ys, xs = (chars == ord(">")).nonzero()
    if len(xs):
        S["stairs"] = (int(xs[0]), int(ys[0]))
    msg = bytes(obs["message"]).split(b"\0")[0]
    if S["stairs"] == (x, y) or b"staircase down here" in msg or b"ladder down here" in msg:
        S["last"] = DOWN
        return DOWN
    next_cell = None
    if S["stairs"]:
        sx, sy = S["stairs"]
        next_cell = _bfs(x, y, chars, colors, glyphs, lambda a, b: (a, b) == (sx, sy))
    if next_cell is None:
        def frontier(a, b):
            if (a, b) in S["visited"]:
                return False
            for dx, dy, _ in DIRS:
                n, m = a + dx, b + dy
                if 0 <= n < 79 and 0 <= m < 21 and chars[m, n] == 32:
                    return True
            return False
        next_cell = _bfs(x, y, chars, colors, glyphs, frontier)
    if next_cell is None:
        S["idle"] += 1
        if S["idle"] % 25 == 0:
            S["visited"] = set()
        if S["idle"] % 3:
            S["last"] = SEARCH
            return SEARCH
        dx, dy, act = random.choice(DIRS)
        S["last"] = act
        return act
    for dx, dy, act in DIRS:
        if (x + dx, y + dy) == next_cell:
            S["last"] = act
            S["target"] = next_cell
            return act
    S["last"] = SEARCH
    return SEARCH
