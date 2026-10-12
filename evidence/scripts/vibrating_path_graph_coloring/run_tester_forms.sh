#!/bin/sh
# Runs the ORIGINAL tester (and the original eval helper) inside the pinned judge image.
# Usage: run_tester_forms.sh  (from any dir; uses ./inputs next to this script)
set -u
IMG=seededge/edgebench.judge.vibrating_path_graph_coloring@sha256:db8a9741831762040afb7e9819f997eb5f5293641fd5cd97d27fce3880ce084e
HERE=$(cd "$(dirname "$0")" && pwd)
timeout 900 docker run --rm --network none --memory 2g --cpus 2 -v "$HERE/inputs:/in:ro" "$IMG" sh -c '
cd /home/workspace/vibrating_path
T=./tools/bin/tester
sha256sum $T /tmp/eval_vibrating_path.py README.md
run(){ printf "%-48s " "$1 $2:"; $T "$1" "$2" >/tmp/o 2>&1; rc=$?; tr "\n" " " </tmp/o; echo "exit=$rc"; }
echo "== authored controls (direct tester)"
run /in/bip4.txt /in/bip4.two_line.out
run /in/bip4.txt /in/bip4.three_line.out
run /in/bip4.txt /in/bip4.bad_coloring.out
run /in/edge2_k1.txt /in/edge2_k1.hit.out
run /in/edge2_k1.txt /in/edge2_k1.nohit.out
echo "== official cases: zero-hit baseline-style coloring in both forms (direct tester)"
for c in 0001 0002 0003 0004 0007 0008; do
  python3 -c "
import sys
d=open(\"cases/$c.txt\").read().split(); N,K=int(d[0]),int(d[2])
col=\" \".join(str(i%K+1) for i in range(N))
open(\"/tmp/two.out\",\"w\").write(\"0\n\"+col+\"\n\"); open(\"/tmp/three.out\",\"w\").write(\"0\n\n\"+col+\"\n\")"
  printf "case %s two-line:   " $c; $T cases/$c.txt /tmp/two.out 2>&1 | tr "\n" " "; echo
  printf "case %s three-line: " $c; $T cases/$c.txt /tmp/three.out 2>&1 | tr "\n" " "; echo
done
echo "== original eval helper on authored corpus {bip4} with two-line vs three-line solution"
rm -rf cases && mkdir cases && cp /in/bip4.txt cases/0000.txt
printf "print(0)\nprint(\"1 2 1 2\")\n" > solution.py; python3 /tmp/eval_vibrating_path.py
printf "print(0)\nprint()\nprint(\"1 2 1 2\")\n" > solution.py; python3 /tmp/eval_vibrating_path.py
'
