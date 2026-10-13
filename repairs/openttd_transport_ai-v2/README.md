# Fixed version of `openttd_transport_ai`: name an API that exists and say how the score is read

## What this fixes

The original instructions tell the solver to maximize a game function, `AICompany.GetCompanyValue`, that does not exist in the pinned game version. A script that calls it crashes, and the supplied starter program calls it in its main loop, after one log line. The fixed version names the function that exists and explains how the score is read; the grader is unchanged.

In detail, the original prompt's Goal says: "Maximize **`AICompany.GetCompanyValue(AICompany.COMPANY_SELF)`**".
OpenTTD 13.4, the pinned game engine, has no `AICompany.GetCompanyValue`. A script that calls it dies
at that call ("the index 'GetCompanyValue' does not exist"). The supplied starter AI in the work
image calls it at `main.nut` line 5, right after its first log line, so it dies too, and the company stops acting for the rest
of the game. Review: `../../evidence/reviews/openttd_transport_ai-native.md`. Side-by-side run:
`paired/results.md`.

The function that exists is `AICompany.GetQuarterlyCompanyValue(company, quarter)`. In the
OpenTTD 13.4 source (`src/script/api/script_company.cpp`), quarter `CURRENT_QUARTER` (0) returns
`CalculateCompanyValue(c)` and quarter `q >= 1` returns `old_economy[q - 1].company_value`. The
grader (`/tmp/openttd_original_eval.py`, `extract_company_value`) reads
`old_economy[0].company_value` from the monthly save files, keeps the last value above 1, and averages
it over the 5 seeds. At the end of the game that is exactly what `GetQuarterlyCompanyValue(SELF, 1)`
returns.

## What changes

1. **Instructions (`work.agent_query`).** The Goal paragraph is replaced. It now names
   `AICompany.GetQuarterlyCompanyValue(AICompany.COMPANY_SELF, AICompany.CURRENT_QUARTER)`, says
   that `GetCompanyValue` does not exist and kills the script, corrects the value formula
   (stations count, other infrastructure does not; floor of 1) and states how the score is read.
   Nothing else in the instructions changes.
2. **Starter (work image).** The starter `my_ai/main.nut` line 5 calls
   `GetQuarterlyCompanyValue(AICompany.COMPANY_SELF, AICompany.CURRENT_QUARTER)` instead of
   `GetCompanyValue(AICompany.COMPANY_SELF)`. `info.nut`, `docs/` and everything else are unchanged.
   `Dockerfile.work` builds the fixed work image `FROM` the original work image digest. `task.json.in` sets
   `work.image_tag` to `f2e9a9fb0fff-ebv-v2`.

The grader image, `eval_cmd`, timeouts, parser and score scale (`log_max`, 1e5 to 1e9) are unchanged.
The task JSON change is in `task-json.diff`.

## How it was checked

The grader is byte-identical, so a given `my_ai/` gets the same score under the original and fixed versions. OpenTTD
runs are deterministic for a fixed seed and AI, and the side-by-side run reproduced the earlier
numbers for the original starter exactly. Results are in `paired/results.md`.

Scores are **not comparable as measures of solver ability** where a solver of the original version
followed the instructions and called the missing function: in the original version that solver's script died, in
the fixed version it would not.

## Build and use

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

Side-by-side run: `paired/stage.sh <dir>` assembles the job (this package without image files, plus the
original task JSON); `tools/e2b_run.py --job <dir>` runs `paired/run.sh` on one E2B worker.

## Limits

- The instructions' Files section says the API documentation is in `docs/noai_api_docs/`. It is actually in
  `docs/openttd_reference_docs/noai_api_docs/`. The supplied HTML documentation also appears to be from a
  later OpenTTD (it mentions "economy-quarter" and `AIEconomyTime`), not 13.4. Neither is
  changed here. Both sets of documentation list `GetQuarterlyCompanyValue` and do not list `GetCompanyValue`.
- The work image's `my_ai/` is also tracked by a Git repository inside the image; in the fixed version,
  `git status` shows `main.nut` as modified. The submission is the `my_ai/` directory, so this
  does not affect scoring.
- No AI model or solver was run. The test submission with a positive value is an audit probe (bus stops and a
  smaller loan, no vehicles), not a strategy.
- The starter's `info.nut` still describes itself as logging "every ~74 days"; `Sleep(74)` is
  74 ticks, about one game day. It is unchanged because it does not affect what the task asks.
