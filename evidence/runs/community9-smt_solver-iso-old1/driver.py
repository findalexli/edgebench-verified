#!/usr/bin/env python3
"""Diagnostic driver: run each hidden case of the judge's own evaluate.py in its own process (same flags: timeout 60, 16 at once, perturb, hidden salt),
so that a pool-worker death is pinned to a case instead of ending the whole evaluation. Scoring uses the evaluator's own classify_result, summarize_logic and WEIGHTS.
Crashed cases are retried with the default stack and once with a 1 GiB stack, to test the stack-overflow explanation."""
import concurrent.futures as cf, importlib.util, json, os, subprocess, sys, tempfile
EV = '/home/workspace/smt_judge/scripts/evaluate.py'
H = '/home/workspace/smt_judge/hidden_benchmarks'
TIMEOUT, SALT = 60, 'hidden-sebench'
spec = importlib.util.spec_from_file_location('ev', EV); ev = importlib.util.module_from_spec(spec); spec.loader.exec_module(ev)
def child(solver, key, path):
    r = ev.run_solver_case((solver, key, path, TIMEOUT, True, SALT))
    print(json.dumps(r))
def one(solver, key, path, stack=None):
    fd, out = tempfile.mkstemp(); os.close(fd)
    cmd = f'{sys.executable} -X faulthandler {sys.argv[0]} one {solver} {key} {path}'
    if stack: cmd = f'ulimit -s {stack}; ' + cmd
    p = subprocess.run(['bash', '-c', 'exec ' + cmd if not stack else cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    os.unlink(out)
    if p.returncode == 0:
        return json.loads(p.stdout.strip().splitlines()[-1]), p.returncode, ''
    tail = [l for l in p.stderr.splitlines() if 'Fatal' in l or 'File "' in l][:6]
    return {'benchmark': key, 'path': path, 'answer': 'error:crash', 'time': 0.0}, p.returncode, tail
if len(sys.argv) > 1 and sys.argv[1] == 'one':
    child(*sys.argv[2:5]); sys.exit(0)
solver, outp = os.path.abspath(sys.argv[1]), sys.argv[2]
expected = ev.load_expected(H + '/expected_answers.json'); manifest = ev.load_manifest(H + '/selection_manifest.json')
benchmarks = ev.find_benchmarks(H, ev.LOGICS, manifest, None)
jobs = [(l, k, p) for l in ev.LOGICS for k, p in benchmarks.get(l, [])]
rows = {}; crashes = {}
def work(j):
    return j, one(solver, j[1], j[2])
with cf.ThreadPoolExecutor(16) as ex:
    for (l, k, p), (r, rc, tail) in ex.map(work, jobs):
        rows[k] = (l, r)
        if rc != 0: crashes[k] = {'logic': l, 'difficulty': manifest.get(k, {}).get('difficulty'), 'rc': rc, 'stack': tail}
print('cases', len(rows), 'crashes', len(crashes), flush=True)
fixed = dict(rows)
for k, c in crashes.items():
    l, r0 = rows[k]
    c['retry_default_rc'] = [one(solver, k, r0['path'])[1] for _ in range(2)]
    r, rc, _ = one(solver, k, r0['path'], stack=1048576)
    c['big_stack_rc'] = rc; c['big_stack_answer'] = r.get('answer'); c['big_stack_model_valid'] = r.get('model_valid'); c['big_stack_time'] = r.get('time')
    c['expected'] = str(expected.get(k))
    fixed[k] = (l, r)
def score(src):
    per = {d: [] for d in ev.DIFFICULTIES}; rs = []
    for k, (l, r) in src.items():
        x = ev.classify_result(dict(r), expected); x['difficulty'] = manifest.get(k, {}).get('difficulty'); x['logic'] = l
        rs.append(x)
        if x['difficulty'] in per: per[x['difficulty']].append(x)
    final = sum(ev.WEIGHTS[d] * ev.summarize_logic(per[d])['score'] for d in ev.DIFFICULTIES)
    return final, rs
f1, rs1 = score(rows); f2, rs2 = score(fixed)
counts = lambda rs: {v: sum(1 for x in rs if x['verdict'] == v) for v in sorted({x['verdict'] for x in rs})}
keep = ('benchmark', 'logic', 'verdict', 'answer', 'time', 'difficulty', 'model_error')
json.dump({'final_crash_as_error': f1, 'final_crash_rerun_big_stack': f2, 'counts_crash_as_error': counts(rs1), 'counts_big_stack': counts(rs2), 'crashes': crashes,
           'rows': [{a: (str(x.get(a) or '')[:70] if a == 'model_error' else x.get(a)) for a in keep} for x in rs1]}, open(outp, 'w'), indent=0)
print('final_crash_as_error', f1, 'final_crash_rerun_big_stack', f2, flush=True)
