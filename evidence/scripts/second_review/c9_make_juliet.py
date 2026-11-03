#!/usr/bin/env python3
"""Job for the Juliet CWE-416 release-witness claim. Arms: real agent-8 (its own EXPERIMENT_416_FREE_SRC flag is on),
agent-8 with the flag off, real best agent-32 with the flag off and on, a generic variant, and a wrong-source bad control."""
import difflib, glob, hashlib, json, os, sys, tarfile
sys.path.insert(0, os.path.dirname(__file__))
from c9_jobs_common import job_dir, real_archive, rewrite, sub_once
T = 'juliet_vulnerability_analyzer'
UP = sys.argv[1]  # upstream tree
OFF = b'EXPERIMENT_416_FREE_SRC = False'; ON = b'EXPERIMENT_416_FREE_SRC = True'
GENERIC = (b"            if (a.get('call') or {}).get('callee') in ALLOC_FUNCS and self.fn_of(fact.path[0]) == sfn:\n",
           b"            if self.fn_of(fact.path[0]) == sfn:\n")
# bad control: a statement that is neither the allocation nor the release: the one before the sink, skipping the free.
BAD = (b"                src = fact.path[0]\n",
       b"                src = sink - 1 if sink - 1 != fact.path[0] else sink - 2\n")
new = open(sys.argv[2]).read(); old = open(sys.argv[3]).read()
paths = [f'edgebench/tasks/{T}/judge/juliet-static-analyzer-evaluator-v3/scoring/score.py',
         f'edgebench/tasks/{T}/environment/workspace/scoring/score.py']
patch = ''
for p in paths:
    assert open(UP + '/' + p).read() == old
    patch += f'diff --git a/{p} b/{p}\n' + ''.join(difflib.unified_diff(
        old.splitlines(True), new.splitlines(True), f'a/{p}', f'b/{p}'))
arms = r'''# Three passes, order reversed each pass. judge_local with task.toml limits (cpus=4); no timing claim here.
for pass in 1 2 3; do o="old new"; [ $pass = 2 ] && o="new old"
  for arm in agent8 agent8_off agent32 agent32_on agent32_generic agent32_bad; do for sd in $o; do grade $arm-p$pass $sd $arm.tar.gz 30; done; done
  for sd in $o; do grade starter-p$pass $sd empty 30; done
done
# The same analyzers on the PUBLIC labels with the shipped scorer: what a solver sees locally before submitting.
mkdir -p $O/pub
for arm in agent32 agent32_on agent32_generic; do mkdir -p /job/w/$arm; tar xzf /job/subs/$arm.tar.gz -C /job/w/$arm
  docker run --rm --network none --entrypoint python3 -v /job/w/$arm:/a -v /job/base/edgebench/tasks/$T/environment/workspace/data/public:/p:ro -w /a $IMGOLD /judge/juliet-static-analyzer-evaluator-v3/scoring/score.py --facts /p/facts.jsonl --labels /p/labels.jsonl --analyzer /a/analyzer.py --submission-root /a >$O/pub/$arm.txt 2>&1
done
# Every distinct real analyzer: how many CWE-416 true positives use the release statement as source (counts only).
docker run --rm --network none --entrypoint python3 -v /job/realscan:/r:ro -v $O:/o $IMGOLD /r/scan.py /judge/juliet-static-analyzer-evaluator-v3/data/hidden /r /o/realscan.json >$O/realscan.log 2>&1
echo "realscan rc=$?" >>$O/summary.txt
'''
d = job_dir('community9-' + T, T, 'Juliet CWE-416 release witness.', 2900, patch, arms)
a8 = real_archive(T, '', 'agent-8'); a32 = real_archive(T, '', 'agent-32')
s = d + '/subs/'
import shutil
shutil.copy(a8, s + 'agent8.tar.gz'); shutil.copy(a32, s + 'agent32.tar.gz')
M = './analyzer.py'
rewrite(a8, s + 'agent8_off.tar.gz', {M: lambda b: sub_once(b, ON, OFF)})
rewrite(a32, s + 'agent32_on.tar.gz', {M: lambda b: sub_once(b, OFF, ON)})
rewrite(a32, s + 'agent32_generic.tar.gz', {M: lambda b: sub_once(sub_once(b, OFF, ON), *GENERIC)})
rewrite(a32, s + 'agent32_bad.tar.gz', {M: lambda b: sub_once(sub_once(b, OFF, ON), *BAD)})
os.makedirs(d + '/realscan', exist_ok=True)
seen = {}
for f in sorted(glob.glob(f'evidence/runs/claude-opus-{T}*/result/out/sforge-logs/runs/opus-v1/{T}/submissions/*/submission.tar.gz')):
    with tarfile.open(f) as t:
        ms = [x for x in t if x.name in ('./analyzer.py', 'analyzer.py')]
        if not ms:
            continue
        b = t.extractfile(ms[0]).read()
    h = hashlib.sha256(b).hexdigest()[:12]
    if h not in seen:
        open(f'{d}/realscan/{h}.py', 'wb').write(b)
    seen.setdefault(h, []).append(f.split('evidence/runs/')[1].split('/')[0] + '/' + f.split('/')[-2])
json.dump(seen, open(d + '/realscan/map.json', 'w'), indent=0)
open(d + '/realscan/scan.py', 'w').write(r'''#!/usr/bin/env python3
"""Run each real analyzer on the hidden facts; count CWE-416 true positives by source form. Counts only."""
import glob, json, os, subprocess, sys, tempfile
H, R, OUT = sys.argv[1:4]
L = {(l['case_id'], l['cwe'], l['sink_stmt']): l for l in map(json.loads, open(H + '/labels.jsonl'))}
F = {}
for line in open(H + '/facts.jsonl'):
    c = json.loads(line); F[c['case_id']] = c
def is_release(case, sid):
    for s in F[case]['stmts']:
        if s.get('stmt_id') == sid:
            return (s.get('call') or {}).get('callee') == 'free' or (s.get('tokens') or [''])[0] == 'delete'
    return False
res = {}
for p in sorted(glob.glob(R + '/*.py')):
    h = os.path.basename(p)[:-3]
    if h == 'scan':
        continue
    with tempfile.TemporaryDirectory() as td:
        o = td + '/f.json'
        try:
            r = subprocess.run([sys.executable, p, '--input', H + '/facts.jsonl', '--output', o], cwd=td, capture_output=True, timeout=60)
            P = json.load(open(o))['findings']
        except Exception as e:
            res[h] = {'error': type(e).__name__}; continue
    tp = rel = ok = 0
    for x in P:
        try:
            k = (str(x['case_id']), str(x['cwe']), int(x['sink_stmt']))
        except Exception:
            continue
        if k in L and k[1] == 'CWE-416':
            tp += 1
            if int(x.get('source_stmt', -1)) == L[k]['source_stmt']: ok += 1
            elif is_release(k[0], int(x.get('source_stmt', -1))): rel += 1
    res[h] = {'cwe416_tp': tp, 'label_source': ok, 'release_source': rel}
json.dump(res, open(OUT, 'w'), indent=0)
''')
print(d, len(seen), 'distinct analyzers')
