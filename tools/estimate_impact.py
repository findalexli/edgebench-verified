#!/usr/bin/env python3
"""Estimate how the v1.0 findings move EdgeBench's published 51-task @12h means.

Inputs: the per-task @12h leaderboard in tasks/README.md (the publisher's numbers) and
evidence/impact/effects.json (direction and size of each repaired task's effect, taken
from its case page). Outputs IMPACT.md and data/impact.csv.

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


def adjusted(lb, m, steps=("dabic", "treant", "borden")):
    """Per-model scores after the exact corrections named in steps (applied in this order)."""
    v2 = {t: lb[t][m] for t in lb}
    if "dabic" in steps:
        del v2["dabic_gravity_inversion"]
    if "treant" in steps:
        v2["treant_forest"] = treant_v2(lb["treant_forest"][m])
    if "borden" in steps:
        v2["borden_source_inversion"] = borden_v2(lb["borden_source_inversion"][m])
    return v2


def decomposition(lb, m):
    """Split the exact shift into D-ABIC removal, Treant scale and Borden scale (applied in that order)."""
    base = mean(lb[t][m] for t in lb)
    a = mean(adjusted(lb, m, ("dabic",)).values())
    b = mean(adjusted(lb, m, ("dabic", "treant")).values())
    c = mean(adjusted(lb, m).values())
    return {"dabic": a - base, "treant": b - a, "borden": c - b}


def bounded_parts(v2, effects):
    """Largest possible rise and fall per bounded task, in points on that task."""
    up, down = {}, {}
    for t, e in effects.items():
        if e["kind"] != "bounded" or v2.get(t) is None:
            continue
        s, b = v2[t], e["bound"]
        if e["direction"] in ("up", "either"):
            up[t] = max(0.0, min(e.get("bound_up", b), e.get("ceiling", 100.0) - s))
        if e["direction"] in ("down", "either"):
            down[t] = min(e.get("bound_down", b), s)
    return up, down


def main():
    lb = parse_leaderboard()
    effects = json.loads((ROOT / "evidence/impact/effects.json").read_text())
    assert len(lb) == 51, len(lb)
    decisions = {d["task_id"]: d for d in json.loads((ROOT / "data/decisions.json").read_text())}
    assert set(lb) == set(decisions)
    repaired = {t for t, d in decisions.items() if d["proposed"] != "retain-with-note"}
    assert repaired == set(effects), sorted(repaired ^ set(effects))

    out = {}
    for m in MODELS:
        v1 = {t: lb[t][m] for t in lb}
        base = mean(v1.values())
        # exact: Treant and Borden rescaled, D-ABIC excluded
        v2 = dict(v1)
        v2["treant_forest"] = treant_v2(v1["treant_forest"])
        v2["borden_source_inversion"] = borden_v2(v1["borden_source_inversion"])
        del v2["dabic_gravity_inversion"]
        exact = mean(v2.values())
        n = len([v for v in v2.values() if v is not None])
        ups, downs = bounded_parts(v2, effects)
        up, down = sum(ups.values()), sum(downs.values())
        assert v2 == adjusted(lb, m)
        out[m] = dict(published=PUBLISHED[m], recomputed=base, exact=exact,
                      treant_v1=v1["treant_forest"], treant_v2=v2["treant_forest"],
                      borden_v1=v1["borden_source_inversion"], borden_v2=v2["borden_source_inversion"],
                      bounded_up=up / n, bounded_down=down / n, n=n,
                      open_down=sum(v2[t] for t, e in effects.items() if e["kind"] == "open"
                                    and e["direction"] in ("down", "either") and v2.get(t) is not None) / n,
                      open_up=sum(100.0 - v2[t] for t, e in effects.items() if e["kind"] == "open"
                                  and e["direction"] in ("up", "either") and v2.get(t) is not None) / n)
        assert abs(base - PUBLISHED[m]) < 0.1, (m, base)

    with open(ROOT / "data/impact.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["model", "published_mean", "recomputed_mean", "exact_adjusted_mean",
                    "bounded_low", "bounded_high", "worst_case_low", "worst_case_high", "tasks_in_mean"])
        for m in MODELS:
            o = out[m]
            w.writerow([m, o["published"], f"{o['recomputed']:.4f}", f"{o['exact']:.4f}",
                        f"{o['exact'] - o['bounded_down']:.4f}", f"{o['exact'] + o['bounded_up']:.4f}",
                        f"{o['exact'] - o['bounded_down'] - o['open_down']:.4f}",
                        f"{o['exact'] + o['bounded_up'] + o['open_up']:.4f}", o["n"]])

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
    # An effect's optional "basis" overrides the Kind label, e.g. for a limit computed by a sweep, not proved.
    KIND = {"exact": "calculated exactly", "excluded": "task removed", "bounded": "proven limit",
            "open": "direction known, size unknown"}

    L.append("# Effect on the published leaderboard\n")
    L.append("EdgeBench publishes each model's score on every task. This page uses those numbers to work out "
             "how the problems we found change each model's average over the 51 public tasks. No AI model "
             "was rerun, and the agents' original submissions are not public. Only part of the effect can "
             "therefore be calculated. **The total change cannot be determined from public data**: it would "
             "require rerunning the models on the fixed tasks, or, for some fixes, regrading the original submissions. "
             "What follows is the largest possible change, a range from fixes with a proven limit, and the corrections that can "
             "be computed exactly. All ranges assume that no fix turns a failed run into a scored one or the reverse; a fix that "
             "does can move a task's average further. Kept tasks are treated as unchanged, "
             "including those whose run-to-run variation for scoring agents is unmeasured (ANN, NetHack, Wesnoth). Generated by `tools/estimate_impact.py`; "
             "the numbers are in [data/impact.csv](data/impact.csv).\n")
    L.append("## Summary\n")
    L.append("Models as EdgeBench names them: Claude Opus 4.8, GPT-5.5, GPT-5.4, GLM-5.1 and DeepSeek-V4-Pro (DS-V4-Pro).\n")
    L.append("| Model | Published average | After the corrections we can calculate exactly | Range, adding fixes with a proven limit | Largest possible change |")
    L.append("| --- | ---: | ---: | :---: | :---: |")
    for m in MODELS:
        o = out[m]
        L.append(f"| {m} | {o['published']:.1f} | **{o['exact']:.1f}** ({o['exact'] - o['recomputed']:+.1f}) | "
                 f"{o['exact'] - o['bounded_down']:.1f} – {o['exact'] + o['bounded_up']:.1f} | "
                 f"{o['exact'] - o['bounded_down'] - o['open_down']:.1f} – {o['exact'] + o['bounded_up'] + o['open_up']:.1f} |")
    L.append("")
    dec = {m: decomposition(lb, m) for m in MODELS}
    rng = lambda k, f="{:.1f}": f"{f.format(min(abs(d[k]) for d in dec.values()))} to {f.format(max(abs(d[k]) for d in dec.values()))}"
    L.append(f"- **Calculated exactly.** Where a fix only changes how a raw result becomes 0–100, or removes a task, "
             f"each published score can be recomputed directly. Together these raise every model's average by "
             f"{min(shifts):.1f} to {max(shifts):.1f} points: the Treant Forest scale adds {rng('treant')}, where "
             f"the old scale capped every score at 21.02 out of 100; the removal of D-ABIC adds {rng('dabic')}; and "
             f"the Borden Inversion scale subtracts {rng('borden', '{:.2f}')}. The order of the models does not change: "
             + " > ".join(order) + ".")
    L.append(f"- **Proven limit.** For {n_bound} fixed tasks the largest possible effect is bounded by the task's own scoring "
             "(proved or computed from the grader; for PFR partly inferred from its rule; for Portfolio Risk from a "
             "decimal sweep, not a proof). "
             f"Together they can move an average by at most {max(out[m]['bounded_down'] for m in MODELS):.1f} "
             f"points down or {max(out[m]['bounded_up'] for m in MODELS):.1f} points up. "
             + (f"That is enough to swap {', '.join(fragile)}, so the 51 public tasks alone do not show which "
                "of them is ahead." if fragile else "That is not enough to reverse any two neighbouring models; whether "
                "the order changes depends on the fixes whose effect size is unknown."))
    L.append(f"- **Direction known, size unknown.** For {n_open} fixed tasks we know whether scores go up or down, but not by "
             "how much. Finding out would require new runs (for fixes that change only instructions or inputs) or "
             "regrading the original submissions (for fixes to the grader). The largest possible change lets every fix, "
             "these and the ones with a proven limit, take its largest possible effect: a score that goes down could fall to 0, "
             "and one that goes up could rise to 100. These tasks, with the open part of Borden Inversion, account for up to "
             f"{max(out[m]['open_down'] for m in MODELS):.1f} points down or {max(out[m]['open_up'] for m in MODELS):.1f} up. "
             "It is an outer limit, not a prediction.")
    L.append("")
    L.append("The recomputed average is only the part we can calculate; the other fixes can still push it up or down. "
             "Several of the largest effects are in the group whose size is unknown.\n")
    L.append("## Can two models swap places?\n")
    L.append("Two neighbouring models can swap if the most one can fall plus the most the other can rise is "
             "at least the gap between them.\n")
    L.append("| Models | Gap after exact corrections | Largest swing with proven limits | Largest swing within the largest possible change |")
    L.append("| --- | ---: | ---: | ---: |")
    for hi, lo, g, bb, ww in gaps:
        L.append(f"| {hi} vs {lo} | {g:.1f} | {bb:.1f} | {ww:.1f} |")
    L.append("")
    for hi, lo, g, bb, ww in gaps:
        if bb < g:
            continue
        uh, dh = bounded_parts(adjusted(lb, hi), effects)
        ul, dl = bounded_parts(adjusted(lb, lo), effects)
        nh, nl = out[hi]["n"], out[lo]["n"]
        parts = {t: dh.get(t, 0) / nh + ul.get(t, 0) / nl for t in set(dh) | set(ul)}
        top = max(parts, key=parts.get)
        if bb - parts[top] < g:
            L.append(f"The swap of {hi} and {lo} rests mainly on `{top}`, where {lo} can gain up to {ul.get(top, 0):.1f} "
                     f"points: without it the largest swing is {bb - parts[top]:.2f}, less than the gap of {g:.2f}, so {lo} "
                     f"would need at least {(g - bb + parts[top]) * nl:.1f} of those points. It also assumes every other "
                     "bounded effect at its extreme at once.\n")
    L.append("No order is guaranteed within the largest possible change. Settling it requires rerunning the models on the fixed tasks.\n")

    L.append("## How EdgeBench computes a published score\n")
    L.append("From the EdgeBench technical report (arXiv 2607.05155, Appendices B and G) and its evaluation platform; the quoted passages are in [evidence/impact/edgebench-scoring-method.md](evidence/impact/edgebench-scoring-method.md):\n")
    L.append("- Each model gets **three 12-hour runs** per task. The published task score is the **average over "
             "the valid runs**; if a run fails, the average uses the runs that remain.")
    L.append("- Each run is scored by its **best submission so far** at the time limit (2 h, 4 h, … 12 h). Each "
             "run's score is converted to 0–100 before averaging.")
    L.append("- A model's headline number is the plain average over tasks. Recomputing it from the published "
             "per-task table gives the published values to within rounding.\n")
    L.append("Three consequences:\n")
    L.append("1. **Only changes of scale can be undone from published numbers.** Any other fix changes which "
             "submissions score what. Only regrading the hidden submissions can show that for fixes to the grader, "
             "and only new runs for fixes that change instructions or inputs (ARC, OpenRCT2, OpenTTD, the Borden "
             "convention, Triangulation's inputs).")
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
             "that the documented starting program cannot reach. On real submissions the original raw result was "
             "2.4 to 3.7 times lower than the documented definition gives (up to about 9 times for a simple honest codec). The fixed version also needs a new 0–100 scale (Section \"A check against real agent runs\"), "
             "so the direction of the change depends on the submission.")
    L.append("- **OpenTTD.** A program that follows the instructions calls a function that does not exist and stops "
             "working. Its effect depends on how often agents followed that instruction, which only new runs can show.")
    L.append("- **SMT Solver.** Correct answers are rejected on some hidden problems, so a model's score can only rise "
             "or stay the same, by an amount that depends on how it writes its answers.")
    L.append("- **Lean Analysis Proofs.** The set of scored items changes from 2,901 to 2,338, so every score "
             "moves, in a direction that depends on which proofs each run completed.")
    L.append("- **Exchange Core, Jagua, FFmpeg, College English.** These accept wrong work. Because a run keeps "
             "its best submission, any over-credited submission sets the run's score.\n")

    L.append("## A check against real agent runs\n")
    L.append("EdgeBench has not released its runs. A third party has published one run of Claude Opus 5.5 on 16 of "
             "the public tasks, four hours each, with every submission and its original score "
             "(`adafadaq/edgebench-opus-5-5-xhigh-rollouts` on Hugging Face). Nine of those tasks are ones we fixed. "
             "A saved submission can test a fix only if the fix changes the grader alone: if it changes what the agent "
             "sees, the agent would have worked differently. Seven fixes are grader-only, and we regraded 314 of their "
             "submissions with both graders (349 paired gradings with repeats; timing-dependent graders three times for "
             "the submissions that decide the score), at the official 4 CPUs, with the run's own grading script and "
             "EdgeBench's best-so-far rule. The original grader reproduced the run's recorded result exactly for all 144 "
             "submissions of the three tasks whose graders do not depend on timing "
             "(`evidence/runs/opus55-regrade2-summary/summary.json`; an earlier two-task regrade is in "
             "`evidence/runs/opus55-regrade/`).\n")
    L.append("| Task | Fix changes | Submissions graded | Run's score: original → fixed | What it shows |")
    L.append("| --- | --- | --- | --- | --- |")
    L.append("| Order Addition | grader | 9 of 9 | 3.79 → **41.24** | The stale checksum fails every result, so the run kept its first agent submission; the fixed grader keeps a later one (+37.45) |")
    L.append("| Integer Codec | grader and scale | 37 of 37 (top 6 three times) | 75.72 → **about 50–54** | Every raw result rises 1.7–4×; the original grader on our machines gives 71.9–73.0. The same submission varies by up to ±20% between machines under both graders (decode timed over a few milliseconds) |")
    L.append("| Juliet Analyzer | grader | 105 of 105 | 99.66 → 99.66 | 14 early submissions lost up to 25 points to the hidden trace form; the agent then switched to it, so the final score is unchanged |")
    L.append("| Molecular Self-Assembly | grader (CPU count) | 8 of 13 (best and final three times) | 100 → 100 | Every graded submission +3–4% raw; the run is above the top of the scale either way (original grader on our machines: 95.9–100) |")
    L.append("| Tree Block Partitioning | grader | 13 of 25 (best and final three times) | 100 → 100 | The affected sub-task scores the same under both graders; no effect in this run |")
    L.append("| Graph Node Classification | grader | 112 of 118 (6 missing from the archive; top 6 three times) | 90.85 → 90.43–90.60 | All valid under both; differences are timing noise (original grader on our machines: 90.44–90.60) |")
    L.append("| Schemathesis Config | grader | 30 of 30 | 100 → 100 | Every submission scores the same under both; no effect in this run |")
    L.append("| Borden Inversion | instructions and starter file | not regradable | 60.10 → 55.14 (scale only) | The agent learned part of the hidden convention by iterating (first submissions about 7); the fix's effect on its work cannot be measured from saved answers |")
    L.append("| Lean Analysis Proofs | grader and two statements | not run (33 GB image, 16 GiB grader) | 96.86 → 98.42 (computed) | The original per-target verdicts counted against the fixed target list |")
    L.append("")
    L.append("This is one model, one run per task and four hours instead of twelve. It shows that the problems "
             "occur in real runs; it does not measure the leaderboard effect.\n")
    L.append("## The exact corrections\n")
    L.append("These fixes change only how a raw result is converted to 0–100, so each published score converts "
             "directly.\n")
    L.append("| Model | Treant Forest: original → fixed | Borden Inversion: original → fixed | Average over 51 → 50 tasks (50 → 49 for Opus 4.8) |")
    L.append("| --- | ---: | ---: | ---: |")
    for m in MODELS:
        o = out[m]
        L.append(f"| {m} | {o['treant_v1']:.1f} → {o['treant_v2']:.1f} | {o['borden_v1']:.1f} → {o['borden_v2']:.1f} | "
                 f"{o['recomputed']:.2f} → {o['exact']:.2f} |")
    L.append("")
    L.append("- **Treant Forest.** The raw result (the total number of turns) is unchanged. The original scale "
             "gives 20 points at 88,189 turns, 80 points at 330,195 and 100 points at 451,198, far above the "
             "turn cap of 92,304, so no score can exceed 21.02. The fixed scale runs straight from the starting program's "
             "3,418 turns (0 points) to the cap, 92,304 (100 points). Every published score is below 20, "
             "where the original scale is a straight line from 5,369 turns (0 points) to 88,189 turns (20 points), "
             "so each converts exactly: turns = 5,369 + score/20 × 82,820. This also holds for an average of "
             "runs, because the conversion is a straight line, with two exceptions (Lean shows the formula fails there, "
             "`evidence/formal/notes/treant_forest.md`; the sizes below are computed, not proved). A run that scored 0 had a raw result of at most "
             "5,369 turns and scores between 0 and 2.19 on the fixed scale, so the formula can overstate the fixed "
             "average by up to 2.19 points divided by the number of runs. A run between 20 and 21.02 falls on the "
             "next segment and shifts the result by at most about 0.12 divided by the number of runs.")
    L.append("- **Borden Inversion.** The original task had no 0–100 conversion, so the published value is the "
             "raw result, which runs from 0 to 109. The fixed version reports raw × 100/109. This is only the "
             "change of scale. The fix also gives agents the grader's physics convention, which raises honest "
             "one-shot fits (7.0 → 31.2 raw in our tests; an agent iterating on the grader's feedback can already learn "
             "part of it). That part needs new runs and is not included.")
    L.append("- **D-ABIC Gravity Inversion** is removed, so the average is taken over 50 tasks (49 for Opus 4.8, "
             "which has no valid result on Rust Multicrate).\n")

    L.append("## Every fixed or removed task\n")
    L.append("| Task | Effect on the original scores | Kind | Proven limit (points) | Opus 4.8 | GPT-5.5 | GPT-5.4 | GLM-5.1 | DS-V4-Pro |")
    L.append("| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for t in sorted(effects):
        e = effects[t]
        b = ("" if e.get("bound") is None else f"{e['bound']:g}" if "bound_up" not in e and "bound_down" not in e
             else f"{e.get('bound_up', e['bound']):g} up, {e.get('bound_down', e['bound']):g} down")
        cells = " | ".join("—" if lb[t][m] is None else f"{lb[t][m]:.1f}" for m in MODELS)
        kind = KIND[e['kind']] if "basis" not in e else f"limit from a {e['basis']}"
        L.append(f"| [{t}](cases/{t}.md) | {e['text']} | {kind} | {b} | {cells} |")
    L.append("")
    L.append("*Up* means the original grader gave correct work too little credit, so the fix raises scores. "
             "*Down* means it gave wrong work too much credit, so the fix lowers scores. A proven limit is "
             "capped by each model's score (a score cannot fall below 0) and by any proven ceiling. The five "
             "right-hand columns are the published 12-hour scores.\n")

    L.append("## Limits\n")
    L.append("- **This is not a regraded leaderboard.** The original submissions are not public, so none was "
             "regraded.")
    L.append("- **Only the 51 public tasks are covered.** EdgeBench's full leaderboard also includes 83 "
             "unreleased tasks.")
    L.append("- **The ranges are not estimates.** The proven-limit range is the largest movement we proved, computed or "
             "(for PFR) inferred, and the largest possible change lets every fix take its largest possible effect.")
    L.append("- **Rounding.** Recomputed averages differ from the published ones by at most "
             f"{max(abs(o['recomputed'] - o['published']) for o in out.values()):.2f}, because the per-task table "
             "is rounded to one decimal. All corrections are applied to the recomputed averages.")
    L.append("- **Fixed tasks form a new version of the benchmark.** These figures show how much the problems "
             "matter. They are not a replacement leaderboard.")
    (ROOT / "IMPACT.md").write_text("\n".join(L) + "\n")
    json.dump(out, sys.stdout, indent=1)


if __name__ == "__main__":
    main()
