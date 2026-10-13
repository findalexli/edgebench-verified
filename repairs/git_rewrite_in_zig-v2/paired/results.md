# git_rewrite_in_zig v2: paired results

## Jobs

Each job ran on one E2B worker (8 vCPU, 8 GiB, `nproc` = 8). Both jobs ended with `status: exit=0` in `evidence/runs/ledger.jsonl`, and the results were collected under each job's `result/out/`.

| Job | Sandbox | Elapsed | What it ran |
|---|---|---|---|
| `evidence/runs/git_rewrite_in_zig-v2-paired-gates-b/` | `iysldoqut8n2fov1vslvn` | 804 s | 7 arms in normal mode, original grader then fixed version |
| `evidence/runs/git_rewrite_in_zig-v2-paired-oracle-b/` | `inntfmvp1bw31v3ad7t0b` | 1546 s | full real-git suite in oracle mode, and bad control (b) in normal mode, original grader then fixed version |

The scripts are also in this folder as `run_gates.sh` and `run_oracle.sh`.

- **Original grader:** `seededge/edgebench.judge.git_rewrite_in_zig@sha256:645bc84baa85…` (`pull.txt`).
  Its `/opt/tests/test.sh` is `c2e6d446…` (`grader_sha.txt`).
- **Fixed version:** built on the worker from `pkg/` (`Dockerfile`, `repair.patch`, `source-lock.json`).
  Its `/opt/tests/test.sh` is `87bae2a5…`, which equals `materialize.outputs` in `source-lock.json`
  (`materialize.log`, `grader_sha.txt`). `compute_reward.py` and `pytest_shim.sh` are identical in both
  images (`grader_sha.txt`). The fixed image IDs are in `v2_image_id.txt`.
- **Command:** the `eval_cmd` from `tasks/git_rewrite_in_zig.json`, word for word, in a fresh container for every arm, with
  `--network none --cpus 8 --memory 6g`. The tree is prepared inside the container from the image's own
  starter at `/home/workspace/zig-port`. The inputs are the same files for both versions (`inputs_sha.txt`).
- **C git for bad control (a) and the oracle:** git v2.47.0 built inside the original image from the scorer's
  own test-suite tree (`cgit_build.txt`, `realgit_build.txt`; binary sha256 `07a24ddf…` in the oracle job).

## Paired table

Reward is `reward.json` → `reward`; the 0-100 score is reward × 100 (linear rescale 0-1). "Checks failed"
is `evidence.json` → `anti_cheat.violations`. Source: each arm's `summary.txt` line, `reward.json`
and `evidence.json`.

| Arm | Role | Original: checks failed | Original: tests passed | Original: reward | Fixed: files removed | Fixed: tests passed | Fixed: reward |
|---|---|---|---|---:|---|---|---:|
| `control`: unmodified starter | good control | none | 2 | 0.000069 | none | 2 | 0.000069 |
| `zig_build_exe`: starter after `zig build-exe src/main.zig -lc -lz` (leaves `main`, `main.o`) | trigger | `precompiled_objects; stray_elf_binaries` | – | **0.0** | `main.o`, `main` | 2 | 0.000069 |
| `obj_only`: as above, only `main.o` left | trigger | `precompiled_objects` | – | **0.0** | `main.o` | 2 | 0.000069 |
| `elf_only`: as above, only `main` left | trigger | `stray_elf_binaries` | – | **0.0** | `main` | 2 | 0.000069 |
| `exec_git`: `test` block in `src/main.zig` runs system git (`zig test` passes 1/1) | trigger | `shells_out_to_git` | – | **0.0** | none | 2 | 0.000069 |
| `exec_git_helper`: `src/difftest.zig` helper runs system git, used only by a `test` block (`zig test` passes 1/1) | trigger | `shells_out_to_git` | – | **0.0** | none | 2 | 0.000069 |
| `bad_wrap_cgit`: `main.zig` execs `./cgit`, a C git v2.47.0 in the project folder | bad control (a) | `stray_elf_binaries` | – | 0.0 | `cgit` | **0** | **0.0** |
| `bad_shell_git`: `main.zig` forwards every call to the system `git` | bad control (b) | none | 2 | 0.000069 | none | 2 | 0.000069 |
| `bad_shell_git_oneline`: the same, with `"git"` on the `std.process.Child` line | bad control (b) | `shells_out_to_git` | – | 0.0 | none | 2 | 0.000069 |
| oracle: real git v2.47.0 in `zig-out/bin`, `HARBOR_ORACLE_MODE=1` | positive control | (skipped in oracle mode) | 29,075 | **1.000000** | (skipped) | 29,075 | **1.000000** |

"–" means the tests ran but the reward ignores them.

- Every arm with 2 passes has the same counts: 2 passed (both in t5xxx) and 69 failed (`reward.json`
  subscores). The `reward.json` of `control`, `zig_build_exe`, `obj_only`, `elf_only`,
  `exec_git` and `exec_git_helper` under the fixed version is byte-identical to `control` under the original grader.
- Oracle: 1007 of 1007 scripts ran in both versions, with 0 failed tests and 0 timeouts. The per-script
  ok / not-ok / timeout counts are identical (`oracle/v{1,2}/per_script_ok_notok_timeout.txt`;
  `summary.txt`: "per-script counts identical"). The eval took 159 s in both versions. The `cpu.max` quota was 800000/100000 and `nproc` was 8.
- After the scored path's deletions (fixed `test.sh:147`, `:235-237`; original `:143`, `:231-233`), the fixed image has no `git` on PATH and no
  executable named `git` or `git-*` outside `zig-out` (`git_after_nuke.txt`).

## Spec checks

- **Good control:** the unmodified starter scores the same under both versions (reward 0.000069).
- **Triggers:** all five honest trees get 0 under the original grader. Under the fixed version each gets
  the starter's reward of 0.000069. The leftovers are deleted and logged (`verifier.log`), and the build and the tests run as for the
  starter.
- **Positive control:** a correct git scores 1.000000 (100) under both versions, with identical
  per-script counts.
- **Bad control (a), C git in the project folder:** 0.0 under both versions. The original grader zeroes it
  with `stray_elf_binaries`. The fixed version deletes `cgit`, and the wrapper passes 0 of 29,075 tests.
- **Bad control (b), system-git wrapper:** under the fixed version, both variants get 0.000069. That is the
  unmodified starter's 2 tests and no credit from git, because no git exists when the tests run. The
  original grader gives 0.000069 to the plain variant and 0.0 to the one-line variant, which its
  source-text check matches. Fixing the one-line variant moves it by 0.0069 points out of 100, to the floor that any
  binary gets.
- **Verdict:** accepted. The fixed version stops zeroing honest trees, scores everything else as the
  original does, and gives wrappers no credit from git.

## Not run

- No AI model or real Zig port was run.
- Each arm of the paired table ran three times (see Repeatability below). The `--cpus` values below 8 from the
  escalation (`git_rewrite_in_zig-nproc-*`) ran once and were not repeated, because the fixed version does not
  change parallelism.
- An earlier round of the same jobs used a fixed `test.sh` that differed only in one comment. It gave the
  same rewards in every arm and is not part of this record.

## Repeatability (2026-10-13)

| job | arms | runs | identical? |
| --- | --- | --- | --- |
| `evidence/runs/git_rewrite_in_zig-v2-paired-gates-b`, `-gates-b-rep2`, `-gates-b-rep3` | `control`, `zig_build_exe`, `obj_only`, `elf_only`, `exec_git`, `exec_git_helper`, `bad_wrap_cgit`, each under both graders | 3 | yes |
| `evidence/runs/git_rewrite_in_zig-v2-paired-oracle-b`, `-oracle-b-rep2`, `-oracle-b-rep3` | oracle, `bad_shell_git`, `bad_shell_git_oneline`, each under both graders | 3 | yes |

The reruns used each job's `run.sh` and inputs unchanged, each on a fresh E2B worker. Each worker rebuilt the fixed grader from this package. Every run has `status: exit=0` in `result/worker.json` and the ledger, and its worker was killed. All 10 arms of the paired table give the same reward, tests passed and anti-cheat reason in all three runs for both graders (`result/out/summary.txt`). The oracle's counts are the same in every run: 29,075 passed, 0 failed, 1,007 scripts, and `per-script counts identical` v1 against v2. Only wall times differ. Per-run values are in `data/paired-repeatability.csv`.
