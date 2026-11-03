#!/usr/bin/env python3
"""Generate DECISIONS.md and data/decisions.csv from data/decisions.json and cases/plain.json."""
import csv
import json
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from names import names as task_names  # noqa: E402
import review as RV  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ORDER = ['repair-v2', 'exclude', 'retain-with-note', 'retain']
LABEL = {'retain': 'Kept as is', 'retain-with-note': 'Kept, with a note', 'repair-v2': 'Fixed', 'exclude': 'Removed'}
MEANING = {'retain': 'No problem found.',
           'retain-with-note': 'No correctable problem found. The note records caveats that no change to the grader removes, including run-to-run or machine-dependent variation, with its size stated or marked unmeasured. Some are not small; the largest, in ANN Vector Search, is about ±7 of 100 points per grading.',
           'repair-v2': 'A problem that changes scores, with a versioned repair package. This outcome is historical and does not certify every current release; APPLYING-FIXES.md and each case page give the component coverage and the integration still pending.',
           'exclude': 'A problem without a sound fix; the task is not part of the verified set.'}


def main():
    rows = sorted(json.loads((ROOT / 'data/decisions.json').read_text()), key=lambda r: r['task_id'])
    plain = json.loads((ROOT / 'cases' / 'plain.json').read_text())
    names = task_names()
    assert len(rows) == 51 and set(plain) == {r['task_id'] for r in rows}
    counts = Counter(r['proposed'] for r in rows)
    rev = RV.load()
    with (ROOT / 'data/decisions.csv').open('w', newline='') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['task_id', 'name', 'decision', 'outcome', 'summary', 'effect', 'what_we_did',
                    'technical_finding', 'technical_max_effect', 'fixed_version_folder', 'validation_status',
                    'problem_category', 'secondary_problem_categories', 'second_review_status'])
        for r in rows:
            t = r['task_id']
            w.writerow([t, names[t], r['proposed'], LABEL[r['proposed']], plain[t]['headline'], plain[t]['effect'],
                        plain[t]['action'], r['finding'], r.get('max_effect', ''), r.get('package', ''), r.get('validation_status') or ('Historical paired scope only; see the case page and package limits' if r.get('package') else ''),
                        r.get('problem_category', ''), ';'.join(r.get('secondary_problem_categories') or []), RV.status(rev, t)])
    lines = ['# Outcome for every task', '',
             'The same data for all 51 public tasks is in [data/decisions.csv](data/decisions.csv), whose `decision` '
             'column uses the codes `retain-with-note`, `repair-v2` (fixed) and `exclude` (removed). These are the first audit\'s outcomes; which of them held up is in [FINDINGS.md](FINDINGS.md).', '', '| Outcome | Tasks | Meaning |', '| --- | ---: | --- |']
    lines += [f'| {LABEL[k]} | {counts[k]} | {MEANING[k]} |' for k in ORDER if counts.get(k)]
    lines += ['| **Total** | **51** | |', '', '| Task | Outcome | What we found | How much it matters |',
              '| --- | --- | --- | --- |']
    for r in sorted(rows, key=lambda r: names[r['task_id']]):
        t = r['task_id']
        lines.append(f"| [{names[t]}](cases/{t}.md) | {LABEL[r['proposed']]} | {plain[t]['headline']} | {plain[t]['effect']} |")
    (ROOT / 'first-audit/DECISIONS.md').write_text(RV.relink('\n'.join(lines) + '\n'))
    cats = {json.loads(f.read_text())['task_id']: json.loads(f.read_text())['category'] for f in (ROOT / 'tasks').glob('*.json')}
    rev = RV.load()
    idx = ['# Case pages', '', 'One page per public EdgeBench task, confirmed tasks first. The status is from the second review; each page '
           "keeps the first audit's record under its status line.", '',
           '| Task | Field | Status | In one line |', '| --- | --- | --- | --- |']
    idx += [f"| [{names[t]}]({t}.md) | {cats[t]} | {RV.LABELS[RV.status(rev, t)]} | {rev[t]['line'] if t in rev else plain[t]['headline']} |"
            for t in sorted((r['task_id'] for r in rows), key=lambda t: (RV.status(rev, t) != 'confirmed', names[t]))]
    (ROOT / 'cases' / 'INDEX.md').write_text('\n'.join(idx) + '\n')
    print(dict(counts))


if __name__ == '__main__':
    main()
