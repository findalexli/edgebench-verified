# Paired check: openttd_transport_ai v2 (prompt + starter fix)

## Question

Does a script that follows the v2 prompt (calls
`AICompany.GetQuarterlyCompanyValue(AICompany.COMPANY_SELF, AICompany.CURRENT_QUARTER)`) run
for the whole game without dying, while the v1 baseline still dies? And does the v2 prompt's
description of the score match what the unchanged scorer reads?

## Setup

- One E2B worker (8 vCPU), job `openttd_transport_ai-v2-paired`, 643 s, exit 0, worker killed.
  Two earlier attempts stopped before any evaluation: the worker had no `patch` (installed in
  `run.sh`), then a Docker Hub pull ended with EOF (pulls now retry). Their logs are in
  `result-failed-setup/`.
- Judge image `seededge/edgebench.judge.openttd_transport_ai@sha256:27167956…` (unchanged in v2).
  v1 work image `…work.openttd_transport_ai@sha256:8c1921e6…`. The v2 work image was built on the
  worker from `Dockerfile.work` after `materialize.sh` regenerated and verified all 4 outputs
  (`result/out/materialize.log`). Evaluator sha256 values match the earlier review:
  `eval_openttd.py` `167e480a…`, `openttd_original_eval.py` `76dae843…`, `openttdlab.py` `5017fa28…`.
- Every submission ran in a fresh judge container (`--network none --memory 6g`) with the exact
  original `eval_cmd`: `cd /home/workspace/openttd_ai && OPENTTD_N_SEEDS=5 python3 /tmp/eval_openttd.py`.
  Then `diag_log.py` repeated the same 5-seed, 20-year run shape with `-d script=4` added, so
  `AILog` lines were captured, and compared each seed's scorer value with the AI's own logged values.
- Submissions (sha256 in `result/out/submission_sha256.txt`):
  - `baseline_v1`: the shipped `my_ai/` from the v1 work image.
  - `probe_min`: our probe. Once per game month it logs
    `GetQuarterlyCompanyValue(SELF, CURRENT_QUARTER)`, `GetQuarterlyCompanyValue(SELF, 1)`, bank
    balance and loan. It does nothing else.
  - `baseline_v2`: the `my_ai/` from the v2 work image (one changed line, `result/out/baseline_v1_v2.diff`).
  - `probe_value`: positive-value control. It builds 8 drive-through bus stops, cuts the loan to
    20,000, then logs the same values monthly. No vehicles, no income.

The judge is the same image for v1 and v2, so each submission scores the same under both
versions by construction. The table shows each submission once; the "v1/v2" columns repeat the
score.

## Paired table

| Submission | Task version it ships with | Script died? | `TOTAL_SCORE` v1 | `TOTAL_SCORE` v2 | Per-seed company value (scorer) | Error flag (5 seeds) |
|---|---|---|---|---|---|---|
| baseline_v1 (shipped starter) | v1 | yes, at `main.nut` line 5 | 0 | 0 | 0 on all 5 seeds | 5/5 YES |
| probe_min (calls corrected API monthly) | follows v2 prompt | no | 0 | 0 | 0 on all 5 seeds | 0/5 |
| baseline_v2 (fixed starter) | v2 | no | 0 | 0 | 0 on all 5 seeds | 0/5 |
| probe_value (positive-value control) | follows v2 prompt | no | 4975 | 4975 | 4,975 on all 5 seeds | 0/5 |

**Trigger: the shipped starter, v1 work image vs v2 work image** (same judge, same `eval_cmd`):

| Starter | Script died? (v1) | Script died? (v2) | `TOTAL_SCORE` v1 | `TOTAL_SCORE` v2 |
|---|---|---|---|---|
| shipped starter (v1 work image vs v2 work image) | yes, at `main.nut` line 5 | no | 0 | 0 |

All four evaluations exited 0 in 69 to 80 s and returned 239 monthly saves per seed, ending
1969-12-01. The `baseline_v1` numbers (money 54,191, loan 100,000, score 0, error YES) are
identical to the earlier review run.

**Engine output, baseline_v1, every seed:**

```
dbg: [script] [0] [S] Your script made an error: the index 'GetCompanyValue' does not exist
dbg: [script] [0] [S] *FUNCTION [Start()] myai/main.nut line [5]
dbg: [script] The script died unexpectedly.
```

**Logged values.**

- `probe_min`, every seed: `PROBE has_GetCompanyValue=false has_GetQuarterlyCompanyValue=true CURRENT_QUARTER=0 EARLIEST_QUARTER=24`.
  240 monthly log lines, the last `CV 1969-12-3 cur=1 q1=1 bank=54191 loan=100000`. The idle
  company's value is at the floor of 1 (cash 54,191 minus loan 100,000 is negative), which the
  scorer counts as 0.
- `baseline_v2`, every seed: 1,825 lines `Company value: 1`, no script error.
- `probe_value`, every seed: `PROBE stops_built=8`, `PROBE set_loan target=20000 ok=true loan=20000 bank=18800`.
  Last line `CV 1969-12-3 cur=4858 q1=4975 bank=4858 loan=20000`. `diag_log.py` saved only the six
  smallest distinct quarter-1 values (`q1_distinct`: 0, 4,975, 5,150, 5,325, 5,500, 5,675), which
  step by 175. The bank balance fell from 18,800 after the loan was cut to 4,858 at the end, about
  174 per quarter over the roughly 80 quarters; the cause of the fall was not checked.
- **Logged value vs scorer:** for every seed of both probes, the last logged
  `GetQuarterlyCompanyValue(SELF, 1)` equals `old_economy[0].company_value` in the final save,
  which is the value the scorer used (`all_logged_q1_equal_final_old_economy0: true`). For
  `probe_value` that value is 4,975, the scored value, while the running `CURRENT_QUARTER`
  value at the end was 4,858. The scorer therefore reads the value at the last quarter boundary
  (1 October 1969), not the running value, as the v2 prompt says.

**Engine-level API check** (`result/out/engine_api_check.txt`): in the cached OpenTTD 13.4
binary (sha256 `cb5d145b…`), `GetQuarterlyCompanyValue` and `CURRENT_QUARTER` occur as
NUL-terminated strings once each; `GetCompanyValue` occurs 0 times. The OpenTTD 13.4 source
(`src/script/api/script_company.cpp`) defines `GetQuarterlyCompanyValue` as
`CalculateCompanyValue(c)` for `CURRENT_QUARTER` and `old_economy[quarter - 1].company_value`
otherwise. The work image's API docs list `GetQuarterlyCompanyValue` and no `GetCompanyValue`.

**Prompt check** (`result/out/prompt_check.txt`): the v2 `agent_query` in `task.json.in` equals
the materialized `files/agent_query.md`; it no longer names `GetCompanyValue(` as a call and does
name `GetQuarterlyCompanyValue`.

## What this establishes and what it does not

- The v1 defect reproduces exactly, and both fixes remove it: a prompt-following script and the
  v2 starter run the whole 20 years with no script error.
- The v2 prompt's score description matches the scorer on a non-trivial value (4,975 on 5 seeds).
- The scorer is unchanged, so no submission's score changes between v1 and v2.
- All five seeds gave identical numbers for every submission. For these probes the costs do not
  depend on the map, so that is expected; whether the 5 seeds produce different maps was not checked.
- No model or competitive solver was run. The probes are audit controls, not strategies.

## Verdict

**Accepted.** v2 replaces the non-existent `AICompany.GetCompanyValue` with
`AICompany.GetQuarterlyCompanyValue` in both the prompt and the starter, and states how the
score is read. On the unchanged judge, the shipped v1 baseline dies on all 5 seeds (score 0), while
the v2 baseline and a probe that calls the corrected API every month run with no error. A
positive-value probe shows the scorer reads exactly the value that
`GetQuarterlyCompanyValue(SELF, 1)` reports at the end of the game (4,975 on all 5 seeds).
