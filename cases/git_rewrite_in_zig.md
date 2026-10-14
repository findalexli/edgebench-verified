# Git Rewrite in Zig (`git_rewrite_in_zig`)

**Outcome:** Fixed. <mark>The original grader sets the whole score to 0 when the submitted folder has a leftover build file (`main`, `main.o`) or a source line that runs the system `git`, even inside a test; a solver that follows the instructions can produce both, and the prompt mentions neither check. The fixed version deletes the leftovers before building and drops the source-text check; a correct git still scores 100.</mark>

## What the task asks

The prompt says: "Reimplement git in Zig as a drop-in replacement for the `git` binary." The binary "must behave identically to the real `git` — same CLI interface, same output formats, same exit codes." The score is the fraction of git v2.47.0's own `t/` test suite that passes, against a fixed total of 29,075 tests. Category: Systems & Software Engineering.

## What goes wrong

- Before scoring, `test.sh` checks the submitted folder. Any one failed check sets the reward to 0 for the whole submission (`compute_reward.py:118-123`). The prompt describes none of these checks. It says only "Do not compile or link the C source or wrap around the existing git binary", and it invites "The system `git` is installed — use it to test your implementation as you go".
- Measured with the original grader in normal mode, on the task's own starter (`evidence/runs/git_rewrite_in_zig-v2-paired-gates-b/`; first seen in `evidence/runs/git_rewrite_in_zig-gates/`):
  - the unmodified starter passes the checks (reward 0.000069, its 2 tests);
  - running `zig build-exe src/main.zig -lc -lz` in the project folder leaves `main` and `main.o`, and the reward is 0 (`precompiled_objects`, `stray_elf_binaries`, `test.sh:105-121`); either file alone also gives 0;
  - a `test` block in `src/` that runs the system git to compare output gives 0 (`shells_out_to_git`, `test.sh:89-94`), and so does a helper file in `src/` used only by tests. Neither is in the shipped binary.
  - The documented `zig build`, and `zig test` and `zig run`, leave no such files (local run in the same grader image, Zig 0.14.0).
- The harness sends the whole project folder except `.git`, `zig-cache`, `zig-out` and `.zig-cache`, with executable bits kept (`sforge/harness/run_agent.py:185-215`), so anything left in the project root or `src/` reaches the checks.

**Note: CPU limit (not changed by the fix).** `test.sh` runs `nproc` test scripts at once with 120 s per script, and `nproc` ignores a CPU quota (`test.sh:286`, `:301`). With a correct git (C v2.47.0, oracle mode) on an 8-core host (`evidence/runs/git_rewrite_in_zig-nproc-c8c4/`, `-c2/`, `-c1/`):

| `--cpus` | Scripts per CPU | Slowest script | Killed at 120 s | Passed | Score |
|---|---:|---:|---:|---:|---:|
| 8 | 1 | 25 s | 0 | 29,075 | 100 |
| 4 | 2 | 45 s | 0 | 29,075 | 100 |
| 2 | 4 | 109 s | 0 | 29,075 | 100 |
| 1 | 8 | 120 s | 2 | 28,311 | 97.37 |

- At `--cpus 1`, `t1092` and `t0027` ran for exactly 120 s and were cut off; 42 + 722 = 764 tests were lost (29,075 − 28,311), and the reward is 0.973723 (`reward.json`). These two scripts are the only ones whose pass count differs from the 8-CPU run.
- Only `t1092` carries the grader's `# TIMEOUT after 120s` marker (`timeouts.txt`). `t0027` has none, though its output is cut off at 120 s, so the marker undercounts timeouts.
- Script durations are each result file's birth time to its last write (`stat_times.txt`). What matters is the number of scripts per CPU, so a 16-core host with `--cpus 2` behaves like the last row. A Zig port slower than C git reaches the limit sooner.
- EdgeBench's leaderboard settings give this grader 4 CPUs (the default, with no override for this task; quoted in [`evidence/impact/edgebench-leaderboard-config.md`](../evidence/impact/edgebench-leaderboard-config.md)). On an 8-core host that is 2 scripts per CPU, the `--cpus 4` row above: no script was cut off, the slowest took 45 s of its 120 s, and a correct git scores 100. On a host with more cores, `nproc` and so the number of scripts per CPU are higher (a 32-core host gives 8 per CPU, the last row); the core count of the leaderboard's hosts is not known. Without a configuration, the harness sets no CPU quota (`judge_cpu_limit` is `None`, `sforge/harness/config.py:69`), and this does not happen. This is documented, not changed.

Notes that ship with the task:

- The prompt does not describe the scoring method (the git `t/` suite, counted per test).
- A real Zig submission must also provide `--exec-path` and the helper programs itself. The prompt does not state this.

## How much it matters

A good-faith submission that trips one of the three checks loses its whole score under the original grader, up to 100 points; the fixed version scores it on its tests. For every other submission the two versions give the same score. How often real runs tripped a check is not known; the leaderboard averages for this task are 15-24 (`evidence/impact/leaderboard_12h.json`).

## The fix

One file changes, `/opt/tests/test.sh` (`repairs/git_rewrite_in_zig-v2/`):

- Leftover `*.o`, `*.a`, `*.so`, `*.so.*` and `*.dylib` files, and executable ELF files outside `zig-out` and the Zig caches, are deleted and logged before the clean build. The original set the score to 0 for them.
- The source-text check for git calls is removed. When the tests run, no git is left to call: the git source, the system git and the C git binaries of the test build are all deleted first (fixed `test.sh:147`, `:235-237`, `:261-262`, which are lines 143, 231-233 and 257-258 of the original; `git_after_nuke.txt` in the paired run shows no `git` or `git-*` program left).
- Everything else is unchanged, including the other checks, the test run, the parallelism and the reward. `compute_reward.py` and `pytest_shim.sh` are identical in both images (`grader_sha.txt`). In `task.json.in` only `judge.image_tag` changes.

Paired run, original grader against fixed version, same inputs, `--network none --cpus 8 --memory 6g` (`repairs/git_rewrite_in_zig-v2/paired/results.md`, from `evidence/runs/git_rewrite_in_zig-v2-paired-gates-b/` and `-oracle-b/`):

| Submitted tree | Original grader | Fixed version |
|---|---:|---:|
| unmodified starter | 0.000069 | 0.000069 |
| after `zig build-exe` (`main`, `main.o`) | 0 | 0.000069 |
| only `main.o` / only `main` | 0 / 0 | 0.000069 / 0.000069 |
| git-calling `test` block / test-only helper file | 0 / 0 | 0.000069 / 0.000069 |
| real git v2.47.0 (oracle mode) | 1.000000 | 1.000000 |
| a submission that wraps a C git | no credit | no credit |

Rewards are 0 to 1; the score out of 100 is the reward × 100. "No credit" means at most the 2 tests the unmodified starter passes (0.000069).

- The fixed version's `reward.json` for the starter and the five good-faith trees is byte-identical to the starter's under the original grader: 2 tests passed, 69 failed.
- With real git, both versions ran 1,007 of 1,007 scripts with 0 failed tests and 0 timeouts, and the per-script counts are identical (`oracle/v{1,2}/per_script_ok_notok_timeout.txt`).

**Scores are comparable with the original.** For every submitted tree the fixed version gives the same score as the original grader, or the original gave 0: if the tree has nothing the fixed version deletes and no line the dropped check matches, both versions run the same commands.

## How we checked it

- **Original grader, from the public image pinned by digest.** Every run used the task's `eval_cmd` word for word in a fresh container with `--network none --memory 6g`, the shipped `test.sh` (sha256 `c2e6d446…`), the git `t/` suite, `compute_reward.py` and `pytest_shim.sh`.
- **Normal-mode runs through the eval_cmd**, with the original grader and the fixed version on the same trees: the starter, five good-faith trees that trip a check, and two kinds of wrapper. Table above.
- **Real git.** A real git v2.47.0 was built inside the grader image (with `--network none`) from the scorer's own test-suite source tree, with the same make flags as `test.sh`, and placed in `zig-out/bin/`. It ran in the harness's own `HARBOR_ORACLE_MODE=1`, which skips the checks on the submitted tree, the clean `zig build` and the removal of the system git; running the tests and computing the reward are identical to the scored path. It scored 29,075 of 29,075, reward 1.000000, in the earlier run (`evidence/runs/git_rewrite_in_zig-oraclefull/`) and under both versions in the paired run. In the full run, each category's pass count equals the grader's fixed `oracle_attempted` baseline exactly: t0 5379, t1 3191, t2 980, t3 4778, t4 3485, t5 4540, t6 2355, t7 2912, t8 493, t9 962. 147 scripts skipped themselves for a missing prerequisite, for example "Cannot run httpd tests as root".
- **CPU limit.** The same real-git run at `--cpus` 8, 4, 2 and 1 on an 8-core E2B worker; `nproc` was 8 and `cpu.max` showed the quota in every run.
- **Fixed version.** Built from the public image with the package's `Dockerfile`; its `test.sh` (sha256 `87bae2a5…`) matches `materialize.outputs` in `source-lock.json` (`materialize.log`). Both paired jobs ended with `status: exit=0` and their results were collected.

## Limits

- No AI model or solver was run. The result rests on test submissions we wrote.
- The good-faith trees in the paired run are the starter with a leftover or a test added, not a real Zig port. Each arm of the paired table ran three times (`-rep2`, `-rep3`), with identical rewards; the `--cpus` escalation jobs ran once.
- The real-git stand-in is C git run in oracle mode, not a Zig binary going through the normal build path.
- The CPU-limit runs used one 8-core host, one run per setting.

## Reproduce

- Grader image: `sha256:645bc84baa85…`.
- Paired runs: `evidence/runs/git_rewrite_in_zig-v2-paired-gates-b/` and `-oracle-b/` (`run.sh`); summary and scripts in `repairs/git_rewrite_in_zig-v2/paired/` (`results.md`, `run_gates.sh`, `run_oracle.sh`).
- First measurement of the checks: `evidence/runs/git_rewrite_in_zig-gates/`. CPU limit: `evidence/runs/git_rewrite_in_zig-nproc-c8c4/`, `-c2/`, `-c1/`.
- Real git, original grader: `evidence/runs/git_rewrite_in_zig-oraclefull/run.sh` (full suite) and `evidence/runs/git_rewrite_in_zig-oraclet0001/run.sh` (t0001 only). Outputs are in each folder's `result/`.
- The fixed version: `repairs/git_rewrite_in_zig-v2/` (`README.md`, `repair.patch`, `materialize.sh`, `source-lock.json`).
- Review: `evidence/reviews/git_rewrite_in_zig-native.md`.
