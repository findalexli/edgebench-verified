# Review: warehouse_forklift_routing (CodeChef WAREHOUS adaptation)

## Claim under review

TASKS.md row: "Historical source/math facts retained (L)". Earlier status: **Held**, with no follow-up. The hold record (`$W/audit/evidence/warehouse-source-review/implementation-hold.json`) is an automatic content-filter stop of a Codex agent that was preparing ordinary native controls. It records no defect. No native warehouse control had ever been run.

These are the "source/math facts" from the earlier dossier (`$W/audit/dossiers/warehouse_forklift_routing/dossier.txt`) and its independent review. I treated each as a hypothesis:

- H1: "It enforces move boundaries and prohibits entering an occupied destination while carrying. An empty forklift may stand on occupied cells." P, D, L and U are checked as described. Lx/Ux cost two characters.
- H2: the diagonal-storage construction gives "S=4*sum(d)+2n=2RC(R+C-1)-2. The exact per-subcase score is 20". An initial E,W detour on each 6x6 case "displays 20.2".
- H3: the tester prints the average to one decimal, even though its comment says it rounds to an integer.
- H4: "Failure paths yield infinity … Current harness adapters reject nonfinite results."
- H5: "The wrapper uses 60 seconds for a solution handling an entire input … README says 30 seconds per subcase, a distinct budget convention."
- H6: "The manifest's piecewise_log_min anchors are calibration data, not known-good control results or proof of useful score distribution."
- H7: from `audit/reviews/optimization_tasks.txt`: "no forklift simulator/tester implementation is retained, so reachability, occupied-cell moves … are not independently source-verified."

Earlier disposition: pending/held. `decisions.json` reads "under review".

## Pinned artifacts

| Item | Identity |
|---|---|
| Task JSON `tasks/warehouse_forklift_routing.json` | `780025706c0b3201025f240e25b742f179c32c25be487d4802f074264b8cbd1c` |
| Judge image | `seededge/edgebench.judge.warehouse_forklift_routing@sha256:ac7fdf03bb73d0f9ded21662c7c3ac246ce521ee5e6b237978a2799c7bc29cb3`, pulled (412 MB) and run locally |
| Work image | `seededge/edgebench.work.warehouse_forklift_routing@sha256:05dd02447c1d1d93201e4567f9591dcdd27a09b7f03794bd5f393b64aaeb5929`, pulled and inspected (not used for scoring) |
| `/tmp/eval_warehouse_manager.py` (in image) | `c5ff0c26ef5d42603926874630d573d4466adfeb117eaede3abca0fe846682fb` |
| `tools/bin/tester` (judge and work images, identical) | `277f4841a25a11a9e9d7cbb751e2b407bd7cbf7f1eeba47c9821085db646bdd3` |
| `tools/bin/gen` = work `tools/src/gen.py` | `127606cb3a4be5110fcf3be59e0560a49e01a244d92ddac93eded23fe5531c5d` |
| work `tools/src/verifier.py` (length-only scorer, does not simulate) | `4c88cdba397c83fb4517cdae8859d8c144f73f2351a423af7c9e45ee70ee4e84` |
| README.md / starter solution.py | `d5fde825ab3174bab15dbc3531b51d6cd4ee56c30bf5efbbcd063371dff7419b` / `51149282d91b2c2d0b6d2f97dcfe6122d17066cbf2dfc35d39434eab3f3bd409` |
| 50 judge inputs `cases/0000..0049.txt` (concatenated) | `04b8cd29f1dab7f2e7d37754950872bcccdfe279e962d42650fbf76f5741be13` (in the image; matches the extracted copy) |
| Original statement | `$W/audit/evidence/optimization-family/WAREHOUS-primary-api.json` (CodeChef API capture, JUNE18, author pieguy) |

The judge image has `tools/bin/{gen,tester}` but no `tools/README.md` and no `tools/src/`. The work image, which is what the solver sees, has both.

## Contract

The prompt (agent_query) and README say:

> "A forklift carrying a good cannot enter an occupied cell. Minimize the total instruction string length."
> "Per test case: (S + 2) / (R + C - 1) - 2*R*C + 20 … Score is averaged over T cases. **Minimize.**"
> "T=5 test cases per input" … "Time limit: 30 seconds per test case"
> README: "50 fixed test cases. **Final score = sum of per-input average scores.**"

The original CodeChef statement says:

> "it must stay in the warehouse and **cannot occupy the same cell as a shipment it does not currently carry**" … "'N','W','S','E': … The destination cell must be inside the warehouse and must not contain any shipment."
> "There are twenty test files … After the end of the contest, your score will be changed to the sum of your program's scores over the other eighteen test files." `max_timelimit` 5 s.

## Independent reproduction

All scripts are in `evidence/scripts/warehouse_forklift_routing/` (see `SHA256SUMS`).

1. **Independent simulator** (`oracle_sim.py`). I wrote it from the statement text, with exact `Fraction` scoring and two rule modes. `prompt` lets an empty forklift enter occupied cells. `original` uses the CodeChef rule that no move may enter an occupied cell.
2. **Differential test against the original tester bytes** (`diff_fuzz.py`, output in `diff_fuzz.out.txt`):
   - 20,000 random, biased command strings (1 or 2 subcases, grids 2x2 to 6x6). All 20,000 agree on accept/reject and on the displayed score (251 accepted).
   - 2,000 outputs of the generic control on grids up to 6x9, half of them with a random single-character edit. All 2,000 agree (1,035 accepted).
   - The prompt-rules oracle equals the tester. Of the 1,035 accepted strings, 932 are **illegal under the CodeChef rule**.
3. **Native tester fixtures** (`authored_cases.py` produces `inputs/authored/`; the judge-image tester output is in `native/out/authored_tester.txt`). There were 16 fixtures and 0 mismatches against the oracle predictions:
   - The diagonal family with reverse arrival (n..3,1,2) over 6x6, 6x20, 20x6, 20x20 and 7x11 scores `Score = 20.0`, exactly 20. Five 6x6 cases give 20.0. Adding an E,W detour gives `20.2` (exact 222/11).
   - `relaxed_walk_over` is the 6x6 diagonal case plus an empty walk across four stored goods. The tester accepts it (`Score = 20.7`, exact 228/11). The CodeChef rule rejects it.
   - All 12 negative controls fail with the expected diagnostics and exit 1: out of bounds; P away from the entrance; PP; D before all goods arrive; D while empty; carrying into an occupied cell; U onto an occupied cell; truncated L; unknown command; missing final D ("34/35"); wrong dispatch order; empty output ("expected 5 output lines, got 1").
4. **Native end-to-end with the verbatim eval_cmd** (`native/run_native.sh`: `--network none --memory 2g --cpus 2`, solution bind-mounted read-only; graded by the repository harness in `harness_grade.py`, output in `native/out/harness_grade.txt`):

| Run | Solution | Evaluator | Harness |
|---|---|---|---|
| control | `control_solution.py`: generic, honest, valid but not tuned (far-first placement, then sliding-puzzle retrieval) | 50/50 OK, `TOTAL_SCORE 46676.8`, 8 s | valid, score 46676.8, **normalized 0.0** (worse than baseline) |
| control_rep | same | byte-identical stdout | identical |
| starter | shipped `solution.py` (prints empty lines) | 50 WA, `score=inf` | **invalid** ("Malformed or nonfinite CASE record") |
| one_bug | control with one honest bug (drops one final D in input 0000) | 49 OK, 1 WA, TOTAL inf | **invalid** |
| time_budget | control plus sleep, using 13 s per test case (65 s per input) | 50 TLE, 421 s wall | **invalid** |
| selection | score_first over all five | picks control | normalized 0.0 |

   For all 50 judge inputs, the native per-input tester scores equal my oracle's exact values rounded to 1 dp. The control's oracle total is 46676.9 (exact), against 46676.8 from the sum of rounded values.
5. **Data** (`data_and_bound.py`, output in `data_and_bound.out.txt`):
   - All 50 files are well-formed: T=5, 6≤R,C≤20, each line is a permutation of 1..RC−1, and good 1 is never last. That is 250 subcases with 158 distinct (R,C) pairs.
   - Replaying generator seeds 0..300,000 reproduces **none** of the 50 files. The public seed range 0..10000 therefore does not include the grading inputs.
6. **Exact tiny-grid optima** (`tiny_optimum.py`, output in `tiny_optimum.out.txt`). I ran Dijkstra over the full tester state for every arrival order on 2x2, 2x3 and 3x2:
   - On the CodeChef sample (2x3, arrivals 3 1 2 4 5), the CodeChef-rules optimum is **50**, the length of the official sample output. This checks the `original` mode.
   - Under the prompt/tester rules the optimum is **42** for every 2x3 order. Under CodeChef rules it ranges from 46 to 50.
   - The lower bound below held in every instance (0 violations).

## Refutation attempts

**H1 (tester rules): CONFIRMED as source behavior. It is consistent with the EdgeBench prompt but differs from the original problem.**

The tester equals my prompt-text simulator on 22,000 differential cases and 16 native fixtures. The relaxed rule is real and disclosed. The prompt says only a carrying forklift is blocked, and the tester's code comments "Can move to occupied if not carrying".

The rule makes the problem easier than WAREHOUS: tiny-grid optima drop from 46–50 to 42, and 932 of 1,035 accepted control strings are illegal under the CodeChef rule. Its side effects are also legal in the tester and not mentioned in the prompt: storing a good at the entrance, P and D while standing on an occupied entrance, and loading while standing on an occupied cell.

A solver who follows the prompt is not scored wrongly. A solver who follows the original CodeChef rule (the prompt names "CodeChef WAREHOUS") is also accepted, because that rule is stricter. So this is a disclosed change to the problem, not a scoring defect. The earlier reviews characterized the tester correctly but never compared it with the original statement.

There is only one forklift, so there are no vertex, swap or follow conflicts between vehicles. The legality rules are a few local guards, and the differential test plus exhaustive tiny-grid search cover them. I judged a TLA+ model unnecessary and did not write one.

**H2: CONFIRMED natively** (20.0 exact and 20.2 displayed).

**H3: CONFIRMED.** Rounding each input to 1 dp shifts TOTAL by at most 50×0.05 = 2.5 raw. Near the realistic score range that is at most about 0.2 normalized points. Python's `%.1f` is deterministic, so it does not affect repeatability.

**H4: CONFIRMED and sharpened.** Any TLE, RE or WA prints `score=inf`. `parse_score_sum` rejects nonfinite CASE values, so **one failed input invalidates the whole submission** (one_bug, time_budget). A failure can never score better than a valid answer: it never contributes 0 and is never dropped. This matches the README's "sum" (an infinite sum) and CodeChef's "non-AC on any file → non-AC". The only quirk is that the harness labels an honest WA as "Malformed or nonfinite CASE record". Scoring is deterministic: identical stdout on repeat, and the tester reads no time or randomness.

**H5: CONFIRMED and UPGRADED to a good-faith defect.** The prompt and README say "30 seconds per test case" and define test cases as the T=5 subcases of each input. The wrapper gives `TIME_LIMIT = 60` seconds to the whole input, which is 12 s per subcase on average, while running 8 inputs in parallel.

An honest solver that budgets 13 s per test case (less than half the promised limit) got 50/50 TLE and an invalid submission natively. Local tools give no warning, because `tools/bin/tester` only scores an output file. Time-budgeted search is the normal style for this kind of contest heuristic, so this trap is reachable.

**H6: much stronger than stated. The anchors are unreachable under this tester and this aggregation.**

Lower bound (holds for every tester-accepted string and every R,C). Let f(r,c)=r+c. Every move changes f of the forklift by exactly ±1. A carried move, an L or a U changes the total f of goods in the warehouse by ±1. P and D happen at f=0.

Let τ be the moment just after the U that follows the last P. At τ all n=RC−1 goods are stored in distinct cells. This must happen before any D, because the last arrival is never good 1. Let Σd be their total distance and z the forklift's position at τ.

- Before τ: the forklift must undo every outward carried step it made. So moves ≥ 2(Σd − K) − f(z), where K is the number of L/U instructions, each costing 2 characters. Adding the n P instructions gives chars ≥ 2Σd + n − f(z).
- After τ: by the symmetric argument, chars ≥ 2Σd + n − f(z).
- Σd ≥ RC(R+C−2)/2 − (R+C−2), because only one cell is unused. Also f(z) ≤ R+C−2.

Hence **S ≥ 2RC(R+C−1) − 6(R+C−2) − 2**, so every valid per-case score is **> 20 − 6(R+C−2)/(R+C−1) > 14**.

The exhaustive tiny-grid search found no violation. I did not formalize the proof in Lean.

On the 50 actual inputs the bound is exact rational **TOTAL ≥ 712.538**, or 14.25 per input. The anchors, divided per input, are:

| Anchor | raw | per input (/50) | per file if 18 CodeChef files |
|---|---|---|---|
| rank1 | 395.80 | **7.92** (impossible: below 14.25) | 21.99 |
| super_anchor | 293.51 | **5.87** (impossible) | 16.31 |
| rank30 | 804.96 | 16.10 (barely above the bound) | 44.72 |
| baseline | 23277.85 | 465.6 | 1293 |

So the maximum attainable normalized score is **rescale(712.538) = 30.31**. The 80–100 band and most of the 20–80 band cannot be reached. Above rank30, the 20-point band needs a raw total near the bound, which would mean beating the diagonal construction's 20 per case on random arrival orders. That is unlikely.

For illustration, a solution averaging 22 per input (raw 1100) maps to **18.1**.

The 18-file reading fits all four anchors against the bound and against the CodeChef setup. This suggests the anchors were set on a different scale, probably the CodeChef leaderboard sum over 18 files. I could not confirm their provenance.

**H7: superseded.** The tester is now pinned, run natively and checked against an independent simulator.

## Formal check

There is no TLA+ model: the task has a single forklift and no inter-vehicle conflicts (see H1). Instead:

- Exact Dijkstra optima on all 2x2, 2x3 and 3x2 instances, under both rule sets, found 0 bound violations and reproduced the CodeChef sample optimum of 50.
- A rational-arithmetic computation of the bound on the 50 inputs gives `198283458104808536/278277680055375` ≈ 712.538.

The potential-argument proof above is a written proof, not machine-checked.

## Verdict

- Earlier source/math facts H1–H4: **CONFIRMED**.
- H5 (time limit): **CONFIRMED and upgraded to a reachable good-faith defect**.
- H6 (anchors): **CONFIRMED-STRONGER, a calibration defect**. Under the current anchors, no valid submission can exceed about 30.3 normalized points.
- The rule relaxation versus CodeChef is **disclosed by the prompt**. It is a note, not a scoring defect.
- There are no data defects.

## Disposition assessment

The held/pending status was not based on any defect, and the hold is lifted. I recommend **repair-v2**, touching only the rescale and the wording or limit. Evaluator logic and data stay as they are:

1. Re-derive `piecewise_log_min` anchors under this tester and this 50-input sum. The proved floor is 712.54, the diagonal-ideal reference is 1000.0 (20 × 50), and real solver runs should calibrate rank30 and rank1.
2. Make the time contract consistent. Either state "60 seconds per input file (5 test cases); up to 8 inputs run in parallel", or set `TIME_LIMIT` to 150 s (5 × 30 s). Raise `eval_timeout` too if needed: 7 waves × 150 s = 1050 s, which fits under 3600.

If no repair happens, use **retain-with-note**: "normalized scores are capped at about 30; honest per-test-case time budgets above 12 s fail".

**Maximum score effect:**

- Anchors: every submission that beats the rank30 raw value is under-scored. The ceiling is 30.3 instead of 100, so up to about 70 normalized points are lost for the strongest possible solutions. Submissions worse than rank30 are scored as intended.
- Time limit: an honest submission that relies on the stated 30 s per test case loses its whole score. That is up to 30.3 points under the current anchors, or up to 100 after re-anchoring.
- Rounding: at most about 0.2 points.

## Recommended publishable wording

"The warehouse task's rescale anchors cannot be reached under its own simulator and 50-input sum: every valid output scores more than 14.25 per input (raw total ≥ 712.5), so normalized scores cannot exceed about 30. Separately, the prompt promises 30 s per test case, but the evaluator allows 60 s per five-case input, and any single timeout invalidates the submission. The task's movement rule (an empty forklift may pass through stored goods) is looser than the original CodeChef rule but is stated in the prompt."

## Repair note

No earlier repair was proposed. The smallest correct fix is anchors re-derived on this tester and these cases, plus either one-line prompt/README wording (60 s per input, 8 in parallel) or `TIME_LIMIT = 150`.

Optional notes:
- The prompt could mention the entrance and stand-on-occupied consequences of the relaxed rule.
- The prompt says to read `tools/README.md`. It exists in the work image but not in the judge image, which does not matter for scoring.

Scaling the current anchors by 50/18 would **not** be correct: the anchors were probably set under the stricter original rules and a different file set.

## Limits

- The control is valid but weak (normalized 0). I did not build a competitive solver, so the real top-score position between 712.5 and about 1100 raw is not measured. The 18.1 figure is an illustration.
- Anchor provenance is unrecovered. The 18-file explanation is a consistency inference.
- Native runs used `--cpus 2` on this host. The time-budget result is structural (65 s > 60 s per input) and does not depend on CPU speed.
- The lower-bound proof is written, not machine-checked. It was checked exhaustively only on grids of size 2x2, 2x3 and 3x2.
- Tamper or scorer-isolation questions, such as the wrapper ignoring the tester's return code, were out of scope.
- No E2B was used: the image is small, so all native runs were local.
