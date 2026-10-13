# OpenTTD Transport AI (`openttd_transport_ai`)

**Outcome:** Fixed. <mark>The instructions tell the solver to maximize a game function, `AICompany.GetCompanyValue`, that does not exist in the pinned game version, so a script that calls it crashes, and the supplied starter program crashes at its first call to it; the fix changes the instructions and the starter, not the grader.</mark>

![A flow shows the original instructions naming GetCompanyValue, which does not exist in OpenTTD 13.4, so a script that calls it dies at that call and its company stops acting, while the fixed instructions and starter name GetQuarterlyCompanyValue, which exists, so the script keeps running; a note says the grader is unchanged and the starter scores 0 in both versions.](figures/openttd_transport_ai.svg)

*The task told solvers to call a game function that does not exist, so the starter crashed at its first call to it; the fix changes the instructions and starter.*

## What the task asks

OpenTTD is an open-source transport-company simulation game. The solver writes "a **Squirrel** AI in `my_ai/` that maximizes **company value** over 20 game-years, averaged across multiple random seed maps." Squirrel is the scripting language OpenTTD uses for computer players. The prompt's goal line reads: "Maximize **`AICompany.GetCompanyValue(AICompany.COMPANY_SELF)`**". It also says "A baseline AI that just logs company value is already in `my_ai/`; improve it". Category: Interactive Games & Simulators.

## What goes wrong

**The instructions name a function that does not exist.** `AICompany.GetCompanyValue` is not in the OpenTTD 13.4 NoAI API, the interface the game offers to computer players. The supplied starter logs one line and then calls it, in its main loop at `main.nut` line 5, and crashes:

```
dbg: [script] [0] [S] Your script made an error: the index 'GetCompanyValue' does not exist
dbg: [script] [0] [S] *FUNCTION [Start()] myai/main.nut line [5]
dbg: [script] The script died unexpectedly.
```

Full run of the original grader on the starter: wall time **63 s**, exit 0, all 5/5 requested seeds returned.

| Seed | Company value | Date of company value | Money | Loan | Net worth | Error |
|---|---|---|---|---|---|---|
| 0 | 0 | N/A | 54,191 | 100,000 | -45,809 | YES |
| 1 | 0 | N/A | 54,191 | 100,000 | -45,809 | YES |
| 2 | 0 | N/A | 54,191 | 100,000 | -45,809 | YES |
| 3 | 0 | N/A | 54,191 | 100,000 | -45,809 | YES |
| 4 | 0 | N/A | 54,191 | 100,000 | -45,809 | YES |

The wrapper printed `CASE 0000 WA score=0` and `TOTAL_SCORE 0`.

- **Expected and observed:** a solver that follows the instructions and calls the named function expects to read its company value. Instead its script is killed at that call, and the company stops acting. The score is its last positive quarterly value, or 0.
- The problem can be found by local testing, which the task provides. It is a misleading instruction, not a grader error.

**The instructions also misstate what is scored.** The Goal line defines the target as "vehicle value at 1.5× purchase + infrastructure value + cash − loans". The grader reads the game's own company value. In the OpenTTD 13.4 source that value counts vehicles at 1.5× their value and stations, plus cash minus loan, with a floor of 1; roads, rails and other infrastructure do not count. The probe in the table below is consistent with this: with 8 stops, no vehicles and cash minus loan negative, it is scored 4,975. Under the test in [`METHOD.md`](../METHOD.md), this is a case of the agent being told a different rule from the one applied. A solver that builds track or roads expecting them to add value is scored without them. Its size was not measured, and the rails part rests on reading the source, not on a run.

**The grader itself behaves correctly.** It reads company value from the game's monthly save files. In a seed-0 run there are 239 monthly saves, from 1950-02-01 to 1969-12-01, so the game runs the full 7,300 days. `old_economy[0].company_value` is 1 in every save, and the grader's `> 1` filter turns that into 0, so a company that does nothing scores 0. With 239 saves and a final date of 1969-12-01, the "last quarterly value" is the 1969-10 quarter. The `error` flag from OpenTTDLab (the library that runs the games) is printed but does not affect the score.

**Run time is not a concern for this run.** One seed alone took 55.4 s, about **9,750 ticks/s**, far above the roughly 150 ticks/s needed. The 5-seed run took 63 s against an `eval_timeout` of 3600 s.

## How much it matters

Up to the whole score for a solver that follows the instructions and calls the named function. Solvers who test locally and use a different function are not affected.

## The fix

The fixed version is in `repairs/openttd_transport_ai-v2/` (the folder holding the fixed version).

- **Instructions.** The Goal paragraph of `work.agent_query` now says that OpenTTD 13.4 has no `AICompany.GetCompanyValue` and that calling it stops the script. It names `AICompany.GetQuarterlyCompanyValue(AICompany.COMPANY_SELF, AICompany.CURRENT_QUARTER)` for the running value, and quarter `1` for the value recorded at the start of the current quarter. It corrects the formula: stations count, other infrastructure does not, and the floor is 1. It states how the score is read: for each seed, the value at the most recent quarter boundary before the game ends (falling back to an earlier quarter above 1, or 0), averaged over the 5 seeds.
- **Starter.** `my_ai/main.nut` line 5 calls `GetQuarterlyCompanyValue(AICompany.COMPANY_SELF, AICompany.CURRENT_QUARTER)`. `Dockerfile.work` builds the fixed work image from the original work image's digest (image about 0.46 GB compressed); `work.image_tag` becomes `f2e9a9fb0fff-ebv-v2`.
- **Basis in the game's code.** The OpenTTD 13.4 source defines `GetQuarterlyCompanyValue` as `CalculateCompanyValue(c)` for `CURRENT_QUARTER` and as `old_economy[quarter - 1].company_value` otherwise. The cached 13.4 program contains the name `GetQuarterlyCompanyValue` and not `GetCompanyValue`. A probe script reported `has_GetCompanyValue=false has_GetQuarterlyCompanyValue=true`.
- The grader image, `eval_cmd`, parser and score scale (`log_max`, with reference points 1e5 to 1e9) are unchanged, so each submission scores the same under the original and fixed versions.

Side-by-side run (exact original `eval_cmd`, 5 seeds, 20 game years; copied from `paired/results.md`). `TOTAL_SCORE` is the raw result (before conversion to 0–100).

| Test submission | Task version it ships with | Script crashed? | `TOTAL_SCORE`, original | `TOTAL_SCORE`, fixed | Company value per seed (as read by the grader) | Error flag (5 seeds) |
|---|---|---|---|---|---|---|
| baseline_v1 (supplied starter) | original | yes, at `main.nut` line 5 | 0 | 0 | 0 on all 5 seeds | 5/5 YES |
| probe_min (calls the correct function monthly) | follows fixed instructions | no | 0 | 0 | 0 on all 5 seeds | 0/5 |
| baseline_v2 (fixed starter) | fixed | no | 0 | 0 | 0 on all 5 seeds | 0/5 |
| probe_value (test submission with a positive value) | follows fixed instructions | no | 4975 | 4975 | 4,975 on all 5 seeds | 0/5 |

The test submission that shows the problem, the supplied starter, on the same grader:

| Starter | Script crashed? (original) | Script crashed? (fixed) | `TOTAL_SCORE`, original | `TOTAL_SCORE`, fixed |
|---|---|---|---|---|
| supplied starter (original work image vs fixed work image) | yes, at `main.nut` line 5 | no | 0 | 0 |

- The idle probes score 0 because an idle company's value stays at the floor of 1 (cash minus a 100,000 loan is negative), which the grader counts as 0. They show that the script survives, not a positive score.
- For both probes, on every seed, the last logged `GetQuarterlyCompanyValue(SELF, 1)` equals the `old_economy[0].company_value` that the grader used. For `probe_value` that is 4,975, while the running `CURRENT_QUARTER` value at the end was 4,858.

**Score compatibility:** scores are comparable as measurements of the same harness. They are not comparable as measures of solver ability where a solver of the original version followed the instructions and called the missing function.

## How we checked it

- **Original grader in the original image, pinned by digest.** The exact eval_cmd, `cd /home/workspace/openttd_ai && OPENTTD_N_SEEDS=5 python3 /tmp/eval_openttd.py`, ran offline under `timeout 2600` in the grader image (`--network none --memory 6g`) on an 8-vCPU host, so all 5 seeds ran in parallel. The submission was the supplied starter `my_ai/` from the work image. OpenTTD 13.4 and OpenGFX 7.1 (the game's graphics set) are pre-cached in the image.
- **Save-file check.** A seed-0 diagnostic (`diag1.py`) calls `run_experiments` with the grader's own arguments and prints every save row.
- **Side-by-side run of the original and fixed versions.** The tables above. It was repeated three times with no verdict change ([`data/paired-repeatability.md`](../data/paired-repeatability.md)).

## Limits

- No AI model or solver was run. Effects are shown only on the supplied starter and probes we wrote.
- In the side-by-side run each test submission was graded once, because the grader image is the same in both versions; the original and fixed `TOTAL_SCORE` columns repeat that score. The versions differ only in the starter and instructions the solver receives.
- The only test submission with a positive raw result is a probe (4,975, far below 1e5, the lower reference point of the score scale, so 0 out of 100). Every company value up to 1e5 scores 0 out of 100, so a score of 0 does not tell a crashed script from a weak one. Whether 1e9, the upper reference point, can be reached was not tested.
- The documentation path in the instructions (`docs/noai_api_docs/`) differs from the real one (`docs/openttd_reference_docs/noai_api_docs/`), and the supplied HTML documentation appears to be from a later OpenTTD than 13.4. Both are noted in the package README and not changed.
- The ticks/s figure is for an idle script on one host. An AI running many vehicles will be slower; that was not measured.

## Reproduce

- Original grader image: `sha256:27167956fd00…`.
- `evidence/runs/openttd_transport_ai-native-baseline/run.sh` (full run) and `evidence/runs/openttd_transport_ai-native-saves-diag/run.sh` (with `diag1.py`). They need a Docker host that can pull the pinned images.
- Review: `evidence/reviews/openttd_transport_ai-native.md`.
- Fix and side-by-side run: `repairs/openttd_transport_ai-v2/` (`paired/stage.sh` then `tools/e2b_run.py`).
