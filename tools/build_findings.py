#!/usr/bin/env python3
"""Generate FINDINGS.md: every task in plain language (from cases/plain.json). Tasks with a problem are grouped
by their primary problem category (data/decisions.json); kept tasks keep their own sections."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from names import names as task_names  # noqa: E402
import categories as C  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

GROUPS = [
    ("Kept: real issues that do not change scores",
     "The issue is real, but it cannot change the score of a good-faith submission out of 100 by a meaningful amount, or the task states it openly, and no change to the grader is needed.",
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
    decisions = json.loads((ROOT / 'data/decisions.json').read_text())
    d = {r['task_id']: r for r in decisions}
    bad = C.validate(decisions)
    assert not bad, bad
    plain = json.loads((ROOT / 'cases' / 'plain.json').read_text())
    names = task_names()
    S = C.en_strings()
    prim = C.by_primary(decisions)
    n_problem = sum(len(v) for v in prim.values())
    seen = set()
    out = ["# Findings", "",
           "All 51 public EdgeBench tasks. Each row gives the problem in one line and how much it changes a "
           "score out of 100. The task name links to the full case: what the task asks, what goes wrong, how it "
           "was checked, the fix, and its limits.", "",
           f"The {n_problem} tasks with a problem (fixed or removed) are grouped into four categories by the "
           "mechanism of their main defect. Each task has exactly one primary category, under which it is listed, "
           "and may have secondary ones (the \"Also\" column). Kept tasks follow in their own sections.", "",
           "| Category | Tasks (primary) |", "| --- | ---: |"]
    out += [f"| [{S['pcat.' + k]}](#{i}-{S['pcat.' + k].lower().replace(' ', '-').replace('–', '').replace('/', '')}) "
            f"| {len(prim[k])} |" for i, k in enumerate(C.KEYS, 1)]
    out += [f"| **Total** | **{n_problem}** |", "",
            "\"How much it matters\" is the largest change we demonstrated or proved for one submission. It is not "
            "an estimate of the effect on the published leaderboard, which is in [IMPACT.md](IMPACT.md).", ""]
    for i, k in enumerate(C.KEYS, 1):
        out += [f"## {i}. {S['pcat.' + k]}", "", f"**{len(prim[k])} tasks.** {S['pcat.' + k + '.blurb']}", "",
                "| Task | Outcome | Also | What goes wrong | How much it matters |",
                "| --- | --- | --- | --- | --- |"]
        for t in sorted(prim[k], key=lambda t: names[t].lower()):
            assert t not in seen, t
            seen.add(t)
            also = '; '.join(S['pcat.' + x] for x in C.secondary(d[t])) or '–'
            out.append(f"| [{names[t]}](cases/{t}.md) | {LABEL[d[t]['proposed']]} | {also} | {plain[t]['headline']} | "
                       f"{plain[t]['effect']} |")
        out.append("")
    assert seen == {t for t, r in d.items() if r['proposed'] in C.PROBLEM}, 'a problem task has no category'
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
            "The grader scores good-faith work as the task promises. Each of these tasks carries a short usage note.", "",
            "| Task | What we checked |", "| --- | --- |"]
    out += [f"| [{names[t]}](cases/{t}.md) | {plain[t]['headline']} |" for t in rest]
    (ROOT / 'FINDINGS.md').write_text('\n'.join(out) + '\n')
    assert len(seen) + len(rest) == 51, (len(seen), len(rest))
    print(len(seen), 'grouped;', len(rest), 'no problem found;',
          ', '.join(f'{k} {len(v)}' for k, v in prim.items()))


if __name__ == '__main__':
    main()
