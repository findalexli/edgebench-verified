#!/usr/bin/env python3
"""Honest, simple, generic known-good control for warehouse_forklift_routing.

Uses only rules stated in the prompt (an EMPTY forklift may stand on / pass occupied
cells; a CARRYING forklift may only enter empty cells).
Placement: fill non-entrance cells farthest-first (distance r+c descending) along a
monotone path of still-empty cells. Retrieval: for good g, if a carry route through
empty cells exists, use it; otherwise move g one step along a shortest path by
sliding-puzzle hole moves (forklift at hole H: L from A, step into A, U back into H).
Not tuned for score.
"""
import sys
from collections import deque

D = {'N': (-1, 0), 'S': (1, 0), 'W': (0, -1), 'E': (0, 1)}
OPP = {'N': 'S', 'S': 'N', 'W': 'E', 'E': 'W'}


def dir_of(a, b):
    d = (b[0] - a[0], b[1] - a[1])
    for k, v in D.items():
        if v == d:
            return k
    raise ValueError


def solve(R, C, arr):
    out = []
    grid = {}
    pos = [0, 0]

    def walk(t):  # empty forklift: free Manhattan walk
        r, c = pos
        out.append(('S' if t[0] > r else 'N') * abs(t[0] - r))
        out.append(('E' if t[1] > c else 'W') * abs(t[1] - c))
        pos[0], pos[1] = t

    def nbrs(p):
        for k, (dr, dc) in D.items():
            q = (p[0] + dr, p[1] + dc)
            if 0 <= q[0] < R and 0 <= q[1] < C:
                yield k, q

    # ---- placement: farthest first
    cells = sorted(((r, c) for r in range(R) for c in range(C) if (r, c) != (0, 0)),
                   key=lambda p: (-(p[0] + p[1]), p[0], p[1]))
    for good, cell in zip(arr, cells):
        out.append('P')
        r, c = cell
        # monotone path of strictly nearer (hence still empty) cells to a predecessor
        if c == 0:
            path = [(i, 0) for i in range(1, r)]; last_dir = 'S'
        else:
            path = [(i, 0) for i in range(1, r + 1)] + [(r, j) for j in range(1, c)]
            last_dir = 'E'
        cur = (0, 0)
        for q in path:
            assert q not in grid
            out.append(dir_of(cur, q)); cur = q
        out.append('U' + last_dir)
        grid[cell] = good
        back = [(0, 0)] + path[:-1]
        if path:
            for q in reversed(back):
                out.append(dir_of(cur, q)); cur = q
        pos[0], pos[1] = 0, 0
    where = {g: p for p, g in grid.items()}

    def swap_hole(H, A):
        # forklift at hole H, good at A adjacent: good moves A->H, hole -> A
        walk(H)
        d = dir_of(H, A)
        out.append('L' + d); out.append(d); out.append('U' + OPP[d])
        g = grid.pop(A); grid[H] = g; where[g] = H
        pos[0], pos[1] = A

    def carry_route(p):
        """Return (X, route) with X adjacent to p, route X->...->(0,0) via empty cells."""
        if p == (0, 0):  # stand on (0,1) (may be occupied), load W, carry into vacated entrance
            return (0, 1), [(0, 1), (0, 0)]
        if (0, 0) in grid:
            for _, q in nbrs(p):
                if q == (0, 0):
                    return (0, 0), []
            return None
        par = {(0, 0): None}
        dq = deque([(0, 0)])
        while dq:
            u = dq.popleft()
            for _, q in nbrs(u):
                if q not in par and q not in grid:
                    par[q] = u; dq.append(q)
        best = None
        for _, X in nbrs(p):
            if X in par:
                cand = X
            else:
                cand = None
                for _, y in nbrs(X):
                    if y in par:
                        cand = y; break
            if cand is None:
                continue
            route = []
            u = cand
            while u is not None:
                route.append(u); u = par[u]
            if X not in par:
                route = [X] + route
            if best is None or len(route) < len(best[1]):
                best = (X, route)
        return best

    for g in range(1, R * C):
        while True:
            p = where[g]
            cr = carry_route(p)
            if cr is not None:
                X, route = cr
                walk(X)
                out.append('L' + dir_of(X, p))
                del grid[p]; del where[g]
                cur = X
                for q in route[1:]:
                    out.append(dir_of(cur, q)); cur = q
                out.append('D')
                pos[0], pos[1] = 0, 0
                break
            # one step of g toward (0,0)
            tgt = (p[0] - 1, p[1]) if p[0] > 0 else (p[0], p[1] - 1)
            if tgt in grid:
                # bring a hole to tgt avoiding p
                par = {tgt: None}; dq = deque([tgt]); E = None
                while dq:
                    u = dq.popleft()
                    if u not in grid:
                        E = u; break
                    for _, q in nbrs(u):
                        if q not in par and q != p:
                            par[q] = u; dq.append(q)
                u = E
                while par[u] is not None:
                    swap_hole(u, par[u]); u = par[u]
            swap_hole(tgt, p)
    return ''.join(out)


def main():
    data = sys.stdin.read().split()
    i = 0; T = int(data[i]); i += 1
    res = []
    for _ in range(T):
        R, C = int(data[i]), int(data[i + 1]); i += 2
        n = R * C - 1
        arr = [int(x) for x in data[i:i + n]]; i += n
        res.append(solve(R, C, arr))
    sys.stdout.write('\n'.join(res) + '\n')


main()
