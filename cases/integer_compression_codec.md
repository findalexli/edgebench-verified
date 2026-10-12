# Integer compression codec (`integer_compression_codec`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Systems & Software Engineering
- **Decision:** Repair v2. The grader normalizes against stored baseline numbers that the documented Varint starter cannot produce. As a result, the starter scores about 0.24 instead of the documented 1.0, and the effective dataset weights differ from the published ones.

## What the task promises

The solver is asked to "Implement a stronger `libintcompress.so` … to improve both compression ratio and decode throughput on the provided datasets". The agent-facing `problem.md` in the judge image defines the per-dataset score relative to "the baseline (official Varint) compressed bits-per-integer and decoding throughput": `S_i = min(B_i^0 / B_i, 8.0) × min(T_i / T_i^0, 40.0)`. `scoring_scheme.md` states: "The baseline implementation is the publicly provided Varint starter. Its composite score is defined as `1.0`."

## What we checked and how

- **Original judge path.** We ran the original `eval_cmd` (`python3 runner_judge.py`) in the pinned judge image on an E2B worker (8 vCPU Xeon @ 2.6 GHz, 7 GB), with `--network none --cpus 4 --memory 6g`. Three submissions were used: the unchanged starter (run twice), the starter with one corrupted value, and an honest delta + zigzag + varint codec.
- **Offline rescore.** We rescored the run logs under the documented definition, with the starter measured on the same host as the baseline (`rescore_documented.py`).
- **Data regeneration.** Running `gen_data.py --full` inside the image regenerated all 8 shipped data files byte for byte.
- **Bound by construction.** A byte-oriented varint needs at least one byte per value, so it always uses at least 8 bits per integer. No formal tool was needed.
- **Paired v1/v2 run.** On one E2B worker, v1 and v2 arms were alternated for the same submission, one container at a time.
- **Original identity.**
  - Judge image: `seededge/edgebench.judge.integer_compression_codec@sha256:15dffad0…89ac`.
  - Key files: `runner_judge.py` sha256 `97bf3d52…`; `internal/baseline/baseline_results.json` sha256 `216173cc…`; starter `src/codec.cpp` sha256 `92703e4b…`.
  - Work image: `@sha256:b6a58b1a…`.

## What we found

**Confirmed, a new good-faith defect.** `runner_judge.py` never measures the baseline. It reads `B_i^0` and `T_i^0` from the stored `baseline_results.json`, labelled "varint-v1 (reference)", and those values cannot come from the shipped starter.

| dataset | starter bpi (measured) | stored "Varint" bpi | stored / measured |
|---|---|---|---|
| docids | 38.98 | 5.13 | 0.132 |
| ts_sec | 40.00 | 4.86 | 0.121 |
| ts_ns | 39.48 | 8.11 | 0.205 |
| temp | 16.00 | 4.27 | 0.267 |
| grid | 39.50 | 17.54 | 0.444 |
| zipf | 12.63 | 7.32 | 0.580 |
| rand | 39.50 | 32.10 | 0.813 |
| sparse | 38.59 | 6.89 | 0.179 |

Five of the stored "Varint" values are below 8 bits per integer, which no byte varint can reach. The stored run log is also internally inconsistent: for docids, the decode time and the throughput disagree by about 1000×. The stored throughputs come from another host.

Results under the original evaluator:

| Submission | Expected (documented) | Observed (original grader) |
|---|---|---|
| unchanged Varint starter | 1.0 | 0.2407 and 0.2455 (two runs) |
| honest delta + zigzag + varint | 6.237 | 0.7590 |
| starter with one corrupted value | 0 | 0.0 (roundtrip mismatch on all 8 datasets) |

**Effect on scores.** Every absolute score is off the documented scale: the starter gets 0.24 instead of 1.0, and the honest codec 0.76 instead of 6.24. The per-dataset distortion ranges from 0.12 to 0.81, so the effective dataset weights differ from the documented weights by up to 6.7× relative to one another. Solutions that trade compression between datasets can therefore rank differently than the documentation implies. Within a single dataset the score is still monotone in compression and speed. The speed term divides a local measurement by a constant from another host, so scores also depend on the scoring host.

**What is valid.** The data regenerate exactly, and the roundtrip gate works: a corrupting codec scores 0. An early truncated listing suggested that two data files were missing. A full listing with hashes ruled that out. Two minor deviations were judged immaterial for honest solvers. The image ships g++ 11.4 instead of the documented 12.2, and "encode + decode ≤ 300 s" is enforced as two separate 300 s limits.

**Earlier record re-checked.** The earlier entry ("metadata/arithmetic controls only", held) was not a disposition review. It neither found nor ruled out this defect.

## Repair

v2 implements the documented definition: the grader measures the shipped starter in the same run and uses it as the baseline. After the submission builds and passes the symbol check, `runner_judge.py` builds the starter from pristine copies with the shipped Makefile, so the compiler and flags are the same. On each dataset, the starter and the submission then run back to back through the same `runner_encode` and `runner_decode`. The starter's measured bpi and decode throughput become `B_i^0` and `T_i^0`.

The repair has these parts:

- Three pristine starter files are added under `internal/baseline/starter/`. They are byte-identical to the solver-visible starter.
- The stored `baseline_results.json` is no longer read.
- If the starter itself fails to build or roundtrip, the run reports an error instead of a score.
- Nothing else changes: the formula, caps (8×, 40×), weights, datasets, roundtrip gate, rescale (linear 0..100), work image and solver-visible text all stay as they were. In the task JSON, only `judge.image_tag` changes.

| Arm | Submission | v1 raw / norm | v2 raw / norm | Pass v1 / v2 | Exit v1 / v2 | Expected | OK |
|---|---|---|---|---|---|---|---|
| Trigger / valid control | shipped Varint starter (unchanged) | **0.2327 / 0.2327** | **0.9786 / 0.9786** (repeat **1.0155**) | 8/8 / 8/8 | 0 / 0 | v1 ≠ 1.0, v2 ≈ 1.0 (documented) | yes |
| Honest control | delta + zigzag + varint | **0.8253 / 0.8253** | **6.7024 / 6.7024** (repeat **6.9708**) | 8/8 / 8/8 | 0 / 0 | v2 = documented definition (offline rescore of the v1 logs against the v1 starter run: 7.43; earlier review: 6.24) | yes |
| Invalid control | starter with one corrupted value | **0 / 0** | **0 / 0** | 0/8 / 0/8 (`roundtrip mismatch`) | 0 / 0 | 0 in both | yes |

Under v2 the starter's compression ratio is exactly 1.0 on every dataset, and its per-dataset speed ratios range from 0.93 to 1.07. The residual from 1.0 is timing noise. The honest codec's compression terms are exact; for example, ts_sec is 40.00 / 8.00 bpi = 5.0×. The v1 values in this table come from a different run than the review's original-evaluator values[^2]. v2 adds about 20 s per evaluation (44 s instead of 24 s wall time). The repair was accepted.

**Score compatibility.** v2 scores are not comparable with v1 scores for any submission. Each per-dataset score changes by the ratio of the measured starter to the stored constants. On the E2B worker that ratio ranged from about 1.5× (rand) to about 12× (ts_sec), so rankings between solutions that trade off across datasets can change. Failing submissions still score 0. The rescale is kept. Re-anchoring it, for example with the starter at 0, is a separate benchmark-policy decision and is not part of this repair.

## Limits and what was not run

- No model or solver re-runs. Effects are shown only on authored controls (the starter, a simple honest codec and a corrupting codec) and counterexamples.
- **Host dependence and noise remain.** The speed term is now a same-host wall-clock ratio. Two v2 runs on one worker gave 0.979 and 1.016 for the starter, and 6.70 and 6.97 for the honest codec. The starter's own throughput moved by up to 15% between runs, although back-to-back pairing cancels most of that.
- The baseline is measured once per dataset (best of 5 decodes). Medians over several baseline runs were not used.
- Only one E2B host was used. The honest control is a simple codec, not a strong solution. No expert reference solution is shipped.
- The image still has g++ 11.4, not the documented 12.2. This is unchanged and affects both versions equally.

## Reproduce

- Offline rescore under the documented definition: `evidence/scripts/integer_compression_codec/rescore_documented.py` (output in `rescore_output.txt`).
- Paired v1/v2 run: `repairs/integer_compression_codec-v2/paired/run.sh`. Summarize with `paired/summarize.py`. Results are in `paired/results.md`, and evidence (logs, file hashes, `summary.txt`) is in `paired/evidence/`.
- Repair: `repairs/integer_compression_codec-v2/repair.patch`, `Dockerfile`, `source-lock.json`.

Supporting records: `repairs/integer_compression_codec-v2/` and `evidence/reviews/integer_compression_codec.md`.


[^2]: The original-evaluator scores differ by run. The review's run gave the starter 0.2407 and 0.2455 and the honest codec 0.7590, with 6.237 under the documented definition. The paired run gave v1 values of 0.2327 and 0.8253, an offline rescore of 7.43, and v2 values of 6.7024 and 6.9708. `decisions.json` cites the rounded "starter 0.24 … honest codec 0.76 vs 6.24" for the finding and "starter 0.23→0.98/1.02" for the repair. This page reports each value with its own run and does not merge them. The differences are run-to-run and host throughput noise, as `paired/results.md` explains.
