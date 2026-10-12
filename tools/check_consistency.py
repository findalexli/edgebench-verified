#!/usr/bin/env python3
"""Check that every published count and decision agrees with data/decisions.json (exit 1 on mismatch)."""
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABEL = {'retain': 'Kept as is', 'retain-with-note': 'Kept, with a note', 'repair-v2': 'Fixed', 'exclude': 'Removed'}
problems = []


def need(cond, msg):
    if not cond:
        problems.append(msg)


def main():
    d = {r['task_id']: r for r in json.loads((ROOT / 'data/decisions.json').read_text())}
    tasks = {p.stem for p in (ROOT / 'tasks').glob('*.json')}
    need(set(d) == tasks and len(d) == 51, f'data/decisions.json covers {len(d)} tasks, task dir has {len(tasks)}')
    c = Counter(r['proposed'] for r in d.values())
    # headline tables in README and the site
    readme = (ROOT / 'README.md').read_text()
    for k, n in c.items():
        lab = {'repair-v2': r'\*\*Fixed\*\*', 'retain-with-note': 'Kept, with a note',
               'retain': 'Kept as is', 'exclude': 'Removed'}[k]
        need(re.search(rf'\| {lab} \| \**{n}\** \|', readme), f'README count for {k} != {n}')
    site = (ROOT / 'site' / 'index.html').read_text()
    need(not re.findall(r'\{\{[\w|:-]+\}\}', site), 'site has unfilled placeholders')
    for k, n in c.items():
        need(f'"proposed": "{k}"' in site, f'site data lacks {k}')
    # data/decisions.csv / DECISIONS.md
    rows = list(csv.DictReader((ROOT / 'data/decisions.csv').open()))
    need({r['task_id']: r['decision'] for r in rows} == {t: r['proposed'] for t, r in d.items()},
         'data/decisions.csv disagrees with data/decisions.json')
    # plain summaries: one per task, action line agrees with the decision
    plain = json.loads((ROOT / 'cases' / 'plain.json').read_text())
    need(set(plain) == set(d), 'cases/plain.json does not cover exactly the 51 tasks')
    pre = {'retain': 'Kept as is', 'retain-with-note': 'Kept, with a note', 'repair-v2': 'Fixed in a new version', 'exclude': 'Removed'}
    for t, r in d.items():
        need(plain.get(t, {}).get('action', '').startswith(pre[r['proposed']]), f'{t}: plain action disagrees with decision')
    # case pages: one per task, decision line matches
    for t, r in d.items():
        p = ROOT / 'cases' / f'{t}.md'
        need(p.exists(), f'missing case page {t}')
        if p.exists():
            head = p.read_text()[:1500]
            want = LABEL[r['proposed']]
            need(re.search(rf'\*\*Outcome:\*\*\s*{re.escape(want)}', head),
                 f'case page {t} decision line does not say "{want}"')
    # repairs: every repair-v2 has an accepted package; FINDINGS covers all 51
    for t, r in d.items():
        pkg = ROOT / 'repairs' / f'{t}-v2'
        if r['proposed'] == 'repair-v2':
            need(pkg.is_dir() and (pkg / 'materialize.sh').exists(), f'{t}: repair package incomplete')
            res = (pkg / 'paired' / 'results.md').read_text() if (pkg / 'paired' / 'results.md').exists() else ''
            need(re.search(r'(?i)accepted', res) and not re.search(r'(?i)NOT ACCEPTED', res.split('##')[-1]),
                 f'{t}: paired results do not end accepted')
            need(r.get('repair', '').startswith('accepted'), f'{t}: data/decisions.json repair not accepted')
    findings = (ROOT / 'FINDINGS.md').read_text()
    for t in d:
        need(f'cases/{t}.md' in findings, f'FINDINGS.md omits {t}')
    pairs = {r['task_id'] for r in csv.DictReader((ROOT / 'data/paired-results.csv').open())}
    need(pairs <= {t for t in d if (ROOT / 'repairs' / f'{t}-v2').is_dir()}, 'data/paired-results.csv has a task without a package')
    need({t for t, r in d.items() if r['proposed'] == 'repair-v2'} <= pairs, 'a repair has no paired rows')
    # README impact sentence agrees with data/impact.csv
    imp = list(csv.DictReader((ROOT / 'data/impact.csv').open()))
    sh = [float(r['exact_adjusted_mean']) - float(r['recomputed_mean']) for r in imp]
    dn = max(float(r['exact_adjusted_mean']) - float(r['bounded_low']) for r in imp)
    up = max(float(r['bounded_high']) - float(r['exact_adjusted_mean']) for r in imp)
    for txt in (f'{min(sh):.1f}–{max(sh):.1f} points', f'at most {dn:.1f} points down or {up:.1f} up'):
        need(txt in ' '.join(readme.split()), f'README impact text missing "{txt}"')
    for m in problems:
        print('MISMATCH:', m)
    print(f'{dict(c)}; {len(problems)} problems')
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
