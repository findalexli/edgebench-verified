#!/usr/bin/env python3
"""Estimate how the v1.0 findings move EdgeBench's published 51-task @12h means.

Inputs: the per-task @12h leaderboard in tasks/README.md (the publisher's numbers) and
evidence/impact/effects.json (direction and size of each repaired task's effect, taken
from its case page). Outputs IMPACT.md and data/impact.csv.

Three kinds of adjustment, kept separate:
  scale    - an interval allowing rounded averages and noninvertible clipping
  bounded  - documented conditional limits; sensitivity - an unproved numerical scenario
  open     - direction known, size requires re-scoring the original submissions
"""
import csv
import json
import math
import pathlib
import sys
from fractions import Fraction

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


def exact(x):
    """The exact rational value of a published decimal (or an int or Fraction)."""
    return x if isinstance(x, Fraction) else Fraction(str(x))


def treant_cap_score(num=float):
    return num(20) + num(60) * (num(92304) - num(88189)) / (num(330195) - num(88189))


TREANT_CAP_SCORE = treant_cap_score()


def treant_interval(s, rounding=0.05, num=float):
    """Outer bounds on the mean repaired score from a rounded mean original score.

    On the reachable original-score domain [0, cap], each run's repaired score
    lies above the chord (0,0)--(cap,100) and below the affine inverse of the
    first segment. Both bounds are affine, so they survive averaging regardless
    of the number of valid runs or which runs meet clipping/segment boundaries.
    This assumes the documented raw-total cap 92304 and fixed valid-run set.
    """
    cap, s, rounding = treant_cap_score(num), num(s), num(rounding)
    low, high = max(num(0), s - rounding), min(cap, s + rounding)
    if low > high:
        raise ValueError("score outside reachable Treant domain")
    return (num(100) * low / cap,
            min(num(100), num(100) * (num(1951) + num(4141) * high) / num(88886)))


def borden_v2(s, num=float):
    # v1 had no rescale (published value is the raw score, 0..109); v2 is linear 0..109.
    return num(100) * num(s) / num(109)


def scale_intervals(lb, model, num=float):
    """Retained task intervals, including one-decimal rounding uncertainty."""
    result = {}
    for task, row in lb.items():
        score = row[model]
        if score is None or task == "dabic_gravity_inversion":
            continue
        score, r = num(score), num(.05)
        if task == "treant_forest":
            result[task] = treant_interval(score, num=num)
        elif task == "borden_source_inversion":
            result[task] = (borden_v2(max(num(0), score - r), num),
                            borden_v2(min(num(109), score + r), num))
        else:
            result[task] = (max(num(0), score - r), min(num(100), score + r))
    return result


def effect_intervals(intervals, effects, kinds, num=float):
    """Conservative per-task propagation; never assume simultaneous attainment."""
    result = dict(intervals)
    for task, effect in effects.items():
        if task not in result or effect["kind"] not in kinds:
            continue
        low, high = result[task]
        default = effect.get("bound")
        default = num(100) if default is None else num(default)
        if effect["direction"] in ("down", "either"):
            low = max(num(0), low - num(effect.get("bound_down", default)))
        if effect["direction"] in ("up", "either"):
            high = max(high, min(num(effect.get("ceiling", 100)), high + num(effect.get("bound_up", default))))
        result[task] = (low, high)
    return result


def average_interval(intervals):
    return tuple(mean(x[i] for x in intervals.values()) for i in (0, 1))


def ranking_certified(higher, lower):
    """Disjoint outer intervals certify order; overlap does not prove reversal."""
    return higher[0] > lower[1]



def outward(value, kind, places=9):
    """Decimal string of an exact endpoint, rounded outward (down for _low, up for _high)."""
    scaled = exact(value) * 10 ** places
    n = math.floor(scaled) if kind == "low" else math.ceil(scaled)
    sign, n = ("-" if n < 0 else ""), abs(n)
    return f"{sign}{n // 10 ** places}.{n % 10 ** places:0{places}d}"


def interval_rows(lb, effects, num=float):
    """Per model: mean endpoints of the four interval kinds, in the number type `num`."""
    # A finite sweep is not a global bound: use the full score domain in the outer range.
    outer_effects = {t: (dict(e, kind="open", bound=None, bound_up=100, bound_down=100)
                         if e["kind"] == "sensitivity" else e) for t, e in effects.items()}
    rows = {}
    for model in MODELS:
        scale = scale_intervals(lb, model, num)
        bounded = effect_intervals(scale, effects, {"bounded"}, num)
        sensitivity = effect_intervals(bounded, effects, {"sensitivity"}, num)
        outer = effect_intervals(bounded, outer_effects, {"open"}, num)
        row = {"tasks_in_mean": len(scale)}
        for name, intervals in [("scale", scale), ("bounded", bounded),
                                ("sensitivity", sensitivity), ("worst_case", outer)]:
            row[name + "_low"], row[name + "_high"] = average_interval(intervals)
        rows[model] = row
    return rows


def write_impact_csv(out, path):
    """Write interval endpoints as exact decimals rounded outward (9 places), so the CSV interval
    always encloses the exact rational interval; other floats with 6 places."""
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(next(iter(out.values()))), lineterminator="\n")
        writer.writeheader()
        for row in out.values():
            writer.writerow({k: outward(v, "low" if k.endswith("_low") else "high")
                             if k.endswith(("_low", "_high")) else
                             (f"{v:.6f}" if isinstance(v, float) else v) for k, v in row.items()})


def main():
    lb = parse_leaderboard()
    effects = json.loads((ROOT / "evidence/impact/effects.json").read_text())
    decisions = {d["task_id"]: d for d in json.loads((ROOT / "data/decisions.json").read_text())}
    assert len(lb) == 51 and set(lb) == set(decisions)
    assert {t for t, d in decisions.items() if d["proposed"] != "retain-with-note"} == set(effects)
    # Endpoints are computed in exact rational arithmetic from the published decimals.
    exact_rows = interval_rows(lb, effects, exact)
    out = {}
    for model, r in exact_rows.items():
        out[model] = dict(model=model, published_mean=PUBLISHED[model],
                          recomputed_mean=mean(row[model] for row in lb.values()),
                          scale_midpoint_mean=float((r["scale_low"] + r["scale_high"]) / 2),
                          **{k: r[k] for k in ("scale_low", "scale_high", "bounded_low", "bounded_high",
                                               "sensitivity_low", "sensitivity_high",
                                               "worst_case_low", "worst_case_high")},
                          tasks_in_mean=r["tasks_in_mean"])
    write_impact_csv(out, ROOT / "data/impact.csv")
    n_open = sum(e["kind"] == "open" for e in effects.values())
    n_bounded = sum(e["kind"] == "bounded" for e in effects.values())
    pairs = list(zip(MODELS, MODELS[1:]))
    bounded_cert = [ranking_certified((out[a]['bounded_low'], out[a]['bounded_high']),
                                      (out[b]['bounded_low'], out[b]['bounded_high'])) for a, b in pairs]
    full = [ranking_certified((out[a]['worst_case_low'], out[a]['worst_case_high']),
                              (out[b]['worst_case_low'], out[b]['worst_case_high'])) for a, b in pairs]
    L = ["# Effect on the published leaderboard", "",
         "The public task averages are not enough to compute a corrected leaderboard, because the original submissions and the raw scores of each run are not available. The intervals below carry the rounding of the public scores, the scale changes and the documented effect limits through to each model's average. They are outer envelopes. They are not estimates, and we have not shown that their endpoints can be reached. `tools/estimate_impact.py` generates this page; [data/impact.csv](data/impact.csv) has the machine-readable results.", "",
         "## Conditional score intervals", "",
         "Every interval keeps the same set of valid runs and treats kept tasks as unchanged. Each one depends on the effect directions and limits listed below, including the inferred PFR credit and the documented cap on Treant's raw total. The 'Plus documented limits' and 'Plus Portfolio sensitivity' columns count every direction-only (open) effect as zero; only the full-domain envelope lets those effects move. New runs, changed failure rates, agents adapting to a fix, or an unsupported assumption about an effect's direction can break these conditions. None of the intervals is a statistical confidence interval.", "",
         "| Model | Published mean | Scale changes and removal | Plus documented limits | Plus Portfolio sensitivity assumption | Full-domain outer envelope |",
         "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for model, row in out.items():
        ranges = [f"{math.floor(row[a]*100)/100:.2f}–{math.ceil(row[b]*100)/100:.2f}" for a,b in
                  [("scale_low","scale_high"),("bounded_low","bounded_high"),
                   ("sensitivity_low","sensitivity_high"),("worst_case_low","worst_case_high")]]
        L.append(f"| {model} | {row['published_mean']:.1f} | " + " | ".join(ranges) + " |")
    L += ["", "`scale_midpoint_mean` in the CSV is a midpoint for display, not an inferred corrected mean. The CSV endpoints are the exact rational endpoints rounded outward to 9 decimals, so each CSV interval contains the exact one. In the full-domain envelope, open effects can span the rest of the score range in their stated directions, and Portfolio gets the full 0–100 range because its sweep does not establish a global bound.", "",
          "## What can be recovered from an average", "",
          "- **D-ABIC:** remove the task; the denominator becomes 50 (49 for Opus 4.8, whose Rust result is missing).",
          "- **Borden:** multiply the rounded raw average by 100/109 and carry the ±0.05 rounding through. The conversion is affine, so it gives the same result before or after averaging. The separate effect of the instruction repair still needs new runs.",
          "- **Treant:** an average below 20 does not show that every run fell on the first linear segment. Because of zero-score clipping and the second segment, inverting the scale directly is unsound. Let C = 20 + 60(92304−88189)/(330195−88189), approximately 21.02022. For each reachable per-run original score s, the repaired score lies between 100s/C and min(100,100(1951+4141s)/88886). The lower chord lies below both linear segments and permits zero at the clipped endpoint; the upper affine line lies above both segments and above the clipped endpoint. Averaging preserves the affine inequalities. We apply the lower bound to max(0,published−0.05) and the upper bound to min(C,published+0.05). These conservative bounds need neither raw scores nor an assumption that all runs occupy the same segment. They use the documented upper bound of 92,304 and do not assume the cap can be reached.",
          "- **Rounding:** each kept task's one-decimal score is enclosed by ±0.05, clipped to its score domain, and this uncertainty is carried through the mean.", "",
          "## Does this certify the model order?", "",
          "If the higher model's lower endpoint is above the lower model's upper endpoint, their order is certified under the stated assumptions. If the outer intervals overlap, these bounds cannot certify the order. That does not show a reversal is possible, because the individual maxima may be unattainable or incompatible with one another.", "",
          f"The documented-limit column uses only the {n_bounded} bounded effects and counts the {n_open} direction-only (open) effects as zero, so an order it certifies holds only if those {n_open} fixes have no effect on the score. The full-domain column lets the open effects span their stated directions; "
          + ("in that envelope every neighbouring pair overlaps, so no order is certified." if not any(full) else "it certifies only the pairs marked Yes."), "",
          f"| Neighbouring models in published order | Certified by documented limits, with the {n_open} direction-only effects counted as zero? | Certified within the full-domain envelope? |",
          "| --- | --- | --- |"]
    for (higher, lower), c_bounded, c_full in zip(pairs, bounded_cert, full):
        L.append(f"| {higher} > {lower} | "
                 f"{f'Yes, only if the {n_open} direction-only fixes have no effect' if c_bounded else 'No; overlap does not establish reversal'} | "
                 f"{'Yes' if c_full else 'No; overlap does not establish reversal'} |")
    L += ["", "## Portfolio sensitivity is separate from a proved limit", "",
          "The saved decimal sweep covers only N=242 or 243 shared dates and strategy period returns from −30% to +100%. Its largest sampled joint rise is 0.3913; its sampled envelope with risk-measure and rounding slack is 0.3921. The sampled fall is 0.10. We show a separate scenario assuming +0.3921/−0.10 applies to the hidden submissions. Neither the grid nor Lean establishes this as a global bound. Lean proves the order and sign of the excess values for a fixed benchmark and exponent under domain hypotheses. It does not prove the ordering of total scores or the size of the score change. The details are in [the case](cases/portfolio_risk_calibration.md) and the [saved sweep](repairs/portfolio_risk_calibration-v2/paired/bound.out).", "",
          "## Every repaired or removed task", "",
          "| Task | Effect assumption and evidence | Classification | Per-task limit or scenario |",
          "| --- | --- | --- | ---: |"]
    for task, effect in sorted(effects.items()):
        bound = effect.get('bound')
        limit = "—"
        if bound is not None:
            parts = []
            if effect['direction'] in ('up', 'either'):
                parts.append(f"+{effect.get('bound_up', bound):g}")
            if effect['direction'] in ('down', 'either'):
                parts.append(f"−{effect.get('bound_down', bound):g}")
            limit = "/".join(parts)
        L.append(f"| [{task}](cases/{task}.md) | {effect['text']} | {effect['kind']} | {limit} |")
    L += ["", "## Evidence and limits", "",
          "The publisher normalizes each run's score, keeps its best submission and averages the valid runs, as [the scoring-method record](evidence/impact/edgebench-scoring-method.md) describes. The scale intervals keep that set of runs, and they do not simulate how agents respond to new instructions or feedback.", "",
          "We separately regraded third-party four-hour Opus 5.5 runs ([the saved regrade summary](evidence/runs/opus55-regrade2-summary/summary.json)). They show that some defects matter in real agent runs, but they are not a regrade of this twelve-hour leaderboard. The audit covers only the 51 public tasks; the publisher also has 83 unreleased tasks. The repairs form a new version of the benchmark."]
    (ROOT / "IMPACT.md").write_text("\n".join(L) + "\n")
    json.dump({m: {k: (float(v) if isinstance(v, Fraction) else v) for k, v in r.items()} for m, r in out.items()},
              sys.stdout, indent=1)


if __name__ == "__main__":
    main()
