# Supporting evidence

Use [findings](FINDINGS.md) for conclusions and the [task tracker](../TASKS.md) for current dispositions. This page selects useful starting points; the [evidence manifest](../evidence/selected/EVIDENCE-MANIFEST.json) lists every selected artifact, its identity and provenance. Source paths inside JSON records may refer to the local archive rather than files shipped in this repository.

## Findings and original-version decisions

- [Finding decisions at the earlier twelve-finding snapshot](../evidence/selected/12-finding-decisions.json) and [historical 51-task observations](../evidence/selected/51-task-coverage.md) retain their dates; neither is the current tracker.
- Later original exclusions: [Wireless](../evidence/selected/wireless-original-exclusion.json), [Jagua](../evidence/selected/jagua-original-exclusion.json), [Equivalence and Graph](../evidence/selected/eq-graph-original-exclusions.json), [Tree](../evidence/selected/tree-original-exclusion.json), [English](../evidence/selected/english-original-exclusion.json) and [VLIW](../evidence/selected/vliw-original-exclusion.json). Findings links the remaining exclusions and exact scope.
- Additional confirmed checker weaknesses: [Rust exception credit](../evidence/selected/rust-known-failure-outcome.json), [HTTP-date predicate](../evidence/selected/datagen-http-date-acceptance.json) and [JUnit assertion](../evidence/selected/reporting-junit-acceptance.json). Component controls do not measure benchmark-wide incidence.

## Repairs and reusable checks

- [Schemathesis function identity](../proposedrepairs/schemathesis-config-function-identity/README.md) and its [native comparison](../evidence/selected/schemathesis-native-repair-comparison.json): matched evidence for the correction, not a complete reference solution.
- [English assessment completeness](../proposedrepairs/college-english-assessment-completeness/README.md): offline supplied-source controls with fixed responses.
- [Rust proposed repair](../proposedrepairs/rust-known-failure-credit/README.md) and [portable reproduction](../reproductions/rust-known-failure-credit/README.md): finite original-helper evidence; actual Cargo/native behavior is separate.
- [Date-checker V2](../proposedrepairs/datagen-http-date/README.md): finite calendar/clock repair, preserved V1 retractions and an unresolved leap-occurrence boundary.
- [JUnit checker repair](../proposedrepairs/reporting-junit/README.md): controlled cases plus a selected native pass against the actual reporting writer; no full patched-scorer approval.

## Reporting candidate and remaining gaps

The [native acceptance](../evidence/selected/reporting-native-reference-acceptance.json), [saved outcomes](../evidence/selected/reporting-native-reference-result.json) and [different review](../evidence/selected/reporting-native-reference-review.json) support 55 printed original tests passing with score 1.0, plus the separate patched JUnit test. The scorer's 53/53 summary is a different count of that same run.

The [22-requirement matrix](REPORTING-COVERAGE.md), [accepted mapping](../evidence/selected/reporting-requirement-coverage-acceptance.json) and [concise source-pinned projection](../evidence/selected/reporting-requirement-coverage-summary.json) explain the limits. The [failed integration-control acceptance](../evidence/selected/reporting-integration-v2-failure-acceptance.json) and [different review](../evidence/selected/reporting-integration-v2-failure-review.json) establish no successful nested lifecycle coverage. Current ready work is in [HANDOFF](../HANDOFF.md).

## Other useful evidence and availability

[Apple numeric bounds](../evidence/selected/apple-numeric-range.json) and its [current execution-record correction](../evidence/selected/apple-current-execution-review.json) separate mathematical conclusions from judge execution. [VRPTW converter pairs](../evidence/selected/vrptw-retained-converter-reproduction.json) and [CTA workbook integrity](../evidence/selected/cta-acquired-workbook-integrity.json) illustrate finite data checks without claiming domain truth. [Carleson's closed setup failure](../evidence/selected/carleson-cap-restoration-failed-prefix.json) illustrates a failed version check that establishes no upstream defect.

The [source manifest](CONSOLIDATED-SOURCE-MANIFEST.json) identifies the execution-source snapshot. Full private inputs, source-citation reports, image layers, raw logs and live accounting remain local. Selected receipts are not a promise that every linked body is redistributable or available in a clone. Earlier chronological reports remain in Git at commit `8f55f7e115cd68d7e61da94db5c8b4e5486e42aa`; current methodology is [VERIFICATION](../VERIFICATION.md).
