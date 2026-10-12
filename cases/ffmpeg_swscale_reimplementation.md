# FFmpeg Swscale Reimplementation (`ffmpeg_swscale_reimplementation`)

**Decision:** Repair (v2). The timed workloads were never checked for correctness, so failed or empty calls earned speed credit; v2 checks each timed call's return code and output.

## What the task asks for

The solver re-implements FFmpeg's libswscale in Zig or Rust as a C-compatible shared library. The library "must handle conversions between any pair of these formats". "If correctness fails on any hidden workload, the score is **zero**." Otherwise `reward = geometric_mean(baseline_time / candidate_time)`. The task rescales this raw score with `log_anchor` (anchor_raw 14.155, anchor_score 43); a raw score of 1 or less becomes 0. Category: Systems & Software Engineering.

## What goes wrong

**Timed workloads earn speed credit without any correctness check.** The score is computed in two stages:

- **Correctness gate.** 30 fixed workloads are compared with the baseline using per-plane PSNR: at least 60 dB for same-size conversion and at least 40 dB for scaling.
- **Timing.** 10 *different* workloads are timed. The timing loop ignores the return value of `swscale_process` and never reads the output buffer.

Several timed configurations never appear in the correctness set: RGBA→RGB24, RGB24→BGRA, 3:1 downscales, a 1.5× bicubic upscale, and 1080p and 4K sizes. A call that returns an error, or does nothing, finishes almost instantly and so gets a very large "speedup".

Each variant below models ordinary incremental development: a path that is not written yet, or a plain bug. Under the original evaluator:

| Variant (honest behaviour modelled) | Correctness | Raw score | Normalized (log_anchor) | Workload driving the change |
|---|---|---|---|---|
| v0 shipped scaffold, unchanged | 30/30 | 0.4585 | 0 | n/a |
| v1 returns error -3 for RGBA→RGB24 ("not implemented yet") | 30/30 | **1.3938** | **5.39** | rgba→rgb24 4K: 16,469× |
| v2 returns error -3 for 3:1 downscale | 30/30 | **3.2112** | **18.93** | 3:1 bilinear 23,856×, 3:1 nearest 7,032× |
| v3 returns success but writes nothing for 3:1 downscale | 30/30 | **3.0083** | **17.87** | 23,864× / 4,467× |

Example: for v1 the expected outcome is no speed credit on RGBA→RGB24, because the call fails. The original evaluator instead recorded a 16,469× speedup on that workload, raising the normalized score from 0 to 5.39. Timings vary by about ±20% from run to run; these shifts of 3 to 7× in raw score are far larger.

**The shipped scaffold is already credited for wrong output.** On the timed workload `rgb24 1080p→360p nearest`, the unchanged scaffold produces **14.91 dB PSNR, against the 40 dB threshold**. That same workload gives the scaffold its largest speedup, 4.65×.

Crashes are handled differently. A Python exception or a NULL context gives that workload 0, and a segfault makes `test.sh` write reward 0. Only error returns and silent no-ops are rewarded. The correctness workloads themselves are checked as stated; they simply never cover the configurations being timed.

Not material: the prompt says the scaffold "already matches the hidden correctness suite at 30/30", and elsewhere describes it as a candidate "which reached 26/30". The native runs measured 30/30.

## Impact

Up to 18.93 normalized points shown for an honest but incomplete variant. Any solver whose library fails or does nothing on a timed configuration outside the correctness set is over-credited.

## Fix (v2)

v2 changes only `compute_reward.py`:

- It checks the return code of each timed call.
- It compares each timed output with the baseline output, using the same 40 dB per-plane PSNR threshold as the correctness workloads.
- A failing timed workload is treated the way the original already treats a crashed workload: its speedup is 0, and it stays in the geometric mean.

Nothing else changes.

| Submission | Role | v1 score | v2 score | v2 note |
| --- | --- | --- | --- | --- |
| reference implementation (run 1) | valid | 0.967353 | 0.980056 | 30/30, no timed errors |
| reference implementation (run 2) | valid | 0.509049 | 0.507032 | 30/30, no timed errors |
| shipped scaffold | baseline | 0.447819 | 0.012416 | its 1080p→360p nearest output is below 40 dB |
| errors on 3:1 downscale | **trigger** | **2.881761** | **0.000464** | two timed workloads return -3 |
| silent no-op on 3:1 downscale | **trigger** | **2.884506** | **0.000463** | two timed outputs below 40 dB |
| errors on RGBA→RGB24 | **trigger** | **1.305860** | **0.000451** | timed error + PSNR failure |
| unsupported yuv420p→rgb24 | invalid | 0.0 (28/30) | 0.0 (28/30) | correctness gate fails in both |

The scores in this table are raw geometric-mean speedups, before the task's rescale. The "reference implementation" is a shim that forwards every call to the FFmpeg baseline library, so its output is correct by construction; run 2 processes every frame twice, which makes it correct but about 2× slower. It is a control, not a submission. This table ran on a different host from the first table, so its raw v1 values differ; both are quoted as recorded. The scaffold's drop under v2 is correct, because its output on one timed workload really is wrong.

**Score compatibility:** correct implementations score as in v1, apart from timing noise. Implementations that produce wrong output, or no output, on a timed workload lose that credit. v2 scores are not comparable with v1 scores.

## How we know

- **Original evaluator in the pinned judge image** (`sha256:38b256686afe…`). Four submissions built from the shipped Rust scaffold, each changing a single line of `swscale_process`, ran through the task's exact `eval_cmd` with `--network none --memory 2g --cpus 2`. That path covers `test.sh`, the source scan, the `cargo build --release` rebuild, `compute_reward.py` and `pytest_shim.sh`.
- **Independent output check.** The original `check_correctness` routine was applied to the 10 timed workloads, with the same PSNR thresholds and the same random-number sequence. The scorer itself never runs this check on those workloads.
- **Paired evaluation** of v1 and v2 on the same submissions with `--network none --memory 4g --cpus 4`. It was repeated three times; no arm changed verdict, and the trigger arms stayed near 0 under v2 in every run (see `paired-repeatability.md`).

## Limits

- No model or solver runs. Effects are shown only on authored controls and counterexamples.
- In v2, a single zero factor pulls the geometric mean close to 0. This follows the original convention for crashes and is not a graded penalty.
- The timed set still differs from the correctness set. v2 checks timed outputs but does not add the timed configurations to the 30 correctness workloads.
- Timings depend on the host: the first table used a host with 2 CPUs, the paired table a host with 4 CPUs.
- The rescale anchor (14.155 → 43) should be re-derived after the repair. No re-derived anchor is recorded.
- Only the shipped scaffold, three one-line variants, one invalid control and the baseline-forwarding shim were tested. No independent full implementation was built.
- Scorer isolation is outside this release's scope (EdgeBench design choice). The finding above does not depend on it.

## Reproduce

- Native variants on the original judge:
  - Build the variants with `evidence/scripts/ffmpeg_swscale_reimplementation/make_variants.py`.
  - Run them with `run_variant.sh`, which uses the verbatim `eval_cmd.sh`.
  - Outputs are in `results_local/<variant>/`.
- Output check on the timed workloads: `evidence/scripts/ffmpeg_swscale_reimplementation/check_bench_outputs.py`. The recorded outputs are `bench_outputs_v0_scaffold.txt` and `bench_outputs_v1_rgba_rgb24_unsupported.txt`.
- Paired v1/v2 evaluation: `repairs/ffmpeg_swscale_reimplementation-v2/paired/run.sh`, with `make_variants.py` and `ref_shim.c` in the same folder.
- Repair package: `repairs/ffmpeg_swscale_reimplementation-v2/`, which contains `Dockerfile`, `repair.patch`, `files/compute_reward.py` and `source-lock.json`.
- Supporting records: `repairs/ffmpeg_swscale_reimplementation-v2/paired/results.md`, the `paired/evidence/` folder and `evidence/reviews/ffmpeg_swscale_reimplementation.md`.
