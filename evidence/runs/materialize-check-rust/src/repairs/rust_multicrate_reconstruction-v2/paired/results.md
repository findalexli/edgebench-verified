# rust_multicrate_reconstruction v2: paired results

## Setup

**Where it ran.** Every number below comes from the task's `eval_cmd`, run verbatim (`inputs/eval_cmd.sh` is the same text as `tasks/rust_multicrate_reconstruction.json` `judge.eval_cmd`). It ran with `--network none` on E2B workers with 8 vCPU, 8 GiB and a 20.7 GB disk. Containers were limited to `--memory 7600m` with `CARGO_BUILD_JOBS=8`, and cargo/rustc was 1.88.0. Each job's `result/worker.json` reads `status: exit=0`, and its collected `result/out/` holds the summary, the logs and every arm's `score-results.json`.

**The three images** (each job lists them in `images.txt`):

| Image | What it is | `score.py` sha256 |
|---|---|---|
| **original grader** (`orig`) | the pinned judge image `…@sha256:d1d18aed…`, as shipped | `d725dd93…` |
| **original grader + cc files** (`origcc`) | the same image with only the four `vendor-deps/cc/src/target/*.rs` files added to its archive. The original `score.py` and hidden tests are unchanged. | `d725dd93…` |
| **fixed version** (`v2`) | built on the worker from this package (`materialize.sh` + `Dockerfile`) | `50707cd4…` |

**The submissions.** Each one is a starter `agent-start` without `vendor-deps/` or `target/`, as `submit_exclude` leaves it. It is built by `build_sub.py`, and its file-tree sha256 is in `submission.sha256`.

| Submission | What it is | Tree sha256 |
|---|---|---|
| starter | the shipped starter, unchanged | `6bcc09c7…` |
| reference | the starter with its 507 `todo!()` files replaced by upstream CAS v1.0.0 (`github.com/codingagentsystem/cas` @ `a0a4b5ad`). In the 182 of those files that carry hidden snippets, the hidden test functions are removed again. In each of the 182, the test region is then checked equal to the starter's, so the grader has to inject the hidden tests, as for any solver who leaves tests unchanged. Test-helper stubs that are not `todo!()`, such as the proptest strategies `Just("test")`, stay as shipped. | `be913f2b…` |
| partial | the reference, with `crates/cas-search/src/metrics.rs` left as in the starter (`todo!()` bodies) | `1a20dd99…` |
| bad | the reference, with `PtyConfig::default()` returning `rows: 25` (the test `test_pty_config_default` expects 24) | `b55aa26c…` |

## Results

Summary of the four submissions' scores out of 100 (details per crate below). The middle column is
the publisher's grading environment, as inferred from the exact reproduction of its starter score.

| Submission | original grader | original grader + cc files | fixed version |
|---|---:|---:|---:|
| starter | 1.4711 | 3.8189 | 5.7236 |
| reference | 27.6091 | 73.9926 | 94.7022 |
| partial | 27.6091 | 73.9926 | 93.9963 |
| bad | 27.5091 | 73.8926 | 94.6022 |

Scores are out of 100. Cells give tests passed / total for each crate. Statuses other than `TEST_FAIL` and `PASS` are noted.

### starter (job `evidence/runs/rust_multicrate_reconstruction-v2-paired-r2-starter`)

| crate | original grader | original grader + cc files | fixed version |
|---|---|---|---|
| cas-types | 1/136 | 1/136 | 1/136 |
| cas-code | 0/50 TEST_CRASH | 0/50 | 0/50 |
| cas-factory-protocol | 13/98 | 13/98 | 14/98 |
| cas-diffs | 12/98 | 12/98 | 12/98 |
| cas-pty | 1/11 | 1/11 | 2/11 |
| cas-recording | 0/29 TEST_CRASH | 1/29 | 1/29 |
| cas-store | 0/216 TEST_CRASH | 2/216 | 2/216 |
| cas-search | 0/136 TEST_CRASH | 0/136 COMPILE_FAIL_ROOT | 7/136 |
| cas-core | 0/201 TEST_CRASH | 18/201 | 18/201 |
| cas-mux | 0/37 TEST_CRASH | 0/37 | 0/37 |
| cas-factory | 0/134 TEST_CRASH | 4/134 | 11/134 |
| cas-mcp | 0/16 TEST_CRASH | 14/16 | 14/16 |
| cas-tui-test | 0/105 | 0/105 | 3/105 |
| cas-cli | 0/1344 TEST_CRASH | 0/1344 COMPILE_FAIL_DOWNSTREAM | 92/1344 |
| **score** | **1.4711** | **3.8189** | **5.7236** |

**The middle column matches the publisher's own grading.** The archive's `judge/skeleton-score.json` records the publisher's run on the starter (`judge/baseline-summary.md`, run on macOS). "Original grader + cc files" reproduces it exactly: the same per-crate statuses, passed, failed and total counts, total score 3.8189, public score 3.3913 and 66 tests passed. With the archive as shipped, the score is 1.4711.

**Why cas-search and cas-cli fail to compile.** `origcc/diag.txt` rebuilds the combined workspace exactly as `score.py` does and compiles it. It shows:

- cas-search: `tokio` unresolved, and no `search_async` or `AsyncBm25Index`. The errors come from the three injected async tests.
- cas-cli: `expected one of ':', '@', or '|', found keyword 'in'` in `cas-cli/tests/proptest/search_properties.rs`. These are the injected proptest tests.

### reference (job `…-paired-r2-reference`)

| crate | original grader | original grader + cc files | fixed version |
|---|---|---|---|
| cas-types | 135/136 | 135/136 | 135/136 |
| cas-code | 0/50 TEST_CRASH | 49/50 | 49/50 |
| cas-factory-protocol | 97/98 | 97/98 | 97/98 |
| cas-diffs | 89/98 | 89/98 | 89/98 |
| cas-pty | 10/11 | 10/11 | 11/11 |
| cas-recording | 0/29 TEST_CRASH | 25/29 | 25/29 |
| cas-store | 0/216 TEST_CRASH | 216/216 | 216/216 |
| cas-search | 0/136 TEST_CRASH | 0/136 COMPILE_FAIL_ROOT | 128/136 |
| cas-core | 0/201 TEST_CRASH | 191/201 | 191/201 |
| cas-mux | 0/37 TEST_CRASH | 0/37 TEST_CRASH | 0/37 TEST_CRASH |
| cas-factory | 0/134 TEST_CRASH | 131/134 | 131/134 |
| cas-mcp | 0/16 TEST_CRASH | 16/16 | 16/16 |
| cas-tui-test | 102/105 | 102/105 | 102/105 |
| cas-cli | 0/1344 TEST_CRASH | 0/1344 COMPILE_FAIL_DOWNSTREAM | 1252/1344 |
| **score** | **27.6091** | **73.9926** | **94.7022** |

The gain from "original grader + cc files" to the fixed version is the sum of three parts, from the layer weights in `score.py`:

- cas-search: 128/136 × 12 = +11.2941
- cas-cli: 1252/1344 × 10 = +9.3155
- the cas-pty doctest no longer skipped: 1/40 × 4 = +0.1000

73.9926 + 20.7096 = 94.7022.

### partial (job `…-paired-r2-partial`)

Only the crates that differ from the reference are shown.

| crate | original grader | original grader + cc files | fixed version |
|---|---|---|---|
| cas-search | 0/136 TEST_CRASH | 0/136 COMPILE_FAIL_ROOT | 120/136 |
| **score** | **27.6091** | **73.9926** | **93.9963** |

### bad (job `…-paired-r2-bad`)

Only the crates that differ from the reference are shown.

| crate | original grader | original grader + cc files | fixed version |
|---|---|---|---|
| cas-pty | 9/11 | 9/11 | 10/11 (failed = 1) |
| **score** | **27.5091** | **73.8926** | **94.6022** |

The broken test still costs one cas-pty test (0.1000 points) in the fixed version: 94.7022 − 94.6022. The intended known failure, `test_pty_config_claude_with_teams`, failed and is credited, as the exemption intends.

### Fail-fast on its own

These jobs use a fourth image, **fixed version without `--no-fail-fast`** (`v2ff`). It is the fixed version with only `--no-fail-fast` taken out of `score.py` again. Each job graded the same submission bytes as the paired job, and its `submission-<sub>.sha256` matches.

| Submission (job) | fixed version without `--no-fail-fast` | fixed version | Tests charged only because Cargo stopped early |
|---|---|---|---|
| starter (`…-v2-failfast-isolation-b`) | 4.7352 | 5.7236 | cas-cli 40, cas-factory 7, cas-tui-test 3, cas-factory-protocol 1, cas-pty 1, cas-search 1 |
| reference (`…-v2-failfast-isolation-r2-reference`) | 94.2674 | 94.7022 | cas-cli 45, cas-pty 1 (doctest) |
| partial (`…-v2-failfast-isolation-r2-partial`) | 90.7380 | 93.9963 | cas-search 32, cas-cli 45, cas-pty 1 |
| bad (`…-v2-failfast-isolation-r2-bad`) | 94.1674 | 94.6022 | cas-cli 45, cas-pty 1 |

**Reference.** In the reference, cas-cli's `proptest_test` binary has failing tests, because the starter's strategy stubs `Just("test")` are left unchanged. Cargo then skips the later cas-cli binaries, so their 45 passing tests are charged as failures: 0.3348 points.

**Partial.** The unfinished `metrics.rs` fails 8 tests in the cas-search library binary. Without `--no-fail-fast`, the 32 passing tests in the 3 integration binaries and the doctests are also lost: 2.8235 points.

Job `…-v2-failfast-isolation-a` (partial and reference in one worker) ran out of disk (`df.log` at 100%, `partial-v2ff/eval.log`: `No usable temporary directory`). Its results are not used. Job `…-v2-failfast-isolation-b` also ran out of disk on its second submission (`bad-v2ff/eval.log`: `No space left on device`), so only its first submission (starter) is used. Disk use stayed at or below 18,228 of 20,711 MB until that submission had finished (`df.log`). The partial, reference and bad submissions were rerun as the `…-isolation-r2-*` jobs, one submission per worker, with the extracted archive and the worker's build cache removed before grading.

### Repeatability

**Round 1.** The round-1 jobs `…-paired-starter`, `…-paired-reference` and `…-paired-partial` were graded with the first package version, which had no cas-search change. They gave the same original-grader and "+ cc files" scores as round 2:

- starter: 1.4711 and 3.8189
- reference: 27.6091 and 73.9926
- partial: 27.6091 and 73.9926

**What round 1 showed.** In round 1, cas-search was still `COMPILE_FAIL_ROOT` in the fixed version, which led to the cas-search change. The reference then scored 83.4081, and the starter 5.1059.

**Disk.** No arm logged `No space left`, `signal: 9` or `SIGKILL` (`*/crate_lines.txt`: `disk_or_oom_hits=0`). The highest disk use was 19,916 of 20,711 MB (`…-paired-r2-reference/result/out/df.log`).

## Repeatability (2026-10-13)

| submission | jobs | runs of the current package | identical? |
| --- | --- | --- | --- |
| reference | `evidence/runs/rust_multicrate_reconstruction-v2-paired-r2-reference`, `-rep2`, `-rep3` | 3 | yes |
| partial | `…-paired-r2-partial`, `-rep2`, `-rep3` | 3 | yes |
| bad | `…-paired-r2-bad`, `-rep2`, `-rep3` | 3 | yes |
| starter | `…-paired-r2-starter` only | 1 | not repeated |

Each rerun used the round-2 job's `run.sh` and `inputs/` unchanged, on a fresh E2B worker. The worker rebuilt the fixed version from the package and graded the submission under all three images. Every rerun has `status: exit=0`, and its worker was killed. In all three runs, each of reference, partial and bad gives the same score under all three images (original grader, original grader + cc files, fixed version: 27.6091 / 73.9926 / 94.7022 for reference, 27.6091 / 73.9926 / 93.9963 for partial, 27.5091 / 73.8926 / 94.6022 for bad). The per-crate status and passed/total counts in `orig/` and `v2/score-results.json` are also identical. Only wall times differ (fixed-version arm 1025–1128 s).

**Subset.** These jobs are expensive (about 40 minutes and up to 19.9 of 20.7 GB of disk each), so the starter, the baseline arm, was not rerun. Its original-grader and "+ cc files" scores are reproduced by round 1 (above), but its fixed-version score of 5.7236 comes from one run.

## Conclusion

Accepted. On the same submission bytes, the fixed version:

- builds every crate that the shipped archive could not build;
- compiles the hidden tests of cas-search and cas-cli, which no submission that leaves the tests unchanged could compile before;
- no longer charges tests that Cargo did not run;
- still charges real failures: partial −8 cas-search tests, bad −1 cas-pty test.

The starter's score (5.7236) stays near the publisher's recorded baseline (3.8189). A complete solution scores 94.7022, against 27.6091 on the published image and 73.9926 in the publisher's environment as reconstructed here.
