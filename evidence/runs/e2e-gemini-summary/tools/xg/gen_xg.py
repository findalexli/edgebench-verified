#!/usr/bin/env python3
"""gen_xg.py E2E_JOB...: make one cross-grade job per finished e2e run (evidence/runs/xg-<e2e job>).

Every submission the run archived (submissions/<round>/{submission.tar.gz,eval.sh,allowed_files.txt}) is
graded with the original judge (the pinned FROM digest of the repair Dockerfile) and the fixed judge (built
from the repair package). Tasks whose repair does not change the judge image are skipped (printed).
"""
import json, os, re, shutil, sys
from pathlib import Path

REPO = Path('/home/alex/edgebench-verified'); HERE = Path(__file__).resolve().parent
SHARD = os.environ.get('SHARD', ''); ONLY = [x for x in os.environ.get('ROUNDS', '').split(',') if x]
for name in sys.argv[1:]:
    e2e = REPO / 'evidence/runs' / name
    p = dict(l.split('=', 1) for l in (e2e / 'params.env').read_text().split())
    t = p['TASK']
    df = REPO / f'repairs/{t}-v2/Dockerfile'
    fro = re.findall(r'^FROM\s+(?:--\S+\s+)?(\S+@sha256:\S+)', df.read_text(), re.M) if df.exists() else []
    v1 = json.load(open(REPO / f'tasks/{t}.json')); v2 = json.load(open(REPO / f'repairs/{t}-v2/task.json.in'))
    if not fro or 'judge' not in fro[0] or v1['judge'].get('image_tag') == v2['judge'].get('image_tag'):
        print(name, 'skip: repair does not change the judge image'); continue
    subs = sorted((e2e / 'result/out/sforge-logs/runs').glob(f'*/{t}/submissions/*/eval.sh'))
    if not subs:  # slimmed run: the submissions are archived outside the repository
        subs = sorted((REPO / '.internal/e2e-artifacts' / name / 'result/out/sforge-logs/runs').glob(f'*/{t}/submissions/*/eval.sh'))
    if ONLY: subs = [s for s in subs if s.parent.name in ONLY]
    if not subs:
        print(name, 'skip: no submissions'); continue
    j = REPO / 'evidence/runs' / f'xg-{name}{SHARD}'
    assert not j.exists(), j
    (j / 'ebv').mkdir(parents=True)
    rounds = []
    for ev in subs:
        r = ev.parent.name; rounds.append(r)
        d = j / 'subs' / r; d.mkdir(parents=True)
        for f in ('submission.tar.gz', 'eval.sh', 'allowed_files.txt'):
            if (ev.parent / f).exists(): shutil.copy(ev.parent / f, d / f)
    shutil.copytree(REPO / f'repairs/{t}-v2', j / 'pkg', ignore=shutil.ignore_patterns('paired', 'files', 'orig'))
    shutil.copytree(REPO / 'tasks', j / 'ebv/tasks')
    for f in ('run.sh', 'judge.sh'): shutil.copy(HERE / f, j / f)
    (j / 'plan.txt').write_text('\n'.join(rounds) + '\n')
    (j / 'params.env').write_text(f"TASK={t}\nV1={fro[0]}\nCWD={v1['cwd']}\nTO1={v1['judge']['eval_timeout']}\n"
                                  f"TO2={v2['judge']['eval_timeout']}\n")
    print(j.name, len(rounds), 'rounds')
