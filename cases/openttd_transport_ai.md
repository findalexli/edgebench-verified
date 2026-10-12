# OpenTTD Transport AI (`openttd_transport_ai`)

**Decision:** Repair (v2) (prompt and starter fix). The prompt's stated goal names an API function, `AICompany.GetCompanyValue`, that does not exist in the pinned engine, so a script that calls it dies, and the shipped baseline dies on its first statement.

## What the task asks for

The solver writes "a **Squirrel** AI in `my_ai/` that maximizes **company value** over 20 game-years, averaged across multiple random seed maps." The prompt's goal line reads: "Maximize **`AICompany.GetCompanyValue(AICompany.COMPANY_SELF)`**". It also says "A baseline AI that just logs company value is already in `my_ai/`; improve it". Category: Interactive Games & Simulators.

## What goes wrong

**The prompt names a function that does not exist.** `AICompany.GetCompanyValue` is not in the OpenTTD 13.4 NoAI API. The shipped baseline calls it as its first statement and dies:

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

The wrapper printed `CASE 0000 WA score=0` and `TOTAL_SCORE 0`.

- **Expected vs observed:** a solver that follows the prompt and calls the named function expects to read its company value. Instead its script is killed at that call, the company stops acting, and the score is its last positive quarterly value or 0.
- The problem is detectable by local testing, which the prompt provides. It is a misleading contract, not a scorer error.

**The scorer itself behaves correctly.** It reads company value from the monthly saves. In a seed-0 run there are 239 monthly saves, from 1950-02-01 to 1969-12-01, so the game runs the full 7,300 days. `old_economy[0].company_value` is 1 in every save, and the evaluator's `> 1` filter yields 0, so a do-nothing company scores 0. With 239 saves and a final date of 1969-12-01, the "last quarterly value" is the 1969-10 quarter. OpenTTDLab's `error` flag is printed but does not affect the score.

**Runtime is not a concern for this run.** One seed alone took 55.4 s, about **9,750 ticks/s**, far above the roughly 150 ticks/s needed. The 5-seed evaluation took 63 s against `eval_timeout` 3600 s.

## Impact

Up to the whole score for a solver that follows the prompt and calls the named function. Solvers who test locally and use a different API are not affected.

## Fix (v2)

Package: `repairs/openttd_transport_ai-v2/`.

- **Prompt.** The Goal paragraph of `work.agent_query` now says that OpenTTD 13.4 has no `AICompany.GetCompanyValue` and that calling it stops the script. It names `AICompany.GetQuarterlyCompanyValue(AICompany.COMPANY_SELF, AICompany.CURRENT_QUARTER)` for the running value and quarter `1` for the value recorded at the start of the current quarter. It corrects the formula: stations count, other infrastructure does not, and the floor is 1. It states how the score is read: per seed, the value at the most recent quarter boundary before the game ends (falling back to an earlier quarter above 1, or 0), averaged over the 5 seeds.
- **Starter.** `my_ai/main.nut` line 5 calls `GetQuarterlyCompanyValue(AICompany.COMPANY_SELF, AICompany.CURRENT_QUARTER)`. `Dockerfile.work` builds the v2 work image from the v1 digest (image about 0.46 GB compressed); `work.image_tag` becomes `f2e9a9fb0fff-ebv-v2`.
- **API basis.** The OpenTTD 13.4 source defines `GetQuarterlyCompanyValue` as `CalculateCompanyValue(c)` for `CURRENT_QUARTER` and `old_economy[quarter - 1].company_value` otherwise. The cached 13.4 binary contains the name `GetQuarterlyCompanyValue` and not `GetCompanyValue`. A probe script reported `has_GetCompanyValue=false has_GetQuarterlyCompanyValue=true`.
- The judge image, `eval_cmd`, parser and rescale anchors (`log_max`, 1e5 to 1e9) are unchanged, so each submission scores the same under v1 and v2.

Paired check (exact original `eval_cmd`, 5 seeds, 20 game years; copied from `paired/results.md`):

| Submission | Task version it ships with | Script died? | `TOTAL_SCORE` v1 | `TOTAL_SCORE` v2 | Per-seed company value (scorer) | Error flag (5 seeds) |
|---|---|---|---|---|---|---|
| baseline_v1 (shipped starter) | v1 | yes, at `main.nut` line 5 | 0 | 0 | 0 on all 5 seeds | 5/5 YES |
| probe_min (calls corrected API monthly) | follows v2 prompt | no | 0 | 0 | 0 on all 5 seeds | 0/5 |
| baseline_v2 (fixed starter) | v2 | no | 0 | 0 | 0 on all 5 seeds | 0/5 |
| probe_value (positive-value control) | follows v2 prompt | no | 4975 | 4975 | 4,975 on all 5 seeds | 0/5 |

Trigger, the shipped starter on the same judge:

| Starter | Script died? (v1) | Script died? (v2) | `TOTAL_SCORE` v1 | `TOTAL_SCORE` v2 |
|---|---|---|---|---|
| shipped starter (v1 work image vs v2 work image) | yes, at `main.nut` line 5 | no | 0 | 0 |

- The idle probes score 0 because an idle company's value stays at the floor of 1 (cash minus a 100,000 loan is negative), which the scorer counts as 0. They show the script survives, not a positive score.
- For both probes, on every seed, the last logged `GetQuarterlyCompanyValue(SELF, 1)` equals the `old_economy[0].company_value` the scorer used. For `probe_value` that is 4,975, while the running `CURRENT_QUARTER` value at the end was 4,858.

**Score compatibility:** scores are comparable as measurements of the same harness. They are not comparable as measures of solver ability where a v1 solver followed the prompt and called the missing function.

## How we know

- **Original evaluator in the pinned image.** The exact eval_cmd, `cd /home/workspace/openttd_ai && OPENTTD_N_SEEDS=5 python3 /tmp/eval_openttd.py`, ran offline under `timeout 2600` in the judge image (`sha256:27167956fd00…`, `--network none --memory 6g`) on an 8-vCPU host, so all 5 seeds ran in parallel. The submission was the shipped baseline `my_ai/` from the work image. OpenTTD 13.4 and OpenGFX 7.1 are pre-cached in the image.
- **Save diagnostic.** A seed-0 diagnostic (`diag1.py`) calls the evaluator's own `run_experiments` arguments and dumps every save row.
- **Paired evaluation.** The tables above. It was repeated three times with no verdict change ([`paired-repeatability.md`](../paired-repeatability.md)).

## Limits

- No model or solver runs. Effects are shown on the shipped baseline and authored probes only.
- The only positive-score control is a probe (4,975, far below the 1e5 lower anchor). Whether the 1e9 upper anchor is reachable was not tested.
- The prompt's docs path (`docs/noai_api_docs/`) differs from the real one (`docs/openttd_reference_docs/noai_api_docs/`), and the shipped HTML docs appear to be from a later OpenTTD than 13.4. Both are noted in the package README and not changed.
- The ticks/s figure is for an idle script on one host. An AI running many vehicles will be slower; that was not measured.

## Reproduce

- `evidence/runs/openttd_transport_ai-native-baseline/run.sh` (full evaluation) and `evidence/runs/openttd_transport_ai-native-saves-diag/run.sh` (with `diag1.py`). They need a Docker host that can pull the pinned images.
- Review: `evidence/reviews/openttd_transport_ai-native.md`.
- Repair and paired run: `repairs/openttd_transport_ai-v2/` (`paired/stage.sh` then `tools/e2b_run.py`).
