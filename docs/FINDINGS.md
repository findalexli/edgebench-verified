# What we found

These twelve conclusions describe specific, confirmed problems in the acquired task versions. They do not certify whole tasks or show how often each problem affects benchmark scores. Current task decisions are on [the status page](../AUDIT-STATUS.md).

“Original check run” below means an actual original task component ran. It does not imply that the entire hosted benchmark ran. Local replays and mathematical arguments are labelled separately.

| Task | Confirmed problem | How it was checked | What the evidence does not establish |
| --- | --- | --- | --- |
| Triangulation Coloring | All ten acquired large meshes contain overlapping triangle interiors, violating the promised input structure. | Acquired-data geometry checks and original task execution. | Why the bad meshes were generated, or whether future meshes are valid. |
| Equivalence Classes | One original checker accepts output above its stated size limit. | Original check run with an at-limit control and an above-limit example. | A score gain. Other runs still encountered submission errors. |
| Graph Node Classification | A confidence value of NaN—an undefined numeric value—is accepted despite a required range of zero to one. | Original validation run on a controlled example. | Better classification quality or a leaderboard gain. |
| Schemathesis Config | Selected tests accept a wrapper even though the requirement is to return the identical decorated function. | Original component tests with a deliberately different wrapper. | That the complete task scorer accepts the same submission. |
| Tree Block Partitioning | A multiplication routine gives the wrong answer when an input and output refer to the same object. | Original routine checked against the specified polynomial meaning on six selected cases. | Correctness of all other operations or freedom from overflow. |
| Lean Analysis Proofs | Two requested statements are false under their written assumptions and intended mathematical meanings. | Source inspection and mathematical counterexamples, separately reviewed. | An installed Lean compiler result. Partial credit remains possible. |
| SMT Solver | The recovered witness lookup merges expressions from different variable scopes, so it cannot represent the distinct values needed in a constructed satisfiable case. | Source analysis and a small constructed test. | An actual full-image failure, false acceptance or score effect. Further implementation work is held. |
| FFmpeg Scaling | A recovered timing component can report a positive speed ratio for an error or missing output without checking those timed results. | Local replay with controlled substitutes. | Bypassing the task's separate correctness checks or improving real performance. Further implementation work is held. |
| College English Exam | The recovered grading/export path accepts an empty assessment or a missing required rubric entry as valid with a score of 100. | Local original-path replay with a simulated grader response. | How often a real grading provider omits entries or whether answers are educationally correct. |
| Order Addition | The original integrity test rejects its own installed scoring helper because the expected and actual hashes differ. | Original tests and matched valid/invalid controls for a small correction. | Approval of the corrected task for release. Valid original scores are still possible. |
| Jagua Nesting | The original placement validator accepts selected shapes whose interiors overlap. | Original complete placement validator on retained overlapping examples and contrasting controls. | A score gain or a complete geometry repair. Some ordinary overlaps already reject. |
| Wireless Electricity Layout | The raw scoring path ranks an observed compilation failure above an observed feasible solution. | Original grading components plus review of the final selection rule. | A normalized leaderboard gain: all three observed normalized scores were zero. |

The [recorded decisions](../evidence/selected/12-finding-decisions.json) retain the exact claims, source identities, counterexamples and accepted evidence references. [Later Wireless decision](../evidence/selected/wireless-original-exclusion.json). The [evidence index](EVIDENCE-INDEX.md) explains which records are included in Git and which remain in the local archive.
