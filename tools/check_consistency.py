#!/usr/bin/env python3
"""Check that every published count and decision agrees with decisions.json (exit 1 on mismatch)."""
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABEL = {'retain': 'Retain', 'retain-with-note': 'Retain with note', 'repair-v2': 'Repair', 'exclude': 'Exclude'}
problems = []


def need(cond, msg):
    if not cond:
        problems.append(msg)


def main():
    d = {r['task_id']: r for r in json.loads((ROOT / 'decisions.json').read_text())}
    tasks = {p.stem for p in (ROOT / 'tasks').glob('*.json')}
    need(set(d) == tasks and len(d) == 51, f'decisions.json covers {len(d)} tasks, task dir has {len(tasks)}')
    c = Counter(r['proposed'] for r in d.values())
    # headline tables in README and the site
    readme = (ROOT / 'README.md').read_text()
    for k, n in c.items():
        lab = {'repair-v2': r'\*\*Repair \(v2\)\*\*', 'retain-with-note': 'Retain with note',
               'retain': 'Retain', 'exclude': 'Exclude'}[k]
        need(re.search(rf'\| {lab} \| \**{n}\** \|', readme), f'README count for {k} != {n}')
    site = (ROOT / 'site' / 'index.html').read_text()
    need('{{' not in site, 'site has unfilled placeholders')
    for k, n in c.items():
        need(f'"proposed": "{k}"' in site, f'site data lacks {k}')
    # decisions.csv / DECISIONS.md
    rows = list(csv.DictReader((ROOT / 'decisions.csv').open()))
    need({r['task_id']: r['decision'] for r in rows} == {t: r['proposed'] for t, r in d.items()},
         'decisions.csv disagrees with decisions.json')
    # case pages: one per task, decision line matches
    for t, r in d.items():
        p = ROOT / 'cases' / f'{t}.md'
        need(p.exists(), f'missing case page {t}')
        if p.exists():
            head = p.read_text()[:1500]
            want = LABEL[r['proposed']]
            need(re.search(rf'\*\*Decision:\*\*\s*{re.escape(want)}', head),
                 f'case page {t} decision line does not say "{want}"')
    # repairs: every repair-v2 has an accepted package; FINDINGS covers all 51
    for t, r in d.items():
        pkg = ROOT / 'repairs' / f'{t}-v2'
        if r['proposed'] == 'repair-v2':
            need(pkg.is_dir() and (pkg / 'materialize.sh').exists(), f'{t}: repair package incomplete')
            res = (pkg / 'paired' / 'results.md').read_text() if (pkg / 'paired' / 'results.md').exists() else ''
            need(re.search(r'(?i)accepted', res) and not re.search(r'(?i)NOT ACCEPTED', res.split('##')[-1]),
                 f'{t}: paired results do not end accepted')
            need(r.get('repair', '').startswith('accepted'), f'{t}: decisions.json repair not accepted')
    findings = (ROOT / 'FINDINGS.md').read_text()
    for t in d:
        need(f'cases/{t}.md' in findings, f'FINDINGS.md omits {t}')
    pairs = {r['task_id'] for r in csv.DictReader((ROOT / 'paired-results.csv').open())}
    need(pairs <= {t for t in d if (ROOT / 'repairs' / f'{t}-v2').is_dir()}, 'paired-results.csv has a task without a package')
    need({t for t, r in d.items() if r['proposed'] == 'repair-v2'} <= pairs, 'a repair has no paired rows')
    for m in problems:
        print('MISMATCH:', m)
    print(f'{dict(c)}; {len(problems)} problems')
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
