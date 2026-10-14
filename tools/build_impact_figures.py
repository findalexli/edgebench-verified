#!/usr/bin/env python3
"""Build the two impact figures and the headline numbers from the data, so they never drift.

Writes
  cases/figures/impact-overview.svg / .json, cases/figures/zh/impact-overview.svg
      All 32 problem tasks: what the problem does to one affected submission, out of 100.
  cases/figures/real-runs.svg / .json, cases/figures/zh/real-runs.svg
      The third-party Claude Opus 5.5 run, regraded: the run's kept score under the original and the fixed
      checker, and the largest change for any single submission.
  data/headline.json
      The headline numbers, each computed here.
  tools/i18n/figures.zh.json (the two figures' entries only)
      Their Chinese caption and alt text.

Sources. Categories come from data/decisions.json, limits (hollow bars) from evidence/impact/effects.json,
real-run values from evidence/runs/opus55-regrade2-summary/summary.json (and, for Lean Analysis,
evidence/runs/opus55-regrade2-lean-derived/result/out/lean_derived.json; for Borden,
evidence/runs/opus55-rollouts-meta/submission-histories.json). Values measured on our test submissions are
in the MEASURED table below; each one names a file and a string that must occur in it, and the build fails
if the string is gone. The line where it occurs is recorded in the figure's .json ("sources").

  python3 tools/build_impact_figures.py           # write the files
  python3 tools/build_impact_figures.py --check   # exit 1 if any file differs from what the data gives
"""
import csv
import html
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from names import names as task_names  # noqa: E402
import categories as PC  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / 'cases' / 'figures'
SUMMARY = 'evidence/runs/opus55-regrade2-summary/summary.json'
LEAN = 'evidence/runs/opus55-regrade2-lean-derived/result/out/lean_derived.json'
HIST = 'evidence/runs/opus55-rollouts-meta/submission-histories.json'
EFFECTS = 'evidence/impact/effects.json'
FIGZH = 'tools/i18n/figures.zh.json'

# ---------------------------------------------------------------------------------------------------------
# Values measured on our own test submissions (original checker against the fixed one, or two forms of the
# same work on the original checker). kind: 'test' (our test submission), 'real' (a real agent submission,
# filled in from the regrade below), 'range' (several runs). sign: '+' the fixed checker gives more, '-' less,
# '±' both directions measured, '' a gap between two forms of the same work (no fixed-version change).
# src: (file, string that must occur in it). Values here are checked against the string where they appear.
# ---------------------------------------------------------------------------------------------------------
MEASURED = {
    'rust_multicrate_reconstruction': dict(v=20.71, sign='+', src=('cases/rust_multicrate_reconstruction.md', '| complete solution (upstream code) | 73.9926 | 94.7022 | +20.7096 |'),
        en='+20.71 (limit 29.22)', zh='+20.71（上限 29.22）'),
    'grid_turing_robot': dict(v=19.80, sign='+', src=('cases/grid_turing_robot.md', '| **16 s of CPU per case** | 4 | **2 OK, 48 TLE, TOTAL `inf` (no score)** | **50 OK, TOTAL 94,092 (19.80)** |'),
        en='+19.80 (was no score)', zh='+19.80（原为无分）'),
    'apple_incremental_game': dict(v=5.04, sign='+', src=('cases/apple_incremental_game.md', '| **20 s of CPU per case** | 4 | **2 OK, 48 TLE, TOTAL 3,955,266 (0.00)** | **50 OK, TOTAL 99,714,418 (5.04)** |'),
        en='+5.04 (was 0)', zh='+5.04（原为 0）'),
    'vibrating_path_graph_coloring': dict(v=2.06, sign='+', src=('cases/vibrating_path_graph_coloring.md', '| **20 s of CPU per case** | 4 | **2 OK, 48 TLE, TOTAL `inf` (no score)** | **50 OK, TOTAL 24,650,014 (2.06)** |'),
        en='+2.06 (was no score)', zh='+2.06（原为无分）'),
    # Broken engines: 4.71-24.40 on the original over four runs each, 0 on the fixed (integration tests fail).
    # The speeds are within run-to-run noise, so this row is not counted in the 10-point headline.
    'exchange_core_throughput': dict(v=24.40, lo=4.71, sign='-', kind='range', src=('cases/exchange_core_throughput.md', 'feeswap scored 7.77–24.40 and dropevents 4.71–15.62 out of 100'),
        en='−4.71 to −24.40 (speed noise)', zh='−4.71 至 −24.40（速度波动）'),
    'college_english_exam_bank': dict(v=100.0, sign='-', src=('cases/college_english_exam_bank.md', '| C: `{"scores": []}` (no rule assessed) | grading failure | valid, **100.0** |'),
        en='−100: empty report', zh='−100：空评分报告'),
    'smt_solver': dict(v=6.21, sign='+', src=('cases/smt_solver.md', "A perfect solver's maximum falls from 78.61 to 72.40, a loss of 6.21 points."),
        en='+6.21 (perfect solver)', zh='+6.21（完美求解器）'),
    'ffmpeg_swscale_reimplementation': dict(v=18.93, sign='-', src=('cases/ffmpeg_swscale_reimplementation.md', '| Variant 2: returns error -3 for 3:1 downscale | 30/30 | **3.2112** | **18.93** |'),
        en='−18.93', zh='−18.93'),
    'dabic_gravity_inversion': dict(v=1.04, sign='+', src=('data/decisions.json', 'good-faith model-space directive 25.77→26.81'),
        en='+1.04 (measured)', zh='+1.04（实测）'),
    'cta_risk_budget_optimization': dict(v=5.00, sign='±', src=('cases/cta_risk_budget_optimization.md', '| leveraged: overseas 45% of NAV, 37.5% of CNY gross | 58.75, `cross_border` 5 | **53.75**, `cross_border` 1 |'),
        en='±5.00 (limit 5)', zh='±5.00（上限 5）'),
    'graph_node_classification': dict(v=24.089, sign='+', src=('repairs/graph_node_classification-v2/paired/results.md', '| neighbor_intkeys | trigger (good faith) | v2.1 | true | 0.240886 | 24.089 |'),
        en='+24.09 (was 0)', zh='+24.09（原为 0）'),
    'tree_block_partitioning': dict(v=4.75, sign='+', src=('cases/tree_block_partitioning.md', 'On the original library it scores 1/10 OK, 9 WA (wrong answer), 0.25 points. On the fixed library it scores 10/10 AC (accepted), 5.00.'),
        en='+4.75 (limit 5)', zh='+4.75（上限 5）'),
    'schemathesis_reporting_observability': dict(v=1.67, sign='-', src=('cases/schemathesis_reporting_observability.md', 'The tested changed versions lose 1.43, 0.83 and 1.67 points.'),
        en='−1.67 (limit 4.76)', zh='−1.67（上限 4.76）'),
    # stdlib_any_year 0.477350 -> 0.467094 = 1.0256 points (2/195 of the total)
    'schemathesis_datagen_pipeline': dict(v=1.03, sign='-', src=('data/decisions.json', 'stdlib_any_year 0.477350/0.467094'),
        en='−1.03 (limit 1.03)', zh='−1.03（上限 1.03）'),
    'schemathesis_config_modernization': dict(v=0.625, sign='-', src=('cases/schemathesis_config_modernization.md', 'at k = 15 that is 1/160, the measured −0.006250'),
        en='−0.625 (limit 0.625)', zh='−0.625（上限 0.625）'),
    'arc_compiler_runtime': dict(v=33.67, sign='', src=('cases/arc_compiler_runtime.md', 'the same correct analyzer scores **69.26** when it returns the array shape the hidden tests use. It scores **35.59** when it keeps the starter'),
        en='33.67 (69.26 vs 35.59)', zh='33.67（69.26 对 35.59）'),
    'juliet_vulnerability_analyzer': dict(v=15.00, sign='+', src=('cases/juliet_vulnerability_analyzer.md', 'An analyzer that finds only the 120 CWE-78 bugs loses 15.00 points (measured: 45.66 against 60.66).'),
        en='+15.00; real run +{real} · limit 26.47', zh='+15.00；真实运行 +{real} · 上限 26.47'),
    # raw 7.031 vs 31.200 on the 0-109 raw scale; out of 100: 6.45 vs 28.62
    'borden_source_inversion': dict(v=22.17, sign='', src=('cases/borden_source_inversion.md', '| grader-convention fit (review, own re-implementation) | good faith | 31.200 | 31.200 | None | 28.62 |'),
        src2=('cases/borden_source_inversion.md', '| textbook ADE fit (review regression case) | good faith, wrong convention | 7.031 | 7.031 | None | 6.45 |'),
        en='22.17 (28.62 vs 6.45)', zh='22.17（28.62 对 6.45）'),
    'triangulation_coloring_optimization': dict(v=48.66, sign='+', src=('cases/triangulation_coloring_optimization.md', '| **20 s of CPU per case** | 4 | **2 OK, 8 TLE, `inf` (no score)** | **2 OK, 8 TLE, `inf`** | 10 OK, 863,058 (48.95) | **10 OK, 874,742 (48.66)** |'),
        en='+48.66 (time-limit part; was no score)', zh='+48.66（时限部分；原为无分）'),
    'portfolio_risk_calibration': dict(v=0.07, sign='+', src=('cases/portfolio_risk_calibration.md', '| 32.45; excess 3.44% | **32.52**; excess 3.47%'),
        en='+0.07', zh='+0.07'),
    'treant_forest': dict(v=13.32, sign='+', src=('cases/treant_forest.md', '| Greedy | fixed | 17960 | 50/50 OK | 0 | 3.04 | 16.36 |'),
        en='+13.32 (3.04 → 16.36)', zh='+13.32（3.04 → 16.36）'),
}
# Values the MEASURED entries derive from, checked exactly.
DERIVED = {
    'rust_multicrate_reconstruction': (Fraction('94.7022') - Fraction('73.9926'), 20.71),
    'dabic_gravity_inversion': (Fraction('26.81') - Fraction('25.77'), 1.04),
    'cta_risk_budget_optimization': (Fraction('58.75') - Fraction('53.75'), 5.00),
    'tree_block_partitioning': (Fraction('5.00') - Fraction('0.25'), 4.75),
    'schemathesis_datagen_pipeline': ((Fraction('0.477350') - Fraction('0.467094')) * 100, 1.03),
    'schemathesis_config_modernization': (Fraction(100, 160), 0.625),
    'arc_compiler_runtime': (Fraction('69.26') - Fraction('35.59'), 33.67),
    'borden_source_inversion': (Fraction('28.62') - Fraction('6.45'), 22.17),
    'portfolio_risk_calibration': (Fraction('32.52') - Fraction('32.45'), 0.07),
    'treant_forest': (Fraction('16.36') - Fraction('3.04'), 13.32),
    'smt_solver': (Fraction('78.61') - Fraction('72.40'), 6.21),
    # D-ABIC, direction column: the grader's own penalty rule at C = 30 (data form 92.92, model form 44.86)
    'dabic_computed_c30': (Fraction('92.92') - Fraction('44.86'), 48.06),
}
# Rows whose only evidence is a direction (no size): a short phrase for the direction column.
DIRECTION = {
    'jagua_nesting_optimization': ('↓ overlaps accepted', '↓ 接受了重叠布局', ('evidence/impact/effects.json', 'down for layouts with overlaps')),
    'openttd_transport_ai': ('↑ up to whole score', '↑ 可达全部分数', ('cases/openttd_transport_ai.md', 'Up to the whole score for a solver that follows the instructions')),
    'git_rewrite_in_zig': ('↑ up to whole score', '↑ 可达全部分数', ('cases/git_rewrite_in_zig.md', 'loses its whole score under the original grader, up to 100 points')),
    'openrct2_theme_park_ai': ('↕ not measured', '↕ 未测量', ('cases/openrct2_theme_park_ai.md', 'This was not measured as a score change.')),
    'triangulation_coloring_optimization': ('+ rule change ↕', '+ 规则变化 ↕', ('evidence/impact/effects.json', 'either: a different flip rule')),
    'warehouse_forklift_routing': ('↑ was no score', '↑ 原为无分', ('cases/warehouse_forklift_routing.md', '| **13 s per test case (uses the promised budget)** | **shows the problem** | **50 TLE → inf** | **50 OK, TOTAL 46676.8** |')),
    # computed from the grader's penalty rule, not measured; the gap is half the score and so grows with C
    'dabic_gravity_inversion': ('computed example: 48.06 at C = 30, grows with C; task removed',
                                '计算示例：C = 30 时为 48.06，随 C 增大；任务已移除',
                                ('cases/dabic_gravity_inversion.md', '| 30 | 1.0 → 92.92 | 0.5 → 44.86 |')),
}
# Labels for rows that show only a limit.
LIMIT_LABEL = {
    'equivalence_class_divide_and_conquer': ('limit 9.67 (down)', '上限 9.67（降低）'),
    'pfr_formalization': ('limit 2.13, not run', '上限 2.13，未实测'),
    'warehouse_forklift_routing': ('limit 30.59', '上限 30.59'),
}
# The headline rule: the problem itself cost a good-faith submission 10 or more points out of 100, measured. Credit wrongly
# given to broken or empty work is shown in the chart but not counted. Arc and Borden count (the same good-faith work loses 33.67 or
# 22.17 points depending on how it is written); Order Addition counts by the score the run keeps.
# Tasks whose 10-point measurement is excluded from the headline count, with the reason.
NOT_COUNTED = {
    'college_english_exam_bank': 'credit given to broken work (an empty grading report scored 100), not points lost by '
                                 'good-faith work; shown in the chart, not counted',
    'ffmpeg_swscale_reimplementation': 'credit given to unfinished work (up to 18.93), not points lost by good-faith work; shown in '
                                       'the chart, not counted',
    'integer_compression_codec': 'the −29.68 comes from the fixed task\'s new 0–100 scale, not from the problem: every '
                                 'submission\'s raw result rose 1.7–4× under the fix',
    'exchange_core_throughput': 'broken engines scored 4.71–24.40 instead of 0, but these speeds are within run-to-run noise '
                                '(the side-by-side run gave 7.77 and about 4.7)',
    'dabic_gravity_inversion': 'the 48.06 (at C = 30; it grows with C) is computed from the grader\'s penalty rule, not '
                               'measured; the measured change is 1.04',
}

T = {
    'en': dict(
        ov_title='In {n10} of {n} tasks with a problem, the problem itself cost good-faith work 10 points or more (measured)',
        ov_sub='What each problem does to one affected submission when it occurs (points out of 100).',
        leg_test='Measured on our test submission', leg_real='Measured on a real agent run',
        leg_bar='Proved or computed limit: the change cannot be larger', leg_comp='Computed from a real run, not run',
        dir_head='Direction only', dir_head2='(size unknown)',
        foot1=('+ / −: the fixed checker gives more / less. No sign: the gap between two good-faith submissions that differ only in '
               'an unstated convention (Arc: error-report format; Borden: physics model); the checker is unchanged.'),
        foot2='How often each problem occurred on the leaderboard is unknown for most tasks.',
        rr_title='A real agent run, regraded: the run\'s score moved in {nk} of {nr} tasks',
        rr_sub='One four-hour Claude Opus 5.5 run per task, regraded with the original and the fixed checker.',
        rr_h1='The run\'s kept score (out of 100)', rr_h2='Largest change for one submission',
        rr_leg_o='original checker', rr_leg_f='fixed checker', rr_leg_c='computed, not run',
        never='problem never occurred', notregr='same grader; needs a new run', zero='0 (scores identical)',
        rr_ranges='Both checkers regraded on our machines; a range is the spread over three gradings.',
        rr_foot='So the problems do reach real agents, though not every time. The run does not measure the effect on the 12-hour leaderboard.',
    ),
    'zh': dict(
        ov_title='在 {n} 个有问题的任务中，有 {n10} 个任务的问题本身让按要求完成的工作实测少得 10 分或更多',
        ov_sub='每个问题发生时，对一份受影响的提交影响多大（满分 100 分）。',
        leg_test='在我们的测试提交上实测', leg_real='在一次真实智能体运行上实测',
        leg_bar='已证明或计算出的上限：变化不会更大', leg_comp='按真实运行计算，未实际运行',
        dir_head='只知道方向', dir_head2='（大小未知）',
        foot1=('+ / −：修复版评分器给分更多 / 更少。无符号：两份按要求完成的提交之间的差距，二者只差在一项未说明的约定上'
               '（Arc：错误报告格式；Borden：物理模型），评分器不变。'),
        foot2='对大多数任务，这些问题在排行榜上发生的频率未知。',
        rr_title='重新评分一次真实智能体运行：{nr} 个任务中有 {nk} 个的运行成绩发生变化',
        rr_sub='每个任务一次四小时的 Claude Opus 5.5 运行，分别用原始评分器和修复版评分器重新评分。',
        rr_h1='运行保留的成绩（满分 100）', rr_h2='单份提交的最大变化',
        rr_leg_o='原始评分器', rr_leg_f='修复版评分器', rr_leg_c='计算所得，未实际运行',
        never='问题从未发生', notregr='评分器不变；需要新的运行', zero='0（分数相同）',
        rr_ranges='两个评分器的分数都是在我们的机器上重新评出的；区间是三次评分的范围。',
        rr_foot='可见这些问题确实会出现在真实智能体身上，但并非每次都出现。这次运行不能衡量对 12 小时排行榜的影响。',
    ),
}
ZH_PCAT = json.loads((ROOT / 'tools/i18n/zh.json').read_text())
EN_PCAT = json.loads((ROOT / 'tools/i18n/en.json').read_text())

STYLE = '''<style>
  .ink{fill:#14212b} .muted{fill:#566773} .rule{stroke:#d3dbe0} .bg{fill:#ffffff}
  .good{fill:#2c7a57} .bad{fill:#ad3528} .warn{fill:#9a6510} .acc{fill:#0f5c78}
  .accS{stroke:#0f5c78} .inkS{stroke:#14212b} .warnS{stroke:#9a6510} .mutedS{stroke:#566773}
  .accBg{fill:#e3eff4} .ioRing{stroke:#ffffff} .ioBand{fill:#eef2f4}
  text{font-family:FONTS}
  @media (prefers-color-scheme: dark){
    .ink{fill:#e2e9ed} .muted{fill:#95a6b1} .rule{stroke:#2a3843} .bg{fill:#152029}
    .good{fill:#6cc79a} .bad{fill:#f08a7c} .warn{fill:#e0a64a} .acc{fill:#6cb6d3}
    .accS{stroke:#6cb6d3} .inkS{stroke:#e2e9ed} .warnS{stroke:#e0a64a} .mutedS{stroke:#95a6b1}
    .accBg{fill:#16303c} .ioRing{stroke:#152029} .ioBand{fill:#1c2a34}
  }
</style>'''
FONTS = {'en': '"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif',
         'zh': '"IBM Plex Sans","Noto Sans SC","Noto Sans CJK SC","PingFang SC","Microsoft YaHei",system-ui,-apple-system,"Segoe UI",sans-serif'}


def esc(s):
    return html.escape(str(s), quote=True)


def text(x, y, s, cls='ink', size=13, anchor='start', weight=400):
    return f'<text x="{x:g}" y="{y:g}" class="{cls}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}">{esc(s)}</text>'


def tw(s, size=13):
    """Rough text width: CJK glyphs are one em, Latin about 0.56 em."""
    return sum(size if ord(c) > 0x2e80 else size * 0.56 for c in s)


def wrap(s, n=28):
    if len(s) <= n:
        return [s]
    words, a = s.split(), ''
    for i, w in enumerate(words):
        if len((a + ' ' + w).strip()) > n:
            return [a, ' '.join(words[i:])]
        a = (a + ' ' + w).strip()
    return [s]


NO_LINE_START = set('，。、；：？！）》」』”’')
NO_LINE_END = set('（《「『“‘')


def wrapw(s, maxw, size=13):
    """Split s into lines no wider than maxw (by the rough width estimate).

    Chinese text breaks between characters, but never before full-width closing punctuation, which stays
    with the character before it, and never inside a run of Latin letters, digits or symbols."""
    cjk = any(ord(c) > 0x2e80 for c in s)
    if cjk:
        units = []
        for c in s:
            if units and (c in NO_LINE_START or units[-1][-1] in NO_LINE_END
                          or (ord(c) <= 0x2e80 and c != ' ' and ord(units[-1][-1]) <= 0x2e80 and units[-1][-1] != ' ')):
                units[-1] += c
            else:
                units.append(c)
    else:
        units = s.split(' ')
    lines, cur = [], ''
    for u in units:
        nxt = cur + u if cjk else (cur + ' ' + u).strip()
        if cur and tw(nxt, size) > maxw:
            lines.append(cur.rstrip())
            cur = u.lstrip()
        else:
            cur = nxt
    return lines + [cur]


def split_label(s):
    """Split a long row label into two lines at its last separator."""
    for sep in (' · ', '; ', '；', '（', ' ('):
        i = s.rfind(sep)
        if i > 0:
            keep = 1 if sep in ('; ', '；') else 0  # a semicolon stays at the end of the first line
            return [s[:i + keep].rstrip(), s[i + keep:].lstrip(' ·;') if sep in (' · ', '; ', '；') else s[i:].lstrip()]
    spaces = [i for i, c in enumerate(s) if c == ' ']
    if spaces:
        i = min(spaces, key=lambda k: abs(k - len(s) / 2))
        return [s[:i], s[i + 1:]]
    return [s]


def diamond(cx, cy, r=6, cls='warn', computed=False):
    d = f'M{cx:g} {cy - r:g}L{cx + r:g} {cy:g}L{cx:g} {cy + r:g}L{cx - r:g} {cy:g}Z'
    if computed:  # computed from a real run's saved verdicts, not run: hollow and dashed
        return f'<path d="{d}" class="bg warnS" stroke-width="1.8" stroke-dasharray="2.5 2"/>'
    return f'<path d="{d}" class="{cls} ioRing" stroke-width="1.5"/>'


def dot(cx, cy, r=5, cls='acc'):
    return f'<circle cx="{cx:g}" cy="{cy:g}" r="{r}" class="{cls} ioRing" stroke-width="1.5"/>'


def find_line(path, needle):
    lines = (ROOT / path).read_text().split('\n')
    hits = [i + 1 for i, l in enumerate(lines) if needle in l]
    if not hits:
        raise SystemExit(f'build_impact_figures: source string not found in {path}: {needle[:80]!r}')
    return f'{path}:{hits[0]}'


# ---------------------------------------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------------------------------------
def load():
    dec = json.loads((ROOT / 'data/decisions.json').read_text())
    eff = json.loads((ROOT / EFFECTS).read_text())
    summ = json.loads((ROOT / SUMMARY).read_text())
    lean = json.loads((ROOT / LEAN).read_text())
    hist = json.loads((ROOT / HIST).read_text())
    return dec, eff, summ, lean, hist


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def real_runs(summ, lean, hist):
    """Per regraded task: kept score, largest per-submission change, counts.

    The kept score is compared like with like: 'orig' is the original checker and 'fixed' the fixed one, both regraded
    on our machines (mean of the gradings, with 'orig_lo'/'orig_hi' and 'fixed_lo'/'fixed_hi' the spread over three
    gradings where the decisive submissions were graded three times). 'recorded' is the score the run itself recorded
    on its own machine; it is mentioned in a note, never plotted against a regrade."""
    out = {}
    for t, v in summ.items():
        ch = []
        for p in v['per']:
            a, b = mean(p['v1']['norm']), mean(p['v2']['norm'])
            if a is not None and b is not None:
                ch.append((b - a, p['round'], a, b))
        big = max(ch, key=lambda c: abs(c[0]))
        out[t] = dict(recorded=v['orig_recorded']['norm'], orig=v['sel_mean']['v1']['norm'],
                      orig_lo=v['sel_min']['v1']['norm'], orig_hi=v['sel_max']['v1']['norm'],
                      fixed_lo=v['sel_min']['v2']['norm'],
                      fixed_hi=v['sel_max']['v2']['norm'], fixed=v['sel_mean']['v2']['norm'],
                      n_history=v['n_history'], n_graded=v['n_graded'], policy=v['policy'],
                      gradings=sum(len(p['v1']['scores']) for p in v['per']),
                      n_changed=sum(1 for c in ch if abs(c[0]) > 1e-9), n_up=sum(1 for c in ch if c[0] > 1e-9),
                      big=big[0], big_round=big[1], big_from=big[2], big_to=big[3], src=SUMMARY)
    g = [r for r in lean if 'v1_score' in r and r['v1_valid']]
    b1 = max(g, key=lambda r: r['v1_score'])
    b2 = max(g, key=lambda r: r['v2_score_derived'])
    big = max(g, key=lambda r: abs(r['v2_score_derived'] - r['v1_score']))
    out['lean_analysis_proofs'] = dict(recorded=100 * b1['v1_score'], orig=100 * b1['v1_score'], fixed=100 * b2['v2_score_derived'],
                                       fixed_lo=None, fixed_hi=None, n_graded=len(g), n_history=len(lean),
                                       big=100 * (big['v2_score_derived'] - big['v1_score']), big_round=big['round'],
                                       computed=True, src=LEAN)
    b = hist['runs']['borden_source_inversion']
    # The grader is unchanged, so the run's answers score the same under both versions; the fix changes the instructions.
    out['borden_source_inversion'] = dict(recorded_raw=b['best_score'], recorded=b['best_score'] * 100 / 109,
                                          orig=b['best_score'] * 100 / 109, fixed=None, n_history=len(b['submissions']),
                                          src=HIST)
    return out


# Classification of the regraded tasks. The defect "never occurred" in a task when no submission changed
# validity and the only differences are timing noise; the case pages and leaderboard page say so:
NEVER = {
    'tree_block_partitioning': ('cases/tree_block_partitioning.md', 'This is timing sensitivity shared by both graders, not the T2 defect'),
    'graph_node_classification': ('cases/graph_node_classification.md', 'none of them shows the problem'),
    'schemathesis_config_modernization': ('tools/site/en/leaderboard.html', 'The defect never occurred: every submission scores the same under both. All 30.'),
}
RR_ORDER = ['order_addition_permutation_optimization', 'integer_compression_codec', 'lean_analysis_proofs',
            'juliet_vulnerability_analyzer', 'molecular_self_assembly', 'tree_block_partitioning',
            'graph_node_classification', 'schemathesis_config_modernization', 'borden_source_inversion']


def build_rows(dec, eff, rr):
    rows = []
    sources = {}
    for r in dec:
        t = r['task_id']
        if r['proposed'] not in PC.PROBLEM:
            continue
        e = eff[t]
        marks, src = [], []
        m = MEASURED.get(t)
        if m:
            src.append(find_line(*m['src']))
            if m.get('src2'):
                src.append(find_line(*m['src2']))
            marks.append(dict(kind=m.get('kind', 'test'), v=m['v'], lo=m.get('lo'), sign=m['sign']))
        if t in DERIVED:
            exact, shown = DERIVED[t]
            assert abs(float(exact) - shown) < 0.005, (t, float(exact), shown)
        # real-run marks
        if t == 'molecular_self_assembly':
            x = rr[t]
            marks.append(dict(kind='real', v=x['big'], sign='+'))
            src.append(f"{SUMMARY} ({x['big_round']}: {x['big_from']:.2f} → {x['big_to']:.2f})")
        if t == 'juliet_vulnerability_analyzer':
            x = rr[t]
            marks.append(dict(kind='real', v=x['big'], sign='+'))
            src.append(f"{SUMMARY} ({x['big_round']}: {x['big_from']:.2f} → {x['big_to']:.2f})")
        if t == 'integer_compression_codec':
            x = rr[t]
            marks.append(dict(kind='real', v=abs(x['big']), sign='-'))
            src.append(f"{SUMMARY} ({x['big_round']}: {x['big_from']:.2f} → {x['big_to']:.2f} on the new scale)")
        if t == 'lean_analysis_proofs':
            x = rr[t]
            marks.append(dict(kind='real', v=x['big'], sign='+', computed=True))
            src.append(f"{LEAN} ({x['big_round']}, computed from saved verdicts)")
        if t == 'order_addition_permutation_optimization':
            x = rr[t]
            marks.append(dict(kind='real', v=x['fixed'] - x['orig'], sign='+', kept=True))
            src.append(f"{SUMMARY} (kept score {x['orig']:.2f} → {x['fixed']:.2f}; each submission's score unchanged)")
        bound = None
        if e['kind'] == 'bounded':
            bound = e.get('bound_up') if e.get('direction') == 'up' and e.get('bound_up') else e['bound']
            if t == 'rust_multicrate_reconstruction':
                bound = e['bound_up']
            src.append(f'{EFFECTS} ({t}: bound {bound})')
        d = DIRECTION.get(t)
        if d:
            src.append(find_line(*d[2]))
        if not marks and bound is None and not d:
            raise SystemExit(f'build_impact_figures: no mark for {t}')
        rows.append(dict(task=t, cat=r['problem_category'], marks=marks, bound=bound, dir=d, kind=e['kind']))
        sources[t] = src
    return rows, sources


def labels(row, rr, lang):
    t = row['task']
    k = 'en' if lang == 'en' else 'zh'
    if t in MEASURED:
        s = MEASURED[t][k]
        if '{real}' in s:
            s = s.replace('{real}', f"{rr[t]['big']:.2f}")
        return s
    if t == 'molecular_self_assembly':
        return f"+{rr[t]['big']:.2f} (real run)" if k == 'en' else f"+{rr[t]['big']:.2f}（真实运行）"
    if t == 'integer_compression_codec':
        v = abs(rr[t]['big'])
        return f'−{v:.2f} (real run, new scale)' if k == 'en' else f'−{v:.2f}（真实运行，新刻度）'
    if t == 'lean_analysis_proofs':
        v = rr[t]['big']
        return f'+{v:.2f} (computed from a real run)' if k == 'en' else f'+{v:.2f}（按真实运行计算）'
    if t == 'order_addition_permutation_optimization':
        x = rr[t]
        v = x['fixed'] - x['orig']
        return (f"+{v:.2f} in the run's kept score" if k == 'en' else f'+{v:.2f}：运行保留的成绩')
    if t in LIMIT_LABEL:
        return LIMIT_LABEL[t][0 if k == 'en' else 1]
    return ''


def size(row):
    vals = [m['v'] for m in row['marks']]
    return max(vals) if vals else (row['bound'] or 0)


def order_rows(rows):
    def key(r):
        tier = 0 if r['marks'] else (1 if r['bound'] is not None else 2)
        return (tier, -size(r))
    return {k: sorted([r for r in rows if r['cat'] == k], key=key) for k in PC.KEYS}


def count10(rows, rr):
    """Tasks that meet the headline rule: one submission's score, two forms of the same work, or the kept score."""
    sub, forms, kept = [], [], []
    for r in rows:
        if r['task'] in NOT_COUNTED:
            continue
        for m in r['marks']:
            if m['v'] >= 10 - 1e-9:
                (kept if m.get('kept') else forms if m['sign'] == '' else sub).append(r['task'])
                break
    return sub, forms, kept


# ---------------------------------------------------------------------------------------------------------
# Figure 1: overview
# ---------------------------------------------------------------------------------------------------------
NX, X0, X1, DX, W = 16, 262, 546, 574, 720


def xs(v):
    return X0 + (X1 - X0) * v / 100


def overview_svg(rows, rr, lang, n10):
    L = T[lang]
    pc = EN_PCAT if lang == 'en' else ZH_PCAT
    grouped = order_rows(rows)
    o = []
    y = 30
    title = L['ov_title'].format(n10=n10, n=len(rows))
    for i, line in enumerate(wrapw(title, W - 2 * NX, 18)):
        o.append(text(NX, y, line, size=18, weight=700))
        y += 24
    o.append(text(NX, y, L['ov_sub'], 'muted', 14))
    # legend
    y += 30
    o.append(dot(NX + 6, y - 4))
    o.append(text(NX + 18, y, L['leg_test']))
    lx = NX + 18 + tw(L['leg_test']) + 26
    o.append(diamond(lx, y - 4))
    o.append(text(lx + 12, y, L['leg_real']))
    y += 22
    o.append(f'<rect x="{NX:g}" y="{y - 10:g}" width="34" height="10" fill="none" class="accS" stroke-width="1.5"/>')
    o.append(text(NX + 42, y, L['leg_bar']))
    lx = NX + 42 + tw(L['leg_bar']) + 26
    o.append(diamond(lx, y - 4, computed=True))
    o.append(text(lx + 12, y, L['leg_comp']))
    # axis
    y += 34
    o.append(text(DX, y - 16, L['dir_head'], 'ink', 13, weight=600))
    o.append(text(DX, y, L['dir_head2'], 'muted', 13))
    for v in (0, 25, 50, 75, 100):
        o.append(text(xs(v), y, str(v), 'muted', 13, 'middle'))
    axis_y = y + 8
    body = []
    y = axis_y + 6
    for k in PC.KEYS:
        rs = grouped[k]
        y += 22
        body.append(f'<rect x="{NX - 6:g}" y="{y - 16:g}" width="{W - 2 * NX + 12:g}" height="22" rx="3" class="ioBand"/>')
        name = pc['pcat.' + k]
        cnt = pc['pcat.count'].replace('{n}', str(len(rs)))
        body.append(text(NX, y, f'{name} · {cnt}', 'ink', 14, weight=600))
        y += 8
        for r in rs:
            nm = wrap(task_names()[r['task']])
            ends = [X0]
            if r['bound'] is not None:
                ends.append(xs(min(r['bound'], 100)))
            ends += [xs(min(m['v'], 100)) for m in r['marks']]
            lab = labels(r, rr, lang)
            right = max(ends) + 9
            # labels stay left of the direction-only column; a long one is split over two lines
            lab_lines = [lab] if not lab or right + tw(lab) <= DX - 10 else split_label(lab)
            dir_lines = wrapw(r['dir'][0 if lang == 'en' else 1], W - DX - 6) if r['dir'] else []
            nl = max(len(nm), len(lab_lines), len(dir_lines))
            h = 22 if nl == 1 else 36 + 15 * (nl - 2)
            cy = y + h / 2
            for i, line in enumerate(nm):
                body.append(text(NX, y + 15 + 15 * i, line, 'ink', 13))
            if r['bound'] is not None:
                bx = xs(min(r['bound'], 100))
                body.append(f'<rect x="{X0:g}" y="{cy - 5:g}" width="{bx - X0:.1f}" height="10" fill="none" class="accS" stroke-width="1.5"/>')
            for m in r['marks']:
                cx = xs(min(m['v'], 100))
                if m['kind'] == 'range':
                    body.append(f'<line x1="{xs(m["lo"]):.1f}" y1="{cy:g}" x2="{cx:.1f}" y2="{cy:g}" class="accS" stroke-width="2"/>')
                    body.append(dot(xs(m['lo']), cy))
                if m['kind'] == 'real':
                    body.append(diamond(cx, cy, computed=m.get('computed', False)))
                else:
                    body.append(dot(cx, cy))
            if lab:
                if right + max(tw(x) for x in lab_lines) <= DX - 10:
                    x0, anchor = right, 'start'
                else:
                    x0, anchor = xs(min(min(m['v'], 100) for m in r['marks'])) - 9, 'end'
                y0 = cy + 4.5 - 7.5 * (len(lab_lines) - 1)
                for i, line in enumerate(lab_lines):
                    body.append(text(x0, y0 + 15 * i, line, 'ink', 13, anchor))
            y0 = cy + 4.5 - 7.5 * (len(dir_lines) - 1)
            for i, line in enumerate(dir_lines):
                body.append(text(DX, y0 + 15 * i, line, 'muted', 13))
            y += h
    bottom = y + 4
    grid = []
    for v in (0, 25, 50, 75, 100):
        grid.append(f'<line x1="{xs(v):.1f}" y1="{axis_y:g}" x2="{xs(v):.1f}" y2="{bottom:g}" class="rule" stroke-width="1"/>')
    grid.append(f'<line x1="{DX - 6:g}" y1="{axis_y:g}" x2="{DX - 6:g}" y2="{bottom:g}" class="rule" stroke-width="1" stroke-dasharray="3 3"/>')
    y = bottom + 22
    fl = wrapw(L['foot1'], W - 2 * NX) + wrapw(L['foot2'], W - 2 * NX)
    foot = [text(NX, y + 19 * i, line, 'muted', 13) for i, line in enumerate(fl)]
    H = y + 19 * (len(fl) - 1) + 8
    return svg_doc(W, H, title, lang, o + grid + body + foot)


def svg_doc(w, h, title, lang, parts):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h:g}" role="img">\n<title>{esc(title)}</title>\n'
            + STYLE.replace('FONTS', FONTS[lang]) + '\n\n' + '\n'.join(parts) + '\n\n</svg>\n')


# ---------------------------------------------------------------------------------------------------------
# Figure 2: real-run strip
# ---------------------------------------------------------------------------------------------------------
P0, P1, Z, SC = 214, 454, 598, 3.0  # panel 1 from P0 to P1 (0-100); panel 2 zero line at Z, SC px per point


def rr_class(t, x):
    if t == 'borden_source_inversion':
        return 'notregr'
    if t in NEVER:
        return 'never'
    if x.get('computed'):
        return 'computed'
    # the kept score changed only if the spreads of the two regrades are clearly apart
    olo, ohi = x.get('orig_lo', x['orig']), x.get('orig_hi', x['orig'])
    flo, fhi = x.get('fixed_lo') or x['fixed'], x.get('fixed_hi') or x['fixed']
    if flo - ohi > 0.5 or olo - fhi > 0.5:
        return 'kept'
    return 'subs'


def rec_note(x, en):
    """The run's own recorded score, when it differs from our regrade on the original checker."""
    r = x['recorded']
    if abs(r - x.get('orig_lo', x['orig'])) < 0.005 and abs(r - x.get('orig_hi', x['orig'])) < 0.005:
        return ''
    r = f'{r:.2f}'.replace('100.00', '100')
    return f'; the run itself recorded {r} on its own machine' if en else f'；该运行在它自己的机器上记录的是 {r}'


def rr_note(t, x, lang):
    en = lang == 'en'
    n = x.get('n_graded')
    if t == 'order_addition_permutation_optimization':
        return (f'Each submission keeps its own score; the fixed checker keeps a later, better one ({n} submissions).' if en else
                f'每份提交自身的分数不变；修复版评分器保留了后来一份更好的提交（{n} 份提交）。')
    if t == 'integer_compression_codec':
        return (f'Raw results rise 1.7–4×; the fixed 0–100 scale lowers the run\'s score{rec_note(x, en)} ({n} submissions).' if en else
                f'原始结果提高 1.7–4 倍；修复后的 0–100 分刻度使运行成绩降低{rec_note(x, en)}（{n} 份提交）。')
    if t == 'lean_analysis_proofs':
        return (f'Computed from the original checker\'s saved verdicts, not run ({n} submissions).' if en else
                f'由原始评分器保存的逐项判定计算得出，未实际运行（{n} 份提交）。')
    if t == 'juliet_vulnerability_analyzer':
        return (f'{x["n_changed"]} of {n} submissions changed; the best one did not.' if en else
                f'{n} 份提交中有 {x["n_changed"]} 份分数变化；最佳提交不变。')
    if t == 'molecular_self_assembly':
        return (f'All {x["n_up"]} graded submissions rose; the kept one was already near the top of the scale{rec_note(x, en)} '
                f'({n} of {x["n_history"]} graded).' if en else
                f'全部 {x["n_up"]} 份受评提交的分数都上升；保留的提交原本已接近刻度顶端{rec_note(x, en)}（{x["n_history"]} 份中评了 {n} 份）。')
    if t == 'tree_block_partitioning':
        return (f'Differences come from timing near the time limit, under both checkers ({n} of {x["n_history"]} graded).' if en else
                f'差异来自接近时限时的计时波动，两个评分器都有（{x["n_history"]} 份中评了 {n} 份）。')
    if t == 'graph_node_classification':
        return (f'The spread is timing noise under both checkers{rec_note(x, en)} ({n} of {x["n_history"]} graded).' if en else
                f'两个评分器下的差异都是计时波动{rec_note(x, en)}（{x["n_history"]} 份中评了 {n} 份）。')
    if t == 'schemathesis_config_modernization':
        return (f'All {n} submissions score the same under both checkers.' if en else
                f'全部 {n} 份提交在两个评分器下得分相同。')
    if t == 'borden_source_inversion':
        return (f'Grader unchanged, so old answers score the same ({x["recorded_raw"]:.2f} raw, {x["orig"]:.2f} out of 100); the fix '
                'changes the instructions, so only new runs can show its effect.' if en else
                f'评分器不变，因此旧答案得分相同（原始结果 {x["recorded_raw"]:.2f}，即 {x["orig"]:.2f} 分，满分 100）；该修复改变的是任务说明，'
                '只有新的运行才能显示它的作用。')
    return ''


def span(lo, hi, mid):
    f = lambda v: f'{v:.2f}'.replace('100.00', '100')  # noqa: E731
    return f'{f(lo)}–{f(hi)}' if lo is not None and hi is not None and abs(hi - lo) > 0.005 else f(mid)


def realruns_svg(rr, lang, nk, nr):
    L = T[lang]
    o = []
    title = L['rr_title'].format(nk=nk, nr=nr)
    y = 30
    for line in wrapw(title, W - 2 * NX, 18):
        o.append(text(NX, y, line, size=18, weight=700))
        y += 24
    o.append(text(NX, y, L['rr_sub'], 'muted', 14))
    y += 28
    o.append(f'<circle cx="{NX + 6}" cy="{y - 4}" r="5" class="bg mutedS" stroke-width="2"/>')
    o.append(text(NX + 18, y, L['rr_leg_o']))
    lx = NX + 18 + tw(L['rr_leg_o']) + 24
    o.append(dot(lx, y - 4))
    o.append(text(lx + 12, y, L['rr_leg_f']))
    lx2 = lx + 12 + tw(L['rr_leg_f']) + 24
    o.append(f'<circle cx="{lx2:g}" cy="{y - 4}" r="5" class="bg accS" stroke-width="2" stroke-dasharray="2 2"/>')
    o.append(text(lx2 + 12, y, L['rr_leg_c']))
    y += 34
    o.append(text(P0, y - 16, L['rr_h1'], 'ink', 13, weight=600))
    o.append(text(Z, y - 16, L['rr_h2'], 'ink', 13, 'middle', 600))
    for v in (0, 50, 100):
        o.append(text(P0 + (P1 - P0) * v / 100, y, str(v), 'muted', 13, 'middle'))
    for v in (-25, 0, 25):
        o.append(text(Z + SC * v, y, f'{v:+d}'.replace('-', '−') if v else '0', 'muted', 13, 'middle'))
    top = y + 8
    body = []
    # vertical spans where grid lines stop, so they do not cross text: all lines (notes), the zero line of the right
    # panel (its labels), and a line of the left panel that a kept-score label crosses (x0, x1, row centre)
    gaps, zgaps, lgaps = [], [], []
    y = top
    px = lambda v: P0 + (P1 - P0) * v / 100  # noqa: E731
    for t in RR_ORDER:
        x = rr[t]
        c = rr_class(t, x)
        nm = wrap(task_names()[t], 26)
        cy = y + 18
        for i, line in enumerate(nm):
            body.append(text(NX, cy + 4.5 + 15 * i - (7 if len(nm) == 2 else 0), line, 'ink', 13, weight=600))
        # panel 1: the kept score, original and fixed checker, both regraded on our machines
        a = x['orig']
        if c == 'notregr':
            body.append(f'<circle cx="{px(a):.1f}" cy="{cy}" r="5" class="bg mutedS" stroke-width="2"/>')
            lab = f'{a:.2f} (raw {x["recorded_raw"]:.2f})' if lang == 'en' else f'{a:.2f}（原始结果 {x["recorded_raw"]:.2f}）'
            body.append(text(px(a) - 10, cy + 4.5, lab, 'ink', 13, 'end'))
            lgaps.append((px(a) - 10 - tw(lab), px(a) - 10, cy))
        else:
            b = x['fixed']
            dash = ' stroke-dasharray="2 2"' if c == 'computed' else ''
            body.append(f'<line x1="{px(a):.1f}" y1="{cy}" x2="{px(b):.1f}" y2="{cy}" class="mutedS" stroke-width="2"/>')
            body.append(f'<circle cx="{px(a):.1f}" cy="{cy}" r="5" class="bg mutedS" stroke-width="2"/>')
            if c == 'computed':
                body.append(f'<circle cx="{px(b):.1f}" cy="{cy}" r="5" class="bg accS" stroke-width="2"{dash}/>')
            else:
                body.append(dot(px(b), cy))
            fa = span(x.get('orig_lo'), x.get('orig_hi'), a)
            fb = span(x.get('fixed_lo'), x.get('fixed_hi'), b)
            lab = f'{fa} → {fb}' if fa != fb or abs(a - b) > 0.005 else f'{fa} = {fb}'
            lo = min(px(a), px(b))
            if max(px(a), px(b)) + 10 + tw(lab) < Z - SC * 30 - 6:
                body.append(text(max(px(a), px(b)) + 10, cy + 4.5, lab, 'ink', 13))
                lgaps.append((max(px(a), px(b)) + 10, max(px(a), px(b)) + 10 + tw(lab), cy))
            else:
                body.append(text(lo - 10, cy + 4.5, lab, 'ink', 13, 'end'))
                lgaps.append((lo - 10 - tw(lab), lo - 10, cy))
        # panel 2
        if c in ('never', 'notregr'):
            body.append(text(Z, cy + 4.5, L[c], 'muted', 13, 'middle'))
            zgaps.append((cy - 9, cy + 8))
        elif t == 'order_addition_permutation_optimization':
            body.append(text(Z, cy + 4.5, L['zero'], 'ink', 13, 'middle'))
            zgaps.append((cy - 9, cy + 8))
        else:
            v = x['big']
            w = SC * min(abs(v), 30)
            xr = Z if v > 0 else Z - w
            dash = ' stroke-dasharray="2 2"' if c == 'computed' else ''
            body.append(f'<rect x="{xr:.1f}" y="{cy - 6}" width="{w:.1f}" height="12" rx="2" class="{"bg accS" if c == "computed" else "acc"}" stroke-width="1.5"{dash}/>')
            s = f'{v:+.2f}'.replace('-', '−')
            if v > 0:
                body.append(text(Z - 6, cy + 4.5, s, 'ink', 13, 'end'))
            else:
                body.append(text(Z + 6, cy + 4.5, s, 'ink', 13))
        notes = wrapw(rr_note(t, x, lang), W - 20 - P0)
        for i, line in enumerate(notes):
            body.append(text(P0, cy + 25 + 17 * i, line, 'muted', 13))
        gaps.append((cy + 12, cy + 30 + 17 * (len(notes) - 1)))
        y += 50 + 17 * (len(notes) - 1)
    bottom = y
    def vline(x, gs, sw):
        out, y0 = [], top
        for g0, g1 in sorted(gs) + [(bottom - 8, bottom - 8)]:
            if g0 > y0:
                out.append(f'<line x1="{x:g}" y1="{y0:g}" x2="{x:g}" y2="{g0:g}" class="rule" stroke-width="{sw}"/>')
            y0 = max(y0, g1)
        return out
    grid = [g for v in (0, 50, 100)
            for g in vline(round(px(v), 1), gaps + [(c - 9, c + 8) for x0, x1, c in lgaps if x0 - 3 <= px(v) <= x1 + 3], 1)]
    grid += vline(Z, gaps + zgaps, 1.5)
    fl = wrapw(L['rr_ranges'], W - 2 * NX) + wrapw(L['rr_foot'], W - 2 * NX)
    foot = [text(NX, bottom + 18 + 18 * i, line, 'muted', 13) for i, line in enumerate(fl)]
    return svg_doc(W, bottom + 26 + 18 * (len(fl) - 1), title, lang, o + grid + body + foot)


# ---------------------------------------------------------------------------------------------------------
# Headline numbers
# ---------------------------------------------------------------------------------------------------------
def outward(lo, hi):
    return math.floor(lo * 100 + 1e-9) / 100, math.ceil(hi * 100 - 1e-9) / 100


def leaderboard(eff):
    rows = {r['model']: r for r in csv.DictReader((ROOT / 'data/impact.csv').open())}
    a, b = rows['Opus 4.8'], rows['GPT-5.5']
    pa, pb = float(a['published_mean']), float(b['published_mean'])
    sa, sb = outward(float(a['scale_low']), float(a['scale_high'])), outward(float(b['scale_low']), float(b['scale_high']))
    ba, bb = outward(float(a['bounded_low']), float(a['bounded_high'])), outward(float(b['bounded_low']), float(b['bounded_high']))
    n_open = sum(1 for e in eff.values() if e['kind'] == 'open')
    assert sa[0] > sb[1], 'scale-only intervals now overlap; rewrite the sentence'
    assert ba[0] <= bb[1], 'documented-limit intervals no longer overlap; rewrite the sentence'
    f = lambda p: f'{p[0]:.2f}–{p[1]:.2f}'  # noqa: E731
    en = (f'On the published leaderboard, Opus 4.8 leads GPT-5.5 by {pa - pb:.1f} points ({pa:.1f} against {pb:.1f}). '
          f'The corrections that can be computed from the public averages keep that order ({f(sa)} against {f(sb)}). '
          f'Adding the per-task limits we documented widens the ranges to {f(ba)} and {f(bb)}. These overlap, so the public '
          f'data can no longer confirm which of the two is ahead. This does not show that they change places; deciding that '
          f'needs the original submissions or new runs. These ranges count the {n_open} effects whose size on the leaderboard is unknown as zero.')
    zh = (f'在已公布的排行榜上，Opus 4.8 以 {pa - pb:.1f} 分领先 GPT-5.5（{pa:.1f} 对 {pb:.1f}）。仅用公开平均分即可计算的修正保持这一顺序'
          f'（{f(sa)} 对 {f(sb)}）。加入我们记录的各任务上限后，区间扩大到 {f(ba)} 和 {f(bb)}，两者重叠，因此仅凭公开数据已无法确认两者中哪个领先。'
          f'这并不表明两者名次互换；要判定这一点，需要原始提交或重新运行。这些区间把 {n_open} 个在排行榜上大小未知的影响计为零。')
    return dict(published={'Opus 4.8': pa, 'GPT-5.5': pb}, scale_only={'Opus 4.8': sa, 'GPT-5.5': sb},
                documented_limits={'Opus 4.8': ba, 'GPT-5.5': bb}, direction_only_counted_as_zero=n_open,
                certified_order=False, rounding='outward to 2 decimals, as in IMPACT.md',
                source='data/impact.csv (scale_low/high, bounded_low/high); IMPACT.md', sentence_en=en, sentence_zh=zh)


def build():
    dec, eff, summ, lean, hist = load()
    rr = real_runs(summ, lean, hist)
    rows, sources = build_rows(dec, eff, rr)
    names = task_names()
    sub10, forms10, kept10 = count10(rows, rr)
    n10 = len(sub10) + len(forms10) + len(kept10)
    prim = PC.by_primary(dec)
    regraded = [t for t in RR_ORDER if t in summ]
    cls = {t: rr_class(t, rr[t]) for t in RR_ORDER}
    kept_changes = [t for t in regraded if cls[t] == 'kept']
    subs_only = [t for t in regraded if cls[t] == 'subs']
    never = [t for t in regraded if cls[t] == 'never']
    for t in never:
        find_line(*NEVER[t])
    out = {}
    out['cases/figures/impact-overview.svg'] = overview_svg(rows, rr, 'en', n10)
    out['cases/figures/zh/impact-overview.svg'] = overview_svg(rows, rr, 'zh', n10)
    out['cases/figures/real-runs.svg'] = realruns_svg(rr, 'en', len(kept_changes), len(regraded))
    out['cases/figures/zh/real-runs.svg'] = realruns_svg(rr, 'zh', len(kept_changes), len(regraded))
    cat_counts = {k: len(prim[k]) for k in PC.KEYS}
    ov = dict(
        alt=(f'A chart with one row for each of the {len(rows)} tasks with a problem, grouped by kind of problem. Each row shows, '
             'on a 0 to 100 axis, the measured change for one affected submission as a filled circle (our test submission) or '
             'a filled diamond (a real agent run; hollow and dashed when computed from a run\'s saved verdicts, not run), and a '
             'proved or computed limit as a hollow bar starting at 0. A separate column on the right lists effects whose '
             'direction is known but whose size is not.'),
        caption=(f'In {n10} of the {len(rows)} tasks with a problem, the problem itself cost good-faith work 10 points or more '
                 'out of 100, measured. Credit wrongly given to broken or empty work (College English, FFmpeg) is shown but not '
                 'counted. For Arc and Borden the figure is the gap between two good-faith submissions that differ only in an '
                 'unstated convention. A change that comes from a fix\'s new scale (Integer Codec) does not count. '
                 'Each row shows what the problem does to one submission when it occurs. Filled marks are measured changes; '
                 'hollow bars are proved or computed limits that the change cannot exceed; the right-hand column lists effects '
                 'whose direction is known but whose size is not. For most tasks we do not know how often the problem occurred '
                 'on the leaderboard.'),
        sources=sources)
    r_or = rr['order_addition_permutation_optimization']
    r_ic = rr['integer_compression_codec']
    r_bo = rr['borden_source_inversion']
    rrj = dict(
        alt=(f'Nine rows, one per fixed task in a third-party Claude Opus 5.5 run. The left panel shows the run\'s kept score '
             'out of 100 under the original checker (hollow circle) and the fixed checker (filled circle), both regraded on our '
             'machines. The right panel shows the largest change for any single submission as a bar from zero, or says that the '
             'problem never occurred or that the grader is unchanged and only a new run can show the fix\'s effect.'),
        caption=(f'We regraded one four-hour Claude Opus 5.5 run, submission by submission, with the original and the fixed '
                 f'checker. The run\'s kept score changed in {len(kept_changes)} of the {len(regraded)} regraded tasks: Order '
                 f'Addition {r_or["orig"]:.2f} → {r_or["fixed"]:.2f}, although no single submission\'s score changed, and '
                 f'Integer Codec {r_ic["orig"]:.2f} → {r_ic["fixed"]:.2f} on the fixed scale (the run itself recorded '
                 f'{r_ic["recorded"]:.2f} on its own machine). Both sides are regrades on our machines. In {len(subs_only)} more '
                 f'tasks single submissions changed by up to {max(abs(rr[t]["big"]) for t in subs_only):.2f} points while the kept '
                 f'score did not, and in {len(never)} the problem never occurred. In Borden Inversion the grader is unchanged, so '
                 f'the run\'s answers score the same ({r_bo["recorded_raw"]:.2f} raw, {r_bo["orig"]:.2f} out of 100); the fix '
                 'changes the instructions, so only new runs can show its effect. It shows that the problems happen to real '
                 'agents, though not every time; it does not measure the effect on the 12-hour leaderboard.'),
        sources={t: rr[t]['src'] for t in RR_ORDER})
    out['cases/figures/impact-overview.json'] = json.dumps(ov, ensure_ascii=False, indent=1) + '\n'
    out['cases/figures/real-runs.json'] = json.dumps(rrj, ensure_ascii=False, indent=1) + '\n'
    # Chinese caption and alt text, kept in tools/i18n/figures.zh.json with the other figures
    big_subs = max(abs(rr[t]['big']) for t in subs_only)
    zh = {
        'impact-overview': dict(
            caption=(f'在 {len(rows)} 个有问题的任务中，有 {n10} 个任务的问题本身让按要求完成的工作实测少得 10 分或更多（满分 100）。'
                     '有错误或空白的工作错误地得到的分数（College English、FFmpeg）画在图中，但不计入。Arc 和 Borden 的数值是两份按要求完成的提交之间的差距，'
                     '二者只差在一项未说明的约定上。修复后的新刻度带来的变化（Integer Codec）不计入。每一行显示问题发生时对一份提交的'
                     '影响：实心标记是实测变化；空心条是已证明或计算出的上限，变化不会超过它；右侧一栏列出只知道方向、不知道大小的影响。对大多数任务，'
                     '我们不知道这些问题在排行榜上发生得有多频繁。'),
            alt=(f'一张图，每个有问题的任务占一行（共 {len(rows)} 行），按问题类别分组。每行在 0 到 100 的横轴上，用实心圆（我们的测试提交）或实心菱形'
                 '（真实智能体运行；按运行保存的判定计算、未实际运行时为空心虚线菱形）表示一份受影响提交的实测变化，用从 0 开始的空心条表示已证明或计算出的上限。右侧单独一栏列出只知道方向、大小未知的影响。')),
        'real-runs': dict(
            caption=(f'我们用原始评分器和修复版评分器逐份重新评分了一次四小时的 Claude Opus 5.5 运行。在可重新评分的 {len(regraded)} 个任务中，'
                     f'有 {len(kept_changes)} 个的运行保留成绩发生变化：Order Addition 从 {r_or["orig"]:.2f} 变为 {r_or["fixed"]:.2f}'
                     f'（但没有任何单份提交的分数变化），Integer Codec 在修复后的刻度上从 {r_ic["orig"]:.2f} 变为 {r_ic["fixed"]:.2f}'
                     f'（该运行在它自己的机器上记录的是 {r_ic["recorded"]:.2f}）。两边都是在我们的机器上重新评分的结果。'
                     f'另有 {len(subs_only)} 个任务中，单份提交的分数最多变化 {big_subs:.2f} 分，而保留的成绩不变；还有 {len(never)} 个任务中问题从未发生。'
                     f'在 Borden Inversion 中评分器没有改变，因此该运行的答案得分相同（原始结果 {r_bo["recorded_raw"]:.2f}，即 {r_bo["orig"]:.2f} 分，满分 100）；'
                     '该修复改变的是任务说明，只有新的运行才能显示它的作用。'
                     '可见这些问题确实会出现在真实智能体身上，但并非每次都出现；这次运行不能衡量对 12 小时排行榜的影响。'),
            alt=(f'{len(RR_ORDER)} 行，每行是第三方 Claude Opus 5.5 运行中的一个已修复任务。左侧面板显示运行保留的成绩（满分 100）：空心圆为原始评分器，'
                 '实心圆为修复版评分器，两者都在我们的机器上重新评分。右侧面板用从零出发的条形显示单份提交的最大变化，或注明问题从未发生，'
                 '或注明评分器不变、只有新的运行才能显示修复的作用。')),
    }
    fz = json.loads((ROOT / FIGZH).read_text())
    fz.update(zh)
    out[FIGZH] = json.dumps(fz, ensure_ascii=False, indent=2) + '\n'
    headline = {
        'generated_by': 'tools/build_impact_figures.py',
        'tasks_examined': len(dec),
        'tasks_with_problem': len(rows),
        'fixed': sum(1 for r in dec if r['proposed'] == 'repair-v2'),
        'removed': sum(1 for r in dec if r['proposed'] == 'exclude'),
        'by_category': cat_counts,
        'measured_change_10_or_more': {
            'count': n10,
            'rule': ('the problem itself cost a good-faith submission 10 or more points out of 100, '
                     'measured on our test submission or a real agent run: in one '
                     'submission\'s score, between two good-faith submissions that differ only in an unstated convention (Arc, '
                     'Borden; the checker is unchanged), or in the score a run keeps (Order Addition). Computed limits, and '
                     'changes that come from a fix\'s new 0–100 scale, do not count'),
            'in_one_submission': {'count': len(sub10), 'tasks': sub10},
            'between_two_forms_of_the_same_work': {'count': len(forms10), 'tasks': forms10},
            'in_the_kept_score_only': {'count': len(kept10), 'tasks': kept10},
            'not_counted': NOT_COUNTED,
        },
        'real_run': {
            'run': 'third-party Claude Opus 5.5, one four-hour run per task (huggingface.co/datasets/adafadaq/edgebench-opus-5-5-xhigh-rollouts)',
            'fixed_tasks_in_run': len(RR_ORDER),
            'regraded_with_both_checkers': len(regraded),
            'submissions_graded': sum(rr[t]['n_graded'] for t in regraded),
            'paired_gradings': sum(rr[t]['gradings'] for t in regraded),
            'kept_score': 'original and fixed checker, both regraded on our machines (mean over the gradings)',
            'kept_score_changes': {t: [round(rr[t]['orig'], 2), round(rr[t]['fixed'], 2)] for t in kept_changes},
            'kept_score_recorded_by_run': {t: round(rr[t]['recorded'], 2) for t in regraded
                                           if abs(rr[t]['recorded'] - rr[t]['orig']) > 0.005},
            'single_submissions_change_kept_score_does_not': {t: round(rr[t]['big'], 2) for t in subs_only},
            'problem_never_occurred': never,
            'computed_not_run': {'lean_analysis_proofs': [round(rr['lean_analysis_proofs']['recorded'], 2),
                                                         round(rr['lean_analysis_proofs']['fixed'], 2)]},
            'grader_unchanged_needs_new_run': {'borden_source_inversion': {
                'raw': round(r_bo['recorded_raw'], 2), 'out_of_100': round(r_bo['orig'], 2)}},
            'largest_single_submission_change': {t: round(rr[t]['big'], 2) for t in RR_ORDER if 'big' in rr[t] and cls[t] not in ('never',)},
            'source': SUMMARY,
        },
        'leaderboard': leaderboard(eff),
        'display_names': {t: names[t] for t in sorted(set(sub10 + forms10 + kept10))},
    }
    out['data/headline.json'] = json.dumps(headline, ensure_ascii=False, indent=1) + '\n'
    return out


def check():
    """Return a list of files that differ from what the data gives (empty when all are current)."""
    bad = []
    for p, s in build().items():
        f = ROOT / p
        if not f.exists() or f.read_text() != s:
            bad.append(f'{p} is stale; run python3 tools/build_impact_figures.py')
    return bad


def main():
    if '--check' in sys.argv:
        bad = check()
        for m in bad:
            print('MISMATCH:', m)
        sys.exit(1 if bad else 0)
    for p, s in build().items():
        f = ROOT / p
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(s)
        print('wrote', p)


if __name__ == '__main__':
    main()
