# Schemathesis data-generation pipeline, fixed version: check that HTTP dates are valid

## What this fixes

The hidden test for generated HTTP dates checks only the pattern of letters and digits, so generators that emit impossible dates, wrong weekdays or clock times like 24:00 still pass. The fixed test checks real calendar dates, matching weekdays and valid clock times. The gap is worth 1/15 of Phase 1, about 1% of the score.

## What changes

### The problem in detail

See the [review](../../evidence/reviews/schemathesis_datagen_pipeline.md). `test_http_date_values_grammar` checks only the shape, using `^\w{3}, \d{2} \w{3} \d{4} \d{2}:\d{2}:\d{2} GMT$`. Generators that emit impossible dates (31 Apr, a wrong weekday), clock times out of range (24:00) or tokens that are not month names pass. This contradicts `TODO.md`'s "valid HTTP-date values" and RFC 9110 §5.6.7 / RFC 5322 §3.3. The gap is 1/15 of Phase 1, about 1% of the score.

### Exact change

One file, `/tests/test_01_header_strategies.py`:
1. The accepted fixed check `is_imf_fixdate` from `proposedrepairs/datagen-http-date/repair.patch` (the "V2 predicate" there). It checks the IMF-fixdate grammar, the Gregorian date, agreement of the weekday, clock bounds and a year that can be represented (≥ 1), and allows `:60` only at 23:59.
2. New in this package, as the review suggested: that one test's `max_examples` goes from 50 to 200. Rare clock defects (hour 24) were caught in only 15/20 random seeds at 50; at 200 they were caught in 20/20.

The number of tests, `test.sh`, the weights and the parser are unchanged. `task.json.in` changes only `judge.image_tag` (`c4be4b8d9369` → `http-date-v2`).

**Resolved (coordinator, 2026-10-12):** the RFC 5322 floor of year ≥ 1900 was removed, because the task does not state it; the check now requires year ≥ 1. The re-run (the amendment in results.md) shows that every honest generator, including one that covers the full range of years, keeps its score.

### Are scores comparable?

Scores from the fixed version are not comparable with the original for submissions whose `http_date_values` emits invalid dates. Those lose 1/15 of Phase 1 (−2/195 of the total). All other submissions score identically.

## How it was checked

Side-by-side run of the original and fixed graders: [paired/results.md](paired/results.md). Both honest generators keep their score, and a run over 20 random seeds found no honest generator wrongly rejected. Both plausible but wrong generators, and a garbage test submission that only has the right shape, lose exactly 1/15 of Phase 1.

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t ebv/schemathesis_datagen_pipeline-judge:v2 .
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

- The generator is the reviewer's minimal overlay for Target 1, and no upstream reference generator was available.
- Whether a leap second actually occurred is not checked.
- The original task and images are untouched.
