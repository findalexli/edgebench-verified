> Historical v2 evidence. The current patch is v2.1 (2026-10-13); these native results do not validate that revision. See [followup.md](followup.md).

# Paired v1/v2 results: schemathesis_datagen_pipeline

> The first run below used an earlier fixed predicate with a year ≥ 1900 floor, and is superseded by the final run at the end of this file. `raw-summary.md` and `seed-sweep.txt` in this folder record the first run (they show `stdlib_any_year` at 0.467094 and 20/20 under the fixed version). The final run's raw scores are in `evidence/runs/schemathesis_datagen_pipeline-v2-paired-b/result/out/summary.md` (per run: `result/out/runs/<variant>.<v1|v2>/verifier/reward.txt`), and its seed sweep in `result/out/extra.log` of the same job. (`result/summary.json` one level up holds only empty rows, because it was summarized over the wrong files; ignore it.) The two repeats, `-paired-b-rep2` and `-paired-b-rep3`, give the same scores.

The E2B job `evidence/runs/schemathesis_datagen_pipeline-v2-paired` ran on worker `ijh8xbuxzxgq7qgagdvib` for 523 s, finished with exit 0 and was killed. It ran every variant through the full original `judge.eval_cmd` in fresh `--network none` containers:
- v1 is the pinned original `@sha256:16b21364…`.
- v2 was built in the worker from `../Dockerfile`.

The overlay is the reviewer's `headers.py` (`evidence/scripts/schemathesis_datagen_pipeline/headers_overlay.py`) plus two variants added for this run, `stdlib_1900` and `stdlib_any_year`. Other targets stay at the starter, so absolute scores are partial. Normalized score = raw score (linear 0..1).

| Variant | Role | v1 score | v2 score | Delta | Phase 1 v1 → v2 |
|---|---|---|---|---|---|
| starter | untouched starter | 0.323504 | 0.323504 | 0 | 0/15 → 0/15 |
| correct | `st.datetimes(1970–2100)` → IMF-fixdate | 0.477350 | 0.477350 | **0** | 8/8 → 8/8 |
| stdlib_1900 | second honest generator: `email.utils.format_datetime`, years 1900–9999 | 0.477350 | 0.477350 | **0** | 8/8 → 8/8 |
| independent_fields | plausibly wrong: day, month and weekday drawn independently (31 Apr, wrong weekday) | 0.477350 | 0.467094 | **−0.010256** | 8/8 → 14/15 |
| off_by_one_clock | plausibly wrong: hour 0–24, minute 0–60 | 0.477350 | 0.467094 | **−0.010256** | 8/8 → 14/15 |
| garbage_shape | invalid control that still matches the old regex (`999, 99 888 0000 99:99:99 GMT`) | 0.477350 | 0.467094 | −0.010256 | 8/8 → 14/15 |
| rfc850 | invalid control (wrong format) | 0.467094 | 0.467094 | 0 | 14/15 → 14/15 |
| stdlib_any_year | boundary probe: same formatter, Hypothesis default years 0001–9999 | 0.477350 | 0.467094 | −0.010256 | 8/8 → 14/15 |

The only test-function difference in any variant is `test_http_date_values_grammar`; the phase summary item `test_phase_1` flips with it for the failing variants. The other 97 items are unchanged. v1's "8/8" is the original script's success floor (`PHASE1_EXPECTED=8` with 15 collected tests); it is unchanged by v2.

Seed sweep (`seed-sweep.txt`): the single date test was run under 20 Hypothesis seeds per variant and image. v2 sets `max_examples=200` for this one test only.

| Variant | v1 failing seeds | v2 failing seeds |
|---|---|---|
| correct | 0/20 | 0/20 |
| stdlib_1900 | 0/20 | 0/20 |
| independent_fields | 0/20 | 20/20 |
| off_by_one_clock | 0/20 | **20/20** (was 15/20 at `max_examples=50`, reviewer sweep) |
| stdlib_any_year | 0/20 | 20/20 (example: `Sun, 01 Jan 1899 00:00:00 GMT`) |

- **Trigger:** both plausibly-wrong generators score the same as correct under v1 and lose 1/15 of phase 1 (−2/195 ≈ −0.0103) under v2, deterministically across 20 seeds. Holds.
- **Valid controls:** both honest generators keep their score. Holds.
- **Invalid controls:** rfc850 is rejected in both versions. garbage_shape was accepted by v1 and is rejected by v2. Holds.
- **Judgment point, not hidden:** `stdlib_any_year` loses points under v2 because it emits years before 1900. RFC 9110 §5.6.7 defers to RFC 5322 §3.3 ("any numeric year 1900 or later"), but `TODO.md` says only "valid HTTP-date values". To avoid that interpretive call, drop the `year < 1900` clause; the other checks are unaffected.

Note: `paired/run.sh` differs from the executed job script only in the `/tests` hash-listing fix. v2 hashes were verified on a local build: `v2-image-tests.sha256`.

## Final paired run (year ≥ 1900 floor removed)

The first paired run penalized `stdlib_any_year` (an honest generator using the full year range)
because the v2 predicate applied RFC 5322's "year ≥ 1900" rule, which the task does not state.
The predicate now requires only a representable year (≥ 1). Re-run on E2B
(job `evidence/runs/schemathesis_datagen_pipeline-v2-paired-b`, worker `ip3daxuk9utuu81sq1s8k`, killed):

| variant | v1 | v2 | 20-seed sweep v1 / v2 |
| --- | --- | --- | --- |
| correct | 0.477350 | 0.477350 | — |
| stdlib_1900 | 0.477350 | 0.477350 | 0/20 / 0/20 |
| **stdlib_any_year** | 0.477350 | **0.477350** (was 0.467094) | 0/20 / 0/20 |
| independent_fields | 0.477350 | 0.467094 | 0/20 / 20/20 |
| off_by_one_clock | 0.477350 | 0.467094 | 0/20 / 20/20 |
| garbage_shape | 0.477350 | 0.467094 | — |
| rfc850 (invalid) | 0.467094 | 0.467094 | — |
| starter | 0.323504 | 0.323504 | — |

No honest generator loses points; all plausibly-wrong generators are caught. **Accepted.**
