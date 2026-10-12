# Git Rewrite in Zig (`git_rewrite_in_zig`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Systems & Software Engineering
- **Decision:** Retain with note. The prompt does not explain how scoring works, and the 120 s per-script timeouts were only tested on 8 cores. A correct, version-matched `git` earns the full score through the original test path: 29,075 of 29,075 tests credited, reward 1.000000, normalized 100.

## What the task promises

"Reimplement git in Zig as a drop-in replacement for the `git` binary." The binary "must behave identically to the real `git` — same CLI interface, same output formats, same exit codes." The score is the fraction of git v2.47.0's own `t/` test suite that passes, against a fixed denominator of 29,075.

## What we checked and how

- **Question:** does a correct implementation actually earn credit through the original verifier path? Before this check, no positive control existed.
- **Stand-in:** a real git v2.47.0, built inside the judge image (`--network none`) from the scorer's own test-suite source tree. The build used the same make flags as `test.sh` Step 3: `make -j8 NO_TCLTK=1 NO_EXPAT=1 NO_GETTEXT=1 prefix=/opt/realgit install`. `/opt/realgit/bin/git --version` reports `git version 2.47.0`.
- **Scoring:** a fresh container (`--network none --cpus 8 --memory 6g`). The stand-in binaries were copied into `/home/workspace/zig-port/zig-out/bin/`, the harness's own `HARBOR_ORACLE_MODE=1` was set, and the verbatim eval_cmd from the task JSON was run. This used the shipped `test.sh`, the git `t/` suite, `compute_reward.py` and `pytest_shim.sh`.
- Two runs on 8-vCPU E2B workers: a t0001-only run (using git's own `GIT_SKIP_TESTS`) and a full-suite run. A first full-suite attempt failed in the build step because it built from a source tree without `t/`. That was a setup error and produced no measurement.
- Original identity: judge image `seededge/edgebench.judge.git_rewrite_in_zig@sha256:645bc84baa85…`; task JSON sha256 `6ae15eab2468…`; key files in `/opt/tests`: `test.sh` `c2e6d4469213…`, `compute_reward.py` `28eea3d67e5b…`, `pytest_shim.sh` `6e38e136602a…`, `git-test-suite.tar.gz` (v2.47.0 source with `t/`) `6d0f5c98d015…`.

## What we found

**Confirmed: the scoring path credits a correct implementation fully.**

| run | scripts run | ok (credited) | not ok | skipped | reward / TOTAL_SCORE | normalized (linear 0–1) | wall |
|---|---|---|---|---|---|---|---|
| t0001 only | 1007 (1006 skipped wholesale) | 86 | 0 | 5 | 0.002958 | 0.30 | 29 s |
| full suite | 1007 | **29,075** | **0** | 1,177 | **1.000000** | **100** | 155 s |

- In the full run, each per-category pass count equals the hard-coded `oracle_attempted` baseline exactly: t0 5379, t1 3191, t2 980, t3 4778, t4 3485, t5 4540, t6 2355, t7 2912, t8 493, t9 962. The 29,075 denominator is therefore achievable exactly, at least on an 8-core host.
- No script hit the 120 s per-script timeout at nproc=8.
- 147 scripts had no `ok` line. These are prerequisite skips such as "Cannot run httpd tests as root", "skipping Windows-specific tests" and "GIT_TEST_ALLOW_SUDO".
- An earlier result, not re-run here, recorded that the shipped stub baseline scores 0; that record is not among the saved evidence here.
- Scorer isolation is outside this release's scope (EdgeBench design choice); no good-faith scoring defect was found.

**How faithful the stand-in is.** Oracle mode is the harness's own path. It skips the submission screens and the build: anti-cheat, the zig build, the strace check, the deletion of system git, and the `/tmp` wipe. Test execution and reward computation are identical to the scored path. The stand-in carries its own exec-path under `/opt/realgit`, so it never relied on the system git that the non-oracle path deletes.

## Note for users

No repair. The decision carries no formal note. The review records these observations for readers:

- A real Zig submission must also provide `--exec-path` and helper binaries itself. The prompt does not state this requirement.
- The prompt does not describe the scoring method (the git `t/` suite, counted per test).
- Per-script timeouts (120 s) are host-dependent. Behavior at lower core counts was not measured.

## Limits and what was not run

- No model or solver re-runs. The effect is shown on one authored positive control only.
- The stand-in is C git, used through oracle mode. It is not a Zig binary going through the non-oracle build path.
- One run on one 8-core host. Timing sensitivity at other core counts was not tested.

## Reproduce

- `evidence/runs/git_rewrite_in_zig-oraclefull/run.sh` (full suite) and `evidence/runs/git_rewrite_in_zig-oraclet0001/run.sh` (t0001 only). They need a Docker host that can pull the pinned image. Outputs are in each folder's `result/`.
- Review: `evidence/reviews/git_rewrite_in_zig-native.md`.

