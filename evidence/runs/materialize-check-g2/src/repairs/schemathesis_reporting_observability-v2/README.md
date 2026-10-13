# Fixed version of `schemathesis_reporting_observability`: JUnit XML and coverage body suppression checks

## What this fixes

Two hidden tests in the original grader give credit for wrong or broken work. The JUnit report test only looks for two words in the output, and the test for leaving request bodies out of unexpected-properties scenarios can never fail. The fixed version makes both tests check real output; correct work scores the same.

In detail ([review](../../evidence/reviews/schemathesis_reporting_observability.md)):

1. `test_junitxml_writer_context_manager` searches for two substrings, so plain text, malformed XML, or XML that drops the `<error>` all pass. This is 1/70 of the total.
2. `test_body_unexpected_parameters_control_deny`, and the matching query test, filter on the wrong `GeneratedValue` class (`specs.openapi.negative` instead of `generation.coverage`). Their check therefore can never fail, and it passes on the untouched starter that lacks the required BODY fix. This is 1/100 of the total.

## What changes

Three grader files, taken byte for byte from the earlier accepted patches `proposedrepairs/reporting-junit/` and `proposedrepairs/reporting-coverage-filter/`. This is the same combined grader as `evidence/selected/reporting-integrated-acceptance.json`, except that the JUnit test in `test_02_reporting.py` was revised on 2026-10-12 (below).

- `/tests/test_02_reporting.py`: parses the XML and requires a `testsuite` or `testsuites` root and, on a test case named `test_label` (the label passed to `record_error`), an `<error>` carrying the message as text or in an attribute. Test names and count are unchanged. These are the points `TODO.md` states (a JUnit XML report; `record_error` "records a test error").
  *Revision (2026-10-12).* The first published fixed version also required a suite named exactly `schemathesis`, exactly one test case, exactly one `<error>` and no `<failure>` or `<skipped>`. `TODO.md` states none of these, so they were dropped (`paired/results.md`, revision section).
- `/tests/test_05_email_coverage.py`: uses the correct class, requires a nonempty stream of values of the correct type, and adds allow and deny cases for both body and query.
- `/tests/test.sh`: the Phase 5 test count goes from 10 to 12. Weights are unchanged.

`task.json.in` changes only `judge.image_tag` (`21a26db29432` → `junit-coverage-v2.1`). Tag `junit-coverage-v2` (v1.0 package) is superseded; rebuild.

**Left out on purpose:** `proposedrepairs/reporting-shared-hooks/` patches `src/schemathesis/pytest/plugin.py` of a candidate *implementation*. It is not a grader file, so it is not part of the fixed version. It appears only as an input to the side-by-side run (inside `fullref`).

**Score compatibility:** scores under the fixed version are not comparable with the original when Phase 2 or Phase 5 is only partly passed. Phase 5 has 12 tests instead of 10. The untouched starter rises from 0.020 to 0.025 because the new allow/deny cases check generator behaviour it already has. Fully correct submissions score 1.0 in both versions. The largest possible change is 4.76 points down (fails the fixed JUnit test and all four new coverage tests) and 2.76 points up (4.76 only if a submission removes `GeneratedValue` from `schemathesis.specs.openapi.negative`). The up bound includes 1.43 points for a correct JUnit writer whose output never contains the string `schemathesis`: the original test fails it, the revised fixed test passes it. See `paired/results.md`.

## How it was checked

A side-by-side run of the original and fixed graders on the same submissions is in [paired/results.md](paired/results.md). The complete accepted implementation stays at 1.0. Three plausibly wrong versions of it, each changed in one line, keep 1.0 under the original grader and lose points under the fixed grader:

| Changed version | Score change under the fixed grader |
|---|---|
| dropped JUnit error | −1/70 |
| missing BODY fix | −1/120 |
| always leaves bodies out (over-suppression) | −1/60 |

The revised JUnit test was checked the same way, three times on fresh workers with identical results, against the original grader and the first fixed version. A correct writer whose suite is named `api-report` instead of `schemathesis` (both as a change to the complete implementation and as a stub) now passes the JUnit test; the original and the first fixed version both fail it (−1/70). Writers that drop the `<error>` or write malformed XML still fail. Every other test outcome is unchanged.

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t ebv/schemathesis_reporting_observability-judge:v2 .
```

`materialize.sh` takes the following steps:

1. Pull the pinned image(s) by digest, unless already present.
2. Extract the original files with `docker create` and `docker cp`. No container runs in this step.
3. Check each original against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of every file under `files/` (and `orig/`) against `source-lock.json` → `materialize.outputs`. Any mismatch fails loudly.

After that, the `Dockerfile` builds without changes. Regenerated files keep the file mode they have in the image.
See `../MATERIALIZE-CHECK.md` for how each package was verified.

## Limits

- The inherited Phase 4 count quirk (9 expected, 11 collected) is unchanged.
- Only one complete implementation was tried, and every correct JUnit writer tried is built on `junit_xml` (with the suite named `schemathesis` or `api-report`). The revised JUnit test still assumes the JUnit convention that a test error is an `<error>` element inside a `<testcase>` whose `name` is the label; a writer that recorded the error as `<failure>`, or put the label only in `classname`, would fail it. `TODO.md` does not spell out either detail.
- The original task and images are untouched.
