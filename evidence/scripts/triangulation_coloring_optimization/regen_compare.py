#!/usr/bin/env python3
"""Regenerate files with shipped gen.generate() and compare bytes to a target.
Usage: python3 -I regen_compare.py <tools/src> target.txt seed k x y
(has_collinear_triple replaced by an equivalent fast exact test.)"""
import sys, os, hashlib
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen
from check_geometry import collinear_triples
gen.has_collinear_triple = lambda pts: collinear_triples(pts) > 0
tgt = open(sys.argv[2]).read()
seed, k, x, y = map(int, sys.argv[3:7])
out = gen.generate(seed, 512, k, x, y)
print(sys.argv[2], "seed", seed, "k", k, "identical" if out == tgt else "DIFFERENT",
      hashlib.sha256(out.encode()).hexdigest()[:16], hashlib.sha256(tgt.encode()).hexdigest()[:16])
if out != tgt:
    a, b = out.split("\n"), tgt.split("\n")
    print(" first lines equal:", sum(1 for _ in __import__('itertools').takewhile(lambda p: p[0] == p[1], zip(a, b))))
