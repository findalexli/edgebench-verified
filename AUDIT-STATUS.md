# Where the audit stands

Scientific evidence snapshot: **October 11, 2026, 07:24 UTC**. Presentation reviewed again at **17:24 UTC**. This is an unfinished, private audit; no benchmark release is approved.

**We have decided to omit ten flawed original task versions from a candidate release. The other 41 public tasks still await a final decision, and none is certified for inclusion.** Since the 06:41 UTC checkpoint, VLIW Kernel Optimization became the tenth exclusion. That is one new final task decision and one newly closed finding. The latest interval did not add a newly tested task.

| Decision on the 51 public originals | Tasks | Meaning |
| --- | ---: | --- |
| Excluded after review | **10** | A specific, independently reviewed defect justifies omitting this exact original version. |
| Awaiting a final decision | **41** | The evidence does not yet support a final keep, repair or exclude decision. |
| Certified for inclusion | **0** | No original or replacement has completed the required release review. |

**What “excluded” means:** omit the exact flawed original from the candidate release and preserve its evidence. The decision is finished for that version. It does not delete the task from the audit, mean every score is wrong, fix the task, or approve a replacement. A corrected version needs its own tests and release decision. [Why these ten originals were excluded](docs/FINDINGS.md#why-ten-original-versions-are-excluded).

**Thirteen specific finding decisions are closed.** A confirmed defect can be settled before its repair is ready, and a useful partial check does not finish a task review. The finding count is separate from the final task decisions above. Another **83 advertised tasks were unavailable** and are outside this audit's acquired set.

## What the latest work established

- **VLIW Kernel Optimization:** an invalid file could replace the live checker and be reported correct in a local run of the original source. Existing native evidence connects that source to the acquired task version. The invalid file itself was not run in the native image. This supports excluding the original; it does not establish a legal optimization or a leaderboard gain. [Decision](evidence/selected/vliw-original-exclusion.json).
- **Ordinary VLIW failures and timeout:** three local calls rejected empty source, malformed source and an empty instruction program. A sleeping program hit the original 600-second limit and received no valid score. These are four new local original-source calls. [Rejections](evidence/selected/vliw-three-rejection-controls.json) · [timeout](evidence/selected/vliw-original-timeout-control.json).
- **Juliet vulnerability detection:** the original public scorer gave an empty analyzer 10 points with zero detections and 192 misses across 192 label records. The written scoring rule deliberately allows that partial credit, so this result is neither a new defect nor successful detection. This was one new public scoring call. [Result](evidence/selected/juliet-original-public-baseline.json).
- **K–12 answer references:** all 100 retained answer-reference rows matched their scenarios. This checks that the records link correctly, not that the answers or labels are true. [Result](evidence/selected/k12-answer-reference-correspondence.json).

The VLIW integrity result and earlier positive native run were recovered and reused, not rerun. The latest update therefore contains **five new local original-source calls**, alongside the data-reference check and the new exclusion decision.

## Why the audit is still unfinished

From the 07:24 checkpoint through the 17:10 state check, no additional task checks completed. The next cloud checks had not launched, and the prepared report was still uncommitted. This was a real stall. The new independent review found an overstated coverage description, corrected below; it did not add new benchmark test results.

Progress has produced clearer defect decisions, but **no task has reached inclusion approval and the latest interval added no newly tested task**. Pending work includes partial checks, formal tasks that have reached only source or environment work, and seven tasks stopped by existing review holds. An example of stalled execution is Carleson: its proof-tool version check crashed before any proof or original helper ran. That is an audit setup failure, not a demonstrated benchmark defect. [Saved attempt](evidence/selected/carleson-cap-restoration-failed-prefix.json).

The next useful work is to finish supported decisions from saved results and complete ready checks on still-pending tasks. A confirmed original defect does not need to be rediscovered before a separate repair can proceed. Where setup fails, make one supported correction, then move to another runnable task rather than repeat the same attempt.

The detailed records below retain the limits of each check. The [verification protocol](VERIFICATION.md) defines the separate standard for including an original or corrected task. The active work window ends **October 12, 2026 at 05:52:16 UTC**.

The historical tracking group of **37 tasks with partial observations** is being reconciled against evidence outside that group. It should not be read as the total number of tasks ever checked or reviewed. This bookkeeping question does not change the ten original-version exclusions or certify any task.

<details>
<summary>Detailed results and earlier checkpoints</summary>

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
