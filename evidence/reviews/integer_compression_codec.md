# integer_compression_codec: fresh good-faith triage

> **Note (2026-10-12).** Superseded statement: "effective dataset weights are distorted by up to
> 6.7× relative to one another". 6.7× is the compression term alone. With the speed term, the
> unchanged starter's per-dataset scores on the original grader span 0.078–0.647 in the paired run
> (8.3×; 8.9× and 7.5× in the repeats). The single-run honest-codec value 6.237 varies with timing:
> the fixed version gives 6.70–8.27 over six runs. See `cases/integer_compression_codec.md`.

## Claim under review

Earlier state (TASKS.md): "Review pending | Metadata/arithmetic controls only (L). | Held | Held; no
follow-up." The task card has no claims and lists blockers "No completed disposition review … execution
review remain incomplete." Questions for this review: what is graded, does the prompt match the grader,
and are the reference and data valid?

## Pinned artifacts

- Task `tasks/integer_compression_codec.json`: `eval_cmd` = `cd /home/workspace/integer-compression-codec
  && python3 runner_judge.py`, parser structured_json, rescale linear 0..100.
- Judge image `seededge/edgebench.judge.integer_compression_codec@sha256:15dffad066b4bd1e4844b3d3798a605c80df8e83db547998b560c28e28e989ac`
  (pulled locally and on E2B; the image id was confirmed on the worker).
- Files in the image (sha256):
  - `runner_judge.py` 97bf3d52…
  - `internal/baseline/baseline_results.json` 216173cc…
  - `evaluation_server/runner_encode.cpp` a6077e23…
  - `runner_decode.cpp` 7e508c4b…
  - `tools/gen_data.py` 1885db41…
  - starter `src/codec.cpp` 92703e4b…
  - `data/*.u32`: 8 files, for example docids e78b1ebc…, ts_sec 0002d655…, zipf 23a4fe46…
- The English agent-facing documents (`problem.md`, `scoring_scheme.md`) in the image differ from the
  Chinese cloud-export copies. The image versions are authoritative and are quoted below.
- E2B job `e2b/jobs/integer_compression_codec-native-controls/`: 8 vCPU Xeon @ 2.6 GHz, 7 GB.
  `run.sh`, the variants and `result/` are kept there.

## Contract (agent-facing, from the image)

`problem.md`:

> "Let B_i^0 and T_i^0 be the baseline (official Varint) compressed bits-per-integer and decoding
> throughput for dataset i … S_i = min(B_i^0 / B_i, 8.0) × min(T_i / T_i^0, 40.0)"

`scoring_scheme.md`:

> "The baseline implementation is the publicly provided Varint starter. Its composite score is
> defined as `1.0`."

Hard constraints are roundtrip equality, a 300 s limit per dataset, and an output buffer of at most
4·n·4 bytes. The documents state g++ 12.2.

## What the grader does

`runner_judge.py` builds with `make -j4`, checks a symbol denylist, then runs each dataset through
`runner_encode` and `runner_decode`. `runner_decode` takes the best of 5 decodes and compares the
output with the input using memcmp. The score is

  S_i = min(b.bpi / bpi_i, 8) · min(gbps_i / b.decode_gbps, 40)

where `b` is read from the **stored file** `internal/baseline/baseline_results.json`. The baseline is
never measured during scoring.

## Independent reproduction (E2B, original judge path, `--network none --cpus 4 --memory 6g`)

| Submission | Status | Score | Notes |
|---|---|---|---|
| s0 shipped Varint starter, unchanged (run twice) | ok | **0.2407 / 0.2455** | the documents promise **1.0** |
| s1 starter + one corrupted value | ok | 0.0 | all 8 datasets `roundtrip mismatch`; the gate works |
| s2 honest delta + zigzag + varint | ok | 0.7590 | documented definition gives 6.237 |

**Data validity.** `gen_data.py --full`, run inside the image, regenerates **all 8 shipped data files
byte for byte** (`result/out/regen.txt`). The data are valid and reproducible.

**The stored baseline does not come from the Varint starter**
(`scripts/integer_compression_codec/rescore_documented.py` → `rescore_output.txt`):

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

A byte-oriented varint cannot go below 8 bits per integer, but five stored "Varint" values are below
8 bits. The starter does not delta-encode, so it also cannot approach these values on the sorted
datasets. `baseline_run.log` is internally inconsistent. For docids it lists `dec_ms=327120` together
with `dec_gbps=1.22`. 400 MB at 1.22 GB/s takes 0.31 s, so dec_ms is about 1000× off. A 327 s decode
would also exceed the judge's own 300 s timeout. The stored throughputs come from a different host:
measured starter throughput on the E2B host is 0.58–1.96 GB/s against stored values of 0.89–1.35.

## Consequences for an honest solver

- The score is not the documented score. The starter scores 0.24 instead of 1.0. The honest
  delta-varint codec scores 0.76 instead of 6.24 under the documented definition, which uses the
  starter measured on the same host.
- Per-dataset factors range from 0.12 to 0.81, so the **effective dataset weights differ from the
  documented w = [2, 1.5, 1.5, 1, …]**. Compression gains on ts_sec count 0.121/0.813 ≈ 1/6.7 as much
  as gains on rand, relative to the documented weighting. Solutions that trade off between datasets
  can therefore rank differently from the documentation. Within a single dataset the score is still
  monotone in compression and speed.
- The compression cap documented as "8× Varint" is effectively 8× the stored value. On ts_sec that
  means bpi ≤ 0.61, against bpi ≤ 5.0 relative to the real starter.
- The speed term divides a throughput measured on the scoring host by a constant from another host,
  so scores are not comparable across scoring hosts. On one host the two starter runs differ by 2%.

## Refutation attempts

- *Is the score still meaningful?* Partly. The roundtrip gate is correct (s1 → 0), the data are exact,
  and per-dataset monotonicity holds. Absolute scores and cross-dataset weighting contradict the
  documents.
- *Did I misread a missing-data problem?* An early truncated `ls` suggested that two data files were
  missing. A full listing and a sha256 of all 8 files refuted this, and the regeneration matches.
- *Could the stored baseline be a different, documented "official Varint"?* The documents name the
  shipped starter explicitly, and no varint can reach bpi < 8.
- *Minor deviations:* the image has g++ 11.4, not the documented 12.2. "encode + decode ≤ 300 s" is
  implemented as two separate 300 s limits. Neither is material for honest solvers.

## Formal check

None needed. The bound "varint ≥ 8 bits per integer" holds by construction: every value needs at
least one byte.

## Verdict

**New good-faith defect CONFIRMED (natively).** The grader normalizes against stored baseline
constants that are not the Varint starter the documents name. The starter scores 0.24 instead of the
promised 1.0, effective dataset weights are distorted by up to 6.7× relative to one another, and the
speed term depends on the host. Data and the roundtrip gate are valid. The earlier entry
"metadata/arithmetic controls only" was not a review. It neither found nor ruled out this defect.

## Disposition assessment

Earlier: held, no disposition. Recommended: **repair as v2** by re-measuring the baseline on the
scoring host, or **withhold the original**. Retaining it with a note is only defensible if consumers
are told that scores are relative to undocumented constants and that cross-dataset weighting differs
from the prompt. The defect does not break per-dataset monotonicity, so this is not an
"unwinnable" class of problem.

## Recommended publishable wording

"The integer-codec grader normalizes against stored baseline numbers that the shipped Varint starter
cannot produce (for example 4.86 instead of 40.0 bits per integer on ts_sec), so the starter scores
0.24 rather than the documented 1.0, and effective dataset weights differ from the published weights.
The datasets regenerate exactly and the roundtrip check works."

## Repair note

No earlier patch exists. The smallest correct fix is to measure the shipped starter in the same judge
run (paired, same host). Run `runner_encode`/`runner_decode` on the starter once per dataset, use its
bpi and decode_gbps as B_i^0 and T_i^0, and leave the rest of the scoring unchanged. A cheaper but
host-dependent fix is to regenerate `baseline_results.json` on the scoring hardware from the actual
starter and state the host. Either way the rescale ceiling (linear 0..100) needs re-anchoring.

## Limits

- One E2B host was used, and the starter was run twice. No expert or reference codec was available:
  the reference solutions in `SPECIFICATION.md` are not shipped. The honest s2 variant is a simple
  control, not a strong solution.
