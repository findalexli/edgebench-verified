# warehouse_forklift_routing v2: evaluator time limit matches the promised 30 s per test case

**Defect** ([review](../../evidence/reviews/warehouse_forklift_routing.md), H5). The prompt and the
README both promise "Time limit: 30 seconds per test case", and both say "T=5 test cases per
input". Each of the 50 judge inputs therefore carries a promised budget of 5 × 30 s = 150 s. The
evaluator `/tmp/eval_warehouse_manager.py` runs `solution.py` once per input with
`TIME_LIMIT = 60`, which is 12 s per test case on average. A timeout scores `inf`, and the harness
rejects any nonfinite CASE, so a single timeout invalidates the whole submission. In the review's
native run, an honest solver that spent 13 s per test case (less than half the promise) got
50/50 TLE and an invalid submission. The local tools give no warning, because `tools/bin/tester`
only scores an output file and does not time anything.

**Change.** One file is changed, `/tmp/eval_warehouse_manager.py`, at one line:
`TIME_LIMIT = 60` becomes `TIME_LIMIT = 150` (`repair.patch`). The value comes straight from the
prompt: 30 s per test case × T=5 test cases per input. The file keeps mode 0755 and is 2340 bytes
instead of 2339. In the task JSON, only `judge.image_tag` changes (`task.json.in`).
`eval_timeout` stays at 3600. With 8 inputs graded in parallel, the worst case is
7 waves × (150 s + 30 s tester) = 1260 s, which is well under 3600. Nothing changes in the work
image, prompt, README, tester, cases, parser or selection.

**Why minimal.** The timeout feeds only the `subprocess.run(..., timeout=TIME_LIMIT)` call for the
solution. Any run that finished within 60 s under v1 finishes, and is scored, the same way under
v2: same stdout, same tester and same aggregation. The only runs whose result changes are those
that took between 60 and 150 s. v1 marked them TLE/`inf`, and v2 scores their output. The other
fix the review suggests, rewording the prompt to "60 s per input", would make the contract
consistent by withdrawing a promise that solvers have already been shown. Raising the limit keeps
the promise that was made.

**Score compatibility.** v2 scores equal v1 scores for every submission whose solver finishes
each input within 60 s. They are not comparable for a submission that takes 60–150 s on any
input: v1 invalidates the whole submission, while v2 scores it. A run near the limit can also
change outcome with machine speed, as in any timed task.

**Anchors: kept unchanged, with a proven ceiling (decision 2026-10-12).** The
`piecewise_log_min` anchors are unchanged in v2. A Lean 4 proof, kernel-checked and independently
recompiled ([review](../../evidence/reviews/warehouse_lower_bound_lean.md)), shows that every valid submission
has raw TOTAL ≥ 198283458104808536/278277680055375 ≈ 712.538 on these 50 inputs. The rank1 (395.80)
and super_anchor (293.51) anchors are therefore unreachable, and **no valid submission can score
above ≈30.3 normalized**. We do not re-anchor: the proven floor is a lower bound, not a known
optimum, and putting 100 there would move the original rank-30 reference from 20 to 96.5, an
invented recalibration. Keeping the anchors preserves comparability with v1 scores. Release notes
state the ≈30.3 ceiling, as for Bipedal's disclosed 30-point cap.

**Paired evaluation:** [paired/results.md](paired/results.md).

**Limits.**
- This fixes only the time contract; the anchor ceiling is documented, not changed (above).
- The time-budget controls use `sleep` to model a solver that spends its budget. They show that
  the limit is enforced per input as promised. They do not model CPU contention from a solver
  that actually computes for 150 s while 8 inputs run in parallel. `eval_cmd` sets no CPU
  allocation, so a CPU-bound solver's speed depends on the machine.
- The valid control is generic and weak (normalized 0.0). The score of a competitive solver is
  not measured.
- Each arm ran once on one E2B worker.

## Build

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
