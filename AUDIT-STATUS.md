# Where the audit stands

Snapshot: **October 11, 2026, 06:41 UTC**. This audit is unfinished; no benchmark release is approved.

## What changed since 06:05 UTC

Three K–12 Math data checks are complete. The tested references and declared ranges passed; recorded history is excluded from recommendation pools. We also rejected a proposed Juliet path rule that the task does not state. These results add evidence on existing tasks, with no new finding or final task decision.

- **K–12 question references:** The two original CSV loaders read **5,000 questions and 50 knowledge points**; **45,000 scenario question references** resolved. This checks parsing and references, not answer labels or educational quality. [Result](evidence/selected/k12-question-reference-integrity.json).
- **K–12 declared ranges:** The selected knowledge-point keys fit **1–50**, and question difficulties fit the declared **1–5** range. No out-of-range references were found. This closes that specific caveat, not the whole data review. [Result](evidence/selected/k12-question-domain.json).
- **K–12 recorded history:** The diagnostic streamed **793,457 history rows**. All **200 scenarios** had past and future records; their recommendation pools excluded both, and test post-test lists excluded history. The **99 past-question references** in padded candidate lists are allowed by the generator, so they are not a new defect or evidence of solver leakage. When the scorer reaches these checks, membership in the measured pools also satisfies the recent-history rule. That is a conditional source/data result, not an executed score. [Result](evidence/selected/k12-history-cutoff.json).
- **Juliet witness paths:** We rejected the proposed requirement that witness statements must form an adjacent or reachable path in the supplied approximate control-flow graph. The acquired contract does not require it. Whether witnesses correctly describe vulnerabilities remains unresolved; no new corpus test ran. [Contract record](evidence/selected/juliet-unrequired-path-hypothesis.json).

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

## Decisions for the 51 public original versions

| Final decision | Tasks |
| --- | ---: |
| Approved for inclusion | 0 |
| Excluded after review | 9 |
| Awaiting a final decision | 42 |

**37 tasks have accepted partial test or data observations. Twelve specific finding decisions are closed.** Those are separate measures; neither means a complete task review.

The nine excluded originals are Triangulation Coloring, Lean Analysis Proofs, Order Addition, Wireless Electricity Layout, Jagua Nesting, Equivalence Classes, Graph Node Classification, Tree Block Partitioning and College English Exam. Their evidenced reasons are in the [findings report](docs/FINDINGS.md). These original-version decisions are finished; proposed replacements need their own review.

Of the **42 pending tasks**, 30 have some accepted observations, five formal tasks have only source/environment work, and seven remain stopped by existing review holds. Another **83 advertised tasks were unavailable**. The older [51-task table](evidence/selected/51-task-coverage.md) keeps its original date and counts.

## Next work

Close supported conclusions from evidence already collected and run ready checks in parallel. Acquire missing actual task data where possible. After one supported setup correction, move to another runnable task rather than repeat the same failed attempt.

Inclusion requires sound task requirements, checker, data, execution and independent-reproduction evidence. No task has passed that full review. Private data, raw logs, credentials and live worker records stay outside Git. [Evidence index](docs/EVIDENCE-INDEX.md) · [Release requirements](VERIFICATION.md).

The active work window ends **October 12, 2026 at 05:52:16 UTC**.
