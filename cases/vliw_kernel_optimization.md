# VLIW Kernel Optimization (`vliw_kernel_optimization`)

**Decision:** Retain with note. The only issue found concerns scorer isolation, which is outside this release's scope; the two honest controls run were scored correctly.

## What the task asks for

The prompt says: "Implement KernelBuilder.build_kernel so the generated instruction program is correct and faster on the simulator." It also says: "Modify only solution.py. Do not change problem.py, runner.py, verifier.py, test cases, or hard-code public or hidden seeds." The submitted program counts only if every correctness case passes; its score is then the cycle count on the performance case. The rescale is `log_min` with baseline 4475.53 and expert 1000. Category: Systems & Software Engineering.

## What goes wrong

No material defect was found. What was checked:

- **Hidden cases.** The file holds 8 correctness cases and 1 performance case, all with height 10, 16 rounds and batch 256.
- **Honest controls on the original evaluator:**

| Submission | Original judge result | Rescaled |
|---|---|---|
| starter `solution.py` (correct naive kernel) | valid, 9/9 PASSED, cycles = 147734 | 0 |
| empty program (known-bad) | invalid, 0/9, no score | (invalid) |

The correctness check rejected the empty program, and the correct starter kernel received a valid cycle count.

- **Scorer isolation** is outside this release's scope (an EdgeBench design choice); no good-faith scoring defect was found.

**Note shipped with the task.** This release does not evaluate scorer isolation (an EdgeBench design choice). The two honest controls run (the starter kernel and an empty program) were scored correctly on the original evaluator.

## Impact

None measured for good-faith submissions.

## Fix (v2)

No change; the note above ships with the task.

## How we know

- **Original evaluator in the pinned image.** The original `eval_cmd` from the task JSON ran unchanged in the judge image (`sha256:e0d5eeaf24e9`) with `--network none`, with only `solution.py` replaced by each control. `problem.py` is byte-identical to `tests/frozen_problem.py`.
- **Rescale.** Rescaled values were computed with the repository's `score_rescale.py` (`log_min`, clipped to 0–100).
- No formal model applies.

## Limits

- No model or solver was run. Results are shown only on authored controls.
- The starter kernel is the only correct control. No strong, optimized legal kernel was run.
- The run record for the two controls is not included in this repository.
- The work image was not run. That the solver can see `runner.py` and `verifier.py` relies on the task's `submit_exclude` list and the task card.
- No historical submissions were inspected.

## Reproduce

- Run the original `eval_cmd` from `tasks/vliw_kernel_optimization.json` in the pinned judge image with `--network none --memory 4g --cpus 2`. Use either the shipped starter `solution.py` or an empty-program `solution.py`.
- Pinned identity:
  - Judge image: `seededge/edgebench.judge.vliw_kernel_optimization@sha256:e0d5eeaf24e98c8a53bd04e2d268cd662ae41871340944baf445afc0274eef5f`.
  - Task JSON: sha256 `b6861e44…57d3`.
  - `runner.py`: `2c49071045bdd796fd5c53abcc70717e700e69b913ccae658eb671dc77ea1172`.
  - `verifier.py`: `4b0bc76cf87dedb68b166ea481c10ebef3eb8a684dc8dc20c283cb3d18ba2fd5`.
  - `problem.py`: `fadb0f0858e2259f5759077a5544b9906dad3ceee80d37b4f0aa77da730c93c9`.
  - Starter `solution.py`: `778c1dceb6e8731424301faa93d47f253ed15bc4016ac002495c5538cf1b39da`.
  - `test_cases/hidden_cases.json`: `81727bbefd0bfa90d2a9e21eaf518a2571d7d93dacc2068c177c886f06050fea`.
