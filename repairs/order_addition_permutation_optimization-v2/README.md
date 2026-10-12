# order_addition_permutation_optimization v2: correct the expected helper fingerprint

## Defect

`tests/test_final_result.py::test_private_judge_files_are_available` checks the installed
private score helper `tests/score_vcpom_result.py` against a hard-coded sha256:

- **Expected:** `3023b9a4…`. This is the hash of an earlier helper with Chinese comments.
- **Installed:** `337837af…`. A later image layer replaced the helper with an English-comment
  translation whose code is functionally identical.

As a result, one of the five tests fails for every submission. Per-submission `TOTAL_SCORE`
values are still correct, but the pass rate is capped at 0.8. Under the task's
`selection: pass_rate_first`, scores are compared only when both pass rates are 1.0. The
run-level best therefore stays on the first valid submission, and later improvements are
ignored. Review: `evidence/reviews/order_addition_permutation_optimization.md`.

## Exact change

One literal in one file, shown in `repair.patch` (generated with `diff -u`):

```
-EXPECTED_SCORE_HELPER_SHA256 = "3023b9a449119e862d4ca86d3ab45599e2496e182be82959a642522f915dbbac"
+EXPECTED_SCORE_HELPER_SHA256 = "337837af7067b3dae8d4ef068d26d8dd8ff779f9a627d95451af2ca411c99630"
```

- The replacement checker `files/home/workspace/complex_job_scheduling/tests/test_final_result.py`
  (6265 bytes, sha256 `37e7bae6…`) is byte-identical to the frozen candidate of the earlier
  reviewed recipe `repairs/order-helper-integrity-v1/`. It was rebuilt here from the original
  image's checker by changing only this literal.
- The helper, `.so`, baseline file, prompt, work image, parser, selection and rescale are all
  unchanged.
- `task.json.in` changes only `judge.image_tag` (`f6f385925889` to `f6f385925889-ebv-v2`).
- The Dockerfile is `FROM` the pinned original judge digest plus one `COPY`.

**Why this is minimal.** The other correct fix would revert the helper to its old bytes, which
would undo the translation. Dropping the hash check would remove an integrity check that does
work.

## The earlier failed pilot (`evidence/selected/order-repair-failed-pilot.json`)

That pilot recorded "invalid capture with zero tests". The saved records show:

- It was a heavy transport experiment: original work-image collection, then a docker-save /
  restore of the candidate judge image, then a capped native backend.
- The judge ran with `timeout=30` and a 1 CPU / 1 GiB, file-capped backend.
- The 711-byte capture was never exported, and its cause is recorded as UNKNOWN.
- Nothing in it points at the checker literal. Zero parsed tests means pytest never produced
  a test report in that restored container.

This package avoids the failure mode as follows:

- The v2 image is built directly in the worker from the pinned base. There is no save/restore.
- A preflight in each image hashes `tests/*` and checks that `pytest --collect-only` collects
  5 tests.
- Each judgement uses the TaskSpec `eval.sh` with the task's own 600 s timeout.
- Every raw capture is saved and graded afterwards with the repo harness.

Both preflights collected 5 tests, and every capture parsed 5 test results.

## Score compatibility

Per-submission raw and normalized scores are unchanged, bit for bit. Pass rates change: a
legal submission now gets 5/5 instead of 4/5. Run-level `best_score` / `best_round` under
`pass_rate_first` are therefore not comparable with v1 whenever a run had more than one valid
submission and a later one scored higher. v1 kept the first; v2 keeps the best.

## Paired evaluation

See `paired/results.md`. **Accepted.**

## Limits

- The submissions are simple controls (identity, and 60 s of random-swap search), far from
  the reference cost. The selection effect does not depend on score magnitude.
- The selection was computed with the repo's `select_best` on the saved reports, not through a
  live `judge_server` run. The work image was not executed.

## Build

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t ebv/order_addition_permutation_optimization-judge:v2 .
```

`materialize.sh` takes the following steps:

1. Pull the pinned image(s) by digest, unless already present.
2. Extract the original files with `docker create` and `docker cp`. No container runs in this step.
3. Check each original against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of every file under `files/` (and `orig/`) against `source-lock.json` → `materialize.outputs`. Any mismatch fails loudly.

After that, the `Dockerfile` builds without changes. Regenerated files keep the file mode they have in the image.
See `../MATERIALIZE-CHECK.md` for how each package was verified.

The task JSON change is in `task-json.diff`.
