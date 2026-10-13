# git_rewrite_in_zig: native addendum (positive control)

> **Note (2026-10-12): superseded disposition.** The task is now fixed in a new version
> (`repairs/git_rewrite_in_zig-v2/`, case page `cases/git_rewrite_in_zig.md`): leftover build files
> are deleted instead of zeroing the score, and the source-text check that zeroed honest test code is
> dropped. The reasons given below for withholding the original are superseded; the case page states
> the current findings. The CPU-limit question is now measured (`evidence/runs/git_rewrite_in_zig-nproc-*`).
> This run used oracle mode, which skips the checks on the submitted tree and the clean build.

**Question.** Does a correct, version-matched `git` actually earn credit through the
original verifier path? Both runs below use the verbatim eval_cmd with the shipped
`test.sh`, the git t/ suite, `compute_reward.py`, `pytest_shim.sh` and the 29,075
denominator.

**Verdict.** CONFIRMED (positive control obtained).

- A real git v2.47.0 stood in for the submission. It was built from the scorer's own
  test-suite source tree and plugged in through the harness's own `HARBOR_ORACLE_MODE=1` path.
- On the full suite it scored exactly **29,075 passed / 0 failed**, so reward **1.000000**
  and `TOTAL_SCORE 1.000000`, which the linear rescale maps to 100.
- Restricted to t0001, it scored 86 passed, giving 0.002958.
- Every per-category pass count equals the hard-coded `oracle_attempted` baseline, so the
  denominator is reproduced exactly on this host.
- This resolves "no positive control exists". The remaining good-faith concerns from the triage are
  unaffected: the undisclosed scoring method and host-dependent timeouts. (Scorer-isolation notes
  are out of scope and kept internally.)

## Pinned artifacts

- Judge image: `seededge/edgebench.judge.git_rewrite_in_zig@sha256:645bc84baa85454ad3a853ce9ef5bde80a04b502eadf088667e76f203793cae7`. The worker pulled it by digest and its image ID was verified.
- Task JSON: `tasks/git_rewrite_in_zig.json` sha256 `6ae15eab2468ec372b36ae6101310d21c34803d147fa79752c3fe55f154a7332`.
- `/opt/tests` files in the image:

  | file | sha256 |
  |---|---|
  | `test.sh` | `c2e6d4469213855332e68080aea62bd94806c56b64e7487a54651122b03329a7` |
  | `compute_reward.py` | `28eea3d67e5bdb409ed06df8cfe0d69be9636b58ee8b2f86900c6d5915f35d0c` |
  | `pytest_shim.sh` | `6e38e136602a6e4b930d248afce9d3c2e857276b7ebb819464c64228c21daab6` |
  | `git-test-suite.tar.gz` (v2.47.0 source with `t/`) | `6d0f5c98d0155302a981a6d6bef0328ffefb6f0ed41149c8dbac47ec0ef0777e` |

## Commands

- Jobs: `e2b/jobs/git_rewrite_in_zig-oraclet0001/run.sh` and `e2b/jobs/git_rewrite_in_zig-oraclefull/run.sh`.
- E2B workers (8 vCPU), both recorded in `e2b/ledger.jsonl`:
  - `i1uxey747vx0xeimehv9k` (t0001 job): exited 0 after 81 s and was killed.
  - `ieuck0mvtppe7r15x9bkk` (full-suite job): exited 0 after 202 s and was killed.
- A first full-suite attempt, worker `id9wbpbgpir9mj74vf87h`, failed in the build step. It
  tried to build from the extracted `git-src`, which lacks `t/`. Its output is kept in
  `result-attempt1-build-failed/`. It was a setup error and produced no measurement.

### Steps

1. **Build** (inside the judge image, `--network none`):
   - `tar xzf /opt/tests/git-test-suite.tar.gz -C /tmp; cd /tmp/git-test-suite && make -j8 NO_TCLTK=1 NO_EXPAT=1 NO_GETTEXT=1 prefix=/opt/realgit install`
   - The build used the same make flags as `test.sh` Step 3.
   - `/opt/realgit/bin/git --version` reports `git version 2.47.0`, and its exec-path is `/opt/realgit/libexec/git-core`.
2. **Score** (fresh container, `--network none --cpus 8 --memory 6g`, with `/opt/realgit` mounted read-only):
   - Copy `/opt/realgit/bin/*` to `/home/workspace/zig-port/zig-out/bin/`.
   - `export HARBOR_ORACLE_MODE=1`.
   - For t0001 only, also `export GIT_SKIP_TESTS='t[1-9]* t0[1-9]* t00[1-9]* t000[02-9]*'`. This is git's own skip mechanism.
   - Then run the verbatim eval_cmd from the task JSON.

## Results

| run | scripts run | ok (credited) | not ok | skipped | reward / TOTAL_SCORE | normalized (linear 0–1) | wall |
|---|---|---|---|---|---|---|---|
| t0001 only | 1007 (1006 skipped wholesale) | 86 | 0 | 5 | 0.002958 | 0.30 | 29 s |
| full suite | 1007 | **29,075** | **0** | 1,177 | **1.000000** | **100** | 155 s |

- In the full run, per-category passes equal `oracle_attempted` exactly: t0 5379, t1 3191,
  t2 980, t3 4778, t4 3485, t5 4540, t6 2355, t7 2912, t8 493, t9 962.
- No script hit the 120 s timeout at nproc=8.
- 147 scripts had no `ok` line. They are prerequisite skips such as "Cannot run httpd tests
  as root", "skipping Windows-specific tests" and "GIT_TEST_ALLOW_SUDO".

## What this establishes, and the stand-in's fidelity

- **The real test path credits a correct implementation fully.** The 29,075 denominator is
  achievable exactly, at least on an 8-core host. This answers the triage's "There is still
  no positive control".
- **Oracle mode is the harness's own path, and it skips several steps**: anti-cheat, the
  zig build, the strace check, the deletion of system git, and the `/tmp` wipe. The skipped
  steps are submission screens and the build. The test execution and reward computation
  are identical to the scored path.
- The stand-in git carries its own exec-path under `/opt/realgit`, so it never relied on
  the system git that the non-oracle path deletes.
- **What it does not show.** A real Zig submission must also produce `--exec-path` and
  helper binaries itself. That requirement remains undisclosed in the prompt (triage
  point). Timeouts at lower core counts were not measured.

## Change to disposition

- The "no positive control" blocker is closed.
- The recommended disposition stays **repair-v2 (withhold original)**. The good-faith reasons are
  unchanged: the scoring method is undisclosed, and scoring is host-dependent. This run makes the
  original's scale credible: 1.0 means the full real git suite passes.
- A repaired version can reuse this run as its positive control.

## Limits

- This was one run on one 8-core host. Timing sensitivity at other core counts was not tested.
- The stand-in is C git, used through oracle mode, not a Zig binary through the non-oracle build path.
