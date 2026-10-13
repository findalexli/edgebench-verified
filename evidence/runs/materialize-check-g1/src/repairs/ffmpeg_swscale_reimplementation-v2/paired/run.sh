#!/bin/bash
# Paired v1/v2 evaluation for ffmpeg_swscale_reimplementation-v2 (E2B worker, root, /job).
# Submission arms run the task's ORIGINAL eval_cmd (tools/eval_cmd.sh, verbatim) inside the judge
# image, --network none; only the image differs (v1 = pinned original, v2 = built from /job/pkg).
# Scorer-level reference arms call /opt/tests/compute_reward.py directly with a baseline-forwarding
# shim as candidate (correct by construction), again on both images.
set -uo pipefail
V1=seededge/edgebench.judge.ffmpeg_swscale_reimplementation@sha256:38b256686afe14f6cec76790a7e884eb46ac70eb918a60351942a9c35c0f879f
V2=ebv/ffmpeg_swscale_reimplementation:v2
O=/job/out; mkdir -p $O/logs $O/rewards /job/sub /job/shim
DR="docker run --rm --network none --memory 4g --cpus 4"
nproc > $O/env.txt; free -m >> $O/env.txt; docker version --format '{{.Server.Version}}' >> $O/env.txt
docker pull $V1 > $O/pull.log 2>&1 || { echo pull-failed | tee -a $O/summary.txt; exit 2; }
docker build -t $V2 /job/pkg > $O/build.log 2>&1 || { echo build-failed | tee -a $O/summary.txt; exit 3; }
docker image inspect $V2 --format '{{.Id}}' > $O/v2_image_id.txt
for img in $V1 $V2; do docker run --rm --network none $img sha256sum /opt/tests/compute_reward.py /opt/tests/test.sh /verifier-data/libswscale_baseline.so; done > $O/scorer_sha.txt
mkdir -p /job/scaffold && tar -xf /job/inputs/scaffold.tar -C /job/scaffold
docker run --rm --network none -v /job:/job $V1 bash -c '
set -e; python3 -I /job/tools/make_variants.py /job/scaffold /job/sub
sha256sum /job/scaffold/src/lib.rs /job/scaffold/Cargo.toml /job/sub/*/src/lib.rs
for r in 1 2; do gcc -O2 -shared -fPIC -DREPEAT=$r -DBASELINE_PATH="\"/verifier-data/libswscale_baseline.so\"" -o /job/shim/ref_shim_r$r.so /job/tools/ref_shim.c -ldl; done
sha256sum /job/shim/*.so' > $O/submissions_sha.txt 2>&1 || { echo prep-failed | tee -a $O/summary.txt; exit 4; }
run_arm() { # $1 arm  $2 version  $3 image
  local t0=$(date +%s); local L=$O/logs/$1-$2
  timeout 900 $DR -v /job/sub/$1:/sub:ro -v /job/tools/eval_cmd.sh:/eval_cmd.sh:ro -v $O/rewards:/out $3 bash -c "
    cp -r /sub/. /home/workspace/swscale-impl/ && cd /home/workspace && bash /eval_cmd.sh > /tmp/stdout.txt 2> /tmp/stderr.txt; rc=\$?
    cp /tmp/stdout.txt /out/$1-$2.stdout.txt; tail -c 20000 /tmp/stderr.txt > /out/$1-$2.stderr.tail.txt
    cp /logs/verifier/reward.json /out/$1-$2.reward.json 2>/dev/null; exit \$rc" > $L.log 2>&1
  local rc=$?
  echo "$1 $2 exit=$rc wall=$(( $(date +%s) - t0 ))s" | tee -a $O/summary.txt
}
run_ref() { # $1 arm (ref_r1|ref_r2)  $2 version  $3 image
  local t0=$(date +%s)
  timeout 900 $DR -v /job/shim:/shim:ro -v $O/rewards:/out $3 bash -c "
    export PYTHONPATH=/opt/tests; mkdir -p /tmp/o
    python3 /opt/tests/compute_reward.py --candidate /shim/ref_shim_${1#ref_}.so --baseline /verifier-data/libswscale_baseline.so --output-dir /tmp/o > /out/$1-$2.stdout.txt 2>&1; rc=\$?
    cp /tmp/o/reward.json /out/$1-$2.reward.json 2>/dev/null; exit \$rc" > $O/logs/$1-$2.log 2>&1
  local rc=$?
  echo "$1 $2 exit=$rc wall=$(( $(date +%s) - t0 ))s" | tee -a $O/summary.txt
}
for arm in scaffold trig_rgba_rgb24_unsupported trig_3to1_unsupported trig_3to1_silent_noop invalid_yuv420p_rgb24_unsupported; do
  run_arm $arm v1 $V1; run_arm $arm v2 $V2
done
for arm in ref_r1 ref_r2; do run_ref $arm v1 $V1; run_ref $arm v2 $V2; done
# Compact per-arm extract (judge python3 has json)
docker run --rm --network none -v $O/rewards:/r:ro $V1 python3 -c '
import json,glob,os
for f in sorted(glob.glob("/r/*.reward.json")):
    d=json.load(open(f)); a=d.get("additional_data",{})
    errs=[(b["label"],b["error"]) for b in a.get("benchmark_results",[]) if "error" in b]
    print(os.path.basename(f)[:-12], "score=%s"%d.get("score"), "correct=%s/%s"%(a.get("correctness_passed"),a.get("correctness_total")),
          "speedups=%s"%a.get("per_workload_speedups"), "timed_errors=%s"%errs, "reason=%s"%a.get("reason"))
' > $O/summary_parsed.txt 2>&1
docker image rm $V2 >/dev/null 2>&1; echo done | tee -a $O/summary.txt
