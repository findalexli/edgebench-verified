# OpenTTD Transport AI (`openttd_transport_ai`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Interactive Games & Simulators
- **Decision:** Retain with note — the prompt's stated goal names an API function, `AICompany.GetCompanyValue`, that does not exist in the pinned engine. A script that calls it crashes. The scorer itself works.

## What the task promises

The solver writes "a **Squirrel** AI in `my_ai/` that maximizes **company value** over 20 game-years, averaged across multiple random seed maps." The prompt's goal line reads: "Maximize **`AICompany.GetCompanyValue(AICompany.COMPANY_SELF)`**". It also says "A baseline AI that just logs company value is already in `my_ai/`; improve it".

## What we checked and how

- Native run of the exact eval_cmd, offline: `cd /home/workspace/openttd_ai && OPENTTD_N_SEEDS=5 python3 /tmp/eval_openttd.py`, under `timeout 2600`. It ran in the pinned judge image (`--network none --memory 6g`) on an 8-vCPU E2B worker, so all 5 seeds ran in parallel. The submission was the shipped baseline `my_ai/` from the work image.
- A seed-0 diagnostic (`diag1.py`) that calls the evaluator's own `run_experiments` arguments and dumps every save row.
- OpenTTD 13.4 and OpenGFX 7.1 are pre-cached in the image, so no network was needed.
- A first attempt produced nothing because of an output-path bug in our own `run.sh`. No evaluation ran in that attempt.
- Original identity: judge image `seededge/edgebench.judge.openttd_transport_ai@sha256:27167956fd00…`; work image `seededge/edgebench.work.openttd_transport_ai@sha256:8c1921e643ed…`; key files `eval_openttd.py` sha256 `167e480ac204…`, `openttd_original_eval.py` `76dae84357c7…`, `openttdlab.py` (OpenTTDLab 0.0.75) `5017fa28a562…`, baseline `info.nut` `891c4c91dab3…`, `main.nut` `77e77c13ae0f…`.

## What we found

**Confirmed: a good-faith prompt trap.** `AICompany.GetCompanyValue` does not exist in the OpenTTD 13.4 NoAI API. The shipped baseline calls it as its first statement and dies:

```
dbg: [script] [0] [S] Your script made an error: the index 'GetCompanyValue' does not exist
dbg: [script] [0] [S] *FUNCTION [Start()] myai/main.nut line [5]
dbg: [script] The script died unexpectedly.
```

Full original evaluation of the baseline: wall time **63 s**, exit 0, all 5/5 requested seeds returned.

| Seed | Company value | CV date | Money | Loan | Net worth | Error |
|---|---|---|---|---|---|---|
| 0 | 0 | N/A | 54,191 | 100,000 | -45,809 | YES |
| 1 | 0 | N/A | 54,191 | 100,000 | -45,809 | YES |
| 2 | 0 | N/A | 54,191 | 100,000 | -45,809 | YES |
| 3 | 0 | N/A | 54,191 | 100,000 | -45,809 | YES |
| 4 | 0 | N/A | 54,191 | 100,000 | -45,809 | YES |

- The wrapper printed `CASE 0000 WA score=0` and `TOTAL_SCORE 0`.
- **Expected vs observed:** a solver that follows the prompt and calls the named function expects to read its company value. Instead its script is killed at that call, the company stops acting, and the score is its last positive quarterly value or 0.
- **Maximum effect:** the whole score for a prompt-following solver. The problem is detectable by local testing, which the prompt provides. It is a misleading-contract issue, not a scorer error.

**The scorer behaves as read from source.** It reads company value from the monthly saves. In the seed-0 diagnostic there are 239 monthly saves, from 1950-02-01 to 1969-12-01, so the game runs the full 7,300 days. `old_economy[0].company_value` is 1 in every save, and the evaluator's `> 1` filter yields 0. A do-nothing company therefore scores 0. With 239 saves and a final date of 1969-12-01, the "last quarterly value" is the 1969-10 quarter. OpenTTDLab's `error` flag is printed but does not affect the score.

**Runtime is not a concern for this run.** One seed alone took 55.4 s, about **9,750 ticks/s**, far above the roughly 150 ticks/s needed. The 5-seed evaluation took 63 s against `eval_timeout` 3600 s. An AI running many vehicles will be slower; that was not measured.

## Note for users

No repair. The note says:

- The prompt's named goal function, `AICompany.GetCompanyValue`, is not in the OpenTTD 13.4 API. Calling it kills the script.
- The scored quantity is the last quarterly `company_value` read from the saves.

The review suggests an optional v2 prompt and starter fix that names the quarterly company value, for example `AICompany.GetQuarterlyCompanyValue(AICompany.COMPANY_SELF, AICompany.CURRENT_QUARTER)`, and fixes the baseline's logging call. Whether that function exists in 13.4 was not verified.

## Limits and what was not run

- No model or solver re-runs. Effects are shown on the shipped baseline only.
- Only the crashing do-nothing baseline was run. There is no positive-score control, so neither the reachability of the 1e9 upper anchor nor run-to-run determinism was tested.
- One run only. The ticks/s figure is for an idle script on this host.

## Reproduce

- `evidence/runs/openttd_transport_ai-native-baseline/run.sh` (full evaluation) and `evidence/runs/openttd_transport_ai-native-saves-diag/run.sh` (with `diag1.py`). They need a Docker host that can pull the pinned images.
- Review: `evidence/reviews/openttd_transport_ai-native.md`.

