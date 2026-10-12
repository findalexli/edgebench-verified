# schemathesis_config_modernization v2: metric decorator identity

**Defect** ([review](../../evidence/reviews/schemathesis_config_modernization.md)): `TODO.md` Target 3 says `@schemathesis.metric` "Returns the function unchanged", but Phase 3 only checks `callable(...)`. A forwarding wrapper therefore scores the same as a correct decorator. The gap is one test item, 1/150 of the total score, and it gives no advantage over correct work.

**Change:** the earlier reviewed patch (`proposedrepairs/schemathesis-config-function-identity/`), applied unchanged:
- `/tests/test_03_metric_system.py` gains `test_metric_decorator_preserves_exact_function_identity`, which asserts `metric(f) is f` and unregisters afterward.
- `/tests/test.sh` changes `PHASE3_TOTAL` and `PHASE3_EXPECTED` from 15 to 16.

Weights, the parser, rescale and the other 131 tests are unchanged. `task.json.in` changes only `judge.image_tag` (`affdace5163f` → `function-identity-v2`).

**Why minimal:** one assertion of the stated contract, plus the count it implies.

**Score compatibility:** v2 scores are not comparable with v1 when Phase 3 is partially passed. The phase has 16 tests instead of 15, so a non-perfect Phase 3 yields a different fraction. Fully passing and fully failing Phase 3 scores are identical.

**Paired evaluation:** [paired/results.md](paired/results.md). Under the full original eval command:
- the correct overlay is unchanged (0.135313);
- the wrapper falls by exactly 1/160;
- the non-registering control fails in both versions.

**Limits:** the overlay is a minimal Target 3 implementation, not a complete solution, so absolute scores are partial. No historical submissions were examined. The original task, its images and the earlier disposition records are untouched.

## Build

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
