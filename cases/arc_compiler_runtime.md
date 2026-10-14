# Arc Compiler Runtime (`arc_compiler_runtime`)

**Outcome:** Fixed. <mark>Hidden tests require a return format for `analyze()` that no solver-visible file documents, and TASK.md misstates the starter's score; the fixed version documents both without changing any score.</mark>

![Two horizontal bars for the same error-checking logic: returning a list of {level, message}, as the hidden tests expect, scores 69.26 out of 100; keeping the starter code's {ok, errors, warnings, program} scores 35.59. A note says type-checking tests passed 128 of 128 versus 0, and that the fix documents the format.](figures/arc_compiler_runtime.svg)

*The same honest error checker scores 69.26 or 35.59 out of 100 in Arc Compiler Runtime, depending only on a return format that no instruction mentions. The agent completes a small compiler; hidden tests worth 33.67 points expect error reports as a list of {level, message}, while the starter code returns another format and nothing the agent can see says which is right. The fix documents the format in the task notes; the checker is unchanged, so the same code scores the same as before.*

## What the task asks

The solver must "Implement the missing Arc compiler and runtime modules under compiler/src/". Arc is a small programming language. The solver is told to "Use CHEATSHEET.md, TASK.md, and the public smoke tests as the language contract." TASK.md states "Starter expectation `SCORE=0.00`", and problem.md states "Expected stripped starter score: 0.00". The hidden grader has 21 test suites, 448 cases and 2970 weight units. Category: Systems & Software Engineering.

## What goes wrong

**The `analyze()` interface is not documented.** The hidden type-system suites call `analyze()` from `compiler/src/semantic.js`. They expect an array of `{level, message}` objects. The messages must contain the substrings "Undefined", "Cannot reassign immutable" and "expects 2". The starter code that ships with the task returns `{ ok, errors, warnings, program }` instead. No solver-visible file names the required shape or the message texts. These suites carry 1000/2970 of the weight (33.67 points).

- Example, on the original grader: the same honest analyzer scores **69.26** when it returns the array shape the hidden tests use. It scores **35.59** when it keeps the starter's object shape. It passes 128/128 type-system cases in the first form and 0 in the second. The solver gets no signal about which form is right.

**The stated starter score is false.** TASK.md and problem.md say the starter scores 0.00. In the original work image (the container the agent works in), the starter scores `SCORE=100.00` on the public tests (48/48) and 35.59 on the hidden tests. This misleads a solver about where it starts. It does not change any score.

**One hanging suite voids the whole submission (unchanged, disclosed).** Each of the 21 hidden suites runs in one process with a 90-second limit. If a suite times out or crashes the process, the grader stops and reports `SCORE_STATUS=INFRA_FAIL`, and the submission is invalid with score 0. Example, on the original grader: the starter scores 35.59. The same starter with a one-character typo that makes string interpolation loop forever on `{items[0]}` is reported invalid (score 0) in six of six gradings (two copies, `t_hang` and `t_hang_rep2`, in each of three runs: `evidence/runs/arc_compiler_runtime-hang-suite`, `-rep2`, `-rep3`). That construct occurs in one suite (`round2-interpreter`, 1.35 of the 100 points), and scoring that suite 0/8 would give 34.75. The evaluator documents this as its infra-failure policy, but no file the solver sees mentions it. It affects only submissions with a real non-terminating bug, and under the task's `score_first` selection, which does not read `valid` (`sforge/harness/selection.py:83-103`), the submission is ranked at 0, so it never displaces a submission that scored above 0.

Checked and found correct: exactly 448 cases run, and each has one counted outcome. The starter run had zero import failures. Expected values are written as literals in the test files.

## How much it matters

Up to 33.67 points (the full type-system weight) are lost, with no warning. This affects every solver that keeps the starter's return shape or does not guess the message texts.

## The fix

The fixed version changes two solver-visible Markdown files in the work image and nothing else:

- `agent-start/TASK.md` replaces the false starter row with the measured `SCORE=100.00` (48/48). It adds a "Semantic analysis interface" section. That section gives the return shape (array of `{level, message}`), the three required substrings with the conditions that produce them, and the rule categories the hidden type-system suites check (stated as rules, not as test programs).
- `agent-start/problem.md` replaces the false "0.00" with the measured value and points to the new section.

The grader image, grader, tests, starter code and task prompt are unchanged. `task.json.in` changes only `work.image_tag`. Documentation was chosen over a starter that returns `[]`. Such a starter would raise the starting score from 35.59 to 47.21 and would still leave the message texts undocumented.

| Test submission | Version | Public smoke tests | Hidden raw result (`SCORE`) | Score out of 100 | Pass rate (cases) | valid | exit |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: |
| (a) shipped starter | original | 100.00 (48/48) | 35.59 | 35.59 | 0.3728 (167/448) | true | 0 |
| (a) shipped starter | fixed | 100.00 (48/48) | 35.59 | 35.59 | 0.3728 (167/448) | true | 0 |
| (b) starter, `analyze()` returns `[]` (documented shape only) | original | 100.00 | 47.21 | 47.21 | 0.4732 (212/448) | true | 0 |
| (b) | fixed | 100.00 | 47.21 | 47.21 | 0.4732 (212/448) | true | 0 |
| (c) invalid: codegen emits `var result = null;` | original | 83.33 (40/48) | 25.79 | 25.79 | 0.2879 (129/448) | true | 0 |
| (c) | fixed | 83.33 (40/48) | 25.79 | 25.79 | 0.2879 (129/448) | true | 0 |
| (d) independent honest analyzer, documented shape | original | 100.00 | 69.26 | 69.26 | 0.6585 (295/448) | true | 0 |
| (d) | fixed | 100.00 | 69.26 | 69.26 | 0.6585 (295/448) | true | 0 |
| (e) same analyzer as (d), starter shape `{ok,errors,warnings,program}` | original | 100.00 | 35.59 | 35.59 | 0.3728 (167/448) | true | 0 |
| (e) | fixed | 100.00 | 35.59 | 35.59 | 0.3728 (167/448) | true | 0 |

Type-system suites (weight 1000/2970 = 33.67 points), cases passed:

| Test submission | round2-type-system /8 | adversarial-1 /40 | adversarial-2 /40 | adversarial-3 /40 |
| --- | ---: | ---: | ---: | ---: |
| (a) starter | 0 | 0 | 0 | 0 |
| (b) `[]` | 5 | 0 | 0 | 40 |
| (d) honest, documented shape | 8 | 40 | 40 | 40 |
| (e) honest, starter shape | 0 | 0 | 0 | 0 |

Per-suite counts are byte-identical between the original and fixed versions for every test submission.

**Are scores comparable?** Scores of single submissions are comparable. An identical `compiler/src/` scores the same under the original and fixed versions (measured for 5 test submissions). The score scale (linear 0–100) and its reference points are unchanged. Results of agent runs are **not** comparable. Solvers of the fixed version are told the interface and message texts that solvers of the original lacked. Agent runs on the two versions should not be pooled or ranked together.

## How we checked it

- **Original grader, from the public image pinned by digest** (unchanged in the fixed version). It ran with the original `judge.eval_cmd` under `--network none`. Each test submission was scored once with `compiler/src/` from the original work image and once from the fixed work image. The public `score.sh` was also run inside each work image.
- **Source comparison.** The hidden grader (`score_hidden.sh`) and the hidden type-system test files were compared with every solver-visible file (TASK.md, problem.md, CHEATSHEET, spec/, docs/, public smoke tests).
- **Case inventory.** A static count of the hidden suites (`case_inventory.py`) gives 21 suites, 448 cases and 2970 weight units.
- **Repeatability.** The side-by-side run of the original and fixed versions was repeated three times. No test submission changed its result (see `data/paired-repeatability.md`).

## Limits

- No AI model or solver was run. Effects are shown only on the test submissions and counterexamples we wrote.
- Test submission (d) was written by someone who had read the hidden tests. It shows that the documented interface is enough. It does not show how a solver without that knowledge would perform.
- Some credit for format alone remains. Returning `[]` earns +11.62. A constant analyzer that always returns one diagnostic scored 57.81 (under a stand-in runtime, not in the image). This is because some cases check only whether the result is empty or non-empty. Fixing this needs grader changes that would alter what scores mean.
- The adversarial type-system cases (32% of the weight; not re-derived from the inventory) come from 9 templates. The fixed version does not change this.
- A rebuild of the fixed image is not claimed to be bit-identical. The package was rebuilt from scratch on a clean machine (`evidence/runs/materialize-check-g3`, `status: exit=0`): `materialize.sh` ran unchanged, all 4 outputs matched the lock and the built image holds the two locked files.
- The fixed work image tag in `task.json.in`, `v2-analyze-contract-docs`, is a local build tag; no fixed image is published, so users build and tag it themselves.
- One detail is unexplained and has no effect on the conclusion: under test submission (c), `round2-codegen` is 5/8, against the starter's 4/8.
- The fixed version keeps the grader's all-or-nothing handling of a suite that hangs or crashes (measured: starter 35.59 valid; the same starter with an infinite loop on one suite's construct is invalid, score 0; `evidence/runs/arc_compiler_runtime-hang-suite`). The trigger is a constructed bug, not a solver's code. Whether a run near the 90 s limit is repeatable was not measured.

## Reproduce

- Grader image: `sha256:00a34432…` (unchanged in the fixed version).
- Side-by-side run: `repairs/arc_compiler_runtime-v2/paired/run.sh` (test submissions in `repairs/arc_compiler_runtime-v2/controls/`; per-suite counts in `paired/suites/`). `repairs/arc_compiler_runtime-v2/` is the folder holding the fixed version.
- Hanging-suite check: `evidence/runs/arc_compiler_runtime-hang-suite/run.sh` (arms in `mutate.py`).
- Case inventory: `python3 -I evidence/scripts/arc_compiler_runtime/case_inventory.py <evaluator-hidden dir>`.
- Change: `repairs/arc_compiler_runtime-v2/repair.patch`, `Dockerfile`, `task.json.in`.
- Supporting records: `repairs/arc_compiler_runtime-v2/` (`source-lock.json` holds full hashes).
