# Review: `order_addition_permutation_optimization`

Reviewer: Claude (critical re-verification), 2026-10-11. Local Docker only, no cloud, no credentials.

## Claim under review

> "A required integrity check expects the wrong fingerprint for its supplied installed helper. Valid reports and nonzero scores remain possible; the small correction is not an approved replacement."

Earlier disposition: **withhold original** (`evidence/selected/order-original-exclusion-binding.json`; card rationale: "the supplied private helper integrity assertion expects 3023... but reads installed 337837...").

## Pinned artifacts

| Item | Identity |
|---|---|
| Task JSON `tasks/order_addition_permutation_optimization.json` | sha256 `d27df71e7e05146b3c8ac49932ea789e5c3d30f53bb538d8d79a8f2ef7d8b84f` |
| Judge image | `seededge/edgebench.judge.order_addition_permutation_optimization@sha256:6d1a1506f52a5cc7c95680c6df7cd72cb95f81fa236b9794aa507490b947fbd8` (pulled, executed) |
| `tests/test_final_result.py` (in image) | `4f1d5fad34da78a1c4083009c0ebcd6de0f2853c13e380ab446b4ad51d8301cc` |
| `tests/score_vcpom_result.py` (in image, installed) | `337837af7067b3dae8d4ef068d26d8dd8ff779f9a627d95451af2ca411c99630` (3651 B, mtime Jul 2) |
| `tests/cost_complex_cy...so` (in image) | `5329caa7...b552` (matches its expected hash) |
| `vcpom_m1000_final_result.txt` | `0abc5e7e...743b` (matches its expected hash) |
| Earlier "merged" extraction `$W/work/task-sources/merged/.../tests/score_vcpom_result.py` | `3023b9a4...dbbac` (3502 B, Chinese comments) - **stale lower layer** |
| Final layer `$W/work/task-sources/order-addition-final-layer-v1/layer.tar.gz` | `42b90b6f...b9a`; contains the 3651 B helper (`337837...`) and English README |
| Upstream harness (ByteDance EdgeBench `6e4e5f4`), copied from `$W/work/edgebench-source` | `selection.py abb55b7b...`, `grading.py ba15c46d...`, `pytest_v.py b099daca...`; all four hashes match `$W/audit/upstream-lock.json` |
| Maintained harness (this repo) | `selection.py 3338ed24...`, `grading.py b3eeac72...`, `pytest_v.py 33375014...`, `judge_server.py 77410d7e...` |

Root cause seen in the bytes: the June 4 layer built `test_final_result.py` with the hash of the Chinese-comment helper. A July 2 layer replaced the helper (and README) with an English-comment translation. That changed only comments and labels, but it changed the file hash, and nobody updated the expected literal. `diff` of the two helpers shows changes to comments, a docstring and example labels only. `parse_result_file` and `score_cost_num` are functionally identical.

## Contract

Prompt and README (scoring section): "The evaluator will check: 1. no private access ... 2. `vcpom_m1000_final_result.txt` has not been modified ... 3. `final_result.txt` exists ... 4. `final_pai` is a valid permutation ... 5. `final_cost` matches the recomputed cost ... 6. A continuous score is calculated using `score_cost_num(cost, num)` from the evaluator-side private `tests/score_vcpom_result.py`." The judge uses `parser: pytest_v`, `selection: pass_rate_first`, `score_direction: maximize`, `rescale: linear 0..100`. Nothing in the contract tells the solver about a helper fingerprint, and a solver cannot affect it: `submit_exclude: ["tests/"]`, and the test reads only `tests/`.

## Code path

`tests/test_final_result.py::test_private_judge_files_are_available`:

```python
assert hashlib.sha256(PRIVATE_SCORE_HELPER_PATH.read_bytes()).hexdigest() == EXPECTED_SCORE_HELPER_SHA256  # "3023b9a4..."
```

- It is unconditional. No mode, flag or submission input reaches it, so it fails for **every** submission.
- On a mismatch, only this one pytest test fails. There is no `TOTAL_SCORE 0` and no session abort. The other four tests, including the one that prints `TOTAL_SCORE`, still run. The helper is loaded at import time without any hash gate, so the score is computed with the installed (functionally identical) helper.
- Consequence in the harness: for `pytest_v`, `pass_rate = passed/total`, so a fully correct submission gets **pass_rate 0.8 instead of 1.0**. The reported `score` is the extracted `TOTAL_SCORE`, which is correct.
- `pass_rate_first` (upstream and maintained versions alike) compares scores **only when both pass rates equal 1.0**. Otherwise a later entry wins only with a strictly higher pass rate. With every valid submission capped at 0.8, the run's `best_score` / `best_round` therefore freeze on the **first** submission that reaches 0.8. Later, better submissions are never selected.

## Independent reproduction

Scripts are in `evidence/scripts/order_addition_permutation_optimization/`:
- `make_result.py` runs inside the image and writes `final_result.txt` using only the public black-box function, counting calls.
- `run_judge.sh OUTDIR` runs the original `eval_cmd` (`python -m pytest tests/test_final_result.py -s -v`) in the pulled image with `--network none --memory 2g --cpus 2`. It then reruns after a one-literal `sed` of the expected helper hash to `337837...`.
- `grade_and_select.py HARNESS_ROOT TASKS_DIR LOGDIR` feeds the saved logs through `grade_output` + `rescale_score` + `select_best`.

Saved outputs are in `observed/`. In-image `sha256sum tests/score_vcpom_result.py` gives `337837af...630`, while the test expects `3023b9a4...bac`. That reproduces the mismatch.

| Submission | Original judge | Repaired literal |
|---|---|---|
| identity permutation (valid; 1 call) | 4 passed / 1 failed (fingerprint); `TOTAL_SCORE 0.0000000033` | 5/5; same score |
| 30 s swap local search (valid; 466 calls) | 4/1 (fingerprint); `TOTAL_SCORE 0.0000009411` | 5/5; same score |
| `badcost` (reported cost = half the true cost) | 3/2; no score | 4/1 (cost mismatch); no score |
| `dup` (duplicate element) | 3/2; no score | 4/1 (not a permutation); no score |

The scores are tiny because 30 s of search is far from the reference cost (2.0e8 vs 9.5e10). The ordering effect does not depend on the magnitude of the scores.

Harness composition, from the real code. Both upstream `6e4e5f4` and the maintained harness give identical results:

```
original judge:  identity pass_rate=0.80 score=3.3e-09 ; search pass_rate=0.80 score=9.411e-07
  history [identity, search]       -> selected identity  best_score=3.3e-09   (better later run ignored)
  history [search, identity]       -> selected search    best_score=9.411e-07
  history [dup, identity, search]  -> selected identity  best_score=3.3e-09
repaired judge:  every history above -> selected search best_score=9.411e-07
```

## Refutation attempts

1. *"The wrong fingerprint never fires on the scoring path."* Refuted. It fires on every submission. The per-submission `TOTAL_SCORE` is indeed correct, but the failed test lowers `pass_rate` to 0.8, and the task's own `selection: pass_rate_first` then uses `pass_rate`. The run-level `best_score` reported by `judge_server.get_run_history` (and stored in upstream `final_result.json` by `run_agent`) depends on submission order and ignores improvements.
2. *"Can a submission avoid it?"* No. `tests/` is excluded from submissions and the check reads only `tests/`.
3. *"Is the per-submission score wrong?"* No. The helpers differ only in comments, and the repaired run produces bit-identical `TOTAL_SCORE` values.
4. *"Is there any consumer that is unaffected?"* Yes. `sforge/visualizer/scanner.py` computes `best_score_0_100 = max(score_0_100 over submissions)` when it loads submissions, and that is order-independent. A summary scan reads `best_round`'s report instead, which is affected. Whether a published number is wrong therefore depends on which consumer produced it.
5. *"Does the repair weaken validity?"* No locally. After the repair, `badcost` and `dup` still fail and produce no score.
6. *"Is the impact real in practice?"* It matters only when a run has more than one valid submission and a later one scores higher. That is the normal pattern for iterative agent runs, but I did not measure the incidence in historical runs.

## Formal check

None. This is a direct byte-hash and control-flow fact; formal tools would not reduce any uncertainty.

## Verdict

**CONFIRMED**, and the impact is broader than the earlier wording says. The fingerprint check fails on every submission. It does not zero the score, but it caps `pass_rate` at 0.8. Under the task's `pass_rate_first` policy, that locks the run-level best score to the first valid submission.

## Disposition assessment

I **agree** with withholding the exact original. The earlier justification undersold the reason. "Valid reports and nonzero scores remain possible" is true per submission, but the defect does reach the reported run score through selection. That justifies withholding even though the measured skill itself is untouched. The fix is a one-literal change outside the solver's control, so the right path is a separately versioned **repair**, approved on its own evidence. Retaining the original with a note would be acceptable only if every published number came from an order-independent max-over-submissions consumer, which is not the case for `final_result.json` / `best_score`.

## Recommended publishable wording

"The original judge checks its own installed score helper against an outdated fingerprint, so every submission fails one of five tests. Per-submission scores are still computed correctly, but the capped pass rate makes the task's pass-rate-first selection keep the first valid submission and ignore later improvements; we withhold the original and propose a one-line fingerprint correction."

## Repair note

The smallest correct fix: set `EXPECTED_SCORE_HELPER_SHA256 = "337837af7067b3dae8d4ef068d26d8dd8ff779f9a627d95451af2ca411c99630"` in `tests/test_final_result.py`. Reverting the helper to the 3502 B version would also work but would revert the translation. Locally, the repaired judge gives 5/5 on valid submissions, still rejects `badcost` and `dup`, and restores score comparison in selection. The earlier native repair pilot (`order-repair-failed-pilot.json`) failed for an unrecorded transport reason. My result is an in-image `sed`, not a rebuilt image run through the full harness pipeline.

## Limits

- Local Docker, x86_64 WSL2. Only the judge image was pulled; the work image was not executed.
- The submissions are simple controls, not reference-quality solutions. No 100-point submission was tested, although by construction a 100-point first submission would also lock the result, which is harmless only if it is the best.
- The selection effect was shown by feeding real logs through real harness code offline, not through a live `judge_server` run.
- Historical incidence in leaderboard runs was not measured.
