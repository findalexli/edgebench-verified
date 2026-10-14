# VLIW Kernel Optimization (`vliw_kernel_optimization`)

**Outcome:** Kept, with a note. <mark>The only issue we found concerns scorer isolation, which is outside this release's scope; the grader scored correctly the two rule-following test submissions we ran.</mark>

## What the task asks

The solver writes a program generator for a simulated VLIW processor, a processor that issues many instructions at once. The task text says: "Implement KernelBuilder.build_kernel so the generated instruction program is correct and faster on the simulator." It also says "Modify only solution.py. Do not change problem.py, runner.py, verifier.py, test cases, or hard-code public or hidden seeds."

The generated program counts only if every correctness case passes. Its raw result (before conversion to 0 to 100) is then the cycle count on the performance case. The score scale is `log_min`, a logarithmic scale where fewer cycles score higher. Its reference point for 0 (the baseline) is 4475.53 cycles, and its reference point for 100 (the expert level) is 1000 cycles. Category: Systems & Software Engineering.

## What we checked

We found no defect that changes scores. We checked the following parts.

- The hidden-case file holds 8 correctness cases and 1 performance case. All have height 10, 16 rounds and batch 256.
- We ran rule-following test submissions on the original grader.

| Submission | Original grader result | Score out of 100 |
|---|---|---|
| starting `solution.py` (correct, simple kernel) | valid, 9/9 PASSED, cycles = 147734 | 0 |
| empty program (known to be wrong) | invalid, 0/9, no score | (invalid) |

The correctness check rejected the empty program, and the correct starting kernel received a valid cycle count.

- Scorer isolation is outside this release's scope (an EdgeBench design choice). We found no scoring defect that affects solvers who follow the rules.

The note that ships with the task says that this release does not evaluate scorer isolation (an EdgeBench design choice), and that the original evaluator scored correctly the two controls run (the starter kernel and an empty program, which should fail).

## How much it matters

We measured no effect for submissions that follow the rules.

The scale saturates below 1000 cycles. `log_min` clips at 100, which it reaches at the expert reference point of 1000 cycles. A third-party Claude Opus 5.5 run (4 hours, published on Hugging Face as `adafadaq/edgebench-opus-5-5-xhigh-rollouts`) on this grader had all 18 submissions valid with 9/9 cases passed. Its kernels took 1122, 1027, 979, 970, 966, 965, 962, 957, 956, 951 and 950 cycles (agent-1 to agent-11, `report.json` `score`). Unclipped, these give 92.3, 98.2, 101.4, 102.0, …, 103.4, so every kernel from 979 cycles on scores 100 and the scale does not separate them. The best published result is 85.6 (GPT-5.5 at 12 hours, `tasks/README.md`), about 1240 cycles, so the published scores are not affected. We did not check whether the 950-cycle kernel is correct beyond the 8 correctness cases and 1 performance case, and we did not inspect its source.

The task does not change; the note above ships with it.

## How we checked it

- We ran the original `eval_cmd` from the task JSON unchanged in the original public grader image, pinned by digest, with `--network none`. Each test submission replaced only `solution.py`. `problem.py` is byte-identical to `tests/frozen_problem.py`.
- We computed scores out of 100 with the repository's `score_rescale.py` (`log_min`, clipped to 0 to 100).
- No formal model applies.

## Limits

- We ran no AI model or solver. The grader runs are on test submissions that we wrote; we read the third-party run above and did not regrade it.
- The starting kernel is the only correct test submission we ran. We did not rerun the third-party run's kernels (down to 950 cycles) or check their correctness on inputs beyond the 9 hidden cases.
- This repository does not include the run record for the two test submissions.
- We did not run the work image. The statement that the solver can see `runner.py` and `verifier.py` relies on the task's `submit_exclude` list and the task card.
- We inspected no historical submissions.

## Reproduce

- Third-party run: `evidence/runs/opus55-rollouts-meta/result/meta/opus-16x4h-1009-0036-w1/vliw_kernel_optimization/` (`final_result.json`, `submissions/*/report.json`).
- Run the original `eval_cmd` from `tasks/vliw_kernel_optimization.json` in the pinned grader image with `--network none --memory 4g --cpus 2`. Use either the shipped starting `solution.py` or an empty-program `solution.py`.
- Pinned identity:
  - Grader image: `seededge/edgebench.judge.vliw_kernel_optimization@sha256:e0d5eeaf24e98c8a53bd04e2d268cd662ae41871340944baf445afc0274eef5f`.
  - Task JSON: sha256 `b6861e44…57d3`.
  - `runner.py`: `2c49071045bdd796fd5c53abcc70717e700e69b913ccae658eb671dc77ea1172`.
  - `verifier.py`: `4b0bc76cf87dedb68b166ea481c10ebef3eb8a684dc8dc20c283cb3d18ba2fd5`.
  - `problem.py`: `fadb0f0858e2259f5759077a5544b9906dad3ceee80d37b4f0aa77da730c93c9`.
  - Starter `solution.py`: `778c1dceb6e8731424301faa93d47f253ed15bc4016ac002495c5538cf1b39da`.
  - `test_cases/hidden_cases.json`: `81727bbefd0bfa90d2a9e21eaf518a2571d7d93dacc2068c177c886f06050fea`.
