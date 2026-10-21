"""Rescale-only repairs across runs: selected score under v1 vs v2, from each run's recorded history."""
import json, sys
from pathlib import Path
REPO = Path('/home/alex/edgebench-verified'); sys.path.insert(0, str(REPO))
from sforge.harness.selection import select_best
from sforge.harness.score_rescale import rescale_score
from sforge.harness.benchmark import load_benchmark
from sforge.harness.task_spec import make_task_spec
bench = load_benchmark(REPO / 'tasks')
T = Path('/tmp/claude-1000/-home-alex-edgebench-verified/37502328-a9c5-450d-9933-406e7f73e061/scratchpad/traces')
runs = {'Opus 5.5 xhigh (Claude Code, 4h)': REPO / 'evidence/runs/opus55-rollouts-meta/result/meta/opus-16x4h-1009-0036-w1',
        'Qwen3.5-122B (Codex, 4-8h)': REPO / '.internal/qwen35-meta',
        'Qwen3.8 Flash Next (Codex, 12h)': T / 'q38meta/export-full47/harness'}
for k in ('full50-20260908-213644', 'full50-max-20260909-230641', 'full50-max-cont8h-20260911-012000'):
    runs[f'Kimi-K3 {k}'] = ('kimi', T / 'kimi/x' / k / 'harness/runs', k)
res = []
for t in ('treant_forest', 'borden_source_inversion'):
    s1 = make_task_spec(REPO / 'tasks' / f'{t}.json', bench); s2 = make_task_spec(REPO / 'repairs' / f'{t}-v2' / 'task.json.in', bench)
    for name, base in runs.items():
        p = (base[1] / f'{base[2]}-{t}' / t / 'run_history.json') if isinstance(base, tuple) else base / t / 'run_history.json'
        if not p.exists(): continue
        h = json.load(open(p)); E = h['entries'] if isinstance(h, dict) else h
        n = sum(1 for e in E if e.get('type') == 'submission')
        b = select_best([dict(e) for e in E], s1.judge.score_direction, s1.judge.selection)
        if b['best_score'] is None: print(t, name, 'no valid'); continue
        v1 = rescale_score(s1.judge.rescale, b['best_score']); v1 = b['best_score'] if v1 is None else v1
        v2 = rescale_score(s2.judge.rescale, b['best_score'])
        res.append({'task': t, 'run': name, 'submissions': n, 'best_round': b['best_round'], 'raw': b['best_score'], 'v1': v1, 'v2': v2})
        print(f"{t:24s} {name:48s} subs={n:4d} best={b['best_round']:9s} raw={b['best_score']:<12.6g} v1={v1:6.2f} v2={v2:6.2f}")
json.dump(res, open(T / 'rescale_runs.json', 'w'), indent=1)
