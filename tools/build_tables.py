#!/usr/bin/env python3
"""Generate the release decision table and CSV from decisions.json (single source of counts)."""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORDER = ['retain', 'retain-with-note', 'repair-v2', 'exclude', 'pending']
LABEL = {'retain': 'Retain', 'retain-with-note': 'Retain with note',
         'repair-v2': 'Repair (v2)', 'exclude': 'Exclude', 'pending': 'Pending'}


def main():
    rows = sorted(json.loads((ROOT / 'decisions.json').read_text()), key=lambda r: r['task_id'])
    assert len(rows) == 51, len(rows)
    counts = Counter(r['proposed'] for r in rows)
    assert sum(counts.values()) == 51
    with (ROOT / 'decisions.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['task_id', 'decision', 'finding', 'max_effect', 'repair_result', 'package', 'status'])
        for r in rows:
            w.writerow([r['task_id'], r['proposed'], r['finding'], r.get('max_effect', ''),
                        r.get('repair', ''), r.get('package', ''), r['status']])
    lines = ['| Decision | Tasks |', '| --- | ---: |']
    lines += [f'| {LABEL[k]} | {counts.get(k, 0)} |' for k in ORDER if counts.get(k)]
    lines += ['| **Total** | **51** |', '', '| Task | Decision | What we found | Max effect | Repair result |',
              '| --- | --- | --- | --- | --- |']
    for r in rows:
        rep = r.get('repair', '—' if r['proposed'] != 'repair-v2' else 'in progress')
        lines.append(f"| `{r['task_id']}` | {LABEL[r['proposed']]} | {r['finding']} | "
                     f"{r.get('max_effect', '')} | {rep} |")
    (ROOT / 'DECISIONS.md').write_text('\n'.join(lines) + '\n')
    print(dict(counts))


if __name__ == '__main__':
    main()
