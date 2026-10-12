# Warehouse Forklift Routing (`warehouse_forklift_routing`)

**Decision:** Repair (v2). The evaluator gives 60 s per five-case input while the prompt promises 30 s per test case; v2 raises the limit to the promised 150 s per input, keeps the rescale anchors unchanged and documents a proven ceiling of about 30.3 normalized points.

## What the task asks for

The task is an adaptation of CodeChef WAREHOUS. The solver must output forklift command strings that store R·C−1 arriving goods on an R x C grid and then dispatch them in order. The goal is to "Minimize the total instruction string length". The prompt states "T=5 test cases per input" and "Time limit: 30 seconds per test case". The README says "Final score = sum of per-input average scores." Category: Combinatorial Optimization.

## What goes wrong

### 1. The time limit is stricter than promised

**Rule.** The prompt promises 30 s per test case, with 5 test cases per input, which is 150 s per input. The evaluator sets `TIME_LIMIT = 60` for the whole input and runs 8 inputs in parallel. A timeout scores `inf`, and the harness rejects any nonfinite CASE, so a single timeout invalidates the whole submission.

**Example, original evaluator.** A time-budgeted control (it sleeps) that spends 13 s per test case, less than half the promised limit, gets 50 TLE and an invalid submission. Expected under the prompt: all 50 inputs scored.

**Why it matters.** The local tools give no warning, because `tools/bin/tester` only scores an output file. A solver that follows the promised budget loses its whole score.

### 2. The rescale anchors cannot be reached

**Rule.** Every string the tester accepts satisfies S ≥ 2RC(R+C−1) − 6(R+C−2) − 2. Every valid per-case score is therefore ≥ 20 − 6(R+C−2)/(R+C−1). On the 50 judge inputs every valid TOTAL is ≥ 198283458104808536/278277680055375 ≈ 712.538, which stays above rank1 even after display rounding.

**Example.** TOTAL ≥ 712.538 > rank1 395.80; super_anchor (293.51) is also below it. Under the task's own rescale, no valid submission can score above about 30.3 normalized points (30.308 at the exact bound; 30.586 at the 710.2 display-rounding floor).

**Why it matters.** The normalized scale has a ceiling well below 100. Ordering is preserved.

### Checked and not material

- **Disclosed rule change.** The tester lets an empty forklift enter occupied cells. This is looser than the original CodeChef rule, but the prompt states it. Solvers that follow either rule are accepted.
- The diagonal construction scores exactly 20.0. Adding an E,W detour gives 20.2.
- The tester prints each input's score to 1 dp. This shifts TOTAL by at most 2.5 raw, or about 0.2 normalized points.
- Failures aggregate to `inf` and invalidate the submission, which matches the README's "sum".
- Scoring is deterministic.
- The data are well-formed. Seed replay 0..300,000 reproduced none of the 50 judge files, so the judge inputs are not in the public seed range.

## Impact

- **Time limit:** a solver that takes 60–150 s on any input, within the promised budget, loses its whole score. Faster solvers are unaffected.
- **Ceiling:** every solver's normalized score is capped at about 30.3.

## Fix (v2)

v2 changes one line in `/tmp/eval_warehouse_manager.py`: `TIME_LIMIT = 60` becomes `TIME_LIMIT = 150`. The value is 30 s per test case × T=5, as the prompt promises. `eval_timeout` stays at 3600. The task JSON changes only `judge.image_tag`. The work image, prompt, README, tester, cases, parser, selection and rescale are unchanged.

The `piecewise_log_min` anchors are kept rather than re-anchored. The proven floor is a lower bound, not a known optimum, so putting 100 there would be an invented recalibration. Keeping the anchors preserves comparability with v1. Release notes state the ≈30.3 ceiling.

| Submission | Role | v1 | v2 |
| --- | --- | --- | --- |
| generic valid control | valid | OK 50/50, TOTAL 46676.8 | OK 50/50, TOTAL 46676.8 |
| one honest bug | invalid | 49 OK + 1 WA → inf | 49 OK + 1 WA → inf |
| shipped starter | invalid | 50 WA → inf | 50 WA → inf |
| **13 s per test case (uses the promised budget)** | **trigger** | **50 TLE → inf** | **50 OK, TOTAL 46676.8** |
| near the 150 s per-input limit | trigger | 50 TLE → inf | 50 OK, TOTAL 46676.8 |

**Score compatibility.** v2 scores equal v1 scores for every submission whose solver finishes each input within 60 s. The two are not comparable for a submission that takes 60–150 s on any input: v1 invalidates the whole submission, while v2 scores it. A run near the limit can also change outcome with machine speed, as in any timed task. Because the anchors are unchanged, the normalized scale (including the ≈30.3 ceiling) is the same in v1 and v2.

## How we know

- **Original evaluator in the pinned image.** The verbatim `eval_cmd` ran in the judge image (`sha256:ac7fdf03…`) with `--network none` and the solution mounted read-only, graded by the repository harness. Arms: a generic valid control, a repeat of that control, the shipped starter, a control with one honest bug, and time-budgeted solvers. 16 authored fixtures ran through the tester in the judge image with 0 mismatches against the oracle's predictions.
- **Independent oracle.** A simulator written from the statement text, with exact `Fraction` scoring and two rule modes (the prompt's rule and the stricter CodeChef rule). A differential test against the original tester bytes used 20,000 random command strings plus 2,000 control outputs (half of them with one-character edits); all agreed. Exact tiny-grid optima came from Dijkstra on 2x2, 2x3 and 3x2, under both rule sets. Data checks covered all 50 judge inputs (250 subcases) and generator seeds 0..300,000.
- **Formal check (Lean 4).** The per-case bound is the theorem `EbvWarehouse.lower_bound` in `formal/lean/ebv/Ebv/WarehouseBound.lean`, kernel-checked under Lean v4.34.1 and Mathlib `d13f23b7` with no `sorry` and no `native_decide`, and recompiled independently. It depends only on Lean's standard axioms `[propext, Classical.choice, Quot.sound]`. `EbvWarehouse.score_bound` gives the per-case score bound. In `Ebv/WarehouseData.lean`, `totalLB_eq` and `totalLB_gt` give the TOTAL bound, and `displayed_gt_rank1` covers display rounding. The theorem is not vacuous: the model accepts a 42-character optimum (`opt23_accepted`), and a stronger bound without the −6(R+C−2) term is proved false (`too_strong_bound_false`); that stronger bound fails on 239 of 248 brute-force optima. The proof does not use the movement-occupancy guard, so it holds under both the prompt's rule and the CodeChef rule.
- **Repeatability.** The paired evaluation was run three times; no verdict changed (`paired-repeatability.md`).

## Limits

- No model or solver was run. Effects are shown on authored controls only.
- The valid control is generic and weak (normalized 0.0). No competitive solver was built, so the best achievable score between the floor (712.5 raw) and about 1000 raw (the diagonal construction) is not measured.
- The time-budget controls use `sleep`. They show that the limit is enforced per input as promised. They do not model CPU contention from 8 compute-bound inputs running in parallel, and `eval_cmd` sets no CPU allocation.
- The match between the Lean model and the tester is a line-by-line hand mapping backed by a 294-string runtime differential test with 0 mismatches, not a kernel-checked proof. The case hypotheses (permutation, last arrival ≠ 1) and the extraction of (R,C) were checked in Python. The normalized ceiling comes from the harness's float rescale code, not from Lean.
- The origin of the anchors is unknown.
- Scorer isolation is outside this release's scope (an EdgeBench design choice); good-faith findings are reported above.

## Reproduce

- Native checks: `evidence/scripts/warehouse_forklift_routing/` (`oracle_sim.py`, `diff_fuzz.py`, `authored_cases.py`, `data_and_bound.py`, `tiny_optimum.py`, `native/run_native.sh`, `harness_grade.py`; checksums in `SHA256SUMS`).
- Lean bound: `evidence/formal/lean/ebv/Ebv/Warehouse{Bound,Check,Data}.lean`, compiled with `evidence/scripts/warehouse_forklift_routing/lean_bound/compile_capped.sh`. Exact totals: `lean_bound/recompute_total.py`. Brute force: `lean_bound/brute_force.py`.
- Paired evaluation: `repairs/warehouse_forklift_routing-v2/paired/run.sh` (as run: `evidence/runs/warehouse_forklift_routing-v2-paired-b/run.sh`).
- Pinned identity: judge image `seededge/edgebench.judge.warehouse_forklift_routing@sha256:ac7fdf03…`; `/tmp/eval_warehouse_manager.py` sha256 `c5ff0c26…`; `tools/bin/tester` sha256 `277f4841…`; the 50 judge inputs (concatenated) sha256 `04b8cd29…`; task JSON sha256 `78002570…`.
- Supporting records: `repairs/warehouse_forklift_routing-v2/` (README, `repair.patch`, `source-lock.json`), `evidence/reviews/warehouse_forklift_routing.md`, `evidence/reviews/warehouse_lower_bound_lean.md`.
