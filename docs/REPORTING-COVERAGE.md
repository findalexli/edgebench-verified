# What the reporting tests establish

Accepted coverage review: **October 11, 2026, 19:13 UTC**. The candidate passed 55 original printed tests, but test counts do not measure specification completeness. Mapping the assertions to the 22 named requirements gives **ten finite behavior conclusions, ten partial checks and two behaviors supported only by source inspection**. None is a whole-task approval.

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
| R2.4 | JUnit output | Partial | Real writer passed repaired error test; open/recorder-write remain. |
| R2.5 | NDJSON output | Partial | Initialization text/file size checked; event parsing and closing remain. |
| R2.6 | Allure format enum | Finite checks | Member and empty extension checked. |
| R2.7 | Report configuration | Finite checks | Enablement/default paths checked; cross-process use remains separate. |
| R3.1 | Recorder dispatcher | Partial | Registration and one recorder checked; removal/separation remain. |
| R3.2 | Automatic pytest lifecycle | Source only | Original tests manually write reports; automatic lifecycle not exercised. |
| R3.3 | Stateful callback | Partial | Marks import; state-machine callback/teardown not exercised. |
| R3.4 | xdist transport | Partial | Interfaces import; actual workers, writes and cleanup remain. |
| R4.1 | Optional example properties | Finite checks | Finite body/query sibling-generation cases checked. |
| R4.2 | Example branch isolation | Finite checks | Finite oneOf/anyOf cases checked. |
| R4.3 | Example routing | Finite checks | Finite top-level extraction cases checked. |
| R5.1 | Email domain normalization | Finite checks | Helper cases and bounded strategies checked. |
| R5.2 | Unexpected body properties | Source only | Potentially empty filtered iteration; runtime nonvacuity remains. |

“Finite checks” means the specific named behavior and inputs have support, not that every behavior under that requirement is proven. The two central gaps are automatic pytest lifecycle and nonvacuous body-property suppression. The latter is a source-indicated hypothesis, not a new confirmed defect. Stateful and xdist execution remain separate checks. No later runtime-control result is claimed by this snapshot.

[Accepted review](../evidence/selected/reporting-requirement-coverage-acceptance.json) · [concise row details and private-source identity](../evidence/selected/reporting-requirement-coverage-summary.json) · [accepted native results](../evidence/selected/reporting-native-reference-acceptance.json). The 61,621-byte source-citation review remains local. Its corrected citation-freeze disclosure is retained in the acceptance record. This summary adds no tests, findings, task breadth, dispositions or certifications.
