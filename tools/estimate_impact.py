#!/usr/bin/env python3
"""Estimate how the v1.0 findings move EdgeBench's published 51-task @12h means.

Inputs: the per-task @12h leaderboard in tasks/README.md (the publisher's numbers) and
evidence/impact/effects.json (direction and size of each repaired task's effect, taken
from its case page). Outputs IMPACT.md and impact.csv.

Three kinds of adjustment, kept separate:
  exact    - a pure change of score scale on unchanged raw scores (recomputed per model)
  bounded  - a documented maximum effect in normalized points (an interval, not a value)
  open     - direction known, size requires re-scoring the original submissions
"""
import csv
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODELS = ["Opus 4.8", "GPT-5.5", "GPT-5.4", "GLM-5.1", "DS-V4-Pro"]
PUBLISHED = {"Opus 4.8": 44.2, "GPT-5.5": 43.1, "GPT-5.4": 34.2, "GLM-5.1": 30.4, "DS-V4-Pro": 25.7}


def parse_leaderboard():
    text = (ROOT / "tasks/README.md").read_text()
    block = text[text.index("| Task | Category | Opus 4.8"):]
    rows = {}
    for line in block.split("\n")[2:]:
        if not line.startswith("| "):
            break
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows[cells[0]] = {}
        for m, cell in zip(MODELS, cells[2:7]):
            v = cell.split("/")[-1]
            rows[cells[0]][m] = None if v == "—" else float(v)
    return rows


def mean(vals):
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals)


def treant_v2(s):
    # v1 piecewise_max segment 0..20 is linear between baseline 5369 and rank30 88189.
    # Every published value is below 20, so raw = 5369 + s/20 * (88189 - 5369).
    assert 0 < s < 20
    raw = 5369.0 + s / 20.0 * (88189.0 - 5369.0)
    return 100.0 * (raw - 3418.0) / (92304.0 - 3418.0)


def borden_v2(s):
    # v1 had no rescale (published value is the raw score, 0..109); v2 is linear 0..109.
    return 100.0 * s / 109.0


def main():
    lb = parse_leaderboard()
    effects = json.loads((ROOT / "evidence/impact/effects.json").read_text())
    assert len(lb) == 51, len(lb)
    decisions = {d["task_id"]: d for d in json.loads((ROOT / "decisions.json").read_text())}
    assert set(lb) == set(decisions)
    repaired = {t for t, d in decisions.items() if d["proposed"] != "retain-with-note"}
    assert repaired == set(effects), sorted(repaired ^ set(effects))

    out = {}
    for m in MODELS:
        v1 = {t: lb[t][m] for t in lb}
        base = mean(v1.values())
        # exact: Treant and Borden rescaled, Dabic excluded
        v2 = dict(v1)
        v2["treant_forest"] = treant_v2(v1["treant_forest"])
        v2["borden_source_inversion"] = borden_v2(v1["borden_source_inversion"])
        del v2["dabic_gravity_inversion"]
        exact = mean(v2.values())
        n = len([v for v in v2.values() if v is not None])
        up = down = 0.0
        for t, e in effects.items():
            if e["kind"] != "bounded" or v2.get(t) is None:
                continue
            s = v2[t]
            b = e["bound"]
            if e["direction"] in ("up", "either"):
                cap = e.get("ceiling", 100.0)
                up += max(0.0, min(b, cap - s))
            if e["direction"] in ("down", "either"):
                down += min(b, s)
        out[m] = dict(published=PUBLISHED[m], recomputed=base, exact=exact,
                      treant_v1=v1["treant_forest"], treant_v2=v2["treant_forest"],
                      borden_v1=v1["borden_source_inversion"], borden_v2=v2["borden_source_inversion"],
                      bounded_up=up / n, bounded_down=down / n, n=n,
                      open_down=sum(v2[t] for t, e in effects.items() if e["kind"] == "open"
                                    and e["direction"] in ("down", "either") and v2.get(t) is not None) / n,
                      open_up=sum(100.0 - v2[t] for t, e in effects.items() if e["kind"] == "open"
                                  and e["direction"] in ("up", "either") and v2.get(t) is not None) / n)
        assert abs(base - PUBLISHED[m]) < 0.1, (m, base)

    with open(ROOT / "impact.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["model", "published_mean", "recomputed_mean", "exact_adjusted_mean",
                    "bounded_low", "bounded_high", "worst_case_low", "worst_case_high", "tasks_in_mean"])
        for m in MODELS:
            o = out[m]
            w.writerow([m, o["published"], f"{o['recomputed']:.2f}", f"{o['exact']:.2f}",
                        f"{o['exact'] - o['bounded_down']:.2f}", f"{o['exact'] + o['bounded_up']:.2f}",
                        f"{o['exact'] - o['bounded_down'] - o['open_down']:.2f}",
                        f"{o['exact'] + o['bounded_up'] + o['open_up']:.2f}", o["n"]])

    def rank(key):
        return [m for m, _ in sorted(out.items(), key=lambda kv: -kv[1][key])]

    L = []
    order = rank("exact")
    shifts = [out[m]["exact"] - out[m]["recomputed"] for m in MODELS]
    gaps = [(hi, lo, out[hi]["exact"] - out[lo]["exact"],
             out[hi]["bounded_down"] + out[lo]["bounded_up"],
             out[hi]["bounded_down"] + out[hi]["open_down"] + out[lo]["bounded_up"] + out[lo]["open_up"])
            for hi, lo in zip(order, order[1:])]
    fragile = [f"{hi} and {lo}" for hi, lo, g, bb, ww in gaps if bb >= g]
    n_exact = sum(e["kind"] in ("exact", "excluded") for e in effects.values()) + 1
    n_bound = sum(e["kind"] == "bounded" for e in effects.values())
    n_open = sum(e["kind"] == "open" for e in effects.values()) - 1
    KIND = {"exact": "calculated exactly", "excluded": "task removed", "bounded": "known maximum",
            "open": "direction only"}

    L.append("# Effect on the published leaderboard\n")
    L.append("EdgeBench publishes each model's score on every task. This page uses those numbers to work out "
             "how the problems we found change each model's average over the 51 public tasks. No AI model "
             "was rerun, and the agents' original submissions are not public. Only part of the effect can "
             "therefore be calculated; the rest is given as a range. Generated by `tools/estimate_impact.py`; "
             "the numbers are in [impact.csv](impact.csv).\n")
    L.append("## Summary\n")
    L.append("| Model | Published average | After the corrections we can calculate exactly | Range, adding fixes with a known maximum effect | Widest possible range |")
    L.append("| --- | ---: | ---: | :---: | :---: |")
    for m in MODELS:
        o = out[m]
        L.append(f"| {m} | {o['published']:.1f} | **{o['exact']:.1f}** ({o['exact'] - o['recomputed']:+.1f}) | "
                 f"{o['exact'] - o['bounded_down']:.1f} – {o['exact'] + o['bounded_up']:.1f} | "
                 f"{o['exact'] - o['bounded_down'] - o['open_down']:.1f} – {o['exact'] + o['bounded_up'] + o['open_up']:.1f} |")
    L.append("")
    L.append(f"- **Calculated exactly.** Some fixes change only how a raw result is converted to 0–100, so a "
             f"published score can be converted directly. They raise every model's average by "
             f"{min(shifts):.1f} to {max(shifts):.1f} points. Most of this comes from Treant Forest, where "
             "the old scale capped every score at 21.02 out of 100. The order of the models does not change: "
             + " > ".join(order) + ".")
    L.append(f"- **Known maximum.** For {n_bound} fixed tasks we proved or demonstrated the largest possible effect. "
             f"Together they can move an average by at most {max(out[m]['bounded_down'] for m in MODELS):.1f} "
             f"points down or {max(out[m]['bounded_up'] for m in MODELS):.1f} points up. "
             + (f"That is enough to swap {', '.join(fragile)}, so the 51 public tasks alone do not show which "
                "of them is ahead." if fragile else "That is not enough to swap any two neighbouring models."))
    L.append(f"- **Direction only.** For {n_open} fixed tasks we know whether scores go up or down, but not by "
             "how much. Finding out would require regrading the original submissions. The widest range lets each "
             "of these take its largest possible effect: a score that goes down could fall to 0, and one that goes "
             "up could rise to 100. The true values lie inside this range. It is an outer limit, not a prediction.")
    L.append("")
    L.append("Read the exact column as the part of the change that is certain, not as the size of the "
             "problem. Several of the largest effects are in the direction-only group.\n")
    L.append("## Can two models swap places?\n")
    L.append("Two neighbouring models can swap if the most one can fall plus the most the other can rise is "
             "at least the gap between them.\n")
    L.append("| Models | Gap after exact corrections | Largest swing with known maximums | Largest swing in the widest range |")
    L.append("| --- | ---: | ---: | ---: |")
    for hi, lo, g, bb, ww in gaps:
        L.append(f"| {hi} vs {lo} | {g:.1f} | {bb:.1f} | {ww:.1f} |")
    L.append("")
    L.append("No order is guaranteed in the widest range. Settling it requires regrading the original submissions "
             "with the fixed tasks.\n")

    L.append("## How EdgeBench computes a published score\n")
    L.append("From the EdgeBench technical report (arXiv 2607.05155, Appendices B and G):\n")
    L.append("- Each model gets **three 12-hour runs** per task. The published task score is the **average over "
             "the valid runs**; if a run fails, the average uses the runs that remain.")
    L.append("- Each run is scored by its **best submission so far** at the time limit (2 h, 4 h, … 12 h). Each "
             "run's score is converted to 0–100 before averaging.")
    L.append("- A model's headline number is the plain average over tasks. Recomputing it from the published "
             "per-task table gives the published values to within rounding.\n")
    L.append("Three consequences:\n")
    L.append("1. **Only changes of scale can be undone from published numbers.** Any other fix changes which "
             "submissions score what, and only the hidden submissions can show that.")
    L.append("2. **Keeping the best submission magnifies over-crediting.** A run keeps its highest score, so a "
             "problem that only sometimes over-credits (noise, a lucky gamble, a lenient check) still raises the "
             "run's score. The agents also see their scores and keep trying for 12 hours, so they are more likely "
             "than a one-time solver to find a lenient check and keep using it.")
    L.append("3. **Discarding failed runs hides some problems.** A run that a problem kills (a time-out, a "
             "crashing program) may be discarded rather than scored 0. The published score then reflects only "
             "the runs that survived.\n")

    L.append("## Large effects whose size is unknown\n")
    L.append(f"Of the {len(effects)} tasks fixed or removed, {n_exact} can be corrected exactly, {n_bound} have "
             f"a known maximum effect, and {n_open} (plus part of Borden Inversion) have a known direction only. "
             "The largest of these:\n")
    L.append("- **Integer Compression Codec.** Every original score is measured against stored reference numbers "
             "that the documented starting program cannot reach. In our tests the fix raises scores about 4 times "
             "(starting program) to 8 times (a simple honest codec). The published 75.3 and 74.4 could reach the "
             "maximum of 100, but per-dataset caps make the factor for strong codecs uncertain.")
    L.append("- **OpenTTD.** A program that follows the instructions calls a function that does not exist and stops "
             "working. GLM-5.1's 0.0 fits this.")
    L.append("- **SMT Solver.** Correct answers are rejected on some hidden problems, so every model's score goes "
             "up by an amount that depends on how it writes its answers.")
    L.append("- **Lean Analysis Proofs.** The set of scored items changes from 2,901 to 2,338, so every score "
             "moves, in a direction that depends on which proofs each run completed.")
    L.append("- **Exchange Core, Jagua, FFmpeg, College English.** These accept wrong work. Because a run keeps "
             "its best submission, any over-credited submission sets the run's score.\n")

    L.append("## The exact corrections\n")
    L.append("These fixes change only how a raw result is converted to 0–100, so each published score converts "
             "directly.\n")
    L.append("| Model | Treant Forest: original → fixed | Borden Inversion: original → fixed | Average over 51 → 50 tasks |")
    L.append("| --- | ---: | ---: | ---: |")
    for m in MODELS:
        o = out[m]
        L.append(f"| {m} | {o['treant_v1']:.1f} → {o['treant_v2']:.1f} | {o['borden_v1']:.1f} → {o['borden_v2']:.1f} | "
                 f"{o['recomputed']:.2f} → {o['exact']:.2f} |")
    L.append("")
    L.append("- **Treant Forest.** The raw result (the total number of turns) is unchanged. The original scale "
             "gives 20 points at 88,189 turns, 80 points at 330,195 and 100 points at 451,198, far above the "
             "maximum possible 92,304, so no score can exceed 21.02. The fixed scale runs straight from the starting program's "
             "3,418 turns (0 points) to the maximum 92,304 (100 points). Every published score is below 20, "
             "where the original scale is a straight line from 5,369 turns (0 points) to 88,189 turns (20 points), "
             "so each converts exactly: turns = 5,369 + score/20 × 82,820. This also holds for an average of "
             "runs, because the conversion is a straight line. The one exception would be a run between 20 and "
             "21.02, which falls on the next segment.")
    L.append("- **Borden Inversion.** The original task had no 0–100 conversion, so the published value is the "
             "raw result, which runs from 0 to 109. The fixed version reports raw × 100/109. This is only the "
             "change of scale. The fix also gives agents the grader's physics convention, which raises honest "
             "fits (7.0 → 31.2 raw in our tests). That part needs new runs and is not included.")
    L.append("- **Dabic Gravity Inversion** is removed, so the average is taken over 50 tasks (49 for Opus 4.8, "
             "which has no valid result on Rust Multicrate).\n")

    L.append("## Every fixed or removed task\n")
    L.append("| Task | Effect on the original scores | Kind | Known maximum (points) | Opus 4.8 | GPT-5.5 | GPT-5.4 | GLM-5.1 | DS-V4-Pro |")
    L.append("| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for t in sorted(effects):
        e = effects[t]
        b = "" if e.get("bound") is None else f"{e['bound']:g}"
        cells = " | ".join("—" if lb[t][m] is None else f"{lb[t][m]:.1f}" for m in MODELS)
        L.append(f"| [{t}](cases/{t}.md) | {e['text']} | {KIND[e['kind']]} | {b} | {cells} |")
    L.append("")
    L.append("*Up* means the original grader gave correct work too little credit, so the fix raises scores. "
             "*Down* means it gave wrong work too much credit, so the fix lowers scores. A known maximum is "
             "limited by each model's score (a score cannot fall below 0) and by any proven ceiling. The five "
             "right-hand columns are the published 12-hour scores.\n")

    L.append("## Limits\n")
    L.append("- **This is not a regraded leaderboard.** The original submissions are not public, so none was "
             "regraded.")
    L.append("- **Only the 51 public tasks are covered.** EdgeBench's full leaderboard also includes 83 "
             "unreleased tasks.")
    L.append("- **The ranges are not estimates.** The known-maximum range is the largest movement we proved or "
             "demonstrated, and the widest range lets every direction-only fix take its largest possible effect.")
    L.append("- **Rounding.** Recomputed averages differ from the published ones by at most "
             f"{max(abs(o['recomputed'] - o['published']) for o in out.values()):.2f}, because the per-task table "
             "is rounded to one decimal. All corrections are applied to the recomputed averages.")
    L.append("- **Fixed tasks form a new version of the benchmark.** These figures show how much the problems "
             "matter. They are not a replacement leaderboard.")
    (ROOT / "evidence/impact/site-note.txt").write_text(
        f"Every model gains {min(shifts):.1f}–{max(shifts):.1f} points from the exact adjustments and the "
        "ranking is unchanged. " + (f"Within the documented bounds, {' and '.join(fragile)} could swap: "
        "the published gap is smaller than the bounds." if fragile else "No pair can swap within the documented bounds.")
        + f" This is a floor: {n_open} more repaired tasks can only be given a direction without the original submissions.\n")
    (ROOT / "IMPACT.md").write_text("\n".join(L) + "\n")
    json.dump(out, sys.stdout, indent=1)


if __name__ == "__main__":
    main()
