# Where the audit stands

Scientific evidence snapshot: **October 11, 2026, 19:17 UTC**. This is an unfinished, private audit; no benchmark release is approved.

**The date-checker repair now rejects six earlier false acceptances, and the reporting coverage review separates tested behavior from remaining gaps.** These advance existing tasks; the totals remain **16 scoped findings, ten excluded originals, 41 pending and zero certified**.

| Decision on the 51 public originals | Tasks | Meaning |
| --- | ---: | --- |
| Excluded after review | **10** | A specific, independently reviewed defect justifies omitting this exact original version. |
| Awaiting a final decision | **41** | The evidence does not yet support a final keep, repair or exclude decision. |
| Certified for inclusion | **0** | No original or replacement has completed the required release review. |

**What “excluded” means:** omit the exact flawed original from the candidate release and preserve its evidence. The decision is finished for that version. It does not delete the task from the audit, mean every score is wrong, fix the task, or approve a replacement. A corrected version needs its own tests and release decision. [Why these ten originals were excluded](docs/FINDINGS.md#why-ten-original-versions-are-excluded).

**Sixteen scoped finding-task decisions are closed.** A confirmed defect can be settled before its repair is ready, and a useful partial check does not finish a task review. The finding count is separate from the final task decisions above. Another **83 advertised tasks were unavailable** and are outside this audit's acquired set.

## Operational update at 19:30 UTC

**All five authored reporting integration controls failed before their nested lifecycle checks.** The installed candidate matched its expected files, but our control creates `tox.ini` and asks pytest to load `pytest.ini`. This is a confirmed source mistake in our control, not a demonstrated defect in the candidate or upstream task. The exact missing filename was not retained in the runtime traceback, so the historical cause remains source-supported rather than directly observed. [Accepted failure review](evidence/selected/reporting-integration-v2-failure-acceptance.json) · [different result review](evidence/selected/reporting-integration-v2-failure-review.json).

The worker is closed. The corrected controls remain source-only; no successful nested lifecycle or xdist coverage is added. The earlier 55 passing original tests and score 1.0 retain their stated limits. A separate coverage-helper process exited successfully, but its result could not be parsed; no scientific conclusion is accepted from it. Findings, task decisions and certifications are unchanged.

## What changed since the 19:03 UTC checkpoint

**Schemathesis Data Generation:** date-checker repair V2 passed all 16 classified reviewer controls; one future leap-second occurrence remains unclassified. It corrects V1's acceptance of years before 1900 and second 60 outside 23:59 GMT. The original impossible-date finding and V1's retracted year assumptions remain documented. This is a finite predicate repair, without native generator or full patched-scorer validation. [Patch, controls and limits](proposedrepairs/datagen-http-date/README.md).

**Schemathesis Reporting:** the accepted 22-requirement mapping gives **ten finite named behavior conclusions, ten partially tested requirements and two behaviors supported only by source inspection**. This is not ten whole requirements approved. Automatic pytest lifecycle, stateful/xdist behavior and nonvacuous body-property checks still need their own evidence. [Readable coverage matrix](docs/REPORTING-COVERAGE.md).

These accepted analyses add no findings, task breadth, exclusions or certifications. This delivery reruns no tests and claims no later integration-control result.

## Earlier native checkpoint at 19:03 UTC (changes since 18:23 UTC)

The reporting implementation was applied as a **30-file overlay** inside the pinned original judge. All five original test modules and the scoring command stayed unchanged. The run completed in 22.6 seconds with **55 distinct printed test items passing** and score **1.0**. The scorer reports **53/53** because phase four uses a nine-test success count while printing 11 items. These are different counts of the same run, not extra tests. [Accepted result](evidence/selected/reporting-native-reference-acceptance.json) · [saved outcomes](evidence/selected/reporting-native-reference-result.json) · [different result review](evidence/selected/reporting-native-reference-review.json).

Afterward, the actual candidate writer passed the separately mounted patched JUnit test in 2.0 seconds. That is one selected repaired-test result, not a run of the full patched scorer. The owned worker closed; the settled usage estimate is $0.00828.

This adds **one original full-scorer call and one selected patched-test call** on a task already checked. It adds no finding, task breadth, exclusion or certification. The overlay is not a persisted replacement image; passing the original tests does not establish the full reporting specification. Actual pytest lifecycle and xdist behavior remain separate questions. The 240-second diagnostic budget differs from the original 1,800-second allowance; no measured aggregate memory peak or fresh independent native rerun is claimed.

## Earlier checkpoint: 16 findings at 18:23 UTC

**Two more checker weaknesses are confirmed: impossible HTTP dates pass a date predicate, and malformed XML passes a reporting test.** There are now **16 confirmed findings at their documented scopes**. Ten original versions remain excluded, 41 public tasks await a final decision, and none is approved for inclusion.

- **Schemathesis Data Generation:** the original date predicate accepts impossible dates and clock values. A separate reviewer reproduced acceptance of April 31 and minute 60; valid dates still pass. This establishes a weakness in the predicate, not a run of the generated strategy or full test suite. [Conclusion](evidence/selected/datagen-http-date-acceptance.json) · [results](evidence/selected/datagen-http-date-result.json) · [independent review](evidence/selected/datagen-http-date-review.json).
- **Schemathesis Reporting:** the unchanged original JUnit test accepts plain text and malformed XML containing its two required text fragments. A separate reviewer reproduced acceptance of a report missing its closing tag. Valid XML passes, while a missing-label control fails the original test. The writer was controlled; actual production output and whole-suite acceptance were not measured. [Conclusion](evidence/selected/reporting-junit-acceptance.json) · [results](evidence/selected/reporting-junit-result.json) · [independent review](evidence/selected/reporting-junit-review.json).
- **Rust:** the scoped source patch passed finite component review. It fixes the measured exception-credit error while preserving the other crate's unresolved allowance. The broader first proposal was narrowed after independent counterevidence. [Prototype and evidence](proposedrepairs/rust-known-failure-credit/README.md).

The two new findings used **17 local original-predicate/test evaluations**: 11 date-predicate evaluations and six reporting-test calls, including separate reproductions. Both tasks already had partial evidence, so this adds depth and conclusions, not two newly checked tasks. No native task run, full-score effect, final task decision or certification is added. The Rust patch remains a local prototype.

## Repair progress after the 18:23 UTC checkpoint

The reporting checker has a concrete patch that checks XML structure and the recorded error. Twelve author controls and four fresh reviewer controls support it. The later native result above adds a pass against the actual candidate writer for the selected patched test; the full patched scorer and a persisted corrected image remain untested. This is a repair prototype, not an approved replacement. [Patch and evidence](proposedrepairs/reporting-junit/README.md).

Apple’s current summary now includes its already accepted 50-case judge run. Its independent-review checklist permits justified fixed-suite evidence, as the protocol requires, instead of demanding a new seed and timing sweep by default. The authentic submission/history path and other task requirements remain unresolved. This correction adds no new test or gate pass. [Record correction](evidence/selected/apple-current-execution-review.json).

## Earlier checkpoint: 14 findings at 17:58 UTC

- **Rust Multicrate Reconstruction:** the original Python helper credited an unrelated failed test when the named exempt test passed. Six authored controls and three independently authored controls support the finding; an independent example reported 11 passed, zero failed and PASS while one hidden failure remained. Cargo responses were simulated. The 0.1 score difference is synthetic, not measured native or benchmark impact. The original task decision remains pending. [Accepted finding](evidence/selected/rust-known-failure-outcome.json) · [portable reproduction](reproductions/rust-known-failure-credit/README.md).
- **Apple Incremental Game:** the mathematical score is bounded by 8,200,000 per case and 410,000,000 across the fixed 50 cases, so correctly computed integer scores convert exactly through the caller’s floating-point step. Independent reasoning and arithmetic checks support this narrow requirement. Saved numeric values were reconstructed as decimal strings; raw markers were not reparsed, and native logarithm rounding remains unproved. [Accepted conclusion](evidence/selected/apple-numeric-range.json).
- **Schemathesis Config:** new public paths may re-export existing implementations while obsolete aliases are removed. This resolves the apparent conflict in those instructions, but the complete list of old paths to remove is still unspecified. No implementation or whole specification approval follows. [Accepted source interpretation](evidence/selected/schemathesis-api-contract.json).

This update adds **one confirmed finding and one satisfied numeric-conversion requirement**, plus a narrow API interpretation. It adds no native or full-task runs, newly checked task, repair validation, final task decision or certification.

## Operational update at 18:12 UTC

The Schemathesis replacement image built successfully, but a configuration guard stopped the attempt before any original scorer ran. The differing field is unknown because the actual configuration and logs were not exported. The owned worker is closed. This was our setup failure, not a new task defect; this attempt will not be retried without concrete evidence identifying the failed guard. That attempt added no scientific result or count change. [Accepted build-stop record](evidence/selected/schemathesis-persisted-build-stop.json).

## Why the audit is still unfinished

The earlier stall remains part of the record: from the 07:24 checkpoint through the 17:10 state check, no additional task checks completed. The next cloud checks had not launched, and the prepared report was still uncommitted. The 17:24 presentation review corrected an overstated coverage description without adding benchmark test results. The Rust, Apple and API conclusions were accepted at 17:58 UTC; the two additional checker findings were accepted by 18:23 UTC.

The new component and arithmetic checks advance specific questions, but **no task has reached inclusion approval and no new task entered the checked set**. Pending work includes partial checks, formal tasks that have reached only source or environment work, and seven tasks stopped by existing review holds. An example of stalled execution is Carleson: its proof-tool version check crashed before any proof or original helper ran. That is an audit setup failure, not a demonstrated benchmark defect. [Saved attempt](evidence/selected/carleson-cap-restoration-failed-prefix.json).

The next useful work is to finish supported decisions from saved results and complete ready checks on still-pending tasks. A confirmed original defect does not need to be rediscovered before a separate repair can proceed. Where setup fails, make one supported correction, then move to another runnable task rather than repeat the same attempt.

The detailed records below retain the limits of each check. The [verification protocol](VERIFICATION.md) defines the separate standard for including an original or corrected task. The active work window ends **October 12, 2026 at 05:52:16 UTC**.

The historical tracking group of **37 tasks with partial observations** is being reconciled against evidence outside that group. It should not be read as the total number of tasks ever checked or reviewed. This bookkeeping question does not change the ten original-version exclusions or certify any task.

<details>
<summary>Detailed results and earlier checkpoints</summary>

## Summary recorded at 07:24 UTC

- **VLIW Kernel Optimization:** an invalid file could replace the live checker and be reported correct in a local run of the original source. Existing native evidence connects that source to the acquired task version. The invalid file itself was not run in the native image. This supports excluding the original; it does not establish a legal optimization or a leaderboard gain. [Decision](evidence/selected/vliw-original-exclusion.json).
- **Ordinary VLIW failures and timeout:** three local calls rejected empty source, malformed source and an empty instruction program. A sleeping program hit the original 600-second limit and received no valid score. These are four new local original-source calls. [Rejections](evidence/selected/vliw-three-rejection-controls.json) · [timeout](evidence/selected/vliw-original-timeout-control.json).
- **Juliet vulnerability detection:** the original public scorer gave an empty analyzer 10 points with zero detections and 192 misses across 192 label records. The written scoring rule deliberately allows that partial credit, so this result is neither a new defect nor successful detection. This was one new public scoring call. [Result](evidence/selected/juliet-original-public-baseline.json).
- **K–12 answer references:** all 100 retained answer-reference rows matched their scenarios. This checks that the records link correctly, not that the answers or labels are true. [Result](evidence/selected/k12-answer-reference-correspondence.json).

The VLIW integrity result and earlier positive native run were recovered and reused, not rerun. The latest update therefore contains **five new local original-source calls**, alongside the data-reference check and the new exclusion decision.


## What changed since 06:41 UTC

**We excluded the original VLIW task after confirming that submitted code can replace its live checker.** Ten original versions are now excluded and thirteen specific finding decisions are closed. No new task entered the tested set, and no task is certified.

The unchanged original runner accepted an invalid file without the required kernel builder in a local source-copy control. A previously accepted native run confirms that the affected runner and verifier are installed in this exact original version. The invalid file itself was not run in the native image. This is a checker-integrity finding, not a permitted optimization or a measured legal score gain. [Decision](evidence/selected/vliw-original-exclusion.json) · [component evidence](evidence/selected/vliw-source-copy-integrity.json).

- **VLIW ordinary failures:** Three separate local source-copy calls rejected empty source, malformed source and an empty instruction program; none earned a valid cycle score. The saved memory anomaly prevents a claim of measured aggregate memory fit, and cleanup establishes direct-child completion only. These controls do not test a native submission or resolve checker replacement. [Result](evidence/selected/vliw-three-rejection-controls.json).
- **VLIW written requirements:** We rejected two extra obligations: final index write-back is expressly unnecessary, and the task does not require historical producer records for its performance anchors. Those source conclusions do not validate all calibration, data or rights. [Contract review](evidence/selected/vliw-specification-calibration.json).
- **K–12 answer references:** All **100 retained answer-reference rows** matched their test scenarios; **1,825 response-label references** resolved and met the integer-binary schema, and all **1,000 preferred post-test references** were known. Preferred lists matched the scenario lists. This extends the prior history-exclusion result only through that exact list correspondence; it does not verify label truth or execute the scorer. The **175 candidate entries without labels** are compatible with intentional padding. [Result](evidence/selected/k12-answer-reference-correspondence.json).

- **VLIW timeout:** One sleeping-program control reached the unchanged **600-second** limit and finished after **600.113 seconds**, with invalid output and null raw/normalized scores. The observed owned parent and direct child were absent afterward. The fallback error row is not a tested hidden kernel case. This was a local source-copy call, not a native-image run; the earlier failed observer's signal cause remains unknown. [Result](evidence/selected/vliw-original-timeout-control.json).
- **Juliet public baseline:** The full original public scorer and unchanged empty analyzer ran once on **240 cases and 192 label records**. They returned **10 points**, status OK, zero true or false positives and **192 misses**. The written low-recall cap makes those points intentional partial credit, not a defect or detection success. Native hidden cases, vulnerability truth and whole-task approval remain untested; the scientific Python micro-version was not captured. [Result](evidence/selected/juliet-original-public-baseline.json).

This update records **one new final task decision, one newly closed finding and five completed local original-path calls**: three ordinary VLIW rejections, one VLIW timeout and one Juliet public scoring call. The integrity control and native positive were recovered and reused, not rerun. The answer-reference check adds data evidence on an existing task. Earlier K–12 CSV, range and history checks and the rejected Juliet path hypothesis remain dated in the [evidence index](docs/EVIDENCE-INDEX.md).

## Earlier checks accepted by 06:05 UTC

We finished the following checks on tasks already under review. They add evidence, but no new finding or final task decision.

- **Routing (VRPTW):** The two original conversion functions reproduced all **56 retained input/output pairs exactly**, covering 5,656 input rows including depots. This checks file conversion, not route feasibility or solver quality. [Result](evidence/selected/vrptw-retained-converter-reproduction.json).
- **Walking (Bipedal):** The original native grader rejected **one malformed model file**. Its five checklist points were intentional partial credit; the walking score was zero. No new successful walking episodes ran; the older 20 episodes were reused. [Result](evidence/selected/bipedal-malformed-checkpoint-native.json).
- **NetHack:** The original result reader handled **four simulated game outputs** as expected: it accepted the score limit and rejected an excessive score, a failed child process and a malformed final result. No game or original full environment ran. [Result](evidence/selected/nethack-original-receipt-boundaries.json).
- **Rust:** The original loader read the **2,749-entry test manifest**. No public test was classified as hidden. However, shortening test identities merged 820 distinct hidden entries into 795 keys, losing 25 distinctions. Actual Rust tests and score effects were not checked. [Result](evidence/selected/rust-retained-split-consistency.json).
- **Portfolio:** All **16,990 price rows** matched instrument metadata; **6,988 macro values** were finite. But **730 price rows** lacked same-date macro data. The task permits strategies without that data, so this difference alone establishes neither a defect nor financial harmlessness. No original scorer ran. [Result](evidence/selected/portfolio-retained-table-links.json).
- **Juliet vulnerability data:** Facts for **976 cases and 915 label records** agreed on references, keys and declared distributions; no structural mismatch was found. Vulnerability and label truth remain unverified, and unlabeled cases are not proven safe. No original analyzer or scorer ran. [Result](evidence/selected/juliet-acquired-case-label-integrity.json).
- **CTA risk-budget data:** The diagnostic read **46,950 price rows and 554,691 selected cells** across six workbook sheets. Tested ticker and USD currency links and selected numeric values passed; no defect was found in those checks. Numeric costs, other sheets and financial correctness remain untested. No original scorer ran. [Result](evidence/selected/cta-acquired-workbook-integrity.json).
- **Carleson:** Required files were restored, but the attempt to check the proof program's version crashed before any proof or original helper ran. The cause is unknown, and the worker is closed. This is a failure of our test setup, not an established benchmark defect. [Saved failure](evidence/selected/carleson-cap-restoration-failed-prefix.json).

The preceding update added **19 execution cases**: four offline English grader calls, nine VLIW cases, two Molecular controls and four Schemathesis component controls. Two concrete proposed patches were checked: [English assessment completeness](evidence/selected/english-final-source-repair.json) and [Schemathesis function identity](evidence/selected/schemathesis-config-identity-repair.json). Neither replacement is certified. Older completed scoring runs were recovered or reused, not rerun. [Details](docs/EVIDENCE-INDEX.md).


</details>
