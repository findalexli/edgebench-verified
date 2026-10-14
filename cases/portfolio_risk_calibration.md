# Portfolio Risk Calibration (`portfolio_risk_calibration`)

**Outcome:** Fixed. <mark>The original grader computes yearly excess return by converting the difference of the two period returns to a yearly figure, instead of taking the difference of the two yearly returns as the instructions state. The fixed version uses the stated formula. A restricted decimal sweep on the full test period found a largest joint rise of 0.3913 points and a sampled envelope of 0.3921; this is not a global bound. Lean preserves the order and sign of excess values for a fixed benchmark and exponent under domain assumptions, not total-score ordering.</mark>

## What the task asks

The solver builds a portfolio strategy. The grader backtests it, that is, runs it on past market data, and compares it with a benchmark index. The task instructions define the convention explicitly:

- "Excess return = strategy annualized return - benchmark annualized return."
- "Information ratio = annualized excess return / tracking error."
- "Sortino ratio = annualized excess return / downside deviation."

An excess return of 12% or more earns full marks for that part of the score, and a negative excess is deducted. Category: Professional Knowledge Work.

## What goes wrong

**The grader uses a different formula from the one stated.** Finance has several accepted definitions of excess return, but the instructions choose one: the difference of the two annualized (yearly) returns. The original grader instead subtracts the benchmark's return over the period from the strategy's return over the period. It then converts that difference to a yearly figure with the exponent 252/N, where N is the number of daily NAV (net asset value) points and 252 is the number of trading days in a year. The two agree only when the exponent is 1.

**Small example.** With 126 NAV points, a strategy return of +20% and a benchmark return of +10%:

- The original grader gives **0.21**. The formula in the instructions gives **0.23** (exactly 21/100 and 23/100).
- Both values are above the 12% cap, so both score 20/20.

**The real test period is much closer to 252 days.** The hidden test period is fixed at about 242 NAV days, so the exponent is 252/242 = 1.0413, not 2. The 126-point example makes the gap roughly 50 times larger than what a real submission sees.

**The supplied example under the original grader:**

| Quantity | Value |
| --- | --- |
| Strategy return over the period | 15.87% |
| Benchmark return over the period | 24.80% (over the 242 dates this submission shares with the benchmark; 24.28% over 243, the count in the side-by-side arms) |
| Excess, original grader | −9.284% |
| Excess, formula in the instructions | −9.373% |
| Excess score, original grader vs instructions | −9.284 vs −9.373 |
| Final total | 0/100 either way: the anti-fraud checks zero its core score, and the penalties (constraint violation 5, anti-fraud 28, short effectiveness 10) take the total to 0 (`evidence/runs/portfolio_risk_calibration-v2-paired/result/out/summary_parsed.txt`, arm `e_example`, both graders) |

The information ratio and the Sortino ratio both divide the excess return by a risk measure, so they change too.

**A separate small inconsistency (no effect on scoring).** The exported `annual_return` uses 241 return intervals, while `benchmark_annual_return` uses 242 NAV points.

The original grader's figure is not the one a solver following the instructions computes for itself. A test strategy that reports its own excess as 3.47% by the instructions' formula is shown 3.44% by the original grader.

## How much it matters

- A finite 50-digit decimal sweep over strategy returns from −30% to +100% and N = 242 or 243 shared dates found a largest sampled joint rise of **0.3913** points and fall of **0.10**. Its envelope allowing arbitrary risk measures at each sampled strategy return, with rounding slack, is **0.3921** (`repairs/portfolio_risk_calibration-v2/paired/bound.out`). This considers all three affected score parts at the same strategy return and includes the grader's 4-decimal rounding. Neither the grid nor the envelope proves a maximum between grid points, for other date counts, or outside the sampled return range. Use +0.3921/−0.10 only as an explicit sensitivity assumption; it is not a bound for every valid submission.
- The largest gap is just below the 12% full-marks line. A strategy whose excess is exactly 12% by the instructions' formula gets 19.85 of 20 excess points from the original grader and 20.00 from the fixed version (installed functions, `paired/results.md`).
- The gap in the excess value itself is at most about 0.56 percentage points for strategy returns from 0% to +100%, and up to about 0.71 points at −30%, where both excess scores are already at the floor of −10 (float64 sweep, `evidence/scripts/portfolio_risk_calibration/sensitivity.out`).
- The exponent is 252/N, where N is the number of the submission's NAV dates shared with the benchmark (`eval_script.py:915-928`). The numerical sweep above covers only N = 242 or 243, the full test period.
- For a fixed benchmark, both formulas rank excess returns in the same order, for every real exponent k > 0, given 1 + a > 0 and 1 + a − b > 0, and they have the same sign when also b > −1, where a and b are the strategy and benchmark returns over the period (proved in Lean, below). The fix does not reorder strategies by excess return or move the 0% deduction line.

## The fix

The fixed version changes one file, `/home/workspace/scoring/eval_script.py`, by 2 lines. The original grader already annualizes the benchmark as (1 + b)^(252/N) − 1 over the N dates the strategy and benchmark share. The fix annualizes the strategy's period return the same way over the same dates and subtracts the two. That is the stated "strategy annualized return − benchmark annualized return". The information ratio and the Sortino ratio use the corrected value, as the instructions define them. These are unchanged: the score thresholds, the tracking error, the downside deviation and the exported `annual_return`, which is only printed. In the task JSON, only `judge.image_tag` changes (`08fe0a4bad80` → `08fe0a4bad80-ebv-v2`).

| # | Test submission | Original grader | Fixed version | Expected |
| --- | --- | --- | --- | --- |
| 1 | **Our strategy, following the instructions** (full grader) | 32.45; excess 3.44% | **32.52**; excess 3.47%, equal to its own figure | gains ✔ |
| 2 | Same trades, reporting the original grader's formula (full grader) | 32.45 | 32.52 | same as 1; the self-report is not scored ✔ |
| 3 | Wrong: momentum signal reversed (full grader) | 0; excess −21.14% | 0; excess −21.33% | stays low ✔ |
| 4 | Starter: the work image as shipped (no `portfolio_optimizer.py`) | 0 | 0 | unchanged ✔ |
| 5 | Image's own example strategy (full grader) | 0; excess −9.28% | 0; excess −9.37% | unchanged total ✔ |
| 6 | **Excess exactly 12% by the instructions' formula** (installed functions) | excess part 19.85; three parts 26.47 | **20.00**; 26.70 | full marks ✔ |
| 7 | Excess exactly 12% by the original grader's formula (installed functions) | 20.00 | 20.00 | unchanged ✔ |
| 8 | Strategy equal to the benchmark (installed functions) | 0 | 0 | unchanged ✔ |

Source: `repairs/portfolio_risk_calibration-v2/paired/results.md`. Rows 1–5 are the task's own `score.py`; rows 6–8 call each image's installed metric and score functions on NAV paths we wrote.

**Are scores comparable?** Not exactly. The sampled changes are small in the stated full-period domain, but no global score-difference bound was established. Rankings by excess value are unchanged only for a fixed benchmark and exponent under the theorem hypotheses; this does not establish total-score ranking compatibility.

## How we checked it

- **Original and fixed graders, side by side.** Both ran on the same inputs, three times on fresh E2B workers, each grader container at `--network none --memory 2g --cpus 2`. The full `score.py` ran on five submissions, and the installed metric and score functions ran on five NAV paths we wrote. All three runs gave identical results (`paired/results.md`; jobs `evidence/runs/portfolio_risk_calibration-v2-paired`, `-rep2`, `-rep3`).
- **Independent oracle.** Both formulas were recomputed in 60-digit decimal arithmetic (`paired/oracle.py`, output `oracle.out`). They match every installed value. For row 6 the oracle gives 0.1200000000 by the instructions' formula and 0.1190841879 by the original grader's.
- **Size sweep.** `paired/bound.py` sweeps strategy returns from −30% to +100% in 50-digit decimal arithmetic for N = 242 and 243 (`bound.out`). The largest sampled joint rise is 0.3913, the sampled envelope with slack is 0.3921, and the sampled fall is 0.10. These are restricted numerical results, not global bounds.
- **Earlier reproduction.** The full original scoring pipeline (from the task's manifest) ran in the grader image (`--network none --memory 2g`) with the image's supplied example optimizer. The installed metric function was called on constant-growth NAV paths of 126, 243 and 252 points, and strategy returns from −30% to +100% were swept against the real benchmark (24.80% over 242 shared dates) with the grader's scoring functions.
- **Lean 4 (a proof checker).** `PortfolioOrderRealExp.lean` models the stated formula, which is the fixed version's formula with one exponent. It proves, with real powers, that the fixed excess rises strictly with the strategy's return (`eC_strictMono`), and that for a fixed benchmark the fixed and original formulas rank any two strategies in the same order (`same_order`), and that the fixed formula has the same sign as the original (`same_sign`, with one exponent and b > −1), for every real k > 0, given 1 + a > 0 and 1 + a − b > 0. The fixed grader's exponents on the test period, 252/242 and 252/243, are covered because the theorems hold for every k > 0 (the instance lemma `k_real_pos` checks 252/242 and 252/241; 252/241 is the exponent of the exported `annual_return`, which no score uses). `FinanceExcessFx.lean` proves the k = 2 identities. All proofs use only the standard axioms and no `sorry` (an unproved placeholder).

## Limits

- No AI model or solver was run. The full-grader arms are a test strategy we wrote (its exposure setting chosen by us after looking at the test period) and the image's own example.
- Our test strategy reaches 3.5% excess, not the 12% cap. The cap is checked through the installed functions on NAV paths we wrote, not through the full grader.
- The +0.3921/−0.10 sensitivity scenario comes from a restricted decimal sweep, not a proof of a global bound. Lean covers order and sign only, not the size or direction of the change, and the link from the Lean model to the code is by a source-line note.
- Other possible issues in this task were not reviewed here.

## Reproduce

- Original grader image: `sha256:42997fb57705…`. Fixed version: `repairs/portfolio_risk_calibration-v2/` (`./materialize.sh && docker build .`).
- Side-by-side run: `repairs/portfolio_risk_calibration-v2/paired/run.sh`; jobs `evidence/runs/portfolio_risk_calibration-v2-paired`, `-rep2`, `-rep3`; oracle `paired/oracle.py`; size sweep `paired/bound.py`.
- Earlier reproduction: `evidence/scripts/portfolio_risk_calibration/` (`witness.py`, `run_full.sh`, `posthoc.py`, `sensitivity.py` and their `.out` files).
- Lean: `evidence/formal/lean/ebv/Ebv/FinanceExcessFx.lean`, `PortfolioOrderRealExp.lean`; note `evidence/formal/notes/portfolio_risk_calibration.md`.
- Supporting records: `evidence/reviews/portfolio_risk_calibration.md`.
