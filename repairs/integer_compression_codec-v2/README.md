# integer_compression_codec v2: baseline = the shipped Varint starter, measured in the same run

**Defect** ([review](../../evidence/reviews/integer_compression_codec.md)). The agent-facing documents define
the per-dataset score relative to "the baseline (official Varint)" and state in `scoring_scheme.md`:
"The baseline implementation is the publicly provided Varint starter. Its composite score is
defined as `1.0`." The grader (`runner_judge.py`) instead divides by constants stored in
`internal/baseline/baseline_results.json`. Those constants cannot come from the starter: five of
the stored "Varint" bits-per-integer values are below 8, which no byte-oriented varint can reach,
and the stored throughputs come from another host. On the judge path the unchanged starter
therefore scores about 0.24 instead of 1.0, and the effective dataset weights differ from the
published weights by up to 6.7x relative to one another.

**Change.** One file is changed and three pristine files are added in the judge image
(`repair.patch`, generated with `diff -ruN`):
- `runner_judge.py`: after the submission builds and passes the symbol check, the grader builds the
  shipped starter from pristine copies into `.judge-bin/starter/` (`make -j4 libintcompress.so`,
  the shipped Makefile, so the same compiler and flags). On each dataset it then runs the starter and
  the submission back to back through the same `runner_encode` / `runner_decode`. The starter's
  measured bpi and `decode_gbps` are used as `B_i^0` and `T_i^0`. `load_baseline()` and the read of
  `baseline_results.json` are removed. The file is left in the image but is no longer read. The
  output additionally reports `baseline_per_dataset` and `baseline_source`. If the starter itself
  fails to build or roundtrip, the run reports `status=error` rather than a score.
- `internal/baseline/starter/{codec.cpp,intcompress.h,Makefile}`: byte-identical copies of the
  shipped `src/codec.cpp`, `include/intcompress.h` and `Makefile`. These are the same files as in
  the solver-visible work image (`b6a58b1a…`, checked on the worker; `paired/evidence/work_sha.txt`).
  Copies are needed because the submission overwrites `src/`, `include/` and `Makefile`.
- `task.json.in` changes only `judge.image_tag`. The `eval_cmd`, the parser, the rescale (linear
  0..100), the caps (8x, 40x), the weights, the datasets, the roundtrip gate and the work image are
  unchanged.

**Why minimal.** The scoring formula, caps, weights and gates stay exactly as documented. Only the
source of `B_i^0` and `T_i^0` changes, from stored constants to the documented starter measured by
the same runners on the same host in the same container. This is the documented definition, so no
solver-visible text changes. Measuring per dataset immediately before the submission keeps the two
timings under the same conditions. The cost is roughly 20 s more per evaluation on the E2B worker
(about 44 s instead of 24 s).

**Score compatibility.** v2 scores are **not comparable** with v1 scores for any submission. For
every submission each per-dataset score changes by the factor
`(starter_bpi_measured / stored_bpi) x (stored_gbps / starter_gbps_measured)`, which on the E2B worker
ranged from about 1.5x (rand) to about 12x (ts_sec), so rankings between solutions that trade off across datasets can
change. Failing submissions still score 0. The rescale (linear 0..100) is kept: a v2 score of 1.0
(the starter) normalizes to 1.0, and the maximum possible raw score is 320 (8 x 40), which is clipped
at 100 as in v1. Re-anchoring the rescale (for example with the starter at 0) is a separate
benchmark-policy decision and is not part of this repair.

**Paired evaluation:** [paired/results.md](paired/results.md). The repair is **accepted**.

**Limits.**
- **Host dependence and noise remain.** The speed term is now a same-host ratio, so it no longer
  depends on an unknown reference host, but it is still a wall-clock measurement. On one 8-vCPU E2B
  worker the starter scored 0.979 and 1.016 in two v2 runs (per-dataset ratios 0.93 to 1.07), and
  the honest delta-zigzag-varint codec scored 6.70 and 6.97 (about ±2% around the mean). The
  starter's own measured throughput moved by up to 15% between runs (docids 0.954 vs 0.826 GB/s),
  but the back-to-back pairing cancels most of that. The compression term is exact and repeatable.
- The starter is measured once per dataset (best of 5 decodes, as for the submission). Taking the
  median of several baseline runs would cut noise further, at extra cost. That was not done, to keep
  the change minimal.
- The image still has g++ 11.4, not the documented 12.2. This is unchanged and affects both
  versions equally.
- One E2B host. The honest control is a simple codec, not a strong solution. No expert reference
  solution is shipped.

## Build

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
