#!/usr/bin/env python3
"""Build the single-file EdgeBench Verified site from data/decisions.json, cases/*.md, cases/plain.json and cases/figures/."""
import csv
import html
import json
import sys
import re
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from names import names as task_names  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / 'cases' / 'figures'
# The site is light-only: drop the figures' dark-mode rules (they exist for GitHub's dark theme).
DARK = re.compile(r'@media \(prefers-color-scheme: ?dark\)\s*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}')


def svg(name):
    s = (FIG / f'{name}.svg').read_text()
    return DARK.sub('', s[s.index('<svg'):])


def caption(name):
    return json.loads((FIG / f'{name}.json').read_text())['caption']


def main():
    decisions = json.loads((ROOT / 'data/decisions.json').read_text())
    meta = {}
    for f in (ROOT / 'tasks').glob('*.json'):
        t = json.loads(f.read_text())
        meta[t['task_id']] = {'name': task_names()[t['task_id']], 'category': t['category']}
    cases = {}
    for f in (ROOT / 'cases').glob('*.md'):
        if f.stem != 'INDEX':
            # the figure is shown in the plain summary above the technical case; drop the duplicate
            cases[f.stem] = re.sub(r'\n!\[[^\]]*\]\(figures/[^)]+\)\n\n\*[^\n]*\*\n', '\n', f.read_text())
    plain = json.loads((ROOT / 'cases' / 'plain.json').read_text())
    formal_by_task = {r['task']: r for r in json.loads((ROOT / 'evidence/formal/summary.json').read_text())['rows']}
    rows = []
    for r in sorted(decisions, key=lambda r: meta[r['task_id']]['name']):
        t = r['task_id']
        extra = {'figure': svg(t), 'figcap': caption(t)} if (FIG / f'{t}.svg').exists() else {}
        fr = formal_by_task.get(t)
        if fr:
            extra['formal'] = f"{fr['result'].capitalize()} in {fr['tool']}. {fr['what']} Limit: {fr['limit']}."
        rows.append({**r, **meta[t], 'plain': plain[t], **extra})
    assert len(rows) == 51 and len(cases) == 51
    counts = Counter(r['proposed'] for r in rows)
    data = {'rows': rows, 'cases': cases, 'counts': counts}
    out = (ROOT / 'tools' / 'site_template.html').read_text()
    out = out.replace('/*__DATA__*/null', json.dumps(data, ensure_ascii=False).replace('</', '<\\/'))
    for k in ('retain', 'retain-with-note', 'repair-v2', 'exclude'):
        out = out.replace('{{' + k + '}}', str(counts.get(k, 0)))

    # Numbered figures, in reading order: {{fig:<name>}} or {{fig:<name>|<task to open>}}.
    n = 0

    def figure(m):
        nonlocal n
        n += 1
        name, _, link = m.group(1).partition('|')
        more = (f' <a href="#{link}" class="case-link" data-case="{link}">Read the case</a>' if link else '')
        return (f'<figure class="fig" id="fig-{name}"><div class="scroll">{svg(name)}</div><figcaption><b>Figure {n}.</b> '
                f'{html.escape(caption(name))}{more}</figcaption></figure>')
    out = re.sub(r'\{\{fig:([\w|-]+)\}\}', figure, out)

    imp = list(csv.DictReader(open(ROOT / 'data/impact.csv')))
    trs = ''.join(
        f"<tr><td>{r['model']}</td><td class=\"n\">{float(r['published_mean']):.1f}</td>"
        f"<td class=\"n\"><b>{float(r['exact_adjusted_mean']):.1f}</b></td>"
        f"<td class=\"n\">{float(r['bounded_low']):.1f}–{float(r['bounded_high']):.1f}</td>"
        f"<td class=\"n\">{float(r['worst_case_low']):.1f}–{float(r['worst_case_high']):.1f}</td></tr>"
        for r in imp)
    ex = {r['model']: float(r['exact_adjusted_mean']) for r in imp}
    shifts = [float(r['exact_adjusted_mean']) - float(r['recomputed_mean']) for r in imp]
    lo = {r['model']: float(r['exact_adjusted_mean']) - float(r['bounded_low']) for r in imp}
    hi = {r['model']: float(r['bounded_high']) - float(r['exact_adjusted_mean']) for r in imp}
    order = sorted(ex, key=lambda m: -ex[m])
    fragile = [(a, b) for a, b in zip(order, order[1:]) if lo[a] + hi[b] >= ex[a] - ex[b]]
    if fragile:
        ftxt = ' '.join(f'<mark>That is enough to reverse {a} and {b}: their gap is {ex[a] - ex[b]:.1f} points, and '
                        f'these fixes alone could move it by up to {lo[a] + hi[b]:.1f}.</mark> The 51 public tasks therefore '
                        f'do not establish which of the two is ahead.' for a, b in fragile)
    else:
        ftxt = 'No two neighbouring models can change places within this range.'
    out = (out.replace('{{impact_rows}}', trs).replace('{{shift_lo}}', f'{min(shifts):.1f}')
           .replace('{{shift_hi}}', f'{max(shifts):.1f}').replace('{{fragile_text}}', ftxt)
           .replace('{{bound_down}}', f'{max(lo.values()):.1f}').replace('{{bound_up}}', f'{max(hi.values()):.1f}'))
    frm = json.loads((ROOT / 'evidence' / 'formal' / 'summary.json').read_text())['rows']
    names = task_names()
    label = {'fix': 'the fix', 'finding': 'the finding', 'note': 'the note', 'numbers': 'published numbers'}
    frows = ''.join(f"<tr><td>{html.escape(names[r['task']])}</td><td>{r['tool'].replace(' ', '&nbsp;')}</td>"
                    f"<td>{r['result'].capitalize()}<br><span style=\"color:var(--muted)\">{label[r['covers']]}</span></td>"
                    f"<td>{html.escape(r['what'])}</td><td>{html.escape(r['limit'])}</td></tr>" for r in frm)
    leans = [p for p in (ROOT / 'evidence/formal/lean/ebv/Ebv').glob('*.lean') if p.with_suffix('.out').exists()]
    thms = sum(len(set(re.findall(r"^'[^']+' (?:depends on axioms|does not depend on any axioms)", p.with_suffix('.out').read_text(), re.M))) for p in leans)
    cfgs = list((ROOT / 'evidence/formal/tla').glob('*/*.cfg'))
    out = (out.replace('{{formal_rows}}', frows).replace('{{formal_tasks}}', str(len(frm)))
           .replace('{{lean_files}}', str(len(leans))).replace('{{lean_thms}}', str(thms))
           .replace('{{tla_runs}}', str(len(cfgs))).replace('{{tla_models}}', str(len({c.parent for c in cfgs})))
           .replace('{{fix_proved}}', str(sum(r['covers'] == 'fix' and r['result'] == 'proved' for r in frm))))
    left = re.findall(r'\{\{[\w|:-]+\}\}', out)
    assert not left, left
    (ROOT / 'site').mkdir(exist_ok=True)
    (ROOT / 'site' / 'index.html').write_text(out)
    print('wrote site/index.html', len(out) // 1024, 'KB', n, 'figures', dict(counts))


if __name__ == '__main__':
    main()
