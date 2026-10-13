# Schemathesis data-generation pipeline, fixed version: check that HTTP dates are valid

## What this fixes

The hidden test for generated HTTP dates checks only the pattern of letters and digits, so generators that emit impossible dates, wrong weekdays or clock times like 24:00 still pass. The fixed test checks real calendar dates, matching weekdays and valid clock times. The gap is worth 1/15 of Phase 1, about 1% of the score.

## What changes

### The problem in detail

See the [review](../../evidence/reviews/schemathesis_datagen_pipeline.md). `test_http_date_values_grammar` checks only the shape, using `^\w{3}, \d{2} \w{3} \d{4} \d{2}:\d{2}:\d{2} GMT$`. Generators that emit impossible dates (31 Apr, a wrong weekday), clock times out of range (24:00) or tokens that are not month names pass. This contradicts `TODO.md`'s "valid HTTP-date values" and RFC 9110 §5.6.7 / RFC 5322 §3.3. The gap is 1/15 of Phase 1, about 1% of the score.

### Exact change

One file, `/tests/test_01_header_strategies.py`:
1. The check `is_imf_fixdate`, based on `proposedrepairs/datagen-http-date/repair.patch` (the "V2 predicate" there). It checks the IMF-fixdate grammar, the Gregorian date, agreement of the weekday, clock bounds and a year ≥ 1900, and allows `:60` only at 23:59.
2. New in this package, as the review suggested: that one test's `max_examples` goes from 50 to 200. Rare clock defects (hour 24) were caught in only 15/20 random seeds at 50; at 200 they were caught in 20/20.

The number of tests, `test.sh`, the weights and the parser are unchanged. `task.json.in` changes only `judge.image_tag` (`c4be4b8d9369` → `http-date-v2.1`).

**Corrected 2026-10-13 (v2.1):** the previous removal of the year ≥ 1900 floor was incorrect. The task requests HTTP dates; [RFC 9110 §5.6.7](https://www.rfc-editor.org/rfc/rfc9110.html#section-5.6.7) imports date semantics from [RFC 5322 §3.3](https://www.rfc-editor.org/rfc/rfc5322.html#section-3.3), including this floor. A generator that emits earlier years is not a valid HTTP-date control. The v2.1 candidate restores the floor and has [paired predicate checks](paired/followup.md); the native paired task-command rerun now passes the three selected controls. See [native evidence](paired/followup.md).

### Are scores comparable?

Scores from the fixed version are not comparable with the original for submissions whose `http_date_values` emits invalid dates. Those lose 1/15 of Phase 1 (−2/195 of the total). For other submissions the test weights and aggregation are unchanged; finite Hypothesis sampling does not guarantee identical outcomes on every run.

## How it was checked

v2.1 native run: `evidence/runs/schemathesis_datagen_pipeline-v2.1-native-20261013b` (ledger `exit=0`). The image was built in the worker with `materialize.sh` and `docker build`, and the original `judge.eval_cmd` scored three controls on the original and v2.1 images: the valid `stdlib_1900` generator keeps 0.477350; the pre-1900 `stdlib_any_year` and the `garbage_shape` generators fall from 0.477350 to 0.467094. See the top of [paired/results.md](paired/results.md).

Historical v2 side-by-side run (not validation of v2.1): the rest of [paired/results.md](paired/results.md). The two historical controls keep their score in v2, and a run over 20 random seeds found no honest generator wrongly rejected. Both plausible but wrong generators, and a garbage test submission that only has the right shape, lose exactly 1/15 of Phase 1.

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`, a hand-written v2.1 diff against the pinned original) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t ebv/schemathesis_datagen_pipeline-judge:v2.1 .
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
