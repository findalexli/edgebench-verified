#!/usr/bin/env python3
"""Summarize three-arm runs (v1 original, v2prev first fixed version, v2 revised): score
(raw == normalized; rescale linear 0..1), pass_rate, phase lines, per-test differences."""
import json, re, sys
from pathlib import Path
ARMS = ['v1', 'v2prev', 'v2']
root = Path(sys.argv[1])
def load(d):
    r = {'score': None, 'pass_rate': None, 'phases': [], 'tests': {}}
    s = (d / 'structured_result.log')
    if s.exists():
        m = re.search(r'>>>>> Start Structured Result\n(.*)\n>>>>> End Structured Result', s.read_text(), re.S)
        if m:
            j = json.loads(m.group(1)); r['score'] = j['score']; r['pass_rate'] = j['pass_rate']; r['valid'] = j.get('valid')
    f = d / 'test_full.log'
    if f.exists():
        t = f.read_text(errors='replace')
        r['phases'] = re.findall(r'^Phase \d+: \d+/\d+ passed$', t, re.M)
        for name, st in re.findall(r'^(?:\.\./|/)?(tests/\S+::\S+) (PASSED|FAILED|ERROR)', t, re.M):
            r['tests'][name] = st
    r['exit'] = (d / 'docker_exit').read_text().strip() if (d / 'docker_exit').exists() else '?'
    r['seconds'] = (d / 'seconds').read_text().strip() if (d / 'seconds').exists() else '?'
    return r
fmt = lambda x: 'n/a' if x is None else f'{x:.6f}'
ph = lambda r: '; '.join(x.split(':')[0].replace('Phase ', 'P') + ':' + x.split(':')[1].split()[0] for x in r['phases'] if x.startswith(('Phase 2', 'Phase 5')))
variants = sorted({p.name.rsplit('.', 1)[0] for p in root.iterdir()})
out = {}
print('| variant | ' + ' | '.join(f'{a} score' for a in ARMS) + ' | v2 - v1 | v2 - v2prev | ' + ' | '.join(f'{a} P2; P5' for a in ARMS) + ' | exits |')
print('|---' * (2 * len(ARMS) + 4) + '|')
for v in variants:
    rs = {a: load(root / f'{v}.{a}') for a in ARMS}; out[v] = rs
    d = lambda x, y: 'n/a' if None in (rs[x]['score'], rs[y]['score']) else f"{rs[x]['score'] - rs[y]['score']:+.6f}"
    print(f"| {v} | " + ' | '.join(fmt(rs[a]['score']) for a in ARMS) + f" | {d('v2', 'v1')} | {d('v2', 'v2prev')} | "
          + ' | '.join(ph(rs[a]) for a in ARMS) + ' | ' + '/'.join(rs[a]['exit'] for a in ARMS) + ' |')
print('\n## Per-test outcomes that differ between arms (v1 / v2prev / v2; - = test absent)\n')
for v in variants:
    t = {a: out[v][a]['tests'] for a in ARMS}
    names = sorted(set().union(*t.values()))
    diffs = [(n, [t[a].get(n, '-') for a in ARMS]) for n in names if len({t[a].get(n, '-') for a in ARMS}) > 1]
    print(f'- **{v}**: ' + ('no differences' if not diffs else ', '.join(f'`{n.split("::")[-1]}` {"/".join(s)}' for n, s in diffs)))
(root.parent / 'summary.json').write_text(json.dumps(out, indent=1))
