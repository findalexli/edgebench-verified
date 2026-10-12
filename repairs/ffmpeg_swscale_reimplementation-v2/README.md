# ffmpeg_swscale_reimplementation v2

**Defect** ([review](../../evidence/reviews/ffmpeg_swscale_reimplementation.md)): the score is the geometric
mean of speedups over 10 timed workloads, gated by 30 correctness workloads; but the timing loop
ignores return codes and never checks the timed output, and several timed configurations are not
among the correctness workloads. An honest but incomplete implementation that errors out or does
nothing on a timed configuration gets an enormous "speedup" (up to ~20,000× on one workload).

**Change** (`files/compute_reward.py`, generated `repair.patch`): each timed call's return code is
checked and the timed output is compared with the baseline using the same per-plane PSNR
threshold (40 dB) as the correctness workloads. A failing timed workload is treated exactly as the
original code already treats a crashed workload: speedup 0, kept in the mean. Nothing else changes.

**Score compatibility:** correct implementations score as in v1 (timing noise only); implementations
that produce wrong or no output on a timed workload lose that credit. Not comparable with v1 scores.

**Limits:** a single zero factor drives the geometric mean to ~0 (the original convention for crashes);
the timed set still differs from the correctness set; timings are host-dependent.
Paired evidence: [paired/results.md](paired/results.md).

## Build

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t ebv/ffmpeg_swscale_reimplementation-judge:v2 .
```

`materialize.sh` takes the following steps:

1. Pull the pinned image(s) by digest, unless already present.
2. Extract the original files with `docker create` and `docker cp`. No container runs in this step.
3. Check each original against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of every file under `files/` (and `orig/`) against `source-lock.json` → `materialize.outputs`. Any mismatch fails loudly.

After that, the `Dockerfile` builds without changes. Regenerated files keep the file mode they have in the image.
See `../MATERIALIZE-CHECK.md` for how each package was verified.
