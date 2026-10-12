# CTA risk budget optimization (`cta_risk_budget_optimization`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Professional Knowledge Work
- **Decision:** Repair v2. The 40% overseas-exposure check adds USD and CNY notionals without currency conversion, so overseas exposure is undercounted about sevenfold. The error is lenient only and worth at most 5/100.

## What the task promises

The task instructions ask for a "Multi-currency, multi-market, multi-instrument backtesting engine". They also ask for "Handling of … exchange rates" and for "single-instrument/sector/overseas exposure … risk constraints". The input risk policy (`risk_policy_doc.docx`, in Chinese) sets the overseas limit at 40% ("境外投资比例不超过基金净值的40%"). It also requires that "所有境外品种的仓位计算必须使用实时汇率折算为人民币等值": every overseas position must be converted to its RMB equivalent at the live exchange rate.

## What we checked and how

- **Native component runs.** In the pinned judge image (`--network none --memory 2g --cpus 1`), we imported the installed `eval_script.py` and called the original `_evaluate_risk_constraints`. Two inputs were adjusted so the cross-border block could be reached: the participation gate was stubbed to pass, and `nav_history` was omitted so the volatility/drawdown veto could not fire. The cross-border code itself was not modified.
- **Code and data reading.** The evaluator recomputes notional as `lots × multiplier × close` from the raw price sheets. All 12 overseas tickers are USD-denominated. The same evaluator converts with USDCNY in its PnL replay and in `_compute_exposure_stats`. Only the cross-border block leaves the conversion out. USDCNY in the data runs from 6.757 to 7.157 (mean 7.004).
- **Exact arithmetic.** Shares were computed with Python `Fraction`.
- **Lean 4.** `formal/lean/ebv/Ebv/FinanceExcessFx.lean` proves the fixture shares (1/3 native, 7/9 in CNY), that the native share passes the limit and the CNY share fails it, and that a native share of 2/5 at FX 7 hides a CNY share of up to 14/17. No `sorry` is used. The proofs depend only on the standard axioms.
- **Shipped reference.** The image's own standard-answer positions were checked under both accountings.
- **Paired v1/v2 run.** One E2B worker ran the component arms and the full original `score.py` on the shipped reference.
- **Original identity.** Judge image `seededge/edgebench.judge.cta_risk_budget_optimization@sha256:34258d85…1b32`. Key file `eval_script.py` has sha256 `252f864a…1300`. The task JSON has sha256 `4681d022…cb1`.

## What we found

**Confirmed.** The cross-border sub-check compares USD and CNY notionals without conversion. This contradicts the policy document's explicit RMB-equivalent rule and the evaluator's own FX handling elsewhere.

Minimal counterexample under the original evaluator (synthetic): 2 lots CNY and 1 lot USD, with price and multiplier 1 and USDCNY 7. The contract (CNY) share is 7/9, which breaches 40%. The evaluator computes 1/3 and records 0 violations. On real data for 2021-06-01, 10 lots CU.SHF plus 8 lots GC.CME give a CNY share of 0.595. The evaluator reads 0.175, so this case also passes.

**Maximum score effect:** up to 5/100 (4 of 80 raw points), in the lenient direction only. Because USDCNY is above 1, the bug can award ratio credit to a portfolio that breaches the limit, but it never penalizes a compliant one. Other gates can cap or veto the risk dimension and hide the swing.

**Effect on the task's own reference.** Converted at USDCNY, the shipped standard-answer positions exceed 40% on 32 of 1565 days, with a maximum of 52.1%. The original check reports 0 violations and full ratio credit.

**Earlier wording.** The earlier claim said the component award changes "from one point to zero". That is correct for the minimal case, but it understates the maximum swing, which is 5 vs 1 risk points.

**Separate observation, not repaired.** The policy states the limit as "40% of fund NAV". The evaluator instead uses the overseas share of gross notional. This is a separate question from the currency issue and is not part of this finding.

## Repair

v2 changes one file, `/home/workspace/scoring/eval_script.py` (+11/−1 lines). Inside the cross-border block, USD-denominated tickers are multiplied by USDCNY from the evaluator's own `fx` data, looked up as of the date. The fallback is 7.0, the same series and fallback the existing `fx_for` helper uses. The 40% threshold, the day-count rules, the `cb_checks` mapping and the NAV-versus-gross-notional question are all unchanged. Same-currency portfolios are numerically unchanged. In the task JSON, only `judge.image_tag` changes.

| # | Arm | Input | v1 | v2 | Expected |
|---|---|---|---|---|---|
| 1 | **Trigger (synthetic)** | 2 lots CNY + 1 lot USD, price and multiplier 1, USDCNY 7. Share is 1/3 native, 7/9 in CNY | violations 0/1; `cross_border` **1** (cost_fx 0) / **5** (cost_fx 2) | violations **1/1**; `cross_border` **0** / **1** | v1 passes the 40% limit wrongly, v2 fails it ✔ |
| 1b | **Trigger (real data)** | 2021-06-01: 10 lots CU.SHF + 8 lots GC.CME. Share is 0.175 native, 0.595 in CNY | violations 0/1; cb **1 / 5** | violations **1/1**; cb **0 / 1** | ✔ |
| 2 | Same-currency control | domestic only (2 lots CU.SHF) | 0/1; cb 1 / 5 | 0/1; cb 1 / 5 | unchanged ✔ |
| 2b | Under-limit mixed control | real data, 10 CU + 2 GC. Share 0.050 native, 0.269 in CNY | 0/1; cb 1 / 5 | 0/1; cb 1 / 5 | unchanged ✔ |
| 2c | Invalid control (over the limit even natively) | synthetic 1 CNY + 1 USD (1/2 native, 7/8 CNY); real 10 CU + 30 GC (0.443 / 0.847) | 1/1; cb 0 / 1 | 1/1; cb 0 / 1 | rejected both ✔ |
| 3 | Shipped reference positions (component) | `standard_answer_artifacts.tar.gz` `backtest_results/positions.csv` + `trades.csv`, 1565 days | violations **0/1565**; cb **1 / 5** | violations **32/1565** (2.04%); cb **0 / 1** | changes, explained below |
| 4 | **Full original scorer, complete shipped reference** | the whole `standard_answer_artifacts.tar.gz` extracted into `/home/workspace` | TOTAL_SCORE **20.0** (raw 16/80); M1 4, M2 0, **M3 0** ("Veto: annual vol 1.3% outside [5%,20%]"), M4 2, M5 10; valid, pass_rate 1.0, exit 0 | **identical**: 20.0, the same metric breakdown, the same veto. Logs are identical apart from timings | unchanged ✔ |

Row 3 changes as intended: 32/1565 is not below the 2% day-count allowance, so v2 awards 0 ratio checks instead of 2. Row 4 is unchanged because the full scorer vetoes the whole risk dimension of the shipped reference (annual volatility 1.3%) before the cross-border score is used. The repair is accepted at component level.

**Score compatibility.** Some submissions hold overseas (USD) contracts whose share, converted at USDCNY, exceeds 40% on at least one day. For those, v2 is not comparable with v1: they can lose cross-border ratio credit, up to 4 of 80 raw points (5 normalized). Only the `cross_border` component inside M3 can change, and only downward. Same-currency portfolios score identically.

## Limits and what was not run

- No model or solver re-runs. Effects are shown on authored controls, counterexamples and the shipped reference only.
- The trigger was exercised through the installed evaluator's `_evaluate_risk_constraints`, with the participation gate stubbed and NAV omitted. It was not run end-to-end through `score.py`. The only complete submission in the image is the standard answer, and it is vetoed before the cross-border block.
- How often real solver submissions are affected was not measured.
- The work image was not inspected for a copy of `eval_script.py`.
- The separate "% of NAV vs % of gross notional" deviation was not repaired.

## Reproduce

- Original-evaluator reproduction: `evidence/scripts/cta_risk_budget_optimization/repro_cross_border.py`. Repaired check: `repro_repaired.py`. Reference positions: `reference_positions_share.py`. Saved outputs are the matching `.out` files.
- Lean proof: `evidence/formal/lean/ebv/Ebv/FinanceExcessFx.lean` (output in `FinanceExcessFx.out`).
- Paired v1/v2 run: `repairs/cta_risk_budget_optimization-v2/paired/run.sh`, results in `paired/results.md`, evidence in `paired/evidence/`.
- Repair: `repairs/cta_risk_budget_optimization-v2/repair.patch`, `Dockerfile`, `source-lock.json`.

Supporting records: `repairs/cta_risk_budget_optimization-v2/` and `evidence/reviews/cta_risk_budget_optimization.md`.

