# Paired results: ffmpeg_swscale_reimplementation v1 vs v2

E2B job `e2b/jobs/ffmpeg_swscale_reimplementation-v2-paired-b` (exit 0, worker killed; first attempt
lost in a host restart). Original scorer path, `--network none`; v1 = pinned judge image; v2 = image
built from this package's Dockerfile. Scores are raw geometric-mean speedups as reported by the scorer (before the task's rescale).

| Submission | Role | v1 score | v2 score | v2 note |
| --- | --- | --- | --- | --- |
| reference implementation (run 1) | valid | 0.967353 | 0.980056 | 30/30, no timed errors |
| reference implementation (run 2) | valid | 0.509049 | 0.507032 | 30/30, no timed errors |
| shipped scaffold | baseline | 0.447819 | 0.012416 | its 1080p→360p nearest output is below 40 dB |
| errors on 3:1 downscale | **trigger** | **2.881761** | **0.000464** | two timed workloads return -3 |
| silent no-op on 3:1 downscale | **trigger** | **2.884506** | **0.000463** | two timed outputs below 40 dB |
| errors on RGBA→RGB24 | **trigger** | **1.305860** | **0.000451** | timed error + PSNR failure |
| unsupported yuv420p→rgb24 | invalid | 0.0 (28/30) | 0.0 (28/30) | correctness gate fails in both |

**Verdict: accepted.** Wrong or missing timed output no longer earns speed credit; correct
implementations keep their scores within timing noise; the invalid control is rejected in both.
The scaffold's drop is correct: its output on one timed workload is genuinely wrong.
