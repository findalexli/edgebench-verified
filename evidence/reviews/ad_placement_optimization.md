# Review: ad_placement_optimization

## Claim under review

Earlier statements:

- `$W/STATUS.md` (~l.123): "Independently checked all 50 ad-placement inputs against the original constraints: no failures or byte duplicates. Four real-image cloud Docker controls passed, and every unit-rectangle case score matched the independent exact-rational oracle, total 826577. Executed image case hashes match the acquired data. Broader geometric checks are still in progress."
- `$W/STATUS.md` (~l.124): "Verified that the public generator seeds 0–49 reproduce all 50 ad-placement grading inputs exactly."
- `TASKS.md`: "Four native functional controls; held (L)." Disposition: **review pending / held**.
- The held "ad-overlap" follow-up. The canonical records (`STATUS.md` ~l.170–174, `AGENTS.md` ~l.210, `audit/AUDIT-BRIEF.md` ~l.352) name it only as a "pending ad-overlap … probe" from a runtime-review queue. An automatic review stopped that queue's agent; no cause was recorded and the probe never ran. No saved spec says exactly what it would test. The card blocker says what was still missing: "broader geometric validity and metamorphic controls remain under review". The only earlier overlap control was `invalid_all_overlap`, where every rectangle is the full square (WA on all 50 cases). I therefore read the probe as: check that the original tester accepts legal contact and rejects real overlap. That is the question answered below. The user lifted the hold for this review.

## Pinned artifacts

- Task: `tasks/ad_placement_optimization.json`, sha256 `972a31a5…7531` (matches the card's `manifest_sha256`). Parser `score_sum`, maximize, `score_first`, `piecewise_max` (baseline 0, rank30 47169682940, rank1 49702568341, super_anchor 5e10). `submit_paths: ["solution.cpp"]`.
- Judge image: `seededge/edgebench.judge.ad_placement_optimization@sha256:997d10b59ba063f23429fb8eace84b0cb28ea22b0f9fe5243ef64a2310e19ba9`. It is 163 MB; I pulled it and ran it locally. In the image: `/tmp/eval_ahc.sh` `8445b091…036ed`, `tools/bin/tester` `2498e6a2…dcb`, `tools/bin/gen` `e68b36f6…2d42d`, and 50 `cases/*.txt`. Their sha256 values equal the acquired copies (`scripts/.../native/results/*/image_hashes`). The image holds no Rust source.
- Work-image sources (earlier byte extraction, `audit/evidence/ad-placement/work-image-provenance/`, layer digest verified there): `tools/src/lib.rs` `afefaa4e…fc0`, `tools/src/bin/tester.rs` `b038bb9a…2c3`, READMEs (effective layer 6). The work-image tester binary hash `2498e6a2…` equals the judge's.
- Official AHC001 material (earlier acquisition): `AHC001-official-tools.zip` `167a9f89…a1c` (`tools/src/bin/vis.rs` `b4b6a18b…98df`, `tools/in/0000–0049.txt`), `AHC001-official-system-seeds.zip` `1deebd59…97f3`. Its `seeds.txt` md5 is `8fc1ce3f4beabac6abc1bdb4206d7f7e`, which equals the md5 the problem page publishes. Problem page `AHC001-primary.html` `799ae877…ca52`.
- Harness: `sforge/harness/log_parsers/score_sum.py`, `grading.py` (`extract_score`, `_grade_legacy`), `selection.py`, `score_rescale.py`, `evolve_scripts.py` (`generate_evolve_prompt`).

## Contract

- agent_query: "Each company i wants an ad space containing point (x_i+0.5, y_i+0.5) with area as close to r_i as possible. Maximize the total satisfaction." It refers to `README.md` for the rules. The harness wrapper adds: "Only the following paths are submitted for evaluation: `solution.cpp`", and "Your **best score** across all submissions is your final score."
- README: "Different rectangles may share edges but must not overlap (common area must be zero)"; "Blank regions are allowed"; "If the ad space does not contain point (x_i+0.5, y_i+0.5), then p_i = 0"; "p_i = 1 - (1 - min(r_i, s_i) / max(r_i, s_i))²"; "Final score = round(10^9 × Σp_i / n)"; output is n lines `a b c d` with "0 ≤ a_i < c_i ≤ 10000, 0 ≤ b_i < d_i ≤ 10000"; "**Final score = sum of scores across all 50 public test cases.**"; it holds "50 fixed public test cases that you cannot view directly". tools/README adds: "If the output is invalid, stderr outputs `wrong answer: <reason>` and exits with code 1".
- Official AHC001 (problem page): touching on sides is allowed, but common area must not be positive. The score is the same formula. Provisional test: 50 cases. System test: 1000 cases. In the system test, an invalid output or TLE makes only that case 0.

## Independent reproduction

Everything ran locally: `docker run --rm --network none --memory 2g --cpus 2|1`, one container at a time, all removed afterwards. No E2B was needed.

**1. Source comparison (Q1).** The scoring loop in the task's `lib.rs` (`compute_score_details` and `intersect`) matches the official AHC001 `vis.rs` `score()` statement for statement. It checks bounds `0..W`, positive area `x1<x2 && y1<y2`, and point containment `x1 ≤ x_i < x2 && y1 ≤ y_i < y2`, which is exactly "contains (x_i+0.5, y_i+0.5)". Overlap is `min(x2)>max(x1) && min(y2)>max(y1)`: strict inequality, so a shared edge or corner is legal. The score is `(1e9*Σp/n).round()` in f64 (round half away from zero). A byte diff is not meaningful: the official zip has no `lib.rs` or `tester.rs`, and its logic lives in `vis.rs`. The two differences are in I/O only:
- The task parses with `split_whitespace` and range-checks every token to `0..=10000`. The official code used proconio `LineSource`.
- The task rejects extra tokens with "Too many rectangles", and it reports invalid output as `wrong answer` with exit code 1 instead of printing 0.

`gen.rs` was refactored (clap, `gen_range(0i32,10000)`), but its output is byte-identical (see 4).

Inherited quirk, identical in the official code: the j<i overlap loop runs only for a rectangle i that contains its own point. So a rectangle that does **not** contain its point (p_i=0) and overlaps an *earlier* rectangle is accepted. If that rectangle comes earlier than the one it overlaps, the overlap is rejected.

**2. Micro fixtures through the original judge tester binary** (`scripts/.../micro/run_micro.sh`, 23 fixtures; oracle written from the README). Result: tester and oracle agree on 22 of 23. The disagreement is the quirk.

| fixture | judge tester | oracle (README rules) |
|---|---|---|
| edge_touch (shared vertical edge) | Score = 1000000000 | OK 1000000000 |
| corner_touch (shared corner) | Score = 1000000000 | OK 1000000000 |
| overlap_1x1 / contained / identical | WA "rectangles 0 and 1 overlap" | WA |
| noncontain_overlaps_earlier (rect 1 misses its point, overlaps rect 0) | **Score = 500000000** | WA (README: overlap forbidden) |
| noncontain_overlapped_by_later (same pair, order swapped) | WA overlap | WA |
| point on right/top edge (x2 == x_i) | Score 500000000 (p=0) | same |
| point on left edge (x1 == x_i) | contained, 509950000 | same |
| max corner 9999..10000 | 1e9 | same |
| x2 = 10001 / a = -1 | WA "Out of range" | WA |
| zero area / reversed corners (c<a) | WA "does not have positive area" | WA |
| too few / too many tokens / empty | WA (EOF / Too many rectangles / EOF) | WA |
| CRLF + tabs + no final newline, `+0`, leading zeros | accepted, correct score | same |
| `10.0`, non-UTF-8 bytes | WA | WA |
| n=1 full square, r=1e8 | 1000000000 | same |

**3. Full original evaluator on all 50 grading cases** (`native/run_native.sh`, then `native/compare.py` with the exact-rational oracle and the repository harness). There were 7 controls × 50 cases = 350 per-case results. Every case's native status and score equals the oracle's (`native/compare_output.txt`). The f64 score equals the exact-rational score in every case.

| control | what it exercises | TOTAL_SCORE (native = oracle) | CASES_OK | normalized |
|---|---|---|---|---|
| unit | unit cells, no contact | 826577 | 50 | 0.00035 |
| tile_full | guillotine tiling of the full square: every tile shares edges and corners, coordinates 0 and 10000 used | 27114970588 | 50 | 11.50 |
| tile_fit | point-containing sub-rectangles sized toward r_i within the tiles | 38525222727 | 50 | 16.33 |
| overlap1 | tile_full with one area-1 overlap per case | 0 | 0 (50 WA) | 0 |
| nocontain | unit cells, company 0 moved off its point | 824412 | 50 | 0.00035 |
| oob | company 0 x2 = 10001 | 0 | 0 (50 WA) | 0 |
| mixed | per case: 2 TLE, 7 RE, 7 WA, 4 CRLF/odd-whitespace, 30 plain | 26265417491 | 34 | 11.14 |

`unit` reproduces the earlier 826577. In `mixed`, TOTAL_SCORE equals the oracle sum over the 34 OK cases. The TLE, RE and WA cases are listed as CASE lines with score 0. `parse_score_sum` accepts all 50 records and the CASES_OK/CASES_TOTAL cross-check. `extract_score` reads TOTAL_SCORE, `score_first` selects it, and `piecewise_max` gives the normalized values shown.

**Timing control.** A solver that busy-waits to 4.9 s of wall time and then prints tile_fit got 50/50 OK, both at `--cpus 2` and at `--cpus 1` (`native/results_timing/`).

**4. Data (Q4).** The judge image's own `gen`, run on `seq 0 49`, produced 50/50 files byte-identical to `cases/` (`data/regen_output.txt`). Those cases are also byte-identical to the official AHC001 `tools/in/0000–0049.txt`. None of seeds 0–49 is among the 1000 official system-test seeds. An independent constraint scan (`data/check_constraints.py`) found: n in 51..198 (sum 4785), coordinates in range, distinct points, r_i ≥ 1, Σr = 10^8 in every case, no byte duplicates, and zero failures.

## Refutation attempts

- *Does the tester wrongly reject honest layouts?* No. Shared edges, shared corners, coordinates exactly 0 or 10000, and a full tiling of the square are all accepted and scored exactly, on real cases and in micro fixtures. Whitespace variants (CRLF, tabs, no final newline) are accepted.
- *Does it accept real overlaps?* Every positive-area overlap is rejected, including a single unit cell, containment and identical rectangles, when the later-indexed rectangle of the pair contains its own point. The one accepted overlap involves a rectangle that earns p_i = 0 and has a lower index than its partner. This is the official AHC001 rule, so AtCoder scored this way too. The accepted output earns nothing from the overlap: its score equals the score of the same output with that rectangle removed. The only possible gain is not having to find room for that zero-score rectangle, which matters only if the scoring rectangles leave fewer free unit cells than there are such companies. Even then, a valid output can free a cell by trimming a 1-wide end strip from the largest rectangle (area ≥ 5e5, so its long side is ≥ 707). That changes one p by at most about 2/707. That is at most about 5.7e4 raw per affected company per case, about 0.0014 normalized points in the 20–80 band and about 0.004 in the 80–100 band. An honest solver gets no benefit from it.
- *Aggregation.* The evaluator scores per case: OK cases are summed, and TLE/RE/WA/CE score 0 but are still listed. That matches the AHC001 system-test rule. No failed case is silently dropped, because `CASES_TOTAL` is the count of case files and the parser cross-checks it. A compile error gives one `CE` line with `CASES_TOTAL 1` and a valid score of 0. A non-zero exit code after valid output counts as RE with 0. That is strict but is the standard contest rule.
- *Is super_anchor 5e10 the true maximum?* Yes, as an upper bound: each case is at most 1e9 (all p_i = 1), and there are 50 cases. Whether 5e10 can actually be reached is not needed for it to be a ceiling. rank1 corresponds to an average p of about 0.994.
- *Does the prompt match the scorer?* Yes on rules, formula, rounding (f64 equals exact rational in all 350 cases) and the per-case sum. One README sentence is inaccurate: the "50 fixed public test cases that you cannot view directly" are exactly generator seeds 0–49. The README's own example `seq 0 9` regenerates judge cases 0000–0009 byte for byte. This does not mis-score anyone, but the cases are not a holdout.
- *Repeatability.* `eval_ahc.sh` runs `min(nproc,2)` cases in parallel, and `nproc` ignores a Docker `--cpus` quota (it reported 16 inside `--cpus 2`). A wall-clock-budgeted solver still finished in time at `--cpus 1`, but it gets half the CPU it would get with 2 or more cores. Scores of time-budgeted heuristics therefore depend on the judge CPU allocation, which the task JSON does not pin (no `cpu_limit`). I did not measure the size of this effect.

## Formal check

None. The rules are simple integer predicates; I checked them with an exact-rational oracle and with fixtures. A formal model would not reduce any remaining uncertainty.

## Verdict

**CONFIRMED** for the earlier statements. On the held geometric question, the tester's validity rules match the README and the official AHC001 rules for honest output: contact is allowed, positive-area overlap is rejected, bounds and containment are exact. The only exception is the inherited, order-dependent acceptance of an overlap by a rectangle that does not contain its point; it has no practical score effect. No defect found can mis-score an honest solver.

## Disposition assessment

I disagree with leaving the task held or pending on this question. Recommended: **retain with a note**. The maximum score effect of any scorer defect found is **0 for honest solvers**. The worst case for the inherited quirk is about 0.004 normalized points per affected company per case. The notes are about provenance and calibration, not correctness:
1. The graded cases are the public seeds 0–49, which are also the official AHC001 example inputs, so this is not a holdout.
2. The rank30/rank1 anchors come from AtCoder results on different instances. I did not check their source.
3. Judge CPU allocation affects how much compute a solver gets.

## Recommended publishable wording

"The original tester enforces the AHC001 rules as written: rectangles may share edges or corners, any overlap with positive area is rejected, and scores matched an exact-rational oracle on all 50 cases for seven controls. The 50 graded inputs are the public generator seeds 0–49 (the official AHC001 example inputs), so the task does not measure performance on unseen instances."

## Repair note

No repair is needed for scoring. Optional cosmetic changes:
- Change the README phrase "cannot view directly" to say the cases are generator seeds 0–49.
- Pin `judge.cpu_limit` (for example 2) so compute per case is repeatable.
- To enforce the README's overlap rule literally, move the containment `continue` after the overlap loop. This would diverge from official AHC001 scoring and changes no honest score, so I do not recommend it.

## Limits

- I did not rebuild the tester from `lib.rs`. Equivalence of source and binary is inferred from matching behavior on every branch exercised (all error messages and scores), not from a reproducible build.
- No real optimizing solver was run. The controls are constructive layouts, and the score impact of CPU allocation is unmeasured.
- The origin of the rank anchors and their comparability to seeds 0–49 were not checked.
- `native/controls.cpp` gained mode 8 (spin) after the seven-mode run. Each `results/<control>/solution.cpp` is the exact file that was evaluated.
- Exact content of the never-executed ad-overlap probe is not recorded anywhere I found. Its scope above is reconstructed from the card blocker and the earlier controls.
