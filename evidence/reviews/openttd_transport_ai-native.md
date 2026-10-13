# openttd_transport_ai: native baseline evaluation (E2B)

> **Note (2026-10-12).** "Crashes on its first statement" below: the starter first logs
> "MyAI baseline started." and crashes at its first call to `GetCompanyValue`, in its main loop at
> `main.nut` line 5. See `cases/openttd_transport_ai.md`.

## Question

Does one full original 5-seed evaluation with the shipped baseline AI do three things?

- Run offline.
- Return every requested seed.
- Fit within `eval_timeout` 3600 s.

Also: what score, and how many ticks/s?

## Pinned artifacts

- Judge image: `seededge/edgebench.judge.openttd_transport_ai@sha256:27167956fd001115b0f6bb3e39e2e220ecd84e053dc3624d2fc3bc07bc9fc09c`
- Work image (baseline source): `seededge/edgebench.work.openttd_transport_ai@sha256:8c1921e643eda26524123b772dd3b6c637566f39f4dddb99ccea6db3e68627e0`
- Evaluator files, with sha256 measured in the container:
  - `/tmp/eval_openttd.py`: `167e480ac2046406999b297a122c196d28160748942aba9a35f622cefb70ba56`
  - `/tmp/openttd_original_eval.py`: `76dae84357c7cf0baf1d712bd88086ce12c0475129d29c9daa1656cb6b123634`
  - `openttdlab.py` (OpenTTDLab 0.0.75): `5017fa28a5629acc73c50e09a9893307eff9f159acd5795a746308282594d8a2`. This matches the "final module" hash in the earlier library acceptance record.
- Baseline `my_ai/` (from the work image):
  - `info.nut`: `891c4c91dab3ab7a57e58c8546708cf60684d172f9e4ecbefbcec88de0141624`
  - `main.nut`: `77e77c13ae0ff527ad8fe6b9d25c9a079c8ee625a5bcdf8173abb1e9248eb768`
- OpenTTD 13.4 and OpenGFX 7.1 archives are pre-cached in the image under `/root/.cache/OpenTTDLab/0.0.75/`, so no network is needed.

## Execution

- Containers: judge image, `--network none --memory 6g`, root, 8 vCPU (`os.cpu_count()` = 8, so all 5 seeds ran in parallel).
- Job: `evidence/runs/openttd_transport_ai-native-baseline/`.
  - Attempt 1 (worker `irbl4y7lk0tdfemhv0q8b`) produced nothing because of a host-side output-path bug in my `run.sh`. No evaluation ran; that output is kept in `result-attempt1-redirect-bug/`.
  - Attempt 2 (worker `il5n70qlrvt2ndf91lizr`, exit 0, 101 s, killed) ran the exact `eval_cmd` offline: `cd /home/workspace/openttd_ai && OPENTTD_N_SEEDS=5 python3 /tmp/eval_openttd.py`, under `timeout 2600`.
  - The networked fallback was not needed.
- Diagnostic: `evidence/runs/openttd_transport_ai-native-saves-diag/` (worker `ie79drsuxuda7iyp78lwo`, exit 0, 81 s, killed). `diag1.py` runs seed 0 through the evaluator's own `run_experiments` arguments and dumps every save row.

## Results

**Full original evaluation** (`full_eval_offline.txt`): wall time **63 s**, exit 0, all 5/5 requested seeds returned.

| Seed | Company value | CV date | Money | Loan | Net worth | Error |
|---|---|---|---|---|---|---|
| 0 | 0 | N/A | 54,191 | 100,000 | -45,809 | YES |
| 1 | 0 | N/A | 54,191 | 100,000 | -45,809 | YES |
| 2 | 0 | N/A | 54,191 | 100,000 | -45,809 | YES |
| 3 | 0 | N/A | 54,191 | 100,000 | -45,809 | YES |
| 4 | 0 | N/A | 54,191 | 100,000 | -45,809 | YES |

`最终得分（平均公司市值）: 0`. The wrapper printed `CASE 0000 WA score=0` and `TOTAL_SCORE 0`.

**Seed-0 diagnostic** (`diag1.txt`):

- There are 239 monthly saves, from 1950-02-01 to 1969-12-01. The game runs the full 7,300 days.
- `old_economy[0].company_value` is 1 in every save. It never exceeds 1, so the evaluator's `> 1` filter yields 0. This matches the earlier source-only prediction for a do-nothing company.
- Speed: one seed alone took 55.4 s, which is about **9,750 ticks/s** (540,200 / 55.4). With 5 in parallel, the evaluation took 63 s.
- **The baseline AI crashes on its first statement.** All 239 rows have `error: True`, and the engine output reads:

```
dbg: [script] [0] [S] Your script made an error: the index 'GetCompanyValue' does not exist
dbg: [script] [0] [S] *FUNCTION [Start()] myai/main.nut line [5]
dbg: [script] The script died unexpectedly.
```

The shipped baseline calls `AICompany.GetCompanyValue(AICompany.COMPANY_SELF)`, which does not exist in the OpenTTD 13.4 NoAI API. OpenTTDLab's `error` flag is `'The script died unexpectedly' in output` (`openttdlab.py:347`). The evaluator only prints that flag; it does not affect the score.

## What this establishes

- **Runtime is not a concern.** The run is offline-capable, returns all seeds and takes about 1 minute against 3,600 s, for this idle AI.
  - An AI that runs many vehicles and spends its opcode budget will be slower. That was not measured here.
  - The 9,750 ticks/s is far above the roughly 150 ticks/s needed.
- **Score definition behaves as read from source.** A do-nothing company scores 0, which normalizes to 0.
- **New starter/prompt defect.** The prompt's stated goal is "Maximize `AICompany.GetCompanyValue(AICompany.COMPANY_SELF)`", but that function does not exist in the pinned engine. The shipped baseline crashes for this reason.
  - An honest solver that follows the prompt and calls it will have its script killed at that call. The company then stops acting, and the score is its last positive quarterly value or 0.
  - This is detectable by local testing, which the prompt provides. It is a misleading-contract issue, not a scorer error.
- The 239 saves (not 240) and the final date 1969-12-01 mean the "last quarterly value" is the 1969-10 quarter. This is consistent with the earlier reading.

## Recommended disposition

**Retain with a note.** The note should say that the prompt's named metric function is not in the 13.4 API, and that the scored quantity is the last quarterly `company_value` from saves.

Smallest prompt/starter fix: the evaluator itself is fine. Name the scored quantity as the quarterly company value, for example `AICompany.GetQuarterlyCompanyValue(AICompany.COMPANY_SELF, AICompany.CURRENT_QUARTER)` or the previous quarter. Fix the baseline's logging call to use it. Whether that function exists in 13.4 was not verified here.

## Limits

- Only the crashing do-nothing baseline was run. There is no positive-score control, so the 1e9 upper anchor's reachability and determinism across runs are not tested.
- One run only, and `ticks/s` is for an idle script on this host.
