#!/usr/bin/env python3
"""Generate FINDINGS.md: defects grouped by how they affect a good-faith solver."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT

GROUPS = [
    ("Correct or honest work is scored below what it deserves",
     "A solver doing what the task asks loses points, or cannot reach the score the scale promises.",
     ["smt_solver", "warehouse_forklift_routing", "borden_source_inversion", "arc_compiler_runtime",
      "lean_analysis_proofs", "order_addition_permutation_optimization", "tree_block_partitioning",
      "dabic_gravity_inversion", "integer_compression_codec", "treant_forest"]),
    ("Incorrect solutions are accepted or rewarded",
     "A plausible wrong solution passes the checks, sometimes scoring higher than a correct one.",
     ["exchange_core_throughput", "ffmpeg_swscale_reimplementation", "jagua_nesting_optimization",
      "triangulation_coloring_optimization", "college_english_exam_bank", "cta_risk_budget_optimization",
      "graph_node_classification", "equivalence_class_divide_and_conquer",
      "schemathesis_reporting_observability", "schemathesis_datagen_pipeline",
      "schemathesis_config_modernization"]),
    ("The task cannot deliver what its prompt promises",
     "The evaluator runs something different from what the solver is told.",
     ["openrct2_theme_park_ai", "openttd_transport_ai"]),
    ("Real but immaterial, or disclosed, issues (retained with a note)",
     "The defect is real but cannot materially change a good-faith solver's reported score, or the task discloses it.",
     ["wireless_electricity_layout", "vibrating_path_graph_coloring", "molecular_self_assembly",
      "portfolio_risk_calibration", "rust_multicrate_reconstruction", "grid_turing_robot",
      "bipedalwalker_locomotion_rl", "vehicle_routing_time_windows", "juliet_vulnerability_analyzer",
      "apple_incremental_game", "ordinal_notation_well_foundedness"]),
    ("Repeatability and environment notes",
     "Scores depend on randomness, host speed or network access that the task does not control.",
     ["nethack_dungeon_agent", "wesnoth_tactical_ai", "ann_vector_search_qps", "dcss_dungeon_ai",
      "new_foundations_consistency", "k12_math_recommendation"]),
]
LABEL = {'retain': 'Retain', 'retain-with-note': 'Retain with note', 'repair-v2': 'Repair (v2)', 'exclude': 'Exclude'}


def main():
    d = {r['task_id']: r for r in json.loads((ROOT / 'decisions.json').read_text())}
    names = {json.loads(f.read_text())['task_id']: json.loads(f.read_text())['name']
             for f in (REPO / 'tasks').glob('*.json')}
    seen = set()
    out = ["# Findings for EdgeBench maintainers", "",
           "Every defect below was checked against the task's original, digest-pinned evaluator, by execution where "
           "feasible; a few rest on source reading or exact arithmetic, as their case pages state (for example the DCSS "
           "missing-morgue rule and the BipedalWalker ceiling). "
           "\"Max effect\" is the largest change to a good-faith solver's score we demonstrated or proved, on "
           "the task's 0–100 scale unless stated; it is not an estimate of historical leaderboard impact. "
           "Each task links to its case page (what we ran, the paired before/after table, limits, and how to "
           "reproduce). Tasks with no defect affecting good-faith solvers are listed at the end.", ""]
    for title, blurb, ids in GROUPS:
        out += [f"## {title}", "", blurb, "", "| Task | Decision | What is wrong | Max effect |", "| --- | --- | --- | --- |"]
        for t in ids:
            r = d[t]; seen.add(t)
            out.append(f"| [{names[t]}](cases/{t}.md) | {LABEL[r['proposed']]} | {r['finding']} | {r.get('max_effect', '')} |")
        out.append("")
    rest = sorted(set(d) - seen, key=lambda t: names[t])
    out += ["## No defect affecting good-faith solvers (some carry usage notes)", "",
            ", ".join(f"[{names[t]}](cases/{t}.md)" for t in rest) + ".", ""]
    (ROOT / 'FINDINGS.md').write_text('\n'.join(out))
    assert len(seen) + len(rest) == 51, (len(seen), len(rest))
    print(len(seen), 'tasks grouped;', len(rest), 'without good-faith defect:', rest)


if __name__ == '__main__':
    main()
