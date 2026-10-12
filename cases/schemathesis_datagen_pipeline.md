# Schemathesis data-generation pipeline (`schemathesis_datagen_pipeline`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Systems & Software Engineering
- **Decision:** Repair v2. The hidden HTTP-date test checks only the shape of the string, so generators that emit impossible dates and clock times pass. The gap is worth about 1% of the score.

## What the task promises

The solver is told to "Treat `/app/TODO.md` as the authoritative task specification." `TODO.md` Target 1 asks for an "**HTTP-date strategy**: Generate valid HTTP-date values in IMF-fixdate format". It adds: "In positive generation mode, all generated values should conform to the protocol grammar." RFC 9110 §5.6.7 annotates `time-of-day` as `00:00:00 - 23:59:60 (leap second)`. It defers the meaning of the date fields to RFC 5322 §3.3, which requires a date-time to be "semantically valid": a real day of the month, a matching weekday and an in-range clock.

## What we checked and how

- **Pinned judge image.** We pulled the image and ran it locally. `/app` is the unmodified schemathesis 4.14.3 starter with hypothesis 6.155.2. The image contains no reference solution.
- **Reviewer-written overlay.** A minimal Target 1 module supplied five `http_date_values` variants:
  - `correct`: `st.datetimes(1970..2100)`.
  - `independent_fields`: plausibly wrong. Weekday, day, month, year and clock are drawn independently.
  - `off_by_one_clock`: plausibly wrong. Hour is drawn from 0–24 and minute from 0–60.
  - `garbage_shape`: invalid control, `"999, 99 888 0000 99:99:99 GMT"`.
  - `rfc850`: wrong-format control.

  The paired run added two more honest generators based on `email.utils.format_datetime`: `stdlib_1900` and `stdlib_any_year`.
- **Phase 1 runs and seed sweeps.** Each variant ran under the full original and the repaired `test_01_header_strategies.py` in the judge image. The single date test was then swept over 20 Hypothesis seeds.
- **Fixed witnesses.** A pure-Python check ran the original regex and the repaired predicate on fixed strings: 31 Apr, 24:00, a wrong weekday, 29 Feb 2023, 29 Feb 2024 and `Sat, 31 Dec 2016 23:59:60`. Calendar validity was checked against Python's Gregorian `calendar`.
- **Paired v1/v2 run.** E2B workers ran the full original `judge.eval_cmd` in fresh `--network none` containers. A second run followed after the coordinator's amendment, described below.
- **Original identity.** Judge image `seededge/edgebench.judge.schemathesis_datagen_pipeline@sha256:16b21364…`. Key files and their sha256:
  - `test_01_header_strategies.py`: `f2bf937f…`
  - `test.sh`: `82939a75…`
  - `TODO.md`: `3cf8492e…`, from the earlier cloud export, matching the earlier record.

## What we found

**Confirmed, and broader than the earlier claim.** The original test checks the string against `^\w{3}, \d{2} \w{3} \d{4} \d{2}:\d{2}:\d{2} GMT$` and nothing else. The regex does not check:

- calendar validity, such as 31 Apr or 29 Feb 2023;
- that the weekday matches the date;
- clock bounds, such as 24:00;
- that the weekday and month names are real names. `\w{3}` accepts any three word characters, so `"Abc, 99 Xyz 0000 99:99:99 GMT"` passes.

The earlier claim, "accepts April 31 and hour 24", understates the weakness.

Example under the original evaluator: the realistic `independent_fields` generator produces impossible dates and mismatched weekdays in about 90% of draws. Of 50 derandomized draws, the original regex accepted 50/50 and the repaired predicate 5/50. The original Phase 1 still passed this generator at 15/15. Expected under the contract: the date test should fail.

**Maximum score effect:** about 1% of the total. The date test is 1 of 15 Phase 1 tests, and Phase 1 has weight 2/13, so the effect is −2/195 of the total. A wrong generator gains nothing over a correct one; both receive the same Phase 1 credit under v1.

**Earlier evidence re-checked.** The earlier evidence used fixed `st.just(<string>)` fixtures, not a generator. Re-checking with realistic field-by-field and off-by-one generators reproduced the gap. The earlier audit withheld the original. This review counts the task as a repair, not an exclusion.

## Repair

v2 changes one file, `/tests/test_01_header_strategies.py`. The shape-only regex is replaced by the predicate `is_imf_fixdate`. The predicate checks the IMF-fixdate grammar, a real Gregorian date, weekday agreement and clock bounds, and allows `:60` only at 23:59. The one date test's `max_examples` also goes from 50 to 200. With 50 examples, rare clock defects (hour 24) were caught in only 15/20 seeds; with 200 they were caught in 20/20. Test counts, `test.sh`, weights and parser are unchanged. In `task.json.in`, only `judge.image_tag` changes.

An earlier draft of the predicate also required year ≥ 1900, following RFC 5322. `TODO.md` does not state that rule, and the first paired run penalized an honest any-year generator because of it. The coordinator therefore removed the floor; the predicate now requires only a representable year (≥ 1). The table below is the re-run after that amendment[^1].

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

Across all variants, `test_http_date_values_grammar` is the only test whose result changes. All other 98 items are unchanged. Scores are partial because the other targets stay at the starter. No honest generator loses points. Every plausibly-wrong generator, and the shape-only garbage control, loses 1/15 of Phase 1. The wrong-format control is rejected in both versions.

**Score compatibility.** v2 differs from v1 only for submissions whose `http_date_values` emits invalid dates or clock times. Those lose 1/15 of Phase 1 (−2/195 of the total). All other submissions score identically.

## Limits and what was not run

- No model or solver re-runs. Effects are shown on authored generators and counterexamples only.
- The generators are the reviewer's minimal Target 1 overlay. No upstream reference generator was available, so absolute scores are partial.
- Leap-second occurrence is not validated. `:60` is allowed only at 23:59 but is not checked against the real leap-second table.
- Property tests remain randomized. Detection was 20/20 seeds for the wrong generators tested, but rarer defects could still pass a given seed.
- How often such bugs occur in real submissions is unknown. `TODO.md` came from the cloud export; its hash matches the earlier record.

## Reproduce

- Original vs repaired test: first run `evidence/scripts/schemathesis_datagen_pipeline/fetch_tests.sh`, which extracts the hidden tests from the pinned image.
- Then run `run_in_judge.sh` with `headers_overlay.py`, `run_seed_sweep.sh` and `check_witnesses.py` from the same folder. Saved outputs: `observed_output.txt`, `observed_seed_sweep.txt` and `observed_witnesses.txt`.
- Paired v1/v2: run `repairs/schemathesis_datagen_pipeline-v2/paired/run.sh` and `paired/extra.sh`. Results are in `paired/results.md`, `paired/raw-summary.md` and `paired/seed-sweep.txt`.
- Repair: `repairs/schemathesis_datagen_pipeline-v2/repair.patch`, `Dockerfile`, `source-lock.json`.

Supporting records: `repairs/schemathesis_datagen_pipeline-v2/` and `evidence/reviews/schemathesis_datagen_pipeline.md`.

[^1]: The first table in `paired/results.md` shows `stdlib_any_year` at v2 0.467094 with 20/20 failing seeds, under an earlier draft that required year ≥ 1900. The coordinator removed that floor; the amendment in `paired/results.md`, `decisions.json` and the updated repair README now agree that the predicate requires a representable year (≥ 1), with `stdlib_any_year` at 0.477350 and 0/20 failing seeds. The shipped `files/` and `repair.patch` contain `year < 1`. This page uses the amended values.
