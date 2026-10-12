# Treant's Forest, fixed version: change the score scale only

## What this fixes

The grader caps each case at 2N² turns, so the highest raw result any submission can reach is 92304. The original score scale puts its reference points far above that, so even a perfect submission scores only 21.02 out of 100. The fixed version replaces the score scale with a straight line from the shipped baseline (3418) to the cap (92304); the grader and raw results are unchanged.

## What changes

### The problem in detail

Each case's raw result is the adventurer's turn count, and the tester program caps it at `max_turns = 2N²`, where N is the grid size
(tester:63,140). Summed over the 50 shipped cases, the cap is exactly **92304**. This was
recomputed from the case headers by `paired/normalize.py` and by
`scripts/_game-tasks-correctness/check_arith.py`.

The reference points of the original `piecewise_max` score scale are:

| Field | Value | Relation to the cap |
| --- | ---: | --- |
| `baseline` | 5369 | below the cap |
| `rank30` | 88189 | just below the cap |
| `rank1` | 330195 | 3.58× the cap |
| `super_anchor` | 451198 | above the cap |

As a result, the cap converts to 21.02/100 (exactly 2543510/121003). The 20–100 part of the
scale cannot be reached by any submission. See
`evidence/reviews/_game-tasks-correctness.md`, section 8.

Where these reference points came from was not recovered. They appear to come from past
leaderboard runs on a different scorer or set of cases.

### Exact change

Only `judge.rescale` (the score scale) in `task.json.in` changes; see `repair.patch`, generated with `diff -u`.

```
- "kind": "piecewise_max", "baseline": 5369.0, "rank30": 88189.0, "rank1": 330195.0, "super_anchor": 451198.0
+ "kind": "linear", "lower": 3418.0, "upper": 92304.0
```

**Fields set.**

- `kind = "linear"`.
- `lower = 3418`. This is the raw result of the shipped baseline (`print(0); print(-1)`) under the original
  grader, which gave 50/50 cases OK. It was measured again in this package's E2B (cloud) run.
- `upper = 92304`. This is Σ 2N² over the shipped cases, the exact maximum of the tester's score
  function.

**How `score_rescale.py` applies these fields.** `linear` maps
`100*(raw-lower)/(upper-lower)` and clips the result to [0, 100]. It reads only `lower` and
`upper`. `score_direction` stays `maximize`, which matches the linear map.

- The shipped baseline maps to 0.
- The cap maps to 100.
- The invalid test submission (raw 0) is clipped to 0.

**Fields removed: `baseline`, `rank30`, `rank1`, `super_anchor`.** `piecewise_max` needs all four.

- `rank1` and `super_anchor` lie above the reachable maximum, so keeping them cannot give a
  coherent 0–100 scale.
- No exact replacements for the rank-based reference points exist, and the instructions forbid inventing new
  ones.
- The original `baseline` (5369) is not the shipped baseline's raw result (3418), and `linear` would ignore
  it.

All four fields were therefore removed, rather than left in place as misleading or ignored
fields. Their past values remain in the original task JSON.

**Other fields.** `judge.image_tag`, `work`, `eval_cmd`, the parser and the timeouts are unchanged.

### Why this is the smallest change

- No grader or work file changes.
- The tester, cases, grader and raw results are byte-identical.
- The `Dockerfile` is a FROM-only reference to the original grader digest. No new image is needed.
  It exists only to satisfy the package layout and the side-by-side run.

### Are scores comparable?

**Scores out of 100 from the fixed version are not comparable with those from the original for any raw result above the
shipped baseline (raw > 3418).**

- The fixed scale is linear from the shipped baseline to the cap.
- The original scale is piecewise, with a ceiling of 21.02 and a different lower reference point (5369).

Raw `TOTAL_SCORE` values stay comparable across versions. The rank-based reference points no longer exist, so a
score of 20 or 80 in the fixed version has no meaning as a leaderboard percentile.

## How it was checked

The side-by-side run used one E2B job with the original `eval_cmd` and `--network none`. See `paired/results.md`. Raw results are identical under both versions; only the conversion to 0–100 differs.

| Submission | Raw result (original and fixed) | Cases OK | Score out of 100, original | Score out of 100, fixed |
| --- | ---: | --- | ---: | ---: |
| Shipped baseline | 3418 | 50/50 | 0.00 | 0.00 |
| Honest greedy | 17960 | 50/50 | 3.04 | 16.36 |
| Invalid (treant on the revealed entrance) | 0 | 0/50, all WA (wrong answer) | 0 | 0 |

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh
```

`materialize.sh` takes the following steps:

1. Pull the pinned image(s) by digest, unless already present.
2. Extract the original files with `docker create` and `docker cp`. No container runs in this step.
3. Check each original against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of every file under `files/` (and `orig/`) against `source-lock.json` → `materialize.outputs`. Any mismatch fails loudly.

After that, the `Dockerfile` builds without changes. Regenerated files keep the file mode they have in the image.
See `../MATERIALIZE-CHECK.md` for how each package was verified.

Only the task JSON changes (`task-json.diff`). `materialize.sh` is a verified no-op, and the `Dockerfile` only pins the unchanged grader image.

## Limits

- 92304 is the exact upper bound on the raw result. Reaching it on every case has not been
  demonstrated; the best honest result on a single case was 47% of that case's cap.
- A linear scale from the baseline to the cap squeezes realistic strong scores together. That cost comes from
  using only exactly computable reference points instead of ones taken from a leaderboard.
- The 2N² cap is still not disclosed in the README; that would be a separate change to what the solver
  sees.
- The question raised in the review about movement rules (the tester versus the original AHC054 game)
  is not addressed by this fix.
