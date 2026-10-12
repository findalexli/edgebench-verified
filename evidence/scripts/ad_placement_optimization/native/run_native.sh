#!/bin/bash
# Runs each control through the ORIGINAL judge image and its unchanged /tmp/eval_ahc.sh.
# One container at a time; --network none; --memory 2g. Afterwards it re-runs the same
# compiled binary on every case (outside the timed eval) to save outputs for the oracle.
set -u
IMG=seededge/edgebench.judge.ad_placement_optimization@sha256:997d10b59ba063f23429fb8eace84b0cb28ea22b0f9fe5243ef64a2310e19ba9
HERE=$(cd "$(dirname "$0")" && pwd)
RES=$HERE/results; mkdir -p "$RES"
names=(x unit tile_full tile_fit overlap1 nocontain oob mixed spin)
for m in ${MODES:-1 2 3 4 5 6 7}; do
  nm=${names[$m]}${TAG:-}; o=$RES/$nm; rm -rf "$o"; mkdir -p "$o/outs"; chmod 777 "$o" "$o/outs"
  (echo "#define MODE $m"; [ -n "${SPIN_MS:-}" ] && echo "#define SPIN_MS $SPIN_MS"; cat "$HERE/controls.cpp") > "$o/solution.cpp"
  timeout 900 docker run --rm --name adp-ctl-$nm --network none --memory 2g --cpus ${CPUS:-2} -e SKIP_RERUN=${SKIP_RERUN:-0} \
    -v "$o":/res "$IMG" bash -c '
      cp /res/solution.cpp /home/workspace/ad-placement/solution.cpp
      cd /home/workspace/ad-placement && bash /tmp/eval_ahc.sh > /res/eval_stdout.log 2> /res/eval_stderr.log
      echo $? > /res/eval_exit
      [ "${SKIP_RERUN:-0}" = 1 ] || for f in cases/*.txt; do id=$(basename $f .txt); timeout 10 ./solution < $f > /res/outs/$id.txt 2>/dev/null; echo "$id $?" >> /res/outs/exit_codes; done
      sha256sum /tmp/eval_ahc.sh tools/bin/tester cases/*.txt > /res/image_hashes
      chmod -R a+rwX /res'
  echo "$nm: $(tail -3 $o/eval_stdout.log | tr '\n' ' ')"
done
