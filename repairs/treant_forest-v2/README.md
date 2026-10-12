# treant_forest v2: rescale anchors only

## Defect

Each case's score is the adventurer's turn count, and the tester caps it at `max_turns = 2N²`
(tester:63,140). Summed over the 50 shipped cases, the cap is exactly **92304**. This was
recomputed from the case headers by `paired/normalize.py` and by
`scripts/_game-tasks-correctness/check_arith.py`.

The v1 `piecewise_max` anchors are:

| Field | Value | Relation to the cap |
| --- | ---: | --- |
| `baseline` | 5369 | below the cap |
| `rank30` | 88189 | just below the cap |
| `rank1` | 330195 | 3.58× the cap |
| `super_anchor` | 451198 | above the cap |

As a result, the cap normalizes to 21.02/100 (exactly 2543510/121003). The 20–100 part of the
scale cannot be reached by any submission. See
`evidence/reviews/_game-tasks-correctness.md`, section 8.

The provenance of these anchors was not recovered. They appear to come from historical
leaderboard runs on a different scorer or case set.

## Exact change

Only `judge.rescale` in `task.json.in` changes; see `repair.patch`, generated with `diff -u`.

```
- "kind": "piecewise_max", "baseline": 5369.0, "rank30": 88189.0, "rank1": 330195.0, "super_anchor": 451198.0
+ "kind": "linear", "lower": 3418.0, "upper": 92304.0
```

**Fields set.**

- `kind = "linear"`.
- `lower = 3418`. This is the shipped baseline's score (`print(0); print(-1)`) under the original
  judge, which gave 50/50 cases OK. It was measured again in this package's E2B run.
- `upper = 92304`. This is Σ 2N² over the shipped cases, the exact maximum of the tester's score
  function.

**How `score_rescale.py` applies these fields.** `linear` maps
`100*(raw-lower)/(upper-lower)` and clips the result to [0, 100]. It reads only `lower` and
`upper`. `score_direction` stays `maximize`, which matches the linear map.

- The shipped baseline maps to 0.
- The cap maps to 100.
- The invalid control (raw 0) clips to 0.

**Fields removed: `baseline`, `rank30`, `rank1`, `super_anchor`.** `piecewise_max` needs all four.

- `rank1` and `super_anchor` lie above the attainable maximum, so keeping them cannot give a
  coherent 0–100 scale.
- No exact replacement rank anchors exist, and the instructions forbid inventing new rank
  anchors.
- The v1 `baseline` (5369) is not the shipped baseline's score (3418), and `linear` would ignore
  it.

All four fields were therefore removed rather than left in place as misleading or ignored
fields. Their historical values remain in the v1 task JSON.

**Other fields.** `judge.image_tag`, `work`, `eval_cmd`, the parser and the timeouts are unchanged.

## Why this is minimal

- No judge or work file changes.
- The tester, cases, evaluator and raw scores are byte-identical.
- The `Dockerfile` is a FROM-only reference to the original judge digest. No new image is needed.
  It exists only to satisfy the package layout and the paired run.

## Score compatibility

**v2 normalized scores are not comparable with v1 normalized scores for any raw score above the
shipped baseline (raw > 3418).**

- v2 is linear from the shipped baseline to the cap.
- v1 is piecewise, with a 21.02 ceiling and a different lower anchor (5369).

Raw `TOTAL_SCORE` values stay comparable across versions. The rank anchors no longer exist, so a
v2 score of 20 or 80 has no leaderboard-percentile meaning.

## Paired evaluation

The run used one E2B job with the original `eval_cmd` and `--network none`. See `paired/results.md`.

| Submission | Raw score (v1 and v2) | Cases OK | v1 normalized | v2 normalized |
| --- | ---: | --- | ---: | ---: |
| Shipped baseline | 3418 | 50/50 | 0.00 | 0.00 |
| Honest greedy | 17960 | 50/50 | 3.04 | 16.36 |
| Invalid (treant on the revealed entrance) | 0 | 0/50, all WA | 0 | 0 |

## Limits

- 92304 is the exact upper bound on the score. Reaching it on every case has not been
  demonstrated; the best honest per-case result was 47% of that case's cap.
- A linear scale from baseline to cap compresses realistic strong scores. That cost comes from
  using only exact anchors instead of leaderboard-derived ones.
- The 2N² cap is still not disclosed in the README; that would be a separate solver-visible
  change.
- The movement-semantics question raised in the review (tester versus the original AHC054 game)
  is not addressed by this repair.

## Build

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

Only the task JSON changes (`task-json.diff`). `materialize.sh` is a verified no-op, and the `Dockerfile` only pins the unchanged judge image.
