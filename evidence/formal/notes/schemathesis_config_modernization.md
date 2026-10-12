# schemathesis_config_modernization: formal note

## Claim

The published score effects of the fix are exact: identity 0, wrapper −1/160, no_register −1/200.
A Phase 3 that is fully passed or fully failed scores the same in both versions; a partly passed
one does not.

## Model and link to the code

`lean/ebv/Ebv/SchemathesisTests.lean` (config section). It models the reward formula of `/tests/test.sh`
(fixed sha256 `0fd4de0a…`; the only change is l.19/l.98, 15 → 16): `weights = [3,1,1,2,2,1]`,
`sum(w·p/t)/sum(w)`. The added test (`test_03_metric_system.py` sha256 `27d75425…`, l.190-198) is
`assert metric(f) is f`.

## Result: proved (score arithmetic); the test logic is not formalized

`cfg_identity`, `cfg_wrapper` and `cfg_no_register` give 0, 1/160 and 1/200, matching the published
differences of the 6-decimal rewards. `cfg_full_or_none` proves the compatibility statement.

The added test is an object-identity check. A Lean model would only restate `metric(f) is f`, so
it is not formalized. Whether a wrapper fails it is an observed result.

## Counter-check

`cfg_partial_differs`: 12/15 ≠ 12/16, so partly passed phases are not comparable, as published.

## Limits

- Only the Phase 3 term is modelled. The other five terms are assumed identical, which the paired
  run observed for every variant.
- The pytest-output parsing in `test.sh` (grep counts) is not modelled.
