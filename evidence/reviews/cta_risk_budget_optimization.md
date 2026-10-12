# Review: cta_risk_budget_optimization (overseas-exposure currency mixing)

## Claim under review

Earlier claim (verbatim): "The original mixes currencies when measuring overseas exposure,
contradicting its common-currency accounting contract. A matched fixture changes exposure from
1/3 to 7/9 and the component award from one point to zero."

Earlier disposition: withhold the exact original (`ADOPT_EXACT_ORIGINAL_WITHHOLDING`,
`evidence/selected/cta-original-exclusion.json`). A finite component repair was accepted but
not certified (`cta-currency-native-acceptance.json`). No `proposedrepairs/` entry exists for this
task.

## Pinned artifacts

- Task: `tasks/cta_risk_budget_optimization.json` sha256 `4681d022…cb1` (`eval_cmd`
  `python3 scoring/score.py`, which runs the manifest command `python3 scoring/run_eval.py`,
  which runs `eval_script.py`, 80 points rescaled to 100).
- Judge image: `seededge/edgebench.judge.cta_risk_budget_optimization@sha256:34258d854f41e9cd5fc179fadbc6348bb8ff4118506b1862273f2a2a6d941b32`
  (pulled and run locally; Python libraries in the image: pandas 3.0.3, numpy 2.4.6).
- File hashes inside the image (they match the extracted sources in `$W/work/task-sources/merged/`):
  - `scoring/eval_script.py` `252f864a1a515fb48283644268938afd75f417fcfe34bba09fc8bab49cd41300`
  - `scoring/run_eval.py` `0aa263ba1d42a8c5ac225f9e8174d6b5b401bb0cc706cb9741e65650fe32f680`
  - `scoring/standard_answer_code.py` `0b9e51443347d392d267f4a3750d97a517dd268889efc36cc0d2c395aa879cb4`
  - Task JSON full hash `4681d022290b1809e48481dab632a67e333b099e89cca031b41a57fd385a805c`
  - `input/task_instruction.md` `dbca3cbc875ea47b8b879de29bed881858c145153a4d23b16f56a4fd5fec72ca`
  - `input/risk_policy_doc.docx` `a3dc94fa471dba5b21ef9341ecd30cd7beeb6351ce48498c0596ca22070e19b3`
  - `input/futures_price_data.xlsx` `2ca55ee4776f8763779139943b83f2243c5dc2cf7f3db5488e58a3a998b74ec2`
  - `input/futures_contract_specs.xlsx` `4f2d2847e89957f3c42b2a2e635c4f5e59ac63851a0c322fe2c7f5faf4aa4a6c`
  - `input/macro_factors_data.xlsx` `c34a1e7d6434bfd20fbb29728049c9b3c389ccbb9af77672ac28f59ddc1ffbf0`

## Contract

The task prompt asks for a "Multi-currency, multi-market, multi-instrument backtesting engine",
"Handling of … exchange rates", "single-instrument/sector/overseas exposure … risk constraints",
and says outputs should be reconcilable on "exchange rate conversions". The task prompt gives no
number for the overseas limit. The number and the currency rule come from the
input `risk_policy_doc.docx` (Chinese; quoted verbatim, translation in brackets):

- "境外投资比例不超过基金净值的40%" [overseas investment must not exceed 40% of fund NAV]
- "所有境外品种的仓位计算必须使用实时汇率折算为人民币等值" [all position calculations for overseas
  instruments must be converted to RMB equivalents at the live exchange rate]
- "境外投资组合的汇率敞口不得超过基金净值的40%（与境外持仓限额一致）" [the FX exposure of the
  overseas portfolio must not exceed 40% of NAV (consistent with the overseas holding limit)]

So the contract does set common-RMB accounting for the overseas-exposure limit, and it says so
explicitly.

## Data schema: are the amounts already converted upstream?

No. The evaluator does not use any submitted notional. It recomputes notional itself from
`lots` (from the submission's holdings), `multiplier` (from `contract_specs`) and `close` (from the
raw price sheets) (`eval_script.py` lines ~1012-1040):

```python
m = mult_lk.get(t, 1); p = price_lk.get((date, t), 0)
n = l * m * p; tn += n
if t in OVERSEAS_TICKERS: on += n
...
if tn > 0 and on/tn > 0.40: violations += 1
```

The raw data marks every overseas row `currency = USD`. All 12 overseas tickers have `currency USD`
in `contract_specs`, and `close` is quoted in USD (for example GC.CME has a mean of about 970 and
LME copper a mean of about 5730). The same evaluator treats these prices as USD in other places:
the PnL replay (line ~623) and `_compute_exposure_stats` (line ~1478) both multiply by
`fx_for(date, 'USD')`, which is USDCNY. The standard-answer code also converts with `fx_rate`. Only
the cross-border block leaves out the conversion. There is no other caller and no upstream
conversion. USDCNY in `fx_rates_daily` runs from 6.757 to 7.157 (mean 7.004), so USD notionals are
undercounted by about 7 times.

## Independent reproduction

Scripts are in `evidence/scripts/cta_risk_budget_optimization/`. All runs used
`docker run --rm --network none --memory 2g --cpus 1` against the pinned image. Each run imported
the installed `/home/workspace/scoring/eval_script.py` and called the original
`_evaluate_risk_constraints`. Only the participation gate was stubbed to "pass", and `nav_history`
was omitted so that the drawdown/vol veto does not fire. The cross-border code itself was not
modified.

`repro_cross_border.py` (output in `repro_cross_border.out`). The oracle is exact `Fraction`
arithmetic.

| case | native share (evaluator) | CNY share (contract) | original `cross_border` (no overseas trades / cost-FX=2) |
|---|---|---|---|
| A: 2 CNY + 1 USD unit, FX 7 (trigger) | 1/3 | 7/9 | **1 / 5** (0 violations) |
| A: domestic only (good control) | 0 | 0 | 1 / 5 |
| A: 1 CNY + 1 USD (bad control) | 1/2 | 7/8 | 0 / 1 (violation) |
| B: real 2021-06-01 data, 10 CU.SHF + 2 GC.CME | 0.050 | 0.269 | 1 / 5 |
| B: real data, 10 CU.SHF + 8 GC.CME (trigger) | 0.175 | **0.595** | **1 / 5** (0 violations) |
| B: real data, 10 CU.SHF + 30 GC.CME | 0.443 | 0.847 | 0 / 1 |

`repro_repaired.py` applies the minimal FX fix (`repair.patch`) to the same installed source and
reruns. The triggers flip: case A goes to 0 / 1 and B with 8 lots goes to 0 / 1. All controls are
unchanged (`repro_repaired.out`).

`reference_positions_share.py` runs on the image's own shipped standard-answer `positions.csv`
(1564 days). The evaluator's native share never exceeds 40% (max 13.8%). The common-CNY share has
mean 26.3% and max 52.1%, and exceeds 40% on **32/1564 days (2.05%)**. Under the original check the
reference earns 2 ratio points (0 violations). Under the corrected check it earns 0, because
32/1564 is not below 2%. So a non-contrived submission (the task's own reference) is affected.

## Refutation attempts

- *Already converted upstream?* No. See the schema section above. The notional is recomputed from
  raw USD prices and no FX factor is applied.
- *FX near 1:1?* No. USDCNY is about 7, so the true share can be badly understated. A native share
  of exactly 40% corresponds to a CNY share of 14/17 (about 82.4%). This is proved in Lean as
  `cta_max_hidden_share`.
- *Arithmetic.* 1/(1+2) = 1/3 ≤ 2/5 < 7/(7+2) = 7/9. Confirmed with exact fractions and in Lean.
- *Direction.* Because FX is above 1, the bug is only ever lenient. It can award ratio points to a
  portfolio that breaches the limit. It never penalizes a compliant one.
- *Score size.* The ratio sub-check is worth 2 `cb_checks`, and `cb_checks` maps to the
  cross-border score as 4→5, 3→3, 1-2→1. With full FX credit the swing is 5 vs 1 risk points (4 of
  80, which is 5 of the 100 normalized points). With no overseas trades it is 1 vs 0. The risk
  total can also be capped (8/12) by other authenticity gates, which would hide the swing. The
  claim's "one point to zero" is the minimal case. It is correct but understates the maximum.
- *Unclaimed second deviation.* The policy says "40% of fund NAV", but the evaluator uses the
  overseas share of gross notional. This is separate from the currency issue and was not part of
  the claim.

## Formal check

`formal/lean/ebv/Ebv/FinanceExcessFx.lean` (output in `FinanceExcessFx.out`) proves
`cta_native_share` (1/3), `cta_cny_share` (7/9), `cta_native_passes`, `cta_cny_fails`, and
`cta_max_hidden_share` (native ≤ 2/5 and FX = 7 give CNY ≤ 14/17). Every one depends only on
`[propext, Classical.choice, Quot.sound]`. There is no `sorry`. The model leaves out per-day
aggregation and the FX time series, which are covered by the Docker runs.

## Verdict

**CONFIRMED.** The cross-border sub-check compares USD and CNY notionals without conversion. This
contradicts the policy document's explicit RMB-equivalent rule and the evaluator's own FX handling
elsewhere. The fixture numbers are exact, and the effect appears on real task data and on the
task's own reference positions.

## Disposition assessment

I agree that the defect is real and reachable by ordinary submissions. "Withhold the exact
original" is defensible, because the error is systematic (about 7 times) and it affects the
reference solution's own award. The magnitude is bounded, though: at most 4/80 raw points, about 5
normalized, and only in the lenient direction. "Repair" with the one-line FX fix is proportionate.
Withholding the original is also acceptable if repairs are always shipped as separate versions.

## Recommended publishable wording

"The original evaluator's 40% overseas-exposure check adds USD and CNY contract notionals without
converting them at USDCNY (about 7), although the task's risk policy requires RMB-equivalent
conversion. This undercounts overseas exposure about sevenfold and can award up to 4 of 80 raw
points to portfolios that breach the limit. The task's own reference positions exceed the limit
in RMB on 2% of days and still receive full ratio credit."

## Repair note

No earlier patch file was in `proposedrepairs/`, so I could not compare with it. The smallest
correct fix multiplies the cross-border notional by USDCNY for USD-denominated specs, reusing the
same `fx_rates_daily` series as the replay (`scripts/cta_risk_budget_optimization/repair.patch`,
verified in `repro_repaired.out`). This fix does not touch the separate "% of NAV vs % of gross
notional" question.

## Limits

- The participation gate was stubbed, and full `run_eval.py` was not run on a complete submission.
- The reference-positions impact was measured with my own reimplementation of the evaluator
  formula (same inputs), not by running the full scorer on the reference outputs.
- I did not measure how often this happens across real solver submissions.
