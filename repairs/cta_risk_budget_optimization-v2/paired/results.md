> Historical FX-only v2 evidence. The current v2.1 NAV-denominator candidate has separate component results in `nav-candidate-results.json`; these native runs do not validate that candidate.

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
