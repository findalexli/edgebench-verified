#!/usr/bin/env python3
"""Independent exact optimum (Dijkstra over full tester state, tester rules) with path
reconstruction; every optimal string is re-validated by the ORIGINAL tester bytes.
Checks L(R,C)=2RC(R+C-1)-6(R+C-2)-2 (proved in Lean) and the too-strong L'=2RC(R+C-1)-2.
Usage: brute_force.py <tester> <outdir> [max_orders_per_grid]"""
import sys, heapq, itertools, random, subprocess, os, time

DIRS = {'N': (-1, 0), 'S': (1, 0), 'W': (0, -1), 'E': (0, 1)}

def opt(R, C, arr):
    n = R * C - 1
    start = (tuple([0] * (R * C)), 0, 0, 0, 0)  # grid, pos, carry, arrived, dispatched
    dist = {start: 0}; prev = {}
    pq = [(0, start)]
    while pq:
        d, st = heapq.heappop(pq)
        if dist[st] != d: continue
        grid, p, cy, k, dp = st
        if dp == n:
            out = []; cur = st
            while cur in prev:
                cur, tok = prev[cur]; out.append(tok)
            return d, ''.join(reversed(out))
        r, c = divmod(p, C); succ = []
        for ch, (dr, dc) in DIRS.items():
            rr, cc = r + dr, c + dc
            if not (0 <= rr < R and 0 <= cc < C): continue
            q = rr * C + cc
            if cy == 0 or grid[q] == 0:
                succ.append((1, ch, (grid, q, cy, k, dp)))
            if cy == 0 and grid[q] != 0:
                g = list(grid); g[q] = 0
                succ.append((2, 'L' + ch, (tuple(g), p, grid[q], k, dp)))
            if cy != 0 and grid[q] == 0:
                g = list(grid); g[q] = cy
                succ.append((2, 'U' + ch, (tuple(g), p, 0, k, dp)))
        if p == 0 and cy == 0 and k < n:
            succ.append((1, 'P', (grid, p, arr[k], k + 1, dp)))
        if p == 0 and cy != 0 and k == n and cy == dp + 1:
            succ.append((1, 'D', (grid, p, 0, k, dp + 1)))
        for w, tok, s2 in succ:
            nd = d + w
            if nd < dist.get(s2, 1 << 60):
                dist[s2] = nd; prev[s2] = (st, tok); heapq.heappush(pq, (nd, s2))
    return None

L = lambda R, C: 2 * R * C * (R + C - 1) - 6 * (R + C - 2) - 2
Lstrong = lambda R, C: 2 * R * C * (R + C - 1) - 2

if __name__ == "__main__":
    tester, outdir = sys.argv[1], sys.argv[2]
    cap = int(sys.argv[3]) if len(sys.argv) > 3 else 200
    os.makedirs(outdir, exist_ok=True)
    random.seed(12345)
    grids = [(1, 2), (2, 1), (1, 3), (3, 1), (1, 4), (4, 1), (1, 5), (2, 2), (2, 3), (3, 2), (2, 4), (4, 2)]
    viol = 0; strong_viol = 0; tester_bad = 0; ncase = 0
    for (R, C) in grids:
        n = R * C - 1
        perms = [p for p in itertools.permutations(range(1, n + 1)) if p[-1] != 1]
        if not perms: continue
        exhaustive = len(perms) <= cap
        if not exhaustive:
            perms = random.sample(perms, 12)
        best = None; t0 = time.time()
        for perm in perms:
            S, s = opt(R, C, list(perm))
            assert len(s) == S
            # validate with original tester
            fi = os.path.join(outdir, 'in.txt'); fo = os.path.join(outdir, 'out.txt')
            open(fi, 'w').write("1\n%d %d\n%s\n" % (R, C, ' '.join(map(str, perm))))
            open(fo, 'w').write(s + "\n")
            pr = subprocess.run([sys.executable, '-I', tester, fi, fo], capture_output=True, text=True)
            if pr.returncode != 0: tester_bad += 1
            ncase += 1
            viol += S < L(R, C); strong_viol += S < Lstrong(R, C)
            if best is None or S < best[0]: best = (S, perm, s)
        print("%dx%d orders=%d (%s) min_opt=%d L=%d L'=%d  slack_min=%d  example=%s %s  [%.1fs]" % (
            R, C, len(perms), 'exhaustive' if exhaustive else 'random sample', best[0], L(R, C), Lstrong(R, C),
            best[0] - L(R, C), ' '.join(map(str, best[1])), best[2], time.time() - t0), flush=True)
    print("instances", ncase, "| L violations", viol, "| L' (too strong) violations", strong_viol,
          "| optimal strings rejected by original tester", tester_bad)
