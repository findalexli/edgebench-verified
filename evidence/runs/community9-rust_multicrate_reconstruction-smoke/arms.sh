
for v in nff ex cc; do cp -r base var-$v; ( cd var-$v && git apply /job/pr-$v.patch ) || { echo patch-failed $v; exit 3; }; done
SC=edgebench/tasks/$T/judge/cas_judge/tools/score.py
for v in nff ex; do mkdir -p d-$v; cp var-$v/$SC d-$v/score.py; cat > d-$v/Dockerfile <<DF
FROM $IMGOLD
COPY score.py /judge/bundle/cas_rust_benchmark/judge/tools/score.py
DF
docker build -q -t c9/rust-$v d-$v >$O/build-$v.log 2>&1 || { echo build-failed $v; exit 6; }; done
# cc: the patched build_vendor.py on the manifest's cc row; only src/target differs from the old image.
mkdir -p d-cc; grep -E '^cc\s' base/edgebench/tasks/$T/environment/vendor/vendor-manifest.tsv > d-cc/m.tsv; cat d-cc/m.tsv >$O/cc-row.txt
v/bin/python var-cc/edgebench/tasks/$T/environment/vendor/build_vendor.py --manifest d-cc/m.tsv --out d-cc/out >$O/cc-vendor.log 2>&1 || { echo cc-vendor-failed; exit 7; }
ls -la d-cc/out/cc/src/target >>$O/cc-row.txt
cat > d-cc/Dockerfile <<DF
FROM $IMGOLD
COPY out/cc/src/target/ /judge/bundle/cas_rust_benchmark/workspace/agent-start/vendor-deps/cc/src/target/
DF
docker build -q -t c9/rust-cc d-cc >$O/build-cc.log 2>&1 || { echo build-failed cc; exit 6; }
docker run --rm --entrypoint sh c9/rust-cc -c 'cd /judge/bundle/cas_rust_benchmark/workspace/agent-start/vendor-deps/cc; ls -la src/target; python3 - <<PY
import json,hashlib
c=json.load(open(".cargo-checksum.json"))["files"]
print("checked",sum(1 for k,v in c.items() if k.startswith("src/target/") and hashlib.sha256(open(k,"rb").read()).hexdigest()==v), "of", sum(1 for k in c if k.startswith("src/target/")))
PY' >>$O/cc-row.txt 2>&1
# Same task.toml but the judge cap raised to the worker's 8 vCPU, used only for the slow cc arms and their old-judge pair.
mkdir -p td8; sed 's/^cpus = 4/cpus = 8/' $TD/task.toml > td8/task.toml
TD8=/job/td8
# Disk guard for cc arms: above 85% used, drop the public phase's target/ once the combined copy exists (it ignores target/, as in the earlier paired runs).
( while true; do sleep 20; u=$(df --output=pcent / | tail -n1 | tr -dc 0-9); if [ "$u" -gt 85 ]; then for c in $(docker ps --format '{{.Names}}' | grep sforge-judge); do docker exec $c sh -c 'if ls -d /tmp/cas-hidden-inject-* >/dev/null 2>&1 && [ -d /tmp/cas_eval/run/agent-start/target ]; then rm -rf /tmp/cas_eval/run/agent-start/target; echo removed; fi' >>$O/disk-guard.log 2>&1; done; fi; done ) &
S=/job/subs
( grade s-old-agent5 $IMGOLD $TD $S/agent5.tar.gz 500; grade s-ex-agent5 c9/rust-ex $TD $S/agent5.tar.gz 500 ) & LA=$!
( grade s-nff-agent5 c9/rust-nff $TD $S/agent5.tar.gz 500 ) & LB=$!
wait $LA $LB
