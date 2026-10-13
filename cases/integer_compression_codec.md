# Integer compression codec (`integer_compression_codec`)

**Outcome:** Fixed. <mark>The grader compares submissions against stored baseline numbers that the documented Varint starter cannot produce, so the starter scores about 0.24 instead of the documented 1.0 and the datasets are in effect weighted differently from what is published.</mark>

![Left: in one paired run the unchanged starter's raw score is 0.23 on the original grader against a documented 1.0, and 0.98 on the fixed grader (which maps it to 0 on its 0 to 100 scale). Right: for the docids dataset the stored "Varint" value is 5.13 bits per integer, below the 8-bit minimum for a whole-byte format and far from the starter's measured 38.98.](figures/integer_compression_codec.svg)

*The original grader compares against stored baseline numbers the starter cannot produce, so the starter's raw score is 0.23 instead of the documented 1.0 (0.98 on the fixed version in the same paired run); the fixed version measures the starter itself.*

## What the task asks

The solver must "Implement a stronger `libintcompress.so` … to improve both compression ratio and decode throughput on the provided datasets". There are eight datasets. The score on each dataset is defined relative to "the baseline (official Varint) compressed bits-per-integer and decoding throughput": `S_i = min(B_i^0 / B_i, 8.0) × min(T_i / T_i^0, 40.0)`. Varint is a simple format that stores each integer in whole bytes. `scoring_scheme.md` states: "The baseline implementation is the publicly provided Varint starter. Its composite score is defined as `1.0`." Category: Systems & Software Engineering.

## What goes wrong

**The baseline is never measured.** `runner_judge.py` reads `B_i^0` and `T_i^0` from a stored file, `baseline_results.json`, labelled "varint-v1 (reference)". Those values cannot come from the starter that ships with the task. In the table, bpi means bits per integer.

| Dataset | Starter bpi (measured) | Stored "Varint" bpi | Stored / measured |
|---|---|---|---|
| docids | 38.98 | 5.13 | 0.132 |
| ts_sec | 40.00 | 4.86 | 0.121 |
| ts_ns | 39.48 | 8.11 | 0.205 |
| temp | 16.00 | 4.27 | 0.267 |
| grid | 39.50 | 17.54 | 0.444 |
| zipf | 12.63 | 7.32 | 0.580 |
| rand | 39.50 | 32.10 | 0.813 |
| sparse | 38.59 | 6.89 | 0.179 |

A byte-oriented varint needs at least one byte per value, so it always uses at least 8 bits per integer. Five of the stored "Varint" values are below 8, which no byte varint can reach. The stored run log also contradicts itself: for docids, the decode time and the throughput disagree by about 1000×. The stored throughputs come from another machine.

On the original grader:

| Submission | Expected (documented) | Result on the original grader |
|---|---|---|
| unchanged Varint starter | 1.0 | 0.2407 and 0.2455 (two runs) |
| honest delta + zigzag + varint | 6.24 (one offline rescore; 6.70–8.27 on the fixed version over six runs) | 0.7590 |
| starter with one corrupted value | 0 | 0.0 (roundtrip mismatch on all 8 datasets) |

Every score is off the documented scale. The distortion differs by dataset, so the datasets are weighted differently from the documentation.

What works correctly: the data regenerate exactly, and the roundtrip check (decoding must return the original integers) rejects a codec that corrupts data. Two small deviations do not matter for honest solvers. The image ships g++ 11.4 instead of the documented 12.2. And "encode + decode ≤ 300 s" is enforced as two separate 300 s limits.

## How much it matters

- All solvers are affected. On raw results, the starter gets about 0.24 instead of 1.0, and the honest codec about 0.8 instead of about 6–8 (timing-dependent; see the table below).
- The compression term alone is distorted by a factor of 0.12 to 0.81 per dataset, up to 6.7× relative to one another. The speed term adds its own per-dataset distortion. Together, the unchanged starter's per-dataset scores on the original grader, which should all be 1.0, range from 0.078 (ts_sec) to 0.647 (rand) in the published paired run, 8.3× apart; the two repeats give 8.9× and 7.5× (`paired/evidence/summary.txt` and the `-rep2`, `-rep3` runs). So the effective weights of the datasets differ from the documented weights by about 7–9× relative to one another on the machine measured. Solutions that trade compression between datasets can rank differently than the documentation implies.
- Within a single dataset, the score still rises with better compression and speed.
- The speed term divides a local measurement by a constant from another machine, so scores also depend on the machine that grades them.

## The fix

The fixed version implements the documented definition: the grader measures the starter in the same run and uses it as the baseline. After the submission builds and passes the symbol check, `runner_judge.py` builds the starter from pristine copies with the shipped Makefile, so the compiler and flags are the same. On each dataset, the starter and the submission run back to back through the same `runner_encode` and `runner_decode`. The starter's measured bpi and decode throughput become `B_i^0` and `T_i^0`.

- Three pristine starter files are added under `internal/baseline/starter/`. They are byte-identical to the starter the solver sees.
- The stored `baseline_results.json` is no longer read.
- If the starter itself fails to build or to pass the roundtrip check, the run reports an error instead of a score.
- The score scale changes from linear 0..100 to linear 1.0..320: the starter (documented score 1.0) maps to 0 and the largest result the formula allows (8 × 40 = 320) maps to 100. Without this, real submissions saturate the scale (see "Real agent submissions" below). A correct codec that is worse than the starter (raw below 1.0) scores 0 on the fixed scale, the same as a failing submission; the unchanged starter itself scores 0.00 to 0.02 (raw 0.97 to 1.06 over six runs).
- The formula, the caps (8×, 40×), the weights, the datasets, the roundtrip check, the work image and all text the solver sees are unchanged. In the task JSON, `judge.image_tag` and the score scale change.

| Role | Submission | Original grader: raw / out of 100 | Fixed grader: raw / out of 100 | Datasets passed, original / fixed | Exit code, original / fixed | Expected | As expected |
|---|---|---|---|---|---|---|---|
| Shows the problem; also a correct test submission | shipped Varint starter (unchanged) | **0.2327 / 0.2327** | **0.9786 / 0.00** (repeat **1.0155 / 0.00**) | 8/8 / 8/8 | 0 / 0 | original ≠ 1.0, fixed ≈ 1.0 (documented) | yes |
| Honest test submission | delta + zigzag + varint | **0.8253 / 0.8253** | **6.7024 / 1.79** (repeat **6.9708 / 1.87**) | 8/8 / 8/8 | 0 / 0 | fixed = documented definition (offline rescore of the original grader's logs against its own starter run: 7.43; separate run of the original grader: 6.24) | yes |
| Invalid test submission | starter with one corrupted value | **0 / 0** | **0 / 0** | 0/8 / 0/8 (`roundtrip mismatch`) | 0 / 0 | 0 in both | yes |

Under the fixed version the starter's compression ratio is exactly 1.0 on every dataset, and its speed ratios per dataset range from 0.93 to 1.07 in this run and from 0.84 to 1.14 over all six fixed-version starter runs. The remaining distance from 1.0 is timing noise. The honest codec's compression terms are exact; for example, ts_sec is 40.00 / 8.00 bpi = 5.0×. The original-grader values in this table differ slightly from those in "What goes wrong" because the speed term varies between runs. The fixed version adds about 20 s per grading (44 s instead of 24 s of wall time).

**Are scores comparable?** Scores from the fixed version are not comparable with scores from the original for any submission. Each per-dataset score changes by the ratio of the measured starter to the stored constants. In the published paired run that ratio ranged from about 1.5× (rand, 1/0.647) to about 13× (ts_sec, 1/0.078), so rankings between solutions that trade off across datasets can change. Failing submissions still score 0. The fixed grader's scores out of 100 in the table use the fixed score scale (1.0..320), computed from the recorded raw results.

**Real agent submissions.** Two submissions from a public Claude Opus 5.5 run (16 tasks, 4 hours each, published on Hugging Face as `adafadaq/edgebench-opus-5-5-xhigh-rollouts`) were regraded with both graders on one machine. The run's best submission scores raw 66.31 on the original grader and 160.76 on the fixed one; an earlier submission scores 31.11 and 114.19. On the original 0..100 scale both fixed results would clip to 100, which is why the scale changes; on the fixed scale they score 50.08 and 35.48 (`evidence/runs/opus55-regrade/`).

## How we checked it

- **Original grader, from the public image pinned by digest.** The original `eval_cmd` (`python3 runner_judge.py`) ran in the grader image on an 8 vCPU Xeon @ 2.6 GHz, 7 GB host, with `--network none --cpus 4 --memory 6g`, on the three submissions above.
- **Offline rescore** of the run logs under the documented definition, with the starter measured on the same machine (`rescore_documented.py`).
- **Data regeneration.** `gen_data.py --full` inside the image regenerated all 8 shipped data files byte for byte.
- **Bound by construction.** The floor of 8 bits per integer for any byte varint follows directly from one byte per value; no formal tool was needed.
- **Side-by-side runs.** The original and fixed graders were alternated on the same submission, one container at a time, giving the table above. The comparison was repeated three times. The verdict never changed (starter about 1.0 and the corrupting codec 0 under the fixed version, 8/8 and 0/8 datasets passed), but timing-based scores moved by up to 25% between runs ([`data/paired-repeatability.md`](../data/paired-repeatability.md)). The paired runs used the original 0..100 scale; the fixed-scale values in the table are computed from the recorded raw results.

## Limits

- We ran no AI model. Effects are shown on three test submissions we wrote (the starter, a simple honest codec and a corrupting codec) and on two submissions from a third-party Claude Opus 5.5 run, each regraded once on one machine.
- **Dependence on the machine and timing noise remain.** The speed term is now a ratio of wall-clock times on the same machine. Over six runs of the fixed version in three separate jobs (two per job), the starter scored 0.97 to 1.06 and the honest codec 6.70 to 8.27 (about ±10% around 7.42); the original grader gave the starter 0.23 to 0.30. The starter's own throughput moved by up to about 18% between runs (grid 0.789 vs 0.646 GB/s), although running the two back to back cancels most of that.
- **Timing noise on real submissions.** In the second regrade of the third-party run (37 submissions with both graders; the top 6 three times on separate E2B workers), the same submission's raw score varied by up to ±20% between machines (for example 55.4 to 73.0 under the original grader), because decoding is timed over only a few milliseconds per dataset (about 3 to 35 ms for these submissions). This holds for both graders, comes from the grader's timing method, and is unchanged by the fix. The fix's direction is stable: every submission scores 1.7 to 4 times higher under the fixed grader (`evidence/runs/opus55-regrade2-codec-a/`, `-codec-b/`, `-reps2/`, `-reps3/`; combined in `evidence/runs/opus55-regrade2-summary/summary.json`).
- The baseline is measured once per dataset (best of 5 decodes). Medians over several baseline runs were not used.
- Only one machine type was used. The honest test submission is a simple codec, not a strong solution. No expert reference solution ships with the task.
- The image still has g++ 11.4, not the documented 12.2. This affects both versions equally.

## Reproduce

- Grader image: `sha256:15dffad0…89ac`.
- Offline rescore under the documented definition: `evidence/scripts/integer_compression_codec/rescore_documented.py` (output in `rescore_output.txt`).
- Side-by-side run of the original and fixed graders: `repairs/integer_compression_codec-v2/paired/run.sh` (`repairs/integer_compression_codec-v2/` is the folder holding the fixed version). Summarize with `paired/summarize.py`. Results are in `paired/results.md`, and logs, file hashes and `summary.txt` are in `paired/evidence/`.
- Fix: `repairs/integer_compression_codec-v2/repair.patch`, `Dockerfile`, `source-lock.json`.
- Supporting records: `repairs/integer_compression_codec-v2/` and `evidence/reviews/integer_compression_codec.md`.
