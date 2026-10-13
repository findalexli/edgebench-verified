# Review: schemathesis_config_modernization

> **Note (2026-10-12).** Superseded statements below: (1) "1/150 of the total" is the value of one test in the original 15-test Phase 3. Under the fixed version's 16-test Phase 3 a wrapper loses 1/160 (0.625 points out of 100), as measured (0.135313 → 0.129063, `repairs/schemathesis_config_modernization-v2/paired/results.md`); an identity-preserving decorator that passes only part of Phase 3 can instead gain up to 1/160. (2) The original suite has 126 tests (30+26+15+19+18+18); the 132 parser items add 6 `test_phase_N` items. (3) `evidence/selected/…` and `proposedrepairs/schemathesis-config-function-identity/` are not in this repository.

## Claim under review

> "Explicit release-policy choice: its metric phase omits the required exact returned-function identity. Reference and wrapper received equal partial scores, with no wrapper advantage. A prior reviewer preferred repair without exclusion."

Earlier disposition: **Withhold original** (`TASKS.md` row 48, `evidence/selected/config-original-exclusion.json`, decision `ADOPT_EXACT_ORIGINAL_WITHHOLDING`). Proposed repair: `proposedrepairs/schemathesis-config-function-identity/`, which adds one identity test and changes Phase 3 from 15 to 16 tests.

## Pinned artifacts

- Judge image: `seededge/edgebench.judge.schemathesis_config_modernization@sha256:ff71a766c254fc62f6ffd12d877297cb22223a0bb2190e91f95fe6b3231d519e`. I pulled it and ran it locally. `/app` is the unmodified schemathesis 3.39.16 starter, and the image contains no reference solution.
- `/tests/test_03_metric_system.py` sha256 `42bc43ff89970586a74af55e811485fcbc50ef8a26034cbd0f0c11a70c4b0eea`, read from the image. It is byte-identical to the cloud-export copy.
- `/tests/test.sh` sha256 `67f455c3b139f0a587211549fe96d0d7e7bb5ed9a06254573d0b9f4266aa9e9e`.
- `TODO.md`, from the cloud-export work tree, sha256 `f9d3cc5eb46674c6280da6e43a746c1ce3b18968cc39124d9a5b3ae979ebad89`. I did not re-extract it from the work image.
- Patched files after applying `patch.diff`: test_03 `27d75425…`, test.sh `0fd4de0a…`. Both match `manifest.json`.

## Contract

`TODO.md` Target 3, requirement 3 (line 76):

> "**`@schemathesis.metric` decorator**: Registers a metric function into a registry. Returns the function unchanged."

Line 126 uses the same wording for `@schemathesis.check`.

Scoring: `weights = [3, 1, 1, 2, 2, 1]`. Phase 3 (metrics) has weight 1 and 15 tests, and phases are scored partially. One Phase 3 test is therefore worth 1/15 × 1/10 = 1/150 of the total, or 1/160 after the repair.

## Independent reproduction

Scripts are in `evidence/scripts/schemathesis_config_modernization/`.

- `metrics_base.py` is a minimal Target 3 overlay that I wrote independently: a registry, `MetricContext`, collector and `maximize`. It has three variants for `metric`:
  - `identity`: registers the function and returns it (correct).
  - `wrapper`: registers and returns a `functools.wraps` forwarding wrapper (plausibly wrong).
  - `no_register`: returns the function without registering it (clearly wrong control).
- `run_in_judge.sh` installs the overlay into the original judge image. It then runs the original and the repaired `test_03_metric_system.py` for each variant.

Command: `docker run --rm --network none --memory 2g --cpus 2 -v $D:/ebv:ro <judge@digest> bash /ebv/run_in_judge.sh`. The output is saved in `observed_output.txt`:

```
variant=identity    tests=orig     :: 15 passed
variant=identity    tests=repaired :: 16 passed
variant=wrapper     tests=orig     :: 15 passed
variant=wrapper     tests=repaired :: 1 failed, 15 passed
variant=no_register tests=orig     :: 3 failed, 12 passed
variant=no_register tests=repaired :: 4 failed, 12 passed
```

- The original Phase 3 cannot tell an identity-preserving decorator from a forwarding wrapper. `test_metric_decorator_returns_function` only asserts `callable(another_metric)`.
- The proposed test separates them and keeps the correct variant at 16/16.
- The control that does not register is still caught by the original tests.

## Refutation attempts

- **Is the wrapper "wrong"?** Literally, yes: the spec says "Returns the function unchanged". Behaviorally, the difference is almost nil. A `functools.wraps` wrapper keeps `__name__`, so it is registered under the right name, gives the same values, and works with `MetricCollector` and `hypothesis.target`. The only observable difference is `decorated is original`, plus the presence of `__wrapped__`. I found no task-relevant behavior that a downstream consumer could get wrong because of it.
- **Does the wrong implementation gain anything?** No. The wrong and correct variants score the same, so there is no advantage over a correct solution. The only distortion is that a spec-violating solution is not docked 1/150 of the total.
- **Did the authors intend identity?** Partly. `test_06_check_system.py:46` asserts `result is my_func` for `@check`, while Phase 3 does not, so the asymmetry looks like an oversight. Even so, the omission is a coverage gap of one test item, not a mis-measurement.
- **Is the trigger reachable by a real submission?** Yes, a solver could write a wrapper decorator. It would be an unusual choice, though, because the upstream pattern and the v3 `targets.register` that solvers start from both return the function itself.

## Formal check

None. No mathematical or state uncertainty applies here.

## Verdict

**CONFIRMED (fact), but the defect is minor.** The original Phase 3 does not check the required identity. A forwarding wrapper and a correct decorator score identically, and the proposed test separates them.

## Disposition assessment

**I disagree with "withhold original".**

- The test failure here meets the narrowest definition of weakness. The wrong implementation is functionally equivalent for every purpose in this task. It gains no score over a correct implementation. The most it can be over-credited is 1/150 of the total.
- Any multi-hundred-line hidden suite has gaps like this. Withholding on this basis would set a bar that almost no task passes, and it removes the whole Config Modernization capability, worth 126 test items.
- The earlier record labels this an "explicit release-policy choice" and admits that a prior different reviewer preferred repair. In my judgment that reviewer was right.

**Recommended disposition:** retain the original with a documented note. If the release policy is "ship strengthened tests as a new version", ship the one-test repair as a versioned replacement. Either way, the task should not be counted as a "withheld because defective" finding in headline numbers.

## Recommended publishable wording

> "Phase 3 of schemathesis_config_modernization does not check that `@schemathesis.metric` returns the decorated function unchanged, so a forwarding wrapper earns the same score as a correct decorator. The gap is one test item, about 0.7% of the task score, and gives no advantage over correct solutions. We add one identity test (Phase 3: 15→16 tests) in a versioned task."

## Repair note

The proposed patch is correct and minimal. It adds one test that asserts `metric(f) is f` with cleanup, and updates the two count constants. I applied it to the image bytes, and the resulting hashes match the manifest. In the judge image, it passes the correct decorator, fails the wrapper, and leaves the clearly-wrong control failing. Optional: the existing `test_metric_decorator_returns_function` could simply be changed to assert `is` instead of adding a test. That would keep the counts at 15 but still creates a new version.

## Limits

- I used a minimal Target 3 overlay that I wrote myself, not a complete task solution. Only Phase 3 was executed, not the full `test.sh`.
- `TODO.md` was taken from the earlier cloud export rather than re-extracted from the pinned work image.
- No historical submissions were examined, so the real-world frequency of wrapper decorators is unknown.

## Rerun

Run `scripts/<task>/fetch_tests.sh` first. It extracts the hidden tests from the pinned judge image into `tests_orig/` and applies the proposed patch into `tests_repaired/`, printing the hashes above. The hidden tests themselves are not stored in this repository. Then run the `run_*.sh` scripts as shown, with `-v <scripts dir>:/ebv:ro`.
