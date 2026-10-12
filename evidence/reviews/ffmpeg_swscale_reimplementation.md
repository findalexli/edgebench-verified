# ffmpeg_swscale_reimplementation: critical re-verification

## Claim under review

Earlier finding (`docs/FINDINGS.md`, "FFmpeg Scaling"; `evidence/selected/12-finding-decisions.json`,
decision `CONFIRMED_SOURCE_LOCAL`):

> "A recovered timing component can report a positive speed ratio even when a timed call fails or
> produces no output. Separate correctness checks were not bypassed; real score gain is unproved."

Decisive versioned claim: "Recovered FFmpeg benchmark_workloads can assign a positive timing ratio
to an API-error or no-output mock without validating timed returns or output pixels." TASKS.md
row: "Review pending … Held; no follow-up."

Question for this review: can an **honest** implementation that has bugs, or that has not yet
implemented a required path, get speed credit it should not get? How do speed and correctness
combine in the score?

## Pinned artifacts

- Task: `tasks/ffmpeg_swscale_reimplementation.json` (sha256 671c78a1…). Rescale is `log_anchor`,
  anchor_raw 14.155, anchor_score 43. In `sforge/harness/score_rescale.py:110-114` that is
  `43·ln(raw)/ln(14.155)`, and 0 when raw ≤ 1.
- Judge image `seededge/edgebench.judge.ffmpeg_swscale_reimplementation@sha256:38b256686afe14f6cec76790a7e884eb46ac70eb918a60351942a9c35c0f879f`
  (pulled and run locally).
- Work image `seededge/edgebench.work.ffmpeg_swscale_reimplementation@sha256:01a8e92ac4f389baa8ef496236599179e9de4e8bc3a30f51dee559e5ca0abdb5`
  (the shipped Rust scaffold `/home/workspace/swscale-impl` came from here: `src/lib.rs` sha256 061025fe…,
  `Cargo.toml` a32cfb2b…).
- Judge files, sha256 checked inside the image: `/opt/tests/compute_reward.py` 2f457ffd…,
  `test.sh` 3b4e836f…, `pixel_formats.py` 32aeb2c8…, `pytest_shim.sh` 6e38e136…,
  `/verifier-data/libswscale_baseline.so` d48dee3a… (matches `baseline_hash.txt`).

## Contract

From the prompt (`agent_query`):

- "Your library must handle conversions between any pair of these formats" (10 formats). It must
  support all three algorithms.
- "If correctness fails on any hidden workload, the score is **zero**."
- `reward = geometric_mean(baseline_time / candidate_time)`, applied only when correctness passes.
- The prompt says the scaffold "already matches the hidden correctness suite at 30/30". An earlier
  section of the same prompt says it is "the verified best run-005 candidate, which reached 26/30"
  and lists four failures. These two statements contradict each other.

## How the score is computed (`compute_reward.py`)

1. `sample_correctness_workloads` produces 30 fixed workloads: 23 same-size conversions at
   800x600, 1280x720, 720x576 or 352x288, plus 7 scaling cases. The candidate's output is checked
   against the baseline using per-plane PSNR (≥ 60 dB for conversion, ≥ 40 dB for scaling). Any
   failure sets the score to 0.
2. `sample_benchmark_workloads` produces 10 **different** timed workloads. In
   `benchmark_workloads`, each library runs `swscale_process` 10 + 100 times and the median time is
   used. The **return value is ignored and the output buffer is never read**. The workload's
   speedup is `base_time / max(cand_time, 1e-15)` and the score is the geometric mean of the 10
   speedups.
3. The timed set contains configurations that the correctness set never checks:
   - `rgb24→bgra` and `rgba→rgb24`: these format pairs are absent from the correctness set.
   - 3:1 downscales (`1080p→360p` bilinear to yuv420p, and nearest): the correctness set has only
     2:1 and 4:3 ratios.
   - 1.5x bicubic: the correctness set has only 2x.
   - 1080p and 4K sizes: the correctness set uses smaller sizes.

## Independent reproduction (original judge path)

`scripts/ffmpeg_swscale_reimplementation/make_variants.py` builds 4 submissions from the shipped
scaffold. Each variant adds one line to `swscale_process`. `run_variant.sh` runs the task's
**exact `eval_cmd`** (saved verbatim as `eval_cmd.sh`) in the pinned judge image with
`--network none --memory 2g --cpus 2`. That covers the real `test.sh`, the source scan, the
`cargo build --release` rebuild, `compute_reward.py` and `pytest_shim.sh`. Outputs are in
`results_local/<variant>/{reward.json,stdout.txt,stderr.txt}`.

| Variant (honest behaviour modelled) | Correctness | Raw score | Normalized (log_anchor) | Workload driving the change |
|---|---|---|---|---|
| v0 shipped scaffold, unchanged | 30/30 | 0.4585 | 0 | n/a |
| v1 returns error -3 for RGBA→RGB24 ("not implemented yet") | 30/30 | **1.3938** | **5.39** | rgba→rgb24 4K: 16,469× |
| v2 returns error -3 for 3:1 downscale | 30/30 | **3.2112** | **18.93** | 3:1 bilinear 23,856×, 3:1 nearest 7,032× |
| v3 returns success but writes nothing for 3:1 downscale | 30/30 | **3.0083** | **17.87** | 23,864× / 4,467× |

The four variants were run in sequence on one local host, and timings vary by about ±20% from run
to run. These shifts are 3 to 7× in raw score, far larger than that noise.

**The shipped scaffold already gets credit for wrong output.**
`scripts/ffmpeg_swscale_reimplementation/check_bench_outputs.py` applies the original
`check_correctness` routine (same PSNR thresholds, same RNG sequence) to the 10 timed workloads.
The unchanged scaffold fails `rgb24 1080p→360p nearest` with **PSNR 14.91 dB against the 40 dB
threshold** (`bench_outputs_v0_scaffold.txt`). That workload gives the scaffold its largest speedup,
4.65×, which multiplies the geometric mean by 4.65^0.1 = 1.166. If the timed workloads were held to
the task's own rule ("correctness fails on any hidden workload → zero"), the scaffold would score 0.
In practice its wrong output is rewarded. The scaffold's nearest-neighbour path matches FFmpeg only
for the 2:1 ratio in the correctness set (720x576→360x288, PSNR inf).

## Refutation attempts

- *Is returning an error code an honest behaviour?* Yes. The API returns `int`, the scaffold already
  returns -1/-2 on bad arguments, and the prompt says nothing about how errors are scored.
  Returning an error for a path that has not been written yet is a normal incremental-development
  state. v3 (success code, nothing written) is an ordinary bug. Neither variant inspects the
  scorer.
- *Is the trigger reachable only with a contrived fixture?* No. The real shipped scaffold triggers
  it unmodified (the 14.91 dB 3:1 nearest output).
- *Do the 30 correctness workloads catch it?* No. They do not cover the timed format pairs, sizes or
  ratios. The earlier statement "Separate correctness checks were not bypassed" is literally true,
  but it misleads: the correctness checks never touch the configurations being timed.
- *Is the effect within noise?* No. One error-returning workload contributes a factor of
  about 16,000^0.1 ≈ 2.6 to the geometric mean.
- *Does a crash get credit?* A Python exception or a NULL context gives that workload 0 (with a
  1e-15 floor, which makes the geometric mean about 0.03× the honest value). A segfault inside
  ctypes kills the scorer and `test.sh` writes reward 0. Crashes are therefore penalized. Error
  returns and silent no-ops are rewarded.

## Formal check

None needed. The behaviour follows from about 20 lines of `benchmark_workloads`, and the native runs
show it directly.

## Verdict

**CONFIRMED (broader than stated; score gain now demonstrated).** The earlier statement "real score
gain is unproved" is now refuted. Honest-but-incomplete variants raise the normalized score from 0
to 5.4 to 18.9 points, and the unchanged shipped scaffold already collects speed credit on a timed
workload where its output fails the task's own PSNR threshold.

## Disposition assessment

Earlier: held, no disposition. Recommended: **withhold the original; repair as v2.** Under the
current scorer, the ranking of honest submissions depends on which unchecked paths are missing or
wrong, and the score rewards that. The prompt also contradicts itself (26/30 vs 30/30), but that is
minor next to the scoring problem.

## Recommended publishable wording

"The timed benchmark ignores `swscale_process` return codes and never checks the timed output. Ten
timed configurations (including RGBA→RGB24, RGB24→BGRA and 3:1 downscales) are never
correctness-checked. In the original judge, an otherwise unchanged starter that returns an error for
RGBA→RGB24 rises from 0 to 5.4 normalized points (raw 0.46→1.39), and the shipped starter already
earns its largest speedup on a 3:1 downscale whose output fails the task's 40 dB threshold."

## Repair note

The earlier record did not propose a concrete patch. The smallest correct fix:

1. In `benchmark_workloads`, require `swscale_process(...) == 0` on every timed call (or at least on
   the warm-up call). After timing, run the same PSNR comparison as `check_correctness` on the
   candidate's output against the baseline's output for that workload. On failure, either zero the
   score, as the prompt promises, or give that workload speedup 0.
2. Optionally, add the 10 benchmark configurations to the correctness set.
3. Remove the stale "26/30 … four remaining failures" section of the prompt.

The anchor (14.155 → 43) must be re-derived after the repair, because published scores obtained
with unvalidated timing may be inflated.

## Limits

- Timings are from one local WSL host with 2 CPUs. Absolute speedups are host-dependent, but the
  3 to 7× raw shifts are not noise.
- Only one shipped scaffold and four one-line variants were tested. No independent full
  implementation was built.
- Scorer isolation (`compute_reward.py` imports `pixel_formats` from `/app`, the submission
  directory) is out of scope under the good-faith rule and was not analysed.
