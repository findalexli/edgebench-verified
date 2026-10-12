#!/bin/bash
# integer_compression_codec: native controls in the pinned judge image.
set -u
IMG=seededge/edgebench.judge.integer_compression_codec@sha256:15dffad066b4bd1e4844b3d3798a605c80df8e83db547998b560c28e28e989ac
mkdir -p /job/out
(nproc; free -g; lscpu | grep -E "Model name|Flags" | cut -c1-200) > /job/out/host.txt
docker pull "$IMG" > /job/out/pull.log 2>&1 || { echo pull failed; exit 1; }
docker image inspect "$IMG" --format '{{.Id}}' >> /job/out/pull.log
EVAL='cd /home/workspace/integer-compression-codec && python3 runner_judge.py'
for v in s0_starter s1_roundtrip_bug s2_delta_zigzag_varint s0_starter; do
  n=$(ls /job/out | grep -c "^run_") ; tag="run_${n}_$v"
  timeout 2400 docker run --rm --network none --cpus 4 --memory 6g -v /job/variants/$v:/v:ro "$IMG" \
    bash -c "cp /v/codec.cpp /home/workspace/integer-compression-codec/src/codec.cpp && $EVAL" > /job/out/$tag.stdout 2> /job/out/$tag.stderr
  echo "$tag exit=$?" >> /job/out/status.txt
done
# Regenerate the full datasets with the shipped generator and compare with the shipped data files.
timeout 1800 docker run --rm --network none --cpus 4 --memory 6g "$IMG" bash -c '
  cd /home/workspace/integer-compression-codec && mkdir -p /tmp/regen &&
  python3 tools/gen_data.py --full --out-dir /tmp/regen > /tmp/regen.log 2>&1; cat /tmp/regen.log;
  for f in data/*.u32; do b=$(basename $f); echo "$b shipped=$(sha256sum < $f | cut -c1-16) regen=$(sha256sum < /tmp/regen/$b | cut -c1-16)"; done
  python3 - <<PY
import numpy as np
for name in ["docids","ts_sec","ts_ns","temp","grid","zipf","rand","sparse"]:
    a=np.fromfile(f"data/{name}.u32",dtype=np.uint32)
    print(name, len(a), int(a.min()), int(a.max()))
PY' > /job/out/regen.txt 2>&1
echo "regen exit=$?" >> /job/out/status.txt
