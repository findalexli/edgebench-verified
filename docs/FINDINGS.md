# What we found

**Ten exact original versions are excluded from the candidate release because of independently reviewed defects.** “Excluded” means omit that original version while keeping its audit record. It does not mean the task is repaired, every score is wrong, or a corrected version is approved.

The audit has **13 closed finding decisions**, including the ten exclusions below. The remaining three findings are confirmed at a narrower scope, with their overall task decisions still pending. None of these findings certifies a replacement or establishes how often the defect changes real benchmark scores. [Current counts and progress](../AUDIT-STATUS.md).

## Why ten original versions are excluded

| Original task | Reason for exclusion | Important limit and evidence |
| --- | --- | --- |
| **Triangulation Coloring** | All ten acquired large meshes contain triangles whose interiors overlap. The supplied inputs violate the promised geometry. | Checks cover those ten meshes; the generation error's cause and future inputs remain unknown. [Accepted finding and decision](../evidence/selected/12-finding-decisions.json). |
| **Lean Analysis Proofs** | Two requested mathematical statements are false under their written assumptions and intended meanings. Sound full completion cannot satisfy those requirements unchanged. | Mathematical counterexamples were separately reviewed; no installed Lean compiler result is claimed, and partial credit remains possible. [Accepted finding and decision](../evidence/selected/12-finding-decisions.json). |
| **Order Addition** | The integrity test expects a different fingerprint from the supplied scoring helper, so the task fails a required check on its own installed file. | Valid reports and nonzero scores remain possible. Tests of a small correction do not approve the replacement. [Decision](../evidence/selected/order-original-exclusion-binding.json). |
| **Wireless Electricity Layout** | The raw scoring and selection path ranks an observed compilation failure above an observed feasible solution. | All three observed normalized scores were zero, so no leaderboard gain was established. [Decision](../evidence/selected/wireless-original-exclusion.json). |
| **Jagua Nesting** | The complete placement validator accepts selected shapes whose interiors overlap, violating the placement requirements. | Some other overlap examples were rejected; the tests showed no score improvement on five equal-width cases. [Decision](../evidence/selected/jagua-original-exclusion.json). |
| **Equivalence Classes** | An original checker accepts output whose operation cost exceeds the stated limit. | An at-limit control also passed. Other runs encountered submission errors; no score gain follows from this finding. [Decision](../evidence/selected/eq-graph-original-exclusions.json). |
| **Graph Node Classification** | The checker turns an undefined confidence value, NaN, into zero and accepts the complete submission despite the required numerical range. | No score inflation or explicit requirement to reject every such violation was established. This is a conservative task-contract decision, not a demonstrated corrupted score. [Decision](../evidence/selected/eq-graph-original-exclusions.json) · [qualification](../evidence/selected/graph-confidence-qualification.json). |
| **Tree Block Partitioning** | A supplied multiplication routine returns the wrong value when it uses the same object as an input and output; the written operation permits this case. | Six selected examples support the defect. The official reference avoids it, and the affected subtask is five of 100 points. [Decision](../evidence/selected/tree-original-exclusion.json). |
| **College English Exam** | The supplied grader can finish without assessing every required rule, accepting an incomplete assessment as valid. | Fixed-response local calls support the finding. The earlier 100-point examples belong to an earlier grader copy, not the final supplied source. [Decision](../evidence/selected/english-original-exclusion.json) · [final-source check](../evidence/selected/english-final-source-repair.json). |
| **VLIW Kernel Optimization** | Submitted code can replace the live per-case checker, allowing an invalid file without the required kernel builder to be reported correct. | The invalid control ran on a local copy of the original source. Existing native receipts identify the same installed runner and verifier, but the invalid file was not run there. [Decision](../evidence/selected/vliw-original-exclusion.json). |

Each row concerns the acquired version. None of these decisions automatically excludes a future corrected version or clears it for release. The historical evidence records keep their original dates and counts; the [status page](../AUDIT-STATUS.md) owns the current totals.

## Three other confirmed findings, with task decisions pending

| Task | What is established | Why the claim stays narrow |
| --- | --- | --- |
| **Schemathesis Config** | Tests omit the requirement to return the identical decorated function and accept a forwarding wrapper instead. | The complete original scorer gave the reference and wrapper the same partial score, 0.135313. This confirms a missing test, not a wrapper score gain or an automatic exclusion. [Accepted full-score result](../evidence/selected/schemathesis-full-consumer-recovery.json). |
| **SMT Solver** | The recovered witness lookup merges expressions from different variable scopes. It cannot represent the different values required by a constructed satisfiable example. | Source analysis and a small local test support this finding; full-image failure, false acceptance and score impact remain unobserved. Existing follow-up work is held. [Accepted finding](../evidence/selected/12-finding-decisions.json). |
| **FFmpeg Scaling** | A recovered timing component can report a positive speed ratio even when a timed call fails or produces no output. | Controlled local substitutes establish the component behavior. The task has separate correctness checks; bypassing them or improving a real benchmark score was not shown. Existing follow-up work is held. [Accepted finding](../evidence/selected/12-finding-decisions.json). |

“Original component ran” means the named original checker, grader or routine was executed. It does not imply that the entire task environment or hosted benchmark ran. Mathematical arguments and local tests are identified separately above.

## Repairs are a separate result

Two proposed changes are available in the original task format: [English assessment completeness](../proposedrepairs/college-english-assessment-completeness/README.md) and [Schemathesis function identity](../proposedrepairs/schemathesis-config-function-identity/README.md). **Neither is a certified replacement.**

For English, four offline calls used fixed model responses and an explicit controlled rubric. The correction preserved a complete assessment at valid 96 and changed an assessment missing a rule from original valid 96 to candidate invalid 0. This shows the selected correction works on those cases. The installed environment and real model-provider behavior remain untested. [Accepted repair check](../evidence/selected/english-final-source-repair.json).

For Schemathesis, the candidate adds the required function-identity check. Its two-file patch and exact original/changed-file identities are recorded, but a newly integrated replacement image has not been certified. [Candidate and tested scope](../proposedrepairs/schemathesis-config-function-identity/README.md).

The [evidence index](EVIDENCE-INDEX.md) explains what is included in this repository and what remains in the local archive. These findings do not measure historical leaderboard effects or establish a complete repair of any task.
