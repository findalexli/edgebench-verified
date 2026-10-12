# openttd_transport_ai v2: name an API that exists and say how the score is read

## Defect

The v1 prompt's Goal says: "Maximize **`AICompany.GetCompanyValue(AICompany.COMPANY_SELF)`**".
OpenTTD 13.4, the pinned engine, has no `AICompany.GetCompanyValue`. A script that calls it dies
at that call ("the index 'GetCompanyValue' does not exist"). The shipped baseline AI in the work
image calls it as its first statement, so it dies too, and the company stops acting for the rest
of the game. Review: `../../evidence/reviews/openttd_transport_ai-native.md`. Paired run:
`paired/results.md`.

The function that exists is `AICompany.GetQuarterlyCompanyValue(company, quarter)`. In the
OpenTTD 13.4 source (`src/script/api/script_company.cpp`), quarter `CURRENT_QUARTER` (0) returns
`CalculateCompanyValue(c)` and quarter `q >= 1` returns `old_economy[q - 1].company_value`. The
scorer (`/tmp/openttd_original_eval.py`, `extract_company_value`) reads
`old_economy[0].company_value` from the monthly saves, keeps the last value above 1, and averages
it over the 5 seeds. At the end of the game that is exactly what `GetQuarterlyCompanyValue(SELF, 1)`
returns.

## Change

1. **Prompt (`work.agent_query`).** The Goal paragraph is replaced. It now names
   `AICompany.GetQuarterlyCompanyValue(AICompany.COMPANY_SELF, AICompany.CURRENT_QUARTER)`, says
   that `GetCompanyValue` does not exist and kills the script, corrects the value formula
   (stations count, other infrastructure does not; floor of 1) and states how the score is read.
   Nothing else in the prompt changes.
2. **Starter (work image).** The baseline `my_ai/main.nut` line 5 calls
   `GetQuarterlyCompanyValue(AICompany.COMPANY_SELF, AICompany.CURRENT_QUARTER)` instead of
   `GetCompanyValue(AICompany.COMPANY_SELF)`. `info.nut`, `docs/` and everything else are unchanged.
   `Dockerfile.work` builds the v2 work image `FROM` the v1 work image digest. `task.json.in` sets
   `work.image_tag` to `f2e9a9fb0fff-ebv-v2`.

The judge image, `eval_cmd`, timeouts, parser and rescale (`log_max`, 1e5 to 1e9) are unchanged.
The task JSON change is in `task-json.diff`.

## Score compatibility

The scorer is byte-identical, so a given `my_ai/` gets the same score under v1 and v2. OpenTTD
runs are deterministic for a fixed seed and AI, and the paired run reproduced the earlier v1
baseline numbers exactly. Scores are **not comparable as measures of solver ability** where a v1
solver followed the prompt and called the missing function: in v1 that solver's script died, in
v2 it would not.

## Limits

- The prompt's Files section says the API docs are in `docs/noai_api_docs/`. They are actually in
  `docs/openttd_reference_docs/noai_api_docs/`. The shipped HTML docs also appear to be from a
  later OpenTTD (they mention "economy-quarter" and `AIEconomyTime`), not 13.4. Neither is
  changed here. Both docs list `GetQuarterlyCompanyValue` and do not list `GetCompanyValue`.
- The work image's `my_ai/` is also tracked by a Git repository inside the image; in v2,
  `git status` shows `main.nut` as modified. The submission is the `my_ai/` directory, so this
  does not affect scoring.
- No model or solver was run. The positive-value control is an audit probe (bus stops and a
  smaller loan, no vehicles), not a strategy.
- The baseline's `info.nut` still describes itself as logging "every ~74 days"; `Sleep(74)` is
  74 ticks, about one game day. Unchanged because it does not affect the contract.

## Build

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh
docker build -f Dockerfile.work -t <tag> .
```

`materialize.sh` pulls the pinned work image by digest (unless present), extracts the original
`my_ai/main.nut` with `docker create` + `docker cp`, takes `work.agent_query` from the EdgeBench
repo's `tasks/openttd_transport_ai.json` (set `EDGEBENCH_ROOT` if needed), checks every original
against `source-lock.json`, applies `repair.patch` with `patch -p1` and verifies the sha256 of every
output. See `../MATERIALIZE-CHECK.md`.

Paired run: `paired/stage.sh <dir>` assembles the job (this package without image files, plus the
original task JSON); `tools/e2b_run.py --job <dir>` runs `paired/run.sh` on one E2B worker.
