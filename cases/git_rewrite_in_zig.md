# Git Rewrite in Zig (`git_rewrite_in_zig`)

**Outcome:** Kept, with a note. A correct `git` of the matching version earns the full score through the original grader: 29,075 of 29,075 tests credited, reward 1.000000, 100 out of 100.

## What the task asks

The prompt says: "Reimplement git in Zig as a drop-in replacement for the `git` binary." The binary "must behave identically to the real `git` — same CLI interface, same output formats, same exit codes." The score is the fraction of git v2.47.0's own `t/` test suite that passes, against a fixed total of 29,075 tests. Category: Systems & Software Engineering.

## What we checked

There is no problem that changes scores enough to matter. The question is whether a correct implementation can actually earn full credit through the original scoring path. It can.

| Run | Test scripts run | Passed (credited) | Failed | Skipped | Reward / TOTAL_SCORE | Score out of 100 (linear from 0–1) | Wall time |
|---|---|---|---|---|---|---|---|
| t0001 only | 1007 (1006 skipped whole) | 86 | 0 | 5 | 0.002958 | 0.30 | 29 s |
| full suite | 1007 | **29,075** | **0** | 1,177 | **1.000000** | **100** | 155 s |

- In the full run, each category's pass count equals the fixed `oracle_attempted` baseline in the grader exactly: t0 5379, t1 3191, t2 980, t3 4778, t4 3485, t5 4540, t6 2355, t7 2912, t8 493, t9 962. The total of 29,075 can be reached exactly, at least on an 8-core host.
- No script hit the 120 s per-script timeout at nproc=8.
- 147 scripts had no `ok` line. These skipped themselves because a prerequisite was missing, for example "Cannot run httpd tests as root", "skipping Windows-specific tests" and "GIT_TEST_ALLOW_SUDO".

Notes that ship with the task:

- The prompt does not describe the scoring method (the git `t/` suite, counted per test).
- A real Zig submission must also provide `--exec-path` and the helper programs itself. The prompt does not state this.
- The per-script timeout (120 s) depends on the host. Behavior with fewer cores was not measured.

## How much it matters

No score effect was found for a correct implementation on an 8-core host. The timeout note could affect solvers only on graders with fewer cores; that effect is not measured.

There is no code change. The note above ships with the task.

## How we checked it

- **Original grader in the pinned image.** A real git v2.47.0 was built inside the grader image (with `--network none`). It was built from the scorer's own test-suite source tree, with the same make flags as `test.sh`: `make -j8 NO_TCLTK=1 NO_EXPAT=1 NO_GETTEXT=1 prefix=/opt/realgit install`. It reports `git version 2.47.0`.
- The binaries were placed in `/home/workspace/zig-port/zig-out/bin/`. They were scored in a fresh container (`--network none --cpus 8 --memory 6g`) with the grader's eval_cmd word for word, the shipped `test.sh`, the git `t/` suite, `compute_reward.py` and `pytest_shim.sh`.
- The run used the harness's own `HARBOR_ORACLE_MODE=1`. This mode skips the checks on the submission and the build step. Running the tests and computing the reward are identical to the scored path. The stand-in git carries its own exec-path under `/opt/realgit`, so it never relied on the system git that the normal path deletes.

## Limits

- No AI model or solver was run. The result rests on one correct test submission.
- The stand-in is C git, run in oracle mode. It is not a Zig binary going through the normal build path.
- One run on one 8-core host. Timing with other core counts was not tested.

## Reproduce

- Grader image: `sha256:645bc84baa85…`.
- `evidence/runs/git_rewrite_in_zig-oraclefull/run.sh` (full suite) and `evidence/runs/git_rewrite_in_zig-oraclet0001/run.sh` (t0001 only). They need a Docker host that can pull the pinned image. Outputs are in each folder's `result/`.
- Review: `evidence/reviews/git_rewrite_in_zig-native.md`.
