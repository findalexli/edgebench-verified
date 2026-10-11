# Where the audit stands

Snapshot: **October 11, 2026, 04:12 UTC**. This page owns the current progress summary. It describes an unfinished audit, not a benchmark release.

| Review outcome for the 51 public original versions | Tasks |
| --- | ---: |
| Approved for inclusion | 0 |
| Excluded after review | 9 |
| Still awaiting a final decision | 42 |

Nine exclusions are finished decisions about the original versions. They do not require more checks to decide whether to include those same versions. A proposed replacement is a separate review.

## What changed

Compared with the report at 03:54 UTC, **one more original-version decision is finished**:

- **College English Exam is excluded.** The final supplied grader requires an assessment for every grading rule, but its code can report completed grading when none was assessed. A different reviewer checked the final source and challenged that conclusion. The decision assumes a successfully loaded nonempty rubric and a successfully parsed response; it does not claim a live provider failure or a 100-point result from the final grader. [Accepted decision](evidence/selected/english-original-exclusion.json).
- **No increase in task coverage or confirmed finding count.** Partial tests or data observations still cover 37 task IDs. Twelve specific finding decisions remain closed. Neither number means those tasks have finished review.
- **Tree's exclusion remains finished.** It was recorded in the preceding update from accepted before/after controls and separate reviews. The official reference avoids the affected use; no complete-task score effect is claimed. [Accepted decision](evidence/selected/tree-original-exclusion.json).
- **Schemathesis's finding remains confirmed, while its task decision stays pending.** A different reviewer confirmed that the saved wrapper passed tests despite violating the required function identity. Its complete scoring path was not observed, so that evidence does not justify claiming the whole task accepted it.
- **The latest Order repair attempt remains a failed attempt.** The corrected grader reported zero test cases; the reviewed worker is closed. No repair was validated and the precise cause is unknown. [Accepted failure](evidence/selected/order-repair-failed-pilot.json).

These are changes over this specific interval, not claims about a whole day's throughput.

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
| College English Exam | Excluded | The final supplied grader can report completed grading without the required per-rule assessments. This is a source-backed decision, not a live final-grader run. |

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
