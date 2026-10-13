#!/usr/bin/env python3
"""Extract per-arm v1/v2 results and scores from one paired run's output directory.

extract(task, run) -> dict arm_index -> (v1_result, v2_result, v1_score, v2_score)
arm_index is the 0-based position of the arm among that task's rows in data/paired-results.csv.
run is 1 (published output), 2 or 3 (rep output). The same parser is used for every run.
"""
import csv, glob, gzip, json, os, re, shutil, subprocess, sys
from pathlib import Path

R = Path(__file__).resolve().parents[2]
import os
S = Path(os.environ.get('EBV_REPEAT_WORK', Path(__file__).resolve().parents[2] / '.internal' / 'repeatability-work'))
S.mkdir(parents=True, exist_ok=True)
PY = __import__('os').environ.get('EBV_PYTHON', __import__('sys').executable)
EV = R / 'evidence/runs'

# published job (run 1) per task, and the rep dir base name
JOB = {
    'arc_compiler_runtime': 'arc_compiler_runtime-v2-paired',
    'borden_source_inversion': 'borden_source_inversion-v2-paired-r2',
    'cta_risk_budget_optimization': 'cta_risk_budget_optimization-v2-paired',
    'dabic_gravity_inversion': 'dabic_gravity_inversion-v2-paired',
    'equivalence_class_divide_and_conquer': 'equivalence_class_divide_and_conquer-v2-paired',
    'exchange_core_throughput': 'exchange_core_throughput-v2-paired-b',
    'ffmpeg_swscale_reimplementation': 'ffmpeg_swscale_reimplementation-v2-paired-b',
    'integer_compression_codec': 'integer_compression_codec-v2-paired',
    'schemathesis_config_modernization': 'schemathesis_config_modernization-v2-paired',
    'schemathesis_datagen_pipeline': 'schemathesis_datagen_pipeline-v2-paired-b',
    'schemathesis_reporting_observability': 'schemathesis_reporting_observability-v2-paired',
    'tree_block_partitioning': 'tree_block_partitioning-v2-paired',
    'triangulation_coloring_optimization': 'triangulation-v2-paired',
    'warehouse_forklift_routing': 'warehouse_forklift_routing-v2-paired-b',
    'portfolio_risk_calibration': 'portfolio_risk_calibration-v2-paired',
    'juliet_vulnerability_analyzer': 'juliet_vulnerability_analyzer-v2-paired',
}
INPKG = ['college_english_exam_bank', 'graph_node_classification', 'jagua_nesting_optimization',
         'order_addition_permutation_optimization', 'treant_forest', 'openttd_transport_ai']


def outdir(task, run, job=None):
    if task == 'lean_analysis_proofs':
        return R / 'repairs/lean_analysis_proofs-v2/paired/out' if run == 1 else EV / f'lean_analysis_proofs-v2-paired-rep{run}/result/out'
    if task in INPKG:
        return R / f'repairs/{task}-v2/paired/result/out' if run == 1 else EV / f'{task}-v2-paired-rep{run}/result/out'
    job = job or JOB[task]
    return EV / job / 'result/out' if run == 1 else EV / f'{job}-rep{run}/result/out'


def rd(p):
    p = Path(p)
    if not p.exists() and Path(str(p) + '.gz').exists():  # large rerun logs are stored gzipped
        import gzip
        return gzip.open(str(p) + '.gz', 'rt', errors='replace').read()
    return p.read_text(errors='replace')


def fnum(x):
    try:
        return float(x)
    except Exception:
        return None


def g(x, nd=6):
    """format number compactly"""
    if x is None:
        return ''
    if isinstance(x, str):
        return x
    if x == float('inf'):
        return 'inf'
    return f'{x:.{nd}g}'


# ---------------------------------------------------------------- per task parsers
def p_arc(o):
    rows = {}
    for r in csv.DictReader(open(o / 'summary.csv')):
        m = re.search(r'"valid": (\w+); "score": ([0-9.]+)', r['hidden_line'])
        rows[(r['version'], r['control'])] = (m.group(1), float(m.group(2))) if m else ('no-score', None)
    ctl = ['a_starter', 'b_format_only', 'c_invalid_codegen', 'd_honest_documented', 'e_honest_starter_shape']
    return {i: (rows[('v1', c)][0], rows[('v2', c)][0], rows[('v1', c)][1], rows[('v2', c)][1]) for i, c in enumerate(ctl)}


def p_borden(o):
    t = rd(o / 'summary.txt'); d = {}
    for name, v, ex, rest in re.findall(r'^(\S+) (v[12]) (exit=\d+) (.*)$', t, re.M):
        m = re.search(r'TOTAL_SCORE (\S+)\s*$', rest)
        d[(name, v)] = (ex, fnum(m.group(1)) if m else None)
    arms = ['textbook_fit', 'judgeconv_fit', 'v2_fit', 'baseline_mid', 'truth', 'invalid_oob', 'invalid_missing']
    out = {}
    for i, a in enumerate(arms):
        v1, v2 = d.get((a, 'v1'), ('missing', None)), d.get((a, 'v2'), ('missing', None))
        out[i] = (v1[0], v2[0], v1[1], v2[1])
    return out


def p_cta(o):
    def fixtures(v):
        L = rd(o / f'logs/fixtures-{v}.log').splitlines(); res = {}; lots = None
        for l in L:
            m = re.match(r'\s+GC lots (\d+)', l)
            if m:
                lots = m.group(1); continue
            m = re.match(r'(\S+) .*cost_fx=(\d) -> cross_border (\d+) .*violations(\d+/\d+)', l)
            if m:
                key = m.group(1) + (f':lots{lots}' if m.group(1) == 'B_real_day' else '')
                res.setdefault(key, {})[m.group(2)] = (m.group(4), m.group(3))
        return {k: f"violations {x['0'][0]}; cb {x['0'][1]} / {x['2'][1]}" for k, x in res.items()}
    def refb(v):
        res = {}
        for fx, cb, viol in re.findall(r'reference cost_fx=(\d) -> cross_border (\d+) .*?violations(\d+/\d+)', rd(o / f'logs/refblock-{v}.log')):
            res[fx] = (viol, cb)
        return f"violations {res['0'][0]}; cb {res['0'][1]} / {res['2'][1]}"
    def full(v):
        m = re.search(r'score=(\S+) valid=(\w+) pass_rate=(\S+) metrics=(\{.*\})', rd(o / 'summary_parsed.txt').split(f'fullref-{v}.log:')[1].splitlines()[0])
        return f'score {m.group(1)} valid {m.group(2)} pass_rate {m.group(3)} {m.group(4)}', float(m.group(1))
    f1, f2 = fixtures('v1'), fixtures('v2'); F1, F2 = full('v1'), full('v2')
    keys = ['A_mixed_2CNY_1USD', 'B_real_day:lots8', 'A_ctrl_domestic_only', 'B_real_day:lots2', 'A_ctrl_over_limit_native_too']
    out = {i: (f1.get(k, 'missing'), f2.get(k, 'missing'), None, None) for i, k in enumerate(keys)}
    out[5] = (refb('v1'), refb('v2'), None, None)
    out[6] = (F1[0], F2[0], F1[1], F2[1])
    return out


def p_dabic(o):
    d = {}
    for name, v, rest in re.findall(r'^(\w+) (v[12]) exit=\d+ wall=\d+s (.*)$', rd(o / 'summary.txt'), re.M):
        val = re.search(r'"valid": (\w+)', rest).group(1); sc = float(re.search(r'"score": ([0-9.e-]+)', rest).group(1))
        sf = re.search(r'"structural_failure": (\w+)', rest).group(1)
        d[(name, v)] = (f'valid={val}; structural_failure={sf}', sc)
    arms = ['model', 'data', 'invalid', 'shipped']
    return {i: (d[(a, 'v1')][0], d[(a, 'v2')][0], d[(a, 'v1')][1], d[(a, 'v2')][1]) for i, a in enumerate(arms)}


def p_equiv(o):
    d = {}
    for name, v, raw, pr, pt in re.findall(r'^(\S+)-(v[12])\.log: raw=(\S+) norm=\S+ pass_rate=(\S+) per_task=(\{.*\})', rd(o / 'summary_parsed.txt'), re.M):
        d[(name, v)] = (f'raw {raw}; pass_rate {pr}; {pt}', float(raw))
    arms = ['crafted-B_over_by_n', 'crafted-A_at_limit', 'ref', 'naive']
    return {i: (d[(a, 'v1')][0], d[(a, 'v2')][0], d[(a, 'v1')][1], d[(a, 'v2')][1]) for i, a in enumerate(arms)}


def p_exchange(o):
    seen = {}; d = {}
    for name, v, rest in re.findall(r'^(\w+) (v1raw|v[12]) exit=\d+ wall=\d+s (.*)$', rd(o / 'summary.txt'), re.M):
        key = name if name != 'control' or v == 'v1raw' else None
        if name == 'control' and v != 'v1raw':
            seen[v] = seen.get(v, 0) + 1; key = f'control{seen[v]}'
        m = re.search(r'CASE 0000 (\w+) score=(\d+)', rest)
        gate = 'gate OK; ' if 'GATE OK' in rest else ''
        d[(key, v)] = (gate + (m.group(1) if m else 'no-case'), float(m.group(2)) if m else None)
    def gv(a, v):
        return d.get((a, v), ('—', None))
    out = {0: (gv('control', 'v1raw')[0], '—', gv('control', 'v1raw')[1], None)}
    for i, a in enumerate(['control1', 'control2', 'topo21', 'feeswap', 'dropevents', 'feeleak', 'compileerr'], start=1):
        x, y = gv(a, 'v1'), gv(a, 'v2'); out[i] = (x[0], y[0], x[1], y[1])
    return out


def p_ffmpeg(o):
    d = {}
    for name, v, sc, corr, te in re.findall(r'^(\S+)-(v[12]) score=(\S+) correct=(\S+) speedups=.*? timed_errors=(\[.*?\]) reason', rd(o / 'summary_parsed.txt'), re.M):
        n = 0 if te == '[]' else te.count("('")
        d[(name, v)] = (f'correct {corr}; timed_errors {n}', float(sc))
    arms = ['ref_r1', 'ref_r2', 'scaffold', 'trig_3to1_unsupported', 'trig_3to1_silent_noop', 'trig_rgba_rgb24_unsupported', 'invalid_yuv420p_rgb24_unsupported']
    return {i: (d[(a, 'v1')][0], d[(a, 'v2')][0], d[(a, 'v1')][1], d[(a, 'v2')][1]) for i, a in enumerate(arms)}


def p_integer(o):
    d = {}
    for r, name, v, raw, val, pas in re.findall(r'^(r\d) (\S+) (v[12]) exit=\d+ wall=\d+s raw=(\S+) norm=\S+ status=\S+ valid=(\w+) pass=(\S+)', rd(o / 'summary.txt'), re.M):
        d[(r, v)] = (f'valid={val}; pass {pas}', float(raw))
    rep = {'r1': d.get(('r4', 'v2')), 'r3': d.get(('r5', 'v2'))}
    out = {}
    for i, r in enumerate(['r1', 'r3', 'r2']):
        out[i] = (d[(r, 'v1')][0], d[(r, 'v2')][0], d[(r, 'v1')][1], d[(r, 'v2')][1])
    out['_repeat'] = {k: (x[1] if x else None) for k, x in rep.items()}
    return out


def p_schem(o, task):
    j = json.load(open(o.parent / 'out' / 'summary.json')) if (o / 'summary.json').exists() else None
    if j is None:
        # summary.json is written next to runs/ by summarize.py; rebuild if missing
        subprocess.run([sys.executable, str(o.parent.parent / 'summarize.py'), str(o / 'runs')], capture_output=True)
        j = json.load(open(o / 'summary.json'))
    def sig(x):
        ph = '; '.join(p.split(':')[0] + ':' + p.split(':')[1].split()[0] for p in x['phases'])
        return ph or 'no phases'
    sweep = {}
    if (o / 'extra.log').exists():
        for var, img, fs in re.findall(r'sweep variant=(\S+) image=(v[12]) failing_seeds=(\S+)', rd(o / 'extra.log')):
            sweep[(var, img)] = fs
    arms = {'schemathesis_config_modernization': ['starter', 'identity', 'wrapper', 'no_register'],
            'schemathesis_datagen_pipeline': ['correct', 'stdlib_1900', 'stdlib_any_year', 'independent_fields', 'off_by_one_clock', 'garbage_shape', 'rfc850', 'starter'],
            'schemathesis_reporting_observability': ['fullref', 'fullref_junit_drops_error', 'fullref_no_body_fix', 'fullref_always_suppress', 'stub_junit_correct', 'stub_junit_drops_error', 'starter']}[task]
    out = {}
    for i, a in enumerate(arms):
        x, y = j[a]['v1'], j[a]['v2']
        s1, s2 = sig(x), sig(y)
        if (a, 'v1') in sweep:
            s1 += f'; sweep failing {sweep[(a, "v1")]}'; s2 += f'; sweep failing {sweep[(a, "v2")]}'
        out[i] = (s1, s2, x['score'], y['score'])
    return out


def p_smt(ob, oc):
    def parse(o):
        d = {}
        for arm, v, cls, val in re.findall(r'^(\w+)\s+(v[12]) (multi_context_27|single_context_42|final_score)\s+(.*)$', rd(o / 'summary_parsed.txt'), re.M):
            d.setdefault((arm, v), {})[cls] = val.strip()
        return d
    b, c = parse(ob), parse(oc)
    out = {}
    for i, arm in enumerate(['ground', 'textual', 'textual_true', 'ground_wrong']):
        src = c if arm == 'ground_wrong' else b
        def sig(v):
            x = src[(arm, v)]
            return f"multi27 {x['multi_context_27']}; single42 {x['single_context_42']}", round(float(x['final_score']), 4)
        a1, a2 = sig('v1'), sig('v2')
        out[i] = (a1[0], a2[0], a1[1], a2[1])
    return out


def p_tree(o):
    d = {}
    for name, v, raw, pr, pt in re.findall(r'^(\S+)-(v[12])\.log: raw=(\S+) norm=\S+ pass_rate=(\S+) per_task=(\{.*\})', rd(o / 'summary_parsed.txt'), re.M):
        d[(name, v)] = (f'raw {raw}; {pt}', float(raw))
    arms = ['ref', 'alias', 'invalid']
    return {i: (d[(a, 'v1')][0], d[(a, 'v2')][0], d[(a, 'v1')][1], d[(a, 'v2')][1]) for i, a in enumerate(arms)}


def p_tri(o):
    pkg = R / 'repairs/triangulation_coloring_optimization-v2/paired'
    r = subprocess.run([PY, str(pkg / 'normalize.py'), str(o), str(R / 'tasks/triangulation_coloring_optimization.json')],
                       capture_output=True, text=True, cwd=str(R))
    d = {}
    for l in r.stdout.splitlines():
        x = json.loads(l); d[(x['solution'], x['version'])] = (f"cases_ok {x['cases_ok']}; valid {str(x['valid']).lower()}", x['normalized'])
    if not d:
        raise RuntimeError(r.stderr[-500:])
    arms = ['donothing', 'greedy', 'nonconvex_flip', 'wrong_count']
    return {i: (d[(a, 'v1')][0], d[(a, 'v2')][0], d[(a, 'v1')][1], d[(a, 'v2')][1]) for i, a in enumerate(arms)}


def p_warehouse(o):
    d = {}
    for name, v, ok, tle, wa, re_, tot in re.findall(r'^(\w+) (v[12]) exit=\d+ wall=\d+s OK=(\d+) TLE=(\d+) WA=(\d+) RE=(\d+) TOTAL_SCORE (\S+)', rd(o / 'summary.txt'), re.M):
        d[(name, v)] = (f'OK {ok} TLE {tle} WA {wa} RE {re_}', float(tot))
    arms = ['control', 'one_bug', 'starter', 'time_budget', 'near_limit']
    return {i: (d[(a, 'v1')][0], d[(a, 'v2')][0], d[(a, 'v1')][1], d[(a, 'v2')][1]) for i, a in enumerate(arms)}


def p_portfolio(o):
    """Full-grader arms: TOTAL_SCORE (summary.txt) and the printed excess (score_report.json);
    T rows: excess part and the three-part sum from the installed functions (logs/threshold-v*.log)."""
    tot = {(n, v): fnum(x) for n, v, x in re.findall(r'^(\w+) (v[12]) exit=\d+ cpus=\d+ secs=\d+ TOTAL_SCORE (\S+)', rd(o / 'summary.txt'), re.M)}
    def res(a, v):
        f = o / 'reports' / f'{a}-{v}' / 'score_report.json'
        j = json.load(open(f)) if f.exists() else {}
        x = j.get('calculated_metrics', {}).get('excess_return_annual')
        if x is None:
            m = re.search(r'summary="([^"]*)"', [l for l in rd(o / 'summary_parsed.txt').splitlines() if l.startswith(f'{a}-{v}.log')][0])
            return m.group(1)
        return f'excess {100 * x:.2f}%; excess part {j["scores"]["excess_return"]}'
    out = {}
    for i, a in enumerate(['a_instructions', 'b_grader', 'c_wrong', 'd_starter', 'e_example']):
        out[i] = (res(a, 'v1'), res(a, 'v2'), tot[(a, 'v1')], tot[(a, 'v2')])
    th = {}
    for v in ('v1', 'v2'):
        for l in rd(o / f'logs/threshold-{v}.log').splitlines():
            if l.startswith('{') and '"row"' in l:
                x = json.loads(l)
                th[(x['row'].split()[0], v)] = f"excess part {x['score_excess']:.2f}; three parts {x['score_three_parts']:.4f}"
    for i, r in enumerate(['T1', 'T2', 'T3', 'T4', 'T5'], start=5):
        out[i] = (th[(r, 'v1')], th[(r, 'v2')], None, None)
    return out


def p_juliet(o):
    """summary.md table: score, status/valid, trace quality and rejection reasons per set, arm and version."""
    d = {}
    for l in rd(o / 'summary.md').splitlines():
        c = [x.strip() for x in l.strip().strip('|').split('|')]
        if len(c) == 11 and c[0] in ('hidden', 'public'):
            st, arm, s1, s2, v1, v2, q1, q2, _, r1, r2 = c
            d[(st, arm)] = (f'{v1}; trace {q1}; {r1}', f'{v2}; trace {q2}; {r2}', fnum(s1), fnum(s2))
    arms = [('hidden', a) for a in ['a78_public', 'a78_input', 'a78_wrong', 'r_hidden', 'r_public78', 'r_sinkonly',
                                     'r_wrong78_tr', 'r_wrong78_src', 'starter', 'crash']] \
        + [('public', a) for a in ['a78_public', 'a78_input', 'a78_wrong']]
    return {i: d[k] for i, k in enumerate(arms)}


def graded(task, run):
    """Run the package's own grade.py on this run's result/out in a scratch copy; return (graded.json, stdout)."""
    d = S / 'grade' / f'{task}-run{run}'
    if d.exists():
        shutil.rmtree(d)
    d.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['rsync', '-a', '--exclude', '/paired/result', '--exclude', '/paired/result-*', f'{R}/repairs/{task}-v2/', f'{d}/'], check=True)
    os.symlink(outdir(task, run).parent, d / 'paired/result')
    r = subprocess.run([PY, 'grade.py'], cwd=d / 'paired', capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-800:])
    return json.load(open(d / 'paired/graded.json')), r.stdout


def p_college(run):
    j, _ = graded('college_english_exam_bank', run)
    names = {'A': 'A_complete_one_deduction_each', 'B': 'B_complete_all_zero', 'F': 'F_B_R009_rule_score_only', 'L': 'L_A_without_rule_scores',
             'C': 'C_empty_scores', 'D': 'D_A_minus_R009', 'E': 'E_B_minus_R009', 'G': 'G_B_R009_no_score_no_checkpoints',
             'I': 'I_B_R009_score0_zero_checkpoints', 'H': 'H_no_json', 'J': 'J_incomplete_then_complete', 'K': 'K_nojson_then_complete'}
    order = ['A', 'B', 'F', 'L', 'C', 'D', 'E', 'G', 'I', 'H', 'J', 'K']
    out = {}
    for i, k in enumerate(order):
        x = j[names[k]]
        out[i] = (str(x['v1']['valid']).lower(), str(x['v2']['valid']).lower(), x['v1']['score'], x['v2']['score'])
    return out


def p_graph(run):
    j, _ = graded('graph_node_classification', run)
    out = {}
    for i, m in enumerate(['baseline', 'neighbor', 'nanconf', 'shrink', 'missing_half']):
        a, b = j[f'v1.{m}']['harness'], j[f'v2.{m}']['harness']
        out[i] = (str(a['valid']).lower(), str(b['valid']).lower(), a['score_0_100'] if a['valid'] else None, b['score_0_100'] if b['valid'] else None)
    return out


def p_jagua(run):
    o = outdir('jagua_nesting_optimization', run)
    def wit(v):
        d = {}
        for name, ok, why in re.findall(r"^(\S+) \((True|False), '([^']*)'", rd(o / f'witnesses_{v}.txt'), re.M):
            d[name] = 'accept' if ok == 'True' else f'reject {why}'
        return d
    w1, w2 = wit('v1'), wit('v2')
    out = {}
    for i, n in enumerate(['valid_adjacent_squares', 'coincident_squares', 'half_slid_squares', 'rect_inside_square', 'triangle_inside_square',
                           'diamond_inside_square', 'diag_shift_squares', 'tiny_overlap_1e-6', 'forbidden_rotation_90', 'allowed_rotation_minus180']):
        out[i] = (w1.get(n, 'missing'), w2.get(n, 'missing'), None, None)
    j, _ = graded('jagua_nesting_optimization', run)
    for i, m in enumerate(['baseline', 'seed_shift', 'drop_last_item'], start=10):
        def sig(v):
            cs = j[f'{v}.{m}']['cases']; c = {k: sum(1 for l in cs if l.split()[2] == k) for k in ('OK', 'WA', 'RE')}
            h = j[f'{v}.{m}']['harness']
            return f"valid {str(h['valid']).lower()}; {c['OK']} / {c['WA']} / {c['RE']}", h['score']
        a, b = sig('v1'), sig('v2'); out[i] = (a[0], b[0], a[1], b[1])
    return out


def p_order(run):
    j, stdout = graded('order_addition_permutation_optimization', run)
    out = {}
    for i, m in enumerate(['identity', 'search', 'badcost', 'dup']):
        a, b = j['v1'][m], j['v2'][m]
        out[i] = (f"{a['passed']}/{a['total_tests']}", f"{b['passed']}/{b['total_tests']}", a['score'], b['score'])
    hist = {}
    for h, v, br, bs in re.findall(r"^history (\[.*?\]) (v[12]) \(\w+\): best_round=(\S+) best_score=(\S+)", stdout, re.M):
        hist[(h, v)] = (br, fnum(bs))
    for i, h in enumerate(["['identity', 'search']", "['search', 'identity']", "['dup', 'identity', 'search']", "['badcost', 'identity', 'search']"], start=4):
        a, b = hist[(h, 'v1')], hist[(h, 'v2')]
        out[i] = (f'best {a[0]}', f'best {b[0]}', a[1], b[1])
    return out


def p_treant(run):
    o = outdir('treant_forest', run)
    pkg = R / 'repairs/treant_forest-v2/paired'
    cases = S / 'mat/treant_forest-v2'  # cases dir is only needed for the cap; use v1-image cases if present
    r = subprocess.run([PY, str(Path(__file__).resolve().parent / 'treant_normalize.py'), str(S / 'treant_cases'), str(o)], capture_output=True, text=True, cwd=str(R))
    d = {}
    for l in r.stdout.splitlines():
        x = json.loads(l)
        if 'sub' in x:
            d[(x['sub'], x['image'])] = x
    if not d:
        raise RuntimeError(r.stderr[-800:])
    out = {}
    for i, s in enumerate(['baseline', 'honest_greedy', 'invalid_revealed']):
        a, b = d[(s, 'v1')], d[(s, 'v2')]
        out[i] = (f"{a['cases_ok']} {'/'.join(a['case_statuses'])}; raw {a['raw']}", f"{b['cases_ok']} {'/'.join(b['case_statuses'])}; raw {b['raw']}", round(a['v1_norm'], 2), round(b['v2_norm'], 2))
    out[3] = ('derived (no execution)', 'derived (no execution)', None, None)
    return out


def p_lean(run):
    o = outdir('lean_analysis_proofs', run)
    def rep(v, var):
        p = o / f'report_{v}_{var}.json.gz'
        if not p.exists():
            p2 = o / f'report_{v}_{var}.json'
            if not p2.exists():
                return ('not run in this harness', None) if run == 1 else None
            t = p2.read_text()
        else:
            t = gzip.open(p, 'rt').read()
        if '"lake_build_rc"' in t and 'Structured' not in t:
            return (f"lake build rc={json.loads(t)['lake_build_rc']}; no score", None)
        s = t.split('>>>>> Start Structured Result')[-1].split('>>>>> End Structured Result')[0]
        j = json.loads(s)
        m = re.search(r'repaired=(\d+/\d+)', j['summary']); tc = re.search(r'type_changed=(\d+)', j['summary'])
        return (f"repaired {m.group(1)}" + (f"; type_changed {tc.group(1)}" if tc else ''), round(j['score'], 6))
    out = {}
    for i, var in enumerate(['orig', 'A', 'BAD', 'T', 'S', 'W']):
        a, b = rep('v1', var), rep('v2', var)
        if a is None or b is None:
            continue
        out[i] = (a[0], b[0], a[1], b[1])
    return out


def p_openttd(run):
    o = outdir('openttd_transport_ai', run)
    def died(v):
        t = rd(o / v / 'diag.txt')
        m = re.search(r'main\.nut line \[(\d+)\]', t)
        dead = 'script died unexpectedly' in t.lower() or 'made an error' in t
        return f'died at main.nut line {m.group(1)}' if (dead and m) else ('died' if dead else 'no')
    def score(v):
        m = re.search(r'^TOTAL_SCORE (\S+)', rd(o / v / 'eval.txt'), re.M)
        return fnum(m.group(1)) if m else None
    out = {0: (died('baseline_v1'), died('baseline_v2'), score('baseline_v1'), score('baseline_v2'))}
    for i, v in enumerate(['baseline_v1', 'probe_min', 'baseline_v2', 'probe_value'], start=1):
        # single judge image: the same measurement stands for both columns
        out[i] = (died(v), died(v), score(v), score(v))
    return out


# ---------------------------------------------------------------- arms added 2026-10-12 (one row = one arm)
# Each spec gives, per version, (job, label or [labels], parser). Run k of an arm reads job (k = 1),
# job-rep2 or job-rep3. Arms whose jobs were not repeated simply have fewer runs.
def _games(o):
    d = {}
    for lab, ok, tle, wa, re_, tot in re.findall(r'^(\S+) cpus=\d+ ver=\S+ sol=\S+ exit=\d+ wall=\S+ OK=(\d+) TLE=(\d+) WA=(\d+) RE=(\d+)(?: TOTAL_SCORE (\S+))?', rd(o / 'summary.txt'), re.M):
        d[lab] = (f'OK {ok} TLE {tle} WA {wa} RE {re_}' + ('' if tot else '; no TOTAL'), fnum(tot) if tot else None)
    return d


def _smtcpu(o):
    d = {}
    for lab, verd, fs in re.findall(r'^(\S+) cpus=\d+ ver=\S+ sol=\S+ exit=\d+ wall=\S+ eval_rc=\d+ parallel=\d+ verdicts=(\{.*?\}) final_score=(\S+)', rd(o / 'summary.txt'), re.M):
        d[lab] = (f'verdicts {verd}', round(float(fs), 6))
    return d


def _git(o):
    d = {}
    for name, v, br, tot in re.findall(r'^(\w+) (v[12]) rc=\d+ wall=\d+s \S+=\[(.*?)\] TOTAL_SCORE (\S+)', rd(o / 'summary.txt'), re.M):
        d[f'{name}-{v}'] = (f'[{br.strip()}]', float(tot))
    return d


def _pfr(o):
    d = {}
    for f in sorted(o.glob('report_v*_*.json')):
        v, var = re.match(r'report_(v[12])_(\w+)\.json', f.name).groups()
        t = rd(f).split('>>>>> Start Structured Result')[-1].split('>>>>> End Structured Result')[0]
        j = json.loads(t[t.index('{'):t.rindex('}') + 1]) if '{' in t else {}
        lst = rd(o / f'listdecl_{v}_{var}.txt')
        st = {n: s for s, n in re.findall(r'^(OK|BAD) (ebv_\w+|app_ent_PFR) :', lst, re.M)}
        m = re.search(r'repaired=(\d+/\d+)', j.get('summary', ''))
        d[f'{var}-{v}'] = (f"valid {str(j.get('valid')).lower()}; repaired {m.group(1) if m else '?'}; "
                           + ', '.join(f'{n} {st[n]}' for n in sorted(st)), j.get('score'))
    return d


def _rust(o):
    d = {}
    for img in ('orig', 'v2'):
        f = o / img / 'score-results.json'
        if not f.exists():
            continue
        j = json.load(open(f))
        cr = '; '.join(f"{c.get('crate_name', k)} {c.get('passed')}/{c.get('total')} {c.get('status')}"
                       for k, c in (sorted(j['crates'].items()) if isinstance(j['crates'], dict) else enumerate(j['crates'])))
        d[img] = (f"{j['score_status']}; passed {j['raw_passed']}/{j['raw_total']}; {cr}", float(j['total_score']))
    return d


WH = 'warehouse_forklift_routing-v2-cpu4-'
VIB = 'vibrating_path_graph_coloring-v2-paired-'
GAMES6 = [('c4-base', 'c4-base'), ('c4-cpu20', None), ('c4-cpu28', None), ('c4-wall25', None), ('c4-spin40', None), ('c8-cpu20', None)]


def _pair(job, a, b=None, parser=_games, job2=None):
    return ((job, a, parser), (job2 or job, b if b is not None else a.replace('-v1', '-v2'), parser))


MULTI = {
    'git_rewrite_in_zig': [_pair('git_rewrite_in_zig-v2-paired-gates-b', f'{n}-v1', parser=_git) for n in
                           ['control', 'zig_build_exe', 'obj_only', 'elf_only', 'exec_git', 'exec_git_helper']]
    + [_pair('git_rewrite_in_zig-v2-paired-oracle-b', 'oracle-v1', parser=_git),
       _pair('git_rewrite_in_zig-v2-paired-gates-b', 'bad_wrap_cgit-v1', parser=_git)]
    + [_pair('git_rewrite_in_zig-v2-paired-oracle-b', f'{n}-v1', parser=_git) for n in ['bad_shell_git', 'bad_shell_git_oneline']],
    'pfr_formalization': [(('pfr_formalization-v2-paired-v1', f'{n}-v1', _pfr), ('pfr_formalization-v2-paired-v2', f'{n}-v2', _pfr))
                          for n in ['starter', 'T', 'D', 'BAD']],
    'rust_multicrate_reconstruction': [((f'rust_multicrate_reconstruction-v2-paired-r2-{s}', 'orig', _rust),
                                        (f'rust_multicrate_reconstruction-v2-paired-r2-{s}', 'v2', _rust))
                                       for s in ['starter', 'reference', 'partial', 'bad']],
    'grid_turing_robot': [_pair('grid_turing_robot-v2-paired', f'{n}-v1') for n in
                          ['c4-baseline', 'c4-cpu12', 'c4-cpu16', 'c4-cpu28', 'c4-wall25', 'c4-spin40', 'c8-cpu20']],
    'molecular_self_assembly': [_pair('molecular_self_assembly-v2-paired', f'{n}-v1') for n in
                                ['c4-baseline', 'c4-cpu12', 'c4-cpu16', 'c4-cpu28', 'c4-wall25', 'c4-spin40', 'c8-cpu20']],
    'apple_incremental_game': [_pair('apple_incremental_game-v2-paired', f'{n}-v1') for n in
                               ['c4-base', 'c4-cpu20', 'c4-cpu28', 'c4-wall25', 'c4-spin40', 'c8-cpu20']],
    'vibrating_path_graph_coloring': [_pair(VIB + 'a', f'{n}-v1') for n in ['c4-base', 'c4-cpu20', 'c4-cpu28']]
    + [_pair(VIB + 'b', 'c4-wall25-v1'),
       ((VIB + 'c', ['c4-wall25-v1-r1', 'c4-wall25-v1-r2'], _games), (VIB + 'c', 'c4-wall25-v2', _games))]
    + [_pair(VIB + 'b', f'{n}-v1') for n in ['c4-spin40', 'c8-cpu20']],
    'triangulation_coloring_optimization': [_pair('triangulation-v2-paired-cpu', f'{n}-v1') for n in
                                            ['c4-base', 'c4-cpu20', 'c4-cpu28', 'c4-wall25', 'c4-spin40', 'c8-cpu20']],
    'warehouse_forklift_routing': [_pair(WH + 'b', 'c4-cpu80-v1'),
                                   ((WH + 'c', 'c4-cpu140-v1', _games), (WH + 'a', 'c4-cpu140-v2', _games))],
}
# rows of data/paired-results.csv that come before the MULTI rows (handled by the per-task parsers above)
MULTI_OFFSET = {'triangulation_coloring_optimization': 4, 'warehouse_forklift_routing': 5}


# rows of data/paired-results.csv that are not counted as fix repeats (index -> reason)
NOT_COUNTED = {'smt_solver': {i: 'CPU-quota cap arm; that part of the SMT fix was withdrawn (the official configs give SMT 16 grader CPUs), so these single-run measurements are not counted as fix repeats' for i in range(4, 11)}}


def job_out(job, run):
    o = EV / (job if run == 1 else f'{job}-rep{run}') / 'result'
    w = o / 'worker.json'
    if run > 1 and not (w.exists() and json.load(open(w)).get('status') == 'exit=0' and (o / 'out').is_dir()):
        return None
    return o / 'out' if (o / 'out').is_dir() else None


def extract_multi(task, run):
    out, cache = {}, {}
    for i, spec in enumerate(MULTI[task], start=MULTI_OFFSET.get(task, 0)):
        vals = []
        for job, lab, parser in spec:
            o = job_out(job, run)
            if o is None:
                break
            key = (job, parser.__name__)
            if key not in cache:
                cache[key] = parser(o)
            d = cache[key]
            labs = lab if isinstance(lab, list) else [lab]
            if not all(l in d for l in labs):
                break
            vals.append((' | '.join(d[l][0] for l in labs), d[labs[0]][1] if len(labs) == 1 else
                         (d[labs[0]][1] if len({d[l][1] for l in labs}) == 1 else None)))
        if len(vals) == 2:
            out[i] = (vals[0][0], vals[1][0], vals[0][1], vals[1][1])
    if not out:
        raise RuntimeError(f'run {run}: no MULTI arm collected')
    return out


# ---------------------------------------------------------------- supplementary jobs (not rows of paired-results.csv)
# Each returns {label: (result, score)} for one run's result/out; build_report compares the labels across runs.
def _x_games(o):
    return _games(o)


def _x_tri_controls(o):
    d = {}
    for c in ('c8', 'c4'):
        x = p_tri(o / c)
        for i, s in enumerate(['donothing', 'greedy', 'nonconvex_flip', 'wrong_count']):
            d[f'{c} {s} v1'] = (x[i][0], x[i][2]); d[f'{c} {s} v2'] = (x[i][1], x[i][3])
    return d


def _x_smt_lines(o):
    d = {}
    for l in rd(o / 'summary_parsed.txt').splitlines():
        k = l.split()
        if len(k) >= 3:
            d[' '.join(k[:3])] = (' '.join(k[3:]), None)
    return d


def _x_exchange(o):
    d, seen = {}, {}
    for name, v, rest in re.findall(r'^(\w+) (v[12]) exit=\d+ wall=\d+s (.*)$', rd(o / 'summary.txt'), re.M):
        seen[(name, v)] = seen.get((name, v), 0) + 1
        m = re.search(r'CASE 0000 (\w+) score=(\d+)', rest)
        sig = ('gate OK; ' if 'GATE OK' in rest else ('gate failed; ' if 'gate failed' in rest else '')) + (m.group(1) if m else 'no-case')
        d[f'{name}#{seen[(name, v)]} {v}'] = (sig, float(m.group(2)) if m else None)
    return d


def _x_arc(o):
    d = {}
    for r in csv.DictReader(open(o / 'summary.csv')):
        j = json.loads(r['structured'].replace(';', ',')) if r['structured'].startswith('{') else {}
        d[r['arm']] = (f"docker_exit {r['docker_exit']}; valid {str(j.get('valid')).lower()}; passed {j.get('passed')}; runner_rc {j.get('runner_returncode')}", j.get('score'))
    return d


def _x_borden(o):
    d = {}
    for name, v, ex, rest in re.findall(r'^(\S+) (v2prev|v[12]) (exit=\d+) (.*)$', rd(o / 'summary.txt'), re.M):
        m = re.search(r'TOTAL_SCORE (\S+)\s*$', rest)
        d[f'{name} {v}'] = (ex, fnum(m.group(1)) if m else None)
    return d


def _x_college(o):
    job = o.parent.parent
    src = EV / 'college_english_exam_bank-v2-paired-multiblock'
    r = subprocess.run([PY, 'grade.py', str(o)], cwd=src, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-500:])
    g = json.load(open(job / 'graded.json'))
    return {f'{n} {v}': (f"valid {str(x['valid']).lower()}", x['score']) for n, a in g.items() for v, x in a.items()}


def _x_schem(o):
    j = json.load(open(o / 'summary.json'))
    sig = lambda x: '; '.join(p.split(':')[0] + ':' + p.split(':')[1].split()[0] for p in x['phases']) or 'no phases'
    return {f'{a} {v}': (sig(x[v]), x[v]['score']) for a, x in j.items() for v in ('v1', 'v2')}


EXTRA = [  # (task, job, what it adds, parser)
    ('schemathesis_reporting_observability', 'schemathesis_reporting_observability-v2-paired-rev2', 'revised fixed version, all arms incl. the added other-suite and unterminated arms', _x_schem),
    ('warehouse_forklift_routing', 'warehouse_forklift_routing-v2-cpu4-a', 'cpu140 at 4 CPUs (fixed and earlier fixed version)', _x_games),
    ('warehouse_forklift_routing', 'warehouse_forklift_routing-v2-cpu4-b', 'cpu80 at 4 CPUs (all three versions)', _x_games),
    ('warehouse_forklift_routing', 'warehouse_forklift_routing-v2-cpu4-c', 'earlier controls at 4 CPUs; cpu80 at 8 CPUs; cpu140 original', _x_games),
    ('warehouse_forklift_routing', 'warehouse_forklift_routing-v2-cpu4-d', 'near-limit control at 4 CPUs', _x_games),
    ('triangulation_coloring_optimization', 'triangulation-v2-paired-cpu', 'CPU arms incl. earlier fixed version', _x_games),
    ('triangulation_coloring_optimization', 'triangulation-v2-paired-cpu-controls', 'flip-rule controls vs the current fixed version, 8 and 4 CPUs', _x_tri_controls),
    ('vibrating_path_graph_coloring', 'vibrating_path_graph_coloring-v2-paired-c', 'wall25 with tester-start logging', _x_games),
    ('exchange_core_throughput', 'exchange_core_throughput-v2-paired-shutdownfail', 'shutdown-failure triggers', _x_exchange),
    ('college_english_exam_bank', 'college_english_exam_bank-v2-paired-multiblock', 'multi-block responses (v1, earlier fixed, fixed)', _x_college),
    ('arc_compiler_runtime', 'arc_compiler_runtime-hang-suite', 'one hidden suite hangs (original grader only)', _x_arc),
    ('borden_source_inversion', 'borden_source_inversion-v2-paired-r3', 'controls vs v1, earlier fixed and fixed work image', _x_borden),
    ('rust_multicrate_reconstruction', 'rust_multicrate_reconstruction-v2-paired-r2-reference', 'reference (original, + cc files, fixed)', None),
]


def _x_rust(o):
    d = {}
    for line in rd(o / 'summary.txt').splitlines():
        m = re.match(r'^(\w+) exit=(\d+) wall=\d+s RAW_PASSED=(\d+) SCORE=(\S+) SCORE_STATUS=(\S+)', line)
        if m:
            d[m.group(1)] = (f'exit {m.group(2)}; passed {m.group(3)}; {m.group(5)}', float(m.group(4)))
    return d


EXTRA = [e if e[3] else (e[0], e[1], e[2], _x_rust) for e in EXTRA if not e[1].startswith('rust')] + [
    ('rust_multicrate_reconstruction', f'rust_multicrate_reconstruction-v2-paired-r2-{s}', f'{s}: original, original + cc files, fixed', _x_rust)
    for s in ('reference', 'partial', 'bad')]


def extract_extra(job, parser, run):
    o = job_out(job, run)
    if o is None:
        raise RuntimeError(f'run {run} not completed')
    return parser(o)


def completed(task, run):
    """rep runs count only when worker.json says exit=0 and result/out exists (lean: local.txt exit=0)"""
    if run == 1:
        return True
    if task == 'lean_analysis_proofs':
        p = EV / f'lean_analysis_proofs-v2-paired-rep{run}/result/local.txt'
        return p.exists() and 'exit=0' in p.read_text()
    jobs = ['smt_solver-v2-paired-b', 'smt_solver-v2-paired-c'] if task == 'smt_solver' else [None]
    for j in jobs:
        o = outdir(task, run, j)
        w = o.parent / 'worker.json'
        if not (o.is_dir() and w.exists() and json.load(open(w)).get('status') == 'exit=0'):
            return False
    return True


def extract(task, run):
    if task in MULTI and task not in JOB and task not in ('smt_solver',):
        return extract_multi(task, run)
    base = {}
    if task in MULTI_OFFSET:
        try:
            base = extract_multi(task, run)
        except RuntimeError:
            base = {}
    if not completed(task, run):
        if base:
            return base
        raise RuntimeError(f'run {run} not completed')
    if task in JOB:
        o = outdir(task, run)
    f = {'arc_compiler_runtime': lambda: p_arc(o), 'borden_source_inversion': lambda: p_borden(o),
         'cta_risk_budget_optimization': lambda: p_cta(o), 'dabic_gravity_inversion': lambda: p_dabic(o),
         'equivalence_class_divide_and_conquer': lambda: p_equiv(o), 'exchange_core_throughput': lambda: p_exchange(o),
         'ffmpeg_swscale_reimplementation': lambda: p_ffmpeg(o), 'integer_compression_codec': lambda: p_integer(o),
         'schemathesis_config_modernization': lambda: p_schem(o, task), 'schemathesis_datagen_pipeline': lambda: p_schem(o, task),
         'schemathesis_reporting_observability': lambda: p_schem(o, task), 'tree_block_partitioning': lambda: p_tree(o),
         'triangulation_coloring_optimization': lambda: p_tri(o), 'warehouse_forklift_routing': lambda: p_warehouse(o),
         'portfolio_risk_calibration': lambda: p_portfolio(o), 'juliet_vulnerability_analyzer': lambda: p_juliet(o),
         'smt_solver': lambda: p_smt(outdir('smt_solver', run, 'smt_solver-v2-paired-b'), outdir('smt_solver', run, 'smt_solver-v2-paired-c')),
         'college_english_exam_bank': lambda: p_college(run), 'graph_node_classification': lambda: p_graph(run),
         'jagua_nesting_optimization': lambda: p_jagua(run), 'order_addition_permutation_optimization': lambda: p_order(run),
         'treant_forest': lambda: p_treant(run), 'lean_analysis_proofs': lambda: p_lean(run), 'openttd_transport_ai': lambda: p_openttd(run)}[task]
    r = f()
    r.update(base)
    return r


if __name__ == '__main__':
    task, run = sys.argv[1], int(sys.argv[2])
    for k, v in extract(task, run).items():
        print(k, v)
