# portfolio_risk_calibration, fixed version: excess return is computed with the formula in the instructions

## What this fixes

The task instructions define "Excess return = strategy annualized return - benchmark annualized return." The original grader does something else. It subtracts the benchmark's return over the period from the strategy's return over the period, and then converts that difference to a yearly figure. The fixed version converts the strategy's period return to a yearly figure in the same way the grader already does for the benchmark, and subtracts. The effect is small: at most about 0.4 points out of 100 on the real test period. It is still a wrong formula that can be corrected, so the task gets a fix.

### The problem in detail

See the [review](../../evidence/reviews/portfolio_risk_calibration.md) and the [case page](../../cases/portfolio_risk_calibration.md).

The instructions (`/home/workspace/input/task_instruction.md` in the judge image, sha256 `a903d236…cd191`) say, under "Benchmark composition":

> Excess return = strategy annualized return - benchmark annualized return.

They also say:

> Information ratio = annualized excess return / tracking error.
> Sortino ratio = annualized excess return / downside deviation.

The original grader (`/home/workspace/scoring/eval_script.py`, sha256 `829eeee1…a4f9b`, lines 921–928):

```python
bench_total = bench_aligned.iloc[-1] / bench_aligned.iloc[0] - 1
benchmark_annual_return = (1 + bench_total) ** (252 / len(common_idx)) - 1
agent_total = agent_aligned.iloc[-1] / agent_aligned.iloc[0] - 1
excess_total = agent_total - bench_total
excess_annual = (1 + excess_total) ** (252 / len(common_idx)) - 1
```

That is `(1 + a − b)^k − 1` with k = 252/N, where a and b are the strategy and benchmark returns over the period. The instructions call for `((1 + a)^k − 1) − ((1 + b)^k − 1)`. The two agree only when k = 1 or b = 0. The same `excess_annual` value is the numerator of the information ratio and the Sortino ratio, so those two scores change as well.

**Why the instructions are not ambiguous here.** Finance has several definitions of excess return, but the instructions pick one in so many words: a difference of two annualized returns. They do not say how to annualize. The grader already annualizes the benchmark as `(1 + b)^(252/N) − 1` over the dates the strategy and benchmark share, and the instructions use 252 trading days a year elsewhere ("daily return annualization factor sqrt(252)"; turnover "× (252 / backtest_days)"). The fix applies that same annualization to the strategy over the same dates. So the formula is fixed in code, not documented.

## What changes

One file, `/home/workspace/scoring/eval_script.py` (`repair.patch`, two lines):

```diff
                 agent_total = agent_aligned.iloc[-1] / agent_aligned.iloc[0] - 1
-                excess_total = agent_total - bench_total
-                excess_annual = (1 + excess_total) ** (252 / len(common_idx)) - 1
+                agent_annual_aligned = (1 + agent_total) ** (252 / len(common_idx)) - 1
+                excess_annual = agent_annual_aligned - benchmark_annual_return
```

Nothing else changes:
- not the score thresholds (full marks at 12%, deduction below 0%), the tracking error or the downside deviation;
- not the exported `annual_return`, which uses 241 return intervals while the benchmark uses the date count (241 vs 242, or 242 vs 243). This small difference is in a figure that is only printed; no score uses it. The fixed excess uses one date count for both returns, so it is exactly "strategy annualized return − benchmark annualized return" over the dates they share.

The task JSON changes only `judge.image_tag` (`08fe0a4bad80` → `08fe0a4bad80-ebv-v2`). The work image is unchanged. It ships no copy of `eval_script.py` (`paired/results.md`, starter inventory).

**Why minimal.** The fix changes the one expression that forms the excess return, and it reuses the grader's own benchmark annualization.

**Score compatibility.** The two formulas have the same sign. For a fixed benchmark they rank strategies' excess returns in the same order (Lean, `PortfolioOrderRealExp.lean`). On the real test data (benchmark return +24.28% over 243 shared dates, or +24.80% over 242, depending on the submission's NAV dates; k ≈ 1.04) the fixed version gives a slightly higher excess return when it is positive and a slightly lower one when it is negative. Total scores can rise by at most 0.39 points (0.3913, with the grader's 4-decimal rounding). That is a joint bound, with all three affected parts at the same strategy return; each part's own worst case (0.18 excess, 0.11 information ratio, 0.10 Sortino) occurs at a different return, and these do not add up. They can fall by at most 0.10, from the excess part only, because both ratio parts are already 0 when the excess is negative (`paired/bound.out`; a decimal sweep, not a proof). Scores from the two versions should not be mixed in a comparison that needs differences below half a point.

## How it was checked

A side-by-side run of the original and fixed graders on the same inputs, repeated on three fresh workers: [paired/results.md](paired/results.md). The fix is accepted on this check alone. A test strategy that we wrote, which follows the instructions, gains 0.07 points through the full grader (32.45 → 32.52). On authored NAV paths whose excess by the instructions' formula is exactly 12%, the excess part rises from 19.85 to 20.00. The wrong-direction strategy and the starter still score 0.

## Limits

- No AI model or solver was run. The full-grader arms use a test strategy we wrote and the image's own example strategy.
- Our honest test strategy does not reach the 12% cap, where the difference is largest. The cap is tested on authored NAV paths through the installed metric and score functions, not through the full grader.
- The bound of about 0.4 points is a 50-digit decimal sweep over strategy returns from −30% to +100%, for the fixed benchmark and both possible date counts (242 and 243). It is not a proof. The Lean results cover ordering and sign only.

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t edgebench.judge.portfolio_risk_calibration:08fe0a4bad80-ebv-v2 .
```

`materialize.sh` takes the following steps:

1. Pull the pinned image by digest, unless it is already present.
2. Extract the original file with `docker create` and `docker cp`. No container runs in this step.
3. Check the original against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of `files/eval_script.py` against `source-lock.json` → `materialize.outputs`. Any mismatch fails loudly.

After that, the `Dockerfile` builds without changes. Each paired-run worker ran `materialize.sh` before building, and it ended with "OK: all 1 output file(s) match source-lock.json" (`materialize.log` in each job).
