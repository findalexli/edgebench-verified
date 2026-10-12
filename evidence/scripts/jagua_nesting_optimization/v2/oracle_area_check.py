"""Independent oracle for the v2 overlap_area(): exact rational Sutherland-Hodgman
clipping of a random simple (star-shaped, possibly concave) polygon A against a random
convex polygon B (SH is exact for a convex clip polygon). Integer coordinates.
Usage: python3 oracle_area_check.py <v2 evaluate.py> [n_trials]"""
import importlib.util, math, random, sys
from fractions import Fraction as F
s = importlib.util.spec_from_file_location("E", sys.argv[1]); E = importlib.util.module_from_spec(s)
sys.modules["E"] = E; s.loader.exec_module(E)
N = int(sys.argv[2]) if len(sys.argv) > 2 else 3000

def area(p):
    return sum(p[i][0] * p[(i+1) % len(p)][1] - p[(i+1) % len(p)][0] * p[i][1] for i in range(len(p))) / 2

def hull(pts):
    pts = sorted(set(pts))
    def cr(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]

def clip(subject, clipper):  # clipper convex, CCW
    out = [(F(x), F(y)) for x, y in subject]
    for i in range(len(clipper)):
        a, b = clipper[i], clipper[(i+1) % len(clipper)]
        inside = lambda p: (b[0]-a[0])*(p[1]-a[1]) - (b[1]-a[1])*(p[0]-a[0]) >= 0
        inp, out = out, []
        if not inp: break
        for j in range(len(inp)):
            p, q = inp[j], inp[(j+1) % len(inp)]
            if inside(q):
                if not inside(p): out.append(inter(p, q, a, b))
                out.append(q)
            elif inside(p):
                out.append(inter(p, q, a, b))
    return out

def inter(p, q, a, b):
    x1, y1, x2, y2 = p[0], p[1], q[0], q[1]; x3, y3, x4, y4 = F(a[0]), F(a[1]), F(b[0]), F(b[1])
    d = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)
    t = ((x1-x3)*(y3-y4) - (y1-y3)*(x3-x4)) / d
    return (x1 + t*(x2-x1), y1 + t*(y2-y1))

def seg_touch(p, q, r, t):
    def o(a, b, c): return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])
    def on(a, b, c): return min(a[0], b[0]) <= c[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= c[1] <= max(a[1], b[1])
    d1, d2, d3, d4 = o(r, t, p), o(r, t, q), o(p, q, r), o(p, q, t)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) and d1 and d2 and d3 and d4: return True
    return (d1 == 0 and on(r, t, p)) or (d2 == 0 and on(r, t, q)) or (d3 == 0 and on(p, q, r)) or (d4 == 0 and on(p, q, t))

def simple(P):
    n = len(P); E = [(P[i], P[(i+1) % n]) for i in range(n)]
    for i in range(n):
        for j in range(i+1, n):
            if j == i+1 or (i == 0 and j == n-1): continue
            if seg_touch(*E[i], *E[j]): return False
    return True

def star(rng, cx, cy):
    k = rng.randint(3, 14); angs = sorted(rng.uniform(0, 2*math.pi) for _ in range(k))
    pts = []
    for a in angs:
        r = rng.randint(2, 30)
        pts.append((cx + round(r*math.cos(a)), cy + round(r*math.sin(a))))
    pts = [p for i, p in enumerate(pts) if p != pts[i-1]]
    return pts

rng = random.Random(12345); bad = 0; tested = 0; maxerr = 0.0; contact = 0
for t in range(N):
    A = star(rng, rng.randint(0, 20), rng.randint(0, 20))
    B = hull([(rng.randint(-5, 45), rng.randint(-5, 45)) for _ in range(rng.randint(3, 9))])
    if len(A) < 3 or len(B) < 3 or area(A) <= 0 or area(B) <= 0 or not simple(A):
        continue
    # skip non-simple A (star polygons with duplicate angles can self-touch)
    try:
        exact = abs(area(clip(A, B))) if True else 0
    except ZeroDivisionError:
        continue
    for X, Y in ((A, B), (B, A)):
        got = E.overlap_area([tuple(map(float, p)) for p in X], [tuple(map(float, p)) for p in Y])
        tested += 1; err = abs(got - float(exact)); maxerr = max(maxerr, err)
        if exact == 0: contact += 1
        if err > 1e-6 * max(1.0, float(exact)):
            bad += 1
            if bad <= 5: print("MISMATCH", X, Y, got, float(exact))
print(f"tested={tested} mismatches={bad} max_abs_err={maxerr:.3g} zero_area_cases={contact}")
