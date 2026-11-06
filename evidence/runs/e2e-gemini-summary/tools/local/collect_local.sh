#!/bin/bash
# collect_e2e.sh JOB: for a finished e2e run, require exit=0, remove the per-run judge admin secret and the
# tarballs (checkpoints are superseded by result/out), write summary.json, then generate and launch its cross-grade.
set -u
E=$(cd $(dirname $0)/.. && pwd)
R=/home/alex/edgebench-verified; cd $R/evidence/runs; J=$1
grep -q '"status": "exit=0"' $J/result/worker.json || { echo "$J NOT exit=0: $(grep -o '"status": "[^"]*"' $J/result/worker.json)"; exit 1; }
find $J/result -name .judge-admin-secret -delete
mkdir -p $R/.internal/e2e-tarballs/$J; mv $J/result/*.tar.gz $R/.internal/e2e-tarballs/$J/ 2>/dev/null
python3 - $J <<'P'
import json, re, sys, glob
j = sys.argv[1]; o = f'{j}/result/out'
txt = open(f'{o}/run_stdout.log').read()
m = re.findall(r'^\{\n.*?^\}', txt, re.S | re.M)
res = json.loads(m[-1]) if m else None
calls = [json.loads(l) for l in open(f'{o}/proxy.jsonl')]
u = {}
for c in calls:
    for k, v in (c.get('usage') or {}).items():
        if isinstance(v, int): u[k] = u.get(k, 0) + v
subs = sorted(glob.glob(f'{o}/sforge-logs/runs/*/*/submissions/*/report.json'))
s = {'job': j, 'run_exit': open(f'{o}/run_exit.txt').read().strip(), 'final_result': res,
     'gemini_calls': len(calls), 'gemini_status': {str(k): sum(1 for c in calls if c.get('status') == k) for k in {c.get('status') for c in calls}},
     'usage': u, 'n_submissions': len(subs)}
json.dump(s, open(f'{j}/result/summary.json', 'w'), indent=1)
fr = res or {}
print(j, s['run_exit'], 'subs', len(subs), 'best', fr.get('best_score'), fr.get('best_round'), 'calls', len(calls))
P
