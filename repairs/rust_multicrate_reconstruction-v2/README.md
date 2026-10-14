# rust_multicrate_reconstruction, fixed version

## What this fixes

On the published grader image, a complete, correct solution scores 27.6 out of 100. Three defects cause this, and a good-faith solver can avoid none of them:

1. **Missing vendored files.** The task's workspace archive lacks four files of the vendored `cc` crate. Cargo then refuses to build the 9 of 14 crates that use `cc`, and the grader scores them as crashed.
2. **Hidden tests that do not compile.** The grader appends hidden tests to two crates' test files in places where they do not compile: cas-search (12 points) and cas-cli (10 points). The whole crate then scores 0, for every solver who leaves the test files unchanged, as the task requires.
3. **Cargo stops at the first failing test file.** Tests in a crate's later test files then never run, and the grader counts them as failed.

The fixed version keeps the earlier one-condition fix to the cas-pty exemption, and adds fixes for these three defects. With the fixed version, the complete solution scores 94.70 and the unchanged starter scores 5.72. With the published image, they score 27.61 and 1.47.

### The problem in detail

**Missing vendored files.**
- `cas_rust_benchmark.tar.gz` holds the workspace, the grader and the hidden tests, and `eval_cmd` unpacks it. It has 44,858 entries. None of them is a path containing a directory named `target`.
- The vendored `cc` 1.2.55 crate has a directory named `target`: `vendor-deps/cc/src/target/` (`apple.rs`, `generated.rs`, `llvm.rs`, `parser.rs`). Those four files are therefore missing. They are listed in `vendor-deps/cc/.cargo-checksum.json`. Of the 741 vendored crates, `cc` is the only one with files missing (how to reproduce the listing and the checksum walk: `cases/rust_multicrate_reconstruction.md`, "Vendored files").
- Cargo checks that list, so it refuses the vendored `cc`. Every crate that builds with `cc` then fails before any test runs. The grader scores them `TEST_CRASH`: cas-code, cas-recording, cas-store, cas-search, cas-core, cas-mux, cas-factory, cas-mcp and cas-cli.
- `eval_cmd` deletes the submission's `vendor-deps/`, and `submit_exclude` drops it, so a solver cannot supply the files.
- The work image's starter lacks the same four files. Building `zstd-sys`, which depends on `cc`, fails there with `failed to open file …/vendor-deps/cc/src/target/apple.rs`, so the solver cannot build or test these crates offline either.

**cas-cli: hidden property tests outside `proptest!`.**
- In `cas-cli/tests/proptest/search_properties.rs`, the hidden tests are four property tests written in `proptest!` syntax (`fn search_never_crashes(query in search_query_strategy())`). Upstream, they sit inside the file's `proptest! { … }` block.
- The starter keeps that block but without these four tests. For files under `tests/`, the grader (`score.py` `inject_hidden_tests`) appends the snippet to the end of the file, after the block.
- The file then does not compile (`expected one of ':', '@', or '|', found keyword 'in'`; `functions used as tests can not have any arguments`). cas-cli, layer L9, scores 0 of 1344.

**cas-search: hidden async tests outside their feature gate.**
- Three hidden tests are `#[tokio::test]` async tests: `test_async_hybrid_search` in `src/hybrid.rs`, `test_async_remove` in `src/bm25_tests/tests.rs`, and `test_async_hybrid_search` in `tests/hybrid_integration.rs`. Upstream, each sits in a `#[cfg(feature = "parallel")] mod async_tests`, which default `cargo test` does not compile.
- The grader appends them outside that module: at the end of the last `#[cfg(test)]` module, or at the end of the file.
- They then fail to compile: `tokio` is an optional dependency, and `search_async` and `AsyncBm25Index` exist only with the `parallel` feature. cas-search, layer L5, scores 0 of 136.

**Cargo fail-fast.** `run_crate_test` runs `cargo test --frozen -p <crate> -- --test-threads=4` without `--no-fail-fast` (`score.py:266-268`). After one test binary fails, Cargo runs no later binary of that crate, and the grader adds the tests that did not run to the failures (`:329-331`). For example, the intended known failure in cas-pty's library tests stops cas-pty's doctest, so a complete solution gets 10 of 11 instead of 11 of 11. Measured on the same submissions, with only this flag removed from the fixed version: the complete solution loses 0.43 points (the cas-pty doctest, and 45 cas-cli tests after the `proptest_test` binary fails on the stub strategies), and the partial solution loses 3.26 points (32 more cas-search tests after its library tests fail). See [paired/results.md](paired/results.md).

**Exemption (earlier fix, kept).** The grader credits the cas-pty known failure if the excused test's name appears anywhere in the output, not only when that test failed. See `../../cases/rust_multicrate_reconstruction.md`.

## What changes

Everything is in the judge image's `cas_rust_benchmark.tar.gz`, which `Dockerfile` rewrites. `eval_cmd` does not change.

- **`files/judge/tools/score.py`**: the earlier exemption fix (credit the cas-pty exemption only if the excused test is among the failed tests) is unchanged. The test run now uses `cargo test --frozen --no-fail-fast -p <crate> -- --test-threads=4`. Test discovery (`--list`) is unchanged.
- **`files/judge/hidden-tests/hidden-sources/cas-cli/tests/proptest/search_properties.rs`**: the four hidden tests are wrapped in their own `proptest! { #![proptest_config(ProptestConfig::with_cases(20))] … }` block, with the same configuration as the starter's block.
- **`files/judge/hidden-tests/hidden-sources/crates/cas-search/{src/hybrid.rs, src/bm25_tests/tests.rs, tests/hybrid_integration.rs}`**: each hidden async test gets `#[cfg(feature = "parallel")]`, the gate its upstream module has. Under the default features the grader uses, these tests are not compiled, as upstream.
- **`files/vendor-deps/cc/src/target/*.rs`**: the four missing files, unchanged from the crates.io `cc-1.2.55.crate`. That crate's sha256 equals the package sha256 recorded in the shipped `.cargo-checksum.json`, and each file's sha256 matches its entry there.
- **`Dockerfile.work`**: the work image gets the same four files, so a solver can build every crate offline.
- **`task.json.in`**: only the two image tags change, to `…-ebv-v2` (`task-json.diff`).

**Score compatibility:** fixed-version scores are not comparable with the original leaderboard. On the published image, a complete solution scores 27.61. With only the vendored files restored (the closest available match to the publisher's own grading, below), it scores 73.99. With the fixed version, it scores 94.70.

## How it was checked

Each submission was graded on the same E2B worker by the task's `eval_cmd`, verbatim, in three images:

- **orig**: the pinned original judge image.
- **origcc**: the original image with only the four `cc` files restored.
- **v2**: this package, built by `materialize.sh` and `Dockerfile` on the worker.

The submissions:

- **starter**: the unchanged starter.
- **reference**: the starter with its 507 `todo!()` files replaced by upstream CAS v1.0.0. In the 182 files that carry hidden snippets, the hidden test functions are removed again, so the grader has to inject them, as for any solver.
- **partial**: the reference with `cas-search/src/metrics.rs` left as in the starter.
- **bad**: the reference with `PtyConfig::default()` returning 25 rows instead of 24.

Results: [paired/results.md](paired/results.md).

- **starter**: origcc reproduces the publisher's recorded starter result (`judge/skeleton-score.json`: score 3.8189, public score 3.3913, 66 tests passed) exactly, crate by crate.
- **reference**: 27.6091 (orig), 73.9926 (origcc), 94.7022 (v2).
- **partial and bad**: each loses only the tests its change breaks.

## Limits

- The reference is upstream CAS v1.0.0, not code from a solver. Its 507 replaced files also carry upstream test helpers. The task allows solvers to implement those.
- Even the complete solution cannot reach 100. Ignored tests count as failures, cas-mux crashes in the ghostty stub as the grader expects (0/37), and a few tests fail in the image. All this is the same in the original grader and the fixed version.
- The starter's proptest strategies are stubs (`Just("test")`). With the fixed version, some of the property tests fail for a solver who leaves that test-helper file unchanged: cas-cli scores 1252/1344 here, against 1258/1344 in an earlier run that used the upstream file (`evidence/runs/rust_multicrate_reconstruction-failfast-paired-r3`). That is 0.045 points.
- The cas-cli exemption still matches the test's name anywhere in the output, as before. With `--no-fail-fast`, more of the output is printed, so the name appears more often. The cap stays 10/1344 = 0.0074 points.
- The runs used `CARGO_BUILD_JOBS=8` and a watcher that deletes the public phase's `target/` once score.py has made its combined workspace. The public phase's results are already final by then, and the combined copy skips `target/`. Without the watcher, the two builds overflow the 20.7 GB worker disk.
- With `--no-fail-fast`, a test binary that crashes after earlier binaries reported results has its tests charged as failures; the crate is `TEST_CRASH` only when no binary reported any result (`score.py`, the `executed == 0` branch).
- The fixed work image was built once (`evidence/runs/materialize-check-rust`), but no `cargo build --frozen -p zstd-sys` was run in it.

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t edgebench.judge.rust_multicrate_reconstruction:b749374fe7bc-ebv-v2 . \
  && docker build -f Dockerfile.work -t edgebench.work.rust_multicrate_reconstruction:7f639fc9d090-ebv-v2 .
```

`materialize.sh` takes the following steps:

1. Pull the pinned judge image by digest, unless it is already present.
2. Copy `cas_rust_benchmark.tar.gz` out of it with `docker create` and `docker cp`. No container runs in this step.
3. Check the archive's sha256, extract the five originals and check each one against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Download `cc-1.2.55.crate` from crates.io, check its sha256, and extract the four files.
6. Verify every output's sha256.

**This package is generated by its own script, not by `tools/make_materialize.py`.** That tool has no step for files inside an archive or for crates.io files. `materialize.sh`, `source-lock.json` and `repair.patch` (with `diff -u`) are written, in the same layout as the other packages, by `gen_package.py`, which is kept internally at `.internal/repairs/rust_multicrate_reconstruction-v2/tools/gen_package.py` and is not published. Run on a clean copy, `materialize.sh` reproduced `files/` byte for byte (9 of 9 outputs verified). The clean-machine rebuild check (`evidence/runs/materialize-check-rust`, `status: exit=0`) ran it unchanged on a fresh E2B worker, built both `Dockerfile` and `Dockerfile.work`, and found every copied file in both images with the locked sha256. No solver build was run in the built work image.
