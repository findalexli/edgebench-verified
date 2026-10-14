# Rust Multicrate Reconstruction (`rust_multicrate_reconstruction`)

**Outcome:** Fixed. <mark>The original grader inserts hidden tests where they do not compile, so two whole crates score 0 for every solver who leaves the tests unchanged, as the task requires: cas-search (12 points) and cas-cli (10 points). Cargo also stops at the first failing test file and the grader counts the tests that did not run as failed. In the publisher's grading environment a complete solution scores 73.99 out of 100; with the fixed version it scores 94.70. Separately, the published images lack four vendored files, so with them as shipped the same solution scores 27.61; this did not affect the publisher's own grading.</mark>

![Two panels. Left: the project's 14 packages as tiles; two are marked in red, search (12 points, scored 0) and cli, the command-line program (10 points, scored 0), because the checker places their hidden tests where they cannot compile. Right: bars, out of 100, for one complete, correct solution: 73.99 with the original checker and 94.70 with the fixed checker, a gain of 20.71 (search +11.29, cli +9.32, a skipped test +0.10).](figures/rust_multicrate_reconstruction.svg)

*Hidden tests that cannot compile zero out 22 of 100 points for every solver who leaves the tests and package settings unchanged. The agent rebuilds a 14-package Rust project and is told not to edit the tests. The checker adds hidden tests to all 14 packages, and in two of them, search (12 points) and the command-line program (10 points), it places them where they do not compile, so both score 0. A complete, correct solution scores 73.99 out of 100 with the original checker as the publisher ran it and 94.70 with the fixed checker. The fixed checker places the hidden tests where they compile, and it also runs tests the original skipped after an earlier failure.*

## What the task asks

The task says: "Complete the missing Rust implementations in the unpacked CAS workspace." It adds that "the hidden evaluator runs additional tests for the same public crate and CLI contracts". A crate is a Rust package; the workspace has 14 of them.

The score is a weighted sum over 10 layers, where each layer contributes `weight × passed / total` of its tests (`score.py` lines 29-38 and 390). cas-search alone makes up layer L5 (weight 12, 136 tests), and cas-cli alone makes up layer L9 (weight 10, 1344 tests). The cas-pty and cas-recording crates make up layer L3 (weight 4, 40 tests). The task forbids editing tests ("Do not edit … tests", `TASK.md`; "Do not delete, weaken, or bypass tests", `SPEC.md`). Category: Systems & Software Engineering.

## What goes wrong

We found four defects. The first three change scores in the publisher's own grading environment, and so the published leaderboard. The fourth affects only people who grade with the published images.

**1. Hidden tests that do not compile (cas-cli and cas-search).** The grader appends each hidden test snippet to the end of the test file, or, for a source file, to the end of its last `#[cfg(test)]` module (`score.py` `inject_hidden_tests`). In two crates that place is wrong.

- In cas-cli, in `cas-cli/tests/proptest/search_properties.rs`, the four hidden tests are written in `proptest!` syntax (`fn search_never_crashes(query in search_query_strategy())`). The starter keeps the file's `proptest! { … }` block without them, and the grader appends them after it, where this syntax is not valid. The file does not compile (`expected one of ':', '@', or '|', found keyword 'in'`; `functions used as tests can not have any arguments`), and cas-cli scores 0 of 1344.
- In cas-search, three hidden tests are `#[tokio::test]` async tests that upstream sit in `#[cfg(feature = "parallel")]` modules: `test_async_hybrid_search` in `src/hybrid.rs` and in `tests/hybrid_integration.rs`, and `test_async_remove` in `src/bm25_tests/tests.rs`. The grader puts them outside those modules. There they need `tokio`, an optional dependency, and `search_async` and `AsyncBm25Index`, which exist only with that feature. cas-search does not compile and scores 0 of 136.

The compiler messages are in `evidence/runs/rust_multicrate_reconstruction-v2-paired-r2-starter/result/out/origcc/diag.txt`. The grader skips a file only if every hidden function name already appears in it. For cas-cli the only way out is to write the hidden tests' exact names, which a solver cannot know. For cas-search a solver could also turn on the crate's `parallel` feature by default (`crates/cas-search/Cargo.toml` declares `parallel = ["tokio"]` with `default = []`), which edits no test; we did not try this route, and nothing in the task points to it. A good-faith solver who leaves the tests and the crate features unchanged therefore gets 0 for L5 and L9.

**2. Cargo stops at the first failing test file.** `run_crate_test` runs `cargo test --frozen -p <crate> -- --test-threads=4` without `--no-fail-fast` (`score.py:266-268`). After one test binary of a crate fails, Cargo runs none of its later binaries (integration-test files, doctests), and the grader adds the tests that did not run to the failures (`:329-331`). The loss depends on where a failure falls, not on how many tests pass. For example, the intended known failure in cas-pty's library tests stops cas-pty's one doctest, so a complete solution gets 10 of 11 instead of 11 of 11.

**3. Exempt-test credit (the earlier finding).** The grader excuses one known-failing test per crate. When a crate has at least one failure, it converts one failure into a pass if the excused test's name appears anywhere in the test output; it does not check whether that test failed. So when the excused cas-pty test passes and another cas-pty test (for example `test_pty_config_default`) fails, the original grader reports PASS with 11 passed and 0 failed instead of TEST_FAIL with 10 and 1. A partly finished solution that follows the rules can trigger this, because the excused test only checks how arguments are built.

**4. Missing vendored files (published images only).** The archive the grader unpacks, `cas_rust_benchmark.tar.gz` (44,858 entries), has no path under any directory named `target`. The vendored `cc` 1.2.55 crate therefore lacks `src/target/{apple,generated,llvm,parser}.rs`, which its `.cargo-checksum.json` lists; of the 741 vendored crates, `cc` is the only one with files missing. Cargo refuses the crate, so the 9 crates that build with `cc` score `TEST_CRASH`: cas-code, cas-recording, cas-store, cas-search, cas-core, cas-mux, cas-factory, cas-mcp and cas-cli. `eval_cmd` replaces the submission's `vendor-deps/`, so a solver cannot supply the files, and the work image lacks them too (`cargo build --frozen -p zstd-sys` fails with `failed to open file …/cc/src/target/apple.rs`).

This did not affect the publisher's grading. With only these four files restored, the original grader scores the unchanged starter 3.8189, which equals the publisher's recorded result (`judge/skeleton-score.json` in the archive) in total score, public score (3.3913), tests passed (66) and every crate's status and counts. With the archive as shipped it scores 1.4711. The publisher therefore graded with a complete vendor tree. Most likely someone packed the archive afterwards with an exclusion of `target` directories, which also removed `cc/src/target/` (inferred). The published scores agree, reaching 57.8 (`tasks/README.md:131`), above the 27.61 a complete solution can score with the images as shipped.

The grader also scores tests the solver adds, which we do not count as a finding. It copies the solver's workspace as it is, appends the hidden tests, and counts every `N passed;` and `N failed;` from `cargo test` (`score.py:286-291`). The crate total is `max(listed tests, EXPECTED_TOTALS)` (`:263-264`, `:329`). Unit tests or doctests the solver writes itself therefore enter both the passed count and the total, although the task README calls the denominator fixed ("The current fixed scoring denominator is `RAW_TOTAL=2611`"; `RAW_TOTAL` is fixed, but the layer scores use the per-crate totals). This is the same in the original grader and the fixed version, and we did not measure its effect on real submissions. Both versions also let an extra passing test hide a missing expected test, which happens only if public tests are deleted or renamed, as the task forbids.

## How much it matters

The publisher graded with the four vendored files present (defect 4 above), so for the published leaderboard the comparison that matters is the original grader plus those files against the fixed version. We measured both on the same submission bytes with the task's `eval_cmd` (`repairs/rust_multicrate_reconstruction-v2/paired/results.md`).

| Submission | Original grader + cc files | Fixed version | Change |
|---|---|---|---|
| unchanged starter | 3.8189 | 5.7236 | +1.9047 |
| complete solution (upstream code) | 73.9926 | 94.7022 | +20.7096 |
| the same, one cas-search module unfinished | 73.9926 | 93.9963 | +20.0037 |
| bad control: wrong default terminal size | 73.8926 | 94.6022 | +20.7096 |

- For the complete solution the gain is cas-search 12 × 128/136 = 11.2941, plus cas-cli 10 × 1252/1344 = 9.3155, plus the cas-pty doctest that Cargo no longer skips, 4 × 1/40 = 0.1000, for 20.7096 in total (`paired/results.md`, reference section).
- We measured fail-fast alone by grading the same submissions with the fixed version minus `--no-fail-fast`. The complete solution loses 0.4348 (94.7022 against 94.2674: the cas-pty doctest and 45 cas-cli tests that run after the property-test binary fails on its stub strategies), the partial solution 3.2583 (93.9963 against 90.7380: also 32 cas-search tests after its library tests fail), and the starter 0.9884 (5.7236 against 4.7352).
- The largest possible gain for any submission is 29.22 points. In the original grader cas-search and cas-cli score 0 for every run that leaves the tests unchanged, so the fixed version can add at most their full weights, 12 + 10 = 22. In every other crate, fail-fast can only cost tests that sit outside the crate's first test binary (the library tests, which always run) and can pass. Their counts come from a run with every binary executed (`evidence/runs/rust_multicrate_reconstruction-failfast-paired-r3/result/out/raw/v2-*`), except cas-mux, with ignored tests left out because they never pass:
  - cas-factory-protocol: 45 integration tests and 5 doctests, 10 × 50/196 = 2.5510 (layer L2, 196 tests);
  - cas-factory: 38 integration tests, 8 × 38/171 = 1.7778 (L7, 171 tests);
  - cas-store: 21 integration tests, 15 × 21/216 = 1.4583 (L4);
  - cas-tui-test: 10 integration tests and 3 doctests, 5 × 13/121 = 0.5372 (L8, 121 tests);
  - cas-pty: 1 doctest, 4 × 1/40 = 0.1000 (L3);
  - cas-mux: 17 integration tests listed by `--list` (`raw/v2-cas-mux-19.stdout`; none ran, because the crate crashes in the terminal stub, `raw/v2-cas-mux-20.stderr`), 8 × 17/171 = 0.7953 (L7).

  The other crates have no other binary with a test that can pass. The total is 22 + 7.2196 = 29.2196. cas-mux crashes in the terminal stub in every complete solution measured, which the grader expects and scores 0 in both versions; without its share the maximum is 28.4243. These counts are for the shipped tests and leave out tests a solver adds.
- In the other direction, the exemption fix can lower a score by at most 4/40 = 0.1000 per grading, the value of one wrongly forgiven cas-pty failure. The cas-cli exemption is unchanged; it could add at most 10/1344 = 0.0074.
- The gain grows with a run's progress in cas-search and cas-cli, so it can change rankings.

With the published images as shipped, a complete solution scores 27.6091 and the starter 1.4711, because 9 crates cannot build. Only someone who grades with those images sees this, and the fixed version also restores the files.

## The fix

All changes are inside the judge image's `cas_rust_benchmark.tar.gz`, which the package's `Dockerfile` rewrites; `eval_cmd` does not change. Package: `repairs/rust_multicrate_reconstruction-v2/`.

- In `judge/tools/score.py`, the test run uses `cargo test --frozen --no-fail-fast -p <crate> -- --test-threads=4`, so every test binary runs. The grader credits the exemption for cas-pty only if the excused test is among the failed tests (the one-condition fix described earlier on this page); the cas-cli rule is unchanged. Test discovery (`--list`) is unchanged.
- For cas-cli, the four hidden property tests sit in their own `proptest! { #![proptest_config(ProptestConfig::with_cases(20))] … }` block, with the starter block's configuration.
- For cas-search, each of the three async tests gets `#[cfg(feature = "parallel")]`, the gate its upstream module has. Under the default features the grader uses, Cargo does not compile them, as upstream.
- The fix restores the four vendored `vendor-deps/cc/src/target/*.rs` files, unchanged from crates.io `cc-1.2.55.crate`, whose sha256 equals the package sha256 in the shipped `.cargo-checksum.json`. `Dockerfile.work` adds them to the work image too, so a solver can build every crate offline.
- In `task.json.in`, only the two image tags change, to `…-ebv-v2`.

Scores are not comparable with the original leaderboard, since a complete solution moves from 73.99 to 94.70 in the publisher's environment. A complete solution still cannot reach 100 in either version, because ignored tests count as failures and cas-mux crashes in the terminal stub, as the grader expects.

## How we checked it

- In the paired run, the task's `eval_cmd` graded each submission verbatim, on the same submission bytes, on one E2B worker per submission (`--network none`, cargo/rustc 1.88.0), in three images: the original judge image pinned by digest; the same image with only the four vendored files added (the publisher's environment); and the fixed version, built on the worker by `materialize.sh` and `Dockerfile`. The submissions were:
  - the starter;
  - a reference: the starter with its 507 files that contain `todo!()` replaced by upstream CAS v1.0.0 (`github.com/codingagentsystem/cas` at `a0a4b5ad`). In the 182 of those files that carry hidden tests, we removed the hidden test functions again, so the grader injects them as for any solver;
  - a partial solution: the reference with `cas-search/src/metrics.rs` left as in the starter;
  - a bad control: the reference with `PtyConfig::default()` returning 25 rows (`test_pty_config_default` expects 24).

  | Submission | Original grader | Original grader + cc files | Fixed version |
  |---|---|---|---|
  | starter | 1.4711 | 3.8189 | 5.7236 |
  | reference | 27.6091 | 73.9926 | 94.7022 |
  | partial | 27.6091 | 73.9926 | 93.9963 (cas-search 120/136, against 128) |
  | bad | 27.5091 | 73.8926 | 94.6022 (cas-pty 10/11, failed = 1) |

  Jobs `evidence/runs/rust_multicrate_reconstruction-v2-paired-r2-{starter,reference,partial,bad}`, each `status: exit=0` with every arm's `score-results.json` collected. The partial and bad controls still lose their broken tests in the fixed version (8 cas-search tests, 1 cas-pty test). Round-1 jobs (`…-v2-paired-{starter,reference,partial}`) gave the same original and "+ cc files" scores; they used a first package without the cas-search change, which is how we found that defect.
- To isolate fail-fast, we graded the same submission bytes with the fixed version minus `--no-fail-fast` (jobs `…-v2-failfast-isolation-r2-{reference,partial,bad}`, and the starter from `…-v2-failfast-isolation-b`; job `…-isolation-a` ran out of disk, and we do not use it).
- For the vendored files, we listed the archive inside the pinned judge image, walked the checksums of all 741 vendored crates (only `cc` misses files), and checked the restored files against `.cargo-checksum.json`. This repository does not save the listing, but it reproduces from `cas_rust_benchmark.tar.gz` (sha256 `5e2fb3e3…`, as in `repairs/rust_multicrate_reconstruction-v2/source-lock.json`): `tar tzf` gives 44,858 entries, none with a path component named `target`; 741 entries match `vendor-deps/*/.cargo-checksum.json`; and comparing each crate's checksum file list with the archive finds missing files only in `vendor-deps/cc` (`src/target/apple.rs`, `generated.rs`, `llvm.rs`, `parser.rs`).
- To test the exemption with real Cargo, we ran the unmodified `run_crate_test` of the original grader and of the corrected one, in the original public image, on a real 11-test crate named `cas-pty` (the 10 real cas-pty test names plus one placeholder).

| Scenario (true failures) | Original grader | Corrected grader |
| --- | --- | --- |
| S1 all pass (0) | PASS 11/0 | PASS 11/0 |
| S2 only excused test fails (1), the intended exemption | PASS 11/0 | PASS 11/0 |
| **S3 excused test passes, `test_pty_config_default` fails (1)** | **PASS 11/0 (false)** | TEST_FAIL 10/1 |
| S4 excused test passes, two others fail (2) | TEST_FAIL 10/1 (one forgiven) | TEST_FAIL 9/2 |
| S5 excused test + one other fail (2) | TEST_FAIL 10/1 | TEST_FAIL 10/1 |
| S6 excused test passes, `…_with_teams_lead` fails (1) | **PASS 11/0 (false)** | TEST_FAIL 10/1 |

- For a formal check of the exemption, we used TLA+, a language for describing a system's behaviour, and its checker TLC explores every reachable state. A bounded model, `KnownFailureCredit.tla`, covers one crate with 4 tests, each ok, FAILED, ignored or absent, and up to 2 excused tests. It checks the invariants `PassSound` and `CreditSound`. On the original grader both fail; in the counterexample `outcome=<<ok,ok,ok,FAILED>>, Ex={1}`, the excused test passes, another fails, and the crate status is PASS. On the corrected rule, which is the fixed version's exemption rule for cas-pty, both hold over 2,304 distinct states with up to 1 excused test and 4,608 with up to 2. The model does not cover the other three defects (hidden-test placement, Cargo stopping at a failing binary, and the vendored files).
- Every score effect above follows from the layer weights in `score.py` and the test counts in the cited runs.

## Limits

- We ran no AI model or solver. The reference is upstream code, not a solver's; its 507 replaced files also carry upstream test helpers, which the task allows solvers to implement.
- The two compile failures hit every submission that leaves the tests unchanged. How much fail-fast and the exemption cost real submissions depends on where their failures fall, and we did not measure it.
- We infer the publisher's grading environment from the exact reproduction of its starter result; the publisher does not document it.
- The bound of 29.22 is for the shipped tests. Tests a solver adds can change crate totals in both versions.
- With `--no-fail-fast`, later test binaries now run; in the original grader Cargo would have stopped before them. If one of them crashes after earlier binaries reported results, the grader charges its tests as failures. It marks the crate `TEST_CRASH` only when no binary reported any result (`score.py`, the `executed == 0` branch). No run outside cas-mux showed such a crash.
- We built the fixed work image (`Dockerfile.work`) once, in the clean-machine rebuild check (`evidence/runs/materialize-check-rust`, `status: exit=0`), and the four restored `cc/src/target` files are in the built image with the locked sha256. We ran no solver build (`cargo build --frozen -p zstd-sys`) in it.
- The starter's property-test strategies are stubs (`Just("test")`). A solver who leaves that helper file unchanged fails a few property tests in the fixed version, where cas-cli scores 1252/1344 here, against 1258/1344 with the upstream file (`evidence/runs/rust_multicrate_reconstruction-failfast-paired-r3`), 0.045 points.
- The runs used a watcher that deletes the public phase's `target/` once the grader has built its combined workspace; without it the two builds overflow the 20.7 GB worker disk. The public phase's results are final by then.
- The exemption test crate uses the real cas-pty test names but not the real crate. The TLA+ model is bounded (4 tests, at most 2 excused) and leaves out compile-fail, timeout and crash branches, multiple test binaries and the layer weighting.
- We did not establish why the task lists `test_pty_config_claude_with_teams` as known-failing.

## Reproduce

- Fixed version and paired runs: `repairs/rust_multicrate_reconstruction-v2/` (`README.md`, `repair.patch`, `materialize.sh`, `source-lock.json`, `Dockerfile`, `Dockerfile.work`); results in `paired/results.md`, with the scripts `run-paired.sh.in`, `run-failfast.sh.in`, `build_sub.py`, `strip.py` and `diag.py`.
- Runs: `evidence/runs/rust_multicrate_reconstruction-v2-paired-*`, `…-v2-paired-r2-*` and `…-v2-failfast-*`; per-binary test counts in `evidence/runs/rust_multicrate_reconstruction-failfast-paired-r3/result/out/raw/`.
- Exemption with real Cargo: `evidence/scripts/rust_multicrate_reconstruction/run_native_fixture.sh` (outputs in `out/run.log` and `out/results.json`). It needs the source export `rust_multicrate_reconstruction_nested-000.tar.gz` (`SRC_TGZ`), which is not in this repository; the original `score.py` can instead be taken from the grader image (sha256 below).
- TLA+ model: `evidence/formal/tla/rust_multicrate_reconstruction/run_tlc.sh` (outputs in `tlc_*.out`).
- Pinned identity: grader image `seededge/edgebench.judge.rust_multicrate_reconstruction@sha256:d1d18aed02e81e5f09938de0272a76a72fab174a784613aefa3eb51443f6e408`, original `judge/tools/score.py` sha256 `d725dd934a01e40948267131d8ae91a075b4217d8012b41468cc9b38bb782b35`; fixed `score.py` sha256 `50707cd4d7e7256777fa806ba450d7185cd2d872806c4c915bd4bc119d09b545`.

Supporting records: `evidence/reviews/rust_multicrate_reconstruction.md`.
