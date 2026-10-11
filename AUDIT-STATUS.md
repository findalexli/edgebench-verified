# Where the audit stands

Snapshot: **October 11, 2026, 02:15 UTC**. This page owns the current progress summary. It describes an unfinished audit, not a benchmark release.

| Review outcome for the 51 public original versions | Tasks |
| --- | ---: |
| Approved for inclusion | 0 |
| Excluded after review | 4 |
| Still awaiting a final decision | 47 |

Four exclusions are finished decisions about the original versions. They do not require more checks to decide whether to include those same versions. A proposed replacement is a separate review.

## What changed

Compared with the previous Git snapshot at 01:22 UTC:

- **One more exclusion completed: Wireless Electricity Layout.** The original scoring path ranked an observed compilation failure above an observed feasible solution. All observed normalized scores were zero, so we have not shown a leaderboard gain. [Accepted decision](evidence/selected/wireless-original-exclusion.json).
- **No increase in task coverage or confirmed finding count.** Partial tests or data observations still cover 37 task IDs. Twelve specific finding decisions remain closed. Neither number means those tasks have finished review.
- **The FLT formal-task attempt failed before proof checks.** Restoring the selected environment succeeded, but the version-check process crashed. No original proof helper ran. The worker was closed; which program received the signal and why are unknown. Independent review of the saved result is still pending at this snapshot. This is a problem with our audit setup, not a new task defect.

These are changes over this specific interval, not claims about a whole day's throughput.

## Which decisions are finished?

| Original task version | Conclusion | Decisive reason |
| --- | --- | --- |
| Triangulation Coloring | Excluded | All ten acquired large meshes contain overlapping triangle interiors, contrary to the promised input structure. |
| Lean Analysis Proofs | Excluded | Two required statements are mathematically false under their stated assumptions and intended meanings. This is a mathematical refutation, not a Lean compiler result. |
| Order Addition | Excluded | The original integrity test rejects its own installed scoring helper. A small correction passed the selected controls; the corrected version still needs its own review. |
| Wireless Electricity Layout | Excluded | The raw scoring path prefers an observed compilation failure over an observed feasible solution. |

The [findings report](docs/FINDINGS.md) explains all twelve confirmed problems and the limits of each check. A confirmed problem can be concluded even while a repair or a broader release decision remains unfinished.

## How much checking has been done?

There are accepted **partial** test or data observations for 37 distinct tasks, including two excluded originals. Among the 47 versions still awaiting a decision:

| Existing evidence or restriction | Tasks |
| --- | ---: |
| Some accepted test or data observations | 35 |
| Formal tasks with environment/source work, but no accepted original proof-helper tests | 5 |
| Follow-up work stopped by existing review holds | 7 |

These categories account for all 47 pending tasks. Seven held tasks must remain visible; they cannot be silently removed from scope. Another 83 advertised tasks were unavailable and are outside the acquired public-task audit.

The older [51-task evidence table](evidence/selected/51-task-coverage.md) records what was checked for each task. Its original date and counts are preserved; this page includes the later Wireless decision.

## What is moving next?

Finish Jagua's original-version decision from the evidence and separate reviews already collected. Check that the proposed Order correction works through the real submission process. Keep other ready task checks moving while formal-tool startup problems are diagnosed. These are separate lanes; a setup failure in one must not stop the others.

We will judge throughput by new task decisions, actual task checks and newly established results. More jobs, copied reports or setup revisions do not by themselves count as audit progress.

## What does release still require?

Every task proposed for inclusion needs evidence that its specification, checker, data, execution and independent reproduction are sound. No task has cleared that full review. Excluding an original does not approve a replacement.

The complete archive remains local. The [evidence index](docs/EVIDENCE-INDEX.md) links the selected records; [VERIFICATION.md](VERIFICATION.md) gives the release requirements. The active work window ends **October 12, 2026 at 05:52:16 UTC**.
