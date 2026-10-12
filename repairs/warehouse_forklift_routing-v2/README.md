# Warehouse Forklift Routing, fixed version: the grader's time limit matches the promised 30 s per test case

## What this fixes

The prompt promises 30 s per test case, which is 150 s for each five-case input, but the original grader allows only 60 s per input, and one timeout voids the whole submission. The fixed grader allows the promised 150 s per input. The score scale is unchanged, and its proven ceiling of about 30.3 out of 100 is documented.

## What changes

### The problem in detail

See the [review](../../evidence/reviews/warehouse_forklift_routing.md), H5. The prompt and the
README both promise "Time limit: 30 seconds per test case", and both say "T=5 test cases per
input". Each of the 50 grading inputs therefore carries a promised budget of 5 × 30 s = 150 s. The
grader `/tmp/eval_warehouse_manager.py` runs `solution.py` once per input with
`TIME_LIMIT = 60`, which is 12 s per test case on average. A timeout scores `inf`, and the harness
rejects any CASE result that is not finite, so a single timeout invalidates the whole submission. In the review's
run on the original grader, an honest solver that spent 13 s per test case (less than half the promise) got
50/50 TLE (time limit exceeded) and an invalid submission. The local tools give no warning, because `tools/bin/tester`
only scores an output file and does not time anything.

### Exact change

One file is changed, `/tmp/eval_warehouse_manager.py`, at one line:
`TIME_LIMIT = 60` becomes `TIME_LIMIT = 150` (`repair.patch`). The value comes straight from the
prompt: 30 s per test case × T=5 test cases per input. The file keeps mode 0755 and is 2340 bytes
instead of 2339. In the task JSON, only `judge.image_tag` changes (`task.json.in`).
`eval_timeout` stays at 3600. With 8 inputs graded in parallel, the worst case is
7 waves × (150 s + 30 s tester) = 1260 s, which is well under 3600. Nothing changes in the work
image, prompt, README, tester, cases, parser or selection.

### Why this is the smallest change

The timeout feeds only the `subprocess.run(..., timeout=TIME_LIMIT)` call for the
solution. Any run that finished within 60 s under the original version finishes, and is scored, the same way under
the fixed version: same stdout, same tester and same totals. The only runs whose result changes are those
that took between 60 and 150 s. The original marked them TLE/`inf`, and the fixed version scores their output. The other
fix the review suggests, rewording the prompt to "60 s per input", would make the task consistent by withdrawing a promise that solvers have already been shown. Raising the limit keeps
the promise that was made.

### Are scores comparable?

Scores from the fixed version equal those from the original for every submission whose solver finishes
each input within 60 s. They are not comparable for a submission that takes 60–150 s on any
input: the original invalidates the whole submission, while the fixed version scores it. A run near the limit can also
change outcome with machine speed, as in any timed task.

### Score scale: kept unchanged, with a proven ceiling (decision 2026-10-12)

The reference points of the `piecewise_log_min` score scale are unchanged in the fixed version. A Lean 4 proof, checked by Lean's kernel and
recompiled independently ([review](../../evidence/reviews/warehouse_lower_bound_lean.md)), shows that every valid submission
has a raw TOTAL ≥ 198283458104808536/278277680055375 ≈ 712.538 on these 50 inputs (lower is better). The rank1 (395.80)
and super_anchor (293.51) reference points are therefore out of reach, and **no valid submission can score
above ≈30.3 out of 100**. The scale is not given new reference points: the proven floor is a lower bound, not a known
optimum. Putting 100 there would move the original rank-30 reference point from 20 to 96.5, which would be an
invented recalibration. Keeping the reference points keeps scores comparable with the original version. The release notes
state the ceiling of ≈30.3, as is done for the disclosed 30-point cap of the Bipedal task.

## How it was checked

Side-by-side run of the original and fixed graders: [paired/results.md](paired/results.md). In plain words: a generic valid test submission gets the same TOTAL of 46676.8 under both graders. Submissions with a bug, and the shipped starter, are rejected under both. A solver that uses 13 s per test case, within the promised budget, times out on all 50 inputs under the original grader and is scored normally (TOTAL 46676.8) under the fixed one.

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t ebv/warehouse_forklift_routing-judge:v2 .
```

`materialize.sh` takes the following steps:

1. Pull the pinned image(s) by digest, unless already present.
2. Extract the original files with `docker create` and `docker cp`. No container runs in this step.
3. Check each original against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of every file under `files/` (and `orig/`) against `source-lock.json` → `materialize.outputs`. Any mismatch fails loudly.

After that, the `Dockerfile` builds without changes. Regenerated files keep the file mode they have in the image.
See `../MATERIALIZE-CHECK.md` for how each package was verified.

## Limits

- This fixes only the time limit; the ceiling of the score scale is documented, not changed (above).
- The test submissions with a time budget use `sleep` to model a solver that spends its budget. They show that
  the limit is enforced per input as promised. They do not model CPU contention from a solver
  that actually computes for 150 s while 8 inputs run in parallel. `eval_cmd` sets no CPU
  allocation, so the speed of a solver limited by CPU depends on the machine.
- The valid test submission is generic and weak (0.0 out of 100). The score of a competitive solver is
  not measured.
- Each test submission ran once on one E2B cloud worker.
