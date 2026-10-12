# schemathesis_datagen_pipeline: formal note

## Claim

On every string the fixed regex parses, the fixed `is_imf_fixdate` accepts exactly the valid
IMF-fixdates: a real Gregorian date with year ≥ 1, the matching weekday, hour 00-23, minute 00-59,
and second 00-59 or a leap second at 23:59:60. The original shape regex accepts nonsense.

## Model and link to the code

`lean/ebv/Ebv/DatagenHttpDate.lean`, core Lean only:

- original test sha256 `f2bf937f…`, l.33 and l.64-68;
- fixed test sha256 `07848bce…`, l.34-65;
- Python 3.11.15 `calendar.monthrange` / `calendar.weekday` (`_ymd2ord`) from the image, transcribed.

The specification is written independently: month lengths by the "thirty days" rule, the
Gregorian leap rule as a Prop, and the weekday by Zeller's congruence, not by counting days.

## Result: proved

- `pyWeekday_eq_zeller`: Python's day-count weekday equals Zeller's for every year ≥ 1, month and day.
- `dim_eq_monthLen`: `monthrange` gives the Gregorian month length.
- `fixedAccepts_iff_spec`: the fixed check is equivalent to the specification for all field values.
- Differential check: `witnesses_agree` reproduces all 8 rows of
  `evidence/scripts/schemathesis_datagen_pipeline/observed_witnesses.txt` for both the original and
  the fixed check. A cross-check in the judge image compared the transcribed formulas and Zeller
  with the real `calendar.weekday` / `monthrange` over every date in years 1-9999: 3,652,059 dates,
  0 mismatches.
- `SchemathesisTests.lean` `datagen_delta`: the published −2/195 is exact. It matches
  0.477350 − 0.467094 to within 1e-6.

## Counter-check

`orig_accepts_garbage`: the original shape check accepts "Abc, 99 Xyz 0000 99:99:99 GMT", and the
fixed regex has no parse for it. `apr31_not_spec`: 31 April 2023 is not in the specification.

## Limits

- The regex step is modelled by a hand-written position parser (`fixedParse`), checked on the
  witnesses only; Python's `re` engine is not formalized.
- The original `\w`/`\d` are modelled as ASCII. Python's are Unicode-wider, so the real original is
  even more permissive.
- The year floor (≥ 1) and "leap second only at 23:59" are the fix's documented choices; leap-second
  occurrence tables are not checked.
- Hypothesis sampling (200 examples) is not modelled: the proof is about the predicate, not about
  detection probability.
