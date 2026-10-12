# Evidence

This folder holds the raw material behind every claim on the case pages. It is written for people
who want to check or rerun a result. The readable account of each task is on its case page in
[`../cases/`](../cases/INDEX.md).

| Folder | What it holds |
| --- | --- |
| [`reviews/`](reviews/) | Detailed technical reviews, one per task or task family. They are working analyses, written with the grader's code open, and use its internal terms. |
| [`scripts/`](scripts/) | The test submissions and checking scripts used for each task, grouped by task |
| [`formal/`](formal/) | Machine-checked results. `lean/` holds Lean 4 proofs with their recorded output, and `tla/` holds TLA+ models with their model-checker output. [`formal/RECHECK.md`](formal/RECHECK.md) logs a full rerun. |
| [`runs/`](runs/) | Logs and results of every grading run on cloud machines, one folder per job, plus `ledger.jsonl`, the record of every machine started and stopped |
| [`impact/`](impact/) | Inputs for the leaderboard estimate in [`../IMPACT.md`](../IMPACT.md): the published per-task scores and the direction and size of each fix's effect |

Some reviews cite documents from the earlier automated audit, such as `VERIFICATION.md`. Those are
preserved at Git tag `earlier-audit-final`. The outcomes published here are in
[`../data/decisions.json`](../data/decisions.json).

Terms used in the technical files:

| Term | Meaning |
| --- | --- |
| v1 | the original task and grader |
| v2 | the fixed version |
| judge | the grader |
| work image | the environment and starter files the agent receives |
| rescale, anchors | the conversion of a raw result to a 0–100 score, and its reference points |
| arm, control, trigger | one test submission; a correct or wrong test submission; the submission that shows the problem |
| paired run | the same test submissions graded by the original and the fixed grader |
