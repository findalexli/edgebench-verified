"""Display names for the 51 tasks. EdgeBench's own names are title-cased task ids ("Smt Solver");
these restore acronyms and proper names. Anything not listed uses EdgeBench's name."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = {
    'ann_vector_search_qps': 'ANN Vector Search QPS',
    'arc_compiler_runtime': 'Arc Compiler Runtime',
    'bipedalwalker_locomotion_rl': 'BipedalWalker Locomotion RL',
    'cta_risk_budget_optimization': 'CTA Risk Budget Optimization',
    'dabic_gravity_inversion': 'D-ABIC Gravity Inversion',
    'dcss_dungeon_ai': 'DCSS Dungeon AI',
    'equivalence_class_divide_and_conquer': 'Equivalence Class Divide and Conquer',
    'ffmpeg_swscale_reimplementation': 'FFmpeg swscale Reimplementation',
    'flt_regular_formalization': 'FLT Regular Formalization',
    'git_rewrite_in_zig': 'Git Rewrite in Zig',
    'k12_math_recommendation': 'K-12 Math Recommendation',
    'nethack_dungeon_agent': 'NetHack Dungeon Agent',
    'openrct2_theme_park_ai': 'OpenRCT2 Theme Park AI',
    'openttd_transport_ai': 'OpenTTD Transport AI',
    'ordinal_notation_well_foundedness': 'Ordinal Notation Well-Foundedness',
    'pfr_formalization': 'PFR Formalization',
    'schemathesis_config_modernization': 'Schemathesis Config Modernization',
    'smt_solver': 'SMT Solver',
    'vliw_kernel_optimization': 'VLIW Kernel Optimization',
    'wesnoth_tactical_ai': 'Wesnoth Tactical AI',
}


def names():
    out = {}
    for f in (ROOT / 'tasks').glob('*.json'):
        t = json.loads(f.read_text())
        out[t['task_id']] = OVERRIDES.get(t['task_id'], t['name'])
    return out
