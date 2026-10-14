# Regrading real agent submissions

**Superseded in scope by the second regrade:** `../opus55-regrade2-summary/` (all 7 fixed tasks whose fix
changes only the grader, 314 submissions, 349 paired gradings with repeats, at the official 4 CPUs). This folder
keeps the first, smaller regrade (two tasks, five submissions) described below.

Source: a third-party run of Claude Opus 5.5 on 16 public EdgeBench tasks, 4 hours each, published at
`huggingface.co/datasets/adafadaq/edgebench-opus-5-5-xhigh-rollouts` (archive sha256 in
`result/out/archive.sha256`). The archive is downloaded on the cloud worker and is not redistributed here.

`run.sh` regrades real submissions with the original grader (pinned public image) and the fixed grader
(rebuilt on the worker with each package's `materialize.sh`; the job copied `repairs/integer_compression_codec-v2`
and `repairs/order_addition_permutation_optimization-v2` from this repository into `repairs/`). Every grading uses
the submission's own recorded `eval.sh` and `judge_one.sh`, with `--network none`.

| Task | Submission | Original grader | Fixed grader |
| --- | --- | --- | --- |
| Integer Codec | agent-20 (the run's best) | raw 66.31 | raw 160.76 (50.08 on the fixed 1.0..320 scale) |
| Integer Codec | agent-3 | raw 31.11 | raw 114.19 (35.48) |
| Order Addition | agent-1, auto-6, agent-2 | 4 of 5 tests each (stale checksum) | 5 of 5 tests each |

This is the first regrade: two Integer Codec submissions, each graded once on one machine ("the run's best"
means best by the run's recorded score). The second regrade (`../opus55-regrade2-summary/summary.json`) graded
all 37 Integer Codec submissions, the top 6 three times; it gives the figure we cite for the run, 75.72 (recorded)
→ 53.95 on the fixed scale (best submission agent-26). agent-20's 160.76 here lies inside its second-regrade range.

Raw outputs: `result/out/logs/`. The run's own submission histories for all seven fixed tasks are summarised in
`../opus55-rollouts-meta/submission-histories.json`.
