#!/usr/bin/env python3
"""Generate FINDINGS.md: every task, grouped by what goes wrong, in plain language (from cases/plain.json)."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from names import names as task_names  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

GROUPS = [
    ("Correct work is scored too low",
     "An agent that does what the task asks loses points it should have earned.",
     ["smt_solver", "borden_source_inversion", "arc_compiler_runtime", "lean_analysis_proofs", "pfr_formalization",
      "tree_block_partitioning", "git_rewrite_in_zig", "rust_multicrate_reconstruction",
      "juliet_vulnerability_analyzer"]),
    ("Wrong work is accepted",
     "A plausible but incorrect submission passes the grader's checks, sometimes scoring higher than a correct one.",
     ["exchange_core_throughput", "ffmpeg_swscale_reimplementation", "jagua_nesting_optimization",
      "college_english_exam_bank", "cta_risk_budget_optimization", "graph_node_classification",
      "equivalence_class_divide_and_conquer", "schemathesis_reporting_observability",
      "schemathesis_datagen_pipeline", "schemathesis_config_modernization"]),
    ("The grader applies a different rule from the one the agent is told",
     "The instructions promise one thing; the grader checks or runs another.",
     ["triangulation_coloring_optimization", "warehouse_forklift_routing", "grid_turing_robot",
      "molecular_self_assembly", "vibrating_path_graph_coloring", "apple_incremental_game",
      "openttd_transport_ai", "openrct2_theme_park_ai", "portfolio_risk_calibration"]),
    ("The 0–100 scale is wrong",
     "The raw result is converted to 0–100 against reference points that cannot be reached or were measured on something else.",
     ["treant_forest", "integer_compression_codec"]),
    ("The wrong submission is kept",
     "Each run should keep its best submission; here it keeps an earlier one.",
     ["order_addition_permutation_optimization"]),
    ("Removed",
     "No sound fix was possible, so the task is not part of the verified set.",
     ["dabic_gravity_inversion"]),
    ("Kept: real issues that do not change scores",
     "The issue is real, but it cannot change an honest agent's score out of 100 by a meaningful amount, or the task states it openly, and no change to the grader is needed.",
     ["bipedalwalker_locomotion_rl", "vehicle_routing_time_windows",
      "ordinal_notation_well_foundedness"]),
    ("Kept: scores that depend on chance, machine speed or network access",
     "The grader works, but repeated runs or different machines can give different scores. This is noise that no change to the grader removes, so these tasks are kept with a note even where the effect is large (ANN Vector Search: about ±7 of 100 points per grading).",
     ["nethack_dungeon_agent", "wesnoth_tactical_ai", "ann_vector_search_qps", "dcss_dungeon_ai",
      "wireless_electricity_layout", "ad_placement_optimization",
      "new_foundations_consistency", "k12_math_recommendation"]),
]
LABEL = {'retain': 'Kept as is', 'retain-with-note': 'Kept, with a note', 'repair-v2': 'Fixed', 'exclude': 'Removed'}


def main():
    d = {r['task_id']: r for r in json.loads((ROOT / 'data/decisions.json').read_text())}
    plain = json.loads((ROOT / 'cases' / 'plain.json').read_text())
    names = task_names()
    seen = set()
    out = ["# Findings", "",
           "All 51 public EdgeBench tasks, grouped by what goes wrong. Each row gives the problem in one line and "
           "how much it changes a score out of 100. The task name links to the full case: what the task asks, "
           "what goes wrong, how it was checked, the fix, and its limits.", "",
           "\"How much it matters\" is the largest change we demonstrated or proved for one submission. It is not "
           "an estimate of the effect on the published leaderboard, which is in [IMPACT.md](IMPACT.md).", ""]
    for title, blurb, ids in GROUPS:
        out += [f"## {title}", "", blurb, "", "| Task | Outcome | What goes wrong | How much it matters |",
                "| --- | --- | --- | --- |"]
        for t in ids:
            assert t not in seen, t
            seen.add(t)
            out.append(f"| [{names[t]}](cases/{t}.md) | {LABEL[d[t]['proposed']]} | {plain[t]['headline']} | "
                       f"{plain[t]['effect']} |")
        out.append("")
    rest = sorted(set(d) - seen, key=lambda t: names[t])
    out += ["## Kept: no problem found", "",
            "The grader scores honest work as the task promises. Each of these tasks carries a short usage note.", "",
            "| Task | What we checked |", "| --- | --- |"]
    out += [f"| [{names[t]}](cases/{t}.md) | {plain[t]['headline']} |" for t in rest]
    (ROOT / 'FINDINGS.md').write_text('\n'.join(out) + '\n')
    assert len(seen) + len(rest) == 51, (len(seen), len(rest))
    print(len(seen), 'grouped;', len(rest), 'no problem found')


if __name__ == '__main__':
    main()
