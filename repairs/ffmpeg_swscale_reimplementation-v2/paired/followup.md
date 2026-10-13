# v2.2 follow-up, 2026-10-13

The candidate validates every warmup/timed output and return value, clears the output buffer before each call, destroys contexts on failure, and forces zero total reward on any failed workload. Validation and buffer clearing are outside the call timer.

The cached v2 replacement was checked against its recorded hash and reverse-patched. The recovered original matched `2f457ffd67d624f9f739b4dd34b80b858a9bbb152e40e4385a8c10a81159365b`. The new diff applies to that original; source and patch hashes are locked.

`evidence/scripts/validator_followup/ffmpeg.py ORIGINAL MATERIALIZED_CANDIDATE` executes the actual original and revised `benchmark_workloads`, `compute_psnr`, and `_run_scoring` functions, with deterministic library/image adapters. Good output retains a speedup of one. Null context, nonzero return, skipped write, and incorrect frame cases are rejected; calls 1, 3, 4 and 6 cover warmup, first timed, middle and final calls. Skipped writes after valid output test the buffer reset. Cleanup is asserted for every created context.

The actual aggregation returns exactly zero for nine factors of 100 and one zero; the original returns 1.995262. Ten factors of two retain reward two. Empty, NaN and infinite factors yield zero in the candidate. Saved results: [followup-component.json](followup-component.json).

The component checks use adapters; the separate native checks below exercise the real shared-library ABI and all official scorer workloads. Buffer resets change cache state. A single paired run does not establish timing equivalence, population-level score changes or the full submission-build path.
The historical v2 native results and Lean model are retained and explicitly apply only to v2. Their positive-floor model is superseded by this candidate's exact-zero gate.

## Superseded v2.1 native attempt

The first candidate used the original pixel helpers on every call. Those helpers box/copy bytes through Python, making repeated checks expensive. The valid original scorer finished in 48 seconds (raw 0.994937), but v2.1 did not finish within the 360-second observation limit. Its container was explicitly terminated at 407 seconds after the timeout's TERM did not stop its shell/child; later arms were interrupted or not run. This is not a failure of the original task's 5,400-second budget.

The [first worker receipt](native-20261013-v2.1/worker.json) records intentional overall exit143, 683 seconds elapsed, and confirmed cleanup. The exact attempted patch, lock and component results are preserved as `followup-v2.1.*`. v2.2 replaces only benchmark buffer extraction/reset with stride-aware `ctypes.string_at` / `memset`, leaving every-call checks and timing boundaries intact. A second native job verifies equivalence against the pinned original helpers before paired scoring. It uses `exec python3`, timeout escalation and exact per-arm container cleanup.

## v2.2 native result

The original digest-pinned image and v2.2 image ran the complete `compute_reward.py` (30 correctness and 10 timed workloads), with the same authored native C controls, serial 2-CPU / 4-GiB containers and no network. All six scorer arms exited 0; the [worker](native-20261013-v2.2/worker.json) exited 0, ran for 201 seconds including setup, and was killed successfully.

| Native control | Original raw reward | v2.2 raw reward | Correctness original / v2.2 | Wall seconds original / v2.2 |
|---|---:|---:|---|---:|
| Forward every call to FFmpeg | 1.056386 | 1.020061 | 30/30 / 30/30 | 38 / 43 |
| Skip second call of each context | 1.038559 | 0.000000 | 30/30 / 30/30 | 33 / 25 |
| Always return an error | 0.000000 | 0.000000 | 0/30 / 0/30 | 3 / 2 |

The skipped-output control fails all 10 candidate timing workloads while passing the separate 30 correctness workloads. It models a repeated-call implementation defect; the skipped call is in warmup, followed by correct calls. Component tests separately cover first/middle/final timed calls. The results establish acceptance/rejection behavior on these controls, not a measured leaderboard correction. Values are raw rewards, and timing differences are not asserted statistically equivalent.

Before scoring, [40 native layouts](native-20261013-v2.2/layouts.json), covering every actual pixel-format descriptor at four dimensions including odd sizes and stride padding, matched original `image_to_bytes` byte-for-byte. Reset cleared all allocated plane bytes including padding. A separate independent synthetic oracle (`check_buffer_layouts.py`) passed 64 guarded layouts. Both check the current source hash `5d02d6809e72dda7051db12d5a113c05a61fe62f390400e3749351c13a2c06c0`.

The fast snapshot/reset resolves the observed v2.1 slowdown for the valid control: v2.2 finishes in 43 seconds, below both the 360-second observation cap and 5,400-second task limit. That is a finite runtime observation, not a universal budget guarantee. These are full scorer calls with native controls, **not** the task's Rust build/submission `eval_cmd`. No fresh model run or all-submission release certification is claimed. The original-helper equivalence and source/patch hashes bind the candidate to these results.

Reproduce after materializing the FFmpeg package with `python3 evidence/scripts/validator_followup/prepare_native.py JOB_DIRECTORY`, then the maintained `tools/e2b_run.py` with lifetime 3000 and budget 2700. The exact native recipe is `run_ffmpeg_native.sh`; every container has an owned name and explicit timeout cleanup.
