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
    if not completed(task, run):
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
         'smt_solver': lambda: p_smt(outdir('smt_solver', run, 'smt_solver-v2-paired-b'), outdir('smt_solver', run, 'smt_solver-v2-paired-c')),
         'college_english_exam_bank': lambda: p_college(run), 'graph_node_classification': lambda: p_graph(run),
         'jagua_nesting_optimization': lambda: p_jagua(run), 'order_addition_permutation_optimization': lambda: p_order(run),
         'treant_forest': lambda: p_treant(run), 'lean_analysis_proofs': lambda: p_lean(run), 'openttd_transport_ai': lambda: p_openttd(run)}[task]
    return f()


if __name__ == '__main__':
    task, run = sys.argv[1], int(sys.argv[2])
    for k, v in extract(task, run).items():
        print(k, v)
