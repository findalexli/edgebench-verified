# order_addition_permutation_optimization, fixed version: correct the expected helper fingerprint

## What this fixes

One grader test compares a helper file against an outdated sha256 fingerprint, so it fails for every submission, even though only the file's comments changed. Each submission's own score stays correct, but under this task's rule for picking a run's best submission, the run stays on its first valid submission and ignores better later ones. The fixed version expects the current file's fingerprint, so correct submissions pass all five tests and the best submission is chosen.

### The problem in detail

`tests/test_final_result.py::test_private_judge_files_are_available` checks the installed
private score helper `tests/score_vcpom_result.py` against a hard-coded sha256:

- **Expected:** `3023b9a4…`. This is the fingerprint of an earlier helper with Chinese comments.
- **Installed:** `337837af…`. A later image layer replaced the helper with an English-comment
  translation whose code works identically.

As a result, one of the five tests fails for every submission. Each submission's `TOTAL_SCORE`
is still correct, but the pass rate is capped at 0.8. The task's rule
`selection: pass_rate_first` keeps the submission that passes the most tests, and compares scores only when both pass rates are 1.0. The
run's best therefore stays on the first valid submission, and later improvements are
ignored. Review: `evidence/reviews/order_addition_permutation_optimization.md`.

## What changes

One value in one file, shown in `repair.patch` (generated with `diff -u`):

```
-EXPECTED_SCORE_HELPER_SHA256 = "3023b9a449119e862d4ca86d3ab45599e2496e182be82959a642522f915dbbac"
+EXPECTED_SCORE_HELPER_SHA256 = "337837af7067b3dae8d4ef068d26d8dd8ff779f9a627d95451af2ca411c99630"
```

- The replacement test file `files/home/workspace/complex_job_scheduling/tests/test_final_result.py`
  (6265 bytes, sha256 `37e7bae6…`) is byte-identical to the frozen candidate of the earlier
  reviewed recipe `repairs/order-helper-integrity-v1/`. It was rebuilt here from the original
  image's test file by changing only this value.
- These are all unchanged: the helper, `.so`, baseline file, prompt, agent's working image, parser, the rule for picking the best submission and the
  score scale.
- `task.json.in` changes only `judge.image_tag` (`f6f385925889` to `f6f385925889-ebv-v2`).
- The Dockerfile is `FROM` the pinned original grader digest plus one `COPY`.

**Why this is minimal.** The other correct fix would revert the helper to its old bytes, which
would undo the translation. Dropping the fingerprint check would remove an integrity check that does
work.

### The earlier failed pilot (`evidence/selected/order-repair-failed-pilot.json`)

That pilot recorded "invalid capture with zero tests". The saved records show:

- It was a heavy transport experiment: collection from the original working image, then a docker-save /
  restore of the candidate grader image, then a capped native backend.
- The grader ran with `timeout=30` and a 1 CPU / 1 GiB, file-capped backend.
- The 711-byte capture was never exported, and its cause is recorded as UNKNOWN.
- Nothing in it points at the expected-fingerprint value. Zero parsed tests means pytest never produced
  a test report in that restored container.

This package avoids that failure as follows:

- The fixed image is built directly on the cloud machine from the pinned base. There is no save/restore.
- A check in each image, before grading, hashes `tests/*` and confirms that `pytest --collect-only` collects
  5 tests.
- Each grading uses the TaskSpec `eval.sh` with the task's own 600 s timeout.
- Every raw capture is saved and graded afterwards with EdgeBench's harness (`sforge` at `6e4e5f4`).

Both pre-grading checks collected 5 tests, and every capture parsed 5 test results.

### Score compatibility

Each submission's raw result and score out of 100 are unchanged, bit for bit. Pass rates change: a
legal submission now gets 5/5 instead of 4/5. The run's `best_score` / `best_round` under
`pass_rate_first` are therefore not comparable with the original version whenever a run had more than one valid
submission and a later one scored higher. The original version kept the first; the fixed version keeps the best.

One further change comes from the harness rather than the task: when no submission in a run has a score, `pass_rate_first` reports the pass rate itself as `best_score`. A run whose only submission is rejected for its cost therefore reports 0.6 under the original version and 0.8 under the fixed one (`evidence/formal/notes/order_addition_permutation_optimization.md`). In both versions that value is higher than every valid submission's score measured here (3.3e-09 to 0.0094 out of 100, `paired/graded.md`).

## How it was checked

A side-by-side run of the original and fixed graders on the same test submissions. See `paired/results.md`. **Accepted.** Correct submissions pass 4 of 5 tests under the original grader and 5 of 5 under the fixed grader, with identical scores.

## Limits

- The submissions are simple test submissions (identity, and 60 s of random-swap search), far from
  the reference cost. The effect on the choice of best submission does not depend on score size.
- The choice of best submission was computed with EdgeBench's `select_best` on the saved reports, not through a
  live `judge_server` run. The agent's working image was not run.

## Build and use

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
