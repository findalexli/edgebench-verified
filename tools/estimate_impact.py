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
    L.append("# Impact on the published scores\n")
    L.append("How much do the defects move EdgeBench's published @12h means over the 51 public tasks? "
             "This page answers from the publisher's own per-task scores (`tasks/README.md`). "
             "No submission was re-scored and no model was re-run, so only effects that are a pure "
             "change of scale can be recomputed exactly. Everything else is reported as a documented "
             "bound, or as a direction whose size is open. Generated by `tools/estimate_impact.py`; "
             "data in [impact.csv](impact.csv).\n")
    order = rank("exact")
    shifts = [out[m]["exact"] - out[m]["recomputed"] for m in MODELS]
    gaps = [(hi, lo, out[hi]["exact"] - out[lo]["exact"],
             out[hi]["bounded_down"] + out[lo]["bounded_up"],
             out[hi]["bounded_down"] + out[hi]["open_down"] + out[lo]["bounded_up"] + out[lo]["open_up"])
            for hi, lo in zip(order, order[1:])]
    L.append("## Headline\n")
    L.append("| Model | Published | Exact adjustments | Range with documented bounds | Worst case if open effects are maximal |")
    L.append("| --- | ---: | ---: | :---: | :---: |")
    for m in MODELS:
        o = out[m]
        L.append(f"| {m} | {o['published']:.1f} | **{o['exact']:.1f}** ({o['exact'] - o['recomputed']:+.1f}) | "
                 f"{o['exact'] - o['bounded_down']:.1f} – {o['exact'] + o['bounded_up']:.1f} | "
                 f"{o['exact'] - o['bounded_down'] - o['open_down']:.1f} – {o['exact'] + o['bounded_up'] + o['open_up']:.1f} |")
    L.append("")
    L.append(f"- **Exact adjustments** raise every model's mean by {min(shifts):.1f} to {max(shifts):.1f} points. "
             "Almost all of this comes from Treant Forest, whose scale capped every submission at 21.02/100. "
             "The ranking is unchanged: " + " > ".join(order) + ".")
    fragile = [f"{hi} vs {lo}" for hi, lo, g, bb, ww in gaps if bb >= g]
    L.append(f"- **Documented bounds** cover the repairs with a proven or demonstrated maximum effect. Together "
             f"they move a mean by at most {max(out[m]['bounded_down'] for m in MODELS):.1f} points down or "
             f"{max(out[m]['bounded_up'] for m in MODELS):.1f} points up. "
             + ("Within these bounds, only " + ", ".join(fragile) + " can swap." if fragile
                else "No neighbouring pair can swap within these bounds."))
    L.append("- **Open effects** are the repairs whose size cannot be known without re-scoring the original "
             "submissions. The worst-case column assumes each of them takes its full range: a downward "
             "effect removes the whole task score, and an upward effect lifts it to 100. That is a limit, "
             "not a prediction.")
    L.append("")
    L.append("| Neighbouring pair | Gap after exact adjustments | Largest swing within documented bounds | Largest swing in the worst case |")
    L.append("| --- | ---: | ---: | ---: |")
    for hi, lo, g, bb, ww in gaps:
        L.append(f"| {hi} vs {lo} | {g:.1f} | {bb:.1f} | {ww:.1f} |")
    L.append("")
    L.append("A pair can swap when its swing is at least its gap. The swing is the higher model's largest "
             "possible fall plus the lower model's largest possible rise. "
             + (f"{' and '.join(fragile)}: the gap is smaller than the documented bounds alone, so the published "
                "order of this pair is not established by the 51 public tasks. " if fragile else "")
             + "No ordering is guaranteed in the worst case. Settling it requires re-scoring the original "
             "submissions under v2.\n")

    L.append("## Exact adjustments\n")
    L.append("These repairs change only how a raw score is mapped to 0–100, so each published score can be "
             "converted directly.\n")
    L.append("| Model | Treant v1 → v2 | Borden v1 → v2 | Mean over 51 → 50 tasks |")
    L.append("| --- | ---: | ---: | ---: |")
    for m in MODELS:
        o = out[m]
        L.append(f"| {m} | {o['treant_v1']:.1f} → {o['treant_v2']:.1f} | {o['borden_v1']:.1f} → {o['borden_v2']:.1f} | "
                 f"{o['recomputed']:.2f} → {o['exact']:.2f} |")
    L.append("")
    L.append("- **Treant Forest.** The raw score is unchanged; v2 maps it with `linear` 3,418 → 92,304 "
             "instead of `piecewise_max`. All five published scores lie below 20, the linear segment of the "
             "old scale, so each converts exactly: raw = 5,369 + s/20 × 82,820. A leaderboard value that is "
             "itself a mean of several runs converts exactly as well, because the segment is linear. The one "
             "caveat is a run between 20 and 21.02, which falls on the next segment.")
    L.append("- **Borden Inversion.** v1 had no rescale, so the published value is the raw score (0–109). "
             "v2 reports raw × 100/109. This is only the scale part. v2 also tells the solver the judge's "
             "physics convention, which raises honest fits (7.0 → 31.2 raw in our controls). That part "
             "needs new runs and is not included.")
    L.append("- **Dabic Inversion** is excluded, so it leaves the mean, which is then taken over 50 tasks "
             "(49 for Opus 4.8, which has no valid Rust Multicrate result).\n")

    L.append("## Every repaired task\n")
    L.append("| Task | Effect on v1 scores | Kind | Bound (points) | Opus 4.8 | GPT-5.5 | GPT-5.4 | GLM-5.1 | DS-V4-Pro |")
    L.append("| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for t in sorted(effects):
        e = effects[t]
        b = "" if e.get("bound") is None else f"{e['bound']:g}"
        cells = " | ".join("—" if lb[t][m] is None else f"{lb[t][m]:.1f}" for m in MODELS)
        L.append(f"| [{t}](cases/{t}.md) | {e['text']} | {e['kind']} | {b} | {cells} |")
    L.append("")
    L.append("Direction is the effect of the repair on a v1 score: *up* means v1 under-credited correct "
             "work, and *down* means v1 over-credited incorrect work. A bound is clipped to each model's "
             "score (a downward effect cannot exceed it) and to any proven ceiling.\n")

    L.append("## What this does not establish\n")
    L.append("- **It is not a re-scored leaderboard.** The published submissions are not public, so no "
             "historical submission was re-scored under v2.")
    L.append("- **It does not cover the 134-task benchmark.** The full leaderboard includes 83 unreleased "
             "tasks, which this release did not examine.")
    L.append("- **Neither range is an estimate.** The documented-bounds range is the largest movement we "
             "proved or demonstrated. The worst case lets every open repair take its full range.")
    L.append("- **Recomputed means differ slightly from the published ones** (by at most "
             f"{max(abs(o['recomputed'] - o['published']) for o in out.values()):.2f}), because the per-task "
             "table is rounded to one decimal. All adjustments are applied to the recomputed means.")
    L.append("- **v2 scores are a different benchmark version.** These figures show how much the defects "
             "matter. They are not a substitute leaderboard.")
    (ROOT / "evidence/impact/site-note.txt").write_text(
        f"Every model gains {min(shifts):.1f}–{max(shifts):.1f} points from the exact adjustments and the "
        "ranking is unchanged. " + (f"Within the documented bounds, {' and '.join(fragile)} could swap: "
        "the published gap is smaller than the bounds." if fragile else "No pair can swap within the documented bounds.") + "\n")
    (ROOT / "IMPACT.md").write_text("\n".join(L) + "\n")
    json.dump(out, sys.stdout, indent=1)


if __name__ == "__main__":
    main()
