# Warehouse Forklift Routing (`warehouse_forklift_routing`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Combinatorial Optimization
- **Decision:** Repair v2. The evaluator gave 60 s per five-case input, while the prompt promises 30 s per test case. v2 raises the limit to the promised 150 s per input. The rescale anchors are kept unchanged by decision, and a proven ceiling of about 30.3 normalized points is documented.

## What the task promises

The task is an adaptation of CodeChef WAREHOUS. The solver must output forklift command strings that store R·C−1 arriving goods on an R x C grid and then dispatch them in order. The goal is to "Minimize the total instruction string length". The prompt states "T=5 test cases per input" and "Time limit: 30 seconds per test case". The README says "Final score = sum of per-input average scores."

## What we checked and how

- Wrote an independent simulator from the statement text, with exact `Fraction` scoring. It has two rule modes: the prompt's rule, and the stricter original CodeChef rule.
- Ran a differential test against the original tester bytes: 20,000 random command strings plus 2,000 control outputs (half of them with one-character edits). All agreed.
- Ran 16 authored fixtures through the tester inside the judge image. There were 0 mismatches against the oracle's predictions.
- Ran native end-to-end tests with the verbatim `eval_cmd` (`--network none --memory 2g --cpus 2`, solution mounted read-only), graded by the repository harness. Arms: a generic valid control, a repeat of that control, the shipped starter, a control with one honest bug, and a time-budgeted solver.
- Checked the data on all 50 judge inputs (250 subcases) and replayed generator seeds 0..300,000.
- Computed exact tiny-grid optima with Dijkstra on 2x2, 2x3 and 3x2, under both rule sets.
- Formalized and kernel-checked the per-case lower bound in Lean 4 (v4.34.1, Mathlib `d13f23b7`). The coordinator recompiled it independently under a 4 GB cap.
- Ran the paired v1/v2 evaluation on one E2B worker.
- Original identity: judge image `seededge/edgebench.judge.warehouse_forklift_routing@sha256:ac7fdf03…`. Key files: `/tmp/eval_warehouse_manager.py` sha256 `c5ff0c26…`; `tools/bin/tester` sha256 `277f4841…`; the 50 judge inputs (concatenated) sha256 `04b8cd29…`; task JSON sha256 `78002570…`.

## What we found

**Confirmed: the time contract is broken (a good-faith defect).** The prompt promises 30 s per test case, with 5 test cases per input, which is 150 s per input. The evaluator sets `TIME_LIMIT = 60` for the whole input and runs 8 inputs in parallel. A timeout scores `inf`, and the harness rejects any nonfinite CASE, so a single timeout invalidates the whole submission. *Example, original evaluator:* a time-budgeted control (it sleeps) that spent 13 s per test case (less than half the promised limit) got 50 TLE and an invalid submission. The local tools give no warning, because `tools/bin/tester` only scores an output file. *Maximum score effect:* a solver that follows the promised budget loses its whole score.

**Confirmed: the anchors cannot be reached (the ceiling is now documented).** Every string the tester accepts satisfies S ≥ 2RC(R+C−1) − 6(R+C−2) − 2. This is the theorem `EbvWarehouse.lower_bound` in `formal/lean/ebv/Ebv/WarehouseBound.lean`, kernel-checked with no `sorry` and no `native_decide`, and recompiled independently by the coordinator. It depends only on Lean's standard axioms `[propext, Classical.choice, Quot.sound]`. The companion theorem `EbvWarehouse.score_bound` gives every valid per-case score ≥ 20 − 6(R+C−2)/(R+C−1). In `Ebv/WarehouseData.lean`, `totalLB_eq` and `totalLB_gt` show that on the 50 judge inputs every valid TOTAL is ≥ 198283458104808536/278277680055375 ≈ 712.538, and `displayed_gt_rank1` shows that this stays above rank1 even after display rounding. The bound is therefore TOTAL ≥ 712.538 > rank1 395.80; super_anchor (293.51) is also below it. Under the task's own rescale, no valid submission can score above about 30.3 normalized points (30.308 at the exact bound; 30.586 at the 710.2 display-rounding floor)[^2].

Two checks show the theorem is not vacuous. The model accepts a 42-character optimum (`opt23_accepted`). A stronger bound without the −6(R+C−2) term is proved false (`too_strong_bound_false`), and that stronger bound fails on 239 of 248 brute-force optima. The proof does not use the movement-occupancy guard, so it holds under both the prompt's rule and the CodeChef rule. One step is not kernel-checked: that the Lean model matches the tester. That match rests on a line-by-line mapping and a 294-string runtime differential test with 0 mismatches.

**Not a scoring defect (disclosed rule change).** The tester lets an empty forklift enter occupied cells. This is looser than the original CodeChef rule, but the prompt states it. Solvers that follow either rule are accepted.

**Confirmed, not material.**
- The diagonal construction scores exactly 20.0. Adding an E,W detour gives 20.2.
- The tester prints each input's score to 1 dp. This shifts TOTAL by at most 2.5 raw, or about 0.2 normalized points.
- Failures aggregate to `inf` and invalidate the submission, which matches the README's "sum".
- Scoring is deterministic.
- The data are well-formed. Seed replay 0..300,000 reproduced none of the 50 judge files, so the judge inputs are not in the public seed range.

**An earlier audit held this task.** The hold was recorded as an "implementation" hold. The hold record shows an automatic content-filter stop of a Codex agent that was preparing ordinary native controls. It records no task defect. The user lifted all such holds on 2026-10-12, and this task was then reviewed in full.

## Repair

v2 changes one line in `/tmp/eval_warehouse_manager.py`: `TIME_LIMIT = 60` becomes `TIME_LIMIT = 150`. The value is 30 s per test case × T=5, as the prompt promises. `eval_timeout` stays at 3600. The task JSON changes only `judge.image_tag`. The work image, prompt, README, tester, cases, parser, selection and rescale are unchanged. The `piecewise_log_min` anchors are kept by decision (2026-10-12) rather than re-anchored. The proven floor is a lower bound, not a known optimum, so putting 100 there would be an invented recalibration. Keeping the anchors preserves comparability with v1. Release notes state the ≈30.3 ceiling. The first paired job was lost to a host restart, a collection failure that says nothing about the repair. The re-run results are:

| Submission | Role | v1 | v2 |
| --- | --- | --- | --- |
| generic valid control | valid | OK 50/50, TOTAL 46676.8 | OK 50/50, TOTAL 46676.8 |
| one honest bug | invalid | 49 OK + 1 WA → inf | 49 OK + 1 WA → inf |
| shipped starter | invalid | 50 WA → inf | 50 WA → inf |
| **13 s per test case (uses the promised budget)** | **trigger** | **50 TLE → inf** | **50 OK, TOTAL 46676.8** |
| near the 150 s per-input limit | trigger | 50 TLE → inf | 50 OK, TOTAL 46676.8 |

Verdict in the results: accepted (time contract). Anchors unchanged by decision; ceiling ≈30.3 documented.

**Score compatibility.** v2 scores equal v1 scores for every submission whose solver finishes each input within 60 s. The two are not comparable for a submission that takes 60–150 s on any input: v1 invalidates the whole submission, while v2 scores it. A run near the limit can also change outcome with machine speed, as in any timed task. Because the anchors are unchanged, the normalized scale (including the ≈30.3 ceiling) is the same in v1 and v2.

## Limits and what was not run

- No model or solver re-runs. Effects are shown on authored controls and counterexamples only.
- The valid control is generic and weak (normalized 0.0). No competitive solver was built, so the best achievable score between the floor (712.5 raw) and about 1000 raw (the diagonal construction) is not measured.
- The time-budget controls use `sleep`. They show that the limit is enforced per input as promised. They do not model CPU contention from 8 compute-bound inputs running in parallel, and `eval_cmd` sets no CPU allocation.
- Each paired arm ran once on one E2B worker.
- The match between the Lean model and the tester is a hand mapping backed by runtime differential tests, not a kernel-checked proof. The case hypotheses (permutation, last arrival ≠ 1) and the extraction of (R,C) were checked in Python. The normalized ceiling comes from the harness's float rescale code, not from Lean.
- The provenance of the anchors was not recovered.
- Scorer isolation is outside this release's scope (EdgeBench design choice); good-faith findings are reported above.

## Reproduce

- Native checks: `evidence/scripts/warehouse_forklift_routing/` (`oracle_sim.py`, `diff_fuzz.py`, `authored_cases.py`, `data_and_bound.py`, `tiny_optimum.py`, `native/run_native.sh`, `harness_grade.py`; checksums in `SHA256SUMS`).
- Lean bound: `evidence/formal/lean/ebv/Ebv/Warehouse{Bound,Check,Data}.lean`, compiled with `evidence/scripts/warehouse_forklift_routing/lean_bound/compile_capped.sh`. Exact totals: `lean_bound/recompute_total.py`. Brute force: `lean_bound/brute_force.py`.
- Paired evaluation: `repairs/warehouse_forklift_routing-v2/paired/run.sh` (as run: `evidence/runs/warehouse_forklift_routing-v2-paired-b/run.sh`).
- Supporting records: `repairs/warehouse_forklift_routing-v2/` (README, `repair.patch`, `source-lock.json`), `evidence/reviews/warehouse_forklift_routing.md`, `evidence/reviews/warehouse_lower_bound_lean.md`.

[^2]: The original review reported the ceiling as 30.31 and the per-case bound as "> 20 − 6(R+C−2)/(R+C−1)", and described the proof as written but not machine-checked. The later Lean review corrects the inequality to "≥", kernel-checks the proof, and reports a ceiling of 30.308 exact or 30.586 after display rounding. This page uses the Lean review's values and the README's headline "≈30.3".
