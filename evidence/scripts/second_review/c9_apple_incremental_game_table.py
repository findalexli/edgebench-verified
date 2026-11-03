#!/usr/bin/env python3
"""Table for the apple_incremental_game pool claim; see c9_pool_table.py. Run from the repo root."""
import os, runpy, sys
sys.argv = ['c9_pool_table.py', 'apple_incremental_game'] + sys.argv[1:]
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'c9_pool_table.py'), run_name='__main__')

# The same file (sha 265f3a3690, alias fork) in earlier runs: in-run grades, and judge_local on the same commit by worker.
import glob, hashlib, json
print('\nfork file, in-run grades (original release, in the Opus run)')
for f in sorted(glob.glob('evidence/runs/claude-opus-apple_incremental_game*/result/out/sforge-logs/runs/*/apple_incremental_game/submissions/*/submission.tar.gz')):
    if hashlib.sha256(open(f, 'rb').read()).hexdigest()[:10] == '265f3a3690':
        r = json.load(open(os.path.dirname(f) + '/report.json')); print(' ', f.split('/')[-2], r.get('summary'), round(r['score_0_100'], 2))
print('fork file, earlier tools/judge_local.py on community 1187e2c (quota 4, 8 vCPUs, one judge at a time), old pool, by worker')
for j, a in [('community-apple_incremental_game-r4', 'real2'), ('community-apple_incremental_game-r5', 'real2'), ('community-apple_incremental_game-r6', 'real2'), ('community2-apple_incremental_game-a1', 'agentB'), ('community2-apple_incremental_game-a2', 'agentB'), ('community2-apple_incremental_game-a3', 'agentB')]:
    v = [json.load(open(f)) for f in sorted(glob.glob(f'evidence/runs/{j}/result/out/g/{a}-p*-old.json'))]
    print(' ', j[-2:], [(d['summary'].split()[0], round(d['score_0_100'], 2)) for d in v])
