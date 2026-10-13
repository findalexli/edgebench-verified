# v2.1 follow-up, 2026-10-13

The year floor is restored to 1900. RFC 9110 §5.6.7 inherits RFC 5322 §3.3 semantics; the task's request for valid HTTP dates need not restate that standard. Historical controls emitting years 1–1899 cannot establish valid-generator compatibility.

The cached v2 replacement was checked against its recorded hash, reverse-patched, and the recovered original matched `f2bf937f58549d6a82468883cf5a199357cef2caaf5dc9da865f962648bdeec6`. The new diff applies to that original and the output hash is locked in `source-lock.json`.

`evidence/scripts/validator_followup/datagen.py ORIGINAL MATERIALIZED_CANDIDATE` runs the actual original regex and revised predicate. Twelve explicit witnesses cover year bounds, century/leap dates, weekdays and clock limits. Independent `datetime` checks enumerate all days of 13 selected boundary years. Results: [followup-component.json](followup-component.json), all assertions passed.

## Native follow-up

The original digest-pinned image and v2.1 image ran the exact original `judge.eval_cmd` on the same three authored overlays, in serial containers with 2 CPUs, 4 GiB memory and no network. All six arms exited 0 in 19–22 seconds.

| Control | Original reward | v2.1 reward | Wall seconds original / v2.1 |
|---|---:|---:|---:|
| `stdlib_1900` valid generator | 0.477350 | 0.477350 | 19 / 20 |
| `stdlib_any_year` including pre-1900 dates | 0.477350 | 0.467094 | 20 / 20 |
| `garbage_shape` invalid dates | 0.477350 | 0.467094 | 22 / 21 |

The two invalid controls lose exactly the one HTTP-date test (rounded reward difference 0.010256, theoretical 2/195). The rest of these minimal Target 1 overlays is not a complete solution to the task.

[Collected native outputs](native-20261013-v2.1/summary.txt) include rewards, structured evaluation stdout and image identities. The shared worker was later intentionally stopped after the separate FFmpeg v2.1 experiment timed out; its overall status is `exit=143`, with `killed=true`. That does not invalidate the six completed Datagen slices, and is not reported as an all-job success. Native inputs are hashed; the recipe is `evidence/scripts/validator_followup/run_native.sh` (the recorded first-attempt recipe).

This establishes finite native repair controls, not whole-task certification or universal sampling behavior. The historical v2 Lean model is still not a proof of v2.1. Local Docker was unavailable; these runs used one owned E2B worker with 683 seconds elapsed across both tasks.

## Reconstruct the native inputs

The exact authored input is committed at `evidence/scripts/validator_followup/datagen_headers_overlay.py`; stage it as `headers_overlay.py`. Extract `judge.eval_cmd` from `tasks/schemathesis_datagen_pipeline.json` into `datagen-eval.sh`. The image/package inputs and environment variants are specified in `evidence/scripts/validator_followup/run_native.sh`; that file records the historical combined Datagen/FFmpeg v2.1 experiment, including its timeout limitation. Use only its Datagen arm for this repair. The FFmpeg v2.2 follow-up has a separate maintained preparation recipe. These input files are audit-authored controls, not a complete task solution.
