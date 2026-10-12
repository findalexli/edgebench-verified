# schemathesis_datagen_pipeline v2: HTTP-date validity check

**Defect** ([review](../../evidence/reviews/schemathesis_datagen_pipeline.md)): `test_http_date_values_grammar` checks only the shape, using `^\w{3}, \d{2} \w{3} \d{4} \d{2}:\d{2}:\d{2} GMT$`. Generators that emit impossible dates (31 Apr, a wrong weekday), out-of-range clocks (24:00) or non-month tokens pass. This contradicts `TODO.md`'s "valid HTTP-date values" and RFC 9110 §5.6.7 / RFC 5322 §3.3. The gap is 1/15 of Phase 1, about 1% of the score.

**Change:** one file, `/tests/test_01_header_strategies.py`:
1. The accepted V2 predicate `is_imf_fixdate` from `proposedrepairs/datagen-http-date/repair.patch`. It checks the IMF-fixdate grammar, the Gregorian date, weekday agreement, clock bounds, a representable year (≥ 1), and allows `:60` only at 23:59.
2. New in this package, as the review suggested: that one test's `max_examples` goes from 50 to 200. Rare clock defects (hour 24) were caught in only 15/20 seeds at 50; at 200 they were caught in 20/20.

Test count, `test.sh`, weights and parser are unchanged. `task.json.in` changes only `judge.image_tag` (`c4be4b8d9369` → `http-date-v2`).

**Score compatibility:** v2 scores are not comparable with v1 for submissions whose `http_date_values` emits invalid dates. Those lose 1/15 of Phase 1 (−2/195 of the total). All other submissions score identically.

**Paired evaluation:** [paired/results.md](paired/results.md). Both honest generators keep their score, and a 20-seed sweep found no false rejection. Both plausibly-wrong generators, and a shape-only garbage control, lose exactly 1/15 of Phase 1.

**Resolved (coordinator, 2026-10-12):** the RFC 5322 year ≥ 1900 floor was removed because the task does not state it; the predicate now requires year ≥ 1. The re-run (results.md amendment) shows every honest generator, including a full-year-range one, keeps its score.

**Limits:** the generator is the reviewer's minimal Target 1 overlay, and no upstream reference generator was available. Leap-second occurrence is not validated. The original task and images are untouched.

## Build

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
