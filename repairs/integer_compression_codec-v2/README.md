# Integer compression codec, fixed version: the baseline is the shipped Varint starter, measured in the same run

## What this fixes

The task documents say a submission is scored against the supplied Varint starter, which should score 1.0. The original grader instead divides by stored numbers that the starter cannot produce, so the starter scores about 0.24 and the datasets are weighted differently from what is published. The fixed grader measures the starter in the same run and uses it as the baseline, exactly as documented.

## What changes

### The problem in detail

See the [review](../../evidence/reviews/integer_compression_codec.md). The documents the agent sees define
the score on each dataset relative to "the baseline (official Varint)" and state in `scoring_scheme.md`:
"The baseline implementation is the publicly provided Varint starter. Its composite score is
defined as `1.0`." The grader (`runner_judge.py`) instead divides by constants stored in
`internal/baseline/baseline_results.json`. Those constants cannot come from the starter. Five of
the stored "Varint" bits-per-integer values are below 8, which no byte-oriented varint can reach (it needs at least one byte, 8 bits, per value).
The stored throughputs come from another machine. On the grading path the unchanged starter
therefore scores about 0.24 instead of 1.0. The compression terms alone are off by up to 6.7x relative to one another; with the speed term,
the starter's per-dataset scores (all 1.0 by definition) span 0.078 to 0.647 in the paired run, so the
effective weights of the datasets differ from the published weights by about 7–9x relative to one another.

### Exact change

One file is changed and three pristine files are added in the grader image
(`repair.patch`, generated with `diff -ruN`):
- `runner_judge.py`: after the submission builds and passes the symbol check, the grader builds the
  shipped starter from pristine copies into `.judge-bin/starter/` (`make -j4 libintcompress.so`, with
  the shipped Makefile, so the compiler and flags are the same). On each dataset it then runs the starter and
  the submission back to back through the same `runner_encode` / `runner_decode`. The starter's
  measured bpi (bits per integer) and `decode_gbps` are used as `B_i^0` and `T_i^0`. `load_baseline()` and the read of
  `baseline_results.json` are removed. The file is left in the image but is no longer read. The
  output also reports `baseline_per_dataset` and `baseline_source`. If the starter itself
  fails to build or to pass the roundtrip check, the run reports `status=error` rather than a score.
- `internal/baseline/starter/{codec.cpp,intcompress.h,Makefile}`: byte-identical copies of the
  shipped `src/codec.cpp`, `include/intcompress.h` and `Makefile`. These are the same files as in
  the work image the solver sees (`b6a58b1a…`, checked on the cloud worker; `paired/evidence/work_sha.txt`).
  Copies are needed because the submission overwrites `src/`, `include/` and `Makefile`.
- `task.json.in` changes `judge.image_tag` and the score scale. The scale becomes linear from 1.0
  (the documented score of the starter) to 320 (the largest possible result, 8 x 40), so the starter
  scores 0 and a perfect codec 100. Both end points are exact quantities of the documented formula.
  The `eval_cmd`, the parser, the caps (8x, 40x), the weights, the datasets, the roundtrip check and
  the work image are unchanged.

### Why this is the smallest change

The scoring formula, caps, weights and checks stay exactly as documented. Only the
source of `B_i^0` and `T_i^0` changes: from stored constants to the documented starter, measured by
the same runners on the same machine in the same container. This is the documented definition, so no
text the solver sees changes. Measuring each dataset immediately before the submission keeps the two
timings under the same conditions. The cost is roughly 20 s more per grading on the E2B cloud worker
(about 44 s instead of 24 s).

### Are scores comparable?

Scores from the fixed version are **not comparable** with scores from the original for any submission. For
every submission, each per-dataset score changes by the factor
`(starter_bpi_measured / stored_bpi) x (stored_gbps / starter_gbps_measured)`. On the E2B worker this factor
ranged from about 1.5x (rand) to about 13x (ts_sec) in the paired run, so rankings between solutions that trade off across datasets can
change. Failing submissions still score 0.

### Why the score scale changes

Keeping the original scale (linear 0..100) would make the fixed task useless for strong solutions. Once the
baseline is measured as documented, raw results run up to 320, and real agent submissions exceed 100: two
submissions from a public Claude Opus 5.5 run regrade to raw 114.19 and 160.76, which the original scale would
both clip to 100 (`../../evidence/runs/opus55-regrade/`). The fixed scale therefore runs from 1.0, the
documented score of the starter, to 320, the largest result the formula allows. Under it those two submissions
score 35.48 and 50.08, the starter scores 0 and the honest codec in the side-by-side test scores 1.79.

## How it was checked

Side-by-side run of the original and fixed graders: [paired/results.md](paired/results.md). The fix is **accepted**.

In plain words: the unchanged starter scores 0.2327 on the original grader and 0.9786 on the fixed one (1.0155 on a repeat), close to the documented 1.0. A simple honest codec (delta + zigzag + varint) scores 0.8253 on the original grader and 6.7024 on the fixed one (6.9708 on a repeat). A starter that corrupts one value scores 0 on both.

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t ebv/integer_compression_codec-judge:v2 .
```

`materialize.sh` takes the following steps:

1. Pull the pinned image(s) by digest, unless already present.
2. Extract the original files with `docker create` and `docker cp`. No container runs in this step.
3. Check each original against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of every file under `files/` (and `orig/`) against `source-lock.json` → `materialize.outputs`. Any mismatch fails loudly.

After that, the `Dockerfile` builds without changes. Regenerated files keep the file mode they have in the image.
See `../MATERIALIZE-CHECK.md` for how each package was verified.

`files/internal/baseline/starter/*` are new image paths whose bytes are unchanged copies of the in-image `Makefile`, `src/codec.cpp` and `include/intcompress.h`; `materialize.sh` copies them from the image.

## Limits

- **Dependence on the machine and timing noise remain.** The speed term is now a ratio of times on the same machine, so it no longer
  depends on an unknown reference machine. But it is still a wall-clock measurement. Over six runs of the fixed
  version in three separate E2B jobs, the starter scored 0.97 to 1.06 (per-dataset ratios 0.84 to 1.14) and the
  honest delta-zigzag-varint codec 6.70 to 8.27 (about ±10% around 7.42); see `data/paired-repeatability.md`. The
  starter's own measured throughput moved by up to about 18% between runs (grid 0.789 vs 0.646 GB/s),
  but running the two back to back cancels most of that. The compression term is exact and repeatable.
- The starter is measured once per dataset (best of 5 decodes, as for the submission). Taking the
  median of several baseline runs would cut noise further, at extra cost. That was not done, to keep
  the change minimal.
- The image still has g++ 11.4, not the documented 12.2. This is unchanged and affects both
  versions equally.
- Only one E2B machine type was used. The honest test submission is a simple codec, not a strong solution. No expert reference
  solution ships with the task.
