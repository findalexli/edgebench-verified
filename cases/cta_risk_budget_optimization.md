# CTA risk budget optimization (`cta_risk_budget_optimization`)

**Outcome:** Fixed in v2.1. <mark>The overseas limit check added US-dollar and yuan values without converting and divided by gross notional instead of fund NAV. v2.1 converts to yuan and divides by same-date total NAV; through the full original scoring command it moves a leveraged breaching portfolio from 58.75 to 53.75 and a compliant unleveraged one from 66.25 to 71.25, in three runs.</mark>

![Bars show an overseas share of 0.175 as the original grader reads it, passing the 0.40 limit, against 0.595 once US-dollar positions are converted to yuan, which breaches it.](figures/cta_risk_budget_optimization.svg)

*The original grader added dollar and yuan values without converting, so a portfolio at 0.595 overseas looked like 0.175 and passed the 40% limit.*

## What the task asks

The agent builds a backtesting engine (a simulator that replays past prices) for futures. The task instructions ask for a "Multi-currency, multi-market, multi-instrument backtesting engine". They also ask for "Handling of … exchange rates" and for "single-instrument/sector/overseas exposure … risk constraints".

The input risk policy (`risk_policy_doc.docx`, in Chinese) sets the overseas limit at 40% ("境外投资比例不超过基金净值的40%"). It also requires that "所有境外品种的仓位计算必须使用实时汇率折算为人民币等值": every overseas position must be converted to its RMB (yuan) equivalent at the live exchange rate. Category: Professional Knowledge Work.

## The fix (v2.1): convert to yuan and divide by fund NAV

The grader's `_check_schema_compliance` requires submitted NAV to be total CNY capital (approximately 1.5 billion), not unit NAV. Its `_compute_exposure_stats` already uses the `date` and `nav` fields. v2.1 changes one file, `/home/workspace/scoring/eval_script.py`. In the cross-border block it converts USD positions to CNY at the grader's own USDCNY series and divides overseas CNY notional by the same-date total CNY NAV. The 40% threshold, the day-count allowance (no violation day: 2 ratio checks; under 2% of days: 1; otherwise 0), the other risk gates and the score mapping are unchanged. In the task JSON, only `judge.image_tag` changes (`a9651058ecef-ebv-v2.1`).

**Holdings dates without a same-date NAV.** No denominator is invented or forward-filled. A holdings date whose same-date NAV is missing, nonfinite or nonpositive counts as one violation day, like a day over the limit, under the original under-2% allowance. A first v2.1 candidate instead removed all ratio credit if any single date lacked a NAV. The shipped standard answer's 1565 holdings dates all have a same-date NAV, but a good-faith engine can easily write one holdings date its NAV file lacks, and the strict rule then scored a compliant portfolio like a breaching one. That candidate was replaced before release; it is kept as `paired/superseded-v2.1-strict-nav.patch`.

**Side-by-side test through the full original scoring command.** Three E2B jobs built the v2.1 image from the package (`materialize.sh` and `docker build`) and ran the task's original `eval_cmd` (`cd /home/workspace && python3 scoring/score.py`) at `--network none --memory 3g --cpus 2`. The full test submissions are a synthetic constant-weight portfolio (`paired/full_submission/main.py`) whose NAV, positions, trades, costs and FX follow the grader's own replay (authenticity check 10/10), with volatility, drawdown and participation inside the risk gate, so the cross-border check is actually reached. Scores are out of 100:

| Test submission | Original grader | Fixed grader (v2.1) |
|---|---|---|
| shipped standard answer | 20 (risk part cancelled: annual volatility 1.3%) | 20, same |
| leveraged: overseas 45% of NAV, 37.5% of CNY gross | 58.75, `cross_border` 5 | **53.75**, `cross_border` 1 |
| unleveraged: overseas 28% of NAV, 87.5% of CNY gross | 66.25, `cross_border` 1 | **71.25**, `cross_border` 5 |
| unleveraged, last NAV row missing (1 of 1564 dates) | 66.25, `cross_border` 1 | 68.75, `cross_border` 3 (strict candidate: 66.25) |

All three jobs gave the same scores. The original grader passes the leveraged portfolio, which breaches the 40%-of-NAV limit on every day, and fails the unleveraged one, which complies on every day; v2.1 reverses both. Only `cross_border` moves, by 4 of 80 raw points (5 of 100). See [results](../repairs/cta_risk_budget_optimization-v2/paired/results.md) and [package instructions](../repairs/cta_risk_budget_optimization-v2/README.md).

Component checks also pass: the genuine original, FX-only, strict and current risk helpers on ten single-day and three 100-day NAV-date controls, against an exact rational oracle ([candidate results](../repairs/cta_risk_budget_optimization-v2/paired/nav-candidate-results.json)).

**Score compatibility.** For portfolios that hold overseas contracts, v2.1 scores are not comparable with original scores: the cross-border component can move by up to 5 points out of 100 in either direction. Domestic-only portfolios with a same-date NAV for every holdings date score identically.

## Historical FX-only finding and evidence

The remainder of this page records the earlier FX-only repair and its evidence. Its “fixed grader” is the superseded `a9651058ecef-ebv-v2`, not the current `v2.1`. Earlier tests omitted NAV and do not validate the new denominator.

## What goes wrong

**The overseas check skips currency conversion.** The grader recomputes each position's notional value (its face value) as `lots × multiplier × close` from the raw price sheets. All 12 overseas tickers are priced in USD. The grader converts with the USDCNY exchange rate in its profit-and-loss replay and in `_compute_exposure_stats`. The cross-border block leaves the conversion out. This contradicts the policy document's rule that positions be counted in RMB. USDCNY in the data runs from 6.757 to 7.157 (mean 7.004).

- Minimal example (synthetic): 2 lots in CNY and 1 lot in USD, with price and multiplier 1 and USDCNY 7. The overseas share in CNY is 7/9, which breaches 40%. The original grader computes 1/3 and records 0 violations.
- Real data, 2021-06-01: 10 lots CU.SHF plus 8 lots GC.CME give an overseas share in CNY of 0.595. The grader reads 0.175, so this case also passes.
- The task's own reference: converted at USDCNY, the shipped standard-answer positions exceed 40% on 32 of 1565 days, with a maximum of 52.1%. The original check reports 0 violations and full ratio credit.

A separate observation, not fixed by historical v2 (fixed by v2.1 above): the policy states the limit as "40% of fund NAV" (net asset value). The grader instead uses the overseas share of gross notional value. This is a separate question from the currency issue.

## Historical FX-only score effect

Up to 5 points out of 100 (4 of 80 raw points), and only in the generous direction. Because USDCNY is above 1, the bug can award ratio credit to a portfolio that breaches the limit. It never penalizes a compliant one. Only solvers holding USD contracts are affected. Other checks can cap or cancel the risk part of the score and hide the swing.

## The historical FX-only fix

The fixed version changes one file, `/home/workspace/scoring/eval_script.py` (+11/−1 lines). Inside the cross-border block, USD-priced tickers are multiplied by USDCNY from the grader's own `fx` data, looked up as of the date. The fallback is 7.0. This is the same series and fallback the existing `fx_for` helper uses.

These are unchanged: the 40% threshold, the day-count rules, the `cb_checks` mapping and the question of NAV against gross notional value. Same-currency portfolios are numerically unchanged. In the task JSON, only `judge.image_tag` changes.

In the table, "violations" counts days over the limit, and `cross_border` (or "cb") is the score of the cross-border check. "cost_fx" is the score of the grader's separate costs-and-exchange-rate check, which the test sets to 0 or 2.

| # | Test submission | Input | Original grader | Fixed grader | Expected |
|---|---|---|---|---|---|
| 1 | **Shows the problem (synthetic)** | 2 lots CNY + 1 lot USD, price and multiplier 1, USDCNY 7. Share is 1/3 unconverted, 7/9 in CNY | violations 0/1; `cross_border` **1** (cost_fx 0) / **5** (cost_fx 2) | violations **1/1**; `cross_border` **0** / **1** | the original grader wrongly passes the 40% limit, the fixed grader fails it ✔ |
| 1b | **Shows the problem (real data)** | 2021-06-01: 10 lots CU.SHF + 8 lots GC.CME. Share is 0.175 unconverted, 0.595 in CNY | violations 0/1; cb **1 / 5** | violations **1/1**; cb **0 / 1** | ✔ |
| 2 | Correct test submission, one currency | domestic only (2 lots CU.SHF) | 0/1; cb 1 / 5 | 0/1; cb 1 / 5 | unchanged ✔ |
| 2b | Correct test submission, mixed currencies, under the limit | real data, 10 CU + 2 GC. Share 0.050 unconverted, 0.269 in CNY | 0/1; cb 1 / 5 | 0/1; cb 1 / 5 | unchanged ✔ |
| 2c | Invalid test submission (over the limit even unconverted) | synthetic 1 CNY + 1 USD (1/2 unconverted, 7/8 CNY); real 10 CU + 30 GC (0.443 / 0.847) | 1/1; cb 0 / 1 | 1/1; cb 0 / 1 | rejected by both ✔ |
| 3 | Shipped reference positions (this check only) | `standard_answer_artifacts.tar.gz` `backtest_results/positions.csv` + `trades.csv`, 1565 days | violations **0/1565**; cb **1 / 5** | violations **32/1565** (2.04%); cb **0 / 1** | changes, explained below |
| 4 | **Full original grader, complete shipped reference** | the whole `standard_answer_artifacts.tar.gz` extracted into `/home/workspace` | TOTAL_SCORE **20.0** (raw 16/80); M1 4, M2 0, **M3 0** ("Veto: annual vol 1.3% outside [5%,20%]"), M4 2, M5 10; valid, pass_rate 1.0, exit 0 | **identical**: 20.0, the same metric breakdown, the same veto. Logs are identical apart from timings | unchanged ✔ |

Row 3 changes as intended. 32/1565 is not below the 2% day-count allowance, so the fixed grader awards 0 ratio checks instead of 2. The grader counts 1565 dates because it includes 2020-01-02, on which every position in `positions.csv` has 0 lots; `reference_positions_share.py` drops zero-lot rows first and counts 1564. Both find 32 violating days (2.04% and 2.05%), so the conclusion is the same. Row 4 is unchanged because the full grader cancels the whole risk part (M3) of the shipped reference for its annual volatility of 1.3%, before the cross-border score is used. The fix is therefore verified on this check alone, not end to end.

**Score compatibility.** Some submissions hold overseas (USD) contracts whose share, converted at USDCNY, exceeds 40% on at least one day. For those, fixed-version scores are not comparable with original scores. They can lose cross-border ratio credit, up to 4 of 80 raw points (5 points out of 100). Only the `cross_border` part inside M3 can change, and only downward. Same-currency portfolios score identically.

## How we checked it

- **Full original scoring command (v2.1).** The original image (pinned by digest) and the v2.1 image built from the package in the worker ran the task's `eval_cmd` on the three full test portfolios in three separate E2B jobs, and on the standard answer in the first job only, `--network none --memory 3g --cpus 2` (each ledger `exit=0`); the portfolio scores matched across the three jobs. The first job also ran the superseded strict v2.1 candidate.
- **Original grader (historical FX-only checks).** The checks ran on the original public image, pinned by digest, with `--network none --memory 2g --cpus 1`. We imported the installed `eval_script.py` and called the original `_evaluate_risk_constraints`. Two inputs were set so the cross-border block could be reached. The participation check was stubbed to pass. `nav_history` was left out, so the volatility/drawdown cancellation could not fire. The cross-border code itself was not modified. The full original `score.py` also ran on the shipped reference (row 4).
- **Exact arithmetic.** Shares were computed with Python `Fraction`.
- **Lean 4.** Lean 4 is a proof assistant that checks mathematical proofs by machine. `evidence/formal/lean/ebv/Ebv/FinanceExcessFx.lean` proves the example shares (1/3 unconverted, 7/9 in CNY). It proves that the unconverted share passes the limit and the CNY share fails it. It also proves that an unconverted share of 2/5 at an exchange rate of 7 hides a CNY share of up to 14/17. No `sorry` (an unproved step) is used. The printed axiom lists (for the two share theorems and the hidden-share bound) contain only the standard axioms; the two pass/fail inequalities have no printed list. A second file, `evidence/formal/lean/ebv/Ebv/CtaFxCheck.lean`, models the fixed cross-border loop (`eval_script.py` lines 1015–1046). `fixed_iff_contract` shows that the fixed per-day test is the 40% test on yuan values; it holds by construction, because the model's yuan value is the code's own formula, which treats every non-USD ticker as CNY. `orig_violation_implies_fixed` shows that the fix can only lower credit, assuming every overseas ticker is USD-priced and every USD ticker is overseas, USDCNY ≥ 1 and non-negative notionals. In the pinned image's data these hold: all 12 `OVERSEAS_TICKERS` are `USD` in `contract_specs`, the other 18 tickers are `CNY`, USDCNY runs from 6.7571 to 7.1566 over 1565 rows, the smallest close price is 0.7753 and the smallest multiplier is 5 (`evidence/formal/notes/cta_risk_budget_optimization.md`).
- **Repeatability.** The side-by-side run of the original and fixed graders was repeated three times. No test submission changed verdict (see `data/paired-repeatability.md`).

## Limits

- No AI model or solver was run. Effects are shown only on test submissions and counterexamples we wrote, and on the shipped reference. The full test portfolios' long/short signs were chosen with hindsight so their NAV passes the drawdown and volatility gates; they are scorer controls, not strategies.
- The historical FX-only test submissions were run through the installed grader's `_evaluate_risk_constraints`, with the participation check stubbed and NAV left out. The v2.1 test submissions ran end to end through `score.py`, but they are synthetic portfolios we wrote; the only complete submission in the image is the standard answer, and its risk part is cancelled before the cross-border block.
- How often real solver submissions are affected was not measured.
- The agent's working image was not inspected for a copy of `eval_script.py`.

## Reproduce

- Original grader image: `sha256:34258d85…`.
- Reproduction on the original grader: `evidence/scripts/cta_risk_budget_optimization/repro_cross_border.py`. Fixed check: `repro_repaired.py`. Reference positions: `reference_positions_share.py`. Saved outputs are the matching `.out` files.
- Lean proofs: `evidence/formal/lean/ebv/Ebv/FinanceExcessFx.lean` and `CtaFxCheck.lean` (outputs in `FinanceExcessFx.out` and `CtaFxCheck.out`).
- v2.1 side-by-side run: `repairs/cta_risk_budget_optimization-v2/paired/run_native_v2.1.sh` with `paired/full_submission/`, jobs `evidence/runs/cta_risk_budget_optimization-v2.1-native-rep{1,2,3}`, results at the top of `paired/results.md`. Component checks: `paired/check_nav_candidate.py`.
- Historical FX-only side-by-side run: `repairs/cta_risk_budget_optimization-v2/paired/run.sh`, results in the second half of `paired/results.md`, evidence in `paired/evidence/`.
- Fix: `repairs/cta_risk_budget_optimization-v2/repair.patch`, `Dockerfile`, `source-lock.json`.
- Supporting records: `repairs/cta_risk_budget_optimization-v2/` (the folder holding the fixed version) and `evidence/reviews/cta_risk_budget_optimization.md`.
