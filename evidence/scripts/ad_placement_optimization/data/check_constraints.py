#!/usr/bin/env python3
"""Independent constraint check of the 50 grading inputs against the README/AHC001 constraints.
Usage: check_constraints.py CASES_DIR"""
import os, sys, hashlib, re
d = sys.argv[1]; bad = []; hashes = {}; ns = []
for f in sorted(os.listdir(d)):
    raw = open(os.path.join(d, f), 'rb').read(); hashes.setdefault(hashlib.sha256(raw).hexdigest(), []).append(f)
    lines = raw.decode('ascii').split('\n')
    if lines[-1] != '': bad.append((f, 'no final newline'))
    lines = [l for l in lines if l != '']
    n = int(lines[0]); ns.append(n)
    if not (50 <= n <= 200) or len(lines) != n + 1: bad.append((f, 'n/lines')); continue
    pts = set(); rs = 0
    for l in lines[1:]:
        if not re.fullmatch(r'\d+ \d+ \d+', l): bad.append((f, 'format ' + l)); continue
        x, y, r = map(int, l.split())
        if not (0 <= x <= 9999 and 0 <= y <= 9999 and r >= 1): bad.append((f, 'range ' + l))
        pts.add((x, y)); rs += r
    if len(pts) != n: bad.append((f, 'duplicate point'))
    if rs != 10**8: bad.append((f, 'sum r = %d' % rs))
print('cases', len(ns), 'n range', min(ns), max(ns), 'sum n', sum(ns))
print('byte duplicates', [v for v in hashes.values() if len(v) > 1])
print('failures', bad)
