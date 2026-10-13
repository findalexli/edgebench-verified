# treant_forest-cpu4v8-b

CPU-quota measurement (4 vs 8 grader CPUs) on the original, digest-pinned grader, 2026-10-13 UTC.
E2B job `cpu4v8-treant-b` (ledger name in `evidence/runs/ledger.jsonl`; sandbox `i1vzgr2baktlczhzngo57`,
`status: exit=0`, worker killed; `result/worker.json`). This directory holds the `treant` arms of that job: `run.sh` and `arms.txt`
are the job's own files, unchanged (they list every task the job ran); `result/out/summary.txt` is the job's full summary;
`logs/`, `timing/` are filtered to this task.
The `docs/` excerpts (grep lines from the image README and grader) are kept out of Git, in
`.internal/evidence/runs/treant_forest-cpu4v8-b/`. Results and method: `cases/treant_forest.md` and the repair package, if any.
