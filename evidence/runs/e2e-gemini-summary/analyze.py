"""Combine the Gemini end-to-end sweep: per task, the v1 run and the v2 run, each as the harness scored it
during the run, and each run's submissions cross-graded with both judges (xg-* jobs).

Usage: python3 analyze.py OUT.json
Selection is EdgeBench's own select_best with the task's policy; scores are converted with each version's
rescale (None when the version defines none, in which case the raw score is reported).
"""
import glob, json, os, sys
from pathlib import Path

REPO = Path('/home/alex/edgebench-verified'); sys.path.insert(0, str(REPO))
from sforge.harness.selection import select_best
from sforge.harness.score_rescale import rescale_score
from sforge.harness.benchmark import load_benchmark
from sforge.harness.task_spec import make_task_spec

RUNS = REPO / 'evidence/runs'
bench = load_benchmark(REPO / 'tasks')


def spec(t, ver):
    p = REPO / 'tasks' / f'{t}.json' if ver == 'v1' else REPO / 'repairs' / f'{t}-v2' / 'task.json.in'
    return make_task_spec(p, bench)


def run_entries(job, t):
    """History entries rebuilt from the run's own reports (reports.jsonl), in submission order (seq)."""
    f = RUNS / job / 'result/out/reports.jsonl'
    rows = sorted((json.loads(l) for l in open(f)), key=lambda r: r['seq']) if f.exists() else []
    return [{'type': 'submission', 'status': 'completed', 'round': r['round'], 'score': r['score'],
             'valid': r['valid'], 'pass_rate': r['pass_rate']} for r in rows]


def xg_entries(job, order, ver):
    rows = []
    for f in glob.glob(str(RUNS / f'xg-{job}*' / 'result/out/derived.json')):
        rows += [r for r in json.load(open(f)) if r['version'] == ver]
    by = {r['round']: r for r in rows}
    return [{'type': 'submission', 'status': 'completed', 'round': rd, 'score': by[rd]['score'],
             'valid': by[rd]['valid'], 'pass_rate': by[rd]['pass_rate']} for rd in order if rd in by]


def sel(es, s):
    b = select_best(es, s.judge.score_direction, s.judge.selection)
    b['norm'] = rescale_score(s.judge.rescale, b['best_score']) if b.get('best_score') is not None else None
    b['n'] = len(es)
    return b


out = {}
tasks = sorted({Path(p).name[len('e2e-gemini-s2h-'):-3] for p in glob.glob(str(RUNS / 'e2e-gemini-s2h-*-v[12]'))})
for t in tasks:
    res = {}
    for run_ver in ('v1', 'v2'):
        job = f'e2e-gemini-s2h-{t}-{run_ver}'
        sm = RUNS / job / 'result/summary.json'
        if not sm.exists():
            res[run_ver] = None; continue
        summ = json.load(open(sm))
        es = run_entries(job, t)
        r = {'harness': sel(es, spec(t, run_ver)), 'final_result': summ['final_result'],
             'gemini_calls': summ['gemini_calls'], 'usage': summ['usage']}
        order = [e['round'] for e in es]
        for g in ('v1', 'v2'):
            x = xg_entries(job, order, g)
            r['xg_' + g] = sel(x, spec(t, g)) if x else None
        res[run_ver] = r
    out[t] = res
json.dump(out, open(sys.argv[1], 'w'), indent=1, default=str)


def f(b):
    if not b: return '-'
    sc = b.get('best_score')
    if sc is None or b.get('best_valid') is False or (isinstance(sc, float) and sc in (float('inf'), float('-inf'))): return 'none'
    return f"{b['norm']:.2f}" if b['norm'] is not None else f"{b['best_score']:.6g}r"


print('| Task | v1 run (harness) | v2 run (harness) | v1 run: v1 judge / v2 judge | v2 run: v1 judge / v2 judge |')
print('|---|---|---|---|---|')
for t, r in out.items():
    a, b = r.get('v1'), r.get('v2')
    print(f"| {t} | {f(a and a['harness'])} | {f(b and b['harness'])} | "
          f"{f(a and a['xg_v1'])} / {f(a and a['xg_v2'])} | {f(b and b['xg_v1'])} / {f(b and b['xg_v2'])} |")
