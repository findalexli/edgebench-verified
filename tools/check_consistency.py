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


def check_categories(d, readme, findings):
    """Every problem task has exactly one valid primary category, and every shown category count agrees."""
    sys.path.insert(0, str(ROOT / 'tools'))
    import categories as PC
    decisions = list(d.values())
    for m in PC.validate(decisions):
        need(False, f'data/decisions.json: {m}')
    prim = PC.by_primary(decisions)
    problem = {t for t, r in d.items() if r['proposed'] in PC.PROBLEM}
    listed = [t for ids in prim.values() for t in ids]
    need(sorted(listed) == sorted(problem), 'problem categories do not give every fixed or removed task exactly one primary category')
    strings = {lang: json.loads((ROOT / 'tools/i18n' / f'{lang}.json').read_text()) for lang in ('en', 'zh')}
    en = strings['en']
    # README: the category table and the section headings
    for i, k in enumerate(PC.KEYS, 1):
        n = len(prim[k])
        name = re.escape(en['pcat.' + k])
        need(re.search(rf'^\| {name} \| {n} \|', readme, re.M), f'README category table count for {k} != {n}')
        need(re.search(rf'^### {i}\. {name} \({n} tasks\)$', readme, re.M), f'README heading count for {k} != {n}')
    need(re.search(rf'^\| \*\*Total\*\* \| \*\*{len(problem)}\*\* \| \|$', readme, re.M), 'README category total wrong')
    # FINDINGS.md: one section per category, its count and exactly its tasks
    for i, k in enumerate(PC.KEYS, 1):
        m = re.search(rf'^## {i}\. {re.escape(en["pcat." + k])}\n\n\*\*(\d+) tasks\.\*\*(.*?)(?=^## )', findings, re.M | re.S)
        need(m and int(m[1]) == len(prim[k]), f'FINDINGS.md count for {k} wrong')
        if m:
            need(sorted(re.findall(r'^\| \[[^\]]+\]\(cases/(\w+)\.md\)', m[2], re.M)) == prim[k],
                 f'FINDINGS.md section {k} lists the wrong tasks')
    # the site: overview headings, the task-list filter and cards, the badge on every task page
    for prefix, lang in (('', 'en'), ('zh/', 'zh')):
        ov = ROOT / 'site' / prefix / 'index.html'
        if not ov.exists():
            continue
        ovt = ov.read_text()
        cnt = strings[lang].get('pcat.count', en['pcat.count'])
        for k in PC.KEYS:
            n = len(prim[k])
            want = cnt.replace('{n}', str(n))
            need(re.search(rf'<h3 id="{k}">.*?<span class="hcount">{re.escape(want)}</span></h3>', ovt),
                 f'site/{prefix}index.html heading count for {k} != {n}')
            need(len(re.findall(re.escape(want), ovt)) >= 2, f'site/{prefix}index.html count list for {k} missing')
        idx = (ROOT / 'site' / prefix / 'tasks' / 'index.html').read_text()
        cards = dict(re.findall(r'data-task="(\w+)" data-outcome="[\w-]+" data-pcat="(\w*)"', idx))
        need(cards == {t: (r.get('problem_category') or '') for t, r in d.items()},
             f'site/{prefix}tasks/index.html card categories disagree with data/decisions.json')
        for k in PC.KEYS:
            m = re.search(rf'data-c="{k}"[^>]*>[^<]*?[(（](\d+)[)）]</button>', idx)
            need(m and int(m[1]) == len(prim[k]), f'site/{prefix}tasks/index.html filter count for {k} wrong')
        for t, r in d.items():
            page = (ROOT / 'site' / prefix / 'tasks' / f'{t}.html').read_text()
            got = re.findall(r'data-pcat="(\w+)"', page)
            need(got == ([r.get('problem_category')] if t in problem else []),
                 f'site/{prefix}tasks/{t}.html category badge {got} disagrees with data/decisions.json')


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
    # the website (tools/build_site.py): no unfilled placeholder on any page; the task list and every
    # task page show each task's decision; the Overview's headline counts match
    pages = sorted((ROOT / 'site').rglob('*.html'))
    need(pages, 'site/ has no pages; run tools/build_site.py')
    for p in pages:
        left = re.findall(r'\{\{[\w|:-]+\}\}', p.read_text())
        need(not left, f'{p.relative_to(ROOT)} has unfilled placeholders {left[:3]}')
    for prefix in ('', 'zh/'):
        index = ROOT / 'site' / prefix / 'tasks' / 'index.html'
        if prefix and not index.exists():
            continue
        need(index.exists(), f'site/{prefix}tasks/index.html missing')
        listed = dict(re.findall(r'data-task="(\w+)" data-outcome="([\w-]+)"', index.read_text())) if index.exists() else {}
        need(listed == {t: r['proposed'] for t, r in d.items()}, f'site/{prefix}tasks/index.html outcomes disagree with data/decisions.json')
        for t, r in d.items():
            tp = ROOT / 'site' / prefix / 'tasks' / f'{t}.html'
            need(tp.exists() and f'data-outcome="{r["proposed"]}"' in tp.read_text(),
                 f'site/{prefix}tasks/{t}.html missing or its outcome is not {r["proposed"]}')
    # the Overview's headline-numbers block (en and zh) carries data-count attributes
    for prefix in ('', 'zh/'):
        ov = ROOT / 'site' / prefix / 'index.html'
        if prefix and not ov.exists():
            continue
        ovt = ov.read_text() if ov.exists() else ''
        for k, n in list(c.items()) + [('n_problem', c.get('repair-v2', 0) + c.get('exclude', 0))]:
            if k == 'retain':
                continue
            need(re.search(rf'data-count="{re.escape(k)}">{n}<', ovt),
                 f'site/{prefix}index.html headline count for {k} != {n}')
    # data/decisions.csv / DECISIONS.md
    rows = list(csv.DictReader((ROOT / 'data/decisions.csv').open()))
    need({r['task_id']: r['decision'] for r in rows} == {t: r['proposed'] for t, r in d.items()},
         'data/decisions.csv disagrees with data/decisions.json')
    # plain summaries: one per task, action line agrees with the decision
    plain = json.loads((ROOT / 'cases' / 'plain.json').read_text())
    need(set(plain) == set(d), 'cases/plain.json does not cover exactly the 51 tasks')
    pre = {'retain': 'Kept as is', 'retain-with-note': 'Kept, with a note', 'repair-v2': 'Fixed in a new version', 'exclude': 'Removed'}
    for t, r in d.items():
        if r.get('validation_status'):
            need(bool(plain.get(t, {}).get('action')), f'{t}: missing scoped repair action')
            need(r['proposed'] == 'repair-v2', f'{t}: repair validation status on non-repair task')
            applying = (ROOT / 'APPLYING-FIXES.md').read_text()
            need(r['validation_status'] in applying, f'{t}: current validation status absent from applying guide')
        else:
            need(plain.get(t, {}).get('action', '').startswith(pre[r['proposed']]), f'{t}: plain action disagrees with decision')
    # case pages: one per task, decision line matches
    for t, r in d.items():
        p = ROOT / 'cases' / f'{t}.md'
        need(p.exists(), f'missing case page {t}')
        if p.exists():
            head = p.read_text()[:1500]
            want = LABEL[r['proposed']]
            if r.get('validation_status'):
                need(re.search(r'\*\*Outcome:\*\*\s*\S[^\n]+', head), f'{t}: missing scoped case outcome')
            else:
                need(re.search(rf'\*\*Outcome:\*\*\s*{re.escape(want)}', head),
                     f'case page {t} decision line does not say "{want}"')
    # repairs: preserve historical paired evidence; current status may have pending release gates
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
    check_categories(d, readme, findings)
    pairs = {r['task_id'] for r in csv.DictReader((ROOT / 'data/paired-results.csv').open())}
    need(pairs <= {t for t in d if (ROOT / 'repairs' / f'{t}-v2').is_dir()}, 'data/paired-results.csv has a task without a package')
    need({t for t, r in d.items() if r['proposed'] == 'repair-v2'} <= pairs, 'a repair has no paired rows')
    # Impact artifacts must use intervals; check freshness against the source effects.
    imp = list(csv.DictReader((ROOT / 'data/impact.csv').open()))
    sys.path.insert(0, str(ROOT / 'tools'))
    import estimate_impact as EI
    lb = EI.parse_leaderboard()
    effects = json.loads((ROOT / 'evidence/impact/effects.json').read_text())
    need({r['model'] for r in imp} == set(EI.MODELS), 'impact model rows differ from source')
    for row in imp:
        need('exact_adjusted_mean' not in row, 'impact CSV still asserts an exact adjusted mean')
        scale = EI.scale_intervals(lb, row['model'])
        bounded = EI.effect_intervals(scale, effects, {'bounded'})
        sensitivity = EI.effect_intervals(bounded, effects, {'sensitivity'})
        outer_effects = {t: (dict(e, kind='open', bound=None, bound_up=100., bound_down=100.)
                             if e['kind'] == 'sensitivity' else e) for t, e in effects.items()}
        outer = EI.effect_intervals(bounded, outer_effects, {'open'})
        for prefix, values in [('scale', scale), ('bounded', bounded),
                               ('sensitivity', sensitivity), ('worst_case', outer)]:
            for suffix, expected in zip(('low', 'high'), EI.average_interval(values)):
                need(abs(float(row[prefix + '_' + suffix]) - expected) < 1e-6,
                     f"impact {row['model']} {prefix}_{suffix} is stale")
        need(int(row['tasks_in_mean']) == len(scale), f"impact {row['model']} task count is stale")
        need(abs(float(row['scale_midpoint_mean']) - sum(EI.average_interval(scale))/2) < 1e-6,
             f"impact {row['model']} display midpoint is stale")
    need(effects['portfolio_risk_calibration']['kind'] == 'sensitivity',
         'Portfolio sweep must not enter the documented-limit category')
    # side-by-side comparison counts in README and METHOD agree with data/paired-repeatability.csv
    import build_site as BS
    cc = BS.comparison_counts()
    for name in ('README.md', 'METHOD.md'):
        txt = ' '.join((ROOT / name).read_text().split())
        m = re.search(r'Across (\d+) graded comparisons.*?(\d+) of them run three times; (\d+) setup runs', txt)
        need(m and (int(m[1]), int(m[2]), int(m[3])) == (cc['graded'], cc['graded3'], cc['setup']),
             f'{name}: comparison counts {m.groups() if m else None} != '
             f"{(cc['graded'], cc['graded3'], cc['setup'])} from data/paired-repeatability.csv")
        if 'All but one' in txt:
            need(cc['graded'] - cc['graded3'] == 1, f'{name} says "All but one" but {cc["graded"] - cc["graded3"]} comparisons have fewer than 3 runs')
    rep_md = ' '.join((ROOT / 'data/paired-repeatability.md').read_text().split())
    need(f"graded comparisons: **{cc['graded']}**, of which **{cc['graded3']}** have all 3 runs" in rep_md,
         'data/paired-repeatability.md graded-comparison totals disagree with data/paired-repeatability.csv')
    # repair packages: the recorded fingerprints of repair.patch and materialize.sh match the files
    import hashlib
    for lock_path in sorted((ROOT / 'repairs').glob('*-v2/source-lock.json')):
        pkg = lock_path.parent
        lock = json.loads(lock_path.read_text())
        m = lock.get('materialize', {}) if isinstance(lock.get('materialize'), dict) else {}
        for key, fname in (('repair_patch_sha256', 'repair.patch'), ('materialize_sh_sha256', 'materialize.sh')):
            if key in m and (pkg / fname).exists():
                need(m[key] == hashlib.sha256((pkg / fname).read_bytes()).hexdigest(),
                     f'{pkg.name}: source-lock {key} is stale')
    # the impact figures, their Chinese captions and data/headline.json match what the data gives
    sys.path.insert(0, str(ROOT / 'tools'))
    import build_impact_figures as BIF
    for m in BIF.check():
        need(False, m)
    for m in problems:
        print('MISMATCH:', m)
    print(f'{dict(c)}; {len(problems)} problems')
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
