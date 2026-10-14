# Schemathesis config modernization (`schemathesis_config_modernization`)

**Outcome:** Fixed. <mark>The Phase 3 tests check only that `@schemathesis.metric` returns something callable, not that it returns the function unchanged; under the fixed tests a wrapper loses one test item, 1/160 of the score (0.625 points out of 100).</mark>

![Phase 3 test results: the original tests pass both a correct decorator and a wrapper at 15/15; the fixed tests fail the wrapper at 15/16.](figures/schemathesis_config_modernization.svg)

*The original tests could not tell a wrapper from the correct decorator; the fixed tests add one test, worth 1/160 of the score.*

## What the task asks

The solver modernizes the configuration layer of schemathesis 3.39.16, a tool for testing web APIs. Hidden tests, grouped into phases, grade the result. The task text tells the solver to "Treat `/app/TODO.md` as the authoritative task specification." `TODO.md` Target 3 states that the "**`@schemathesis.metric` decorator**: Registers a metric function into a registry. Returns the function unchanged." A decorator is a function that takes another function and returns a function in its place. `TODO.md` uses the same wording for `@schemathesis.check`. Category: Systems & Software Engineering.

## What goes wrong

The decorator must return the function unchanged, but the original test `test_metric_decorator_returns_function` only asserts `callable(another_metric)`. A wrapper that forwards calls to the function therefore scores the same as a correct decorator.

We tested three variants of `metric` on a minimal implementation of Target 3.

- `identity` registers the function and returns it, which is correct.
- `wrapper` returns a forwarding wrapper built with `functools.wraps`, which is plausibly wrong.
- `no_register` never registers the function, which is clearly wrong.

These are the Phase 3 results under the original tests (`orig`) and the fixed tests (`repaired`).

```
variant=identity    tests=orig     :: 15 passed
variant=identity    tests=repaired :: 16 passed
variant=wrapper     tests=orig     :: 15 passed
variant=wrapper     tests=repaired :: 1 failed, 15 passed
variant=no_register tests=orig     :: 3 failed, 12 passed
variant=no_register tests=repaired :: 4 failed, 12 passed
```

Under the specification, the wrapper should lose the test item that checks identity. On the original grader it passes 15/15, the same as the correct decorator.

The effect is small. In behaviour, the wrapper is almost equivalent to the correct decorator. It keeps `__name__`, registers under the right name, returns the same values, and works with the collector and with `hypothesis.target`. The only differences are `decorated is original` and the presence of `__wrapped__`. The wrong implementation gains no advantage over a correct one and only avoids losing one item. The authors probably intended identity, since the Phase 6 test asserts `result is my_func` for `@check` and Phase 3 has no such check.

## How much it matters

The effect is at most 1/160 of the total, 0.625 points out of 100. The score is Σ(weight × passed/total)/10 over six phases, and Phase 3 has weight 1. With the fixed version's 16 Phase 3 tests, a wrapper that passes k of the 15 original tests drops from k/15 to k/16 of the Phase 3 weight, a loss of k/2400; at k = 15 that is 1/160, the measured −0.006250. (In the original 15-test phase, one test is worth 1/15 × 1/10 = 1/150.)

The change does not only lower scores. A submission whose decorator returns the function unchanged but passes only k < 15 of the original Phase 3 tests rises from k/15 to (k+1)/16, a gain of (15 − k)/2400. Either change is at most 1/160 per run. Only submissions with a wrapper decorator, or with a partly passed Phase 3, score differently.

## The fix

- `/tests/test_03_metric_system.py` gains `test_metric_decorator_preserves_exact_function_identity`. The test asserts `metric(f) is f` and unregisters the function afterwards.
- `/tests/test.sh` changes `PHASE3_TOTAL` and `PHASE3_EXPECTED` from 15 to 16.

The weights, the parser, the score scale and the 126 original tests are unchanged. In `task.json.in`, only `judge.image_tag` changes.

| Variant | Role | Original grader (raw) | Fixed grader (raw) | Change | Phase 3, original → fixed |
|---|---|---|---|---|---|
| starter | untouched starting `/app` | 0.031466 | 0.031466 | 0 | 0/15 → 0/16 |
| identity | reviewer's correct Target 3 overlay (`metric` returns `func`) | 0.135313 | 0.135313 | **0** | 15/15 → 16/16 |
| wrapper | plausibly wrong: returns a `functools.wraps` forwarding wrapper | 0.135313 | 0.129063 | **−0.006250 (−1/160)** | 15/15 → 15/16 |
| no_register | invalid test submission: never registers | 0.115313 | 0.110313 | −0.005000 | 12/15 → 12/16 |

In every variant, the only test items whose results differ are the added identity test and, for the wrapper, the Phase 3 "all passed" item (`test_phase_3`), which flips from passed to failed. The other 131 original items keep their result from the original grader. Scores are raw values on a 0 to 1 scale; the task's `linear` 0..1 scale gives the score out of 100 as 100 × raw (0.135313 is 13.53). Scores are partial because the overlay implements Target 3 only, not the whole task.

Scores from the original and fixed graders are identical when the submission passes all 16 tests of the fixed Phase 3, or fails all of them. When Phase 3 is partly passed they are not comparable, because the phase has 16 tests instead of 15, and an imperfect phase yields a different fraction.

## How we checked it

- We ran the original grader in the original public image, pinned by digest. The grader image holds the unmodified schemathesis 3.39.16 starting code in `/app` and no reference solution. Each variant and the untouched starting code ran through the full original `judge.eval_cmd` (`bash /tests/test.sh` plus the structured parser), in a fresh `--network none` container, under both the original and the fixed tests.
- For an independent check, the reference is the sentence of the specification in `TODO.md` ("Returns the function unchanged"), and the added test checks it directly. No formal model applies.
- We repeated the side-by-side run of the original and fixed graders three times, and no outcome changed (`data/paired-repeatability.md`).

## Limits

- We ran no AI model or solver. The effects shown come only from test submissions that we wrote.
- The overlay is a minimal implementation of Target 3, not a complete solution to the task, so the absolute scores are partial.
- We examined no historical submissions, so we do not know how often real solvers write wrapper decorators.
- We did not extract `TODO.md` again from the pinned work image.
- The added test checks `schemathesis.generation.metrics.metric`; for the top-level `schemathesis.metric`, which `TODO.md` names, the tests still check only that it is callable, so a wrapper re-exported at the top level (for example with `functools.wraps`) still passes all three metric tests although `schemathesis.metric(f) is f` is false (local probe). Closing this would need one more assertion and a new paired run.
- We rebuilt the package from scratch on a clean machine (`evidence/runs/materialize-check-g2`, `status: exit=0`). `materialize.sh` ran unchanged, both outputs matched the lock, and the built image holds the locked test files.
- This repository does not store the hidden tests. The scripts extract them from the pinned grader image when you rerun the check.

## Reproduce

- Grader image digest: `sha256:ff71a766…`.

1. Run `evidence/scripts/schemathesis_config_modernization/fetch_tests.sh`. It extracts the hidden tests from the pinned grader image and applies the patch.
2. Run `evidence/scripts/schemathesis_config_modernization/run_in_judge.sh` with `metrics_base.py`. The saved output is `observed_output.txt`.

The side-by-side run of the original and fixed graders is `repairs/schemathesis_config_modernization-v2/paired/run.sh`, with results in `paired/results.md` and `paired/raw-summary.md`. The fix itself is in `repairs/schemathesis_config_modernization-v2/repair.patch`, `Dockerfile` and `source-lock.json`.

Supporting records: `repairs/schemathesis_config_modernization-v2/` (the folder holding the fixed version) and `evidence/reviews/schemathesis_config_modernization.md`.
