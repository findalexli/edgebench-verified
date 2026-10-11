# Where the audit stands

Snapshot: **October 11, 2026, 05:02 UTC**. This page owns the current progress summary. It describes an unfinished audit, not a benchmark release.

| Review outcome for the 51 public original versions | Tasks |
| --- | ---: |
| Approved for inclusion | 0 |
| Excluded after review | 9 |
| Still awaiting a final decision | 42 |

Nine exclusions are finished decisions about the original versions. They do not require more checks to decide whether to include those same versions. A proposed replacement is a separate review.

## What changed

Since the 04:12 UTC snapshot, five sets of new checks were accepted and one completed scoring result was recovered. **The totals remain nine excluded originals, 42 pending tasks, zero certified tasks, 37 task IDs with partial observations and twelve closed finding decisions.** These results add detail; they do not add newly checked task IDs or new findings.

- **The English completeness repair passed four offline full-grader calls.** With fixed model responses and a controlled rubric, a complete partial assessment stayed byte-identical at valid 96. Omitting one required assessment gave valid 96 in the final supplied original source and invalid 0 in the candidate. This validates the versioned correction on that source path. It does not approve a replacement task, establish installed-image parity or measure a live grader. The original exclusion stands. [Accepted repair check](evidence/selected/english-final-source-repair.json).
- **VLIW passed nine fresh seed cases using the original source-copy runner.** A separate arithmetic derivation agreed with the reference's final value and index hashes. Machine final indices were not checked, and this local run establishes no physical speed or calibration claim. [Accepted checks](evidence/selected/vliw-fresh-nine-local.json).
- **Selected Schemathesis data were consistent.** Eight response labels, four generation pairs and two reference locations passed the finite checks; no selected-fixture defect was found. This is not a whole-corpus, standards or rights conclusion. [Accepted data check](evidence/selected/schemathesis-selected-fixture-data.json).
- **Schemathesis Config's complete scoring path was recovered, not rerun.** Reference and the same identity-violating wrapper had already completed 126 original outcomes each: both passed 22, including 15/15 metric checks, and received the same partial score 0.135313. The missing identity check is confirmed and needs a versioned repair; there is no observed wrapper score gain or automatic exclusion. Actual submission-history selection remains unobserved. [Accepted recovery](evidence/selected/schemathesis-full-consumer-recovery.json).

The Bipedal 20-episode result is an older accepted result already represented in the evidence table; it adds no new episodes in this interval. The latest reviewed Order repair attempt still ran zero checker cases and validated no repair. [Accepted failure](evidence/selected/order-repair-failed-pilot.json).

Addendum: **October 11, 2026, 04:59 UTC**. Two later results are accepted. The original Molecular Self-Assembly tester accepted the authored tick 999 completion with score 24,789,550 and rejected tick 1000 before scoring; the coincident, stationary coordinates do not establish realistic molecular behavior. The Schemathesis Config correction adds a required identity test while preserving partial credit. Four fresh source-component controls kept behavior, registration and cleanup intact: the reference returned the required identity twice, while the wrapper failed identity twice. Earlier native 16/16 reference versus 15/16 wrapper results are reused, not rerun; no derived-image or replacement certification is claimed. [Molecular controls](evidence/selected/molecular-final-tick-local.json); [Schemathesis repair](evidence/selected/schemathesis-config-identity-repair.json).

Across this update there are **19 new execution cases**: four English original/candidate calls, nine VLIW source-copy cases, two Molecular original-tester controls and four Schemathesis source-component controls. The eight labels, four generation pairs and two references are separate data diagnostics. The recovered Schemathesis 126-outcome runs and older Bipedal 20 episodes add no new execution. Counts remain **nine excluded, 42 pending, 37 task IDs with partial observations, twelve closed finding decisions and zero certified tasks**. These are additional checks on existing tasks, not 19 complete task reviews.

## Which decisions are finished?

| Original task version | Conclusion | Decisive reason |
| --- | --- | --- |
| Triangulation Coloring | Excluded | All ten acquired large meshes contain overlapping triangle interiors, contrary to the promised input structure. |
| Lean Analysis Proofs | Excluded | Two required statements are mathematically false under their stated assumptions and intended meanings. This is a mathematical refutation, not a Lean compiler result. |
| Order Addition | Excluded | The original integrity test rejects its own installed scoring helper. A small correction passed the selected controls; the corrected version still needs its own review. |
| Wireless Electricity Layout | Excluded | The raw scoring path prefers an observed compilation failure over an observed feasible solution. |
| Jagua Nesting | Excluded | The required placement validator accepts selected overlapping interiors. |
| Equivalence Classes | Excluded | A mandatory operation-cost check accepts output above the stated limit. |
| Graph Node Classification | Excluded | The required confidence-range check accepts an undefined numeric value. |
| Tree Block Partitioning | Excluded | The supplied multiplication operation violates the unrestricted value behavior stated in the task. |
| College English Exam | Excluded | The final supplied grader can report completed grading without the required per-rule assessments. Later offline calls check a versioned correction on that supplied source. |

The [findings report](docs/FINDINGS.md) explains all twelve confirmed problems and the limits of each check. A confirmed problem can be concluded even while a repair or a broader release decision remains unfinished.

## How much checking has been done?

There are accepted **partial** test or data observations for 37 distinct tasks, including seven excluded originals. Among the 42 versions still awaiting a decision:

| Existing evidence or restriction | Tasks |
| --- | ---: |
| Some accepted test or data observations | 30 |
| Formal tasks with environment/source work, but no accepted original proof-helper tests | 5 |
| Follow-up work stopped by existing review holds | 7 |

These categories account for all 42 pending tasks. Seven held tasks must remain visible; they cannot be silently removed from scope. Another 83 advertised tasks were unavailable and are outside the acquired public-task audit.

The older [51-task evidence table](evidence/selected/51-task-coverage.md) records what was checked for each task. Its original date and counts are preserved; this page includes the later Wireless, Jagua, Equivalence, Graph, Tree and English decisions.

## What is moving next?

Finish other supported original-version decisions from accepted evidence and advance ready original task checks. The corrected Order version and formal proof tasks still need a working original execution path; repeat a failed setup only with a specific supported correction.

We will judge throughput by new task decisions, actual task checks and newly established results. More jobs, copied reports or setup revisions do not by themselves count as audit progress.

## What does release still require?

Every task proposed for inclusion needs evidence that its specification, checker, data, execution and independent reproduction are sound. No task has cleared that full review. Excluding an original does not approve a replacement.

The complete archive remains local. The [evidence index](docs/EVIDENCE-INDEX.md) links the selected records; [VERIFICATION.md](VERIFICATION.md) gives the release requirements. The active work window ends **October 12, 2026 at 05:52:16 UTC**.
