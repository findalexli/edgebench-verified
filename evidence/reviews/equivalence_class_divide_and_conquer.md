# Review: equivalence_class_divide_and_conquer

> **Note (2026-10-12).** Superseded statement: "up to +5.17 of 100 points in the worst case"
> (Refutation attempts). 5.17 is the effect of one official case falling in the window. T3 scores
> its full 10 points only when all 30 cases pass, and the window exists on each of cases 1–28
> (cases 29 and 30 cannot exceed the limit), so the largest possible difference is
> 10 − 0.5·2/30·10 = 9.67 points. Also, the undercount is the size of the last operation's target,
> |N_last|, which is larger than the last step's cost whenever that step starts from a non-empty
> neighbourhood. See `cases/equivalence_class_divide_and_conquer.md`.

## Claim under review

Earlier claim (docs/FINDINGS.md): "An original checker accepts output whose operation cost exceeds the stated limit. An at-limit control passed; no score gain was established."
Earlier disposition: **withhold the original** (`excluded_exact_original`). Evidence: `evidence/selected/eq-graph-original-exclusions.json`, `evidence/selected/equivalence-t3-*.json`.

## Pinned artifacts

- Task: `tasks/equivalence_class_divide_and_conquer.json`. eval_cmd `python3 /opt/p2_judge/prob/P2/eval.py --source-root /home/workspace/p2 --time-factor 1 --time-grace 0 --score-sum`. Problem weights 5/5/10/15/25/40.
- Judge image (pulled, executed): `seededge/edgebench.judge.equivalence_class_divide_and_conquer@sha256:f793d805d7e2adcec68355343230db3ea15b1010a98678850d2fe89e9ba767e6`
- Files read from the image (sha256):
  - `P2/T3_P8204/data/checker.cpp` f92b52cc37615e28e906d461cf9607ad42e8ea7bdac2a56fd215fc070edd4145. This matches the earlier audit's hash.
  - `prob/testlib.h` bb323e3c89285214966076e0d23d5a295c5f6126da7ff198c1276ddb95ecb1a0
  - `prob/eval_common.py` 0b20c8bfa4cd1f717cabc68aa085abf7a1c5d28df8c70ac18e04b1fb728b7541
  - `P2/T3_P8204/std.cpp` 47d7c75ec5d1244d840f861ab1a73c6f6be99a732ef3c18cd58d231706951932
  - `P2/T3_P8204/题面.md` c391e16859ad8ac162ce1ad0173490cfbcd1c8f2b70106a9908a4ef976e6a11a
- The image contains 30 official T3 inputs (`data/1..30.in`) with empty `.ans` files.

## Contract

The defect is in problem T3 (P8204, "directed neighbourhoods"), worth **10 of 100 points**. From `题面.md`:

> 你可以从 N(1,0) 出发，经过不超过 5m 次操作到达每个给出的有向邻域 … 操作1的代价为移动前后两个有向邻域的元素个数之差，操作2和3不计代价 … **你需要保证操作的总代价不超过 2.5×10^9。**

In English: the solver starts at N(1,0) and uses at most 5m operations. Operation 1 costs |new| − |old|, and undo and mark operations are free. **The total cost must be ≤ 2.5·10⁹.** The constraints are n, m ≤ 10⁶.

Scoring (`eval_common.task_score_fraction`): if all 30 T3 cases pass, T3 scores 10 points. Otherwise each passing case is worth 0.5·10/30 points.

## What the checker computes, and the exact defect

The checker appends a state `t[tt]` for each operation 1 and keeps a net coefficient `ct[k]`: −1 for each move out of state k and +1 for its creation. The true cost is Σ_{k=0..tt} ct[k]·|t[k]|. The final sweep is:

```cpp
std::iota(oq, oq+tt, 0), std::sort(oq, oq+tt, ...);
for (int i=0, j=0; i<tt; w+=1ll*ct[oq[i]]*(...), i++)
```

This sweep covers indices 0..tt−1 only, so it **omits the last state created, `t[tt]`**. No operation 1 follows the last operation 1, so `ct[tt]` = +1. The counted cost is therefore true_cost − |N_last|, where N_last is the target of the last operation 1. The checker then tests `w <= W` with `W = 2.5e9`, which matches the statement. The operation count (`readInt(0, m*5)`) is also correct.

The consequence is that an output with true cost in **(2.5·10⁹, 2.5·10⁹ + |N_last|]** is accepted. Since |N_last| ≤ n ≤ 10⁶, the overshoot can be at most **10⁶, which is 0.04 % of the limit**.

## Independent reproduction

All runs used the unchanged checker compiled inside the pinned image, exactly as `compile_checker` does: `g++ -std=c++17 -Ofast -pipe -I prob -I data`. Scripts are in `evidence/scripts/equivalence_class_divide_and_conquer/`. The crafted, official-input and random-case runs used `--memory 4g` because they ran before the coordinator's 2 GiB cap. The strictness check later used 1 GiB. All runs used one container, `--network none`.

**1. Crafted cases (`gen_crafted.py`, `run_crafted.sh`, output in `run_crafted_output.txt`).** The input is a star with n = 10⁶, where N(1,2) is all vertices. Every query is (1,2). The output strategy repeats "1 1 2 / 3 i / 2" for each query.

| case | true cost | original checker | instrumented (full sweep) |
|---|---|---|---|
| A m=2500 | 2.500·10⁹ (= limit) | ok | ok |
| **B m=2501** | **2.501·10⁹ (> limit)** | **ok Correct** | WA cost exceeded |
| C m=2502 | 2.502·10⁹ | WA (counts 2.501·10⁹) | WA |
| D = B + trailing zero-cost move "1 1 0" | 2.501·10⁹ | WA | WA |
| E efficient (move once, mark all) | 10⁶ | ok | ok |

Case D is the key control. Adding one free move at the end makes the original checker reject the same over-limit sequence. This shows that the leak is exactly "the last created state is not counted". It is not a tolerance and not a misreading of the limit.

**2. Brute-force oracle (`random_oracle.py`, `run_random.sh`, output in `random_results.txt`).** I generated 329 random small trees (n ≤ 7) with random legal operation sequences. For each case, the oracle computed |N(x,y)| directly from the statement's definition. I compared it with:

- the instrumented checker's full-sweep total;
- the original checker with only `W` changed to an environment parameter. At W = oracle_true − |N_last| the original must accept, and at one less it must reject.

**Result: 0 mismatches in 329 cases.** In 307 cases (all those with a non-empty last target), the original accepted with W = true_cost − 1. This confirms counted = true − |N_last| in general, not just on the crafted star.

**3. Official inputs (`run_official.sh`, output in `official_results.txt`).** These runs measured whether the defect could matter on real data.

- **Official reference `std.cpp`:** 30/30 accepted. The maximum true cost over the 30 inputs is 871,274,246 (case 19), which is **35 % of the limit**. The reference is never near the boundary.
- **Naive legal strategy (`naive.cpp`)**, which jumps from empty to each target, marks and undoes:
  - 6/30 accepted, all with very small costs.
  - The other 24 exceed the limit, by at least **116,912,620** (case 13: true cost 2,616,912,620).
  - The largest possible leak is ≤ n = 10⁶. So the defect flips **none** of the 30 naive verdicts, and could not flip them even if the queries were reordered to put the largest target last.

## Refutation attempts

- *Is the limit stated differently?* No. The statement says "不超过 2.5×10^9" (≤), and the checker's `w <= W` with `W = 2.5e9` matches. The defect is the omitted state, not the comparison.
- *Is it intended tolerance?* No. Case D shows that the verdict depends on whether a free move is appended, which no intended tolerance would do.
- *Is it reachable through the real harness?* Yes. Any submitted program's stdout goes to this checker. The trigger needs no audit fixture, only a true cost inside the 10⁶-wide window above the limit.
- *Does it give a score advantage?* Only conditionally. A solution whose true cost on some official input falls in (2.5·10⁹, 2.5·10⁹+|N_last|] has that case wrongly accepted, and a solver can widen the window to its largest target by moving it last. Flipping one case moves T3 from at most 4.83 to 10 points, or one case's 0.167, so up to +5.17 of 100 points in the worst case. On the official inputs, however, the reference uses ≤ 35 % of the budget and the naive approach misses by ≥ 1.17·10⁸. I found no realistic solution that lands in the window. **No score gain is demonstrated**, and the window is 0.04 % of the budget.
- *Other checker deviations.* These are in the opposite direction, rejecting statement-legal outputs (`strictness/`, `run_strictness.sh`, output in `strictness_output.txt`):
  - The move test compares (x, depth bound) pairs rather than set inclusion.
  - The mark test requires the identical (x,y) pair rather than the same set.
  - Example: tree 1–2, query N(2,1) = {2}. Reaching it via N(2,2) (also {2}) is rejected ("Invalid exposion" / "Invalid mark"). The direct route is accepted.
  - These cannot inflate scores. Natural solutions, including std, never hit them. They are noted for completeness only.

## Formal check

None. The counting identity is a telescoping sum and is not where the uncertainty lies. The uncertainty was in what the C++ code actually sums. That was settled by executing the original binary against an independent brute-force oracle (329 cases, 0 mismatches) and by the paired crafted controls B/D.

## Verdict

**CONFIRMED-NARROWER.** The checker under-counts cost by exactly the size of the final operation-1 target, an off-by-one in `iota`/loop bound `tt`. It therefore accepts true costs up to 2.5·10⁹ + |N_last| ≤ 2.5·10⁹ + 10⁶. The defect is real, reachable through the real harness, and confined to T3 (10/100 points). The window is ≤ 0.04 % of the budget. The reference and a naive solver are both far from it on all 30 official inputs, and no score gain is shown.

## Disposition assessment

The earlier wording is accurate as far as it goes: "accepts output whose operation cost exceeds the stated limit" and "no score gain was established". It omits the bound, and without it a reader could assume an unbounded bypass.

Withholding the *unchanged original* is technically consistent with VERIFICATION.md, because a mandatory check is wrong and "retain" requires all gates to pass. It is disproportionate as the task's end state, though: a 6-problem, 100-point task would be withheld over a ≤ 10⁶-unit leak in a 2.5·10⁹ budget on a 10-point component, with no observed effect. The proportionate outcome is to **repair** the original with the one-token fix below and keep the original's withholding as a bookkeeping state, not as a finding of invalid scores. If repair is not possible before release, "retain with a published note" (bounded leak, no observed impact) is more defensible than total exclusion. I agree with the earlier disposition only as an interim record. I recommend **repair**.

## Recommended publishable wording

"In the original T3 checker, the cost of the final move is left out of the total, so outputs exceeding the 2.5×10⁹ cost limit by at most the size of that last neighbourhood (≤10⁶, under 0.04 %) are accepted. On all 30 official inputs the reference solution uses at most 35 % of the budget, and no score change was observed."

## Repair note

Smallest correct fix: include index `tt` in the sweep. Change `std::iota(oq, oq+tt, 0), std::sort(oq, oq+tt, …)` to `oq+tt+1`, and `i<tt` to `i<=tt`. The array size `Q = 5N+1` already accommodates index tt ≤ 5·10⁶. That is the exact change in `checker_true_cost.cpp`, minus the diagnostic print.

The repo has no proposed equivalence patch. The earlier audit's packets describe a "one-byte index repair", which I did not inspect byte-for-byte. Fixing only `iota`/`sort` without the loop bound, or the reverse, would be wrong.

With the fixed checker:
- crafted case B is rejected, while A and E are accepted;
- all 30 official std outputs are still accepted, because the instrumented checker accepted all of them;
- the naive verdicts are unchanged.

## Limits

- Only T3 was examined. The other five problems (90 points) were not run.
- The search for "realistic near-limit" solutions covered only two strategies, the reference and naive. A solver with cost within 10⁶ of the limit on some official case cannot be ruled out in principle.
- The strictness side observation follows my reading of "当前所在邻域是 N(xi,yi)" as set equality. Pair equality is an arguable intended reading.
- The full `eval.py` six-problem run was not executed. The checker was run directly, compiled with the harness's own flags and include paths.
