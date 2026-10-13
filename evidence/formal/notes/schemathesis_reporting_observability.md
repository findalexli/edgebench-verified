# schemathesis_reporting_observability: formal note

## Claim

1. The original deny-case body test cannot fail, given that the coverage generator yields only
   values of the coverage module's class (observed: 12 of 12 on the starter, not proved): it filters
   on the `negative` module's class instead. The fixed test can fail, and it rejects the starter's
   behaviour.
2. The published score changes are exact: −1/70, −1/120, −1/60, +1/200 and −13/1400. So are the
   per-test weights of 1/70 (JUnit test) and 1/100 (a Phase 5 test). These weights bound the
   original's wrong credit. The largest change the fixed version can make to one submission (4.76
   points down, 2.76 up) is computed from the same weights on the case page and is not in Lean.

## Model and link to the code

`lean/ebv/Ebv/SchemathesisTests.lean` (reporting section).

- Original `test_05_email_coverage.py` sha256 `8f1831e4…`: l.98 imports the `negative` module's
  `GeneratedValue`; l.117-118 filter on it and assert the scenario is absent.
- Fixed sha256 `10401e44…`, l.95 and l.117-121.
- Reward: `test.sh` l.164 `weights = [2,2,3,2,1]`, Phase 5 10 → 12 (fixed sha256 `5f3a136b…`).

## Result: proved (vacuity and arithmetic); the JUnit fix is not formalizable usefully

`orig_vacuous`: if every value has the coverage class, the original test passes on every output,
including one that contains the forbidden scenario. The premise was observed: 12 of 12 values on the
starter. `fixed_accepts` covers correct behaviour in both the allow and the deny case. The `rep_*`
theorems match each published difference; `rep_stub_drops` checks the 6-decimal rounding.

The fixed JUnit test depends on an XML parser (`xml.etree`). Modelling it would mean formalizing XML,
and the original's substring check is trivially satisfied by plain text, so neither is formalized.

## Counter-check

`fixed_rejects`: the fixed deny test rejects a stream that contains the forbidden scenario (the
starter), the empty stream, and an always-suppress implementation in the allow case.

## Limits

- Coverage values are reduced to (class, scenario). `cover_schema_iter` is not modelled.
- The class premise is observed, not proved.
- The JUnit and query tests are not formalized beyond the score arithmetic.
