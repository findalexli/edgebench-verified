#!/bin/bash
# Usage: run_native.sh <name> <solution.py path> ; runs the verbatim eval_cmd in the pinned judge image
set -u
IMG=seededge/edgebench.judge.warehouse_forklift_routing@sha256:ac7fdf03bb73d0f9ded21662c7c3ac246ce521ee5e6b237978a2799c7bc29cb3
HERE=$(cd "$(dirname "$0")/.." && pwd)
NAME=$1; SOL=$(readlink -f "$2"); OUT=$HERE/native/out; mkdir -p $OUT
CN=ebv-wh-$NAME-$$
/usr/bin/time -f "%e s wall" timeout 3700 docker run --rm --name $CN --network none --memory 2g --cpus ${CPUS:-2} \
  -v "$SOL":/home/workspace/warehouse_manager/solution.py:ro -v "$HERE":/opt/ctl:ro \
  --entrypoint bash $IMG -c 'cd /home/workspace/warehouse_manager && python3 /tmp/eval_warehouse_manager.py' \
  > $OUT/$NAME.stdout 2> $OUT/$NAME.stderr
echo "rc=$?" >> $OUT/$NAME.stderr
tail -3 $OUT/$NAME.stdout
