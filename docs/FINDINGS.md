# What we found

**We decided to withhold ten exact original versions from the proposed verified release.** “Excluded” is a release decision; it does not mean every score is wrong or repair is impossible. Evidence remains available, and corrected versions need separate approval.

There are **16 closed finding-task decisions**: ten with exclusions and six whose task decisions remain pending. None certifies a replacement or measures historical leaderboard impact. [Current summary](../README.md) · [Task decisions](../TASKS.md).

## Why ten original versions are excluded

| Original task | Reason for exclusion | Important limit and evidence |
| --- | --- | --- |
| **Triangulation Coloring** | All ten acquired large meshes violate the promised geometry: triangle interiors overlap. | The cause and future inputs remain untested. [Accepted finding and decision](../evidence/selected/12-finding-decisions.json). |
| **Lean Analysis Proofs** | Two required statements in the acquired source are mathematically false; sound completion requires changing them. | This is an acquired-source contract decision: installed theorem types and Lean compiler behavior remain unverified. Other targets can earn legitimate partial credit. [Accepted finding and decision](../evidence/selected/12-finding-decisions.json). |
| **Order Addition** | A required integrity check expects the wrong fingerprint for its supplied installed helper. | Valid reports and nonzero scores remain possible; the small correction is not an approved replacement. [Decision](../evidence/selected/order-original-exclusion-binding.json). |
| **Wireless Electricity Layout** | Raw scoring ranks an observed compilation failure above a feasible solution. | All three normalized scores were zero; no leaderboard gain was shown. [Decision](../evidence/selected/wireless-original-exclusion.json). |
| **Jagua Nesting** | The complete validator accepts selected shapes with overlapping interiors. | Other overlaps were rejected; five equal-width cases showed no score improvement. [Decision](../evidence/selected/jagua-original-exclusion.json). |
| **Equivalence Classes** | An original checker accepts output whose operation cost exceeds the stated limit. | An at-limit control passed; no score gain was established. [Decision](../evidence/selected/eq-graph-original-exclusions.json). |
| **Graph Node Classification** | Conservative policy choice: the checker silently replaces NaN confidence with zero. | Acceptance violates the supplied numerical range, but tolerance may be intended. Mandatory total rejection and score inflation are unproved. [Decision](../evidence/selected/eq-graph-original-exclusions.json) · [qualification](../evidence/selected/graph-confidence-qualification.json). |
| **Tree Block Partitioning** | A supplied multiplication routine gives a wrong result when input and output share storage, a case permitted by its operation contract. | Six selected examples support a defect in **5/100 points**. The official reference avoids it; the other 95 points are not invalidated. [Decision](../evidence/selected/tree-original-exclusion.json). |
| **College English Exam** | The grader accepts an assessment missing required rules as complete. | Fixed-response local calls support this. Earlier 100-point examples used an earlier grader copy. [Decision](../evidence/selected/english-original-exclusion.json) · [final-source check](../evidence/selected/english-final-source-repair.json). |
| **VLIW Kernel Optimization** | Submitted code can replace the live checker and make an invalid file appear correct. | The invalid control ran on an original source copy. Native receipts match installed source identities; no native invalid-submission run occurred. [Decision](../evidence/selected/vliw-original-exclusion.json). |

None of these exclusions rests merely on missing evidence or our environment failures. Current totals are in the [summary](../README.md).

## Six other confirmed findings, with task decisions pending

| Task | What is established | Why the claim stays narrow |
| --- | --- | --- |
| **Schemathesis Data Generation** | The original date predicate accepts impossible dates and times, including April 31 and minute 60. | Eleven predicate evaluations; no generator, native or score-impact claim. [Conclusion](../evidence/selected/datagen-http-date-acceptance.json) · [independent review](../evidence/selected/datagen-http-date-review.json). |
| **Schemathesis Reporting** | The original JUnit test accepts non-XML or malformed XML containing its two required text fragments. | Four authored and two independent original-function calls used controlled writers. Actual-writer repair evidence follows below. [Conclusion](../evidence/selected/reporting-junit-acceptance.json) · [review](../evidence/selected/reporting-junit-review.json). |
| **Rust Multicrate Reconstruction** | A passing test on the known-failure list can cancel an unrelated failure, allowing the Python helper to report PASS. | Six authored and three independent controls simulated Cargo. The 0.1 score effect is synthetic; incidence and native impact are unknown. [Finding](../evidence/selected/rust-known-failure-outcome.json) · [reproduction](../reproductions/rust-known-failure-credit/README.md). |
| **Schemathesis Config** | Tests omit the requirement to return the identical decorated function and accept a forwarding wrapper instead. | The original scorer gave reference and wrapper the same partial score, 0.135313. This confirms the missing test, without score gain. [Accepted full-score result](../evidence/selected/schemathesis-full-consumer-recovery.json). |
| **SMT Solver** | The recovered witness lookup merges expressions from different variable scopes. It cannot represent the different values required by a constructed satisfiable example. | Source and a small local test support this; native failure and score impact remain unobserved. Follow-up is held. [Accepted finding](../evidence/selected/12-finding-decisions.json). |
| **FFmpeg Scaling** | A recovered timing component can report a positive speed ratio even when a timed call fails or produces no output. | Local substitutes establish this behavior. Separate correctness checks were not bypassed; real score gain is unproved. Follow-up is held. [Accepted finding](../evidence/selected/12-finding-decisions.json). |

A component call is not a full native task run. Mathematical arguments, local controls and native results are distinguished above.

## Other scoped conclusions

Apple Incremental Game’s integer conversion is exact within its mathematical range: 8,200,000 per case, 410,000,000 for 50 cases. Native logarithm rounding remains unproved. [Range review](../evidence/selected/apple-numeric-range.json). Schemathesis’s new API paths can coexist with removal of obsolete aliases, but the complete removal list remains unspecified. [API interpretation](../evidence/selected/schemathesis-api-contract.json). Neither adds a finding or clears a task gate.

## Repairs are a separate result

**None is a certified task replacement.** Test-suite results and finite correction checks do not approve a whole task.

**Schemathesis Reporting:** the candidate implementation passed **55 distinct printed test items** in one unchanged native scorer run, earning **1.0**. The script reported 53/53 because its phase-four success count differs from the printed item count. The actual candidate writer then passed the separately mounted repaired JUnit test. This supports the selected repair, not a full patched-scorer run or all reporting requirements. [Accepted native result](../evidence/selected/reporting-native-reference-acceptance.json) · [JUnit repair](../proposedrepairs/reporting-junit/README.md).

Five later integration controls failed before lifecycle assertions. Our fixture creates `tox.ini`, but the controls request `pytest.ini`: a source-confirmed control defect, not a new reporting finding. The exact historical traceback was not exported. This attempt validates no lifecycle or xdist behavior. [Accepted failure review](../evidence/selected/reporting-integration-v2-failure-acceptance.json).

**Schemathesis Data Generation:** date-checker V2 passed **16 classified independent predicate checks**, fixing six earlier false acceptances. One future leap-second occurrence remains unclassified. No generator, Hypothesis suite or native scorer ran; arbitrary leap-second occurrence remains outside the correction. [Accepted correction](../evidence/selected/datagen-http-date-repair-v2-acceptance.json) · [patch and limits](../proposedrepairs/datagen-http-date/README.md).

**College English:** four offline calls used fixed model responses and a controlled rubric. The correction preserved a complete assessment at valid 96 and changed one missing a rule from valid 96 to invalid 0. Installed and real-provider behavior remain untested. [Repair](../proposedrepairs/college-english-assessment-completeness/README.md) · [accepted checks](../evidence/selected/english-final-source-repair.json).

**Schemathesis Config:** the correction passed a native comparison on partial implementations. The reference retained 0.135313; the wrapper changed to 0.129063, exactly −1/160. All 126 original outcomes stayed unchanged in each pair. October 8 runs were recovered; complete implementation remains absent. [Comparison](../evidence/selected/schemathesis-native-repair-comparison.json) · [patch](../proposedrepairs/schemathesis-config-function-identity/README.md).

**Rust:** an [accepted finite prototype](../proposedrepairs/rust-known-failure-credit/README.md) credits the `cas-pty` exemption only for its explicit FAILED outcome and adjusts the corresponding totals. Five paired helper controls used simulated Cargo responses; different review reused earlier mixed-bucket controls after checking the V2 guard. CLI allowance behavior remains unresolved. No native Rust repair ran.

[Evidence index](EVIDENCE-INDEX.md).
