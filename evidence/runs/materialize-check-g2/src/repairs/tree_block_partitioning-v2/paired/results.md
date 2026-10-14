# Paired v1/v2 results: tree_block_partitioning

- **Job:** one E2B worker (8 CPU, 7.9 GB). Job ID `tree_block_partitioning-v2-paired`, sandbox
  `i4u41fnx9eeubs7znp1ce`. It exited 0 after 322 s and was killed after collection.
- **Images:** v1 is the pinned `seededge/edgebench.judge.tree_block_partitioning@sha256:6ebbb44a…69d2`.
  v2 was built in the worker from `../Dockerfile`, image ID `sha256:a6439e39…fb23`.
- **Library hashes in the containers:** v1 `0c57271b…c982`, v2 `26c4edc6…e2ea`
  (`evidence/lib_sha.txt`).
- **Command:** every arm ran the original `eval_cmd`, which grades all six subtasks:
  `cd /home/workspace/p1 && python3 /opt/p1_judge/prob/P1/eval.py --source-root /home/workspace/p1 --time-factor 1 --time-grace 0 --score-sum`.
  Containers used `--network none --memory 4g --cpus 2` and ran one at a time. Submission files
  were bind-mounted over `/home/workspace/p1/T{1..6}.cpp`.
- **Scores:** raw score is `TOTAL_SCORE` (read with `sforge.harness.grading.extract_score`).
  Normalized score comes from `score_rescale` linear 0..100. Pass rate is the passing score_sum
  units (`parse_score_sum`) out of 7200.

| Arm | Submission | v1 raw / norm | v2 raw / norm | v1 → v2 per subtask (T1..T6 cases passed) | Exit v1/v2 | Pass rate v1 → v2 |
|---|---|---|---|---|---|---|
| Valid control | Official `std.cpp` for all six subtasks | **100 / 100** | **100 / 100** | 45/45, 10/10, 20/20, 10/10, 40/40, 10/10 in both | 0/0 | 1.000 → 1.000 |
| Trigger | T2 = alias variant of `std.cpp` (`make_alias_variant.py`); T1, T3–T6 empty | **0.25 / 0.25** (T2 1/10) | **5 / 5** (T2 10/10) | T2 1/10 → 10/10; all others 0 (empty) | 1/1 | 0.005 → 0.050 |
| Invalid control | T2 = `std.cpp` with the second merge factor dropped (`make_invalid_variant.py`); others empty | **0.25 / 0.25** (T2 1/10, 9 WA) | **0.25 / 0.25** (T2 1/10, 9 WA) | unchanged | 1/1 | 0.005 → 0.005 |

**Reading the table.**
- Whole-task parity holds for the reference: 100 → 100, with every case in T1–T6 passing under
  both versions.
- The contract-valid alias variant goes from 0.25 to 5.00 on T2.
- The ordinary wrong submission is rejected the same way by both versions. Case 1 has no block
  merges, so every variant passes it.
- The exit code is 1 whenever any case fails, as in the original evaluator.
- The earlier missing-answer control was replaced by this logic-error control, which actually
  exercises the merge path.

**Verdict: accepted.** The trigger is fixed, the reference score is unchanged across all six
subtasks, and the invalid control is rejected by both versions.

**Evidence** (`evidence/`): `summary.txt`, `summary_parsed.txt` (produced by `summarize.py`),
`logs/*.log` (full evaluator output), `submissions_sha.txt`, `lib_sha.txt`, `build.log`,
`worker.json`.
