#!/usr/bin/env python3
"""Exact minimum instruction length on tiny grids by Dijkstra over the full tester state,
under the prompt/tester rules ("prompt") and the CodeChef rules ("original").
Checks the lower bound S >= 2RC(R+C-1) - 6(R+C-2) - 2 (proved for all R,C in the review)
and reproduces the CodeChef sample (2x3, arrivals 3 1 2 4 5; sample length 50).
Note: the problem's grid is R rows x C columns; the sample explanation's (2,1) uses (x,y)."""
import sys, heapq, itertools

DIRS = {'N': (-1, 0), 'S': (1, 0), 'W': (0, -1), 'E': (0, 1)}


def opt(R, C, arr, mode):
    n = R * C - 1
    start = (tuple([0] * (R * C)), 0, 0, 0, 1)   # grid, pos, cargo, k(arrived), nxt(dispatch)
    dist = {start: 0}; pq = [(0, start)]
    while pq:
        d, st = heapq.heappop(pq)
        if dist.get(st) != d:
            continue
        grid, p, cargo, k, nxt = st
        if nxt == n + 1:
            return d
        r, c = divmod(p, C)
        succ = []
        for ch, (dr, dc) in DIRS.items():
            rr, cc = r + dr, c + dc
            if not (0 <= rr < R and 0 <= cc < C):
                continue
            q = rr * C + cc
            if grid[q] == 0 or (cargo == 0 and mode == 'prompt'):
                succ.append((1, (grid, q, cargo, k, nxt)))
            if cargo == 0 and grid[q] != 0:
                g = list(grid); g[q] = 0
                succ.append((2, (tuple(g), p, grid[q], k, nxt)))
            if cargo != 0 and grid[q] == 0:
                g = list(grid); g[q] = cargo
                succ.append((2, (tuple(g), p, 0, k, nxt)))
        if p == 0 and cargo == 0 and k < n:
            succ.append((1, (grid, p, arr[k], k + 1, nxt)))
        if p == 0 and cargo == nxt and k == n:
            succ.append((1, (grid, p, 0, k, nxt + 1)))
        for w, s2 in succ:
            nd = d + w
            if nd < dist.get(s2, 1 << 60):
                dist[s2] = nd; heapq.heappush(pq, (nd, s2))
    return None


def bound(R, C):
    return 2 * R * C * (R + C - 1) - 6 * (R + C - 2) - 2


if __name__ == "__main__":
    print("sample 2x3 [3,1,2,4,5]: prompt-rules opt", opt(2, 3, [3, 1, 2, 4, 5], 'prompt'),
          "original-rules opt", opt(2, 3, [3, 1, 2, 4, 5], 'original'), "bound", bound(2, 3))
    viol = 0
    for (R, C) in [(2, 2), (2, 3), (3, 2)]:
        n = R * C - 1
        for perm in itertools.permutations(range(1, n + 1)):
            if perm[-1] == 1:
                continue
            a = opt(R, C, list(perm), 'prompt'); b = opt(R, C, list(perm), 'original')
            if a < bound(R, C) or (b is not None and b < a):
                viol += 1
            print(R, C, perm, "prompt", a, "original", b, "bound", bound(R, C), "diag", 2 * R * C * (R + C - 1) - 2)
    print("violations", viol)
