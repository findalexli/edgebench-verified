#!/usr/bin/env python3
"""Independent exact-rational oracle for ad_placement_optimization (AHC001 rules as stated in
the task README). Written from the README, not from the tester source.

README rules: n rectangles "a b c d", integers, 0 <= a < c <= 10000, 0 <= b < d <= 10000;
different rectangles may share edges but common area must be zero; p_i = 0 if the rectangle
does not contain (x_i+0.5, y_i+0.5), else 1 - (1 - min(r,s)/max(r,s))^2;
score = round(1e9 * sum p_i / n).

Rounding: exact rational, half away from zero (Rust f64::round semantics). The oracle also
reports the f64 left-to-right evaluation and flags any case where the two would differ.

Usage: oracle.py INPUT OUTPUT   -> prints JSON {status, score, reason, ...}
"""
import json, re, sys
from fractions import Fraction as F

W = 10000


def read_input(path):
    tok = open(path).read().split()
    n = int(tok[0])
    pts = [(int(tok[1 + 3 * i]), int(tok[2 + 3 * i]), int(tok[3 + 3 * i])) for i in range(n)]
    return n, pts


def round_half_away(q):
    fl = q.numerator // q.denominator
    frac = q - fl
    return fl + 1 if frac >= F(1, 2) else fl  # q >= 0 here


def judge(n, pts, out_text):
    tok = out_text.split()  # str.split(): any whitespace incl. \r, \t
    if len(tok) < 4 * n:
        return {"status": "WA", "reason": "too few tokens"}
    if len(tok) > 4 * n:
        return {"status": "WA", "reason": "too many tokens"}
    rects = []
    for i in range(n):
        ts = tok[4 * i:4 * i + 4]
        if not all(re.fullmatch(r"[+-]?[0-9]+", t) for t in ts):  # decimal integer tokens only
            return {"status": "WA", "reason": f"non-integer token in rectangle {i}"}
        a, b, c, d = (int(t) for t in ts)
        if not (0 <= a < c <= W and 0 <= b < d <= W):
            return {"status": "WA", "reason": f"rectangle {i} out of range or not positive area"}
        rects.append((a, b, c, d))
    # README rule: every pair must have zero common area (all pairs, order independent)
    overlaps = []
    order = sorted(range(n), key=lambda i: rects[i][0])
    for ii in range(n):  # sweep on x
        i = order[ii]
        for jj in range(ii + 1, n):
            j = order[jj]
            if rects[j][0] >= rects[i][2]:
                break
            ow = min(rects[i][2], rects[j][2]) - max(rects[i][0], rects[j][0])
            oh = min(rects[i][3], rects[j][3]) - max(rects[i][1], rects[j][1])
            if ow > 0 and oh > 0:
                overlaps.append((min(i, j), max(i, j), ow * oh))
    contains = [rects[i][0] <= pts[i][0] < rects[i][2] and rects[i][1] <= pts[i][1] < rects[i][3]
                for i in range(n)]
    # What the original AHC001 scorer loop would reject: overlap (j<i) checked only when rect i
    # contains its own point.
    quirk_rejects = [o for o in overlaps if contains[o[1]]]
    total = F(0)
    total_f = 0.0
    for i in range(n):
        if not contains[i]:
            continue
        a, b, c, d = rects[i]
        s, r = (c - a) * (d - b), pts[i][2]
        q = F(min(s, r), max(s, r))
        total += 1 - (1 - q) ** 2
        qf = min(s, r) / max(s, r)
        total_f += 1.0 - (1.0 - qf) * (1.0 - qf)
    exact = F(10 ** 9) * total / n
    score = round_half_away(exact)
    f64 = 1e9 * total_f / n
    f64_round = int(f64 + 0.5) if f64 >= 0 else -int(-f64 + 0.5)
    res = {"status": "OK" if not overlaps else "WA",
           "score": score if not overlaps else 0,
           "unrejected_score": score, "f64_score": f64_round,
           "f64_matches_exact": f64_round == score,
           "dist_to_half": float(abs(exact - (exact.numerator // exact.denominator) - F(1, 2))),
           "n_contain": sum(contains), "overlaps": overlaps[:5], "n_overlaps": len(overlaps),
           "original_loop_would_reject": bool(quirk_rejects),
           "area_sum": sum((c - a) * (d - b) for a, b, c, d in rects)}
    if overlaps:
        res["reason"] = f"{len(overlaps)} overlapping pair(s)"
    return res


if __name__ == "__main__":
    n, pts = read_input(sys.argv[1])
    raw = open(sys.argv[2], "rb").read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        print(json.dumps({"status": "WA", "reason": "not utf-8"})); sys.exit()
    print(json.dumps(judge(n, pts, text)))
