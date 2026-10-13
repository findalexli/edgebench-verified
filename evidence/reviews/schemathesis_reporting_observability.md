# Review: schemathesis_reporting_observability

> **Note (2026-10-12).** "Correct solutions are never penalized" holds for the implementations tested
> (one complete implementation and two `junit_xml`-based writers). The fixed JUnit test also
> requires a suite named exactly `schemathesis`, exactly one test case and no `<failure>` or
> `<skipped>`, and `TODO.md` does not name the suite. The 2.4% is the original's wrong credit; the
> fixed version can move one submission's score by up to 4.76 points down or 1.33 up (superseded: see the later note below). See
> `cases/schemathesis_reporting_observability.md`.
>
> **Note (2026-10-12, later).** The fixed JUnit test was revised: it no longer requires the suite
> name, a single test case, or the absence of `<failure>`/`<skipped>`. The original test also fails
> a correct writer whose suite has another name. The rise bound is now 2.76 points for good-faith work; a rise reaches 4.76 only if a submission makes `GeneratedValue` unimportable.

## Claim under review

> "The JUnit check accepts malformed output, and the coverage filter can miss forced wrong generation behavior."

Earlier disposition: **Withhold original** (`TASKS.md` row 50, "Original checker gaps support withholding [49]"). Proposed repairs:

- `proposedrepairs/reporting-junit/`: the JUnit test parses the XML.
- `proposedrepairs/reporting-coverage-filter/`: uses the correct `GeneratedValue` class, requires non-empty output, and adds allow/deny parametrization (Phase 5: 10→12 tests).

## Pinned artifacts

- Judge image: `seededge/edgebench.judge.schemathesis_reporting_observability@sha256:b1e16633e75b2a21ef805961bb190c0a71afb75225986997340185eb7d67fc54`. I pulled it and ran it locally. `/app` is the unmodified schemathesis 4.13.0 starter.
- Original test files, read from the image:

| File | sha256 |
|---|---|
| `test_02_reporting.py` | `8dc05817c504528f39792abfef1b3924f3d012a34db7f15fac4cbeb100c2e76c` (matches the junit manifest) |
| `test_05_email_coverage.py` | `8f1831e4597df47ed6e68fecceead5bdbbfb309e0c32018988519c1636632839` |
| `test.sh` | `c74c6c42a1c63799f6bf16496c1288aa135f00c51426123500f97aab210dc428` |

- Patched files: test_02 `9dd6184a…` (matches the junit manifest), test_05 `10401e44…`, test.sh `5f3a136b…`.
- `TODO.md`, from the cloud-export work tree, sha256 `097166d37caa29316e03f9589c3d3cf941f8c6b313c7e355c7945c9c2d85467a`.

## Contract

`TODO.md` Target 2, requirement 4 (line 61):

> "**`JunitXmlWriter`**: A context-manager class that writes JUnit XML reports. Methods: `open`, `write` …, `record_error` (records a test error)."

`TODO.md` Target 5, fix 2 (line 109):

> "The `allow-extra-parameters = false` configuration suppresses unexpected-properties coverage scenarios for query, header, and cookie parameters, but not for request bodies. Bodies should be included in this suppression."

Requirement 2 (line 115) repeats it: "include body parameters alongside the existing query, header, and cookie locations."

Scoring: `weights = [2, 2, 3, 2, 1]`.

| Test | Phase | Phase size | Share of total |
|---|---|---|---|
| JunitXmlWriter test | 2 | 14 tests | 1/70 ≈ 1.4% |
| Body coverage test | 5 | 10 tests | 1/100 = 1.0% |

## Independent reproduction

Scripts are in `evidence/scripts/schemathesis_reporting_observability/`.

### A. JUnit check (`run_junit_in_judge.sh`, output in `observed_junit.txt`)

`reporting_overlay/__init__.py` is a minimal `schemathesis.reporting` package that I wrote. The VCR, HAR and NDJSON classes are only import stubs. `JunitXmlWriter` has four variants:

- `correct`: uses the `junit_xml` library that the starter's own CLI handler already uses.
- `drops_error`: plausibly wrong. Well-formed XML that lists the testcase but never writes the `<error>`, so CI would show the failed operation as passing.
- `unterminated`: plausibly wrong. Malformed XML with the root elements never closed.
- `plaintext`: a control that is not XML at all.

```
correct      orig: 1 passed   repaired: 1 passed
drops_error  orig: 1 passed   repaired: 1 failed
unterminated orig: 1 passed   repaired: 1 failed
plaintext    orig: 1 passed   repaired: 1 failed
```

The original assertion is only `"schemathesis" in content and "test_label" in content`.

### B. Coverage body-suppression check (`run_coverage_in_judge.sh` and `run_coverage_variants.sh`, outputs in `observed_coverage*.txt`)

First, the diagnostic on the **unmodified starter**, which does *not* implement the body fix. With `BODY, allow=False`, `cover_schema_iter` yields 12 values. All 12 are instances of `schemathesis.generation.coverage.GeneratedValue`, none are instances of `schemathesis.specs.openapi.negative.GeneratedValue`, and `OBJECT_UNEXPECTED_PROPERTIES` **is present**.

The original test filters on `isinstance(value, negative.GeneratedValue)`, which is the wrong class. The scenario set is therefore always empty and the assertion is vacuous.

The original and repaired tests were then run against three implementations. "Deny" means the original test or the `[False]` case; "allow" means the `[True]` case.

| Implementation | Original body / query deny tests | Repaired body: deny / allow | Repaired query: deny / allow |
|---|---|---|---|
| `starter` (no fix) | PASS / PASS | **FAIL** / PASS | PASS / PASS |
| `correct_fix` (adds BODY) | PASS / PASS | PASS / PASS | PASS / PASS |
| `always_suppress` (ignores the flag) | PASS / PASS | PASS / **FAIL** | PASS / **FAIL** |

## Refutation attempts

- **Is the JUnit trigger plausible?** Dropping the `<error>` element and forgetting to close the document are ordinary bugs, and both defeat the purpose of a JUnit report. The plain-text control shows the check does not require XML at all. The correct `junit_xml`-based writer passes both the original and the repaired test, so the repair does not over-constrain.
- **Is the coverage trigger "forced"?** The earlier wording ("can miss forced wrong generation behavior") **understates** the defect. No forcing is needed. The body test passes on the *untouched starter*, which is exactly the "before" state the test header claims it catches ("Fails on v4.13.0: AssertionError — … body not in allow-extra-parameters check"). That header statement is false for these bytes. Because the type filter always rejects every value, the test cannot fail for any implementation built on the real coverage generator. It awards free credit to a do-nothing submission.
- **Does any wrong implementation gain *over* a correct one?** No. All implementations get the same credit on these items. The harm is credit for unimplemented or incorrect behavior: about 1% for the vacuous coverage item and about 1.4% for JUnit. Correct solutions are never penalized.
- **The query test** is also vacuous but guards pre-existing behavior. It carries no distortion beyond being uninformative.

## Formal check

None. The issue is a deterministic class-identity and string-assertion one, and direct execution settles it.

## Verdict

**CONFIRMED, and the coverage part is stronger than stated.**

- The JUnit test accepts malformed, non-XML and error-less output.
- The body-suppression test is vacuous, because it filters on the wrong `GeneratedValue` class. It passes on the unmodified starter, which lacks the required fix, and also on an over-suppressing implementation.

## Disposition assessment

"Repair (versioned)" is the right outcome, and both proposed patches are justified. Whether to *withhold the original* is a policy question. Together the two items mis-credit at most about 2.4% of the task score and never penalize correct work. Of the two, the vacuous coverage test is the stronger reason to prefer not shipping the original unchanged, because it gives the starter credit for an unimplemented requirement.

I would report this task as **repaired (new version)**, not as a task lost to exclusion, provided the repaired judge is executed end to end. Earlier records report a 55/53 test-count quirk and broader integration controls. Those are outside this claim and were not re-checked here.

## Recommended publishable wording

> "Two hidden tests in schemathesis_reporting_observability under-measure their requirements. The JUnit writer test only searches for two substrings, so malformed or error-less XML passes. The body-suppression coverage test filters on the wrong `GeneratedValue` class, which makes it pass even for the unmodified starter that lacks the fix. A versioned task parses the XML and checks the coverage stream with allow/deny controls; together the gaps affect about 2.4% of the task score."

## Repair note

- **JUnit patch.** It is correct and reasonably minimal. It parses with ElementTree, accepts both `testsuite` and `testsuites` roots, and requires one `testcase` named `test_label` with an `<error>` carrying the message, either as text or as the `message` attribute. It passed the `junit_xml` library output and rejected all three wrong variants. The test count is unchanged.
- **Coverage patch.** It is correct. It imports `GeneratedValue` from `schemathesis.generation.coverage`, asserts the stream is non-empty and correctly typed, and adds allow=True controls that catch over-suppression. A smaller fix would be to change only the import, which alone restores the deny check against the starter. The allow-controls are a reasonable addition but increase Phase 5 from 10 to 12 tests, so partial scores are not comparable with the original.

## Limits

- The reporting overlay is a stub except for `JunitXmlWriter`, so only the two named test functions were executed, not the full patched `test.sh`.
- The integration claims in `TASKS.md` (xdist, stateful, 55/53 counts) were not reviewed.
- `TODO.md` was taken from the cloud export.

## Rerun

Run `scripts/<task>/fetch_tests.sh` first. It extracts the hidden tests from the pinned judge image into `tests_orig/` and applies the proposed patch into `tests_repaired/`, printing the hashes above. The hidden tests themselves are not stored in this repository. Then run the `run_*.sh` scripts as shown, with `-v <scripts dir>:/ebv:ro`.
