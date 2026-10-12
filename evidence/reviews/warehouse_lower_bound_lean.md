# Machine check: warehouse_forklift_routing lower bound and unreachable anchors

## Question

`reviews/warehouse_forklift_routing.md` (H6) argues with a hand-written potential function that every command string the tester accepts satisfies

  S ≥ L(R,C) = 2·R·C·(R+C−1) − 6·(R+C−2) − 2.

If that holds, every valid per-case score is at least 20 − 6(R+C−2)/(R+C−1). Summed over the 50 judge inputs, the raw TOTAL is at least 712.54. The rescale anchors rank1 = 395.80 and super_anchor = 293.51 then cannot be reached, and normalized scores are capped near 30.3. This note checks that claim with a machine. The reviewer's claim is a hypothesis here.

## Pinned artifacts

| Item | SHA-256 |
|---|---|
| Judge image | `seededge/edgebench.judge.warehouse_forklift_routing@sha256:ac7fdf03bb73d0f9ded21662c7c3ac246ce521ee5e6b237978a2799c7bc29cb3` (already local; files extracted with `docker create` + `docker cp`) |
| `tools/bin/tester` (Python source, the rule authority) | `277f4841a25a11a9e9d7cbb751e2b407bd7cbf7f1eeba47c9821085db646bdd3` |
| `/tmp/eval_warehouse_manager.py` (wrapper) | `c5ff0c26ef5d42603926874630d573d4466adfeb117eaede3abca0fe846682fb` |
| `cases/0000..0049.txt` (concatenated) | `04b8cd29f1dab7f2e7d37754950872bcccdfe279e962d42650fbf76f5741be13` |
| `tasks/warehouse_forklift_routing.json` | `780025706c0b3201025f240e25b742f179c32c25be487d4802f074264b8cbd1c` |
| `sforge/harness/score_rescale.py` | `98feb630390f217cb67e21315b5ca8a4f2eb6d1bb28cc9822152b3ed58be4b19` |

These hashes match the ones in the earlier review.

## 1. Rules, taken from the original tester source

These rules come from `tools/bin/tester`; line numbers are in brackets. For each case, the tester reads `R C` and then one line with n = R·C−1 arrival ids. Every output line is `.strip()`ped, and S = len(line) [41-42]. A line longer than 500000 characters is rejected [44].

- **State** [49-55]: an R×C grid (0 means empty; otherwise it holds a good id); the forklift at (0,0), not carrying; `arrival_idx = 0`; `dispatch_idx = 0`.
- **N/S/W/E** [63-76]: N is r−1, S is r+1, W is c−1, E is c+1. The destination must be inside the grid. If the forklift is carrying, the destination must be empty. **An empty forklift may enter an occupied cell** (the branch is a bare `pass`, commented "Can move to occupied if not carrying"). Each costs 1 character.
- **P** [78-92]: the forklift must be at (0,0), not carrying, with `arrival_idx < n`. It then carries `ship[arrival_idx]`, and `arrival_idx` increases by 1. The cell (0,0) may be occupied. Costs 1 character.
- **D** [94-111]: the forklift must be at (0,0) and carrying, all n goods must have arrived, and the carried id must equal `dispatch_idx + 1`. Then `dispatch_idx` increases by 1 and the forklift is empty. Costs 1 character.
- **L⟨d⟩** [113-135]: the next character must be a direction and the neighbour must be in bounds. The forklift must be empty and the neighbour occupied. The good moves into the forklift, which itself does not move. Costs 2 characters.
- **U⟨d⟩** [137-159]: the next character must be a direction and the neighbour must be in bounds. The forklift must be carrying and the neighbour empty. The good is stored there and the forklift does not move. Costs 2 characters.
- **Anything else** [161], or L/U at the end of the string [115, 139]: reject.
- **Accept** [165-169] when the whole line executes and `dispatch_idx = n`. The case score is (S+2)/(R+C−1) − 2RC + 20. The input score is the average over the T cases, printed as `Score = {avg:.1f}` [172-174].
- **Wrapper**: `TOTAL_SCORE` is the sum of the 50 printed (1-dp) values. Any TLE, RE or WA gives `inf`, which the harness rejects. So a scored submission must have all 50 inputs accepted.

## 2. Lean formalization (`formal/lean/ebv/Ebv/WarehouseBound.lean`)

**Model.** `Cmd` (`mv d | P | D | L d | U d`, with cost 1/1/1/2/2) and `parse : List Char → Option (List Cmd)` reproduce the tester's character loop. `St` holds the position (ℕ×ℕ), `carry : Option ℕ`, `grid : ℕ×ℕ → Option ℕ`, `arr` and `disp`. `step` encodes exactly the guards listed in section 1, and `run` folds `step` over a command list. `Accepts R C ship str` means: `parse str = some cs`, `run init cs = some e`, and `e.disp = R*C−1`.

**Mapping notes:**
- The tester uses 0 for "not carrying"; the model uses `Option`. These agree because every arrival line is a permutation of 1..n, which was checked on all 250 cases.
- The tester's `all_arrived` flag equals `arr ≥ n` in the model.
- The model omits the 500000-character cap. Dropping a rejection condition can only make a lower bound on accepted strings harder to prove, so the omission is safe.
- The tester interleaves parsing and execution. The model parses first and then runs. Both reject on the first failure, so they accept the same strings.

**Proof outline (all kernel-checked):**
- f(r,c) = r+c. Φ is the sum of f over every good in the warehouse, stored or carried. The invariant `Inv` says: positions are in bounds; occupied cells are in bounds; |occupied| + [carrying] + disp = arr; and arr ≤ n.
- `step_props`: every accepted step preserves `Inv` and satisfies both cost ≥ Δ(2Φ − f(forklift) + arr) and cost ≥ Δ(−2Φ + f(forklift) + disp). This is checked case by case for each of the 5 command kinds. Neither inequality uses the "carrying cannot enter an occupied cell" guard.
- `run_props`: the per-step inequalities sum over a run (telescoping).
- `pre_step` / `split_tau`: τ is the moment just after the first U that follows the last P. At τ, nothing is carried, arr = n and disp = 0. τ exists because D needs id disp+1 = 1 while the forklift carries ship[n−1] ≠ 1.
- `phi_tau`: at τ the n = RC−1 stored goods occupy all cells but one, so Φ(τ) ≥ Σ_cells f − (R+C−2).
- `sum_cells_two`: 2·Σ_cells f = RC(R+C−2).
- `phi_end`: Φ = 0 at the end.
- Combining these: S ≥ 4Φ(τ) − 2f(τ) + 2n ≥ L(R,C).

**Theorem statements:**

```lean
theorem lower_bound (hR : 1 ≤ R) (hC : 1 ≤ C) (hn : 2 ≤ R * C) (hlast : ship (R * C - 2) ≠ 1)
    (str : List Char) (hacc : Accepts R C ship str) :
    2 * (R : ℤ) * C * ((R : ℤ) + C - 1) - 6 * ((R : ℤ) + C - 2) - 2 ≤ (str.length : ℤ)

theorem score_bound (same hypotheses) :
    (20 : ℚ) - 6 * ((R : ℚ) + C - 2) / ((R : ℚ) + C - 1) ≤
      ((str.length : ℚ) + 2) / ((R : ℚ) + C - 1) - 2 * R * C + 20

theorem too_strong_bound_false :      -- negative control, see section 4
    ¬ (∀ str, Accepts 2 3 ship23 str → 2 * 2 * 3 * (2 + 3 - 1) - 2 ≤ str.length)
```

**Rule question from the coordinator.** The relaxed rule ("an empty forklift may pass through stored goods") does not affect the argument. The proof never uses either occupancy guard on moves. It uses only:
- unit moves inside the grid;
- P and D at (0,0);
- L/U move a good by one cell;
- U needs an empty target, so stored goods sit in distinct cells;
- the dispatch order and the last arrival ≠ 1.

The bound therefore holds under the tester's rule and also under the stricter CodeChef rule.

**Compile and axioms**: see "Compile status" below. `Ebv/WarehouseCheck.lean` imports the core file and holds the non-vacuity example, the negative control and the differential test.

## 3. The 50 actual inputs (exact rationals)

`scripts/warehouse_forklift_routing/lean_bound/recompute_total.py` parses each input line by line, the same way the tester does (output in `recompute_total.out.txt`):

- 50 files and 250 cases. **0 cases fail the theorem's hypotheses** (R,C ≥ 6, each line is a permutation of 1..n, last arrival ≠ 1).
- Exact TOTAL lower bound = Σ_files mean_cases (20 − 6(R+C−2)/(R+C−1)) = **198283458104808536 / 278277680055375 ≈ 712.538131**. This equals the reviewer's figure exactly.
- The wrapper sums the 1-dp displayed values, not the exact averages. Each displayed value is at least floor(10·avg)/10, so the reported TOTAL_SCORE is at least **710.2**.
- The script also writes `formal/lean/ebv/Ebv/WarehouseData.lean`, which holds the 250 (R,C) pairs. The kernel checks there:
  - `dims_shape`: 50 files × 5 cases (`decide`, no axioms).
  - `totalLB_eq`: the exact fraction above (`norm_num`).
  - `totalLB_gt`: 712.53 < bound.
  - `displayed_gt_rank1`: bound − 50·0.05 > 395.802847 = rank1.

  Axioms for the last three: `[propext, Classical.choice, Quot.sound]`.
- Rescale (`sforge.harness.score_rescale.rescale_score` with the task's own `piecewise_log_min` spec):

| raw | normalized |
|---|---|
| 712.538 | 30.308 |
| 710.2 (displayed-rounding floor) | 30.586 |
| 1000 (diagonal-construction score of 20 per case) | 18.71 |
| rank30 804.959 | 20 |
| rank1 395.803 | 80 |
| super_anchor 293.514 | 100 |

  The rescale is non-increasing in raw; a grid scan from 710.2 to about 23,000 confirms it, and each piece is a decreasing log, matching at the anchors. So **no valid submission can normalize above 30.59**. rank1 needs raw ≤ 395.80, which is below the proved floor of 710.2, so it is unreachable; so is super_anchor.

## 4. Negative control and small-grid search

`scripts/warehouse_forklift_routing/lean_bound/brute_force.py` is an independent Dijkstra over the full tester state with path reconstruction. Every optimal string it finds was re-run through the **original tester bytes** (output in `brute_force.out.txt`).

| Grid | Orders | Smallest exact optimum over orders | Proved L | Too-strong L' = 2RC(R+C−1)−2 |
|---|---|---|---|---|
| 1×3, 3×1 | all | 16 | 4 | 16 |
| 1×4, 4×1 | all | 26 | 12 | 30 (violated) |
| 1×5 | all 18 | 40 | 24 | 48 (violated) |
| 2×2 | all 4 | 22 | 10 | 22 |
| 2×3, 3×2 | all 96 each | 42 | 28 | 46 (violated) |
| 2×4, 4×2 | 12 random each | 70 | 54 | 78 (violated) |

- 248 instances in total. **L is violated 0 times. L' is violated 239 times.** All 248 optimal strings are accepted by the original tester.
- So the check is not vacuous: removing the −6(R+C−2) correction gives a false bound. On these tiny grids the proved L sits 12–16 characters below the optimum. It is valid but not tight.
- On full-size grids, the diagonal construction (exactly 20 per case, natively confirmed in the earlier review) is at most 6(R+C−2) above L. So the true optimum lies in [L, L + 6(R+C−2)] whenever that construction applies.
- In Lean, `opt23_accepted` proves by `decide` that the 42-character optimum for 2×3 with arrivals 1..5 is accepted by the model. `too_strong_bound_false` proves L' false in the model. `opt23_drop_last_rejected` shows that the model is not trivially accepting.
- A runtime differential test (`#eval` inside the Lean file, fixtures from `gen_diff.py`) covers 294 strings: optima plus 1–3 random character edits, of which 21 are tester-accepted. It checks that the Lean `accepts?` agrees with the original tester on every string. The expected mismatch count is 0; see "Compile status".

## Compile status

- Lean v4.34.1 with Mathlib `d13f23b7` (the project manifest). Compiled by `scripts/warehouse_forklift_routing/lean_bound/compile_capped.sh`, under the heavy-job lock, one file at a time.
- Each compile ran inside `python:3.11.14-slim` with `--memory 4g --network none`. The host toolchain and Mathlib oleans were mounted read-only.
- Outputs are saved as `Ebv/Warehouse{Bound,Check,Data}.out`. All three exit 0, with no `sorry` and no `native_decide`.

```
'EbvWarehouse.parse_cost' depends on axioms: [propext, Quot.sound]
'EbvWarehouse.lower_bound' depends on axioms: [propext, Classical.choice, Quot.sound]
'EbvWarehouse.score_bound' depends on axioms: [propext, Classical.choice, Quot.sound]
"differential fixtures=294 accepted=21 mismatches=0"
'EbvWarehouse.opt23_accepted' depends on axioms: [propext, Classical.choice, Quot.sound]
'EbvWarehouse.too_strong_bound_false' depends on axioms: [propext, Classical.choice, Quot.sound]
'EbvWarehouse.opt23_drop_last_rejected' depends on axioms: [propext, Classical.choice, Quot.sound]
'EbvWarehouseData.dims_shape' does not depend on any axioms
'EbvWarehouseData.totalLB_eq' depends on axioms: [propext, Classical.choice, Quot.sound]
'EbvWarehouseData.totalLB_gt' depends on axioms: [propext, Classical.choice, Quot.sound]
'EbvWarehouseData.displayed_gt_rank1' depends on axioms: [propext, Classical.choice, Quot.sound]
```

These are only Lean's standard axioms.

**Incident during this check.** One attempt ran `lake` inside a container that had no `git`. Lake then judged the Mathlib URL "changed" and deleted `.lake/packages/mathlib`. I restored it on the host with `lake exe cache get`, under the lock. That re-cloned the same rev (`d13f23b7…`), and all 8530 oleans came from the local cache with nothing downloaded. Later compiles call `lean` directly, with the project mounted read-only.

### Kernel-checked vs not

| Step | Status |
|---|---|
| S ≥ L(R,C) for every string the model accepts, for all R,C ≥ 1 with RC ≥ 2 and last arrival ≠ 1 | **kernel-checked** |
| Per-case score ≥ 20 − 6(R+C−2)/(R+C−1) | **kernel-checked** |
| Exact TOTAL bound on the 250 (R,C) pairs = 198283458104808536/278277680055375 > 712.53; bound − 2.5 > rank1 | **kernel-checked** (from the Python-extracted (R,C) list) |
| Model = original tester | hand mapping line by line, plus a 294-string runtime differential (0 mismatches) and 248 brute-force optima accepted by both. **Not kernel-checked** |
| The 250 cases satisfy the hypotheses (permutation, last ≠ 1) | Python, 0 failures |
| Display rounding: reported TOTAL ≥ 710.2 | Python. Lean uses the weaker −0.05 per input |
| Normalized ceiling 30.31 (exact) / 30.59 (after rounding) | harness float code (`score_rescale.py`) |

## Verdict

**Anchors unreachable: CONFIRMED.**

- The reviewer's bound S ≥ 2RC(R+C−1) − 6(R+C−2) − 2 is proved in Lean, without `sorry`, for a model of the original tester's rules.
- The relaxed "empty forklift may pass through goods" rule is in the model, and the proof does not depend on it.
- On the 50 judge inputs, any fully valid submission has raw TOTAL ≥ 712.538 exactly, and the 1-dp sum actually reported is ≥ 710.2.
- rank1 (395.80) and super_anchor (293.51) are below that floor, so they are unreachable.
- Under the task's own rescale, the maximum normalized score is about **30.3–30.6**.
- One small correction to the earlier review: the per-case bound is "≥ 20 − 6(R+C−2)/(R+C−1)", not "> …". This does not matter for the conclusion.

## Limits

- The model's correspondence to the tester is a hand mapping, line by line, backed by the 294-string runtime differential test. The tester's Python code is not itself verified.
- The arithmetic over the 50 inputs is kernel-checked from the (R,C) list. That list was extracted by Python from the pinned case files. The hypotheses (permutation, last ≠ 1) were checked by Python, not by Lean.
- Display rounding (≥ 710.2) is argued in Python from monotone rounding. In Lean, a weaker margin is used (−0.05 per input) and suffices.
- The bound is not tight: on tiny grids the optimum is 12–16 characters above L. This review does not establish where the best achievable score lies between 712.5 and about 1000 raw (the diagonal construction).
- The rescale ceiling uses the harness's float code, not Lean.
- Brute force covers grids of at most 8 cells. 3×3 and larger were not searched. This does not affect validity, which is proved for all R and C.
