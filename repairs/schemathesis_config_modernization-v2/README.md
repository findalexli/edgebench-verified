# schemathesis_config_modernization, fixed version: metric decorator identity

## What this fixes

The task's specification says the `@schemathesis.metric` decorator returns the function unchanged, but the original tests only check that it returns something callable. A wrapper therefore scores the same as a correct decorator. The fixed version adds one test that checks the function comes back unchanged; under it a wrapper loses one test item, 1/160 of the total score (0.625 points out of 100).

## The problem

Details are in the [review](../../evidence/reviews/schemathesis_config_modernization.md). `TODO.md` Target 3 says `@schemathesis.metric` "Returns the function unchanged", but Phase 3 of the hidden tests only checks `callable(...)`. A wrapper that forwards calls to the function therefore scores the same as a correct decorator. The gap is one test item: 1/160 of the total score under the fixed version's 16-test Phase 3 (1/150 for one test of the original 15-test phase). It gives no advantage over correct work.

## What changes

The change is the patch proposed in the review, applied unchanged:

- `/tests/test_03_metric_system.py` gains `test_metric_decorator_preserves_exact_function_identity`. It asserts `metric(f) is f` and unregisters the function afterward.
- `/tests/test.sh` changes `PHASE3_TOTAL` and `PHASE3_EXPECTED` from 15 to 16.

The weights, the parser, the score scale and the 126 original tests are unchanged. `task.json.in` changes only `judge.image_tag` (`affdace5163f` → `function-identity-v2`).

**Why the change is minimal:** it adds one assertion of the stated specification, plus the test count that follows from it.

**Score compatibility:** scores from the fixed grader are not comparable with scores from the original grader when Phase 3 is partly passed. The phase has 16 tests instead of 15, so an imperfect Phase 3 yields a different fraction. Scores of submissions that pass all 16 tests of the fixed Phase 3, or fail all of them, are identical. A partly passed Phase 3 can move either way: a wrapper passing k of the 15 original tests loses k/2400, and an identity-preserving decorator passing k < 15 of them gains (15 − k)/2400; both are at most 1/160.

## How it was checked

The side-by-side run of the original and fixed graders is in [paired/results.md](paired/results.md). Every test submission ran through the full original evaluation command:

- the correct implementation (overlay) scores the same on both graders (0.135313);
- the wrapper loses exactly 1/160;
- the test submission that never registers the function fails on both graders.

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t edgebench.judge.schemathesis_config_modernization:function-identity-v2 .
```

`materialize.sh` takes the following steps:

1. Pull the pinned image(s) by digest, unless already present.
2. Extract the original files with `docker create` and `docker cp`. No container runs in this step.
3. Check each original against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of every file under `files/` (and `orig/`) against `source-lock.json` → `materialize.outputs`. Any mismatch fails loudly.

After that, the `Dockerfile` builds without changes. Regenerated files keep the file mode they have in the image.
See `../MATERIALIZE-CHECK.md` for how each package was verified.

## Limits

- The overlay is a minimal implementation of Target 3, not a complete solution, so the absolute scores are partial.
- No historical submissions were examined.
- The added test checks `schemathesis.generation.metrics.metric`; the top-level `schemathesis.metric`, which `TODO.md` names, is still only checked for being callable, so a wrapper re-exported at the top level (for example with `functools.wraps`) still passes all three metric tests although `schemathesis.metric(f) is f` is false (local probe). Closing this would need one more assertion and a new paired run.
- The package was rebuilt from scratch on a clean machine (`evidence/runs/materialize-check-g2`, `status: exit=0`): `materialize.sh` ran unchanged, both outputs matched the lock and the built image holds the locked test files.
- The original task, its images and the earlier decision records are untouched.
