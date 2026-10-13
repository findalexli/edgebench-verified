# ffmpeg_swscale_reimplementation, fixed version

## What this fixes

The original grader times 10 workloads but never checks whether the timed calls succeeded or produced correct output. An honest but unfinished library that returns an error, or does nothing, on a timed conversion therefore finishes almost instantly and earns a huge "speedup". The fixed version checks each timed call and gives no speed credit for a failed or wrong result.

## The problem

Details are in the [review](../../evidence/reviews/ffmpeg_swscale_reimplementation.md). The score is the geometric mean of speedups over 10 timed workloads, and it is zero unless the submission passes 30 correctness workloads. But the timing loop ignores return codes and never checks the timed output. Several timed configurations are also not among the correctness workloads. An honest but incomplete implementation that errors out or does nothing on a timed configuration gets an enormous "speedup" (up to ~20,000× on one workload).

## What changes

The change is in `files/compute_reward.py`; `repair.patch` is generated from it.

- The return code of each timed call is checked.
- The timed output is compared with the output of the original FFmpeg library, using the correctness workloads' per-plane PSNR thresholds (40 dB for scaling, 60 dB for same-size conversions). The output of the last timed call of each workload is compared; the return code of every timed call is checked. PSNR is the peak signal-to-noise ratio, measured for each colour plane.
- A failing timed workload is treated exactly as the original code already treats a crashed workload: its speedup is 0, and it is kept in the mean.

Nothing else changes.

**Score compatibility:** correct implementations score as on the original grader, apart from timing noise. Implementations that produce wrong output, or no output, on a timed workload lose that credit. Scores from the fixed grader are not comparable with scores from the original grader.

## How it was checked

The side-by-side run of the original and fixed graders on the same submissions is in [paired/results.md](paired/results.md).

The fix is accepted on that run. The three test submissions that show the problem (errors on 3:1 downscale, a silent no-op on 3:1 downscale, and errors on RGBA→RGB24) scored 2.881761, 2.884506 and 1.305860 on the original grader, and 0.000464, 0.000463 and 0.000451 on the fixed grader. A correct control, a shim that forwards every call to the original library, kept its score within timing noise on both graders: 0.967353 and 0.980056 when it processes each frame once, and 0.509049 and 0.507032 when it processes each frame twice (a second, about 2× slower correct control). An invalid submission (unsupported yuv420p→rgb24) scored 0.0 (28/30) on both graders. The shipped starting code dropped from 0.447819 to 0.012416. That drop is correct: its output on one timed workload (1080p→360p nearest) is below 40 dB, so it really is wrong. All values are raw geometric-mean speedups, before conversion to the 0–100 score scale.

## Build and use

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

## Limits

- A single zero factor drives the geometric mean to ~0. This is the original convention for crashes.
- The timed set still differs from the correctness set.
- Timings depend on the host.
