# Review: jagua_nesting_optimization

> **Note (2026-10-12).** "Score depends only on strip width" below is superseded: `evaluate_case` multiplies the width-based raw score by a runtime multiplier (`score = raw * rt_mult`). The score does not depend on overlap. The comparison "about 10^6 times above the validator's EPS" compares an area with a coordinate tolerance and is withdrawn.

## Claim under review

Earlier claim (docs/FINDINGS.md): "The complete validator accepts selected shapes with overlapping interiors. Other overlaps were rejected; five equal-width cases showed no score improvement."
Earlier disposition: **withhold original** (evidence/selected/jagua-original-exclusion.json; card rationale: "the unchanged installed validator accepts positive-area coincident/collinear placements").

## Pinned artifacts

- Task: `tasks/jagua_nesting_optimization.json` (eval_cmd runs `jagua_task_scorer/score.sh`, which runs `evaluate.py`).
- Judge image: `seededge/edgebench.judge.jagua_nesting_optimization@sha256:4f029bf7c86d4762ecb7f183b6e1a016fcf8b705ac0efe28aed8f5e9e5208466` (pulled and run).
  - In image: `evaluate.py` sha256 `08159f8e3a59648460d8cd352ff3b71908763d9a521b41b95c90ba443f35cbe1`, `score.sh` `04459173a6b05f43e680a93f6dbe14d71c79ab28c9a5cbc8c7f38f8c7592aa63`. These match the cloud-export copies. Candidate `lbf/src` and `jagua-rs/src` are byte-identical to `jagua-rs-ref`.
- Work image: `seededge/edgebench.work.jagua_nesting_optimization@sha256:fce9b7ad99122f7f7004d932150117b8b026d7b58a5324aa9ab757504d961966` (pulled; used only to read `SEBENCH_TASK.md`, sha256 `9bff3a0acd0513648540e1bc6d53fa40627f3b13c0e63db4b224686ebf917e8e`).

## Contract

- agent_query: "Keep outputs geometrically valid; the judge independently checks all placements."
- SEBENCH_TASK.md: "...independently verify the geometric feasibility of each output solution." "...illegal output, missing items, out-of-bounds placement, **overlaps**, timeout, or program crashes all result in a score of 0." "Do not output fabricated solutions; the Judge will reconstruct polygons and perform independent geometric verification."
- evaluate.py docstring: validates "independently in Python so that a submission cannot win by printing impossible strip widths."
- Tolerance: the validator uses `EPS = 1e-5`; its comment says only "Boundary touching is allowed". The jagua-rs README describes a collision engine with optional `min_item_separation` and polygon simplification, but the scorer never calls the Rust engine to check validity. Its only check is the Python one. Neither document allows overlap with positive area. Touching at boundaries is allowed.

## Independent reproduction

Mechanism, from reading `polygons_overlap` in the original `evaluate.py`: it reports overlap only when (a) two edges cross properly (`o1*o2 < -EPS and o3*o4 < -EPS`; every collinear or endpoint-touching case returns False), or (b) a **vertex** of one polygon lies strictly inside the other, with boundary points counted as "not inside". So any overlap where no edges cross properly and every vertex sits outside or on the other polygon's boundary is accepted. This is not a tolerance effect. It happens with exact integer coordinates.

Inputs: eight hand-made witnesses with integer coordinates, rotation 0, strip height 20 (`scripts/jagua_nesting_optimization/make_pair_witnesses.py`). They were run through the **unchanged original `validate_solution`** inside the pinned judge image (`validate_in_image.py`):

```
docker run --rm --network none --memory 1g --cpus 1 -v $D:/s:ro <judge@digest> python3 /s/validate_in_image.py /s/witnesses
```

| witness | original validator | overlap area (shapely) | exact closed form |
|---|---|---|---|
| valid_adjacent_squares (shared edge, legal) | accept | 0 | 0 |
| coincident_squares (two copies at the same pose) | **accept** | 100 | 100 (100% of item) |
| half_slid_squares (shift 5 along x) | **accept** | 50 | 50 |
| rect_inside_square (10x5 inside 10x10) | **accept** | 50 | 50 |
| triangle_inside_square | **accept** | 50 | 50 |
| diamond_inside_square (vertices at edge midpoints, no shared edge) | **accept** | 50 | 50 |
| diag_shift_squares (shift 5,5; proper crossings) | reject `overlap_0_1` | 25 | 25 |
| tiny_overlap_1e-6 | accept | 1e-5 | 1e-5 (tolerance scale; benign) |

Saved outputs: `witnesses/validator_output.txt`, `witnesses/shapely_output.txt`. The witnesses are integer polygons with simple closed-form areas, so the exact closed form is the second oracle. Each area is at least 25% of an item's area, about 10^6 times above the validator's EPS.

## Refutation attempts

- *Is it intended tolerance?* No. The accepted overlaps are 50–100% of an item's area, with integer coordinates and no floating-point rounding. The only case at tolerance scale (1e-6 shift) is benign and is a separate matter.
- *Is it reachable through the real harness?* Yes, by construction. `submit_paths` includes `lbf/src/`. The scorer validates whatever `sol_<stem>.json` the candidate binary writes, and `placed_items` is a plain list of (item_id, rotation, translation). Repeating an item's pose for its later copies needs no special fixture. The card states the earlier audit also had a coincident-copy witness accepted on the real hidden asset `shapes1.json`. I did not re-run that witness.
- *Does it matter for scores?* Score depends only on strip width (`max(max_x, reported)`) relative to the reference. Every hidden instance has items with demand above 1 (e.g. shapes1: 4 item types, 43 copies; shirts: 8 types, 99 copies). Placements that stack copies are accepted, so they need less strip width than any feasible packing. On that basis I infer that scores can be inflated, and probably far past the 18% target improvement that earns full case points. **This is an inference from code, not a measured result.** I started and then deliberately stopped an end-to-end full-scorer run (see Limits), so no score number is reported here.
- *The earlier counter-evidence, "five equal-width cases showed no score improvement"*: per `jagua-original-disposition-sol-v2/exclusion-rationale.json`, these were V56 diagnostic runs where `ref_width = cand_width = 5`. They were not designed to exploit the hole. They show nothing about whether the defect can affect scores, and the FINDINGS wording reads as if impact had been tested and found absent.
- *Side observation (not part of the claim):* `validate_solution` never reads `allowed_orientations`, so rotations the instance forbids are not rejected. I did not exercise this.

## Formal check

None. The defect is shown by concrete integer witnesses with exact areas, so a formal model would not reduce any real uncertainty.

## Verdict

**CONFIRMED, and broader than stated.** The original validator accepts overlaps with large positive area. These are not confined to "selected shapes" or to coincident copies: they include half-slid equal-height items and contained polygons (triangle or diamond inside a square) that share no edge. Ordinary proper-crossing overlaps are rejected. The cause is the vertex-in-polygon plus proper-crossing test, not floating-point tolerance.

## Disposition assessment

I **agree with withholding the original**. The task's only safeguard against "impossible strip widths" fails on simple integer inputs. The candidate fully controls the emitted layout, and the score depends only on width. An optimization benchmark whose feasibility check a submission can bypass cannot rank solvers. A note alone would not be enough. A repaired version would need a separate review.

## Recommended publishable wording

"The original scorer's geometry check misses many overlaps with positive area, including identical copies placed at the same position and polygons contained inside other polygons. These are accepted with exact integer coordinates, so the cause is not numerical tolerance. Because the score depends only on strip width, this check cannot guarantee that winning layouts are feasible, and the original task is withheld."

Drop "five equal-width cases showed no score improvement". It describes diagnostics that did not test score impact.

## Repair note

Smallest correct fix: replace `polygons_overlap` with an interior-intersection test that treats contact as legal. For example, compute the intersection area with exact rational arithmetic (or shapely/GEOS) and reject if it exceeds a small absolute or relative threshold. Alternatively, run strict interior-point tests: check edge midpoints and the centroids of a triangulation, not just vertices, and treat collinear overlapping edges with opposite interior sides correctly. Also enforce `allowed_orientations`. The earlier general candidate (`work/task-repairs/jagua-general-polygon-overlap-sol-v1/evaluate.py`) was not re-reviewed here. Any repair must be tested against the containment and half-slide witnesses above, not only against coincident copies.

## Limits

- No full-scorer run and no measured score inflation. I started an end-to-end run with a modified `lbf` that solved with demand 1 and then repeated poses, but stopped it before any result and removed that code. Treating a working score-gaming submission as an audit deliverable seemed inappropriate. Score impact is therefore an analytic inference.
- The witnesses are hand-made instances, not the hidden assets. That this happens on hidden assets rests on the code path, which ignores instance specifics, and on the earlier shapes1 witness, which I did not re-run.
- I did not compute an exact rational polygon-clipping oracle; for these integer rectangles, triangles and diamonds the closed-form areas are the exact oracle. Shapely 2.2.0 is the second oracle.
- No assessment of historical submissions or leaderboard impact.
