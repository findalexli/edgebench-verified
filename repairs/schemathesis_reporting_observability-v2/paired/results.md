# Paired v1/v2 results: schemathesis_reporting_observability

The E2B job `e2b/jobs/schemathesis_reporting_observability-v2-paired` ran on worker `igvolh7xz26uawbe3d29c` for 182 s, finished with exit 0 and was killed. It ran every variant through the full original `judge.eval_cmd` in fresh `--network none` containers:
- v1 is the pinned original `@sha256:b1e16633…`.
- v2 was built in the worker from `../Dockerfile`.

Normalized score = raw score (linear 0..1).

`fullref` is the earlier accepted complete reporting implementation: the 30-file overlay `work/packets/reporting-full-reference-astra-high-v2/overlay` plus the shared-hook `plugin.py`, sha256 `2affff28…`. It is an input to this run, not part of the repair. The `fullref_*` variants are single-line mutations of it. `stub_*` is the reviewer's minimal `schemathesis.reporting` stub.

| Variant | Role | v1 score | v2 score | Delta | Phase 2 / Phase 5 (v1 → v2) |
|---|---|---|---|---|---|
| fullref | correct complete implementation | 1.000000 | 1.000000 | **0** | 14/14 → 14/14 ; 10/10 → 12/12 |
| fullref_junit_drops_error | plausibly wrong: `record_error` creates the testcase but drops `<error>` | 1.000000 | 0.985714 | **−0.014286 (−1/70)** | 14/14 → 13/14 |
| fullref_no_body_fix | plausibly wrong: Target 5 fix 2 omitted (BODY not suppressed) | 1.000000 | 0.991667 | **−0.008333** | 10/10 → 11/12 |
| fullref_always_suppress | plausibly wrong: suppression ignores `allow_extra_parameters` | 1.000000 | 0.983333 | **−0.016667** | 10/10 → 10/12 |
| stub_junit_correct | reviewer stub, `junit_xml`-based writer | 0.091429 | 0.096429 | +0.005000 | 5/14 → 5/14 ; 2/10 → 3/12 |
| stub_junit_drops_error | reviewer stub, error dropped | 0.091429 | 0.082143 | −0.009286 | 5/14 → 4/14 ; 2/10 → 3/12 |
| starter | untouched starter | 0.020000 | 0.025000 | +0.005000 | 0/14 → 0/14 ; 2/10 → 3/12 |

Per-test differences: `raw-summary.md`. Phases 1, 3 and 4 are identical in every variant. The only changed items are:
- `test_junitxml_writer_context_manager`
- the two former `*_deny` coverage tests, replaced by four parametrized `[False]`/`[True]` tests

- **Trigger:** all three plausibly-wrong mutants of a v1-perfect implementation keep 1.0 under v1 and lose points under v2. Holds.
- **Valid control:** fullref stays at 1.0, with 57 printed items and 55 script-reported. This matches the earlier integrated acceptance in `evidence/selected/reporting-integrated-acceptance.json`. Holds. The correct stub JUnit writer passes the JUnit test in both versions.
- **Invalid controls:** the starter's missing body fix is now caught (`body[False]` fails). Holds.
- **Score-compatibility caveat:** the untouched starter and the stub variants gain +0.005 under v2. Phase 5 goes from 2/10 to 3/12 because the new `[True]` cases and the query `[False]` case check pre-existing generator behavior that the starter already has. No implementation is penalized for being correct. Still, v2 does not remove all starter credit in phase 5; it moves it from the vacuous body-deny test to legitimate pre-existing-behavior checks. A smaller alternative changes only the `GeneratedValue` import (phase 5 stays at 10 tests; the starter would drop to 1/10), but it would not catch `always_suppress`.

The inherited phase-4 count quirk (`PHASE4_EXPECTED=9`, 11 collected) is unchanged and out of scope.

Note: `paired/run.sh` differs from the executed job script only in the `/tests` hash-listing fix. v2 hashes were verified on a local build: `v2-image-tests.sha256`.
