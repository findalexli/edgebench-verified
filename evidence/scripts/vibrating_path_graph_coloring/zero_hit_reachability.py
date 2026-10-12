#!/usr/bin/env python3
"""For each official case, decide whether a zero-hit answer (Q=0) can ever be valid,
i.e. whether the input graph is K-colorable.

Certificates (exact, independent of the tester):
  K=1: any edge.  K=2: an odd cycle (BFS 2-coloring conflict).
  K=3/K=4 with a (K+1)-clique: a K_{K+1} subgraph.
Otherwise (N=10000, K in {3,4}) report the first-moment bound on the probability that
the published generator (uniform simple graph with M edges) yields a K-colorable graph:
  P <= K^N * ((1-1/K) * N/(N-1))^M      (union bound over colorings; for a fixed
  colouring the non-monochromatic pairs are at most (1-1/K)N^2/2 of N(N-1)/2 pairs,
  and sampling M distinct pairs uniformly avoids monochromatic pairs w.p. <= ratio^M).
Usage: zero_hit_reachability.py <cases_dir>
"""
import sys, os, math, itertools, collections
from fractions import Fraction

def load(p):
    d = open(p).read().split()
    N, M, K = int(d[0]), int(d[1]), int(d[2])
    off = 3 + N
    edges = [(int(d[off+3*i])-1, int(d[off+3*i+1])-1) for i in range(M)]
    return N, M, K, edges

def odd_cycle(N, adj):
    col = [-1]*N
    for s in range(N):
        if col[s] >= 0 or not adj[s]: continue
        col[s] = 0; q = collections.deque([s])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if col[v] < 0: col[v] = col[u]^1; q.append(v)
                elif col[v] == col[u]: return (u, v)
    return None

def clique(adj, size):
    # greedy-ordered search for a clique of given size
    N = len(adj)
    order = sorted(range(N), key=lambda x: -len(adj[x]))
    def ext(cl, cand):
        if len(cl) == size: return cl
        for v in list(cand):
            r = ext(cl+[v], cand & adj[v])
            if r: return r
            cand = cand - {v}
            if len(cl) + len(cand) < size: break
        return None
    for v in order:
        r = ext([v], set(w for w in adj[v] if w > v) )
        if r: return r
    return None

def log_first_moment(N, M, K):
    if K == 1: return float("-inf")
    return N*math.log(K) + M*(math.log(1-1/K) + math.log(N/(N-1)))

def main(cd):
    rows = []
    for f in sorted(os.listdir(cd)):
        N, M, K, E = load(os.path.join(cd, f))
        es = set((min(u,v), max(u,v)) for u, v in E)
        assert len(es) == M and all(u != v for u, v in E), f
        adj = [set() for _ in range(N)]
        for u, v in E: adj[u].add(v); adj[v].add(u)
        cert = None
        if K == 1: cert = f"edge {E[0][0]+1}-{E[0][1]+1}"
        elif K == 2:
            oc = odd_cycle(N, adj); cert = f"odd-cycle conflict at edge {oc[0]+1}-{oc[1]+1}" if oc else None
        elif N <= 1000:
            c = clique(adj, K+1)
            if c:
                assert all(b in adj[a] for a, b in itertools.combinations(c, 2))
                cert = f"K{K+1} clique {[x+1 for x in c]}"
        lb = log_first_moment(N, M, K)
        rows.append((f, N, K, cert, lb))
        print(f"{f} N={N} K={K} cert={cert} ln(P_gen K-colorable)<={lb:.1f}", flush=True)
    nc = sum(1 for r in rows if r[3])
    print(f"CASES {len(rows)} EXACT_CERTIFIED_NOT_K_COLORABLE {nc} BOUND_ONLY {len(rows)-nc} MAX_LN_BOUND {max(r[4] for r in rows if not r[3]) if nc<len(rows) else None}")

if __name__ == "__main__":
    main(sys.argv[1])
