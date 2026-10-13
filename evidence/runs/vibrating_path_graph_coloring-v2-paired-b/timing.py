# Summarise per-process timing files (/ebvtiming/<pid>.txt) per arm: processes, finished, killed (no end line),
# wall and CPU seconds of the finished ones.
import sys, glob, os, statistics
for d in sorted(glob.glob(sys.argv[1] + '/*')):
    walls, cpus, noend = [], [], 0
    for f in glob.glob(d + '/*.txt'):
        e = [l for l in open(f).read().split('\n') if l.startswith('end')]
        if not e: noend += 1; continue
        p = e[0].split(); walls.append(float(p[3])); cpus.append(float(p[5]))
    n = len(walls) + noend
    if walls:
        print(f"{os.path.basename(d):22s} n={n:3d} finished={len(walls):3d} killed={noend:3d} "
              f"wall min/med/max={min(walls):.2f}/{statistics.median(walls):.2f}/{max(walls):.2f} "
              f"cpu min/mean/med/max={min(cpus):.2f}/{statistics.mean(cpus):.2f}/{statistics.median(cpus):.2f}/{max(cpus):.2f}")
    else:
        print(f"{os.path.basename(d):22s} n={n:3d} finished=0 killed={noend}")
