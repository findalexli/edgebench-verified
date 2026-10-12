# VLIW Kernel Optimization (`vliw_kernel_optimization`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Systems & Software Engineering
- **Decision:** Retain with note. The only issue found concerns scorer isolation, which is outside this release's scope. Honest submissions are scored correctly.

## What the task promises

The prompt says: "Implement KernelBuilder.build_kernel so the generated instruction program is correct and faster on the simulator." It also says: "Modify only solution.py. Do not change problem.py, runner.py, verifier.py, test cases, or hard-code public or hidden seeds."

The submitted program counts only if every correctness case passes. Its score is then the cycle count on the performance case. The rescale is `log_min` with baseline 4475.53 and expert 1000.

## What we checked and how

- **Native runs.** We ran the original `eval_cmd` from the task JSON, unchanged, inside the pinned judge image. Settings were `--network none --memory 4g --cpus 2`, with only `solution.py` replaced by each control.
- **Honest controls.**
  - A known-good control: the starter `solution.py` shipped in the image, which builds a correct naive kernel.
  - A known-bad control: an empty program.
- **Hidden cases.** The file holds 8 correctness cases and 1 performance case, all with height 10, 16 rounds and batch 256.
- **Rescale.** Rescaled values were computed with the repository's `score_rescale.py` (`log_min`, clipped to 0–100).
- **Original identity.**
  - Judge image: `seededge/edgebench.judge.vliw_kernel_optimization@sha256:e0d5eeaf24e98c8a53bd04e2d268cd662ae41871340944baf445afc0274eef5f`.
  - Task JSON: sha256 `b6861e44…57d3`.
  - `runner.py`: `2c49071045bdd796fd5c53abcc70717e700e69b913ccae658eb671dc77ea1172`.
  - `verifier.py`: `4b0bc76cf87dedb68b166ea481c10ebef3eb8a684dc8dc20c283cb3d18ba2fd5`.
  - `problem.py`: `fadb0f0858e2259f5759077a5544b9906dad3ceee80d37b4f0aa77da730c93c9`. It is byte-identical to `tests/frozen_problem.py`.
  - Starter `solution.py`: `778c1dceb6e8731424301faa93d47f253ed15bc4016ac002495c5538cf1b39da`.
  - `test_cases/hidden_cases.json`: `81727bbefd0bfa90d2a9e21eaf518a2571d7d93dacc2068c177c886f06050fea`.

## What we found

**Honest controls on the original evaluator.**

| Submission | Original judge result | Rescaled |
|---|---|---|
| starter `solution.py` (correct naive kernel) | valid, 9/9 PASSED, cycles = 147734 | 0 |
| empty program (known-bad) | invalid, 0/9, no score | (invalid) |

The correctness check rejects a wrong program, and a correct kernel receives its true cycle count.

**Scorer isolation.** Scorer isolation is outside this release's scope (EdgeBench design choice); no good-faith scoring defect was found.

**Earlier withholding.** An earlier audit withheld the original task because of a scorer-isolation concern. Under this release's scope, that concern is not grounds for withholding. Re-checking found no defect that affects a good-faith submission.

## Note for users

No repair. The note says: this release does not evaluate scorer isolation (an EdgeBench design choice). Honest submissions are scored correctly on the original evaluator.

## Limits and what was not run

- No model or solver re-runs were done. Results are shown only on authored controls.
- Only one judge image was used, with the starter kernel as the only correct control. No strong, optimized legal kernel was run.
- The work image was not run. The claim that the solver can see `runner.py` and `verifier.py` relies on the task's `submit_exclude` list and the task card.
- No historical submissions were inspected.

## Reproduce

- Run the original `eval_cmd` from `tasks/vliw_kernel_optimization.json` in the pinned judge image with `--network none --memory 4g --cpus 2`. Use either the shipped starter `solution.py` or an empty-program `solution.py`.
- The workspace script folder for this task also holds internal-only audit material and is not part of the public bundle.
