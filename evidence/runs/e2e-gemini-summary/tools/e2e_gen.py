#!/usr/bin/env python3
"""Create one end-to-end agent job per (task, version) under evidence/runs/.

Usage: e2e_gen.py RUNTAG VERSION AGENT_TIMEOUT TASK...
  VERSION v1 = the original task as published; v2 = the repair package built on the worker.
Job name: e2e-gemini-<RUNTAG>-<task>-<version>.
"""
import shutil, sys
from pathlib import Path

REPO = Path('/home/alex/edgebench-verified')
E2E = Path(__file__).resolve().parent
tag, ver, timeout, tasks = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4:]
assert ver in ('v1', 'v2')
ign = shutil.ignore_patterns('__pycache__', '*.pyc', '.git')
for t in tasks:
    job = REPO / 'evidence' / 'runs' / f'e2e-gemini-{tag}-{t}-{ver}'
    job.mkdir(exist_ok=False)
    shutil.copy(E2E / 'run.sh', job / 'run.sh')
    (job / 'common').mkdir()
    for f in ('flex_proxy.py', 'experiment.yaml'):
        shutil.copy(E2E / f, job / 'common' / f)
    shutil.copytree(REPO / 'sforge', job / 'ebv' / 'sforge', ignore=ign)
    shutil.copytree(REPO / 'tasks', job / 'ebv' / 'tasks', ignore=ign)
    if ver == 'v2':
        shutil.copytree(REPO / 'repairs' / f'{t}-v2', job / 'pkg',
                        ignore=shutil.ignore_patterns('paired', 'files', 'orig', '__pycache__'))
    (job / 'params.env').write_text(
        f'TASK={t}\nVERSION={ver}\nMODEL_ID=gemini-4-argon\nAGENT_TIMEOUT={timeout}\nEVAL_INTERVAL=300\n'
        f'WORK_CPU=4\nWORK_MEM=4g\nJUDGE_CPU=4\nJUDGE_MEM=3g\nRUN_ID={tag}-{ver}\n')
    print(job.name)
