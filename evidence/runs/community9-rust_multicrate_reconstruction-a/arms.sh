
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
# The slow arms at 8 vCPU: the worker's 8 GiB cannot hold the bundle's build.jobs=16, so both old and cc images get CARGO_BUILD_JOBS=8 (as in the earlier paired runs).
for b in "$IMGOLD old8" "c9/rust-cc cc8"; do set -- $b; mkdir -p d-$2; printf 'FROM %s\nENV CARGO_BUILD_JOBS=8\n' $1 > d-$2/Dockerfile; docker build -q -t c9/rust-$2 d-$2 >$O/build-$2.log 2>&1 || { echo build-failed $2; exit 6; }; done
if [ -f /job/subs/reference-overlay.tgz ]; then
  # Reference (upstream CAS v1.0.0 bodies, hidden tests removed) built on the worker only; never copied to out/.
  mkdir -p /job/ref/up /job/ref/w; tar -xzf /job/subs/reference-overlay.tgz -C /job/ref/up
  cid=$(docker create $IMGOLD true); docker cp $cid:/judge/bundle/cas_rust_benchmark/workspace/agent-start /job/ref/w/start; docker cp $cid:/judge/bundle/cas_rust_benchmark/judge/hidden-tests/hidden-sources /job/ref/w/hs; docker rm -f $cid >/dev/null
  ( cd /job/subs && /job/v/bin/python /job/subs/build_sub.py reference /job/ref/w/start /job/ref/up /job/ref/w/hs /job/ref/sub/agent-start ) >$O/build_sub.log 2>&1 || { echo build-sub-failed; tail -5 $O/build_sub.log; exit 8; }
  rm -rf /job/ref/w /job/ref/up; ( cd /job/ref/sub && find agent-start -type f | LC_ALL=C sort | xargs sha256sum | sha256sum ) >$O/reference.sha
  /job/v/bin/python - <<'PY'
import tarfile, os
with tarfile.open('/job/ref/reference.tar.gz', 'w:gz') as t:
    for d, _, fs in os.walk('/job/ref/sub/agent-start'):
        for f in sorted(fs):
            p = os.path.join(d, f); t.add(p, os.path.relpath(p, '/job/ref/sub'), recursive=False)
PY
  rm -rf /job/ref/sub
fi
# Disk guard for cc arms: above 85% used, drop the public phase's target/ once the combined copy exists (it ignores target/, as in the earlier paired runs).
( while true; do sleep 20; u=$(df --output=pcent / | tail -n1 | tr -dc 0-9); if [ "$u" -gt 85 ]; then for c in $(docker ps --format '{{.Names}}' | grep sforge-judge); do docker exec $c sh -c 'if ls -d /tmp/cas-hidden-inject-* >/dev/null 2>&1 && [ -d /tmp/cas_eval/run/agent-start/target ]; then rm -rf /tmp/cas_eval/run/agent-start/target; echo removed; fi' >>$O/disk-guard.log 2>&1; done; fi; done ) &
S=/job/subs
( grade old-agent1-p1 $IMGOLD $TD $S/agent1.tar.gz 320; grade nff-agent1-p1 c9/rust-nff $TD $S/agent1.tar.gz 320; grade old-agent5-p1 $IMGOLD $TD $S/agent5.tar.gz 320; grade nff-agent5-p1 c9/rust-nff $TD $S/agent5.tar.gz 320; grade old-auto8-p1 $IMGOLD $TD $S/auto8.tar.gz 320; grade nff-auto8-p1 c9/rust-nff $TD $S/auto8.tar.gz 320; grade ex-agent1-p1 c9/rust-ex $TD $S/agent1.tar.gz 320; grade ex-agent5-p1 c9/rust-ex $TD $S/agent5.tar.gz 320 ) & LA=$!
( grade nff-agent1-p2 c9/rust-nff $TD $S/agent1.tar.gz 320; grade old-agent1-p2 $IMGOLD $TD $S/agent1.tar.gz 320; grade nff-agent5-p2 c9/rust-nff $TD $S/agent5.tar.gz 320; grade old-agent5-p2 $IMGOLD $TD $S/agent5.tar.gz 320; grade nff-auto8-p2 c9/rust-nff $TD $S/auto8.tar.gz 320; grade old-auto8-p2 $IMGOLD $TD $S/auto8.tar.gz 320; grade ex-agent5-p2 c9/rust-ex $TD $S/agent5.tar.gz 320; grade ex-agent1-p2 c9/rust-ex $TD $S/agent1.tar.gz 320 ) & LB=$!
wait $LA $LB
