# v2.1 native paired run (2026-10-13)

- **Jobs:** `evidence/runs/cta_risk_budget_optimization-v2.1-native-rep1` (worker `iesvlr8usa3eik8wzb3av`, 442 s), `-rep2` (`irzuucbcnadblc2aekr39`, 201 s) and `-rep3` (`i7kwgav50r7hov4lot9m3`, 201 s). Each ledger record is `status: exit=0`, and each `result/out/summary.txt` ends with `done`. Recipe: `paired/run_native_v2.1.sh`.
- **Images:** v1 is the pinned original (`eval_script.py` `252f864a…`). v2.1 was built in each worker from this package: `materialize.sh` pulled the pinned image, extracted and patched `eval_script.py` and verified `5090b56a…`; then `docker build`. rep1 also built the superseded strict candidate from the previous package (`9f5149da…`, "strict" column). The installed hashes were read back from each image (`eval_sha_images.txt`).
- **Command:** the task's original `eval_cmd`, `cd /home/workspace && python3 scoring/score.py` (which runs the submitted `main.py`, then the evaluator), `--network none --memory 3g --cpus 2`. TOTAL_SCORE is out of 100 (raw out of 80); `cross_border` is the 5-point component inside the 20-point risk dimension.
- **Submissions:** the shipped standard answer (`standard_answer_artifacts.tar.gz` extracted into `/home/workspace`), and `full_submission/main.py` with `config-<arm>.json`. `main.py` writes a constant-weight portfolio from the task inputs with the grader's own accounting: authenticity check 10/10 (NAV accounting 2, continuity 2, replay 3, cost/FX 2), total CNY NAV starting at 1.5e9, volatility and drawdown inside the risk gate, participation passing. `leveraged`: overseas 45% of NAV, 37.5% of CNY gross (75% domestic). `unleveraged`: overseas 28% of NAV, 87.5% of CNY gross (4% domestic). `unleveraged-navgap`: `unleveraged` with the last NAV row (2025-12-31) dropped, so 1 of 1564 holdings dates has no same-date NAV.

| Submission | Role | v1 | v2.1 | strict (rep1 only) |
|---|---|---|---|---|
| shipped standard answer | baseline | TOTAL_SCORE 20 (raw 16); risk vetoed: annual vol 1.3% | TOTAL_SCORE 20, same veto | TOTAL_SCORE 20, same veto |
| leveraged (overseas 45% of NAV) | trigger | TOTAL_SCORE 58.75 (raw 47); violations 0/1564; cross_border 5 | TOTAL_SCORE 53.75 (raw 43); violations 1564/1564; cross_border 1 | 53.75; cross_border 1 |
| unleveraged (overseas 28% of NAV) | trigger | TOTAL_SCORE 66.25 (raw 53); violations 1564/1564; cross_border 1 | TOTAL_SCORE 71.25 (raw 57); violations 0/1564; cross_border 5 | 71.25; cross_border 5 |
| unleveraged-navgap (1 of 1564 dates without NAV) | valid | TOTAL_SCORE 66.25 (raw 53); cross_border 1 | TOTAL_SCORE 68.75 (raw 55); violations 1/1564; cross_border 3 | 66.25; no ratio credit; cross_border 1 |

rep2 and rep3 (v1 and v2.1 only) gave the same TOTAL_SCORE, raw score and `cross_border` in every arm. The original grader reads `leveraged` as compliant because it adds USD and CNY without conversion (native overseas share about 8%) and divides by gross; v2.1 finds 45% of NAV on every day. It reads `unleveraged` as a breach on every day (native share about 50% of gross); v2.1 finds 28% of NAV. In both cases only `cross_border` moves (4 raw points, 5 out of 100), and the other dimensions are identical.

**Standard answer and NAV dates.** The shipped reference has 1565 NAV dates and 1565 holdings dates, all aligned (`rep1/result/out/standard_answer_dates.txt`), so the NAV-date rule does not touch it. Its `nav` column is unit NAV (first value 1.0), which the original schema check rejects, and the full scorer vetoes its whole risk dimension on volatility before the cross-border block, so all three versions give 20.

**NAV-date rule.** `unleveraged-navgap` is the reviewer's case: a compliant portfolio whose NAV file lacks one holdings date. The strict candidate removed all ratio credit and scored it like a breaching portfolio (66.25). v2.1 counts the date as one violation day under the original <2% allowance (68.75; the aligned portfolio scores 71.25).

**Verdict: accepted.** Both decisive arms move in the policy's direction through the full original command, three times; the standard answer is unchanged.

> Everything below is historical FX-only v2 evidence. Those native runs do not validate v2.1.


# Paired v1/v2 results: cta_risk_budget_optimization

- **Job:** one E2B worker. Job ID `cta_risk_budget_optimization-v2-paired`, sandbox
  `ikynqjupudtgrkqra1c6q`. It exited 0 after 161 s and was killed after collection.
- **Images:** v1 is the pinned `seededge/edgebench.judge.cta_risk_budget_optimization@sha256:34258d85…1b32`
  (`eval_script.py` `252f864a…1300`). v2 was built in the worker from `../Dockerfile`, image ID
  `sha256:55ed8541…5df7` (`eval_script.py` `4e0ddc4e…110a`, owner agent:agent).
- **Containers:** `--network none --memory 2g/3g --cpus 2`.
- **Component arms (rows 1–3):** these import the installed `scoring/eval_script.py` and call the
  original `CTAEvaluator._evaluate_risk_constraints`. The participation gate is stubbed to pass,
  `nav_history` is omitted so that the vol/drawdown veto cannot fire, and the costs_fx score is
  set to 0 or 2. The scripts are `repro_cross_border.py` and `reference_block.py`.
- **Full arm (row 4):** the original `eval_cmd` (`cd /home/workspace && python3 scoring/score.py`),
  run on a complete submission. Its score was parsed with `parse_structured_json`.

| # | Arm | Input | v1 | v2 | Expected |
|---|---|---|---|---|---|
| 1 | **Trigger (synthetic)** | 2 lots CNY + 1 lot USD, price and multiplier 1, USDCNY 7. Share is 1/3 native, 7/9 in CNY | violations 0/1; `cross_border` **1** (cost_fx 0) / **5** (cost_fx 2) | violations **1/1**; `cross_border` **0** / **1** | v1 passes the 40% limit wrongly, v2 fails it ✔ |
| 1b | **Trigger (real data)** | 2021-06-01: 10 lots CU.SHF + 8 lots GC.CME. Share is 0.175 native, 0.595 in CNY | violations 0/1; cb **1 / 5** | violations **1/1**; cb **0 / 1** | ✔ |
| 2 | Same-currency control | domestic only (2 lots CU.SHF) | 0/1; cb 1 / 5 | 0/1; cb 1 / 5 | unchanged ✔ |
| 2b | Under-limit mixed control | real data, 10 CU + 2 GC. Share 0.050 native, 0.269 in CNY | 0/1; cb 1 / 5 | 0/1; cb 1 / 5 | unchanged ✔ |
| 2c | Invalid control (over the limit even natively) | synthetic 1 CNY + 1 USD (1/2 native, 7/8 CNY); real 10 CU + 30 GC (0.443 / 0.847) | 1/1; cb 0 / 1 | 1/1; cb 0 / 1 | rejected both ✔ |
| 3 | Shipped reference positions (component) | `standard_answer_artifacts.tar.gz` `backtest_results/positions.csv` + `trades.csv`, 1565 days | violations **0/1565**; cb **1 / 5** | violations **32/1565** (2.04%); cb **0 / 1** | changes, explained below |
| 4 | **Full original scorer, complete shipped reference** | the whole `standard_answer_artifacts.tar.gz` extracted into `/home/workspace` | TOTAL_SCORE **20.0** (raw 16/80); M1 4, M2 0, **M3 0** ("Veto: annual vol 1.3% outside [5%,20%]"), M4 2, M5 10; valid, pass_rate 1.0, exit 0 | **identical**: 20.0, the same metric breakdown, the same veto. Logs are identical apart from timings | unchanged ✔ |

**Why the reference changes in row 3.**
- Converted at USDCNY, the reference's overseas share exceeds the policy's 40% limit on 32 of 1565
  days. The maximum is 52.1%, which the review's independent reimplementation also found.
- 32/1565 is not below 2%, so v2 awards 0 ratio checks instead of 2. That moves the component from
  1 to 0 (cost_fx 0) or from 5 to 1 (cost_fx 2).
- This is the intended correction. The reference really does breach the stated limit in RMB terms.

**Full-scorer coverage.**
- The image ships exactly one complete eligible submission, the standard answer. The full scorer
  vetoes its whole risk dimension on annual volatility before the cross-border score is used, so
  v1 and v2 give the same 20.0.
- No complete submission in the image reaches the changed block through `score.py`, so the
  trigger was not run end-to-end. It was run against the installed evaluator code with only the
  participation gate stubbed, as in rows 1–3.

**Verdict: accepted, at component level.**
- The trigger is fixed (rows 1 and 1b).
- The same-currency and under-limit controls are unchanged.
- The over-limit invalid controls are rejected by both versions.
- The full original scorer gives the shipped reference an unchanged score of 20.0.

The reference's component score changes, and the change is explained and correct. The
end-to-end trigger through `score.py` is **not run**, because no eligible submission exists in
the image.

**Evidence** (`evidence/`): `summary.txt`, `summary_parsed.txt`, `logs/fixtures-v*.log`,
`logs/refblock-v*.log`, `logs/fullref-v*.log`, `eval_sha-v*.txt`, `build.log`, `worker.json`.
