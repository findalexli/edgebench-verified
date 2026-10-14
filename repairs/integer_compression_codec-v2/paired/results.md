# Paired v1/v2 results: integer_compression_codec

- **Job:** one E2B worker (8 vCPU Intel Xeon @ 2.60 GHz, 7.9 GB, Docker 29.4.1), job
  `integer_compression_codec-v2-paired`. It exited 0 after 322 s and was killed after collection
  (`evidence/worker.json`).
- **Images:** v1 is the pinned `seededge/edgebench.judge.integer_compression_codec@sha256:15dffad0…89ac`.
  v2 was built in the worker from `../Dockerfile` (image ID `sha256:27aa152a…ad40`). File hashes in
  both containers are in `evidence/file_sha.txt`: `runner_judge.py` 97bf3d52… (v1) and f205adb8… (v2);
  the starter copies are identical to `src/`, `include/` and `Makefile`. The work image's starter files
  are identical too (`evidence/work_sha.txt`).
- **Command:** every arm ran the original `eval_cmd`
  `cd /home/workspace/integer-compression-codec && python3 runner_judge.py`, with
  `--network none --cpus 4 --memory 6g`, one container at a time. Arms alternate v1 and v2 for the
  same submission. The variant `codec.cpp` was copied over `src/codec.cpp` (variants reused from
  `evidence/runs/integer_compression_codec-native-controls/`; hashes in `evidence/variants_sha.txt`).
- **Scores:** raw = structured-result `score`. Normalized = `score_rescale` linear 0..100
  (= raw here). Pass rate = datasets with roundtrip OK and no error, out of 8. Exit = container exit.

| Arm | Submission | v1 raw / norm | v2 raw / norm (superseded 0..100 scale; see below) | Pass v1 / v2 | Exit v1 / v2 | Expected | OK |
|---|---|---|---|---|---|---|---|
| Trigger / valid control | shipped Varint starter (unchanged) | **0.2327 / 0.2327** | **0.9786 / 0.9786** (repeat **1.0155**) | 8/8 / 8/8 | 0 / 0 | v1 ≠ 1.0, v2 ≈ 1.0 (documented) | yes |
| Honest control | delta + zigzag + varint | **0.8253 / 0.8253** | **6.7024 / 6.7024** (repeat **6.9708**) | 8/8 / 8/8 | 0 / 0 | v2 = documented definition (offline rescore of the v1 logs against the v1 starter run: 7.43; earlier review: 6.24) | yes |
| Invalid control | starter with one corrupted value | **0 / 0** | **0 / 0** | 0/8 / 0/8 (`roundtrip mismatch`) | 0 / 0 | 0 in both | yes |

**Reading the table.**
- The starter now scores about 1.0, as documented. The residual is timing noise: the compression
  ratio is exactly 1.0 on every dataset, and the per-dataset speed ratios range from 0.93 to 1.07
  (`evidence/summary.txt`). Over the six v2 starter runs in this job and the `-rep2` and `-rep3` jobs, they range from 0.84 to 1.14, and the honest codec scores 6.70 to 8.27.
- The honest codec's v2 score follows the documented definition. Its compression terms are exact
  (for example ts_sec 40.00 / 8.00 bpi = 5.0x). The speed terms are same-host ratios. The offline
  rescore (7.43) uses a starter measured in a different container run (r1), so it differs from the
  paired v2 values (6.70 / 6.97) by run-to-run throughput noise. The earlier review's 6.24 came from a
  different worker.
- The invalid control fails the roundtrip gate on all 8 datasets in both versions.
- The exit status is 0 for all arms, as in the original evaluator, which always exits 0 and
  reports status in the JSON.
- v2 adds about 20 s per evaluation (44 s instead of 24 s wall time).

**Verdict: accepted.** The trigger is fixed (0.23 → 0.98/1.02), the honest control is scored by
the documented definition (the change is the intended rescaling; see the README's score
compatibility statement), and the invalid control is rejected in both versions.

**Evidence** (`evidence/`): `summary.txt` (one line per arm, from `summarize.py`), `logs/*.stdout`
(full structured results, including `baseline_per_dataset` for v2), `file_sha.txt`,
`work_sha.txt`, `variants_sha.txt`, `v2_image_id.txt`, `build.log`, `env.txt`, `worker.json`.

## Score scale revision (after a check on real agent submissions)

The table above was recorded with the original score scale (linear 0..100), under which the normalized
score equals the raw result. Real agent submissions showed that this scale saturates once the baseline is
measured as documented, so the fixed task now uses linear 1.0..320 (the starter's documented score to the
formula's maximum, 8 x 40). Raw results are unchanged; only the conversion to 0-100 differs:

- shipped starter: raw 0.9786 / 1.0155 -> 0.00 / 0.00 (the clipped value of -0.0067 is 0);
- honest codec: raw 6.7024 / 6.9708 -> 1.79 / 1.87;
- invalid submission: 0 -> 0.

The same arms with the v2 normalized score on the current scale (this is what `data/paired-results.csv` records):

| Submission | v1 raw / norm | v2 raw / norm (current linear 1..320 scale) |
|---|---|---|
| shipped Varint starter (unchanged) | 0.2327 / 0.2327 | 0.9786 / 0.00 (repeat 1.0155 / 0.00) |
| delta + zigzag + varint | 0.8253 / 0.8253 | 6.7024 / 1.79 (repeat 6.9708 / 1.87) |
| starter with one corrupted value | 0 / 0 | 0 / 0 |

Real submissions from a public Claude Opus 5.5 run (`evidence/runs/opus55-regrade/`), regraded on one
E2B machine: the run's best (agent-20) scores raw 66.31 on the original grader and 160.76 on the fixed
grader; an earlier one (agent-3) scores 31.11 and 114.19. On the old scale both fixed results clip to 100;
on the fixed scale they score 50.08 and 35.48. The verdict above is unaffected: the trigger is fixed,
correct work is scored by the documented definition, and the invalid submission is still rejected.
