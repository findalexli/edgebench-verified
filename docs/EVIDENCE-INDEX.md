# Supporting evidence

Use [findings](FINDINGS.md) for conclusions and the [task tracker](../TASKS.md) for current dispositions. This page selects useful starting points; the [evidence manifest](../evidence/selected/EVIDENCE-MANIFEST.json) lists every selected artifact, its identity and provenance. Source paths inside JSON records may refer to the local archive rather than files shipped in this repository.

## Findings and original-version decisions

- [Finding decisions at the earlier twelve-finding snapshot](../evidence/selected/12-finding-decisions.json) and [historical 51-task observations](../evidence/selected/51-task-coverage.md) retain their dates; neither is the current tracker.
- Later original exclusions: [Wireless](../evidence/selected/wireless-original-exclusion.json), [Jagua](../evidence/selected/jagua-original-exclusion.json), [Equivalence and Graph](../evidence/selected/eq-graph-original-exclusions.json), [Tree](../evidence/selected/tree-original-exclusion.json), [English](../evidence/selected/english-original-exclusion.json) and [VLIW](../evidence/selected/vliw-original-exclusion.json). Findings links the remaining exclusions and exact scope.
- Additional confirmed checker weaknesses: [Rust exception credit](../evidence/selected/rust-known-failure-outcome.json), [HTTP-date predicate](../evidence/selected/datagen-http-date-acceptance.json), [JUnit assertion](../evidence/selected/reporting-junit-acceptance.json) and [reporting coverage filter](../evidence/selected/reporting-coverage-filter-acceptance.json). The last result is four actual native helper calls on candidate V2, with all 36 values discarded by the original filter; no original test-function/full-scorer or historical score-impact claim.

## Repairs and reusable checks

- [Tree T2 regression](../evidence/selected/tree-t2-repair-regression-acceptance.json) and [different review](../evidence/selected/tree-t2-repair-regression-review.json): ten official reference passes and ten wrong-control rejections in each original/corrected arm. Complements earlier alias-trigger evidence; T2 only, 5/100 points.
- [Equivalence T3 one-input repair check](../evidence/selected/equivalence-t3-repair-case-acceptance.json) and [different review](../evidence/selected/equivalence-t3-repair-case-review.json): corrected checker plus 64 MiB output allowance accepts the same official input, producing 40,623,541 bytes. Combined change, not all 30 cases or isolated score impact.

- [Schemathesis function identity](../proposedrepairs/schemathesis-config-function-identity/README.md) and its [native comparison](../evidence/selected/schemathesis-native-repair-comparison.json): matched evidence for the correction, not a complete reference solution.
- [English assessment completeness](../proposedrepairs/college-english-assessment-completeness/README.md): offline supplied-source controls with fixed responses.
- [Rust proposed repair](../proposedrepairs/rust-known-failure-credit/README.md) and [portable reproduction](../reproductions/rust-known-failure-credit/README.md): finite original-helper evidence; actual Cargo/native behavior is separate.
- [Date-checker V2](../proposedrepairs/datagen-http-date/README.md): finite calendar/clock repair, preserved V1 retractions and an unresolved leap-occurrence boundary.
- [JUnit checker repair](../proposedrepairs/reporting-junit/README.md): controlled cases plus a selected native pass against the actual reporting writer; no full patched-scorer approval.

## Reporting candidate and remaining gaps

The [fresh shared-hook regression](../evidence/selected/reporting-shared-regression-acceptance.json) and [different review](../evidence/selected/reporting-shared-regression-review.json) support the changed plugin's 55 original identities passing with score 1.0, plus a separate repaired JUnit test. The unchanged script reports 53/53. This newly measured regression preserves the [historical base result](../evidence/selected/reporting-native-reference-acceptance.json); the scorer is still unpatched.

The [current matrix](REPORTING-COVERAGE.md) has 13 finite-check rows and nine partial rows, not completed requirements. [Shared-hook comparison](../evidence/selected/reporting-shared-hook-acceptance.json): zero to four passes among five unchanged controls. [Corrected error assessment](../evidence/selected/reporting-writer-error-acceptance.json): five passes with event-based controls on that same candidate, without resolving the old stdout failure's cause. [Coverage-test repair](../proposedrepairs/reporting-coverage-filter/README.md): 20 expectations on earlier base V2—12 normal returns/eight expected assertions, using 12 actual-generator calls/eight doubles. The [combined corrected judge](../evidence/selected/reporting-integrated-acceptance.json) now passes 57 collected/55 reported tests at score 1.0, with all 24 countercontrols matching; [different review](../evidence/selected/reporting-integrated-review.json) preserves the finite limits. The original-judge regression remains separate. Historical [19:13](../evidence/selected/reporting-requirement-coverage-acceptance.json), [20:04](../evidence/selected/reporting-coverage-repair-acceptance.json) and [20:09](../evidence/selected/reporting-shared-hook-mapping.json) mappings retain their scope. [Next work](../HANDOFF.md).

## Other useful evidence and availability

[Treant contract conclusion](../evidence/selected/treant-contract-conclusion.json): the adapted README counts turns, rejecting a separate arithmetic-defect claim; movement intent remains unresolved.

[Apple numeric bounds](../evidence/selected/apple-numeric-range.json) and its [current execution-record correction](../evidence/selected/apple-current-execution-review.json) separate mathematical conclusions from judge execution. [VRPTW converter pairs](../evidence/selected/vrptw-retained-converter-reproduction.json) and [CTA workbook integrity](../evidence/selected/cta-acquired-workbook-integrity.json) illustrate finite data checks without claiming domain truth. [Carleson's closed setup failure](../evidence/selected/carleson-cap-restoration-failed-prefix.json) illustrates a failed version check that establishes no upstream defect.

The [source manifest](CONSOLIDATED-SOURCE-MANIFEST.json) identifies the execution-source snapshot. Full private inputs, source-citation reports, image layers, raw logs and live accounting remain local. Selected receipts are not a promise that every linked body is redistributable or available in a clone. Earlier chronological reports remain in Git at commit `8f55f7e115cd68d7e61da94db5c8b4e5486e42aa`; current methodology is [VERIFICATION](../VERIFICATION.md).
