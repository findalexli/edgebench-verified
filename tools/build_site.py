#!/usr/bin/env python3
"""Build the EdgeBench Verified website into site/ from the repository's data.

Pages (English at the site root; each other language under site/<lang>/):
  index.html             Overview          prose: tools/site/<lang>/overview.html
  tasks/index.html       all 51 tasks      generated from data/decisions.json and cases/plain*.json
  tasks/<task_id>.html   one per task      cases/<id>.md (or cases/<lang>/<id>.md) and tasks/<id>.json
  method.html            How we verified   prose: tools/site/<lang>/method.html
  leaderboard.html       Leaderboard       prose: tools/site/<lang>/leaderboard.html
plus site/assets/site.css (from tools/site/site.css) and site/figures/ (figures used as images).

UI strings and generated prose come from tools/i18n/<lang>.json, falling back to tools/i18n/en.json.
A page whose own text falls back to English shows a "translation pending" note. tools/i18n/README.md
lists the files a translator writes.

Markdown is rendered here, server-side, by tools/mdrender.py; the pages load no JavaScript library.
Template syntax: {{name}} data values, {{t:key}} strings, {{task:<id>|text}} task links,
{{fig:<name>}} / {{fig:<name>|<task>}} numbered figures, {{verif:<id>}} evidence lines,
{{root}} the language's site root, {{site_root}} the real site root (data/, assets/).
"""
import csv
import html
import json
import math
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from names import names as task_names  # noqa: E402
import mdrender  # noqa: E402
import categories as PC  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
SRC = ROOT / 'tools' / 'site'
I18N = ROOT / 'tools' / 'i18n'
FIG = ROOT / 'cases' / 'figures'
REPO = 'https://github.com/findalexli/edgebench-verified'
BLOB = REPO + '/blob/main/'
TREE = REPO + '/tree/main/'
SITE_URL = 'http://lishengzhi.com/edgebench-verified/'
# Languages. 'en' is the source; every other language is built under site/<code>/ from its own sources,
# falling back to English with a visible note. Set BUILD_ZH = False to build English only and hide the
# language switch.
BUILD_ZH = True
LANGS = {'en': {'html_lang': 'en', 'prefix': ''}, 'zh': {'html_lang': 'zh-CN', 'prefix': 'zh/'}}
# Chinese pages also load CJK web fonts (Google Fonts serves them in unicode-range slices, so a page
# downloads only the glyphs it uses); site.css puts them in the font stack for :lang(zh).
ZH_FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;600'
            '&family=Noto+Serif+SC:wght@400;600;700&display=swap">')
ORDER = ['repair-v2', 'exclude', 'retain-with-note', 'retain']
# Shown (and written to APPLYING-FIXES.md and data/decisions.csv) for a repair without a recorded validation status.
VALIDATION_DEFAULT = 'Historical paired scope only; see the case page and package limits'
TABS = [('overview', 'index.html'), ('tasks', 'tasks/index.html'), ('method', 'method.html'),
        ('leaderboard', 'leaderboard.html')]
# Grader CPUs and memory in EdgeBench's leaderboard settings (quoted in
# evidence/impact/edgebench-leaderboard-config.md): 4 CPUs / 8 GB by default, the Lean override 8 / 16 GB,
# and SMT Solver 16 / 16 GB. The build checks these ids against that page.
LEAN_8CPU = ['carleson_formalization', 'combinatorial_games_formalization', 'flt_regular_formalization',
             'lean_analysis_proofs', 'new_foundations_consistency', 'pfr_formalization',
             'sphere_eversion_formalization']
SMT_16CPU = ['smt_solver']
CONFIG_MD = 'evidence/impact/edgebench-leaderboard-config.md'
# The site is light-only: drop the figures' dark-mode rules (they exist for GitHub's dark theme).
DARK = re.compile(r'@media \(prefers-color-scheme: ?dark\)\s*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}')
PLACEHOLDER = re.compile(r'\{\{[\w|:-]+\}\}')


def svg(name, lang='en'):
    p = FIG / lang / f'{name}.svg' if lang != 'en' and (FIG / lang / f'{name}.svg').exists() else FIG / f'{name}.svg'
    s = p.read_text()
    return DARK.sub('', s[s.index('<svg'):])


def caption(name):
    return json.loads((FIG / f'{name}.json').read_text())['caption']


def evidence_figure(n_tasks, n_formal, n_thm, n_tla, n_fix, n_fix_proved, n_cmp, n_real):
    """Figure: the four layers of evidence behind the audit, with live counts.

    n_fix is the number of fixed tasks tested side by side (OpenRCT2's instruction-only fix has nothing
    to run); the removed task's partial fix is shown separately."""
    cols = [
        ('1', 'Examined', 'original code and images', [f'{n_tasks} tasks examined', 'source, component and', 'native evidence']),
        ('2', 'Proved formally', 'Lean 4 and TLA+', [f'{n_formal} tasks, {n_thm} theorems', f'{n_tla} model-checking runs', f'{n_fix_proved} repair models checked']),
        ('3', 'Historical pairs', 'components and graders', [f'{n_fix} fixes + 1 partial fix', f'{n_cmp} comparisons', 'nearly all run 3 times']),
        ('4', 'Checked on real runs', 'a public agent run', [f'{n_real} fixed tasks covered;', '7 regraded with', 'both graders;', 'Lean computed']),
    ]
    w, g = 178, 16
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 210" role="img">',
         '<title>Four evidence layers with different scope: tasks examined in the original code and images, '
         'models proved in Lean 4 or checked in TLA+, historical paired comparisons of saved versions, '
         'and fixed tasks covered by one public agent run.</title>',
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
        'alt': 'Four columns: examined in the original code and images, proved formally in Lean 4 and TLA+, historical paired comparisons, checked on real runs.',
        'caption': 'Four evidence layers with different scope. Historical source/helper controls, native runs and formal models are not interchangeable or independently certified reproductions. Paired comparisons refer to the saved versions; they do not certify newer candidates. The real-agent record covers nine tasks, with seven regraded under both graders and Lean Analysis computed from saved verdicts.'}) + '\n')


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
    return {'arms': {k: runs[k] for k in graded}, 'executed': len(executed), 'graded': len(graded),
            'graded3': sum(runs[k] >= 3 for k in graded), 'executed3': sum(runs[k] >= 3 for k in executed),
            'setup': len(executed) - len(graded), 'derived': sum(derived.values()),
            'not_run': len(pr) - len(runs),
            'tasks': len({t for t, _ in graded}) - 1}   # minus the removed task's partial fix


# ---------------------------------------------------------------- strings and per-language sources

class Strings:
    """Look up UI strings for one language, falling back to English and remembering what fell back."""

    def __init__(self, lang):
        self.lang = lang
        self.en = json.loads((I18N / 'en.json').read_text())
        p = I18N / f'{lang}.json'
        self.own = self.en if lang == 'en' else (json.loads(p.read_text()) if p.exists() else {})
        self.missing = set()

    def __call__(self, key, **kw):
        if key in self.own:
            s = self.own[key]
        else:
            if key not in self.en:
                raise KeyError(f'string {key!r} missing from tools/i18n/en.json')
            s = self.en[key]
            if self.lang != 'en' and s:
                self.missing.add(key)
        return fill(s, kw)

    def opt(self, key, default):
        """An optional string (for example a category name): the default is the English text."""
        if key in self.own:
            return self.own[key]
        if self.lang != 'en':
            self.missing.add(key)
        return default


def fill(s, kw):
    """Replace {name} for the given names only, so other braces in a string are left alone."""
    if not kw:
        return s
    return re.sub(r'\{(\w+)\}', lambda m: str(kw[m.group(1)]) if m.group(1) in kw else m.group(0), s)


class Lang:
    def __init__(self, code):
        self.code = code
        self.meta = LANGS[code]
        self.t = Strings(code)
        self.major = False      # the page's own text fell back to English
        pending_path = I18N / f'pending-{code}.json'
        self.pending = json.loads(pending_path.read_text()) if code != 'en' and pending_path.exists() else {}
        self.extra = {}
        for name in ('figures', 'formal', 'validation'):
            p = I18N / f'{name}.{code}.json'
            self.extra[name] = json.loads(p.read_text()) if code != 'en' and p.exists() else {}

    def reset(self):
        self.t.missing = set()
        self.major = False

    def source(self, en_path, own_path):
        """Read a per-language source, falling back to English (and marking the page pending)."""
        stale = en_path.relative_to(ROOT).as_posix() in self.pending.get('sources', [])
        if self.code != 'en' and own_path.exists() and not stale:
            return own_path.read_text()
        if self.code != 'en':
            self.major = True
        return en_path.read_text()

    def template(self, page):
        return self.source(SRC / 'en' / f'{page}.html', SRC / self.code / f'{page}.html')

    def plain(self, plain_en):
        p = ROOT / 'cases' / f'plain.{self.code}.json'
        own = json.loads(p.read_text()) if self.code != 'en' and p.exists() else {}
        for tid in self.pending.get('plain', []):
            own.pop(tid, None)
        return own, plain_en

    def formal(self, tid):
        translated = self.extra['formal'].get(tid, {})
        if tid in self.pending.get('formal', []):
            translated = {}
        if self.code != 'en' and not translated:
            self.t.missing.add(f'formal:{tid}')
        return translated

    def validation(self, tid, english):
        """Translated validation status, used only while its recorded English source is current."""
        own = self.extra['validation'].get(tid, {})
        if self.code == 'en':
            return english
        if own.get('en') == english and own.get('text'):
            return own['text']
        self.t.missing.add(f'validation:{tid}')
        return english

    def caption(self, name):
        c = self.extra['figures'].get(name)
        if isinstance(c, dict):     # {"caption": ..., "alt": ...}; the alt text is used on the case pages
            c = c.get('caption')
        if c:
            return c
        if self.code != 'en':
            self.t.missing.add(f'figure:{name}')
        return caption(name)


def esc(s):
    return html.escape(str(s), quote=True)


def plain_html(s):
    """A plain-words summary field: escaped text, with `code` spans shown as code."""
    return re.sub(r'`([^`]+)`', r'<code>\1</code>', esc(s))


def nobraces(s):
    """Content inserted into a page must not look like a template placeholder."""
    return s.replace('{{', '&#123;&#123;').replace('}}', '&#125;&#125;')


def fmtnum(v):
    if isinstance(v, bool) or v is None:
        return str(v)
    if isinstance(v, int) or (isinstance(v, float) and v.is_integer() and abs(v) < 1e15):
        return f'{int(v):,}'
    s = f'{v:,}'
    return s


def plural_time(t, secs):
    if secs % 3600 == 0:
        h = secs // 3600
        return t('task.grading.hour') if h == 1 else t('task.grading.hours', n=h)
    if secs % 60 == 0:
        return t('task.grading.minutes', n=secs // 60)
    return t('task.grading.minutes', n=f'{secs / 60:.1f}')


# ---------------------------------------------------------------- data shared by all languages

def load_data():
    decisions = json.loads((ROOT / 'data/decisions.json').read_text())
    names = task_names()
    tasks = {}
    for f in (ROOT / 'tasks').glob('*.json'):
        t = json.loads(f.read_text())
        tasks[t['task_id']] = t
    plain = json.loads((ROOT / 'cases' / 'plain.json').read_text())
    frm = json.loads((ROOT / 'evidence' / 'formal' / 'summary.json').read_text())['rows']
    rows = []
    for r in decisions:
        t = r['task_id']
        rows.append({**r, 'name': names[t], 'category': tasks[t]['category']})
    rows.sort(key=lambda r: (ORDER.index(r['proposed']), r['name'].lower()))
    assert len(rows) == 51 and set(tasks) == {r['task_id'] for r in rows} and set(plain) == set(tasks)
    config = (ROOT / CONFIG_MD).read_text()
    for t in LEAN_8CPU + SMT_16CPU:
        assert t in config and t in tasks, f'{t} not in {CONFIG_MD}'
    bad = PC.validate(decisions)
    assert not bad, bad
    return {'decisions': decisions, 'rows': rows, 'tasks': tasks, 'names': names, 'plain': plain,
            'pcat': PC.by_primary(decisions), 'pcat2': PC.by_secondary(decisions),
            'formal': frm, 'formal_by': {x['task']: x for x in frm},
            'counts': Counter(r['proposed'] for r in rows)}


def numbers(D):
    """Every number placeholder of the prose templates, computed from the data (language-independent)."""
    counts = D['counts']
    v = {k: str(counts.get(k, 0)) for k in ORDER}
    cc = comparison_counts()
    v.update(n_cmp=cc['graded'], n_cmp3=cc['graded3'], n_cmp_once=cc['graded'] - cc['graded3'], n_cmp_tasks=cc['tasks'], n_cmp_setup=cc['setup'],
             n_cmp_derived=cc['derived'], n_cmp_noexec=cc['not_run'],
             n_problem=counts.get('repair-v2', 0) + counts.get('exclude', 0))
    assert sum(len(x) for x in D['pcat'].values()) == int(v['n_problem']), 'problem categories do not cover every problem task'
    v.update({f'pcat_n_{k}': len(D['pcat'][k]) for k in PC.KEYS})
    frm = D['formal']
    leans = [p for p in (ROOT / 'evidence/formal/lean/ebv/Ebv').glob('*.lean') if p.with_suffix('.out').exists()]
    thms = sum(len({t for t in re.findall(r"^'[^']+' (?:depends on axioms: \[[^\]]*\]|does not depend on any axioms)",
                                          p.with_suffix('.out').read_text(), re.M) if 'sorryAx' not in t}) for p in leans)
    cfgs = list((ROOT / 'evidence/formal/tla').glob('*/*.cfg'))
    fix_proved = sum(r['covers'] == 'fix' and r['result'] in ('proved', 'model-checked') for r in frm)
    evidence_figure(51, len(frm), thms, len(cfgs), cc['tasks'], fix_proved, cc['graded'], 9)
    v.update(formal_tasks=len(frm), lean_files=len(leans), lean_thms=thms, tla_runs=len(cfgs),
             tla_models=len({c.parent for c in cfgs}), fix_proved=fix_proved,
             fix_partly=sum(r['covers'] == 'fix' and r['result'].startswith('partly') for r in frm),
             formal_checks=len(leans) + len(cfgs))
    imp = list(csv.DictReader(open(ROOT / 'data/impact.csv')))
    effects = json.loads((ROOT / 'evidence/impact/effects.json').read_text())
    import math
    def interval_cell(row, prefix):
        # Round outward so displayed intervals remain outer bounds.
        low = math.floor(float(row[prefix + '_low']) * 100) / 100
        high = math.ceil(float(row[prefix + '_high']) * 100) / 100
        return f'{low:.2f}–{high:.2f}'
    v['impact_rows'] = ''.join(
        f"<tr><td>{r['model']}</td><td class=\"n\">{float(r['published_mean']):.1f}</td>"
        f"<td class=\"n\"><b>{interval_cell(r, 'worst_case')}</b></td>"
        f"<td class=\"n\">{interval_cell(r, 'bounded')}</td>"
        f"<td class=\"n\">{interval_cell(r, 'sensitivity')}</td>"
        f"<td class=\"n\">{interval_cell(r, 'scale')}</td></tr>"
        for r in imp)
    v.update(n_bound=sum(e['kind'] == 'bounded' for e in effects.values()),
             n_open=sum(e['kind'] == 'open' for e in effects.values()))
    # The leaderboard page states that every neighbouring pair overlaps in the full-domain envelope.
    _env = sorted(imp, key=lambda r: -float(r['published_mean']))
    assert all(float(a['worst_case_low']) <= float(b['worst_case_high']) for a, b in zip(_env, _env[1:])), \
        'a neighbouring pair is separated in the full-domain envelope; update the leaderboard text'
    pr = list(csv.DictReader(open(ROOT / 'data/paired-results.csv')))
    v.update(paired_rows=len(pr), paired_tasks=len({r['task_id'] for r in pr}),
             paired_setup=sum(r['role'] == 'setup' for r in pr))
    # Overlap fails to certify order; it never proves a jointly attainable reversal.
    by_model = {r['model']: r for r in imp}
    order = sorted(by_model, key=lambda m: -float(by_model[m]['published_mean']))
    D['fragile'] = [{'a': a, 'b': b, 'rests': None}
                    for a, b in zip(order, order[1:])
                    if float(by_model[a]['bounded_low']) <= float(by_model[b]['bounded_high'])]
    D['arms'] = cc['arms']
    return {k: str(x) for k, x in v.items()}


# ---------------------------------------------------------------- page assembly

class Page:
    """One output page: its path relative to the language root and the links it needs."""

    def __init__(self, L, rel):
        self.L, self.rel = L, rel
        depth = rel.count('/')
        self.root = '../' * depth
        self.site_root = self.root + ('../' if L.code != 'en' else '')

    def task_href(self, tid):
        return f'{self.root}tasks/{tid}.html'


def task_link(P, D, tid, text=None):
    assert tid in D['tasks'], tid
    return f'<a class="task-link" href="{P.task_href(tid)}">{text or esc(D["names"][tid])}</a>'


def generated_prose(P, D, num):
    t = P.L.t
    out = {}
    if D['fragile']:
        parts = []
        for f in D['fragile']:
            s = t('gen.fragile', a=f['a'], b=f['b'])
            r = f['rests']
            if r:
                s += t('gen.rests_on', task=task_link(P, D, r['task']), b=f['b'], gain=r['gain'], swing=r['swing'], need=r['need'])
            parts.append(s)
        out['fragile_text'] = ' '.join(parts)
        out['rank_text'] = t('gen.rank_fragile', pairs=t('gen.pair_join').join(
            t('gen.pair', a=f['a'], b=f['b']) for f in D['fragile']))
    else:
        out['fragile_text'] = t('gen.not_fragile')
        out['rank_text'] = t('gen.rank_none')
    rows = []
    for r in D['formal']:
        tr = P.L.formal(r['task'])
        if P.L.code != 'en' and not tr:
            t.missing.add(f'formal:{r["task"]}')
        rows.append(f"<tr><td>{task_link(P, D, r['task'])}</td><td>{r['tool'].replace(' ', '&nbsp;')}</td>"
                    f"<td>{esc(t.opt('formal.result.' + r['result'], r['result'].capitalize()) if P.L.code != 'en' else t('formal.result.' + r['result']))}"
                    f"<br><span style=\"color:var(--muted)\">{t('formal.covers.' + r['covers'])}</span></td>"
                    f"<td>{esc(tr.get('what', r['what']))}</td><td>{esc(tr.get('limit', r['limit']))}</td></tr>")
    out['formal_rows'] = ''.join(rows)
    # problem categories: the count and the tasks of each (primary, then secondary)
    by = {r['task_id']: r for r in D['rows']}

    def links(ids):
        ids = sorted(ids, key=lambda x: D['names'][x].lower())
        return t('pcat.join').join(task_link(P, D, x) + (t('pcat.removed_mark') if by[x]['proposed'] == 'exclude' else '')
                                   for x in ids)
    for k in PC.KEYS:
        out[f'pcat_count_{k}'] = t('pcat.count', n=len(D['pcat'][k]))
        line = t('pcat.tasks_line', n=len(D['pcat'][k]), tasks=links(D['pcat'][k]), href=f'{P.root}tasks/index.html#{k}')
        if D['pcat2'][k]:
            line += '<br>' + t('pcat.secondary_line', tasks=links(D['pcat2'][k]))
        out[f'pcat_tasks_{k}'] = line
    return out


def verif(P, D, tid):
    t = P.L.t
    parts = [t('verif.lead')]
    r = D['formal_by'].get(tid)
    if r:
        parts.append(t('verif.formal', tool=r['tool'].replace(' ', '&nbsp;'), what=t('verif.cov.' + r['covers'], result=r['result'] if P.L.code == 'en' else t('formal.result.' + r['result']))))
    runs = [v for (tt, _), v in D['arms'].items() if tt == tid]
    if tid == 'dabic_gravity_inversion':
        parts.append(t('verif.dabic'))
    elif not runs:
        parts.append(t('verif.norun'))
    elif min(runs) >= 3:
        parts.append(t('verif.three'))
    else:
        parts.append(t('verif.three_but_some', n=sum(v < 3 for v in runs), m=len(runs)))
    return t('verif.join').join(parts)


def headline_values():
    """{{headline:<key>}} values for the Overview, from data/headline.json (tools/build_impact_figures.py).

    An unknown key raises KeyError, so a missing number fails the build instead of showing a placeholder."""
    h = json.loads((ROOT / 'data' / 'headline.json').read_text())
    rr, lb = h['real_run'], h['leaderboard']
    pub, sc, dl = lb['published'], lb['scale_only'], lb['documented_limits']
    a, b = 'Opus 4.8', 'GPT-5.5'
    oa = rr['kept_score_changes']['order_addition_permutation_optimization']
    f2 = lambda x: f'{x:.2f}'
    return {
        'tasks_10pt': str(h['measured_change_10_or_more']['count']),
        'real_regraded': str(rr['regraded_with_both_checkers']),
        'real_run_changed': str(len(rr['kept_score_changes'])),
        'real_subs_changed': str(len(rr['single_submissions_change_kept_score_does_not'])),
        'real_never': str(len(rr['problem_never_occurred'])),
        'oa_orig': f2(oa[0]), 'oa_fixed': f2(oa[1]),
        'top1_pub': f'{pub[a]:.1f}', 'top2_pub': f'{pub[b]:.1f}', 'top_gap': f'{pub[a] - pub[b]:.1f}',
        'top1_scale_low': f2(sc[a][0]), 'top1_scale_high': f2(sc[a][1]),
        'top2_scale_low': f2(sc[b][0]), 'top2_scale_high': f2(sc[b][1]),
        'top1_low': f2(dl[a][0]), 'top1_high': f2(dl[a][1]),
        'top2_low': f2(dl[b][0]), 'top2_high': f2(dl[b][1]),
    }


def expand(P, D, num, text):
    """Fill a prose template for one page."""
    t = P.L.t
    text = re.sub(r'\{\{t:([\w.\-]+)\}\}', lambda m: t(m.group(1)), text)
    text = re.sub(r'\{\{task:(\w+)(?:\|([^{}]*))?\}\}', lambda m: task_link(P, D, m.group(1), m.group(2)), text)
    if '{{headline:' in text:
        hv = headline_values()
        text = re.sub(r'\{\{headline:(\w+)\}\}', lambda m: hv[m.group(1)], text)
    n = 0

    def figure(m):
        nonlocal n
        n += 1
        name, _, link = m.group(1).partition('|')
        more = f' <a href="{P.task_href(link)}" class="case-link">{t("fig.read_case")}</a>' if link else ''
        return (f'<figure class="fig" id="fig-{name}"><div class="scroll">{svg(name, P.L.code)}</div><figcaption><b>{t("fig.label", n=n)}</b> '
                f'{esc(P.L.caption(name))}{more}</figcaption></figure>')
    text = re.sub(r'\{\{fig:([\w|-]+)\}\}', figure, text)
    text = re.sub(r'\{\{verif:(\w+)\}\}', lambda m: verif(P, D, m.group(1)), text)
    values = {**num, **generated_prose(P, D, num)}
    text = re.sub(r'\{\{([\w-]+)\}\}', lambda m: values[m.group(1)] if m.group(1) in values else m.group(0), text)
    text = text.replace('{{root}}', P.root).replace('{{site_root}}', P.site_root)
    return text


def layout(P, active, title, description, content, scripts='', wide=False):
    L, t = P.L, P.L.t
    current = ' aria-current="page"'
    tabs = ''.join(f'<a href="{P.root}{href}"{current if key == active else ""}>{t("nav." + key)}</a>'
                   for key, href in TABS)
    tabs += f'<a href="{REPO}">{t("nav.github")}&nbsp;&#8599;</a>'
    langs = [c for c in LANGS if c == 'en' or BUILD_ZH]
    sw, alts = [], []
    for c in langs:
        to_root = P.site_root + LANGS[c]['prefix']
        cur = ' aria-current="true"' if c == L.code else ''
        sw.append(f'<a href="{to_root}{P.rel}" hreflang="{LANGS[c]["html_lang"]}" lang="{LANGS[c]["html_lang"]}"{cur}>{t("lang." + c)}</a>')
        alts.append(f'<link rel="alternate" hreflang="{LANGS[c]["html_lang"]}" href="{SITE_URL}{LANGS[c]["prefix"]}{P.rel}">')
    pending = ''
    if L.code != 'en' and (L.major or L.t.missing):
        note = t('pending_note') if L.major else t('pending_note_partial')
        pending = f'<div class="pending" role="note"><div class="in">{note}</div></div>'
        if L.major:
            alts.append('<meta name="robots" content="noindex">')
    out = (SRC / 'layout.html').read_text()
    rep = {'html_lang': L.meta['html_lang'], 'page_title': esc(title), 'page_description': esc(description),
           'alternates': '\n'.join(alts) if len(langs) > 1 else '', 'site_root': P.site_root, 'root': P.root,
           'tabs': tabs, 'lang_switch': ' / '.join(sw) if len(langs) > 1 else '', 'pending': pending,
           'footer_class': 'wide-footer' if wide else '', 'scripts': scripts,
           'main_lang': ' lang="en"' if L.code != 'en' and L.major else '',
           'lang_head': ZH_FONTS if L.code == 'zh' else ''}
    out = re.sub(r'\{\{t:([\w.\-]+)\}\}', lambda m: t(m.group(1)), out)
    out = re.sub(r'\{\{(\w+)\}\}', lambda m: rep[m.group(1)] if m.group(1) in rep else m.group(0), out)
    out = out.replace('{{content}}', content)
    return out


def write(P, text):
    left = PLACEHOLDER.findall(text)
    assert not left, (P.L.code, P.rel, left[:5])
    path = SITE / P.L.meta['prefix'] / P.rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


# ---------------------------------------------------------------- prose pages

def prose_page(L, D, num, page, rel, active):
    L.reset()
    P = Page(L, rel)
    body = expand(P, D, num, L.template(page))
    t = L.t
    title = t('page.overview.title') if page == 'overview' else t(f'page.{page}.title')
    desc = t('site.description') if page == 'overview' else t(f'page.{page}.description')
    write(P, layout(P, active, title, desc, body))


# ---------------------------------------------------------------- tasks index

TASKS_JS = """<script>
(function () {
  var list = document.getElementById('cards'); if (!list) return;
  var items = [].slice.call(list.children), q = document.getElementById('q');
  var count = document.getElementById('count'), empty = document.getElementById('empty');
  var tpl = count.getAttribute('data-tpl'), filt = 'all', cat = 'all';
  var buttons = [].slice.call(document.querySelectorAll('#filters button[data-f]'));
  var cbuttons = [].slice.call(document.querySelectorAll('#cfilters button[data-c]'));
  function apply(push) {
    var term = q.value.trim().toLowerCase(), shown = 0;
    items.forEach(function (li) {
      var ok = (filt === 'all' || li.getAttribute('data-outcome') === filt) &&
               (cat === 'all' || li.getAttribute('data-pcat') === cat) &&
               (!term || li.getAttribute('data-search').indexOf(term) >= 0);
      li.classList.toggle('card-hidden', !ok); if (ok) shown++;
    });
    count.textContent = tpl.replace('{shown}', shown).replace('{total}', items.length);
    empty.hidden = shown > 0;
    buttons.forEach(function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-f') === filt)); });
    cbuttons.forEach(function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-c') === cat)); });
    if (push) {
      var hs = [filt, cat].filter(function (x) { return x !== 'all'; }).join('+');
      try { history.replaceState(null, '', hs ? '#' + hs : location.pathname + location.search); } catch (e) {}
    }
  }
  buttons.forEach(function (b) { b.addEventListener('click', function () { filt = b.getAttribute('data-f'); apply(true); }); });
  cbuttons.forEach(function (b) { b.addEventListener('click', function () { cat = b.getAttribute('data-c'); apply(true); }); });
  q.addEventListener('input', function () { apply(false); });
  location.hash.slice(1).split('+').forEach(function (h) {
    if (buttons.some(function (b) { return b.getAttribute('data-f') === h; })) filt = h;
    if (cbuttons.some(function (b) { return b.getAttribute('data-c') === h; })) cat = h;
  });
  apply(false);
})();
</script>"""


def plain_for(L, D, tid):
    own, en = L.plain(D['plain'])
    if L.code != 'en' and tid not in own:
        L.major = True
    return own.get(tid, en[tid])


def tasks_index(L, D):
    L.reset()
    P = Page(L, 'tasks/index.html')
    t = L.t
    counts = D['counts']
    btns = [f'<button type="button" data-f="all" aria-pressed="true">{t("tasks.all", n=len(D["rows"]))}</button>']
    btns += [f'<button type="button" data-f="{k}" aria-pressed="false">{t("tasks.filter", label=t("outcome." + k), n=counts[k])}</button>'
             for k in ORDER if counts.get(k)]
    cbtns = [f'<button type="button" data-c="all" aria-pressed="true">{t("tasks.cat_all")}</button>']
    cbtns += [f'<button type="button" data-c="{k}" aria-pressed="false">{t("tasks.filter", label=t("pcat." + k + ".short"), n=len(D["pcat"][k]))}</button>'
              for k in PC.KEYS]
    cards = []
    for r in D['rows']:
        tid = r['task_id']
        p = plain_for(L, D, tid)
        cat = t.opt('category.' + r['category'], r['category']) if L.code != 'en' else r['category']
        pk = PC.primary(r) or ''
        pname = t('pcat.' + pk) if pk else ''
        search = ' '.join([r['name'], tid, r['category'], cat, p['headline'], p['about'], t('outcome.' + r['proposed']),
                           pname]).lower()
        chip = f'<span class="badge pc">{t("pcat." + pk + ".short")}</span>' if pk else ''
        cards.append(
            f'<li data-task="{tid}" data-outcome="{r["proposed"]}" data-pcat="{pk}" data-search="{esc(search)}">'
            f'<a class="card" href="{tid}.html"><span class="top"><span>{esc(cat)}</span>'
            f'<span class="badges">{chip}<span class="badge b-{r["proposed"]}">{t("outcome." + r["proposed"])}</span></span></span>'
            f'<span class="name">{esc(r["name"])}</span><span class="line">{esc(p["headline"])}</span>'
            f'<span class="go">{t("tasks.open")} &rarr;</span></a></li>')
    body = (f'<header class="title tasks-head"><p class="kicker">{t("tasks.kicker")}</p><h1>{t("tasks.h1")}</h1>'
            f'<p class="subtitle" style="font-style:normal;font-size:19px">{t("tasks.intro")}</p>'
            f'<p class="note">{t("tasks.legend")} {t("tasks.legend_cat")}</p></header>'
            f'<section class="wide" style="padding-top:6px">'
            f'<div class="controls" id="filters" role="group" aria-label="{esc(t("tasks.filter_label"))}">{"".join(btns)}</div>'
            f'<div class="controls cfilters" id="cfilters" role="group" aria-label="{esc(t("tasks.filter_cat_label"))}">{"".join(cbtns)}</div>'
            f'<div class="controls"><div class="search"><label for="q" class="skip">{t("tasks.search_label")}</label>'
            f'<input id="q" type="search" placeholder="{esc(t("tasks.search_placeholder"))}" autocomplete="off"></div></div>'
            f'<p class="count" id="count" aria-live="polite" data-tpl="{esc(t("tasks.count", shown="{shown}", total="{total}"))}">'
            f'{t("tasks.count", shown=len(cards), total=len(cards))}</p>'
            f'<ul class="cards" id="cards">{"".join(cards)}</ul>'
            f'<div class="empty" id="empty" hidden>{t("tasks.empty")}</div></section>')
    write(P, layout(P, 'tasks', t('page.tasks.title'), t('page.tasks.description'), body,
                    scripts=TASKS_JS, wide=True))


# ---------------------------------------------------------------- task pages

def srcline(t, path):
    link = f'<a href="{BLOB}{path}"><code>{path}</code></a>'
    return f'<div class="src">{t("task.grading.source", src=link)}</div>'


def grading(P, D, tid):
    t = P.L.t
    task = D['tasks'][tid]
    j = task['judge']
    src = f'<a href="{BLOB}tasks/{tid}.json">tasks/{tid}.json</a>'
    rows = []

    def row(label, value):
        rows.append(f'<dt>{label}</dt><dd>{value}</dd>')
    if task.get('game_mode') or j.get('game_server_cmd'):
        row(t('task.grading.game'), t('task.grading.game_text') + f'<pre><code>{esc(j.get("game_server_cmd", ""))}</code></pre>')
    if j.get('eval_cmd'):
        cmd = j['eval_cmd']
        lines = cmd.count('\n') + 1
        if lines > 6:
            first = esc(cmd.split('\n', 1)[0])
            row(t('task.grading.cmd'), f'<pre><code>{first} …</code></pre><details class="longcmd"><summary>'
                f'{t("task.grading.cmd_long", n=lines)}</summary><pre class="long"><code>{esc(cmd)}</code></pre></details>')
        else:
            row(t('task.grading.cmd'), f'<pre><code>{esc(cmd)}</code></pre>')
    row(t('task.grading.timeout'), t('task.grading.timeout_text', minutes=plural_time(t, int(j['eval_timeout'])),
                                     seconds=fmtnum(int(j['eval_timeout']))))
    paths = ', '.join(f'<code>{esc(p)}</code>' for p in task.get('submit_paths', []))
    sub = t('task.grading.submit_text', paths=paths)
    if task.get('submit_exclude'):
        sub += ' ' + t('task.grading.submit_exclude', paths=', '.join(f'<code>{esc(p)}</code>' for p in task['submit_exclude']))
    row(t('task.grading.submit'), sub)
    parser = j.get('parser', '')
    if parser in ('score_sum', 'structured_json', 'pytest_v'):
        raw = t('parser.' + parser)
    elif not parser and (task.get('game_mode') or j.get('game_server_cmd')):
        raw = t('parser.game')
    else:
        raw = t('parser.other', parser=esc(parser))
    row(t('task.grading.raw'), raw)
    direction = j.get('score_direction')
    row(t('task.grading.direction'), t('direction.minimize') if direction == 'minimize' else
        t('direction.maximize') if direction == 'maximize' else t('direction.maximize_default'))
    rs = j.get('rescale')
    if not rs:
        conv = t('rescale.none')
    else:
        kind = rs['kind']
        vals = {k: fmtnum(v) for k, v in rs.items() if k != 'kind'}
        if kind == 'log_anchor':
            vals['full'] = f"{rs['anchor_raw'] ** (100 / rs['anchor_score']):,.4g}"
        key = 'rescale.' + kind
        conv = (t(key, **vals) if key in t.en else t('rescale.unknown', kind=esc(kind)))
        conv += ' ' + t('rescale.nonfinite') + ' ' + t('rescale.kind', kind=esc(kind))
    row(t('task.grading.rescale'), conv + srcline(t, 'sforge/harness/score_rescale.py'))
    best = t('selection.best.minimize') if direction == 'minimize' else t('selection.best.maximize')
    sel = j.get('selection')
    if sel in ('score_first', 'valid_then_score', 'pass_rate_first'):
        stext = t('selection.' + sel, best=best)
    elif sel is None:
        stext = t('selection.default') + ' ' + t('selection.pass_rate_first', best=best)
    else:
        stext = f'<code>{esc(sel)}</code>'
    row(t('task.grading.selection'), stext + srcline(t, 'sforge/harness/selection.py'))
    row(t('task.grading.internet'), t('internet.true') if task.get('internet') else t('internet.false'))
    mk = 'smt' if tid in SMT_16CPU else 'lean' if tid in LEAN_8CPU else 'default'
    row(t('task.grading.machine'), t('machine.' + mk) + ' ' + t('machine.source', url=BLOB + CONFIG_MD))
    return f'<p class="note">{t("task.grading.intro", task_json=BLOB + f"tasks/{tid}.json", id=tid)}</p><dl class="grade">{"".join(rows)}</dl>', src


def case_link_fn(P, D, md_dir, used_figs):
    """Rewrite a link in a case page: other cases become task pages, figures site-local, the rest GitHub."""
    import posixpath

    def link(href, is_image):
        if re.match(r'^(https?:|mailto:)', href):
            return href
        if href.startswith('#'):
            return href
        path, _, frag = href.partition('#')
        frag = '#' + frag if frag else ''
        cands = [posixpath.normpath(posixpath.join(md_dir, path)), posixpath.normpath(posixpath.join('cases', path))]
        target = next((c for c in cands if (ROOT / c).exists()), cands[0])
        if target.startswith('..'):
            return None
        m = re.fullmatch(r'cases/(\w+)\.md', target)
        if m and m.group(1) in D['tasks']:
            return P.task_href(m.group(1)) + frag
        m = re.fullmatch(r'cases/figures/([\w.-]+\.svg)', target)
        if m and is_image:
            used_figs.add(m.group(1))
            return f'{P.site_root}figures/{m.group(1)}'
        is_dir = (ROOT / target).is_dir() or path.endswith('/')
        return (TREE if is_dir else BLOB) + target.rstrip('/') + frag if target != '.' else REPO
    return link


def prompt_link(href, is_image):
    return href if re.match(r'^https?://', href) else None


TASK_JS = """<script>
(function () {
  [].forEach.call(document.querySelectorAll('.prompt'), function (box) {
    var body = box.querySelector('.prompt-body'), b = box.querySelector('.prompt-toggle');
    if (body.scrollHeight <= body.clientHeight + 40) { box.classList.remove('clamped'); b.parentNode.removeChild(b); return; }
    b.addEventListener('click', function () {
      var open = box.classList.toggle('clamped') === false;
      b.textContent = open ? b.getAttribute('data-less') : b.getAttribute('data-more');
      b.setAttribute('aria-expanded', String(open));
      if (!open) box.scrollIntoView({block: 'start'});
    });
  });
})();
</script>"""


def task_page(L, D, i, used_figs):
    L.reset()
    r = D['rows'][i]
    tid = r['task_id']
    P = Page(L, f'tasks/{tid}.html')
    t = L.t
    task = D['tasks'][tid]
    p = plain_for(L, D, tid)
    cat = t.opt('category.' + r['category'], r['category']) if L.code != 'en' else r['category']
    md_dir = (f'cases/{L.code}' if L.code != 'en'
              and (ROOT / 'cases' / L.code / f'{tid}.md').exists()
              and f'cases/{tid}.md' not in L.pending.get('sources', []) else 'cases')
    md = L.source(ROOT / 'cases' / f'{tid}.md', ROOT / 'cases' / L.code / f'{tid}.md')
    md = re.sub(r'\A\s*# [^\n]*\n', '', md)                       # the page has its own title
    # the figure is shown in the summary above the case; drop the duplicate and its caption line
    md = re.sub(r'\n!\[[^\]]*\]\(figures/[^)]+\)\n\n\*[^\n]*\*\n', '\n', md, count=1)
    case_html = mdrender.render(md, link=case_link_fn(P, D, md_dir, used_figs), heading_offset=1, slug_prefix='case-')
    prompt_html = mdrender.render(task['work']['agent_query'], link=prompt_link, heading_offset=2, slug_prefix='prompt-')
    figure = ''
    if (FIG / f'{tid}.svg').exists():
        figure = (f'<figure class="fig"><div class="scroll">{svg(tid, L.code)}</div>'
                  f'<figcaption>{esc(L.caption(tid))}</figcaption></figure>')
    fr = D['formal_by'].get(tid)
    formal = ''
    if fr:
        tr = L.formal(tid)
        res = t.opt('formal.result.' + fr['result'], fr['result'].capitalize()) if L.code != 'en' else t('formal.result.' + fr['result'])
        formal = (f'<dt>{t("task.sum.formal")}</dt><dd>' +
                  esc(t('task.formal', result=res, tool=fr['tool'], what=tr.get('what', fr['what']), limit=tr.get('limit', fr['limit']))) + '</dd>')
    pk = PC.primary(r)
    category = ''
    if pk:
        sec = PC.secondary(r)
        ctext = (t('task.category.with_secondary', primary=t('pcat.' + pk), secondary=t('pcat.join').join(t('pcat.' + x) for x in sec))
                 if sec else t('task.category.primary_only', primary=t('pcat.' + pk)))
        category = (f'<dt>{t("task.sum.category")}</dt><dd><a href="{P.root}index.html#{pk}">{esc(ctext)}</a></dd>')
    status = ''
    if r['proposed'] == 'repair-v2':
        english = r.get('validation_status') or VALIDATION_DEFAULT
        text = L.validation(tid, english) if r.get('validation_status') else t('task.sum.status_default')
        status = f'<dt>{t("task.sum.status")}</dt><dd>{esc(text)}</dd>'
    summary = (f'<dl class="sum"><dt>{t("task.sum.about")}</dt><dd>{plain_html(p["about"])}</dd>'
               f'<dt>{t("task.sum.problem")}</dt><dd>{plain_html(p["problem"])}</dd>'
               f'<dt>{t("task.sum.effect")}</dt><dd>{plain_html(p["effect"])}</dd>'
               f'<dt>{t("task.sum.action")}</dt><dd>{plain_html(p["action"])}</dd>{category}{status}{formal}</dl>')
    grade_html, _ = grading(P, D, tid)
    # files
    links = [(BLOB + f'cases/{tid}.md', t('task.links.case')), (BLOB + f'tasks/{tid}.json', t('task.links.task_json', id=tid))]
    pkg = ROOT / 'repairs' / f'{tid}-v2'
    if pkg.is_dir():
        links.append((TREE + f'repairs/{tid}-v2', t('task.links.package')))
        if (pkg / 'paired' / 'results.md').exists():
            links.append((BLOB + f'repairs/{tid}-v2/paired/results.md', t('task.links.paired')))
    if tid in D['paired_tasks']:
        links.append((f'{P.site_root}data/paired-results.csv', t('task.links.paired_csv')))
    for rv in sorted((ROOT / 'evidence' / 'reviews').glob(f'{tid}*.md')):
        if rv.stem == tid or rv.stem.startswith(tid + '-'):
            links.append((BLOB + f'evidence/reviews/{rv.name}', t('task.links.review') + f' (<code>{rv.name}</code>)'))
    if (ROOT / 'evidence' / 'scripts' / tid).is_dir():
        links.append((TREE + f'evidence/scripts/{tid}', t('task.links.scripts')))
    if (ROOT / 'evidence' / 'formal' / 'notes' / f'{tid}.md').exists():
        links.append((BLOB + f'evidence/formal/notes/{tid}.md', t('task.links.formal')))
    links.append((BLOB + 'evidence/README.md', t('task.links.evidence')))
    files = '<ul class="links">' + ''.join(f'<li><a href="{esc(h)}">{lab}</a></li>' for h, lab in links) + '</ul>'
    rows = D['rows']
    prv, nxt = rows[i - 1], rows[(i + 1) % len(rows)]
    pager = (f'<nav class="pager" aria-label="{esc(t("task.all"))}">'
             f'<a class="prev" href="{prv["task_id"]}.html" rel="prev"><small>&larr; {t("task.prev")}</small>{esc(prv["name"])}</a>'
             f'<a class="all" href="index.html">{t("task.all")}</a>'
             f'<a class="next" href="{nxt["task_id"]}.html" rel="next"><small>{t("task.next")} &rarr;</small>{esc(nxt["name"])}</a></nav>')
    toc = ''.join(f'<a href="#{a}">{t("task.toc." + k)}</a>' for a, k in
                  (('summary', 'summary'), ('prompt', 'prompt'), ('grading', 'grading'), ('found', 'found'), ('files', 'links')))
    lang_note = t('task.prompt.lang_note')
    found_note = t('task.found.lang_note')
    sep = ' ' if L.code == 'en' else ''  # no space between sentences in Chinese
    body = (f'<div class="col"><div class="crumbs"><a href="index.html">&larr; {t("task.back")}</a>'
            f'<span>{t("task.field", field=esc(cat))}</span></div>'
            f'<header class="task-head"><h1>{esc(r["name"])}</h1>'
            f'<span class="badge b-{r["proposed"]}" data-outcome="{r["proposed"]}">{t("outcome." + r["proposed"])}</span> '
            + (f'<a class="badge pc" data-pcat="{pk}" href="{P.root}index.html#{pk}">{t("pcat." + pk)}</a> ' if pk else '') +
            f'<span class="id">{tid}</span>'
            f'<p class="summary">{esc(p["headline"])}{"." if P.L.code == "en" else "。"}</p>'
            f'<nav class="toc" aria-label="{esc(t("task.summary.h2"))}">{toc}</nav></header>'
            f'<section id="summary"><h2 class="sec">{t("task.summary.h2")}</h2>{summary}{figure}</section>'
            f'<section id="prompt"><h2 class="sec">{t("task.prompt.h2")}</h2>'
            f'<p class="origin">{t("task.prompt.origin", task_json=BLOB + f"tasks/{tid}.json", id=tid)}'
            f'{(sep + lang_note) if lang_note else ""}</p>'
            f'<div class="prompt clamped"><div class="prompt-body md" lang="en">{nobraces(prompt_html)}</div>'
            f'<button type="button" class="prompt-toggle" aria-expanded="false" data-more="{esc(t("task.prompt.more"))}" '
            f'data-less="{esc(t("task.prompt.less"))}">{t("task.prompt.more")}</button></div></section>'
            f'<section id="grading"><h2 class="sec">{t("task.grading.h2")}</h2>{grade_html}</section>'
            f'<section id="found"><h2 class="sec">{t("task.found.h2")}</h2>'
            f'<p class="note">{t("task.found.intro", repo=REPO)}{(sep + found_note) if found_note else ""}</p>'
            f'<div class="md"{" lang=en" if md_dir == "cases" and L.code != "en" else ""}>{nobraces(case_html)}</div></section>'
            f'<section id="files"><h2 class="sec">{t("task.links.h2")}</h2>{files}</section>'
            f'{pager}</div>')
    write(P, layout(P, 'tasks', t('page.task.title', name=r['name']), p['headline'], body, scripts=TASK_JS))


# ---------------------------------------------------------------- main

def main():
    D = load_data()
    D['paired_tasks'] = {r['task_id'] for r in csv.DictReader(open(ROOT / 'data/paired-results.csv'))}
    num = numbers(D)
    # start from a clean tree, keeping only the downloadable data the Pages workflow copies in
    for p in SITE.glob('*'):
        if p.name == 'data':
            continue
        shutil.rmtree(p) if p.is_dir() else p.unlink()
    (SITE / 'assets').mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SRC / 'site.css', SITE / 'assets' / 'site.css')
    used_figs = set()
    report = {}
    for code in [c for c in LANGS if c == 'en' or BUILD_ZH]:
        L = Lang(code)
        pend = []
        for page, rel, active in (('overview', 'index.html', 'overview'), ('method', 'method.html', 'method'),
                                  ('leaderboard', 'leaderboard.html', 'leaderboard')):
            prose_page(L, D, num, page, rel, active)
            pend.append(L.major)
        tasks_index(L, D)
        pend.append(L.major)
        for i in range(len(D['rows'])):
            task_page(L, D, i, used_figs)
            pend.append(L.major)
        report[code] = (len(pend), sum(pend))
    if used_figs:
        (SITE / 'figures').mkdir(exist_ok=True)
        for f in sorted(used_figs):
            s = (FIG / f).read_text()
            (SITE / 'figures' / f).write_text(DARK.sub('', s))
    pages = sorted(p.relative_to(SITE).as_posix() for p in SITE.rglob('*.html'))
    kb = sum((SITE / p).stat().st_size for p in pages) // 1024
    print(f'wrote {len(pages)} pages ({kb} KB) to site/:', ', '.join(
        f'{c}: {n} pages, {k} pending translation' for c, (n, k) in report.items()), dict(D['counts']))


if __name__ == '__main__':
    main()
