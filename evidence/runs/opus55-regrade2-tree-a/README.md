# opus55-regrade2-tree-a

Tree Block Partitioning, rep 1 of 7 submissions (best, final and one per distinct original score; the rest in tree-b).

Part of the second regrade of the third-party Claude Opus 5.5 run (archive sha256 `61c05f73…2613`, downloaded on
the worker and not redistributed). `run.sh` grades each line of `plan.txt` (`task round rep`) with the original
judge image (pinned digest) and then the fixed image (built on the worker with the package's `materialize.sh` and
`docker build`), one container at a time, `--network none --cpus 4 --memory 6g` (official `judge_cpu_limit: 4`;
6 GiB instead of 8 because the worker has 8 GiB). `judge.sh` reproduces sforge `judge_submission`: it extracts
exactly the archived `allowed_files.txt` from the archived `submission.tar.gz` and runs the archived `eval.sh`.

Kept here: `result/out/derived.json` (scores, verdicts, wall times, submission and capture sha256, graded offline
with this repository's sforge `grade_output` and `rescale_score`), image IDs, logs, `progress.txt`, and
`result/worker.json` (`status: exit=0`). Raw grader captures were moved to `.internal/opus55-regrade2/tree-a/`.
The repair package copied into `pkg/` for the run was removed after collection. Combined results:
`../opus55-regrade2-summary/`.
