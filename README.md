# EdgeBench Verified

An independent audit of whether EdgeBench’s tasks, tests and data measure what they promise. We are checking problems and proposed fixes against the original task formats. This private repository is a work in progress, not a released replacement benchmark.

**Saved conclusions, October 11, 2026:**

| What we know | Count |
| --- | ---: |
| Public tasks acquired | 51 |
| Tasks with confirmed findings, within the scope stated in each case | 19 |
| Original versions we would withhold from a verified release | 16 |
| Original task decisions still pending | 35 |
| Task versions approved for a verified release | 0 |
| Additional advertised tasks unavailable to this audit | 83 |

The [19 finding tasks](evidence/selected/finding-task-union-19.json) overlap the other rows; these counts must not be added together. A confirmed problem can be settled before its repair or the rest of the task is reviewed.

**“Excluded” means “withhold this original version unchanged.”** It does not mean deleted, worthless, impossible to score or unfixable. For example, an original checker that accepts overlapping shapes should be corrected and tested as a new version. Graph’s exclusion is a conservative policy choice about invalid confidence values; no score inflation was demonstrated. Every reason and its limits are in the findings.

## Start here

- [Findings](docs/FINDINGS.md): what went wrong, how we checked it and what each conclusion establishes.
- [Task tracker](TASKS.md): the current decision and next useful question for every public task.
- [Handoff](HANDOFF.md): where the work stands and how another contributor can continue.

The reporting implementation now passes the combined corrected judge: **57 collected tests passed, 55/55 reported, score 1.0**, and all 24 paired countercontrols matched. This closes the judge-repair integration check. The earlier original-judge 55 collected/53 reported run remains a separate result; neither run certifies the complete task. Details and failed hypotheses remain in [Findings](docs/FINDINGS.md) and the [reporting requirement table](docs/REPORTING-COVERAGE.md).

Two further native repair checks are complete. Tree’s corrected T2 library preserves all ten official reference cases and rejects all ten missing-answer controls before and after the fix. Equivalence’s corrected T3 checker passes one official input with a 64 MiB audit output allowance, producing 40,623,541 bytes; the earlier 16 MiB allowance blocked that input. These deepen existing repair evidence without certifying either task. [Results and limits](docs/FINDINGS.md).

**October 11, 2026, 23:21 UTC:** Molecular’s original helper accepted a solution using about 1.22 GB despite the stated 1 GB limit, in our explicitly 2 GiB audit environment. Published settings provide an aggregate 8 GiB judge limit, not the promised per-solution enforcement. This is a new scoped finding, not a repair or a claim about historical deployments. Juliet’s 736 retained records join and 723 labels match, but 18 label locations still need their original convention resolved. Vibrating’s actual tester accepted two valid tiny examples and rejected six invalid ones; the tested failure hypothesis was not confirmed. [Evidence and next questions](TASKS.md).

The 51-task audit remains unfinished because resolving one finding does not validate the rest of a task, its data or its replacement. Thirty-five original decisions remain pending; no corrected version is certified.

## What this repository contains

Original-format task definitions, the harness, reviewed source, selected evidence and repair/reproduction packages. The [evidence index](docs/EVIDENCE-INDEX.md) identifies supporting records. Private task bodies, large images and the live cloud coordinator are not all included; a clean clone cannot yet reproduce every result. [Contributing](CONTRIBUTING.md) explains how to make a focused change.

`TASKS.md` owns current task decisions. Selected evidence and the partial `audit/task-registry.json` retain their historical dates and counts. Earlier narrative checkpoints remain in Git history; they are not additional current instructions.

The harness derives from ByteDance Seed EdgeBench at `6e4e5f4aa087a9121aa09a6059e5484e5102c6ff`; its Apache-2.0 license remains in `LICENSE`. Public task definitions derive from the Hugging Face release at `6cc5a7f1b3288ce52484ad828177b8cc86b05b75`, with a separate license in `tasks/LICENSE`. These notices do not establish redistribution rights for every dataset or dependency inside task images.
