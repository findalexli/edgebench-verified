"""Honest simple TRICOL solution: greedy recolouring, then greedy README-legal (convex) flips.
Uses only the README contract; no tester internals."""
import sys

def main():
    t = sys.stdin.read().split()
    n, m, X, Y, P, Q = (int(v) for v in t[:6]); s = t[6]; i = 7
    pts = []
    for _ in range(n):
        pts.append((int(t[i]), int(t[i + 1]))); i += 2
    tris = []
    for _ in range(m):
        tris.append(tuple(sorted(int(t[i + k]) - 1 for k in range(3)))); i += 3
    col = list(s)
    def ugly(tr):
        a, b, c = tr
        return col[a] == col[b] or col[b] == col[c] or col[a] == col[c]
    inc = [[] for _ in range(n)]
    for k, tr in enumerate(tris):
        for v in tr:
            inc[v].append(k)
    U = sum(ugly(tr) for tr in tris)
    C = 0
    # greedy recolouring: accept a change only if it lowers X*C + U^2
    improved = True
    while improved:
        improved = False
        for v in range(n):
            cur = col[v]
            base = sum(ugly(tris[k]) for k in inc[v])
            best = None
            for c in "RGB":
                if c == cur:
                    continue
                col[v] = c
                nu = U - base + sum(ugly(tris[k]) for k in inc[v])
                nc = C + (c != s[v]) - (cur != s[v])
                col[v] = cur
                if nc > P:
                    continue
                gain = (X * C + U * U) - (X * nc + nu * nu)
                if gain > 0 and (best is None or gain > best[0]):
                    best = (gain, c, nu, nc)
            if best:
                _, col[v], U, C = best
                improved = True
    # greedy convex flips (README rule): accept if U^2 drop exceeds Y
    def orient(p, q, r):
        return (q[0]-p[0])*(r[1]-p[1]) - (q[1]-p[1])*(r[0]-p[0])
    alive = set(range(len(tris)))
    e2t = {}
    def add(k):
        a, b, c = tris[k]
        for e in ((a, b), (b, c), (a, c)):
            e2t.setdefault(e, set()).add(k)
    def rem(k):
        a, b, c = tris[k]
        for e in ((a, b), (b, c), (a, c)):
            e2t[e].discard(k)
            if not e2t[e]:
                del e2t[e]
    for k in range(len(tris)):
        add(k)
    flips = []
    improved = True
    while improved and len(flips) < Q:
        improved = False
        for (u, v) in list(e2t):
            if len(flips) >= Q:
                break
            ks = e2t.get((u, v))
            if not ks or len(ks) != 2:
                continue
            k1, k2 = ks
            a = next(x for x in tris[k1] if x not in (u, v))
            b = next(x for x in tris[k2] if x not in (u, v))
            if a == b or (min(a, b), max(a, b)) in e2t:
                continue
            s1, s2 = orient(pts[u], pts[v], pts[a]), orient(pts[u], pts[v], pts[b])
            s3, s4 = orient(pts[a], pts[b], pts[u]), orient(pts[a], pts[b], pts[v])
            if not (s1 * s2 < 0 and s3 * s4 < 0):
                continue
            n1, n2 = tuple(sorted((a, b, u))), tuple(sorted((a, b, v)))
            nu = U - ugly(tris[k1]) - ugly(tris[k2]) + ugly(n1) + ugly(n2)
            if U * U - nu * nu > Y:
                rem(k1); rem(k2)
                tris[k1], tris[k2] = n1, n2
                add(k1); add(k2)
                U = nu
                flips.append((u, v))
                improved = True
    print(C, len(flips))
    print("".join(col))
    for u, v in flips:
        print(u + 1, v + 1)

main()
