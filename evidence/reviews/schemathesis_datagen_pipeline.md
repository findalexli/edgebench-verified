# Review: schemathesis_datagen_pipeline

## Claim under review

> "The complete HTTP-date property accepts impossible April 31 and hour 24 values under supplied strategies."

Earlier disposition: **Withhold original** (`TASKS.md` row 49, `evidence/selected/datagen-original-exclusion.json`, decision `ADOPT_EXACT_ORIGINAL_WITHHOLDING`). Proposed repair: `proposedrepairs/datagen-http-date/` (V2 predicate `is_imf_fixdate`).

## Pinned artifacts

- Judge image: `seededge/edgebench.judge.schemathesis_datagen_pipeline@sha256:16b21364d67906d802e24d0b3b4505c42a6ac0f91cd5b382bb4c9d1d20224d37`. I pulled it and ran it locally. `/app` is the unmodified schemathesis 4.14.3 starter with hypothesis 6.155.2, and the image contains no reference solution.
- `/tests/test_01_header_strategies.py` sha256 `f2bf937f58549d6a82468883cf5a199357cef2caaf5dc9da865f962648bdeec6`, read from the image. It matches the earlier record.
- `/tests/test.sh` sha256 `82939a75d3ce1f9a7ef4f74420975e673cef8e4d8ed57085b9f468c6e0cfbf84`.
- Repaired test after applying `repair.patch`: `b5ae22f45cd7e7a2cb9f74979fa599cfdb97d672ca1d971682416871dd94261d`. It matches the manifest.
- `TODO.md`, from the cloud-export work tree, sha256 `3cf8492eacc5b49379f239ea1bb11933dd88f7382bb5cf77f045a4256e06fb82`. It matches the earlier record.
- RFC texts fetched from rfc-editor.org: RFC 9110 §5.6.7 and RFC 5322 §3.3.

## Contract

`TODO.md` Target 1, line 44:

> "**HTTP-date strategy**: Generate valid HTTP-date values in IMF-fixdate format."

Line 36 adds: "In positive generation mode, all generated values should conform to the protocol grammar."

**RFC check.** The ABNF alone is purely syntactic (`day = 2DIGIT`, `hour = 2DIGIT`). The RFCs nonetheless restrict both the clock and the date:

- RFC 9110 §5.6.7 annotates the grammar itself: `time-of-day = hour ":" minute ":" second ; 00:00:00 - 23:59:60 (leap second)`.
- RFC 9110 §5.6.7 also states that "the semantics of day-name, day, month, year, and time-of-day are the same as those defined for the Internet Message Format constructs with the corresponding name ([RFC5322], Section 3.3)".
- RFC 5322 §3.3: "A date-time specification MUST be semantically valid. That is, the day-of-week (if included) MUST be the day implied by the date, the numeric day-of-month MUST be between 1 and the number of days allowed for the specified month (in the specified year), the time-of-day MUST be in the range 00:00:00 through 23:59:60 … The year is any numeric year 1900 or later."
- RFC 9110 also says "An HTTP-date value represents time as an instance of … UTC". April 31 is not an instant.

So "31 Apr" and "24:00:00" are syntactically admissible under the ABNF, but they are not *valid* HTTP-dates. The task promises *valid* values, so the promise covers calendar validity, weekday agreement and clock bounds.

Scoring: `weights = [2, 1, 2, 2, 2, 1, 1, 2]`. Phase 1 has 15 collected tests and weight 2/13. If exactly one Phase 1 test fails, the score drops from 2/13 to (14/15)·(2/13), which is about 1.0% of the total.

## Independent reproduction

Scripts are in `evidence/scripts/schemathesis_datagen_pipeline/`.

`headers_overlay.py` is a minimal Target 1 module that I wrote independently, with all six names the test imports. It offers five `http_date_values` implementations, selected by `EBV_DATE_VARIANT`:

- `correct`: `st.datetimes(1970..2100)` formatted locale-independently.
- `independent_fields`: a plausibly-wrong "grammar-driven" generator. It draws weekday, day 1–31, month, year and clock from separate strategies.
- `off_by_one_clock`: plausibly wrong. Real dates, but hour drawn from 0–24 and minute from 0–60.
- `garbage_shape`: a control such as `"999, 99 888 0000 99:99:99 GMT"`.
- `rfc850`: the wrong format, as a control.

Range and ETag strategies are minimal valid implementations.

`run_in_judge.sh` runs the full original and the full repaired `test_01_header_strategies.py` (15 tests each) in the original judge image, then reports 50 derandomized draws per variant. Output is in `observed_output.txt`:

```
variant=correct            orig: 15 passed     repaired: 15 passed
variant=independent_fields orig: 15 passed     repaired: 1 failed, 14 passed
variant=off_by_one_clock   orig: 15 passed     repaired: 15 passed   (seed-dependent, see below)
variant=garbage_shape      orig: 15 passed     repaired: 1 failed, 14 passed
variant=rfc850             orig: 1 failed      repaired: 1 failed
draws independent_fields: 50/50 accepted by original regex, 5/50 by V2 predicate
draws off_by_one_clock:   50/50 original, 48/50 V2 (e.g. 'Tue, 16 May 1972 24:19:00 GMT')
draws garbage_shape:      50/50 original, 0/50 V2
```

`run_seed_sweep.sh` runs the repaired date test over 20 Hypothesis seeds (`observed_seed_sweep.txt`):

| Variant | Seeds failing |
|---|---|
| `independent_fields` | 20/20 |
| `off_by_one_clock` | 15/20 |
| `correct` | 0/20 |

`check_witnesses.py` is a pure-Python check of fixed strings, with output in `observed_witnesses.txt`:

- The original regex `^\w{3}, \d{2} \w{3} \d{4} \d{2}:\d{2}:\d{2} GMT$` accepts every witness: 31 Apr, 24:00, wrong weekday, 29 Feb 2023, and `"Abc, 99 Xyz 0000 99:99:99 GMT"`.
- V2 rejects all the invalid witnesses and accepts the valid ones, including 29 Feb 2024 and `Sat, 31 Dec 2016 23:59:60`.

## Refutation attempts

- **Is the trigger contrived?** The earlier evidence used `st.just(<fixed string>)` singleton strategies. That is a fixture, not a submission. I replaced it with a realistic field-by-field generator, the most natural "write it from the grammar" bug. That generator produces impossible dates and mismatched weekdays in about 90% of draws, and the original phase still passes it at 15/15.
- **Does the RFC actually forbid these values?** Yes, as quoted above, through the prose and the annotated grammar comment, though not through the bare ABNF. The prompt also says "valid".
- **Does the wrong generator gain score over a correct one?** No. Both receive 15/15 in Phase 1. The defect is uncredited spec violation, worth about 1% of the total, not a ranking inversion.
- **Practical impact.** A generator that emits impossible dates in positive mode defeats the purpose of Target 1, which is to send protocol-valid conditional headers. So this is a meaningful behavior gap, not a cosmetic one.
- **The earlier claim is narrower than reality.** The original check is shape-only, and `\w{3}` accepts any three word characters, so it does not even enforce the weekday/month name sets, digit ranges or year ≥ 1900. "Accepts April 31 and hour 24" understates the weakness.

## Formal check

None needed. The repaired predicate was checked against `calendar` (Gregorian) on 8 fixed witnesses and on 50 derandomized draws per variant.

## Verdict

**CONFIRMED (broader than stated).** The original HTTP-date check is a shape-only regex. It accepts impossible calendar dates, weekday/date mismatches, out-of-range clocks and even non-month or non-weekday tokens. A realistic wrong generator passes the full original Phase 1 at 15/15.

## Disposition assessment

"Repair (strengthened test, new version)" is the right outcome. Withholding the unchanged original is defensible only as shorthand for "ship the repaired version instead". The defect affects one property worth about 1% of total score and never penalizes a correct solution. That is not a reason to drop the task's other seven targets from the benchmark.

I would therefore count this as a **repair**, not an exclusion finding, in headline numbers. The repaired test has been executed against a real (overlay) generator in the native judge, which the earlier evidence lacked, so the main stated blocker ("this fixture run does not validate a generator") is addressed in part.

## Recommended publishable wording

> "In schemathesis_datagen_pipeline, the hidden test for the HTTP-date header strategy checks only the shape of the string. Generators that emit impossible dates (31 Apr, mismatched weekday) or out-of-range clocks (24:00) pass, contrary to the task's 'valid HTTP-date' requirement and RFC 9110/5322 semantics. We replace the regex with a calendar/clock validity check in a versioned task; the gap affects about 1% of the task score."

## Repair note

The V2 predicate is correct for the cases I checked:

- Gregorian day-of-month, including leap years.
- Weekday agreement, clock bounds, and year ≥ 1900.
- `:60` only at 23:59. This is stricter than RFC 5322's range but consistent with how leap seconds are actually inserted. A correct `st.datetimes` generator never emits `:60`, so it costs nothing.

It is minimal, touching one helper and one assertion, and leaves test counts unchanged. One weakness: with `max_examples=50`, rare defects such as hour 24 at a 1/25 rate are caught in only about 75% of seeds. That nondeterminism is inherent to the original property-test design. Raising `max_examples` to about 200 for this one test would make detection of such generators near-certain at negligible cost. This is optional.

## Limits

- I used a minimal Target 1 overlay that I wrote myself, not a complete solution. Only Phase 1 was executed, not the full `test.sh`.
- The upstream reference generator is not in the image and was not checked.
- `TODO.md` came from the cloud export, but its hash matches the earlier record.
- The frequency of such bugs in real submissions is unknown.

## Rerun

Run `scripts/<task>/fetch_tests.sh` first. It extracts the hidden tests from the pinned judge image into `tests_orig/` and applies the proposed patch into `tests_repaired/`, printing the hashes above. The hidden tests themselves are not stored in this repository. Then run the `run_*.sh` scripts as shown, with `-v <scripts dir>:/ebv:ro`.
