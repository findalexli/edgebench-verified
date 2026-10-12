#!/usr/bin/env python3
"""Regenerate TRICOL inputs with the shipped gen.py/delaunay.py and a chosen triangulation.py.

Usage: python3 -I regen_v2.py <dir with triangulation.py> <dir with gen.py,delaunay.py> <outdir>
Writes cases/0000..0009.txt and sample_data/0000..0002.txt from the PARAMS table below.
Only change to the shipped generator path: gen.has_collinear_triple is replaced by an exactly
equivalent O(N^2 log N) exact-integer test (same boolean), so N=512 runs quickly.
"""
import hashlib, os, sys
tri_dir, gen_dir, out = sys.argv[1:4]
sys.path[:0] = [tri_dir, gen_dir, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))]
import triangulation, gen  # triangulation resolved from tri_dir first
assert os.path.dirname(os.path.abspath(triangulation.__file__)) == os.path.abspath(tri_dir)
from check_geometry import collinear_triples
gen.has_collinear_triple = lambda pts: collinear_triples(pts) > 0

# (file, seed, K, X, Y). Seeds/K for cases/0000 and all samples are recovered exactly
# (byte-for-byte reproduction of the originals with the original triangulation.py).
# cases/0001..0009: original seeds NOT recovered; seeds 9000000+i are new, K inferred
# from the original defect profile (16 for 0000-0004, 256 for 0005-0009); X,Y copied
# from each original file header. P=256, Q=1024 (gen defaults) as in every original.
PARAMS = [("cases/%04d.txt" % i, 9000000 + i, 16 if i < 5 else 256, x, y)
          for i, (x, y) in enumerate([(10,160),(20,80),(40,40),(80,20),(160,10)] * 2)]
PARAMS += [("sample_data/0000.txt", 1000001, 16, 10, 160),
           ("sample_data/0001.txt", 1000002, 16, 40, 40),
           ("sample_data/0002.txt", 1000003, 256, 80, 20)]
only = sys.argv[4:]
for name, seed, k, x, y in PARAMS:
    if only and name not in only:
        continue
    txt = gen.generate(seed, 512, k, x, y)
    path = os.path.join(out, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write(txt)
    print(name, seed, k, x, y, hashlib.sha256(txt.encode()).hexdigest(), flush=True)
