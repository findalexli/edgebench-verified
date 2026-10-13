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


def evidence_figure(n_tasks, n_formal, n_thm, n_tla, n_fix, n_fix_proved, n_cmp, n_real):
    """Figure: the four layers of evidence behind the audit, with live counts.

    n_fix is the number of fixed tasks tested side by side (OpenRCT2's instruction-only fix has nothing
    to run); the removed task's partial fix is shown separately."""
    cols = [
        ('1', 'Reproduced', 'on the original grader', [f'{n_tasks} tasks examined', 'correct, triggering and', 'wrong test submissions']),
        ('2', 'Proved formally', 'Lean 4 and TLA+', [f'{n_formal} tasks, {n_thm} theorems', f'{n_tla} model-checking runs', f'{n_fix_proved} fixes proved, in model']),
        ('3', 'Tested side by side', 'original vs fixed grader', [f'{n_fix} fixes + 1 partial fix', f'{n_cmp} comparisons', 'nearly all run 3 times']),
        ('4', 'Checked on real runs', 'a public agent run', [f'{n_real} fixed tasks: histories read', '2 regraded with both graders', '']),
    ]
    w, g = 178, 16
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 210" role="img">',
         '<title>Four layers of evidence: findings reproduced on the original grader, claims proved in Lean 4 or TLA+, '
         'fixes tested side by side against the original, and fixes checked on a real agent run.</title>',
         '<style>.ink{fill:#1b1f23} .muted{fill:#5f6368} .box{fill:#f6f7f9;stroke:#c9ced4} .hl{fill:#fff6c8;stroke:#d9c25a} '
         '.num{fill:#1a4f8b} text{font-family:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif}'
         '@media (prefers-color-scheme: dark){.ink{fill:#e2e9ed} .muted{fill:#95a6b1} .box{fill:#1b2630;stroke:#3a4a57} '
         '.hl{fill:#3a3418;stroke:#8a7a2a} .num{fill:#6cb6d3}}</style>']
    for i, (k, t, sub, lines) in enumerate(cols):
        x = i * (w + g)
        o.append(f'<rect class="{"hl" if k == "2" else "box"}" x="{x + .5}" y="0.5" width="{w - 1}" height="208" rx="8"/>')
        o.append(f'<text class="num" x="{x + 16}" y="36" font-size="26" font-weight="600">{k}</text>')
        o.append(f'<text class="ink" x="{x + 16}" y="66" font-size="16.5" font-weight="600">{t}</text>')
        o.append(f'<text class="muted" x="{x + 16}" y="87" font-size="14">{sub}</text>')
        for j, line in enumerate(lines):
            o.append(f'<text class="ink" x="{x + 16}" y="{124 + j * 24}" font-size="14">{line}</text>')
    o.append('</svg>')
    (FIG / 'evidence-layers.svg').write_text('\n'.join(o) + '\n')
    (FIG / 'evidence-layers.json').write_text(json.dumps({
        'alt': 'Four columns: reproduced on the original grader, proved formally in Lean 4 and TLA+, tested side by side, checked on real runs.',
        'caption': 'Four independent layers of evidence. Every finding\'s mechanism was demonstrated on the original grader; where a claim could '
                   'be stated precisely it was also proved in Lean 4 or model-checked in TLA+; the fixes were tested side by side, almost every comparison three times '
                   '(exceptions in Section 2); '
                   'and a real agent run was checked on seven fixed tasks, two of them regraded with both graders.'}) + '\n')


def comparison_counts():
    """Side-by-side comparisons, counted from data/paired-repeatability.csv.

    A graded comparison is an executed arm (not a derived row such as Treant's score cap) whose role is
    not 'setup' (a run that prepares an input, such as Borden's hidden true source). 'graded3' counts the
    graded comparisons with three or more runs. 'not_run' counts rows of data/paired-results.csv that
    have no executed arm at all (OpenRCT2's instruction-only fix)."""
    rep = list(csv.DictReader(open(ROOT / 'data' / 'paired-repeatability.csv')))
    runs, role, derived = Counter(), {}, {}
    for x in rep:
        k = (x['task_id'], x['arm'])
        runs[k] += 1
        role[k] = x['role']
        derived[k] = derived.get(k, True) and x['v1_result'] == 'derived (no execution)'
    executed = [k for k in runs if not derived[k]]
    graded = [k for k in executed if role[k] != 'setup']
    pr = list(csv.DictReader(open(ROOT / 'data' / 'paired-results.csv')))
    return {'arms': {k: runs[k] for k in executed}, 'executed': len(executed), 'graded': len(graded),
            'graded3': sum(runs[k] >= 3 for k in graded), 'executed3': sum(runs[k] >= 3 for k in executed),
            'setup': len(executed) - len(graded), 'derived': sum(derived.values()),
            'not_run': len(pr) - len(runs),
            'tasks': len({t for t, _ in graded}) - 1}   # minus the removed task's partial fix


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
    cc = comparison_counts()
    _arms = cc['arms']
    n_cmp, n_cmp3, n_cmp_tasks = cc['graded'], cc['graded3'], cc['tasks']
    out = (out.replace('{{n_cmp}}', str(n_cmp)).replace('{{n_cmp3}}', str(n_cmp3)).replace('{{n_cmp_tasks}}', str(n_cmp_tasks))
           .replace('{{n_cmp_setup}}', str(cc['setup'])).replace('{{n_cmp_derived}}', str(cc['derived']))
           .replace('{{n_cmp_noexec}}', str(cc['not_run'])))
    out = out.replace('{{n_problem}}', str(counts.get('repair-v2', 0) + counts.get('exclude', 0)))

    frm0 = json.loads((ROOT / 'evidence' / 'formal' / 'summary.json').read_text())['rows']
    leans0 = [p for p in (ROOT / 'evidence/formal/lean/ebv/Ebv').glob('*.lean') if p.with_suffix('.out').exists()]
    thm0 = sum(len({t for t in re.findall(r"^'[^']+' (?:depends on axioms: \[[^\]]*\]|does not depend on any axioms)", p.with_suffix('.out').read_text(), re.M) if 'sorryAx' not in t}) for p in leans0)
    evidence_figure(51, len(frm0), thm0, len(list((ROOT / 'evidence/formal/tla').glob('*/*.cfg'))), n_cmp_tasks,
                    sum(r['covers'] == 'fix' and r['result'] in ('proved', 'model-checked') for r in frm0), n_cmp, 7)
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
    effects = json.loads((ROOT / 'evidence/impact/effects.json').read_text())
    trs = ''.join(
        f"<tr><td>{r['model']}</td><td class=\"n\">{float(r['published_mean']):.1f}</td>"
        f"<td class=\"n\"><b>{float(r['worst_case_low']):.1f}–{float(r['worst_case_high']):.1f}</b></td>"
        f"<td class=\"n\">{float(r['bounded_low']):.1f}–{float(r['bounded_high']):.1f}</td>"
        f"<td class=\"n\">{float(r['exact_adjusted_mean']):.1f}</td></tr>"
        for r in imp)
    wide_down = max(float(r['exact_adjusted_mean']) - float(r['worst_case_low']) for r in imp)
    wide_up = max(float(r['worst_case_high']) - float(r['exact_adjusted_mean']) for r in imp)
    ex = {r['model']: float(r['exact_adjusted_mean']) for r in imp}
    shifts = [float(r['exact_adjusted_mean']) - float(r['recomputed_mean']) for r in imp]
    lo = {r['model']: float(r['exact_adjusted_mean']) - float(r['bounded_low']) for r in imp}
    hi = {r['model']: float(r['bounded_high']) - float(r['exact_adjusted_mean']) for r in imp}
    order = sorted(ex, key=lambda m: -ex[m])
    fragile = [(a, b) for a, b in zip(order, order[1:]) if lo[a] + hi[b] >= ex[a] - ex[b]]
    import estimate_impact as EI
    lb = EI.parse_leaderboard()
    names_ = task_names()

    def rests_on(a, b):
        # The single bounded task that contributes most to the swing, and the swing without it.
        ua, da = EI.bounded_parts(EI.adjusted(lb, a), effects)
        ub, db = EI.bounded_parts(EI.adjusted(lb, b), effects)
        na = sum(v is not None for v in EI.adjusted(lb, a).values())
        nb = sum(v is not None for v in EI.adjusted(lb, b).values())
        parts = {t: da.get(t, 0) / na + ub.get(t, 0) / nb for t in set(da) | set(ub)}
        top = max(parts, key=parts.get)
        need = (ex[a] - ex[b] - (lo[a] + hi[b] - parts[top])) * nb
        return (f' This rests mainly on {names_[top]}, where {b} can gain up to {ub.get(top, 0):.1f} points: without it '
                f'the largest swing is {lo[a] + hi[b] - parts[top]:.1f} points, less than the gap, so {b} would need at least '
                f'{need:.1f} of those points. It also assumes every other bounded effect at its extreme at once.'
                if lo[a] + hi[b] - parts[top] < ex[a] - ex[b] and da.get(top, 0) == 0 else '')
    if fragile:
        ftxt = ' '.join(f'<mark>That is enough to reverse {a} and {b}: their gap is {ex[a] - ex[b]:.1f} points, and '
                        f'these fixes alone could move it by up to {lo[a] + hi[b]:.1f}.</mark> The 51 public tasks therefore '
                        f'do not establish which of the two is ahead.' + rests_on(a, b) for a, b in fragile)
    else:
        ftxt = 'That is not enough to reverse any two neighbouring models.'
    out = (out.replace('{{impact_rows}}', trs).replace('{{shift_lo}}', f'{min(shifts):.1f}')
           .replace('{{shift_hi}}', f'{max(shifts):.1f}').replace('{{fragile_text}}', ftxt)
           .replace('{{rank_text}}', ('<mark>Even the effects we can bound are enough that the public tasks do not establish the order of '
                                      + ' and '.join(f'{a} and {b}' for a, b in fragile) + '.</mark>') if fragile else
                    '<mark>The fixes whose effect we can bound do not reverse any neighbouring pair of models; whether the ranking '
                    'changes depends on the fixes whose effect size is unknown.</mark>')
           .replace('{{n_bound}}', str(sum(e['kind'] == 'bounded' for e in effects.values())))
           .replace('{{open_down}}', f"{max(float(r['bounded_low']) - float(r['worst_case_low']) for r in imp):.1f}")
           .replace('{{open_up}}', f"{max(float(r['worst_case_high']) - float(r['bounded_high']) for r in imp):.1f}")
           .replace('{{n_open}}', str(sum(e['kind'] == 'open' for e in effects.values()) - 1))
           .replace('{{bound_down}}', f'{max(lo.values()):.1f}').replace('{{bound_up}}', f'{max(hi.values()):.1f}'))
    dec = {m: EI.decomposition(lb, m) for m in EI.MODELS}
    for k in ('dabic', 'treant', 'borden'):
        vals = [abs(d[k]) for d in dec.values()]
        fmt = '{:.2f}' if k == 'borden' else '{:.1f}'
        out = out.replace('{{' + k + '_lo}}', fmt.format(min(vals))).replace('{{' + k + '_hi}}', fmt.format(max(vals)))
    pr = list(csv.DictReader(open(ROOT / 'data/paired-results.csv')))
    out = (out.replace('{{paired_rows}}', str(len(pr))).replace('{{paired_tasks}}', str(len({r['task_id'] for r in pr})))
           .replace('{{paired_setup}}', str(sum(r['role'] == 'setup' for r in pr))))
    frm = json.loads((ROOT / 'evidence' / 'formal' / 'summary.json').read_text())['rows']
    names = task_names()
    label = {'fix': 'the fix', 'finding': 'the finding', 'note': 'the note', 'numbers': 'published numbers'}
    frows = ''.join(f"<tr><td>{html.escape(names[r['task']])}</td><td>{r['tool'].replace(' ', '&nbsp;')}</td>"
                    f"<td>{r['result'].capitalize()}<br><span style=\"color:var(--muted)\">{label[r['covers']]}</span></td>"
                    f"<td>{html.escape(r['what'])}</td><td>{html.escape(r['limit'])}</td></tr>" for r in frm)
    leans = [p for p in (ROOT / 'evidence/formal/lean/ebv/Ebv').glob('*.lean') if p.with_suffix('.out').exists()]
    thms = sum(len({t for t in re.findall(r"^'[^']+' (?:depends on axioms: \[[^\]]*\]|does not depend on any axioms)", p.with_suffix('.out').read_text(), re.M) if 'sorryAx' not in t}) for p in leans)
    cfgs = list((ROOT / 'evidence/formal/tla').glob('*/*.cfg'))
    out = (out.replace('{{formal_rows}}', frows).replace('{{formal_tasks}}', str(len(frm)))
           .replace('{{lean_files}}', str(len(leans))).replace('{{lean_thms}}', str(thms))
           .replace('{{tla_runs}}', str(len(cfgs))).replace('{{tla_models}}', str(len({c.parent for c in cfgs})))
           .replace('{{fix_proved}}', str(sum(r['covers'] == 'fix' and r['result'] in ('proved', 'model-checked') for r in frm)))
           .replace('{{fix_partly}}', str(sum(r['covers'] == 'fix' and r['result'].startswith('partly') for r in frm)))
           .replace('{{formal_checks}}', str(len(leans) + len(cfgs)))
           .replace('{{wide_down}}', f'{wide_down:.1f}').replace('{{wide_up}}', f'{wide_up:.1f}'))
    fby = {r['task']: r for r in frm}
    cov = {'fix': 'fix proved correct', 'finding': 'finding proved', 'note': 'note proved', 'numbers': 'published numbers proved'}

    def verif(m):
        t = m.group(1)
        parts = ['<b>Evidence:</b> reproduced on the original grader']
        r = fby.get(t)
        if r:
            what = cov[r['covers']].replace('proved', r['result'])
            parts.append(f"{r['tool'].replace(' ', '&nbsp;')}: {what}")
        runs = sorted({v for (tt, _), v in _arms.items() if tt == t})
        if t == 'dabic_gravity_inversion':
            parts.append('partial fix tested side by side, three runs; task removed')
        elif not runs:
            parts.append('fix changes instructions only; nothing to run')
        elif runs == [3] or min(runs) >= 3:
            parts.append('fix tested side by side, three runs')
        else:
            parts.append('fix tested side by side, three runs (one comparison once)')
        return ' · '.join(parts)
    out = re.sub(r'\{\{verif:(\w+)\}\}', verif, out)
    left = re.findall(r'\{\{[\w|:-]+\}\}', out)
    assert not left, left
    (ROOT / 'site').mkdir(exist_ok=True)
    (ROOT / 'site' / 'index.html').write_text(out)
    print('wrote site/index.html', len(out) // 1024, 'KB', n, 'figures', dict(counts))


if __name__ == '__main__':
    main()
