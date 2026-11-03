#!/usr/bin/env python3
"""SMT textual lookup: stub arms on the full hidden set (sforge eval), real solver r1 auto-6 on the 69 affected files and on the full set, the public view."""
import collections, glob, json, os, re, statistics as st
J = sorted(glob.glob('evidence/runs/community9-smt_solver-*/result/out'))
print('--- full hidden set, sforge eval: raw, 0-100, correct/774')
rows = {}
for o in J:
    for f in glob.glob(o + '/s/*.report.json'):
        m = re.match(r'(.+?)-(p\d|full\d)-(old|new)\.report\.json', os.path.basename(f))
        if not m: continue  # real-stack* reports are printed in their own section below
        d = json.load(open(f)); x = d.get('metrics') or {}
        rows.setdefault((m.group(1), m.group(3)), []).append((m.group(2), o.split('/')[2][-9:], d['score'], d['score_0_100'], d['valid'], d['summary'], round(d['runtime_seconds'], 1), x.get('by_difficulty') or x.get('difficulty_summary')))
for k in sorted(rows):
    v = sorted(rows[k], key=str)
    print(k[0], k[1], len(v), [x[3] for x in v], v[0][5], [x[6] for x in v])
print('--- 69 affected hidden sat files: verdict counts per run')
rows = {}
for o in J:
    for f in glob.glob(o + '/sub/*/res.json'):
        m = re.match(r'(.+)-p(\d)-(old|new)$', os.path.basename(os.path.dirname(f)))
        d = json.load(open(f)); c = collections.Counter(r['verdict'] for r in d['rows'])
        dif = collections.Counter(r['difficulty'] for r in d['rows'] if r['verdict'] == 'correct')
        rows.setdefault((m.group(1), m.group(3)), []).append((o.split('/')[2][-5:], m.group(2), dict(c), dict(dif), collections.Counter(r['model_error'].split(' for ')[0][:24] for r in d['rows'] if r['verdict'] == 'invalid_model').most_common(3)))
for k in sorted(rows):
    for r in sorted(rows[k], key=str):
        print(k[0], k[1], *r)
print('--- public QF_UF and QF_UFLRA, shipped evaluate.py')
for o in J:
    for f in sorted(glob.glob(o + '/pub/*/res.json')):
        d = json.load(open(f)); print(o.split('/')[2][-5:], os.path.basename(os.path.dirname(f)), dict(collections.Counter(r['verdict'] for r in d['rows'])))
print('--- real reports')
rs = collections.Counter(); arch = collections.Counter(); tot = 0
for f in glob.glob('evidence/runs/claude-opus-smt_solver*/result/out/sforge-logs/runs/*/smt_solver/submissions/*/report.json'):
    d = json.load(open(f)); rs[d.get('score_0_100')] += 1; tot += 1
print('reports', tot, dict(rs))
print('archives without report: r1 auto-4, auto-5, auto-6 share one sha', len({open(f, 'rb').read() for f in glob.glob('evidence/runs/claude-opus-smt_solver/result/out/sforge-logs/runs/*/smt_solver/submissions/auto-[456]/submission.tar.gz')}))
print('--- real solver, full hidden set: official sforge eval, no fix (fulla-old, fulla-new, fullb-old) and direct evaluate.py (direct16-old)')
for j in ('fulla-old', 'fullb-old', 'fulla-new'):
    for f in glob.glob(f'evidence/runs/community9-smt_solver-{j}/result/out/s/*.report.json'):
        d = json.load(open(f)); print(j, d['summary'], 'valid', d['valid'], 'runtime', round(d['runtime_seconds']))
D = 'evidence/runs/community9-smt_solver-direct16-old/result/out/direct/'
if os.path.exists(D + 'eval.err'):
    print('direct16-old stderr last line:', open(D + 'eval.err').read().strip().splitlines()[-1][:120]); print('direct16-old cgroup:', ' '.join(open(D + 'run.log').read().split()[:12]))
print('--- real solver, full hidden set, one process per case, evaluator\'s own scoring (raw final, crashes, verdicts)')
for f in sorted(glob.glob('evidence/runs/community9-smt_solver-iso-*/result/out/iso/res.json')):
    d = json.load(open(f)); j = f.split('/')[2].split('-')[-2:]
    print('-'.join(j), round(d['final_crash_as_error'] * 100, 2), 'crashes', len(d['crashes']), [v['rc'] for v in d['crashes'].values()], 'retries', [v['retry_default_rc'] for v in d['crashes'].values()], 'big stack rc', [v['big_stack_rc'] for v in d['crashes'].values()], 'valid', [v['big_stack_model_valid'] for v in d['crashes'].values()], d['counts_crash_as_error'], open(f.replace('res.json', 'run.log')).read().split('oom_kill')[1].split()[0] + ' oom kills')
print('--- real solver, full hidden set, sforge eval, stack fix on both judges')
for f in sorted(glob.glob('evidence/runs/community9-smt_solver-stack-*/result/out/s/*.report.json')):
    d = json.load(open(f)); print(f.split('/')[2].split('-')[-1], d['summary'], 'valid', d['valid'], 'runtime', round(d['runtime_seconds']))
