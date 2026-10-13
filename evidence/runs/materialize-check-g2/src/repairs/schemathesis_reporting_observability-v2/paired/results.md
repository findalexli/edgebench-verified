# Paired v1/v2 results: schemathesis_reporting_observability

The E2B job `evidence/runs/schemathesis_reporting_observability-v2-paired` ran on worker `igvolh7xz26uawbe3d29c` for 182 s, finished with exit 0 and was killed. It ran every variant through the full original `judge.eval_cmd` in fresh `--network none` containers:
- v1 is the pinned original `@sha256:b1e16633…`.
- v2 was built in the worker from `../Dockerfile`. It was the first fixed version (`test_02_reporting.py` `9dd6184a…`), superseded on 2026-10-12; see the revision section below.

Normalized score = raw score (linear 0..1).

`fullref` is the earlier accepted complete reporting implementation: the 30-file overlay `work/packets/reporting-full-reference-astra-high-v2/overlay` plus the shared-hook `plugin.py`, sha256 `2affff28…`. It is an input to this run, not part of the repair. The `fullref_*` variants are single-line mutations of it. `stub_*` is the reviewer's minimal `schemathesis.reporting` stub.

| Variant | Role | v1 score | v2 score | Delta | Tests passed, P2 = Phase 2, P5 = Phase 5 (v1 → v2) |
|---|---|---|---|---|---|
| fullref | correct complete implementation | 1.000000 | 1.000000 | **0** | P2 14/14 → 14/14; P5 10/10 → 12/12 |
| fullref_junit_drops_error | plausibly wrong: `record_error` creates the testcase but drops `<error>` | 1.000000 | 0.985714 | **−0.014286 (−1/70)** | P2 14/14 → 13/14 |
| fullref_no_body_fix | plausibly wrong: Target 5 fix 2 omitted (BODY not suppressed) | 1.000000 | 0.991667 | **−0.008333** | P5 10/10 → 11/12 |
| fullref_always_suppress | plausibly wrong: suppression ignores `allow_extra_parameters` | 1.000000 | 0.983333 | **−0.016667** | P5 10/10 → 10/12 |
| stub_junit_correct | reviewer stub, `junit_xml`-based writer | 0.091429 | 0.096429 | +0.005000 | P2 5/14 → 5/14; P5 2/10 → 3/12 |
| stub_junit_drops_error | reviewer stub, error dropped | 0.091429 | 0.082143 | −0.009286 | P2 5/14 → 4/14; P5 2/10 → 3/12 |
| starter | untouched starter | 0.020000 | 0.025000 | +0.005000 | P2 0/14 → 0/14; P5 2/10 → 3/12 |

Per-test differences: `raw-summary.md`. Phases 1, 3 and 4 are identical in every variant. The only changed items are:
- `test_junitxml_writer_context_manager`
- the two former `*_deny` coverage tests, replaced by four parametrized `[False]`/`[True]` tests

- **Trigger:** all three plausibly-wrong mutants of a v1-perfect implementation keep 1.0 under v1 and lose points under v2. Holds.
- **Valid control:** fullref stays at 1.0, with 57 printed items and 55 script-reported. This matches the earlier integrated acceptance in `evidence/selected/reporting-integrated-acceptance.json`. Holds. The correct stub JUnit writer passes the JUnit test in both versions.
- **Invalid controls:** the starter's missing body fix is now caught (`body[False]` fails). Holds.
- **Score-compatibility caveat:** the untouched starter and the stub variants gain +0.005 under v2. Phase 5 goes from 2/10 to 3/12 because the new `[True]` cases and the query `[False]` case check pre-existing generator behavior that the starter already has. The one correct implementation tested is not penalized. Still, v2 does not remove all starter credit in phase 5; it moves it from the vacuous body-deny test to legitimate pre-existing-behavior checks. A smaller alternative changes only the `GeneratedValue` import (phase 5 stays at 10 tests; the starter would drop to 1/10), but it would not catch `always_suppress`.

The inherited phase-4 count quirk (`PHASE4_EXPECTED=9`, 11 collected) is unchanged and out of scope.

Note: `paired/run.sh` differs from the executed job script only in the `/tests` hash-listing fix. v2 hashes were verified on a local build: `v2-image-tests.sha256`.

**Largest possible change** (from the weights 2, 2, 3, 2, 1 in `test.sh`): down by 1/70 + 1/30 = 0.047619, for a submission that passes everything under v1 but fails the v2 JUnit test and all four new coverage tests; up by at most 4/12·0.1 − 2/10·0.1 = 0.013333 while the two original coverage tests pass, or 0.033333 if a submission makes `schemathesis.specs.openapi.negative.GeneratedValue` unimportable. The v2 JUnit test cannot pass where the v1 test fails. (These bounds are for the first fixed version; the revision section below gives the revised up bound.)

## Revision (2026-10-12): the JUnit test asks only for what `TODO.md` states

**Why.** `TODO.md` Target 2 (line 61) asks for "A context-manager class that writes JUnit XML
reports" whose `record_error` "records a test error". The first published fixed test
(`test_02_reporting.py` `9dd6184a…`) also required a suite named exactly `schemathesis`, exactly
one test case in the report, exactly one `<error>`, and no `<failure>` or `<skipped>`. `TODO.md`
states none of these, so a correct writer could lose 1/70 for an unstated detail.

**Change.** `test_junitxml_writer_context_manager` now requires: the output parses as XML; the root
is `testsuite` or `testsuites`; some `<testcase>` named `test_label` (the label passed to
`record_error`) holds at least one `<error>`; and one such `<error>` carries the message, in its text
or in an attribute value. The suite name, the number of test cases and errors, and the absence of
`<failure>`/`<skipped>` are no longer checked. The test name and the test count are unchanged;
`test.sh` and `test_05_email_coverage.py` are unchanged. Revised file: `8615de49…` (5,619 B).
`repair.patch`, `materialize.sh` and `source-lock.json` were regenerated with
`tools/make_materialize.py`, and a clean-copy `./materialize.sh` reproduced the three files byte for
byte. The superseded file is kept outside Git.

**Jobs.** `evidence/runs/schemathesis_reporting_observability-v2-paired-rev2`, `-rev2-rep2` and
`-rev2-rep3`: three fresh E2B workers (`is3jwyc5c19u7t3s6cddl`, `i2c6pyx6p3uoput5r0x6z`,
`iakajnorekfc1nwu32o9s`), each `status: exit=0` in 282–302 s and killed. Each ran every submission
through the original `judge.eval_cmd` under three graders: v1 the original (`/tests/test_02_reporting.py`
`8dc05817…`), v2prev the first fixed version (`9dd6184a…`) and v2 the revised one (`8615de49…`); the
in-image hashes are in each job's `result/out/tests-*.sha256`. New submissions:
- `fullref_junit_other_suite`: `fullref` with the JUnit suite named `api-report` instead of `schemathesis` (correct);
- `stub_junit_other_suite`: the `junit_xml`-based stub writer with the suite named `api-report` (correct);
- `stub_junit_unterminated`: the stub writer with unclosed root elements (malformed XML, wrong).

| Variant | Role | v1 | v2prev | v2 (revised) | P2 (v1 / v2prev / v2) |
|---|---|---|---|---|---|
| fullref | correct complete implementation | 1.000000 | 1.000000 | 1.000000 | 14 / 14 / 14 |
| **fullref_junit_other_suite** | correct, suite named `api-report` | **0.985714** | **0.985714** | **1.000000** | 13 / 13 / 14 |
| fullref_junit_drops_error | wrong: `<error>` dropped | 1.000000 | 0.985714 | 0.985714 | 14 / 13 / 13 |
| fullref_no_body_fix | wrong: BODY not suppressed | 1.000000 | 0.991667 | 0.991667 | 14 / 14 / 14 |
| fullref_always_suppress | wrong: flag ignored | 1.000000 | 0.983333 | 0.983333 | 14 / 14 / 14 |
| stub_junit_correct | stub, correct writer | 0.091429 | 0.096429 | 0.096429 | 5 / 5 / 5 |
| **stub_junit_other_suite** | stub, correct writer, suite `api-report` | **0.077143** | **0.082143** | **0.096429** | 4 / 4 / 5 |
| stub_junit_drops_error | stub, `<error>` dropped | 0.091429 | 0.082143 | 0.082143 | 5 / 4 / 4 |
| stub_junit_unterminated | stub, malformed XML | 0.091429 | 0.082143 | 0.082143 | 5 / 4 / 4 |
| starter | untouched starter | 0.020000 | 0.025000 | 0.025000 | 0 / 0 / 0 |

All three runs gave these scores and the same per-test outcomes (`result/out/summary.md` in each job).

**Spec checks.**

- **Correct writer with another suite name passes.** Both `*_other_suite` submissions fail the JUnit
  test under v1 and v2prev and pass it under v2. The original test fails them too: their output does
  not contain the string `schemathesis`. So the original grader also took 1/70 from a correct writer
  that names its suite differently; the revised fixed version does not.
- **Wrong writers still fail.** `drops_error` (both forms) and `unterminated` pass under v1 and fail
  under v2prev and v2.
- **Everything else is unchanged.** For every other submission and every other test, v2 gives the same
  outcome as v2prev; `fullref` stays at 1.0.

**Largest possible change, revised.** The down bound is unchanged: 1/70 + 1/30 = 0.047619. The up
bound grows by the JUnit test, which can now pass where the original fails (a correct writer whose
output never contains `schemathesis`): 1/70 + 0.013333 = 0.027619, or 1/70 + 0.033333 = 0.047619 if a
submission also makes `schemathesis.specs.openapi.negative.GeneratedValue` unimportable. The sentence
above, "The v2 JUnit test cannot pass where the v1 test fails", held for the first fixed version only.

**Verdict:** **accepted** (revised `test_02_reporting.py` `8615de49…`).

## Repeatability (2026-10-13)

| job | arms | runs | identical? |
| --- | --- | --- | --- |
| `…-v2-paired`, `-rep2`, `-rep3` | the seven arms of the first paired table | 3 | yes |
| `evidence/runs/schemathesis_reporting_observability-v2-paired-rev2`, `-rev2-rep2`, `-rev2-rep3` | all ten arms of the revision, both graders (20 results) | 3 | yes |

Every run has `status: exit=0`. Every arm gives the same per-phase pass counts and the same score in all three runs (`result/out/summary.json`).
