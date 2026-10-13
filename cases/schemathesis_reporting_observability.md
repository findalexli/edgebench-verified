# Schemathesis reporting and observability (`schemathesis_reporting_observability`)

**Outcome:** Fixed. <mark>The hidden test for the JUnit report writer accepts broken output, and the test for leaving request bodies out of certain generated scenarios can never fail; together the two gaps give wrong credit for about 2.4% of the score.</mark>

![Two panels: the original JUnit test and the original body-suppression test both pass broken work, while the fixed tests fail it.](figures/schemathesis_reporting_observability.svg)

*Two hidden tests gave credit to broken work, about 2.4% of the score together; the fixed tests fail the broken versions.*

## What the task asks

Schemathesis is a tool that automatically tests web APIs. The solver extends reporting and observability in schemathesis 4.13.0 and is told to "Treat `/app/TODO.md` as the authoritative task specification." The grader scores the work with hidden tests. Two targets matter here:

- Target 2: a "**`JunitXmlWriter`**: A context-manager class that writes JUnit XML reports", with a `record_error` method that "records a test error". JUnit XML is a common test-report format read by CI (continuous integration) systems.
- Target 5, fix 2: "The `allow-extra-parameters = false` configuration suppresses unexpected-properties coverage scenarios for query, header, and cookie parameters, but not for request bodies. Bodies should be included in this suppression."

Category: Systems & Software Engineering.

## What goes wrong

### 1. The JUnit test accepts broken or incomplete reports

**Rule.** `record_error` must record an error in a JUnit XML report. The original test only checks that the strings `"schemathesis"` and `"test_label"` appear somewhere in the output.

**Example.** Four test writers: `correct` (built on the `junit_xml` library that the starter's command-line tool already uses), `drops_error` (well-formed XML, no `<error>`), `unterminated` (malformed XML) and `plaintext` (no XML at all). Expected: only `correct` passes. Observed, with the original test ("orig") and the fixed test ("repaired"):

```
correct      orig: 1 passed   repaired: 1 passed
drops_error  orig: 1 passed   repaired: 1 failed
unterminated orig: 1 passed   repaired: 1 failed
plaintext    orig: 1 passed   repaired: 1 failed
```

**Why it matters.** A writer that drops the `<error>` makes a failed operation look like a pass in CI, and it still earns the test's credit. In the other direction, a correct writer that names its suite something other than `schemathesis` fails the original test, because the string `schemathesis` then appears nowhere in its output (shown on E2B in the revision runs below); `TODO.md` does not name the suite.

### 2. The test for leaving bodies out can never fail

**Rule.** With `allow-extra-parameters = false`, request bodies must not produce unexpected-properties scenarios (generated test inputs with extra, undeclared fields).

**Example.** On the untouched starter, which lacks the body fix, `cover_schema_iter` produces 12 values when body suppression is requested, and the unwanted `OBJECT_UNEXPECTED_PROPERTIES` scenario is present. All 12 values belong to the coverage module's `GeneratedValue` class. The test filters on a different class of the same name, so its set of scenarios is always empty and its check can never fail. Expected: the test fails on the starter, as its own header comment says. Observed: it passes on the starter. It also passes on an implementation that ignores the flag and always leaves bodies out.

**Why it matters.** The test gives credit for missing or incorrect behaviour. The matching test for query parameters can never fail either, but it only guards behaviour the starter already has.

## How much it matters

The score is Σ wᵢ·passedᵢ/totalᵢ / 10 over five phases with weights 2, 2, 3, 2, 1 (`/tests/test.sh`). One Phase 2 test is worth 2/(14·10) = 1/70 of the total; one Phase 5 test is worth 1/100 in the original and 1/120 in the fixed version.

- Wrong credit in the original: the JUnit test gives at most 1/70 (about 1.4 points out of 100), and the body test at most 1/100 (1.0 point).
- Wrong deduction in the original: the JUnit test takes 1/70 (about 1.4 points) from a correct writer whose output does not contain the string `schemathesis`.
- Largest drop under the fixed version: 4.76 points. A submission that passes everything under the original but fails the fixed JUnit test and all four new coverage tests loses 1/70 in Phase 2 and 10·(1 − 8/12)/100 = 1/30 in Phase 5, together 1/70 + 1/30 = 4.76 points. The tested changed versions lose 1.43, 0.83 and 1.67 points.
- Largest rise under the fixed version: 2.76 points. The revised JUnit test can pass where the original fails: a correct writer whose output never contains the string `schemathesis` (for example, a suite with another name) fails the original test and passes the revised one, 1/70 or 1.43 points. In Phase 5 the two original coverage tests pass on any submission whose coverage generator runs, so with no other Phase 5 test passed the share moves from 2/10 to at most 4/12, which is 1.33 points; together 2.76 points. The starter and the stubs gain 0.5 points. The rise could reach 4.76 points only if a submission removed the `GeneratedValue` class from `schemathesis.specs.openapi.negative`, which the original coverage tests import.
- No wrong implementation tested scores above a correct one, and the one correct implementation tested keeps 1.0.

## The fix

The fixed version changes three grader files:

- `/tests/test_02_reporting.py` parses the XML. It accepts either a `testsuite` or a `testsuites` root and requires a test case named `test_label` (the label passed to `record_error`) holding an `<error>` that carries the message, as text or in an attribute. These are the points `TODO.md` states: a JUnit XML report, and `record_error` "records a test error". Test names and the number of tests are unchanged.
- `/tests/test_05_email_coverage.py` uses the correct `GeneratedValue` class and requires a non-empty stream of values of the correct type. It also adds cases where extra parameters are allowed and where they are denied, for both body and query.
- `/tests/test.sh` raises the Phase 5 test count from 10 to 12. Weights are unchanged.

In `task.json.in`, only `judge.image_tag` changes.

In the table below, `fullref` is a complete reference implementation used as a correct test submission. The `fullref_*` rows each change one line of it, and the `stub_*` rows use a minimal stub. Scores are raw results (before conversion to 0–100) on a 0–1 scale.

| Test submission | Role | Original grader | Fixed grader | Change | Tests passed, P2 = Phase 2, P5 = Phase 5 (original → fixed) |
|---|---|---|---|---|---|
| fullref | correct complete implementation | 1.000000 | 1.000000 | **0** | P2 14/14 → 14/14; P5 10/10 → 12/12 |
| fullref_junit_drops_error | plausibly wrong: `record_error` creates the test case but drops `<error>` | 1.000000 | 0.985714 | **−0.014286 (−1/70)** | P2 14/14 → 13/14 |
| fullref_no_body_fix | plausibly wrong: Target 5 fix 2 left out (BODY not suppressed) | 1.000000 | 0.991667 | **−0.008333** | P5 10/10 → 11/12 |
| fullref_always_suppress | plausibly wrong: suppression ignores `allow_extra_parameters` | 1.000000 | 0.983333 | **−0.016667** | P5 10/10 → 10/12 |
| stub_junit_correct | reviewer stub, `junit_xml`-based writer | 0.091429 | 0.096429 | +0.005000 | P2 5/14 → 5/14; P5 2/10 → 3/12 |
| stub_junit_drops_error | reviewer stub, error dropped | 0.091429 | 0.082143 | −0.009286 | P2 5/14 → 4/14; P5 2/10 → 3/12 |
| starter | untouched starter | 0.020000 | 0.025000 | +0.005000 | P2 0/14 → 0/14; P5 2/10 → 3/12 |

Phases 1, 3 and 4 give identical results for every test submission. The only items that change are:

- the JUnit test;
- the two former deny-only coverage tests, which are replaced by four allow/deny tests;
- the Phase 2 and Phase 5 summary items (`test_phase_2`, `test_phase_5`) of the changed versions that now fail those phases.

All three plausibly wrong versions score 1.0 under the original grader but lose points under the fixed grader. The correct test submission stays at 1.0.

**Revision of the fix (2026-10-12).** The first published fixed version also required the suite to be named exactly `schemathesis`, exactly one test case and one `<error>`, and no `<failure>` or `<skipped>` element. `TODO.md` states none of these; `schemathesis` is only the suite name the starter's command-line JUnit handler uses. The revised test drops them. A side-by-side run of the original grader, the first fixed version and the revised one, three times on fresh workers, gave the same results as the table above for every earlier submission. Three submissions were added:

| Test submission | Role | Original grader | First fixed version | Revised fixed version |
|---|---|---|---|---|
| fullref_junit_other_suite | correct: suite named `api-report` | 0.985714 | 0.985714 | 1.000000 |
| stub_junit_other_suite | correct stub writer, suite named `api-report` | 0.077143 | 0.082143 | 0.096429 |
| stub_junit_unterminated | wrong: malformed XML | 0.091429 | 0.082143 | 0.082143 |

The original test also fails a correct writer with another suite name, because its output does not contain the string `schemathesis`; so does the first fixed version. The revised version passes it. Writers that drop the `<error>` or write malformed XML fail under both fixed versions.

**Score compatibility.** Fully correct submissions score 1.0 in both versions. When Phase 2 or Phase 5 is only partly passed, original and fixed scores are not comparable, because Phase 5 has 12 tests instead of 10. Under the fixed version the untouched starter and the stub submissions gain +0.005. The new allow cases and the query deny case check behaviour the starter's generator already has. So the starter's Phase 5 credit moves from the body test that could never fail to checks that are real. A smaller alternative would change only the `GeneratedValue` import and keep 10 tests, but it would not catch an implementation that always leaves bodies out.

## How we checked it

- **Original grader in the original image, pinned by digest.** The grader image holds the unmodified schemathesis 4.13.0 starter. Every test submission ran through the full original `judge.eval_cmd` and through the fixed grader, in fresh `--network none` containers.
- **Direct inspection.** The class of every value produced by `cover_schema_iter` on the starter was inspected. This shows why the original coverage filter is always empty. The fixed coverage tests were run against the starter, a correct fix and a fix that always leaves bodies out.
- **Repeatability.** The side-by-side run of the original and fixed graders was run three times; no verdict changed (`data/paired-repeatability.md`). These repeats used the first fixed version. The run with the revised fixed version was also done three times (`evidence/runs/schemathesis_reporting_observability-v2-paired-rev2`, `-rev2-rep2`, `-rev2-rep3`), with identical scores and per-test outcomes.

## Limits

- No AI model or solver was run. Effects are shown only on test submissions and changed versions we wrote.
- Only one complete implementation was available as a correct test submission, and every correct JUnit writer tried is built on `junit_xml`. The revised JUnit test still assumes the usual JUnit form: the error is an `<error>` element in a `<testcase>` whose `name` is the label. A writer that recorded it as `<failure>`, or put the label only in `classname`, would fail it, and a report whose root element carries an XML namespace (`<testsuites xmlns=…>`) would also fail it (local probe; an XML declaration, a byte-order mark, CDATA or nested `testsuites` pass); `TODO.md` does not spell out these details.
- A count quirk in Phase 4 (9 expected, 11 collected) is unchanged and out of scope.
- The package was rebuilt from scratch on a clean machine (`evidence/runs/materialize-check-g2`, `status: exit=0`): all 3 outputs matched the lock and the built image holds the locked test files.
- Broader integration behaviour (xdist, stateful runs, a 55/53 test-count quirk) was not checked.
- `TODO.md` was taken from the cloud export of the work tree (sha256 `097166d3…`), not re-extracted from the work image.
- The hidden tests are not stored in this repository. They are extracted from the pinned grader image when the checks are rerun.

## Reproduce

- Original grader image: `sha256:b1e16633…`.
- **Original vs fixed tests.** First run `evidence/scripts/schemathesis_reporting_observability/fetch_tests.sh`. Then run `run_junit_in_judge.sh` (with `reporting_overlay/`), `run_coverage_in_judge.sh` and `run_coverage_variants.sh`. Saved outputs are in `observed_junit.txt`, `observed_coverage.txt` and `observed_coverage_variants.txt`.
- **Side-by-side run of the original and fixed graders.** `repairs/schemathesis_reporting_observability-v2/paired/run.sh`. Results are in `paired/results.md` and `paired/raw-summary.md`.
- **Fix.** `repairs/schemathesis_reporting_observability-v2/repair.patch`, `Dockerfile` and `source-lock.json`.

Supporting records: `repairs/schemathesis_reporting_observability-v2/` (the folder holding the fixed version) and `evidence/reviews/schemathesis_reporting_observability.md`.
