#!/usr/bin/env python3
"""Build the single-file EdgeBench Verified site from decisions.json and release/cases/*.md."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT


def main():
    decisions = json.loads((ROOT / 'decisions.json').read_text())
    meta = {}
    for f in (REPO / 'tasks').glob('*.json'):
        t = json.loads(f.read_text())
        meta[t['task_id']] = {'name': t['name'], 'category': t['category']}
    cases = {}
    for f in (ROOT / 'cases').glob('*.md'):
        if f.stem != 'INDEX':
            cases[f.stem] = f.read_text()
    rows = []
    for r in sorted(decisions, key=lambda r: meta[r['task_id']]['name']):
        rows.append({**r, **meta[r['task_id']]})
    assert len(rows) == 51 and len(cases) == 51
    counts = Counter(r['proposed'] for r in rows)
    data = {'rows': rows, 'cases': cases, 'counts': counts}
    tpl = (ROOT / 'tools' / 'site_template.html').read_text()
    out = tpl.replace('/*__DATA__*/null', json.dumps(data, ensure_ascii=False).replace('</', '<\\/'))
    for k in ('retain', 'retain-with-note', 'repair-v2', 'exclude'):
        out = out.replace('{{' + k + '}}', str(counts.get(k, 0)))
    (ROOT / 'site').mkdir(exist_ok=True)
    (ROOT / 'site' / 'index.html').write_text(out)
    print('wrote site/index.html', len(out) // 1024, 'KB', dict(counts))


if __name__ == '__main__':
    main()
