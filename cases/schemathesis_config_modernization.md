# Schemathesis config modernization (`schemathesis_config_modernization`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Systems & Software Engineering
- **Decision:** Repair v2. Phase 3 checks only that `@schemathesis.metric` returns something callable, not that it returns the function unchanged. The gap is one test item, about 1/150 of the score.

## What the task promises

The solver is told to "Treat `/app/TODO.md` as the authoritative task specification." `TODO.md` Target 3 states that the "**`@schemathesis.metric` decorator**: Registers a metric function into a registry. Returns the function unchanged." It uses the same wording for `@schemathesis.check`.

## What we checked and how

- **Pinned judge image.** We pulled it and found that `/app` is the unmodified schemathesis 3.39.16 starter. The image contains no reference solution.
- **Overlay.** We wrote a minimal Target 3 overlay (a registry, `MetricContext`, a collector and `maximize`) with three variants of `metric`:
  - `identity` registers the function and returns it. This is correct.
  - `wrapper` returns a `functools.wraps` forwarding wrapper. This is plausibly wrong.
  - `no_register` never registers the function. This is clearly wrong.
- **Phase 3 runs.** Each variant was run against the original and the repaired `test_03_metric_system.py` in the judge image (`--network none --memory 2g --cpus 2`).
- **Paired v1/v2 run.** One E2B worker ran every variant, plus the untouched starter, through the full original `judge.eval_cmd` (`bash /tests/test.sh` plus the structured parser). Each run used a fresh `--network none` container with 2 CPU and 3 GiB.
- **Original identity.**
  - Judge image `seededge/edgebench.judge.schemathesis_config_modernization@sha256:ff71a766…`.
  - `test_03_metric_system.py` sha256 `42bc43ff…`.
  - `test.sh` sha256 `67f455c3…`.
  - `TODO.md` sha256 `f9d3cc5e…`, taken from the earlier cloud export and not re-extracted from the work image.

## What we found

**Confirmed, minor.** The original `test_metric_decorator_returns_function` only asserts `callable(another_metric)`. A forwarding wrapper and a correct decorator therefore score the same.

Phase 3 under the original and repaired tests:

```
variant=identity    tests=orig     :: 15 passed
variant=identity    tests=repaired :: 16 passed
variant=wrapper     tests=orig     :: 15 passed
variant=wrapper     tests=repaired :: 1 failed, 15 passed
variant=no_register tests=orig     :: 3 failed, 12 passed
variant=no_register tests=repaired :: 4 failed, 12 passed
```

Expected under the contract: the wrapper should lose the identity item. Observed under the original evaluator: the wrapper passes 15/15, the same as the correct decorator.

**Maximum score effect:** about 1/150 of the total. Phase 3 has weight 1 of 10 and 15 tests, so one test is worth 1/15 × 1/10.

**Materiality.** In behaviour the wrapper is almost equivalent to the correct decorator. It keeps `__name__`, registers under the right name, returns the same values and works with the collector and `hypothesis.target`. The only differences the reviewer found are `decorated is original` and the presence of `__wrapped__`. The wrong implementation gains no advantage over a correct one; it only avoids losing one item. The authors probably intended identity: the Phase 6 test asserts `result is my_func` for `@check`, but Phase 3 has no such check.

**Earlier disposition re-checked.** An earlier audit withheld the original as an "explicit release-policy choice" because this identity check was missing. Re-checking showed that the gap is one test item and gives no advantage over correct work. The task should not be counted as withheld for a defect. It is published as a versioned repair instead.

## Repair

v2 applies the earlier reviewed patch unchanged:

- `/tests/test_03_metric_system.py` gains `test_metric_decorator_preserves_exact_function_identity`. The test asserts `metric(f) is f` and unregisters the function afterwards.
- `/tests/test.sh` changes `PHASE3_TOTAL` and `PHASE3_EXPECTED` from 15 to 16.

Weights, the parser, the rescale and the other 131 tests are unchanged. In `task.json.in`, only `judge.image_tag` changes.

| Variant | Role | v1 score | v2 score | Delta | Phase 3 v1 → v2 |
|---|---|---|---|---|---|
| starter | untouched starter `/app` | 0.031466 | 0.031466 | 0 | 0/15 → 0/16 |
| identity | reviewer's correct Target 3 overlay (`metric` returns `func`) | 0.135313 | 0.135313 | **0** | 15/15 → 16/16 |
| wrapper | plausibly wrong: returns a `functools.wraps` forwarding wrapper | 0.135313 | 0.129063 | **−0.006250 (−1/160)** | 15/15 → 15/16 |
| no_register | invalid control: never registers | 0.115313 | 0.110313 | −0.005000 | 12/15 → 12/16 |

The only per-test difference in any variant is the added identity test, plus the wrapper's Phase 3 "all passed" item (`test_phase_3`), which flips from passed to failed. The other 131 original items keep their v1 outcome. Scores are partial because the overlay implements Target 3 only, not the whole task.

**Score compatibility.** v1 and v2 scores are identical when Phase 3 is fully passed or fully failed. When Phase 3 is partially passed they are not comparable, because the phase has 16 tests instead of 15 and a non-perfect phase yields a different fraction.

## Limits and what was not run

- No model or solver re-runs. Effects are shown on authored controls and counterexamples only.
- The overlay is a minimal Target 3 implementation written by the reviewer, not a complete task solution, so absolute scores are partial.
- No historical submissions were examined, so how often real solvers write wrapper decorators is unknown.
- `TODO.md` came from the earlier cloud export and was not re-extracted from the pinned work image.
- The hidden tests are not stored in this repository. They are extracted from the pinned judge image at rerun time.

## Reproduce

1. Run `evidence/scripts/schemathesis_config_modernization/fetch_tests.sh`. It extracts the hidden tests from the pinned judge image and applies the patch.
2. Run `evidence/scripts/schemathesis_config_modernization/run_in_judge.sh` with `metrics_base.py`. The saved output is `observed_output.txt`.

The paired v1/v2 run is `repairs/schemathesis_config_modernization-v2/paired/run.sh`, with results in `paired/results.md` and `paired/raw-summary.md`. The repair itself is in `repairs/schemathesis_config_modernization-v2/repair.patch`, `Dockerfile` and `source-lock.json`.

Supporting records: `repairs/schemathesis_config_modernization-v2/` and `evidence/reviews/schemathesis_config_modernization.md`.

