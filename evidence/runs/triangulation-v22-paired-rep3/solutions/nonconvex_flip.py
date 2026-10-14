"""Trigger: do-nothing colours plus ONE flip of an edge whose quadrilateral is NOT convex
(apexes on opposite sides of uv, but u and v on the same side of ab). The README forbids it."""
import sys

def main():
    t = sys.stdin.read().split()
    n, m = int(t[0]), int(t[1]); s = t[6]; i = 7
    pts = []
    for _ in range(n):
        pts.append((int(t[i]), int(t[i + 1]))); i += 2
    e2t = {}
    for _ in range(m):
        tr = tuple(sorted(int(t[i + k]) - 1 for k in range(3))); i += 3
        a, b, c = tr
        for e in ((a, b), (b, c), (a, c)):
            e2t.setdefault(e, []).append(tr)
    def orient(p, q, r):
        return (q[0]-p[0])*(r[1]-p[1]) - (q[1]-p[1])*(r[0]-p[0])
    for (u, v) in sorted(e2t):
        ts = e2t[(u, v)]
        if len(ts) != 2:
            continue
        a = next(x for x in ts[0] if x not in (u, v)); b = next(x for x in ts[1] if x not in (u, v))
        if a == b:
            continue
        s1, s2 = orient(pts[u], pts[v], pts[a]), orient(pts[u], pts[v], pts[b])
        s3, s4 = orient(pts[a], pts[b], pts[u]), orient(pts[a], pts[b], pts[v])
        if s1 * s2 < 0 and s3 * s4 > 0:
            print("0 1"); print(s); print(u + 1, v + 1); return
    print("0 0"); print(s)

main()
