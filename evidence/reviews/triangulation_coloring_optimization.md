# Review: `triangulation_coloring_optimization`

> **Note (2026-10-12).** Not covered below: the dependence of scores on the grader's CPU count (8 cases at once under a 30 s wall-clock limit; the publisher's leaderboard setting gives the grader 4 CPUs). It is measured (`evidence/runs/triangulation_coloring_optimization-cpu4v8-a`, `-b`) and fixed in the same new version, which now also runs at most as many cases at once as the grader's CPU quota (`evidence/runs/triangulation-v2-paired-cpu`). See `cases/triangulation_coloring_optimization.md`.

## Claim under review

> "All ten acquired large meshes violate the promised geometry: triangle interiors overlap. The cause and future inputs remain untested." (docs/FINDINGS.md)

Decision record (evidence/selected/12-finding-decisions.json): "All ten acquired N=512 meshes have positive-area triangle overlaps, violating the stated planar-triangulation input contract." Disposition: **withhold original** ("Excluded exact version").

## Pinned artifacts

- Task JSON `tasks/triangulation_coloring_optimization.json`, sha256 `4def4778…8621b7`.
- Judge image `seededge/edgebench.judge.triangulation_coloring_optimization@sha256:beeea763…dcf671` (pulled and run).
- Work image `seededge/edgebench.work.triangulation_coloring_optimization@sha256:618da32c…6c05b` (pulled; workspace copied out with `docker create`/`docker cp`, container removed).
- The judge image's `cases/*`, `tools/src/*`, `tools/bin/tester` and `/tmp/eval_triangulation_coloring.py` have the same sha256 as the extracted `$W/work/task-sources/merged/...` copies. Hashes:
  - cases 0000–0009: `8e0c5efc…`, `fba99cce…`, `362f488d…`, `dfaf087b…`, `14f9d0e4…`, `71934c46…`, `31ea2a43…`, `44c321e6…`, `336e98f9…`, `db31b15c…`
  - `verifier.py` `1f0c714a…`, `triangulation.py` `32862fe5…`, `gen.py` `67201f1e…`, `delaunay.py` `2681c12e…`, `tools/bin/tester` `01b6e17b…` (a 25-line Python wrapper around `verifier.Verifier`), eval script `1c5100f5…`, README `51eca84c…`
  - Work image only: `sample_data/0000..0002.txt` `3c3a4ec2…`, `d6c6ddcb…`, `ea69321d…`; `sample_data/README.md` `b690ceb5…`; `tools/README.md` `38020c9a…`. The work image ships the same `tools/src` and `tester` as the judge image.

## Contract

- README.md: "Given **N = 512** points … and a **triangulation** of those points". Flip rule: "if an edge is a diagonal of a **convex quadrilateral** formed by two adjacent triangles, replace it with the other diagonal. The result remains a valid triangulation." Constraints: "**M ≤ 1024** triangles", "Coordinates in [1, 10⁴], no three collinear points".
- agent_query: "flips change the triangulation; **U** (ugly triangles) is counted on the **final** triangulation"; "The local `tester` applies flips exactly like the judge".
- tools/README.md: the tester "**Executes each flip** on the input triangulation (invalid flip → wrong answer)"; "matches the official CodeChef scoring model".
- sample_data/README.md: cases are built with a "pre-flip K", described as "the random edge-flip count applied during case generation (official CodeChef parameter)". Sample K values are 16 and 256. Judge seeds "start at 9,000,000".
- The geometry is therefore promised: the input is a planar triangulation of the given points, and flip legality is defined geometrically (convex quadrilateral). The contract does not promise a Delaunay triangulation, and nothing says the points are in convex position.
- I could not check the CodeChef TRICOL statement. The fetched page had only a title. Statements about fidelity to CodeChef are unverified.

## Independent reproduction

All geometry uses exact Python integers (`orient` determinants); no floats. Scripts are in `evidence/scripts/triangulation_coloring_optimization/`.

1. `check_geometry.py` runs these checks on each case:
   - exact separating-axis test for each distinct pair of triangles with overlapping open interiors;
   - proper edge crossings;
   - vertices strictly inside a triangle;
   - duplicate and degenerate triangles;
   - non-manifold edges;
   - Euler characteristic and vertex links;
   - exact area excess against the convex hull;
   - collinear point triples (gcd-direction method).

   Results for the hidden cases (`cases_geometry.jsonl`):

| case | X,Y | M (planar 2N−2−h) | overlapping tri pairs | crossing edge pairs | vertex inside tri | folded edges | duplicate tris | non-manifold edges | V−E+F |
|---|---|---|---|---|---|---|---|---|---|
| 0000 | 10,160 | 1007 (1007) | 36 | 9 | 8 | 12 | 0 | 0 | 1 |
| 0001 | 20,80 | 1006 (1007) | 21 | 6 | 3 | 9 | 0 | 0 | 1 |
| 0002 | 40,40 | 1003 (1004) | 24 | 6 | 4 | 11 | 1 | 1 | 2 |
| 0003 | 80,20 | 1004 (1006) | 17 | 4 | 3 | 9 | 0 | 0 | 1 |
| 0004 | 160,10 | 1002 (1003) | 48 | 15 | 6 | 18 | 0 | 0 | 1 |
| 0005 | 10,160 | 1002 (1003) | 538 | 156 | 89 | 189 | 8 | 8 | 9 |
| 0006 | 20,80 | 1003 (1005) | 551 | 161 | 92 | 195 | 7 | 7 | 8 |
| 0007 | 40,40 | 1002 (1003) | 583 | 173 | 91 | 219 | 11 | 12 | 13 |
| 0008 | 80,20 | 1001 (1005) | 502 | 138 | 87 | 195 | 10 | 10 | 11 |
| 0009 | 160,10 | 1004 (1005) | 583 | 163 | 100 | 222 | 9 | 9 | 10 |

   - No case has degenerate triangles or collinear point triples.
   - Every case's sum of |area| exceeds the hull area (strict overlap).
   - In 9 of 10 cases, M is below 2N−2−h. The triangle set also does not cover the convex hull.

2. Cause, established with the shipped `gen.py` (`regen_compare.py`, `run_gen.py`):
   - `gen.generate(9000000, N=512, K=16, X=10, Y=160)` reproduces hidden `cases/0000.txt` byte for byte.
   - `gen.generate(1000001/2/3, …)` reproduces all three `sample_data` files byte for byte.
   - The only change was replacing the O(N³) `has_collinear_triple` with an exactly equivalent O(N² log N) exact test that returns the same boolean.
   - I did not recover the seeds for cases 0001–0009. I searched 9000000–9002000 and simple strides. Their defect profile matches K=16 for 0001–0004 and K=256 for 0005–0009.
   - Pure generator output (K=0) has no overlaps, crossings, folds or duplicates, but misses a few hull triangles because of a Bowyer-Watson super-triangle artifact.
   - Overlaps grow with K: 9–11 pairs at K=16, 68–91 at K=64, 448–541 at K=256, and 3156 at K=1024 (`gen_results.jsonl`).
   - Root cause: `Triangulation.is_flippable` checks only that the two apexes a and b lie on opposite sides of line uv. It never checks that u and v lie on opposite sides of line ab. This accepts non-convex quadrilaterals, and the flip folds the triangulation. `gen.apply_random_flips` uses this same predicate, so the bug is in the shared library, not only in the inputs.

3. Scoring impact (`flip_rule_analysis.py`, `flip_rules.jsonl`, `judge_image_run.log`):
   - On every hidden case, 317–379 interior edges pass the official flip predicate but are not diagonals of a convex quadrilateral. The README rule forbids these flips.
   - No convex-quadrilateral flip is rejected. The official rule is a strict superset of the documented rule.
   - Through the original `tools/bin/tester` in the pinned judge image, on `cases/0009.txt`:
     - The trivial output scores `Score = 644809` (U=803).
     - Adding one README-illegal non-convex flip (edge 39–52) is accepted and scores `Score = 641611` (U=801).
     - A flip the documented contract forbids therefore improves the official score.
   - N=4 control (`n4_nonconvex.txt/.out`) is a valid, non-overlapping 2-triangle input with a reflex quadrilateral:
     - The official tester accepts the forbidden flip (`Score = 41`).
     - The resulting two triangles overlap (1 overlapping pair, a vertex strictly inside, exact area excess 588/2).
     - So the defect does not need a bad input.
   - Duplicate triangles (in 6 of 10 hidden cases) are stored twice and counted twice in U. They can never be flipped: their edges have either 3 incident entries or a == b.
   - Full original eval, shipped trivial `solution.py`, pinned judge image: `CASES_OK 10`, `TOTAL_SCORE 6092430`. The scoring path works. The rescale `baseline` 6102378 is close to but not equal to this trivial total; I did not investigate where it comes from.

## Refutation attempts

- "Geometry is cosmetic; it is a combinatorial problem."
  - This is partly true. U counts the listed triples and ignores coordinates.
  - It fails for flips. Flip legality uses coordinates, and the official predicate diverges from the stated convex rule on about 25% of interior edges per case. That changes which moves exist. A solver obeying the README cannot use moves that score better (shown on case 0009).
  - Folded edges (9–222 per case) are combinatorially adjacent pairs that are unflippable only because of the bad embedding.
- "The solver can see it, so it is fair."
  - The work image ships the same `verifier.py`, `tester` and three sample files.
  - The samples have the same defects: 17–528 overlapping pairs and 1–10 duplicate triangles.
  - A solver that tests against the tester sees exactly the judge's rule, and hidden-case behavior is not a surprise relative to the samples. This limits the harm: scores are consistent and reproducible, not random.
  - The harm is a contract and validity problem. The documented problem ("valid triangulation", "convex quadrilateral", "M ≤ 1024 … triangulation") differs from the scored problem: a lax flip rule, non-manifold inputs and double-counted duplicate triangles.
- "Overlap counts are edge incidences."
  - The counts here are distinct triangle pairs from an exact separating-axis test. The earlier caveat no longer applies.
- "Only an audit fixture triggers it."
  - No fixture is needed. The ten shipped judge inputs trigger it directly.
  - A real one-flip submission passing through the real tester changes the score.

## Formal check

None. The predicates are integer determinants evaluated exactly, and the separating-axis criterion for convex polygons with disjoint interiors is standard. A proof assistant would not reduce any real uncertainty.

## Verdict

**CONFIRMED, and broader than claimed.** All ten hidden inputs have positive-area triangle overlaps. Six are not even combinatorial triangulations (duplicate triangles, non-manifold edges). The cause is now established: the shared `is_flippable` predicate accepts non-convex flips, and `gen.py` applies K random flips with it. Cases 0000 and all three samples are reproduced byte for byte. The same predicate is the official scorer's move rule, so the defect is not cosmetic: the scorer accepts, and rewards, moves the task statement forbids.

## Disposition assessment

I agree with withholding the original. The scored problem differs from the documented one in its move set as well as its inputs, and both the inputs and the legality rule must change. Retaining it with a note is defensible only if the task is rewritten as "optimize against the shipped flip predicate". That would contradict the README and the claimed CodeChef alignment.

A repair is cheap and well defined, but it changes the task. It needs re-scoring and new rescale anchors. The current `baseline`/`rank*` anchors were set on the defective cases and rule.

## Recommended publishable wording

"All ten hidden inputs contain overlapping triangles, and six also contain duplicated triangles. The inputs were made by the task's own generator, which applies random edge flips using a flip check that also accepts non-convex quadrilaterals. The official scorer uses the same check, so it accepts and can reward flips the task statement forbids; we withhold the original."

## Repair note

There was no earlier repair to compare. The smallest correct fix:

1. In `triangulation.py` `is_flippable`, also require `a != b`, `ccw(a,b,u)*ccw(a,b,v) < 0`, and that neither new triangle duplicates an existing one.
2. Regenerate the ten cases and three samples with the same `gen.py` and seeds once the fix is in. Seeds are known for 0000 (9000000) and the samples. The others are not recovered, so new seeds would have to be documented.
3. Optionally, add hull triangles that the Delaunay super-triangle drops, or state the actual promise as "a triangulated polygon of the points".
4. Re-derive the rescale anchors.

I have not run this fix end-to-end.

## Limits

- The seeds for cases 0001–0009 were not recovered. That they came from gen.py rests on the matching defect profile, plus the exact match for 0000 and the samples.
- I did not read the CodeChef TRICOL original, so I cannot say whether CodeChef's own data or checker shares the bug.
- I did not measure how much a strong solver gains from non-convex flips across a full optimization. Only the single-flip gain (U 803 → 801 on case 0009) is shown.
- The origin of the rescale anchors was not examined.
