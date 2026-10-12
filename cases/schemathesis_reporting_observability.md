# Schemathesis reporting and observability (`schemathesis_reporting_observability`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Systems & Software Engineering
- **Decision:** Repair v2. The JUnit writer test accepts malformed output, and the body-suppression coverage test is vacuous. Together the two gaps mis-credit about 2.4% of the score.

## What the task promises

The solver is told to "Treat `/app/TODO.md` as the authoritative task specification." `TODO.md` asks for two things relevant here:

- Target 2: a "**`JunitXmlWriter`**: A context-manager class that writes JUnit XML reports", with a `record_error` method that "records a test error".
- Target 5, fix 2: "The `allow-extra-parameters = false` configuration suppresses unexpected-properties coverage scenarios for query, header, and cookie parameters, but not for request bodies. Bodies should be included in this suppression."

## What we checked and how

- **Pinned judge image.** We pulled the judge image and ran it locally. `/app` is the unmodified schemathesis 4.13.0 starter.
- **JUnit check.** A minimal reviewer-written `schemathesis.reporting` package supplied four `JunitXmlWriter` variants:
  - `correct`, built on the `junit_xml` library that the starter's CLI already uses;
  - `drops_error`, which writes well-formed XML but no `<error>`;
  - `unterminated`, which writes malformed XML;
  - `plaintext`, which writes no XML at all.

  Each variant ran against the original and the repaired JUnit test in the judge image.
- **Coverage check.** We inspected what `cover_schema_iter` yields on the unmodified starter. We then ran the original and repaired coverage tests against three implementations: the starter (no fix), a correct fix, and an over-suppressing fix that ignores the flag.
- **Paired v1/v2 run.** One E2B worker ran every variant through the full original `judge.eval_cmd` in fresh `--network none` containers. Variants included a complete reference implementation used as a positive control, three single-line mutants of it, the reviewer's stub, and the untouched starter.
- **Original identity.** Judge image `seededge/edgebench.judge.schemathesis_reporting_observability@sha256:b1e16633…`. Key files:

  | File | sha256 |
  | --- | --- |
  | `test_02_reporting.py` | `8dc05817…` |
  | `test_05_email_coverage.py` | `8f1831e4…` |
  | `test.sh` | `c74c6c42…` |
  | `TODO.md` (from the earlier cloud export) | `097166d3…` |

## What we found

**JUnit check: Confirmed.** The original assertion only checks that the strings `"schemathesis"` and `"test_label"` appear somewhere in the output. Expected: a malformed report, or a report missing the error, should fail. Observed with the original test:

```
correct      orig: 1 passed   repaired: 1 passed
drops_error  orig: 1 passed   repaired: 1 failed
unterminated orig: 1 passed   repaired: 1 failed
plaintext    orig: 1 passed   repaired: 1 failed
```

A writer that drops the `<error>` makes a failed operation look like a pass in CI, and it still earns the item.

**Maximum score effect:** 1/70 of the total (about 1.4%).

**Body-coverage check: Confirmed, broader than the earlier claim.** The earlier wording said the filter "can miss forced wrong generation behavior". No forcing is needed. On the untouched starter, which lacks the body fix, `cover_schema_iter` yields 12 values with body suppression requested, and the unwanted `OBJECT_UNEXPECTED_PROPERTIES` scenario is present. All 12 values belong to the coverage module's `GeneratedValue` class. The test filters on a different class of the same name, so its scenario set is always empty and the assertion can never fail. Expected: the test should fail on the starter, as its own header comment claims. Observed: it passes on the starter, and it also passes on an over-suppressing implementation. The query-parameter sibling test is vacuous in the same way, but it only guards behaviour that already existed.

**Maximum score effect:** 1/100 of the total (1.0%).

No wrong implementation scores above a correct one, and correct work is never penalized. The harm is credit for missing or incorrect behaviour.

## Repair

v2 changes three judge files. The files are taken byte-for-byte from the two earlier accepted patches.

- `/tests/test_02_reporting.py` parses the XML. It accepts either a `testsuite` or a `testsuites` root, and it requires one `test_label` testcase with an `<error>` carrying the message. Test names and test count are unchanged.
- `/tests/test_05_email_coverage.py` uses the correct `GeneratedValue` class and requires a non-empty, correctly typed stream. It also parametrizes allow/deny cases for both body and query.
- `/tests/test.sh` raises the Phase 5 count from 10 to 12. Weights are unchanged.

In `task.json.in`, only `judge.image_tag` changes. A separate earlier patch to a candidate implementation's plugin file is not a judge file and is not part of v2.

In the table below, the `fullref` rows are the complete reference implementation used as a positive control. The `fullref_*` rows are single-line mutations of it, and the `stub_*` rows use the reviewer's minimal stub.

| Variant | Role | v1 score | v2 score | Delta | Phase 2 / Phase 5 (v1 → v2) |
|---|---|---|---|---|---|
| fullref | correct complete implementation | 1.000000 | 1.000000 | **0** | 14/14 → 14/14 ; 10/10 → 12/12 |
| fullref_junit_drops_error | plausibly wrong: `record_error` creates the testcase but drops `<error>` | 1.000000 | 0.985714 | **−0.014286 (−1/70)** | 14/14 → 13/14 |
| fullref_no_body_fix | plausibly wrong: Target 5 fix 2 omitted (BODY not suppressed) | 1.000000 | 0.991667 | **−0.008333** | 10/10 → 11/12 |
| fullref_always_suppress | plausibly wrong: suppression ignores `allow_extra_parameters` | 1.000000 | 0.983333 | **−0.016667** | 10/10 → 10/12 |
| stub_junit_correct | reviewer stub, `junit_xml`-based writer | 0.091429 | 0.096429 | +0.005000 | 5/14 → 5/14 ; 2/10 → 3/12 |
| stub_junit_drops_error | reviewer stub, error dropped | 0.091429 | 0.082143 | −0.009286 | 5/14 → 4/14 ; 2/10 → 3/12 |
| starter | untouched starter | 0.020000 | 0.025000 | +0.005000 | 0/14 → 0/14 ; 2/10 → 3/12 |

Phases 1, 3 and 4 give identical results in every variant. The only changed items are the JUnit test and the two former deny-only coverage tests, which are replaced by four parametrized allow/deny tests, plus the Phase 2 and Phase 5 summary items (`test_phase_2`, `test_phase_5`) of the mutants that now fail those phases. All three plausibly wrong mutants score 1.0 under v1 but lose points under v2. The positive control stays at 1.0.

**Score compatibility.** Fully correct submissions score 1.0 in both versions. When Phase 2 or Phase 5 is only partly passed, v1 and v2 scores are not comparable, because Phase 5 has 12 tests instead of 10. Under v2 the untouched starter and the stub variants gain +0.005. The new allow cases and the query deny case check generator behaviour the starter already has, so starter credit in Phase 5 moves from the vacuous body test to legitimate checks. A smaller alternative would change only the `GeneratedValue` import and keep 10 tests, but it would not catch over-suppression.

## Limits and what was not run

- No model or solver re-runs were made. Effects are shown only on authored variants, mutants and counterexamples.
- Only one complete implementation was available as a positive control.
- An inherited count quirk in Phase 4 (9 expected, 11 collected) is unchanged and out of scope.
- The broader integration claims in earlier records (xdist, stateful runs, a 55/53 test-count quirk) were not re-checked.
- `TODO.md` came from the earlier cloud export and was not re-extracted from the work image.
- The hidden tests are not stored in this repository. They are extracted from the pinned judge image when the checks are rerun.

## Reproduce

- **Original vs repaired tests.** First run `evidence/scripts/schemathesis_reporting_observability/fetch_tests.sh`. Then run `run_junit_in_judge.sh` (with `reporting_overlay/`), `run_coverage_in_judge.sh` and `run_coverage_variants.sh`. Saved outputs are in `observed_junit.txt`, `observed_coverage.txt` and `observed_coverage_variants.txt`.
- **Paired v1/v2 run.** `repairs/schemathesis_reporting_observability-v2/paired/run.sh`. Results are in `paired/results.md` and `paired/raw-summary.md`.
- **Repair.** `repairs/schemathesis_reporting_observability-v2/repair.patch`, `Dockerfile` and `source-lock.json`.

Supporting records: `repairs/schemathesis_reporting_observability-v2/` and `evidence/reviews/schemathesis_reporting_observability.md`.
