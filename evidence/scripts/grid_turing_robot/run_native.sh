#!/usr/bin/env bash
# Run each solution in solutions/ through the ORIGINAL evaluator inside the pinned judge image.
# Usage: run_native.sh <outdir> [solution names...]
set -u
IMG=seededge/edgebench.judge.grid_turing_robot@sha256:f67864ad75a3a2af0f7904a05a30b888f66ce2ed5c1f3cac7d7482e578a296c3
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=$1; shift; mkdir -p "$OUT"
for s in "$@"; do
  name=grid-ebv-$s-$$
  timeout 900 docker run --rm --name "$name" --network none --memory 2g --cpus ${CPUS:-4} \
    -v "$HERE/solutions:/sol:ro" "$IMG" bash -c "
      cp /sol/$s.py /home/workspace/grid_turing_robot/solution.py &&
      sha256sum /home/workspace/grid_turing_robot/solution.py /tmp/eval_grid_turing_robot.py /home/workspace/grid_turing_robot/tools/bin/tester /home/workspace/grid_turing_robot/tools/src/verifier.py >&2 &&
      echo '>>>>> Start Test Output' &&
      cd /home/workspace/grid_turing_robot && python3 /tmp/eval_grid_turing_robot.py; echo \"EXIT \$?\" >&2;
      echo '>>>>> End Test Output'" > "$OUT/$s.log" 2> "$OUT/$s.err"
  echo "$s docker_exit=$?"
done
