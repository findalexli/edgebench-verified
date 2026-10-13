# treant_forest v2 paired evaluation

**E2B job.** One owned worker ran `paired/run.sh` and was killed by its exact ID. The run
took 42 s and ended with exit 0. Outputs are in `paired/result/out/`.

**Scoring path.** Every row used the original `eval_cmd`:

```
cd /home/workspace/treants_forest && python3 /tmp/eval_treants_forest.py
```

Containers ran with `--network none`, `--memory 4g` and `--cpus 8`.

- **v1** is the original judge image at digest `783e9ca2…`.
- **v2** is the image built inside the worker from the FROM-only Dockerfile.

**Hashes.** Inside both images these files hashed to the pinned values:

- `eval_treants_forest.py`: `ce2833ac…`
- `tools/bin/tester`: `6cbb3a72…`
- the 50 cases: `bc256294…`

**Normalization.** `normalize.py` uses the repo's `sforge/harness/score_rescale.py`. The
output is saved in `normalize.out.jsonl`.

- v1 anchors: `piecewise_max` with baseline 5369, rank30 88189, rank1 330195 and super 451198.
- v2 anchors: `linear` with lower 3418 and upper 92304.

| Submission | Image | Raw TOTAL_SCORE | Cases OK | Eval exit | v1 normalized | v2 normalized |
| --- | --- | ---: | --- | --- | ---: | ---: |
| Shipped baseline (`0`, `-1`) | v1 | 3418 | 50/50 OK | 0 | 0.00 | 0.00 |
| Shipped baseline | v2 | 3418 | 50/50 OK | 0 | 0.00 | 0.00 |
| Honest greedy (grid-only maze lengthening) | v1 | 17960 | 50/50 OK | 0 | 3.04 | 16.36 |
| Honest greedy | v2 | 17960 | 50/50 OK | 0 | 3.04 | 16.36 |
| Invalid: treant on the revealed entrance | v1 | 0 | 0/50 (all WA) | 0 | 0.00 | 0.00 |
| Invalid: treant on the revealed entrance | v2 | 0 | 0/50 (all WA) | 0 | 0.00 | 0.00 |

## Anchor endpoints

These rows are computed with `score_rescale.py`, not by running a submission.

| Raw | v1 | v2 | Exact v2 |
| ---: | ---: | ---: | --- |
| 0 | 0.00 | 0.00 | 0 |
| 3418 (shipped baseline) | 0.00 | 0.00 | 0 |
| 5369 (old v1 `baseline` field) | 0.00 | 2.19 | 97550/44443 |
| 92304 (= Σ 2N², the score cap) | **21.02** | **100.00** | 100 |
| 330195 (old rank1, exceeds the cap) | 80.00 | 100.00 | 100 |

## Checks against the spec

- **Trigger (the anchor defect).** Under v1, the highest raw score the tester can produce maps to
  21.02/100, so 79 points of the scale are unreachable. Under v2 the same raw score maps to 100.
  The honest policy's raw score of 17960 is 19.5% of the cap. v1 puts it at 3.04 and v2 at 16.36.
- **Valid controls.** Raw scores were identical in v1 and v2: 3418 for the baseline and 17960 for
  the honest policy, with all 50 cases OK. The judge is unchanged, so this is expected. Only the
  normalized value changes, and only because of the new anchors.
- **Invalid control.** Every case was rejected (`wrong answer: cannot place treant at revealed
  cell`), giving raw 0 and normalized 0 under both v1 and v2.
- The raw scores match an earlier local run of the original evaluator and tester, which gave 3418,
  17960 and 0.

## Limits

- 92304 is the exact upper bound on the score: `Score = turns` and `turns <= 2N²` (tester:63,140).
  Nobody has shown that a policy can reach the cap on all 50 cases. The best honest per-case
  result was 47% of that case's cap.
- `docker image inspect` printed nothing for the original image because of a format-template
  error. The image's identity rests on the pinned digest pull and on the in-image file hashes.

## Verdict

**Accepted** (anchors only; judge unchanged). Raw scores are identical in v1 and v2: 3,418 for the
baseline and 17,960 for the honest policy, all 50 cases OK. Only the normalized values change, from
the new anchors: the honest policy moves from 3.04 to 16.36. The invalid control scores raw 0 and
normalized 0 in both versions.
