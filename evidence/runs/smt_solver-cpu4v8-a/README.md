# smt_solver-cpu4v8-a

CPU-quota measurement (4 vs 8 grader CPUs) on the original, digest-pinned grader, 2026-10-13 UTC.
E2B job `cpu4v8-smt-a` (ledger name in `evidence/runs/ledger.jsonl`; sandbox `iraan0bw9kae3qvk5cxdx`,
`status: exit=0`, worker killed; `result/worker.json`). This directory holds all arms of that job: `run.sh` and `arms.txt`
are the job's own files, unchanged; `result/out/summary.txt` is the job's full summary;
`logs/`, `timing/`, `json/` are filtered to this task.
The `docs/` excerpts (grep lines from the image README and grader) are kept out of Git, in
`.internal/evidence/runs/smt_solver-cpu4v8-a/`. Results and method: `cases/smt_solver.md` and the repair package, if any.
