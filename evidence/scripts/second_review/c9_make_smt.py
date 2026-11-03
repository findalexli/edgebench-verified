#!/usr/bin/env python3
"""Jobs for the SMT textual-lookup claim. Real solver: r1 auto-6 (never scored in the run: no report), unchanged (textual keys) and changed only
where it renders witness keys (let-expanded ground keys, the form smtlib_spec.md documents). Stub arms replay the z3 witness sets of the earlier repair.
new = repairs/smt_solver-v2/repair.patch on both copies of evaluate.py."""
import difflib, importlib.util, io, os, shutil, subprocess, sys, tarfile, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from c9_jobs_common import job_dir, real_archive
T = 'smt_solver'
UP, NEWEV = sys.argv[1:3]
OLD = open(UP + f'/edgebench/tasks/{T}/judge/smt_judge/scripts/evaluate.py').read(); NEW = open(NEWEV).read()
patch = ''
for p in (f'edgebench/tasks/{T}/judge/smt_judge/scripts/evaluate.py', f'edgebench/tasks/{T}/environment/workspace/scripts/evaluate.py'):
    assert open(UP + '/' + p).read() == OLD
    patch += f'diff --git a/{p} b/{p}\n' + ''.join(difflib.unified_diff(OLD.splitlines(True), NEW.splitlines(True), f'a/{p}', f'b/{p}'))
PREV = 'evidence/runs/smt_solver-v2-paired-b/'
PRE = r'''# 8 vCPU / 8 GiB worker: official is 16 CPUs, 16g. 16 solver processes stay as in judge/run.sh.
export SEVAL_ARGS="--judge-cpu-limit 8 --judge-mem-limit 7g"
sed -i 's/^cpus = 16/cpus = 8/; s/^memory = "16g"/memory = "7g"/' base/edgebench/tasks/$T/task.toml new/edgebench/tasks/$T/task.toml
'''
POST = r'''# Reuse the downloaded blob for the second build.
if [ "$t" = base ]; then mkdir -p new/edgebench/tasks/$T/judge/blobs; cp base/edgebench/tasks/$T/judge/blobs/* new/edgebench/tasks/$T/judge/blobs/; fi
'''
SUB = r'''# The 69 affected hidden sat files with the judge's own evaluate.py and its flags (timeout 60, parallel 16, perturb, hidden salt).
sub69(){ # label side arm est
  local sd=$2 img; [ $sd = old ] && img=$IMGOLD || img=$IMGNEW
  fits $4 "$1-$sd-sub69" || return 0
  local out=$O/sub/$1-$sd; mkdir -p $out /job/w/$3; [ -f /job/w/$3/build.sh ] || tar xzf /job/subs/$3.tar.gz -C /job/w/$3
  local t0=$(date +%s)
  timeout 900 docker run --rm --network none --cpus 8 --memory 7g -v /job/files69.txt:/files69.txt:ro -v /job/w/$3:/sub:ro -v $out:/out --entrypoint bash $img -c '
python3 - <<PY
import json,os,shutil
H="/home/workspace/smt_judge/hidden_benchmarks"; fs=[l.strip() for l in open("/files69.txt") if l.strip()]
for f in fs:
    os.makedirs(os.path.dirname("/tmp/hb/"+f),exist_ok=True); shutil.copy(H+"/"+f,"/tmp/hb/"+f)
e=json.load(open(H+"/expected_answers.json")); m=json.load(open(H+"/selection_manifest.json"))
json.dump({f:e[f] for f in fs},open("/tmp/hb/expected_answers.json","w")); json.dump([x for x in m if x["selected_path"] in set(fs)],open("/tmp/hb/selection_manifest.json","w"))
PY
cp -r /sub /tmp/sub && cd /tmp/sub && chmod +x build.sh solve && ./build.sh && python3 /home/workspace/smt_judge/scripts/evaluate.py --solver ./solve --benchmarks /tmp/hb --expected /tmp/hb/expected_answers.json --manifest /tmp/hb/selection_manifest.json --timeout 60 --parallel 16 --perturb --perturb-salt hidden-sebench --submission-root /tmp/sub --output /tmp/res.json > /out/eval.out 2>&1; echo eval_rc=$?
python3 - <<PY
import json
d=json.load(open("/tmp/res.json")); rows=[{k:r.get(k) for k in ("benchmark","verdict","answer","time","difficulty","model_error")} for v in d["results"].values() for r in v]
for r in rows: r["model_error"]=(r["model_error"] or "")[:70]
json.dump({"final_score":d["final_score"],"rows":rows},open("/out/res.json","w"))
PY
' > $out/run.log 2>&1
  echo "sub69 $1 $sd rc=$? wall=$(( $(date +%s)-t0 )) $(tail -1 $out/run.log | cut -c1-60)" >>$O/summary.txt
}
pub(){ # label side arm: what a solver sees locally: the public QF_UF and QF_UFLRA files with the shipped evaluate.py (timeout 60, parallel 8)
  local sd=$2 img d; [ $sd = old ] && { img=$IMGOLD; d=base; } || { img=$IMGNEW; d=new; }
  fits 300 "$1-$sd-pub" || return 0
  local out=$O/pub/$1-$sd; mkdir -p $out /job/w/$3; [ -f /job/w/$3/build.sh ] || tar xzf /job/subs/$3.tar.gz -C /job/w/$3
  timeout 600 docker run --rm --network none --cpus 8 --memory 7g -v /job/$d/edgebench/tasks/$T/environment/workspace/benchmarks:/b0:ro -v /job/w/$3:/sub:ro -v $out:/out --entrypoint bash $img -c 'cp -r /b0 /tmp/b; cp -r /sub /tmp/sub; cd /tmp/sub; chmod +x build.sh solve; ./build.sh; python3 /home/workspace/smt_judge/scripts/evaluate.py --solver ./solve --benchmarks /tmp/b --expected /tmp/b/expected_answers.json --manifest /tmp/b/selection_manifest.json --logics QF_UF QF_UFLRA --timeout 60 --parallel 8 --submission-root /tmp/sub --output /out/res.json > /out/eval.out 2>&1; echo eval_rc=$?; python3 -c "
import json
d=json.load(open(\"/out/res.json\")); rows=[{k:r.get(k) for k in (\"benchmark\",\"verdict\",\"model_error\")} for v in d[\"results\"].values() for r in v]
for r in rows: r[\"model_error\"]=(r[\"model_error\"] or \"\")[:70]
json.dump({\"final_score\":d[\"final_score\"],\"rows\":rows},open(\"/out/res.json\",\"w\"))"' > $out/run.log 2>&1
  echo "pub $1 $sd rc=$? $(tail -1 $out/run.log | cut -c1-60)" >>$O/summary.txt
}
'''
def tar_dir(path, root, names=None):
    with tarfile.open(path, 'w:gz') as t:
        for dp, dn, fn in os.walk(root):
            dn.sort()
            for f in sorted(fn):
                p = os.path.join(dp, f); a = os.path.relpath(p, root)
                ti = tarfile.TarInfo(a); b = open(p, 'rb').read(); ti.size = len(b); ti.mode = os.stat(p).st_mode & 0o777
                t.addfile(ti, io.BytesIO(b))
def populate(d, arms_real=True):
    s = d + '/subs/'
    a6 = real_archive(T, '', 'auto-6')
    shutil.copy(a6, s + 'real.tar.gz')
    shutil.copy(PREV + 'files69.txt', d + '/files69.txt')
    with tempfile.TemporaryDirectory() as td:
        with tarfile.open(a6) as t:
            t.extractall(td + '/x')
        subprocess.check_call([sys.executable, 'evidence/scripts/second_review/c9_smt_ground_keys.py', td + '/x'])
        with tarfile.open(a6) as src, tarfile.open(s + 'realground.tar.gz', 'w:gz') as dst:
            for m in src:
                data = open(td + '/x/' + m.name, 'rb').read() if m.isfile() else None
                if data is not None: m.size = len(data)
                dst.addfile(m, io.BytesIO(data) if data is not None else None)
    for arm in ('ground', 'textual', 'textual_true', 'ground_wrong'):
        with tempfile.TemporaryDirectory() as td:
            shutil.copytree(PREV + 'result/out/subs_witness_sets/' + arm + '/src', td + '/src')
            for f in ('build.sh', 'solve'):
                shutil.copy(PREV + 'stub/' + f, td + '/' + f)
            tar_dir(s + arm + '.tar.gz', td)
    open(d + '/prebuild.sh', 'w').write(PRE); open(d + '/postbuild.sh', 'w').write(POST)
A_SMOKE = SUB + r'''mkdir -p $O/sub $O/pub
pub real-p1 old real
pub realground-p1 old realground
sub69 real-p1 old real 500
seval ground-p1 old ground.tar.gz 240
'''
A_MAIN = SUB + r'''mkdir -p $O/sub $O/pub
# Stub arms on the full hidden set via sforge eval; real solver on the 69 affected files; two passes, order reversed; plus the public view.
for pass in 1 2; do o="old new"; [ $pass = 2 ] && o="new old"
  for arm in ground textual textual_true ground_wrong; do for sd in $o; do seval $arm-p$pass $sd $arm.tar.gz 240; done; done
  for arm in real realground; do for sd in $o; do sub69 $arm-p$pass $sd $arm 500; done; done
done
for sd in old new; do pub real-p1 $sd real; pub realground-p1 $sd realground; done
'''
A_FULL = lambda sd, pass_, arm: SUB + rf'''mkdir -p $O/sub $O/pub
# Full hidden set via sforge eval, 60 s per case, 16 solver processes on 8 CPUs.
seval {arm}-full{pass_} {sd} {arm}.tar.gz 2900
'''
os.makedirs('evidence/runs', exist_ok=True)
mode = sys.argv[3]
if mode == 'smoke':
    d = job_dir('community9-smt_solver-smoke', T, 'SMT smoke.', 1500, patch, A_SMOKE, only='base'); populate(d); print(d)
elif mode == 'main':
    d = job_dir('community9-smt_solver-a', T, 'SMT paired arms.', 3150, patch, A_MAIN); populate(d); print(d)
elif mode == 'full':
    # full-old1 and full-new1 were first attempts: the time guard (est 3100 against limit 3200) skipped the run, so no arm ran.
    for sd, p, arm, name in (('old', 1, 'real', 'fulla-old'), ('new', 1, 'real', 'fulla-new'), ('old', 2, 'real', 'fullb-old'), ('new', 2, 'real', 'fullb-new')):
        d = job_dir('community9-smt_solver-' + name, T, 'SMT real solver on the full hidden set.', 3280, patch, A_FULL(sd, p, arm), only='base' if sd == 'old' else 'new'); populate(d); print(d)
elif mode == 'direct':
    # fulla-old: sforge eval of the real solver ended with correct=0/0 and no eval log kept (the score file was absent). These runs call the same evaluate.py
    # with the same flags directly, keep stdout and stderr, the cgroup memory events and peak, and per-file verdicts.
    # usage: ... direct <name> <old|new> <parallel> [per-process-limit-kib]
    name, sd, par = sys.argv[4:7]; lim = sys.argv[7] if len(sys.argv) > 7 else ''
    ul = f'ulimit -v {lim}; ' if lim else ''
    A = rf'''mkdir -p $O/direct
img=$IMGOLD; [ {sd} = new ] && img=$IMGNEW
mkdir -p /job/w/real; tar xzf /job/subs/real.tar.gz -C /job/w/real
t0=$(date +%s)
timeout 3000 docker run --name direct --network none --cpus 8 --memory 7g -v /job/w/real:/sub:ro -v $O/direct:/out --entrypoint bash $img -c '
cp -r /sub /home/workspace/smt_solver_x && cd /home/workspace/smt_solver_x && chmod +x build.sh solve && ./build.sh >/out/build.out 2>&1
{ul}python3 /home/workspace/smt_judge/scripts/evaluate.py --solver ./solve --benchmarks /home/workspace/smt_judge/hidden_benchmarks --expected /home/workspace/smt_judge/hidden_benchmarks/expected_answers.json --manifest /home/workspace/smt_judge/hidden_benchmarks/selection_manifest.json --timeout 60 --parallel {par} --perturb --perturb-salt hidden-sebench --submission-root /home/workspace/smt_solver_x --output /tmp/res.json > /out/eval.out 2> /out/eval.err; echo eval_rc=$?
cat /sys/fs/cgroup/memory.events; cat /sys/fs/cgroup/memory.peak
python3 - <<PY
import json
d=json.load(open("/tmp/res.json")); rows=[{{k:r.get(k) for k in ("benchmark","verdict","answer","time","difficulty","model_error")}} for v in d["results"].values() for r in v]
for r in rows: r["model_error"]=(r["model_error"] or "")[:70]
json.dump({{"final_score":d["final_score"],"logic_summary":d.get("logic_summary"),"rows":rows}},open("/out/res.json","w"))
PY
' > $O/direct/run.log 2>&1
echo "direct {name} {sd} par={par} lim={lim} rc=$? wall=$(( $(date +%s)-t0 ))" >>$O/summary.txt
docker inspect direct --format 'exit={{{{.State.ExitCode}}}} oom={{{{.State.OOMKilled}}}}' >>$O/summary.txt
'''
    d = job_dir('community9-smt_solver-' + name, T, 'SMT real solver, full hidden set, direct evaluate.py with logs.', 3280, patch, A, only='base' if sd == 'old' else 'new'); populate(d); print(d)
elif mode == 'iso':
    # usage: ... iso <name> <old|new> [arm]: evaluate.py's own case function, one process per case, to pin the BrokenProcessPool seen in direct16-old.
    name, sd = sys.argv[4:6]; arm = sys.argv[6] if len(sys.argv) > 6 else 'real'
    A = rf'''mkdir -p $O/iso
img=$IMGOLD; [ {sd} = new ] && img=$IMGNEW
mkdir -p /job/w/{arm}; tar xzf /job/subs/{arm}.tar.gz -C /job/w/{arm}
t0=$(date +%s)
timeout 3000 docker run --name iso --network none --cpus 8 --memory 7g -v /job/w/{arm}:/sub:ro -v /job/driver.py:/driver.py:ro -v $O/iso:/out --entrypoint bash $img -c '
cp -r /sub /home/workspace/smt_solver_x && cd /home/workspace/smt_solver_x && chmod +x build.sh solve && ./build.sh >/out/build.out 2>&1
python3 /driver.py ./solve /out/res.json > /out/driver.out 2> /out/driver.err; echo driver_rc=$?
cat /sys/fs/cgroup/memory.events; cat /sys/fs/cgroup/memory.peak
' > $O/iso/run.log 2>&1
echo "iso {name} {sd} rc=$? wall=$(( $(date +%s)-t0 ))" >>$O/summary.txt
docker inspect iso --format 'exit={{{{.State.ExitCode}}}} oom={{{{.State.OOMKilled}}}}' >>$O/summary.txt
'''
    d = job_dir('community9-smt_solver-' + name, T, 'SMT real solver, full hidden set, one process per case.', 3280, patch, A, only='base' if sd == 'old' else 'new'); populate(d)
    shutil.copy('evidence/scripts/second_review/c9_smt_iso_driver.py', d + '/driver.py'); print(d)
elif mode == 'stack':
    # usage: ... stack <name> <old|new> <pass>: full sforge eval of the real solver with the stack-overflow fix on both judges (old = base + stack fix, new = textual fix + stack fix).
    name, sd, p = sys.argv[4:7]
    A = SUB + rf'''mkdir -p $O/sub $O/pub
seval real-stack{p} {sd} real.tar.gz 2900
'''
    d = job_dir('community9-smt_solver-' + name, T, 'SMT real solver, full hidden set, sforge eval, stack fix on both judges.', 3280, patch, A, only='base' if sd == 'old' else 'new'); populate(d)
    shutil.copy('evidence/scripts/second_review/c9_smt_stack_fix.py', d + '/stack_fix.py')
    open(d + '/prebuild.sh', 'a').write('/job/v/bin/python /job/stack_fix.py {base,new}/edgebench/tasks/$T/judge/smt_judge/scripts/evaluate.py {base,new}/edgebench/tasks/$T/environment/workspace/scripts/evaluate.py\n')
    print(d)
