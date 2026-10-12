# Git Rewrite in Zig (`git_rewrite_in_zig`)

**Decision:** Retain with note. A correct, version-matched `git` earns the full score through the original test path: 29,075 of 29,075 tests credited, reward 1.000000, normalized 100.

## What the task asks for

"Reimplement git in Zig as a drop-in replacement for the `git` binary." The binary "must behave identically to the real `git` — same CLI interface, same output formats, same exit codes." The score is the fraction of git v2.47.0's own `t/` test suite that passes, against a fixed denominator of 29,075. Category: Systems & Software Engineering.

## What goes wrong

There is no material defect. The question checked was whether a correct implementation can actually earn full credit through the original scoring path. It can.

| run | scripts run | ok (credited) | not ok | skipped | reward / TOTAL_SCORE | normalized (linear 0–1) | wall |
|---|---|---|---|---|---|---|---|
| t0001 only | 1007 (1006 skipped wholesale) | 86 | 0 | 5 | 0.002958 | 0.30 | 29 s |
| full suite | 1007 | **29,075** | **0** | 1,177 | **1.000000** | **100** | 155 s |

- In the full run, each per-category pass count equals the hard-coded `oracle_attempted` baseline exactly: t0 5379, t1 3191, t2 980, t3 4778, t4 3485, t5 4540, t6 2355, t7 2912, t8 493, t9 962. The 29,075 denominator is achievable exactly, at least on an 8-core host.
- No script hit the 120 s per-script timeout at nproc=8.
- 147 scripts had no `ok` line. These are prerequisite skips such as "Cannot run httpd tests as root", "skipping Windows-specific tests" and "GIT_TEST_ALLOW_SUDO".

Notes that ship with the task:

- The prompt does not describe the scoring method (the git `t/` suite, counted per test).
- A real Zig submission must also provide `--exec-path` and helper binaries itself. The prompt does not state this.
- The per-script timeout (120 s) depends on the host. Behavior at lower core counts was not measured.

## Impact

No score effect was found for a correct implementation on an 8-core host. The timeout note could affect solvers only on judges with fewer cores; that effect is not measured.

## Fix (v2)

No change; the note above ships with the task.

## How we know

- **Original evaluator in the pinned image.** A real git v2.47.0 was built inside the judge image (`sha256:645bc84baa85…`, `--network none`) from the scorer's own test-suite source tree, with the same make flags as `test.sh`: `make -j8 NO_TCLTK=1 NO_EXPAT=1 NO_GETTEXT=1 prefix=/opt/realgit install`. It reports `git version 2.47.0`.
- The binaries were placed in `/home/workspace/zig-port/zig-out/bin/` and scored in a fresh container (`--network none --cpus 8 --memory 6g`) with the verbatim eval_cmd, the shipped `test.sh`, the git `t/` suite, `compute_reward.py` and `pytest_shim.sh`.
- The run used the harness's own `HARBOR_ORACLE_MODE=1`. This mode skips the submission screens and the build step. Test execution and reward computation are identical to the scored path. The stand-in carries its own exec-path under `/opt/realgit`, so it never relied on the system git that the normal path deletes.

## Limits

- No model or solver runs. The result rests on one positive control.
- The stand-in is C git, run through oracle mode. It is not a Zig binary going through the normal build path.
- One run on one 8-core host. Timing at other core counts was not tested.

## Reproduce

- `evidence/runs/git_rewrite_in_zig-oraclefull/run.sh` (full suite) and `evidence/runs/git_rewrite_in_zig-oraclet0001/run.sh` (t0001 only). They need a Docker host that can pull the pinned image. Outputs are in each folder's `result/`.
- Review: `evidence/reviews/git_rewrite_in_zig-native.md`.
