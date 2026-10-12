# Schemathesis data-generation pipeline (`schemathesis_datagen_pipeline`)

**Decision:** Repair (v2). The hidden HTTP-date test checks only the shape of the string, so generators that emit impossible dates and clock times pass; the gap is worth about 1% of the score.

## What the task asks for

The solver builds data-generation strategies for schemathesis 4.14.3 and is told to "Treat `/app/TODO.md` as the authoritative task specification." `TODO.md` Target 1 asks for an "**HTTP-date strategy**: Generate valid HTTP-date values in IMF-fixdate format". It adds: "In positive generation mode, all generated values should conform to the protocol grammar." RFC 9110 §5.6.7 annotates `time-of-day` as `00:00:00 - 23:59:60 (leap second)`. It defers the meaning of the date fields to RFC 5322 §3.3, which requires a date-time to be "semantically valid": a real day of the month, a matching weekday and an in-range clock. Category: Systems & Software Engineering.

## What goes wrong

**Rule.** Generated HTTP-dates must be valid dates in IMF-fixdate format. The original test checks each string against `^\w{3}, \d{2} \w{3} \d{4} \d{2}:\d{2}:\d{2} GMT$` and nothing else. The regex does not check:

- calendar validity, such as 31 Apr or 29 Feb 2023;
- that the weekday matches the date;
- clock bounds, such as 24:00;
- that the weekday and month names are real names. `\w{3}` accepts any three word characters, so `"Abc, 99 Xyz 0000 99:99:99 GMT"` passes.

**Example.** A realistic generator that draws weekday, day, month, year and clock independently (`independent_fields`) produces impossible dates and mismatched weekdays in about 90% of draws. Of 50 derandomized draws, the original regex accepted 50/50 and the repaired predicate 5/50. Expected under the contract: the date test should fail. Observed under the original evaluator: Phase 1 passes this generator at 15/15.

**Why it matters.** A wrong generator gains nothing over a correct one, but both receive the same Phase 1 credit, so the test cannot tell them apart.

## Impact

At most about 1% of the total. The date test is 1 of 15 Phase 1 tests, and Phase 1 has weight 2/13, so the effect is −2/195 of the total. Only solvers whose `http_date_values` emits invalid dates or clock times are affected.

## Fix (v2)

v2 changes one file, `/tests/test_01_header_strategies.py`. The shape-only regex is replaced by the predicate `is_imf_fixdate`. The predicate checks the IMF-fixdate grammar, a real Gregorian date, weekday agreement and clock bounds, and allows `:60` only at 23:59. It requires only a representable year (≥ 1), because `TODO.md` states no year floor. The one date test's `max_examples` goes from 50 to 200: with 50 examples, rare clock defects (hour 24) were caught in only 15/20 seeds; with 200 they were caught in 20/20. Test counts, `test.sh`, weights and parser are unchanged. In `task.json.in`, only `judge.image_tag` changes.

Variants: `correct` (`st.datetimes(1970..2100)`); `stdlib_1900` and `stdlib_any_year` (honest generators based on `email.utils.format_datetime`); `independent_fields` and `off_by_one_clock` (plausibly wrong; hour 0–24 and minute 0–60 for the latter); `garbage_shape` (invalid control, `"999, 99 888 0000 99:99:99 GMT"`); `rfc850` (wrong-format control); and the untouched starter.

| variant | v1 | v2 | 20-seed sweep v1 / v2 |
| --- | --- | --- | --- |
| correct | 0.477350 | 0.477350 | — |
| stdlib_1900 | 0.477350 | 0.477350 | 0/20 / 0/20 |
| **stdlib_any_year** | 0.477350 | **0.477350** | 0/20 / 0/20 |
| independent_fields | 0.477350 | 0.467094 | 0/20 / 20/20 |
| off_by_one_clock | 0.477350 | 0.467094 | 0/20 / 20/20 |
| garbage_shape | 0.477350 | 0.467094 | — |
| rfc850 (invalid) | 0.467094 | 0.467094 | — |
| starter | 0.323504 | 0.323504 | — |

Across all variants, `test_http_date_values_grammar` is the only test whose result changes; for the three rejected generators the `test_phase_1` summary item also flips from passed to failed. All other 97 items are unchanged. Scores are partial because the other targets stay at the starter. No honest generator loses points. Every plausibly-wrong generator, and the shape-only garbage control, loses 1/15 of Phase 1. The wrong-format control is rejected in both versions.

**Score compatibility.** v2 differs from v1 only for submissions whose `http_date_values` emits invalid dates or clock times that the test's 200 sampled examples hit. Those lose 1/15 of Phase 1 (−2/195 of the total). All other submissions score identically.

## How we know

- **Original evaluator in the pinned image.** The judge image (`sha256:16b21364…`) holds the unmodified schemathesis 4.14.3 starter with hypothesis 6.155.2 and no reference solution. Each variant ran under the full original `judge.eval_cmd` and under v2, in fresh `--network none` containers. The single date test was also swept over 20 Hypothesis seeds.
- **Independent oracle.** A pure-Python check ran the original regex and the repaired predicate on fixed strings: 31 Apr, 24:00, a wrong weekday, 29 Feb 2023, 29 Feb 2024 and `Sat, 31 Dec 2016 23:59:60`. Calendar validity was checked against Python's Gregorian `calendar`.
- **Repeatability.** The paired evaluation was run three times; no verdict changed (`paired-repeatability.md`).

## Limits

- No model or solver was run. Effects are shown on authored generators only.
- The generators are a minimal Target 1 overlay. No upstream reference generator was available, so absolute scores are partial.
- Leap-second occurrence is not validated. `:60` is allowed only at 23:59 but is not checked against the real leap-second table.
- Property tests remain randomized. Detection was 20/20 seeds for the wrong generators tested, but rarer defects could still pass a given seed.
- How often such bugs occur in real submissions is unknown.

## Reproduce

- Original vs repaired test: first run `evidence/scripts/schemathesis_datagen_pipeline/fetch_tests.sh`, which extracts the hidden tests from the pinned image.
- Then run `run_in_judge.sh` with `headers_overlay.py`, `run_seed_sweep.sh` and `check_witnesses.py` from the same folder. Saved outputs: `observed_output.txt`, `observed_seed_sweep.txt` and `observed_witnesses.txt`.
- Paired v1/v2: run `repairs/schemathesis_datagen_pipeline-v2/paired/run.sh` and `paired/extra.sh`. Results are in `paired/results.md`, `paired/raw-summary.md` and `paired/seed-sweep.txt`. The `stdlib_any_year` row above is the amended result recorded in `paired/results.md`.
- Repair: `repairs/schemathesis_datagen_pipeline-v2/repair.patch`, `Dockerfile`, `source-lock.json`.

Supporting records: `repairs/schemathesis_datagen_pipeline-v2/` and `evidence/reviews/schemathesis_datagen_pipeline.md`.
