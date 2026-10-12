#!/usr/bin/env python3
"""Header ("N K T") and exact-byte match of grading cases against gen.py seeds lo..hi.
Usage: seeds_header.py <gen.py dir> <cases_dir> <lo> <hi>"""
import sys, os, hashlib
sys.path.insert(0, sys.argv[1])
from gen import generate
cd = sys.argv[2]
heads = {}; hashes = {}
for f in sorted(os.listdir(cd)):
    b = open(os.path.join(cd, f), 'rb').read()
    heads.setdefault(b.split(b'\n', 1)[0].decode(), []).append(f)
    hashes[hashlib.sha256(b).hexdigest()] = f
hh = 0; ex = 0
for s in range(int(sys.argv[3]), int(sys.argv[4]) + 1):
    t = generate(s)
    hd = t.split('\n', 1)[0]
    if hd in heads:
        hh += 1; print('HEADER_MATCH seed', s, hd, heads[hd])
    if hashlib.sha256(t.encode()).hexdigest() in hashes:
        ex += 1; print('EXACT_MATCH seed', s, hashes[hashlib.sha256(t.encode()).hexdigest()])
print('range', sys.argv[3], sys.argv[4], 'header_matches', hh, 'exact_matches', ex)
