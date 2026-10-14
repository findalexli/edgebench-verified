# Git Rewrite in Zig, fixed version: leftover build files are deleted instead of zeroing the score

## What this fixes

Before scoring, the original grader checks the submitted folder, and three of its checks set the whole score to 0 for things an honest solver can leave behind. `zig build-exe src/main.zig` run in the project folder leaves `main` and `main.o`, and either file gives 0. A source line that runs the system `git` to compare results gives 0, even inside a `test` block that is not part of the shipped binary. The prompt mentions none of these checks, and it invites testing against the system git. The fixed version deletes the leftover build files before the clean build and drops the source-text check. Everything else is unchanged.

## What changes

### The problem in detail

See the escalation runs in `evidence/runs/git_rewrite_in_zig-gates/` and the case page. The original
`/opt/tests/test.sh` (sha256 `c2e6d446…`) runs these checks in Step 1. Each failed check sets
`ANTI_CHEAT_RESULT="fail"`, and `compute_reward.py:118-123` then writes reward 0 for the whole submission:

- `shells_out_to_git` (`test.sh:89-94`): any line under `src/` that contains `std.process.Child`,
  `std.posix.execve` or `std.os.execve` together with `"git"` or `"/usr/bin/git"`. The check reads lines of
  text, so it also matches a differential test in a `test` block, or in a helper file that only tests use.
- `precompiled_objects` (`test.sh:105-112`): any `*.o`, `*.a`, `*.so`, `*.so.*` or `*.dylib` outside
  `zig-out/` and the Zig caches.
- `stray_elf_binaries` (`test.sh:114-121`): any executable ELF file outside `zig-out/` and the Zig caches.

The prompt says only "Do not compile or link the C source or wrap around the existing git binary — write
Zig", and "The system `git` is installed — use it to test your implementation as you go". The harness
sends the whole project folder except `.git`, `zig-out`, `zig-cache` and `.zig-cache`, so leftovers in the
project folder reach the grader.

### Exact change

One file changes, `/opt/tests/test.sh` (`repair.patch`: 19 lines removed, 23 added, comments included).
The file keeps mode 0755.

1. **Leftover build files are deleted, not penalized.** In place of the `precompiled_objects` and
   `stray_elf_binaries` checks, the fixed version deletes the same files and logs each one
   (`Removed precompiled object: …`, `Removed stray ELF executable: …`):
   - files named `*.o`, `*.a`, `*.so`, `*.so.*` or `*.dylib` (not directories), unless `file` reports
     their content as text, for example a source file such as `foo.so.zig`;
   - regular executable files whose `file` description contains `ELF`, the same test as the original.

   Both searches use the original paths and exclusions, so `zig-out/`, `zig-cache/` and `.zig-cache/` are
   never searched. Step 2 deletes and rebuilds those folders anyway (original `test.sh:144`), and it already deletes
   every `*.o`, `*.a` and `*.so` before the clean build (original `test.sh:145`).
2. **The `shells_out_to_git` source-text check is removed.** Calling git cannot earn credit in the
   tests, because the scored path removes every git the binary could call: `/app/git-src` is deleted
   before the build (fixed `test.sh:147`, original `:143`), the system git is deleted before the tests (fixed
   `:235-237`, original `:231-233`), and the C git binaries are removed from the test build (fixed `:261-262`,
   original `:257-258`). Every executable named `git` or
   `git-*` is gone after these steps (`git_after_nuke.txt` in the paired run). The paired run measures
   this directly: a binary that forwards every call to the system git passes the same 2 tests as the
   unmodified starter, under both versions.
3. In the task JSON, only `judge.image_tag` changes (`task.json.in`, `task-json.diff`).

Nothing else changes. The other checks are unchanged: C code over 2,000 lines, a `build.zig` that
compiles the git source, a `@cImport` of git headers, the `strace` step and `libgit2` linking. So are
the clean build, the test run, the per-script time limit, `NPARALLEL=$(nproc)`, `compute_reward.py`
and `pytest_shim.sh`. The work image and the prompt are not changed.

### Why this is the smallest change

- For any submitted folder, the fixed version gives the same score as the original or a higher one.
  If the folder has none of the deleted files and no line that matches the removed check, the two
  versions run identical commands. If it does have one, the original gives 0.
- Deleting a leftover keeps it out of the build and the tests, which is what zeroing was meant to
  achieve. The deletion cannot touch the build output: `zig-out/` is excluded, and it is rebuilt from
  source in Step 2.
- The only files the original zeroes and the fixed version keeps are text files with an object-file
  name. They are not object code.
- Restricting the source check to non-test code was considered and not used. It would need a Zig parser
  in the grader. It would still zero a helper file that only tests use (arm `exec_git_helper` below).
  It would also add nothing to scoring, because no git exists when the tests run.

### Are scores comparable?

Yes for every submission that the original does not zero through these three checks. Those
submissions get byte-identical `reward.json` in the paired run. A real-git positive control gives 29,075
of 29,075 tests under both versions, with identical per-script counts. Submissions that the original zeroed for a
leftover file or a git call in `src/` are scored on their tests in the fixed version, so their scores are not comparable.

## How it was checked

Paired run on the same inputs: [paired/results.md](paired/results.md). In plain words:

- The unmodified starter scores the same under both versions (2 tests).
- Four honest trees score 0 under the original grader and the starter's 2 tests under the fixed version:
  `zig build-exe` leftovers, only `main.o`, only `main`, and a git-calling `test` block. A fifth, a
  git-calling helper file used only by tests, behaves the same way.
- A real git scores 100 under both versions.
- Two kinds of wrapper get no credit from git under the fixed version. A wrapper that runs a C git stored
  in the project folder passes 0 tests, because the binary is deleted. A wrapper that runs the system git
  passes the starter's 2 tests, because no git is left when the tests run.

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`)
and the recipe for rebuilding the full file. Regenerate it, then build:

```bash
./materialize.sh && docker build -t edgebench.judge.git_rewrite_in_zig:0d404251e9c9-ebv-v2 .
```

`materialize.sh` takes the following steps:

1. Pull the pinned image by digest, unless it is already present.
2. Extract `/opt/tests/test.sh` with `docker create` and `docker cp`. No container runs in this step.
3. Check it against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of `files/test.sh` against `source-lock.json` → `materialize.outputs`.

It needs GNU `patch` on the host. The E2B workers have none, so the paired jobs apply the same patch
inside the original judge image, which has `patch`, and then check the same sha256 (`materialize.log`).

## Limits

- No AI model or real Zig port was run. The honest arms are the task's starter with a leftover or a
  test added, so they show the checks' effect, not a realistic score.
- How often real agents leave such files or write such tests is not known. The leaderboard averages for
  this task are 15-24 (`evidence/impact/leaderboard_12h.json`), one value per model; per-run scores and
  reasons are not available.
- The CPU-quota oversubscription (`NPARALLEL=$(nproc)`, original `test.sh:286`, fixed `:290`) is not changed. It is documented
  on the case page. The paired run uses `--cpus 8` on 8-CPU workers, where no script timed out.
- Each arm of the paired table ran three times (`-rep2`, `-rep3`), with identical rewards (`paired/results.md`, Repeatability). The `--cpus` escalation jobs ran once.
