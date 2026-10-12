# Paired v1/v2 results: equivalence_class_divide_and_conquer

- **Job:** one E2B worker (8 CPU). Job ID `equivalence_class_divide_and_conquer-v2-paired`,
  sandbox `ig1n2jrfsp43bqudz7vh3`. It exited 0 after 463 s and was killed after collection.
- **Images:** v1 is the pinned `seededge/edgebench.judge.equivalence_class_divide_and_conquer@sha256:f793d805…e767e6`
  (checker `f92b52cc…4145`). v2 was built in the worker from `../Dockerfile`, image ID
  `sha256:21182791…19dc` (checker `14734cf3…299e`).
- **Command:** every arm ran the original evaluator,
  `cd /home/workspace/p2 && python3 /opt/p2_judge/prob/P2/eval.py --source-root /home/workspace/p2 --time-factor 1 --time-grace 0 --score-sum`,
  inside `--network none --memory 3g --cpus 3`.
  - The reference and naive arms used it exactly as given, grading all six subtasks.
  - The crafted arms appended `--task T3 --case 31 -v`, with the crafted input bind-mounted as
    `T3_P8204/data/31.in` and an empty `31.ans`.
  - The reference v1 and v2 runs ran at the same time (2 × 3 CPUs on 8). Every other arm ran on
    its own.
- **Scores:** raw score is `TOTAL_SCORE`. Normalized score comes from `score_rescale` linear 0..100.
  Pass rate is score_sum units.
- **Native limits:** `ulimit -f` is unlimited in both images (`evidence/checker_sha_and_limits.txt`).

| Arm | Submission / input | v1 | v2 | Expected |
|---|---|---|---|---|
| **Trigger** | `naive.cpp` on crafted B (star, n=10⁶, m=2501; true cost 2.501·10⁹ > limit) | **AC**, raw 10 (T3 1/1) | **WA "Operation cost exceeded"**, raw 0 | v1 wrong, v2 right ✔ |
| At-limit control | `naive.cpp` on crafted A (m=2500; true cost exactly 2.5·10⁹) | AC, raw 10 | AC, raw 10 | accept both ✔ |
| **Valid control (whole task)** | official `std.cpp` for T1–T6 | **raw 100 / norm 100**; T1 5/5, T2 10/10, **T3 30/30**, T4 25/25, T5 20/20, T6 30/30; exit 0; pass rate 1.000 | **raw 100 / norm 100**; identical per-subtask counts; exit 0; pass rate 1.000 | unchanged ✔ |
| Invalid control | `naive.cpp` as T3, others empty, on the 30 official inputs | raw 1 / norm 1; T3 6 AC / **24 WA** (cost exceeded); exit 1; pass rate 0.020 | raw 1 / norm 1; the same 6 AC / 24 WA, case by case; exit 1; pass rate 0.020 | rejected both ✔ |

**Checker run directly** on all crafted outputs, compiled as `compile_checker` does
(`evidence/checker_direct.txt`):

| Case | v1 | v2 |
|---|---|---|
| A at limit | ok | ok |
| B over by n | **ok** | **WA** |
| C over by 2n | WA | WA |
| D (B plus a trailing free move) | WA | WA |
| E efficient | ok | ok |

**64 MiB question.** It was an audit artefact. Under the native evaluator, with no limits
changed, the reference passes all 30 official T3 inputs in both v1 and v2. Those inputs include
case 24, whose output is about 40.6 MB and exceeds the earlier audit's 16 MiB file cap.

**Verdict: accepted.** The trigger is fixed, the at-limit case and the whole-task reference score
are unchanged (100 → 100, T3 30/30), and the invalid naive cases are rejected by both versions.

**Evidence** (`evidence/`): `summary.txt`, `summary_parsed.txt`, `logs/*.log`, `inputs_sha.txt`,
`checker_direct.txt`, `checker_sha_and_limits.txt`, `build.log`, `worker.json`.
