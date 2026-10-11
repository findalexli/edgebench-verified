# What the reporting tests establish

Current evidence update: **October 11, 2026, 21:08 UTC, after accepted combined-judge integration**. The 22 named requirements have **13 finite checks and nine partial checks**. These describe evidence across exact candidate versions, not completed requirements or whole-task approval. The original judge’s 55 collected/53 reported pass remains separate from the combined corrected judge’s new 57 collected/55 reported pass; both score 1.0. All 24 integrated countercontrols match. This closes the combined-repair check without changing the requirement categories. Historical categories remain: 19:13 had ten finite/ten partial/two source-only; 20:04 had 11 finite/ten partial/one failed-controls row; 20:09 had 12 finite/ten partial.

| Requirement | Behavior | Evidence | Practical conclusion |
| --- | --- | --- | --- |
| R1.1 | Check-result data and exports | Finite checks | Fields and exports work in the tested cases. |
| R1.2 | Validation hooks | Partial | Schema/global paths observed; test scope, ordering and fast path remain. |
| R1.3 | Network-error hooks | Partial | Registration checked; actual failed-request dispatch remains. |
| R1.4 | Schema after-call hook | Finite checks | Actual successful request reached its recorder. |
| R1.5 | Hook-presence query | Finite checks | Register/unregister transitions checked. |
| R1.6 | Generated-value metadata | Partial | Generation runs; rewritten metadata not asserted. |
| R2.1 | Writer exports | Finite checks | Four writers and command helper export correctly. |
| R2.2 | VCR output | Partial | YAML/header shape checked; faithful interaction content remains. |
| R2.3 | HAR output | Partial | Nonempty report checked; request/response correspondence remains. |
| R2.4 | JUnit output | Partial | Real writer passes the repaired test within the integrated judge; four paired controls match. Open/recorder-write semantics remain partial. |
| R2.5 | NDJSON output | Partial | Initialization text/file size checked; event parsing and closing remain. |
| R2.6 | Allure format enum | Finite checks | Member and empty extension checked. |
| R2.7 | Report configuration | Finite checks | Enablement/default paths checked; cross-process use remains separate. |
| R3.1 | Recorder dispatcher | Partial | Finite registration/removal and separation pass; second-pop removal and accumulated check contents are not directly asserted. |
| R3.2 | Automatic pytest lifecycle | Finite checks | Five corrected stateless controls support opening, delivery and observed-writer closing, including named injected errors; exact session-start timing remains unproved. |
| R3.3 | Stateful callback | Partial | Later corrected controls pass three serial modes, including callback delivery and cleanup, on unchanged implementation. Finite scope; no broader xdist or all-schema conclusion. |
| R3.4 | xdist transport | Finite checks | Ordinary and injected-error worker/controller paths pass; arbitrary serialization and complete reports after interruption remain unproved. |
| R4.1 | Optional example properties | Finite checks | Finite body/query sibling-generation cases checked. |
| R4.2 | Example branch isolation | Finite checks | Finite oneOf/anyOf cases checked. |
| R4.3 | Example routing | Finite checks | Finite top-level extraction cases checked. |
| R5.1 | Email domain normalization | Finite checks | Helper cases and bounded strategies checked. |
| R5.2 | Unexpected body properties | Finite checks | Four real body/query allow/deny streams checked; corrected tests matched 20 paired expectations, including wrong-output and vacuity controls. |

“Finite checks” supports only the named behavior and inputs. Earlier coverage-test repair checks used base V2: 20 matched expectations, comprising 12 normal returns/eight expected assertions, using 12 actual-generator calls/eight doubles. Shared-hook correction improved four of five unchanged controls; five later event-based controls passed on that same changed plugin. The latter changed the error assessment, does not explain the earlier stdout failure, and does not make an unchanged-control zero-to-five comparison. The exceptional parallel control verifies observed-writer closing but skips final report content and complete receipt of both schemas. A separate fresh regression passed the original 55 identities and selected repaired JUnit test. The later combined corrected judge passes all 57 collected items (55 reported), score 1.0, and repeats all 20 coverage plus four JUnit countercontrols successfully. JUnit countercontrols use explicit writer doubles; its full phase separately exercises the real writer. Combined integration is closed. Three later corrected serial stateful controls pass their callback and cleanup assertions on unchanged implementation; lazy-schema/broader stateful behavior and fresh independent native reproduction remain open. The dated 13/9 classification is retained, not newly remapped here.

[Historical 19:13 UTC accepted review](../evidence/selected/reporting-requirement-coverage-acceptance.json) · [concise row details and private-source identity](../evidence/selected/reporting-requirement-coverage-summary.json) · [accepted native results](../evidence/selected/reporting-native-reference-acceptance.json). The 61,621-byte source-citation review remains local. Its corrected citation-freeze disclosure is retained in the acceptance record. This summary adds no tests, findings, task breadth, dispositions or certifications.

Evidence updates: [historical 20:04 mapping](../evidence/selected/reporting-coverage-repair-acceptance.json) · [failed base integration](../evidence/selected/reporting-integration-v3-acceptance.json) · [unchanged-control comparison](../evidence/selected/reporting-shared-hook-acceptance.json) · [historical 20:09 mapping](../evidence/selected/reporting-shared-hook-mapping.json) · [accepted corrected controls and current mapping](../evidence/selected/reporting-writer-error-acceptance.json) · [fresh original-suite regression](../evidence/selected/reporting-shared-regression-acceptance.json).

[Accepted combined integration](../evidence/selected/reporting-integrated-acceptance.json) · [different saved-result review](../evidence/selected/reporting-integrated-review.json).

[Accepted later serial stateful controls](../evidence/selected/reporting-stateful-corrected-acceptance.json) · [different detailed review](../evidence/selected/reporting-stateful-corrected-detailed-review.json). Earlier zero-of-three failures came from an unsupported every-callback-positive audit premise; this is not a zero-to-three implementation improvement.
