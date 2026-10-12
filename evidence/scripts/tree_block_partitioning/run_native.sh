#!/bin/bash
# Native T2 run in the pinned judge image, original evaluator path, 4 arms:
#   {std, alias-variant} x {original library, patched library (bind-mounted over the original)}
# Usage: run_native.sh <scratch dir containing tar/ extract of tree_block_partitioning-000.tar.gz>
set -uo pipefail
H=$(cd "$(dirname "$0")" && pwd); S="$1"
IMG=seededge/edgebench.judge.tree_block_partitioning@sha256:6ebbb44ab188660b15d260143e942ddcf0ba3bceb0bb7d7c78e976b1a36669d2
T2=$S/tar/opt/p1_judge/prob/P1/T2_P7881
mkdir -p $S/sub_std $S/sub_alias $S/native
cp $T2/std.cpp $S/sub_std/T2.cpp
python3 -I $H/make_alias_variant.py $T2/std.cpp $S/sub_alias/T2.cpp
python3 -I $H/patch_overlay.py $T2/data/interactive_lib.cpp $S/patched_lib
LIB=/opt/p1_judge/prob/P1/T2_P7881/data/interactive_lib.cpp
EVAL="python3 /opt/p1_judge/prob/P1/eval.py --source-root /sub --task T2 --time-factor 1 --time-grace 0 --score-sum -v"
for sub in std alias; do for lib in orig patched; do
  M=""; [ $lib = patched ] && M="-v $S/patched_lib/interactive_lib.cpp:$LIB:ro"
  echo "=== submission=$sub library=$lib"
  timeout 600 docker run --rm --network none --memory 2g --cpus 2 -v $S/sub_$sub:/sub:ro $M $IMG \
    bash -c "sha256sum $LIB; cd /home/workspace/p1 && $EVAL" > $S/native/$sub-$lib.log 2>&1
  echo "exit=$?"; grep -E "interactive_lib|^CASE|TOTAL_SCORE|T2_P7881:" $S/native/$sub-$lib.log
done; done
