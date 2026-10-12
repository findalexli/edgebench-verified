#!/usr/bin/env python3
"""Summarize paired runs: score (raw == normalized; rescale linear 0..1), pass_rate, phase lines, per-test diffs."""
import json, re, sys
from pathlib import Path
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
        res = re.search(r'^Result: .*$', t, re.M); r['result'] = res.group(0) if res else ''
        for name, st in re.findall(r'^(?:\.\./|/)?(tests/\S+::\S+) (PASSED|FAILED|ERROR)', t, re.M):
            r['tests'][name] = st
    r['exit'] = (d / 'docker_exit').read_text().strip() if (d / 'docker_exit').exists() else '?'
    r['seconds'] = (d / 'seconds').read_text().strip() if (d / 'seconds').exists() else '?'
    return r
variants = sorted({p.name.rsplit('.', 1)[0] for p in root.iterdir()})
out = {}
print('| variant | v1 score | v2 score | delta | v1 pass_rate | v2 pass_rate | v1 phases | v2 phases | exits | secs |')
print('|---|---|---|---|---|---|---|---|---|---|')
for v in variants:
    a, b = load(root / f'{v}.v1'), load(root / f'{v}.v2'); out[v] = {'v1': a, 'v2': b}
    d = (b['score'] - a['score']) if None not in (a['score'], b['score']) else None
    fmt = lambda x: 'n/a' if x is None else f'{x:.6f}'
    print(f"| {v} | {fmt(a['score'])} | {fmt(b['score'])} | {'n/a' if d is None else f'{d:+.6f}'} | {fmt(a['pass_rate'])} | {fmt(b['pass_rate'])} | {'; '.join(x.split(':')[0]+':'+x.split(':')[1].split()[0] for x in a['phases'])} | {'; '.join(x.split(':')[0]+':'+x.split(':')[1].split()[0] for x in b['phases'])} | {a['exit']}/{b['exit']} | {a['seconds']}/{b['seconds']} |")
print('\n## Per-test outcome differences v1 -> v2 (tests absent in one version shown as -)\n')
for v in variants:
    a, b = out[v]['v1']['tests'], out[v]['v2']['tests']
    diffs = [(n, a.get(n, '-'), b.get(n, '-')) for n in sorted(set(a) | set(b)) if a.get(n) != b.get(n)]
    print(f'- **{v}**: {len(a)} v1 items, {len(b)} v2 items; ' + ('no differences' if not diffs else ', '.join(f'`{n.split("::")[-1]}` {x}->{y}' for n, x, y in diffs)))
(root.parent / 'summary.json').write_text(json.dumps(out, indent=1))
