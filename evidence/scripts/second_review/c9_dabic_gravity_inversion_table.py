#!/usr/bin/env python3
"""DABIC data-space gate: sforge eval scores per arm and judge, with the components and gate fields, plus the C/D/F reached by every real report."""
import glob, json, os, re, statistics as st
J = ['community9-dabic_gravity_inversion-smoke', 'community9-dabic_gravity_inversion-a', 'community9-dabic_gravity_inversion-b']
rows = {}
for j in J:
    for f in glob.glob(f'evidence/runs/{j}/result/out/s/*.report.json'):
        m = re.match(r'(.+)-p(\d)-(old|new)\.report\.json', os.path.basename(f))
        d = json.load(open(f)); x = d.get('metrics') or {}
        g = dict(re.findall(r'([A-F])=([\d.]+)', d.get('summary') or ''))
        rows.setdefault((m.group(1), m.group(3)), []).append(dict(j=j[-5:], p=m.group(2), score=d['score'], valid=d['valid'], C=g.get('C'), E=g.get('E'), A=g.get('A'), pen=x.get('structural_penalty'), data=x.get('is_data_space'), sf=x.get('structural_failure'), ndata=x.get('n_data_space_matrix_matches'), ncell=x.get('n_model_space_matrix_matches'), t=round(d['runtime_seconds'], 1)))
print('arm judge n mean min max | per run: score C E pen is_data structural_failure data_matches cell_matches seconds')
for k in sorted(rows):
    v = sorted(rows[k], key=lambda r: r['p'])
    s = [r['score'] for r in v]
    print(k[0], k[1], len(v), round(st.mean(s), 3), round(min(s), 3), round(max(s), 3))
    for r in v:
        print('   ', r['j'], 'p' + r['p'], round(r['score'], 4), r['valid'], 'A', r['A'], 'C', r['C'], 'E', r['E'], 'pen', r['pen'], r['data'], r['sf'], r['ndata'], r['ncell'], r['t'])
print('--- real reports (claude-opus-*)')
rs = []
for f in glob.glob('evidence/runs/claude-opus-dabic_gravity_inversion*/result/out/sforge-logs/runs/*/dabic_gravity_inversion/submissions/*/report.json'):
    d = json.load(open(f)); m = d.get('metrics') or {}; o = m.get('penalty_observed') or {}
    rs.append((d.get('score') or 0, o.get('C') or 0, o.get('D') or 0, o.get('F') or 0, m.get('structural_penalty'), m.get('is_data_space'), m.get('n_model_space_matrix_matches') or 0, f.split('runs/')[1].split('/')[0][-3:] + '/' + f.split('/')[-2]))
print('reports', len(rs), 'best', max(rs)[:5], max(rs)[7], 'maxC', max(r[1] for r in rs), 'maxD', max(r[2] for r in rs), 'maxF', max(r[3] for r in rs))
print('C>=19.5', sum(r[1] >= 19.5 for r in rs), 'C>=26', sum(r[1] >= 26 for r in rs), 'F>=10', sum(r[3] >= 10 for r in rs), 'penalties', sorted({r[4] for r in rs}, key=str), 'model-space hits', sum(r[6] > 0 for r in rs), 'is_data_space false', sum(r[5] is False for r in rs))
