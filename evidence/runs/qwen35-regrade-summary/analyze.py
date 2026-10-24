"""Combine derived rows from all regrade2 jobs; per task: paired v1/v2, selection under each grader."""
import json, glob, sys, statistics as st
from pathlib import Path
REPO = Path('/home/alex/edgebench-verified'); sys.path.insert(0, str(REPO))
from sforge.harness.selection import select_best
from sforge.harness.score_rescale import rescale_score
from sforge.harness.benchmark import load_benchmark
from sforge.harness.task_spec import make_task_spec
bench = load_benchmark(REPO / 'tasks')
rows = []
for f in sorted(glob.glob(str(REPO / 'evidence/runs/qwen35-regrade-*/result/out/derived.json'))):
    for r in json.load(open(f)): r['job'] = f.split('/')[-4]; rows.append(r)
hist = {}
for f in glob.glob(str(REPO / '.internal/qwen35-meta/*/run_history.json')):
    hist[f.split('/')[-2]] = json.load(open(f))['entries']
out = {}
for t in sorted({r['task'] for r in rows}):
    s1 = make_task_spec(REPO / 'tasks' / f'{t}.json', bench); s2 = make_task_spec(REPO / 'repairs' / f'{t}-v2' / 'task.json.in', bench)
    R = [r for r in rows if r['task'] == t]
    by = {}
    for r in R: by.setdefault(r['round'], {}).setdefault(r['version'], []).append(r)
    H = hist[t]; orig = {}
    for e in H: orig[e['round']] = e  # later duplicate wins (its tarball is the archived one)
    def entries(ver, agg):
        es = []; seen = set()
        for e in H:
            rd = e['round']
            if rd in seen: continue  # duplicated round names: one archived tarball
            seen.add(rd)
            if ver == 'v1' and rd in by and 'v1' not in by[rd] and 'v2' in by[rd] and e.get('type') == 'submission':
                # V2_ONLY follow-up shard (tree_block only): its v1 regrade reproduced all the recorded rounds it graded,
                # so the recorded result stands in for the v1 arm on the rounds it did not regrade.
                es.append(dict(e)); continue
            if rd not in by or ver not in by[rd]: continue
            g = by[rd][ver]; sc = [x['score'] for x in g if x['score'] is not None]
            val = agg(sc) if sc else None
            es.append({'type': 'submission', 'status': 'completed', 'round': rd, 'valid': all(x['valid'] for x in g),
                       'pass_rate': st.mean(x['pass_rate'] or 0 for x in g), 'score': val})
        return es
    pol, d = s1.judge.selection, s1.judge.score_direction
    origsel = select_best([dict(e) for e in H], d, pol)
    res = {'policy': pol, 'n_history': len(H), 'n_graded': len(by),
           'orig_recorded': {**origsel, 'norm': rescale_score(s1.judge.rescale, origsel['best_score'])}}
    for name, agg in (('mean', st.mean), ('min', min), ('max', max)):
        e1 = entries('v1', agg); e2 = entries('v2', agg)
        b1 = select_best(e1, d, pol); b2 = select_best(e2, d, pol)
        res['sel_' + name] = {'v1': {**b1, 'norm': rescale_score(s1.judge.rescale, b1['best_score'])},
                              'v2': {**b2, 'norm': rescale_score(s2.judge.rescale, b2['best_score'])}}
    per = []
    for rd, vv in by.items():
        o = orig.get(rd, {})
        def summ(g): 
            sc = [x['score'] for x in g]
            return {'scores': sc, 'valid': [x['valid'] for x in g], 'passed': [x['passed'] for x in g], 'total': g[0]['total_tests'],
                    'wall': [x['wall_s'] for x in g], 'timed_out': any(x['timed_out'] for x in g),
                    'norm': [rescale_score((s1 if g[0]['version']=='v1' else s2).judge.rescale, x) for x in sc]}
        per.append({'round': rd, 'orig_score': o.get('score'), 'orig_valid': o.get('valid'), 'orig_pr': o.get('pass_rate'),
                    'v1': summ(vv.get('v1', [])) if 'v1' in vv else None, 'v2': summ(vv.get('v2', [])) if 'v2' in vv else None})
    res['per'] = per
    out[t] = res
json.dump(out, open(sys.argv[1], 'w'), separators=(',', ':'), sort_keys=True, default=str)
for t, r in out.items():
    print('==', t, r['policy'], 'graded', r['n_graded'], '/', r['n_history'])
    print('   orig recorded:', r['orig_recorded']['best_round'], r['orig_recorded']['best_score'], r['orig_recorded']['norm'])
    for k in ('mean', 'min', 'max'):
        v1, v2 = r['sel_' + k]['v1'], r['sel_' + k]['v2']
        print('   sel[%s] v1:' % k, v1['best_round'], v1['best_score'], v1['norm'], '| v2:', v2['best_round'], v2['best_score'], v2['norm'])
