#!/usr/bin/env python3
"""Build the single-file EdgeBench Verified site from decisions.json and release/cases/*.md."""
import json
import re
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
            # the figure is shown in the plain summary above the technical case; drop the duplicate
            cases[f.stem] = re.sub(r'\n!\[[^\]]*\]\(figures/[^)]+\)\n\n\*[^\n]*\*\n', '\n', f.read_text())
    rows = []
    plain = json.loads((ROOT / 'cases' / 'plain.json').read_text())
    for r in sorted(decisions, key=lambda r: meta[r['task_id']]['name']):
        t = r['task_id']
        fig = ROOT / 'cases' / 'figures' / f'{t}.svg'
        extra = {}
        if fig.exists():
            svg = fig.read_text()
            svg = svg[svg.index('<svg'):]
            cap = json.loads((ROOT / 'cases' / 'figures' / f'{t}.json').read_text())
            extra = {'figure': svg, 'figcap': cap['caption']}
        rows.append({**r, **meta[t], 'plain': plain[t], **extra})
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
    ex = {r['model']: float(r['exact_adjusted_mean']) for r in imp}
    shifts = [float(r['exact_adjusted_mean']) - float(r['recomputed_mean']) for r in imp]
    lo = {r['model']: float(r['exact_adjusted_mean']) - float(r['bounded_low']) for r in imp}
    hi = {r['model']: float(r['bounded_high']) - float(r['exact_adjusted_mean']) for r in imp}
    order = sorted(ex, key=lambda m: -ex[m])
    fragile = [(a, b) for a, b in zip(order, order[1:]) if lo[a] + hi[b] >= ex[a] - ex[b]]
    if fragile:
        ftxt = ' '.join(f'This is enough to change the order of {a} and {b}: their gap is {ex[a] - ex[b]:.1f} points, '
                        f'and these fixes could move it by up to {lo[a] + hi[b]:.1f}. The public tasks alone therefore do not '
                        f'show which of the two is ahead.' for a, b in fragile)
    else:
        ftxt = 'No two neighbouring models can change places within this range.'
    out = (out.replace('{{impact_rows}}', trs).replace('{{shift_lo}}', f'{min(shifts):.1f}')
           .replace('{{shift_hi}}', f'{max(shifts):.1f}').replace('{{fragile_text}}', ftxt))
    assert '{{' not in out, out[out.index('{{'):out.index('{{') + 40]
    (ROOT / 'site').mkdir(exist_ok=True)
    (ROOT / 'site' / 'index.html').write_text(out)
    print('wrote site/index.html', len(out) // 1024, 'KB', dict(counts))


if __name__ == '__main__':
    main()
