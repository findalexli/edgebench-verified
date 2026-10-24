# Regrade of the third-party Qwen3.5-122B-A10B run: combined results

> **Raw run output is not in this repository.** The per-run directories named on this page (`../<job>/`: transcripts, submissions, judge logs, `derived.json`) were kept out to keep the repository small; this page, the table and `analysis.json` are what they reduce to.

Source: the Hugging Face dataset `adafadaq/edgebench-opus-5-5-xhigh-rollouts`, folder `qwen3.5-122b-a10b/`
(Codex scaffold, 47 tasks, 24 at 4 h and 23 at 8 h of agent time). Each worker fetched only its task's
`submissions/<round>/{submission.tar.gz,eval.sh,allowed_files.txt}` from the dataset ZIPs by HTTP range reads
(`zipfetch.py` in each job). The archive is not redistributed, and raw grader captures are moved to
`.internal/qwen35-regrade/` at collection.

Method: the same as `../opus55-regrade2-summary/`. One job per task (`../qwen35-regrade-<task>/`) grades every
recorded submission with the original judge image (pinned digest, the `FROM` of the repair Dockerfile) and then
with the fixed image (built on the worker from the repair package with `materialize.sh` and `docker build`).
Each grading is one container, `--network none --cpus 4 --memory 6g`. The archived `eval.sh` is used in both arms
because no repair changes `eval_cmd`, and the eval timeout is each version's own `eval_timeout`. A round starts
only if 1.3 times the slowest round so far still fits in the worker's budget. Rounds that do not fit are listed
as `skipped-deadline` in `progress.txt` and graded by a follow-up job.

- `collect.sh JOBDIR` checks for `status: exit=0`, grades the captures with sforge's `grade_output` and
  `rescale_score` (`grade.py`), and moves the raw captures out of the repository.
- `analyze.py OUT.json` combines all `derived.json` files with the run's recorded `run_history.json` (kept in
  `.internal/qwen35-meta/`). For each task it reports the selected run score under EdgeBench's own `select_best`
  and the task's selection policy: the original record, the v1 regrade and the v2 regrade.

The v1 regrade is the control. It must reproduce the recorded scores (exactly for deterministic graders) before
a v1/v2 difference is read as the effect of the repair.

Repairs that change only the score scale (`treant_forest`, `borden_source_inversion`) need no regrade. Their v2
score is the v2 rescale of the run's own selected raw score. These are computed for every public run that has
round histories. `rescale_runs.json` covers Opus 5.5, Qwen3.5-122B, Qwen3.8 Flash Next and three Kimi-K3 runs.
