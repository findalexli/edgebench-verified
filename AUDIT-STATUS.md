# Where the audit stands

Snapshot: **October 11, 2026, 03:00 UTC**. This page owns the current progress summary. It describes an unfinished audit, not a benchmark release.

| Review outcome for the 51 public original versions | Tasks |
| --- | ---: |
| Approved for inclusion | 0 |
| Excluded after review | 7 |
| Still awaiting a final decision | 44 |

Seven exclusions are finished decisions about the original versions. They do not require more checks to decide whether to include those same versions. A proposed replacement is a separate review.

## What changed

Compared with the last report merged into Git at 02:15 UTC, **three more original-version decisions are finished**:

- **Jagua Nesting is excluded.** The required placement validator accepts selected shapes whose interiors overlap. The decision has separate reviews; it does not prove a score gain or approve a complete geometry repair. [Accepted decision](evidence/selected/jagua-original-exclusion.json).
- **Two more original-version exclusions completed: Equivalence Classes and Graph Node Classification.** The first accepts an operation cost above its mandatory limit; the second accepts an undefined confidence value despite the required zero-to-one range. The accepted witnesses and separate reviews finish these original-version decisions; they do not establish score gains or approve replacements. [Accepted decisions](evidence/selected/eq-graph-original-exclusions.json).
- **No increase in task coverage or confirmed finding count.** Partial tests or data observations still cover 37 task IDs. Twelve specific finding decisions remain closed. Neither number means those tasks have finished review.
- **The Order and New Foundations failure reviews are complete.** Order's original-work submission reached the corrected judge, but no tests ran and no repair was validated. New Foundations stopped during preparation of the read-only filesystem, before acquiring its image or running proof helpers. Both saved failures and owned worker closures are accepted. The earlier incomplete Order output and the New Foundations preparation failure still have unresolved causes; neither establishes a new task defect. [Accepted result references](evidence/selected/EVIDENCE-MANIFEST.json).
- **An English component result was recovered:** its 22 controlled original-helper cases were completed and reviewed on October 9, so this is reused evidence and adds no new execution or coverage.
- **The saved FLT failure review is finished.** No proof helper ran. Which program received the crash signal and why remain unknown; this is a failed audit attempt, not a new task defect.

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

The [findings report](docs/FINDINGS.md) explains all twelve confirmed problems and the limits of each check. A confirmed problem can be concluded even while a repair or a broader release decision remains unfinished.

## How much checking has been done?

There are accepted **partial** test or data observations for 37 distinct tasks, including five excluded originals. Among the 44 versions still awaiting a decision:

| Existing evidence or restriction | Tasks |
| --- | ---: |
| Some accepted test or data observations | 32 |
| Formal tasks with environment/source work, but no accepted original proof-helper tests | 5 |
| Follow-up work stopped by existing review holds | 7 |

These categories account for all 44 pending tasks. Seven held tasks must remain visible; they cannot be silently removed from scope. Another 83 advertised tasks were unavailable and are outside the acquired public-task audit.

The older [51-task evidence table](evidence/selected/51-task-coverage.md) records what was checked for each task. Its original date and counts are preserved; this page includes the later Wireless, Jagua, Equivalence and Graph decisions.

## What is moving next?

Finish other supported original-version decisions from accepted evidence and advance ready original task checks. The corrected Order version and formal proof tasks still need a working original execution path; repeat a failed setup only with a specific supported correction.

We will judge throughput by new task decisions, actual task checks and newly established results. More jobs, copied reports or setup revisions do not by themselves count as audit progress.

## What does release still require?

Every task proposed for inclusion needs evidence that its specification, checker, data, execution and independent reproduction are sound. No task has cleared that full review. Excluding an original does not approve a replacement.

The complete archive remains local. The [evidence index](docs/EVIDENCE-INDEX.md) links the selected records; [VERIFICATION.md](VERIFICATION.md) gives the release requirements. The active work window ends **October 12, 2026 at 05:52:16 UTC**.
