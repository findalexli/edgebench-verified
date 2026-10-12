# schemathesis_config_modernization, fixed version: metric decorator identity

## What this fixes

The task's specification says the `@schemathesis.metric` decorator returns the function unchanged, but the original tests only check that it returns something callable. A wrapper therefore scores the same as a correct decorator. The fixed version adds one test that checks the function comes back unchanged; the gap it closes is one test item, 1/150 of the total score.

## The problem

Details are in the [review](../../evidence/reviews/schemathesis_config_modernization.md). `TODO.md` Target 3 says `@schemathesis.metric` "Returns the function unchanged", but Phase 3 of the hidden tests only checks `callable(...)`. A wrapper that forwards calls to the function therefore scores the same as a correct decorator. The gap is one test item, 1/150 of the total score, and it gives no advantage over correct work.

## What changes

The change is the earlier reviewed patch (`proposedrepairs/schemathesis-config-function-identity/`), applied unchanged:

- `/tests/test_03_metric_system.py` gains `test_metric_decorator_preserves_exact_function_identity`. It asserts `metric(f) is f` and unregisters the function afterward.
- `/tests/test.sh` changes `PHASE3_TOTAL` and `PHASE3_EXPECTED` from 15 to 16.

The weights, the parser, the score scale and the other 131 tests are unchanged. `task.json.in` changes only `judge.image_tag` (`affdace5163f` → `function-identity-v2`).

**Why the change is minimal:** it adds one assertion of the stated specification, plus the test count that follows from it.

**Score compatibility:** scores from the fixed grader are not comparable with scores from the original grader when Phase 3 is partly passed. The phase has 16 tests instead of 15, so an imperfect Phase 3 yields a different fraction. Scores that fully pass or fully fail Phase 3 are identical.

## How it was checked

The side-by-side run of the original and fixed graders is in [paired/results.md](paired/results.md). Every test submission ran through the full original evaluation command:

- the correct implementation (overlay) scores the same on both graders (0.135313);
- the wrapper loses exactly 1/160;
- the test submission that never registers the function fails on both graders.

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t ebv/schemathesis_config_modernization-judge:v2 .
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
- The original task, its images and the earlier decision records are untouched.
