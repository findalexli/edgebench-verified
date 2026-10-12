#!/usr/bin/env python3
"""Independent oracle for grid_turing_robot, written from README.md text only
(does not import tools/src/verifier.py).

Subcommands:
  data  <cases_dir>              structural checks of every case + baseline sum
  score <case> <output>          independent score of one output (prints raw cost or INVALID)
  scoreall <cases_dir> <out_dir> score every <out_dir>/<case>.out, print per-case and sum
  brute                          tiny-instance brute force of minimum C+Q (see docstring of brute())
"""
import sys, os, itertools
from collections import deque

DIRS = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}


def read_case(path):
    tok = open(path).read().split('\n')
    N, K, T = map(int, tok[0].split())
    v = [tok[1 + i].strip() for i in range(N)]
    h = [tok[1 + N + i].strip() for i in range(N - 1)]
    tg = [tuple(map(int, tok[2 * N + i].split())) for i in range(K)]
    return N, K, T, v, h, tg


def passable(N, v, h, i, j, d):
    # README: v_{i,j}='1' wall between (i,j),(i,j+1); h_{i,j}='1' wall between (i,j),(i+1,j)
    ni, nj = i + DIRS[d][0], j + DIRS[d][1]
    if not (0 <= ni < N and 0 <= nj < N):
        return False
    if d == 'R': return v[i][j] == '0'
    if d == 'L': return v[i][j - 1] == '0'
    if d == 'D': return h[i][j] == '0'
    if d == 'U': return h[i - 1][j] == '0'


def bfs(N, v, h, s):
    dist = {s: 0}
    q = deque([s])
    while q:
        c = q.popleft()
        for d in 'UDLR':
            if passable(N, v, h, c[0], c[1], d):
                n = (c[0] + DIRS[d][0], c[1] + DIRS[d][1])
                if n not in dist:
                    dist[n] = dist[c] + 1
                    q.append(n)
    return dist


def simulate(N, K, T, v, h, tg, init, rules):
    """README semantics: start at target 0 in state 0; each step reads (c,q),
    repaints, updates state, moves unless wall/'S'. A target counts only when it is
    the current one. Missing rule => robot cannot continue (halt)."""
    g = [row[:] for row in init]
    pos = tg[0]; q = 0; V = 1
    for _ in range(T):
        if V == K:
            break
        c = g[pos[0]][pos[1]]
        if (c, q) not in rules:
            break
        a, s, d = rules[(c, q)]
        g[pos[0]][pos[1]] = a
        q = s
        if d != 'S' and passable(N, v, h, pos[0], pos[1], d):
            pos = (pos[0] + DIRS[d][0], pos[1] + DIRS[d][1])
        if pos == tg[V]:
            V += 1
    return V


def score(case, out):
    N, K, T, v, h, tg = read_case(case)
    lines = open(out).read().split('\n')
    try:
        C, Q, M = map(int, lines[0].split()[:3])
        assert 1 <= C <= N ** 4 and 1 <= Q <= N ** 4 and 0 <= M <= T, 'header range'
        init = [list(map(int, lines[1 + i].split())) for i in range(N)]
        assert all(len(r) == N and all(0 <= x < C for x in r) for r in init), 'grid'
        rules = {}
        for k in range(M):
            p = lines[1 + N + k].split()
            c, q, a, s = map(int, p[:4]); d = p[4]
            assert (c, q) not in rules, 'dup'
            assert 0 <= c < C and 0 <= a < C and 0 <= q < Q and 0 <= s < Q, 'rule range'
            assert d in 'UDLRS' and len(d) == 1, 'dir'
            rules[(c, q)] = (a, s, d)
    except Exception as e:
        return None, repr(e)
    V = simulate(N, K, T, v, h, tg, init, rules)
    if V == K:
        return C + Q, 'full'
    return 2 * N ** 4 + (K - V) * N ** 2, f'partial V={V}/{K}'


def data(cases_dir):
    tot_base = 0
    rows = []
    for f in sorted(os.listdir(cases_dir)):
        N, K, T, v, h, tg = read_case(os.path.join(cases_dir, f))
        assert 10 <= N <= 20 and N <= K <= N * N
        assert len(v) == N and all(len(r) == N - 1 and set(r) <= {'0', '1'} for r in v)
        assert len(h) == N - 1 and all(len(r) == N and set(r) <= {'0', '1'} for r in h)
        assert len(set(tg)) == K and all(0 <= a < N and 0 <= b < N for a, b in tg)
        d0 = bfs(N, v, h, (0, 0))
        conn = len(d0) == N * N
        X = sum(bfs(N, v, h, tg[i - 1])[tg[i]] for i in range(1, K))
        ok = X <= T <= 2 * X
        base = 2 * N ** 4 + (K - 1) * N ** 2
        tot_base += base
        rows.append((f, N, K, T, X, conn, ok, base))
        print(f, f'N={N} K={K} T={T} X={X} connected={conn} X<=T<=2X={ok} baseline_cost={base} lb_C1_stepstate={X+2}')
    print('ALL_CONNECTED', all(r[5] for r in rows), 'ALL_T_IN_RANGE', all(r[6] for r in rows))
    print('BASELINE_SUM', tot_base)
    print('SUM_X_PLUS_2', sum(r[4] + 2 for r in rows))


def scoreall(cases_dir, out_dir):
    tot = 0
    for f in sorted(os.listdir(cases_dir)):
        s, why = score(os.path.join(cases_dir, f), os.path.join(out_dir, f + '.out'))
        print(f, s, why)
        tot = None if (tot is None or s is None) else tot + s
    print('SUM', tot)


def brute():
    """Exhaustive minimum C+Q on tiny hand instances (1x3 and 2x2 open boards,
    3-4 targets): for increasing C+Q, enumerate every initial colouring and every
    rule table (each (c,q) pair either has no rule = halt, or any (A,S,D)).
    Shows C+Q=2 is reachable only when a single repeated direction visits all
    targets, and that the minimum grows with route complexity."""
    insts = [
        ('line3', 1, 3, ['00'], [], [(0, 0), (0, 1), (0, 2)]),
        ('line3_back', 1, 3, ['00'], [], [(0, 1), (0, 2), (0, 0)]),
        ('sq2_cycle', 2, 4, ['0', '0'], ['00'], [(0, 0), (0, 1), (1, 1), (1, 0)]),
        ('sq2_zig', 2, 4, ['0', '0'], ['00'], [(0, 0), (1, 1), (0, 1), (1, 0)]),
    ]
    for name, N, K, v, h, tg in insts:
        # dimensions: N rows x width from v
        W = len(v[0]) + 1 if v and v[0] != '' else 1
        best = None
        skipped = []
        for CQ in range(2, 6):
            for C in range(1, CQ):
                Q = CQ - C
                pairs = [(c, q) for c in range(C) for q in range(Q)]
                acts = [None] + [(a, s, d) for a in range(C) for s in range(Q) for d in 'UDLRS']
                if len(acts) ** len(pairs) * C ** (N * W) > 4_000_000:
                    skipped.append((C, Q))
                    continue
                found = False
                T = 4 * K * (N + W)
                for init_flat in itertools.product(range(C), repeat=N * W):
                    init = [list(init_flat[r * W:(r + 1) * W]) for r in range(N)]
                    for tab in itertools.product(acts, repeat=len(pairs)):
                        rules = {p: t for p, t in zip(pairs, tab) if t is not None}
                        if simulate_rect(N, W, K, T, v, h, tg, init, rules) == K:
                            found = True; break
                    if found: break
                if found:
                    best = CQ; break
            if best: break
        print('BRUTE', name, 'min C+Q =', best, 'skipped (C,Q) combos (not enumerated):', skipped)


def simulate_rect(N, W, K, T, v, h, tg, init, rules):
    def pas(i, j, d):
        ni, nj = i + DIRS[d][0], j + DIRS[d][1]
        if not (0 <= ni < N and 0 <= nj < W): return False
        if d == 'R': return v[i][j] == '0'
        if d == 'L': return v[i][j - 1] == '0'
        if d == 'D': return h[i][j] == '0'
        return h[i - 1][j] == '0'
    g = [r[:] for r in init]; pos = tg[0]; q = 0; V = 1
    for _ in range(T):
        if V == K: break
        c = g[pos[0]][pos[1]]
        if (c, q) not in rules: break
        a, s, d = rules[(c, q)]
        g[pos[0]][pos[1]] = a; q = s
        if d != 'S' and pas(pos[0], pos[1], d):
            pos = (pos[0] + DIRS[d][0], pos[1] + DIRS[d][1])
        if pos == tg[V]: V += 1
    return V


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'data': data(sys.argv[2])
    elif cmd == 'score': print(*score(sys.argv[2], sys.argv[3]))
    elif cmd == 'scoreall': scoreall(sys.argv[2], sys.argv[3])
    elif cmd == 'brute': brute()
