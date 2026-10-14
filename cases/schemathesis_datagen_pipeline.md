# Schemathesis data-generation pipeline (`schemathesis_datagen_pipeline`)


**2026-10-13 revision:** v2.1 restores the RFC year floor (year ≥ 1900). A clean native run (`schemathesis_datagen_pipeline-v2.1-native-20261013b`, ledger `exit=0`) built the v2.1 image from the package and ran the original evaluation command on six arms. The valid generator kept reward 0.477350, while the pre-1900 and garbage generators fell to 0.467094. These finite controls do not certify the whole task. See [follow-up](../repairs/schemathesis_datagen_pipeline-v2/paired/followup.md).

**Outcome:** Original defect confirmed; v2.1 repair validated on paired native controls. <mark>The hidden test for HTTP dates checks only the shape of the string, so generators that emit impossible dates and clock times pass; the gap is worth about 1% of the score.</mark>

![The original date test accepts a nonsense date string and all 50 dates from a generator whose dates are about 90% impossible; the fixed test accepts only the 5 valid ones.](figures/schemathesis_datagen_pipeline.svg)

*The original date test checked only the string shape, so a generator whose dates are about 90% impossible passed 50 of 50; the fixed test accepts only the 5 valid dates.*

## What the task asks

The solver builds data-generation strategies for schemathesis 4.14.3, a tool that tests web APIs. The task tells the solver to "Treat `/app/TODO.md` as the authoritative task specification." `TODO.md` Target 1 asks for an "**HTTP-date strategy**: Generate valid HTTP-date values in IMF-fixdate format". It adds that "In positive generation mode, all generated values should conform to the protocol grammar." RFC 9110 §5.6.7, the standard for HTTP dates, annotates `time-of-day` as `00:00:00 - 23:59:60 (leap second)`. It leaves the meaning of the date fields to RFC 5322 §3.3, which requires a date-time to be "semantically valid": a real day of the month, a matching weekday and a clock time in range. Category: Systems & Software Engineering.

## What goes wrong

Generated HTTP dates must be valid dates in IMF-fixdate format. The original test checks each string against `^\w{3}, \d{2} \w{3} \d{4} \d{2}:\d{2}:\d{2} GMT$` and nothing else. The pattern does not check:

- that the date exists in the calendar (31 Apr and 29 Feb 2023 do not);
- that the weekday matches the date;
- clock bounds, such as 24:00;
- that the weekday and month names are real names. `\w{3}` accepts any three word characters, so `"Abc, 99 Xyz 0000 99:99:99 GMT"` passes.

A realistic generator, `independent_fields`, draws weekday, day, month, year and clock independently and produces impossible dates and mismatched weekdays in about 90% of draws. Of 50 draws with fixed randomness, the original pattern accepted 50/50 and the fixed check 5/50. Under the task's specification the date test should fail, but on the original grader Phase 1 passes this generator at 15/15.

A wrong generator gains nothing over a correct one, but both receive the same Phase 1 credit, so the test cannot tell them apart.

## How much it matters

The effect is at most about 1% of the total. The date test is 1 of 15 Phase 1 tests, and Phase 1 has weight 2/13, so the effect is −2/195 of the total. It affects only solvers whose `http_date_values` emits invalid dates or clock times.

## The fix

The fixed version changes one file, `/tests/test_01_header_strategies.py`. It replaces the pattern that checks only the shape with the check `is_imf_fixdate`. That check covers the IMF-fixdate grammar, a real Gregorian date, agreement of the weekday and clock bounds, and allows `:60` only at 23:59. It requires a year of 1900 or later, because `TODO.md` asks for valid HTTP-date values and RFC 9110 §5.6.7 takes date semantics from RFC 5322 §3.3 ("any numeric year 1900 or later"). An earlier v2 dropped this floor (year ≥ 1); v2.1 restores it. The one date test's `max_examples` goes from 50 to 200. With 50 examples, the test caught rare clock defects (hour 24) in only 15/20 random seeds; with 200 it caught them in 20/20. The number of tests, `test.sh`, the weights and the parser are unchanged. In `task.json.in`, only `judge.image_tag` changes.

The current v2.1 result comes from a native run of the original `judge.eval_cmd` with `--cpus 2 --memory 4g --network none`.

| Generator | Role | Score, original grader | Score, fixed grader (v2.1) |
| --- | --- | --- | --- |
| stdlib_1900 | valid | 0.477350 | 0.477350 |
| stdlib_any_year (years before 1900) | invalid | 0.477350 | **0.467094** |
| garbage_shape | invalid | 0.477350 | **0.467094** |

The longer table below is the historical v2 run (year ≥ 1 predicate). Its test generators are `correct` (`st.datetimes(1970..2100)`); `stdlib_1900` and `stdlib_any_year` (generators based on `email.utils.format_datetime`; the second also emits years before 1900, which v2.1 rejects); `independent_fields` and `off_by_one_clock` (plausible but wrong; the latter draws hour 0 to 24 and minute 0 to 60); `garbage_shape` (invalid test submission, `"999, 99 888 0000 99:99:99 GMT"`); `rfc850` (test submission in the wrong format); and the untouched starter.

| Generator | Score, original grader | Score, historical v2 | Failures in 20 seeds, original / v2 |
| --- | --- | --- | --- |
| correct | 0.477350 | 0.477350 | — |
| stdlib_1900 | 0.477350 | 0.477350 | 0/20 / 0/20 |
| **stdlib_any_year** | 0.477350 | **0.477350** | 0/20 / 0/20 |
| independent_fields | 0.477350 | 0.467094 | 0/20 / 20/20 |
| off_by_one_clock | 0.477350 | 0.467094 | 0/20 / 20/20 |
| garbage_shape | 0.477350 | 0.467094 | — |
| rfc850 (invalid) | 0.467094 | 0.467094 | — |
| starter | 0.323504 | 0.323504 | — |

Across all generators, `test_http_date_values_grammar` is the only test whose result changes. For the three rejected generators, the `test_phase_1` summary item also flips from passed to failed. All other 97 items are unchanged. Scores are partial because the other targets stay at the starter. In historical v2 no generator with in-range years lost points; under v2.1 `stdlib_any_year` also loses 1/15 of Phase 1, because it emits years before 1900. Every plausible but wrong generator, and the garbage that only has the right shape, loses 1/15 of Phase 1. Both versions reject the test submission in the wrong format.

The fixed version (v2.1) scores differently from the original only for submissions whose `http_date_values` emits invalid dates, years before 1900 or invalid clock times that the test's 200 sampled examples hit. Those lose 1/15 of Phase 1 (−2/195 of the total). All other submissions score identically.

## How we checked it

- We ran the original grader from the public image pinned by digest. The grader image holds the unmodified schemathesis 4.14.3 starter with hypothesis 6.155.2 (the property-testing library) and no reference solution. Each generator ran under the full original `judge.eval_cmd` and under the fixed version, in fresh `--network none` containers. We also ran the single date test with 20 Hypothesis seeds.
- As an independent check, a pure-Python script ran the original pattern and the fixed check on fixed strings (31 Apr, 24:00, a wrong weekday, 29 Feb 2023, 29 Feb 2024 and `Sat, 31 Dec 2016 23:59:60`) and checked calendar validity against Python's Gregorian `calendar`.
- We did the side-by-side run of the original and fixed graders three times, and no result changed (`data/paired-repeatability.md`).

## Limits

- We ran no AI model or solver. The effects shown come only from the generators we wrote.
- The generators are a minimal overlay for Target 1. No upstream reference generator was available, so the scores are partial.
- The check does not test whether a leap second occurred. It allows `:60` only at 23:59 and does not compare it with the real table of leap seconds.
- The property tests remain random. The test caught the wrong generators we tried in 20/20 seeds, but rarer defects could still pass a given seed.
- We do not know how often such bugs occur in real submissions.

## Reproduce

- Grader image: `sha256:16b21364…`.
- Original vs fixed test: first run `evidence/scripts/schemathesis_datagen_pipeline/fetch_tests.sh`, which extracts the hidden tests from the pinned image.
- Then run `run_in_judge.sh` with `headers_overlay.py`, `run_seed_sweep.sh` and `check_witnesses.py` from the same folder. The saved outputs are `observed_output.txt`, `observed_seed_sweep.txt` and `observed_witnesses.txt`.
- Side-by-side run of the original and fixed graders: run `repairs/schemathesis_datagen_pipeline-v2/paired/run.sh` and `paired/extra.sh` (`repairs/schemathesis_datagen_pipeline-v2/` is the folder holding the fixed version). Results are in `paired/results.md`. The table above is the final run, `evidence/runs/schemathesis_datagen_pipeline-v2-paired-b/result/out/summary.md` (seed sweep in `result/out/extra.log`); `paired/raw-summary.md` and `paired/seed-sweep.txt` record an earlier run with a year ≥ 1900 floor in the fixed check and are superseded.
- v2.1 native run (current fix): `evidence/runs/schemathesis_datagen_pipeline-v2.1-native-20261013b/run.sh`, results in `result/out/summary.txt` and at the top of `paired/results.md`.
- Fix: `repairs/schemathesis_datagen_pipeline-v2/repair.patch`, `Dockerfile`, `source-lock.json`.

Supporting records: `repairs/schemathesis_datagen_pipeline-v2/` and `evidence/reviews/schemathesis_datagen_pipeline.md`.
