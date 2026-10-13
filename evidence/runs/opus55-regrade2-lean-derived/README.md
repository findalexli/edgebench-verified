# opus55-regrade2-lean-derived

Not a regrade. The Lean Analysis judge image is 33 GB (the worker has 18 GB free disk) and the official judge
setting is 8 CPUs / 16 GiB (the worker has 8 GiB), so the fixed grader cannot be run here. This job extracted the
original grader's per-target verdicts (`test_output.txt`) for the 22 archived submissions and counted, for each,
the v1-credited targets that remain in the v2 target set (`v2_targets.txt`, the 2338 names in
`repairs/lean_analysis_proofs-v2/paired/out/report_v2_orig.json.gz`). On the paired controls this count equals the
v2 grader's credit exactly (T: 26 v1 → 15, equal to v2's 15); the only v2 credit it cannot see is the two corrected
statements, which an agent that saw the original statements could not have proved as written. Result:
`result/out/lean_derived.json` (counts only).
