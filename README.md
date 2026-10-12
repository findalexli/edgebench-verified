# EdgeBench Verified

An independent audit of whether EdgeBench’s tasks, tests and data measure what they promise. We are checking problems and proposed fixes against the original task formats. This private repository is a work in progress, not a released replacement benchmark.

**Saved conclusions, October 12, 2026:**

| What we know | Count |
| --- | ---: |
| Public tasks acquired | 51 |
| Tasks with confirmed findings, within the scope stated in each case | 21 |
| Original versions we would withhold from a verified release | 18 |
| Original task decisions still pending | 32 |
| Retained task versions under the maintained harness | 1 |
| Additional advertised tasks unavailable to this audit | 83 |

The [21 finding tasks](evidence/selected/finding-task-union-21.json) overlap the other rows; these counts must not be added together. A confirmed problem can be settled before its repair or the rest of the task is reviewed.

**“Excluded” means “withhold this original version unchanged.”** It does not mean deleted, worthless, impossible to score or unfixable. For example, an original checker that accepts overlapping shapes should be corrected and tested as a new version. Graph’s exclusion is a conservative policy choice about invalid confidence values; no score inflation was demonstrated. Every reason and its limits are in the findings.

## Start here

- [Findings](docs/FINDINGS.md): what went wrong, how we checked it and what each conclusion establishes.
- [Task tracker](TASKS.md): the current decision and next useful question for every public task.
- [Handoff](HANDOFF.md): where the work stands and how another contributor can continue.

## Latest completed work — October 12, 2026

**ANN is the first retained task.** Its unchanged task, evaluator and fixed corpus pass the five task-specific review requirements under the separately versioned maintained harness. The actual CLI accepted flat search at raw QPS 19 and rejected the empty control. Two different reviewers and root approved the exact bundle; the task checker has no errors. [Decision and limits](evidence/selected/ann-retain-root-review.json) · [Runnable inputs and commands](reproductions/ann-original-cli/README.md).

**Vehicle routing:** all 56 feasible route witnesses passed the actual original checker and caller. The deployed reference table had all 56 rows, with no fallback. An instruction-only clarification is prepared but not adopted; the separate decimal-boundary question remains. [Accepted result](evidence/selected/vrptw-all56-native-acceptance.json) · [Proposed clarification](reproductions/vrptw-instruction-clarification/README.md).

**Three adventure games:** six actual host sessions exercised partial/full trajectories, scores, history selection and archive transport. Anchorhead finished at 99/100 without victory; Trinity and Tryst reached their maximum scores. Their inclusion records still need final exact-bundle approvals; the native result is already accepted. [Evidence](evidence/selected/three-adventure-native-release-acceptance.json).

**Dungeon Crawl:** the clean CLI run finished all five games with scores 2, 21, 18, 7 and 14, mean 12.4. The result and cleanup are saved; independent result review and repair approval remain. [Collected result](evidence/selected/dcss-cli-result-collection.json).

Earlier completed repair checks remain available: Reporting passes the combined corrected judge (57 collected tests, 55 reported, score 1.0) plus 24 countercontrols; Tree preserves ten official cases and rejects ten missing answers; Equivalence passes one official T3 input under the disclosed 64 MiB output allowance. These are finite repair results, not completed whole-task reviews. [Findings and limits](docs/FINDINGS.md).

**The audit is not finished:** 32 original decisions remain pending, and no repaired task has final inclusion approval. All owned cloud workers are closed. Work is being handed to Claude at the user's request. The [handoff](HANDOFF.md) identifies the saved work to finish first, the interrupted reviews, and the private evidence that a clone does not contain.

## What this repository contains

Original-format task definitions, the harness, reviewed source, selected evidence and repair/reproduction packages. The [evidence index](docs/EVIDENCE-INDEX.md) identifies supporting records. Private task bodies, large images and the live cloud coordinator are not all included; a clean clone cannot yet reproduce every result. [Contributing](CONTRIBUTING.md) explains how to make a focused change.

`TASKS.md` owns current task decisions. Selected evidence and the partial `audit/task-registry.json` retain their historical dates and counts. Earlier narrative checkpoints remain in Git history; they are not additional current instructions.

The harness derives from ByteDance Seed EdgeBench at `6e4e5f4aa087a9121aa09a6059e5484e5102c6ff`; its Apache-2.0 license remains in `LICENSE`. Public task definitions derive from the Hugging Face release at `6cc5a7f1b3288ce52484ad828177b8cc86b05b75`, with a separate license in `tasks/LICENSE`. These notices do not establish redistribution rights for every dataset or dependency inside task images.
