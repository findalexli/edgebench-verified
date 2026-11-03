#!/usr/bin/env python3
"""Create E2B job dirs for the community9 container checks of rust_multicrate_reconstruction,
integer_compression_codec, treant_forest and git_rewrite_in_zig. Usage: c9_make_jobs.py <job-spec-name> ...
Every job builds the current judge from source at the pinned community commit, grades with a copy of
tools/judge_local.py that also keeps result.json and the full log, and applies fixes as `git apply`-able patches."""
import difflib, hashlib, io, json, os, shutil, stat, subprocess, sys, tarfile, textwrap
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
UP = Path(os.environ.get("C9_UP", "/tmp/claude-1000/-home-alex-edgebench-verified/b902f0c3-094f-4474-9624-5f20b9cfe806/scratchpad/up-all"))
RUNS = ROOT / "evidence/runs"
SHA = "1187e2ca503d5ba3b4d23a50e7851f730a8126de"

COMMON = r'''#!/bin/bash
# @DESC@
# Judge built from source: EdgeBench community @ 1187e2ca503d5ba3b4d23a50e7851f730a8126de.
set -uo pipefail
T=@T@; SHA=1187e2ca503d5ba3b4d23a50e7851f730a8126de; O=/job/out; mkdir -p $O/g; cd /job
START=$(date +%s); LIMIT=@LIMIT@
{ nproc; free -m; df -h /; date -u; docker version --format '{{.Server.Version}}'; } >$O/env.txt 2>&1
( while true; do echo "$(date -u +%T) $(df -m / | tail -n 1)"; sleep 30; done ) >$O/df.log 2>&1 &
curl -LsSf https://astral.sh/uv/install.sh | sh >$O/uv.log 2>&1; export PATH=$HOME/.local/bin:$PATH
git clone -q --filter=blob:none --no-checkout -b community https://github.com/ByteDance-Seed/EdgeBench.git base >$O/clone.log 2>&1
( cd base && git sparse-checkout set --no-cone '/*.md' '/tools/' '/pyproject.toml' '/README*' '/LICENSE' '/sforge/' '/edgebench/benchmark.toml' '/edgebench/bases/' "/edgebench/tasks/$T/" && git checkout -q $SHA ) >>$O/clone.log 2>&1 || { echo clone-failed; exit 2; }
git -C base rev-parse HEAD >$O/head.txt
uv venv -q --python 3.12 v >>$O/uv.log 2>&1; uv pip install -q --python v/bin/python -e base >>$O/uv.log 2>&1 || { echo install-failed; exit 4; }
# judge_local.py copy: same grading, also keeps result.json fields and the full log.
sed -e 's/"result_found": bool(result), "log_tail": log\[-3000:\]}/"result_found": bool(result), "log_tail": log[-3000:], "result": result, "log": log[-400000:]}/' \
    -e 's/if k != "log_tail"}/if k not in ("log_tail", "log", "result")}/' base/tools/judge_local.py > /job/jl.py
grep -q '"log": log' /job/jl.py || { echo jl-patch-failed; exit 9; }
cat > /job/bj.py <<'PY'
import sys
from pathlib import Path
from sforge.harness.config import load_config
from sforge.harness.task_spec import load_task
from sforge.harness.docker_build import build_judge_image
spec = load_task(Path('edgebench/tasks/' + sys.argv[1])); print(build_judge_image(spec, load_config({})))
PY
# Base image: content-addressed key; pull the publisher's copy of that key if available, else build (snapshot.ubuntu.com has timed out once).
pullbase(){ local k; k=$( cd base && /job/v/bin/python -c "from pathlib import Path; from sforge.harness.task_spec import load_task; print(load_task(Path('edgebench/tasks/$T')).base_image_key)" ); echo "base $k" >>$O/base.txt; docker pull -q docker.io/seededge/$k >>$O/base.txt 2>&1 && docker tag docker.io/seededge/$k $k && docker image inspect $k --format '{{.Id}}' >>$O/base.txt; }
bj(){ local i; for i in 1 2 3; do ( cd $1 && /job/v/bin/python /job/bj.py $T ) >$O/build-$1.log 2>&1 && return 0; mkdir -p $O/buildlogs-$i; cp -r $1/logs/build_images/* $O/buildlogs-$i/ 2>/dev/null; echo "build attempt $i failed $1" >>$O/summary.txt; done; echo build-failed $1; tail -30 $O/build-$1.log; exit 5; }
tag(){ ( cd $1 && /job/v/bin/python -c "from pathlib import Path; from sforge.harness.task_spec import load_task; print(load_task(Path('edgebench/tasks/$T')).judge_image_key)" ); }
pullbase; bj base; IMGOLD=$(tag base); TD=/job/base/edgebench/tasks/$T
echo "old $IMGOLD $(docker image inspect $IMGOLD --format '{{.Id}}')" >$O/tags.txt
sha256sum /job/subs/* >$O/subs.sha 2>/dev/null
echo "setup_s $(( $(date +%s)-START ))" >>$O/summary.txt
fits(){ local el=$(( $(date +%s)-START )); [ $(( el+$1 )) -le $LIMIT ] && return 0; echo "SKIP $2 est=$1 elapsed=$el" >>$O/summary.txt; return 1; }
grade(){ # label image task_dir archive|empty est_seconds
  local lb=$1 img=$2 td=$3 ar=$4 est=$5 a="--empty"
  fits $est $lb || return 0
  [ "$ar" != empty ] && a="--archive $ar"
  ( cd /job/base && /job/v/bin/python /job/jl.py --task-dir $td --image $img $a --out $O/g/$lb.json ) >$O/g/$lb.stdout 2>&1
  local rc=$?; echo "$lb rc=$rc t=$(( $(date +%s)-START )) $(cut -c1-200 $O/g/$lb.stdout | tail -n 1)" >>$O/summary.txt
}
source /job/arms.sh
wait_lanes(){ :; }
docker system df >>$O/env.txt; df -h / >>$O/env.txt; echo done >>$O/summary.txt
'''

def write_job(name, t, desc, limit, arms, patches, subs=None):
    d = RUNS / name
    assert not (d / "result").exists(), f"{name} already has result"
    (d / "subs").mkdir(parents=True, exist_ok=True)
    run = COMMON.replace("@T@", t).replace("@DESC@", desc).replace("@LIMIT@", str(limit))
    (d / "run.sh").write_text(run)
    (d / "arms.sh").write_text(arms)
    for k, v in patches.items():
        (d / k).write_text(v)
    for k, v in (subs or {}).items():
        if isinstance(v, bytes): (d / "subs" / k).write_bytes(v)
        else: shutil.copy2(v, d / "subs" / k)
    print(name, "ok", sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) // 1024, "KiB")

def udiff(rel, old, new):
    return "".join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), "a/" + rel, "b/" + rel))

def real(t, sub, run=""):
    return RUNS / f"claude-opus-{t}{run}/result/out/sforge-logs/runs/opus-v1/{t}/submissions/{sub}/submission.tar.gz"

def tar_replace(src, edits, adds=None):
    """Copy tar members unchanged except edits {member: fn(bytes)->bytes}, plus adds {member: bytes}."""
    buf = io.BytesIO(); seen = set()
    with tarfile.open(src) as a, tarfile.open(fileobj=buf, mode="w:gz") as b:
        for m in a:
            if m.isfile():
                data = a.extractfile(m).read()
                if m.name in edits:
                    data = edits[m.name](data); seen.add(m.name); m.size = len(data)
                b.addfile(m, io.BytesIO(data))
            else:
                b.addfile(m)
        for k, v in (adds or {}).items():
            ti = tarfile.TarInfo(k); ti.size = len(v); ti.mode = 0o644; b.addfile(ti, io.BytesIO(v))
    assert seen == set(edits), (seen, edits.keys())
    return buf.getvalue()

def solo_tar(name, path):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as b:
        data = Path(path).read_bytes(); ti = tarfile.TarInfo(name); ti.size = len(data); ti.mode = 0o644; b.addfile(ti, io.BytesIO(data))
    return buf.getvalue()

# ---------- treant_forest
def treant(name, arms, limit=1500):
    t = "treant_forest"; rel = f"edgebench/tasks/{t}/task.toml"
    old = (UP / rel).read_text()
    new = old.replace('rescale = { kind = "piecewise_max", baseline = 5369.0, rank30 = 88189.0, rank1 = 330195.0, super_anchor = 451198.0 }',
                      'rescale = { kind = "linear", lower = 3418.0, upper = 92304.0 }')
    assert new != old
    prelude = r'''
cp -r base new; ( cd new && git apply /job/pr.patch ) || { echo patch-failed; exit 3; }
TDN=/job/new/edgebench/tasks/$T
# Measurement arm only: the tester with the undocumented 2*N*N stop removed (one line), nothing else.
mkdir -p nocap; cat > nocap/Dockerfile <<DF
FROM $IMGOLD
RUN sed -i 's/max_turns = N \* N \* 2$/max_turns = N * N * 2000/' /home/workspace/treants_forest/tools/bin/tester && grep -n 'max_turns = N' /home/workspace/treants_forest/tools/bin/tester
DF
docker build -q -t c9/treant-nocap nocap >$O/build-nocap.log 2>&1 || { echo nocap-build-failed; exit 6; }
docker run --rm --entrypoint grep c9/treant-nocap -n 'max_turns' /home/workspace/treants_forest/tools/bin/tester >>$O/tags.txt
docker run --rm --entrypoint sh $IMGOLD -c 'sha256sum /judge/* /home/workspace/treants_forest/tools/bin/tester; python3 -c "
import glob
s=0
for f in sorted(glob.glob(\"/home/workspace/treants_forest/cases/*\")):
    s+=2*int(open(f).readline().split()[0])**2
print(\"sum2NN\",s)"' >$O/judge.sha 2>&1
S=/job/subs
'''
    subs = {
        "agent10.tar.gz": real(t, "agent-10", "-v1"), "agent40.tar.gz": real(t, "agent-40", "-v1"),
        "agent33.tar.gz": real(t, "agent-33", "-v1"), "agent1.tar.gz": real(t, "agent-1", "-v1"),
        "greedy.tar.gz": solo_tar("solution.py", ROOT / "repairs/treant_forest-v2/paired/subs/honest_greedy/solution.py"),
        "invalid.tar.gz": solo_tar("solution.py", ROOT / "repairs/treant_forest-v2/paired/subs/invalid_revealed/solution.py"),
    }
    write_job(name, t, "treant_forest: real runs at the turn cap; old vs linear rescale; tester without the cap as a measurement.", limit, prelude + arms, {"pr.patch": udiff(rel, old, new)}, subs)

# ---------- integer_compression_codec
def integer(name, arms, limit=2500):
    t = "integer_compression_codec"
    rel_b = f"edgebench/tasks/{t}/judge/workspace/internal/baseline/baseline_results.json"; rel_t = f"edgebench/tasks/{t}/task.toml"
    rep = json.load(open(real(t, "auto-1").with_name("report.json")))
    meas = {x["name"]: x for x in rep["metrics"]["per_dataset"]}
    old = (UP / rel_b).read_text(); new = old
    import re
    for n, x in meas.items():
        pat = re.compile(r'("name": "%s".*?"encoded_bytes": )\d+(,\s*"bpi": )[0-9.]+' % n, re.S)
        bpi = x["encoded_bytes"] * 8 / x["n"]
        new, c = pat.subn(lambda m: f'{m.group(1)}{x["encoded_bytes"]}{m.group(2)}{bpi!r}', new, count=1)
        assert c == 1, n
    json.loads(new)
    oldt = (UP / rel_t).read_text()
    newt = oldt.replace('rescale = { kind = "linear", lower = 0.0, upper = 100.0 }', 'rescale = { kind = "linear", lower = 1.0, upper = 320.0 }')
    assert newt != oldt
    prelude = r'''
cp -r base new; ( cd new && git apply /job/pr.patch ) || { echo patch-failed; exit 3; }
TDN=/job/new/edgebench/tasks/$T
# new judge = old judge + the one data file the patch changes (the dataset generation layer is not repeated).
mkdir -p nj; cp new/edgebench/tasks/$T/judge/workspace/internal/baseline/baseline_results.json nj/; cat > nj/Dockerfile <<DF
FROM $IMGOLD
COPY baseline_results.json /home/workspace/integer-compression-codec/internal/baseline/baseline_results.json
DF
docker build -q -t c9/int-new nj >$O/build-new.log 2>&1 || { echo new-build-failed; exit 6; }
docker run --rm --entrypoint sh c9/int-new -c 'cd /home/workspace/integer-compression-codec; grep -n "bpi" internal/baseline/baseline_results.json' >>$O/tags.txt
S=/job/subs
'''
    corrupt = lambda b: (b.replace(b"out[i] = v;", b"out[i] = (i == 0) ? v + 1 : v;") if b.count(b"out[i] = v;") == 1 else 1/0)
    subs = {
        "starter.tar.gz": real(t, "auto-1"),                # real, byte-identical to the public starter
        "top.tar.gz": real(t, "agent-15", "-r2"),           # 4215fcb6ae, best repeatable real
        "flipA.tar.gz": real(t, "auto-3"),                  # f51fc943a0
        "flipB.tar.gz": real(t, "auto-5", "-r2"),           # a0add9f4f1
        "bad.tar.gz": tar_replace(real(t, "auto-1"), {"src/codec.cpp": corrupt}),
    }
    write_job(name, t, "integer_compression_codec: stored bpi anchors vs the starter's exact bpi (with the 1..320 scale).", limit, prelude + arms,
              {"pr.patch": udiff(rel_b, old, new) + udiff(rel_t, oldt, newt)}, subs)

# ---------- git_rewrite_in_zig
ORACLE = b'''const std = @import("std");

// Differential check against the system git, as the task prompt invites. Not imported by the binary.
test "system git runs" {
    var child = std.process.Child.init(&.{ "git", "--version" }, std.testing.allocator);
    child.stdout_behavior = .Ignore;
    const term = try child.spawnAndWait();
    try std.testing.expect(term == .Exited and term.Exited == 0);
}
'''
def zig(name, arms, limit=3200):
    t = "git_rewrite_in_zig"; rel = f"edgebench/tasks/{t}/judge/tests/test.sh"
    txt = (ROOT / "repairs/git_rewrite_in_zig-v2/repair.patch").read_text()
    body = txt[txt.index("--- a/files/test.sh"):].replace("a/files/test.sh", "a/" + rel).replace("b/files/test.sh", "b/" + rel)
    prelude = r'''
cp -r base new; ( cd new && git apply /job/pr.patch ) || { echo patch-failed; exit 3; }
bj new; IMGNEW=$(tag new); echo "new $IMGNEW $(docker image inspect $IMGNEW --format '{{.Id}}')" >>$O/tags.txt
S=/job/gen; mkdir -p $S /job/w
cp /job/subs/auto39.tar.gz $S/real.tar.gz
# Scaffold archive in the same member style as real archives (./name), from the task's own scaffold.
/job/v/bin/python - <<'PY'
import tarfile, os
root = '/job/base/edgebench/tasks/git_rewrite_in_zig/environment/zig-port'
with tarfile.open('/job/gen/scaf.tar.gz', 'w:gz') as t:
    for d, _, fs in os.walk(root):
        for f in sorted(fs):
            p = os.path.join(d, f); t.add(p, './' + os.path.relpath(p, root), recursive=False)
PY
# Generate main.o the way a solver would, with the judge image's Zig, for both trees; check the oracle test compiles and passes.
for k in scaf real; do mkdir -p /job/w/$k; tar -xzf $S/$k.tar.gz -C /job/w/$k; cp /job/subs/oracle_test.zig /job/w/$k/src/oracle_test.zig; chmod -R a+rwX /job/w/$k
  docker run --rm --network none -v /job/w/$k:/w --entrypoint bash $IMGOLD -c 'cd /w && zig build-obj src/main.zig -lc -lz; echo build-obj rc=$?; ls -la main.o; zig test src/oracle_test.zig; echo zigtest rc=$?; rm -rf .zig-cache' >$O/gen-$k.log 2>&1
  /job/v/bin/python /job/addm.py $S/$k.tar.gz $S/$k-obj.tar.gz ./main.o=/job/w/$k/main.o
  /job/v/bin/python /job/addm.py $S/$k.tar.gz $S/$k-test.tar.gz ./src/oracle_test.zig=/job/w/$k/src/oracle_test.zig
done
sha256sum $S/* >>$O/subs.sha
'''
    addm = '''import sys, tarfile, io
src, out, *adds = sys.argv[1:]
with tarfile.open(src) as a, tarfile.open(out, 'w:gz') as b:
    for m in a:
        b.addfile(m, a.extractfile(m) if m.isfile() else None)
    for x in adds:
        k, p = x.split('=', 1); d = open(p, 'rb').read(); ti = tarfile.TarInfo(k); ti.size = len(d); ti.mode = 0o644; b.addfile(ti, io.BytesIO(d))
'''
    subs = {"auto39.tar.gz": real(t, "auto-39", "-r2"), "oracle_test.zig": ORACLE}
    write_job(name, t, "git_rewrite_in_zig: leftover main.o and a test-only system-git call, on the scaffold and on a real run, old vs fixed test.sh.", limit, prelude + arms, {"pr.patch": body}, subs)
    (RUNS / name / "addm.py").write_text(addm)

# ---------- rust_multicrate_reconstruction
def rust_patches():
    t = "rust_multicrate_reconstruction"; rel = f"edgebench/tasks/{t}/judge/cas_judge/tools/score.py"; relv = f"edgebench/tasks/{t}/environment/vendor/build_vendor.py"
    s = (UP / rel).read_text()
    a = '["cargo", "test", "--frozen", "-p", pkg, "--", "--test-threads=4"]'
    nff = s.replace(a, '["cargo", "test", "--frozen", "--no-fail-fast", "-p", pkg, "--", "--test-threads=4"]'); assert nff != s
    ex = s.replace('        passed, failed = 0, 0\n', '        passed, failed = 0, 0\n        failed_test_paths = set()\n', 1)
    ex2 = ex.replace('                elif result_str == "FAILED":\n', '                elif result_str == "FAILED":\n                    failed_test_paths.add(test_path)\n', 1)
    ex3 = ex2.replace('                if test_name in stdout:\n', '                if ((crate_name == "cas-pty" and test_name in failed_test_paths)\n                        or (crate_name != "cas-pty" and test_name in stdout)):\n', 1)
    assert ex != s and ex2 != ex and ex3 != ex2
    v = (UP / relv).read_text()
    vn = v.replace('dropped = "target" in parts[:-1]', 'dropped = False'); assert vn != v
    both = s.replace(a, '["cargo", "test", "--frozen", "--no-fail-fast", "-p", pkg, "--", "--test-threads=4"]')
    return dict(nff=udiff(rel, s, nff), ex=udiff(rel, s, ex3), cc=udiff(relv, v, vn), all=udiff(rel, s, ex3.replace(a, '["cargo", "test", "--frozen", "--no-fail-fast", "-p", pkg, "--", "--test-threads=4"]')) + udiff(relv, v, vn))

def rust(name, arms, subs_names, limit=3150, reference=False):
    t = "rust_multicrate_reconstruction"; p = rust_patches()
    prelude = r'''
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
mkdir -p d-ccnff8; cp var-nff/$SC d-ccnff8/score.py; printf 'FROM c9/rust-cc8\nCOPY score.py /judge/bundle/cas_rust_benchmark/judge/tools/score.py\n' > d-ccnff8/Dockerfile; docker build -q -t c9/rust-ccnff8 d-ccnff8 >$O/build-ccnff8.log 2>&1 || { echo build-failed ccnff8; exit 6; }
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
'''
    src = {"agent1": ("agent-1",""), "agent5": ("agent-5",""), "auto8": ("auto-8","")}
    subs = {f"{k}.tar.gz": real(t, *src[k]) for k in subs_names}
    if reference:
        subs["reference-overlay.tgz"] = ROOT / ".internal/evidence/runs/rust_multicrate_reconstruction-v2-paired-r2-reference-rep3/inputs/reference-overlay.tgz"
        subs["build_sub.py"] = ROOT / "repairs/rust_multicrate_reconstruction-v2/paired/build_sub.py"
        subs["strip.py"] = ROOT / "repairs/rust_multicrate_reconstruction-v2/paired/strip.py"
    write_job(name, t, "rust_multicrate_reconstruction: fail-fast, cas-pty exemption and cc files, one change at a time, real submissions.", limit, prelude + arms,
              {"pr.patch": p["all"], "pr-nff.patch": p["nff"], "pr-ex.patch": p["ex"], "pr-cc.patch": p["cc"]}, subs)

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1]))
    for s in spec:
        globals()[s.pop("kind")](**s)
