# ffmpeg_swscale_reimplementation, fixed version

## What this fixes

The original grader times 10 workloads but never checks whether the timed calls succeeded or produced correct output. An honest but unfinished library that returns an error, or does nothing, on a timed conversion therefore finishes almost instantly and earns a huge "speedup". The fixed version checks each timed call and gives no speed credit for a failed or wrong result.

## The problem

Details are in the [review](../../evidence/reviews/ffmpeg_swscale_reimplementation.md). The score is the geometric mean of speedups over 10 timed workloads, and it is zero unless the submission passes 30 correctness workloads. But the timing loop ignores return codes and never checks the timed output. Several timed configurations are also not among the correctness workloads. An honest but incomplete implementation that errors out or does nothing on a timed configuration gets an enormous "speedup" (up to ~20,000× on one workload).

## What changes

The change is in `files/compute_reward.py`; `repair.patch` is generated from it.

- Every warmup and timed call checks its return code and output against the original FFmpeg result, using 40 dB for scaling and 60 dB for same-size conversion.
- Output buffers are cleared before each call; an incomplete implementation cannot accidentally reuse a previous frame. Clearing and validation happen outside the measured call interval.
- A failed workload forces the total raw reward to exactly zero. The historical positive floor could leave a positive overall reward when other factors were large.
- Contexts are destroyed even when validation raises an exception.

This revision is **v2.2**, with a distinct judge image tag. All-valid speedup aggregation is unchanged, but per-call checking changes execution/cache conditions and adds wall time. The valid native control finished in 43 seconds versus 38 seconds originally; this finite observation does not establish statistical timing equivalence.

## How it was checked

[Follow-up component checks](paired/followup.md) exercise the original and revised scorer functions, using deterministic library and image adapters. Correct calls retain credit; null contexts, nonzero returns, skipped writes and wrong outputs lose credit, including early and middle calls followed by a correct final call. The actual aggregation rejects one failed workload even when the other nine are 100× faster.

[Historical native paired results](paired/results.md) apply only to v2. They are preserved, but do not validate v2.2. The current v2.2 patch passed six [native paired scorer arms](paired/followup.md): the correct forwarder retained raw reward (1.056386 → 1.020061), a skipped-output control fell from 1.038559 to exactly zero despite passing 30/30 separate correctness workloads, and the always-error control stayed at zero. Forty native buffer-layout checks also passed. This follow-up invokes the full scorer directly and does not rerun the Rust submission-build path.

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t edgebench.judge.ffmpeg_swscale_reimplementation:d3c0aa3fa987-ebv-v2.2 .
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

- Every-call validation adds wall time. The first implementation exceeded a 360-second observation cap; stride-aware native copies reduced the correct-control run to 43 seconds. Approximate output can still require more PSNR computation.
- The timed set still differs from the correctness set.
- Timings depend on the host; clearing buffers also changes cache state.
