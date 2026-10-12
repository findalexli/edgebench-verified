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
    import csv
    imp = list(csv.DictReader(open(ROOT / 'impact.csv')))
    trs = ''.join(
        f"<tr><td>{r['model']}</td><td class=\"n\">{float(r['published_mean']):.1f}</td>"
        f"<td class=\"n\"><b>{float(r['exact_adjusted_mean']):.1f}</b></td>"
        f"<td class=\"n\">{float(r['bounded_low']):.1f} – {float(r['bounded_high']):.1f}</td>"
        f"<td class=\"n\">{float(r['worst_case_low']):.1f} – {float(r['worst_case_high']):.1f}</td></tr>"
        for r in imp)
    note = (ROOT / 'evidence' / 'impact' / 'site-note.txt').read_text().strip()
    out = out.replace('{{impact_rows}}', trs).replace('{{impact_note}}', note)
    (ROOT / 'site').mkdir(exist_ok=True)
    (ROOT / 'site' / 'index.html').write_text(out)
    print('wrote site/index.html', len(out) // 1024, 'KB', dict(counts))


if __name__ == '__main__':
    main()
