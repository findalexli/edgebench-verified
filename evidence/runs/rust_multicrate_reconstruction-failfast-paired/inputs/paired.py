#!/usr/bin/env python3
"""KB-06b paired run. Imports the ORIGINAL, unmodified judge/tools/score.py and builds the
combined (agent code + injected hidden tests) workspace exactly as score_workspace() does.
For each crate it calls the original run_crate_test() twice on the same built workspace:
  v1: unmodified  (cargo test --frozen -p PKG -- --test-threads=4)
  v2: identical except '--no-fail-fast' is inserted after 'test' in the test-run command
      (the --list discovery command is unchanged).
Raw cargo stdout/stderr of every call is saved under /out/raw/. Nothing in score.py is edited;
v2 is applied by wrapping subprocess.run as seen by score.py."""
import json, os, subprocess, sys, tempfile, time
from dataclasses import asdict
RUN = '/tmp/cas_eval/run'
sys.path.insert(0, RUN + '/tools')
import score as S
OUT = '/out'; os.makedirs(OUT + '/raw', exist_ok=True)
S.load_split_manifest(RUN + '/hidden-tests/split-manifest.json')
ws = os.path.join(tempfile.mkdtemp(prefix='cas-hidden-inject-'), 'ws')
S.copy_workspace_tree(RUN + '/agent-start', ws, share_vendor=True)
n = S.inject_hidden_tests(ws, RUN + '/hidden-tests/hidden-sources')
print('injected', n, flush=True)
real_run = subprocess.run
state = {'arm': None, 'crate': None, 'k': 0}
def wrapped(args, **kw):
    a = list(args)
    if state['arm'] == 'v2' and a[:2] == ['cargo', 'test'] and '--list' not in a:
        a.insert(2, '--no-fail-fast')
    t = time.time()
    r = real_run(a, **kw)
    state['k'] += 1
    base = f"{OUT}/raw/{state['arm']}-{state['crate']}-{state['k']}"
    open(base + '.cmd', 'w').write(' '.join(a) + f"\nrc={r.returncode} sec={time.time()-t:.1f}\n")
    open(base + '.stdout', 'w').write(r.stdout or '')
    open(base + '.stderr', 'w').write(r.stderr or '')
    return r
S.subprocess.run = wrapped
order = sys.argv[1].split(',') if len(sys.argv) > 1 else [c for l in S.LAYER_CONFIG for c in l['crates']]
tmo = int(os.environ.get('CRATE_TIMEOUT', '1800'))
res = {'v1': {}, 'v2': {}}
for crate in order:
    for arm in ('v1', 'v2'):
        state.update(arm=arm, crate=crate)
        r = S.run_crate_test(ws, crate, tmo)
        res[arm][crate] = asdict(r)
        print(arm, crate, r.status, f'{r.passed}/{r.total} failed={r.failed}', f'{r.duration_sec:.0f}s', flush=True)
        json.dump(res, open(OUT + '/paired.json', 'w'), indent=1)
for arm in ('v1', 'v2'):
    rs = [S.CrateResult(**d) for d in res[arm].values()]
    S.classify_downstream_failures(rs)
    sc, layers = S.compute_score(rs, S.LAYER_CONFIG)
    res[arm + '_score'] = sc; res[arm + '_layers'] = layers
    print(arm, 'SCORE', sc, flush=True)
json.dump(res, open(OUT + '/paired.json', 'w'), indent=1)
