# Arc Compiler Runtime (`arc_compiler_runtime`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Systems & Software Engineering
- **Decision:** Repair v2 — hidden tests require an undocumented `analyze()` return format, and TASK.md misstates the starter's score; v2 documents both without changing any score.

## What the task promises

The solver must "Implement the missing Arc compiler and runtime modules under compiler/src/" and is told to "Use CHEATSHEET.md, TASK.md, and the public smoke tests as the language contract." TASK.md states "Starter expectation `SCORE=0.00`", and problem.md states "Expected stripped starter score: 0.00".

## What we checked and how

- Source reading of the hidden evaluator (`score_hidden.sh`) and the hidden type-system test files, compared with every solver-visible file (TASK.md, problem.md, CHEATSHEET, spec/, docs/, public smoke tests).
- A static case inventory of the hidden suites (`case_inventory.py`): 21 suites, 448 cases, 2970 weight units.
- A local run of the original scorer bytes with a bun stand-in for tsx/node, which reproduced the earlier native starter result exactly (167/448, weighted 1057/2970, 35.59).
- A paired evaluation on one E2B worker: five authored controls, each scored by the **original judge image** with the **original `judge.eval_cmd`** under `--network none`, once with `compiler/src/` from the v1 work image and once from the v2 work image. The public `score.sh` was also run inside each work image.
- Original identity: judge image `seededge/edgebench.judge.arc_compiler_runtime@sha256:00a34432…` (unchanged in v2); work image `@sha256:3d90ab27…`; key files `score_hidden.sh` sha256 `42a75e67…4994`, `agent-start/TASK.md` `d22bfb01…c5a7d`, `compiler/src/semantic.js` `76a6b573…b1e`.

## What we found

**Confirmed: undocumented `analyze()` interface.** The hidden type-system suites call `analyze()` from `compiler/src/semantic.js` and expect an array of `{level, message}` objects whose messages contain the substrings "Undefined", "Cannot reassign immutable" and "expects 2". The shipped starter returns `{ ok, errors, warnings, program }`, and no solver-visible file names the required shape or message texts. These suites carry 1000/2970 weight (33.67 points).

- Example, original evaluator: the same honest analyzer scores **69.26** when it returns the array shape the hidden tests use, and **35.59** when it keeps the starter's object shape. It earns 128/128 type-system cases in the first form and 0 in the second, with no signal to the solver about which form is right.
- Maximum score effect: up to 33.67 points (the full type-system weight), lost silently.

**Confirmed: false starter expectation.** TASK.md and problem.md say the starter scores 0.00. Measured in the original work image, the shipped starter scores public `SCORE=100.00` (48/48) and hidden 35.59. This misleads a solver about where it starts but does not change any score.

**Refuted (overstated): "suite totals do not prove 448 assertions ran."** An earlier audit raised this. Re-checking showed exactly 448 cases with one counted outcome each, and the starter run had zero import failures, so all 448 were attempted. Expected values are literals in the test files.

Scorer isolation is outside this release's scope (EdgeBench design choice); the good-faith interface defect above was found and is repaired below.

## Repair

v2 changes two solver-visible Markdown files in the work image and nothing else. `agent-start/TASK.md` replaces the false starter row with the measured `SCORE=100.00` (48/48) and adds a "Semantic analysis interface" section: the return shape (array of `{level, message}`), the three required substrings with the conditions that produce them, and the rule categories the hidden type-system suites check (as rules, not test programs). `agent-start/problem.md` replaces the false "0.00" with the measured value and points to the new section. The judge image, evaluator, tests, starter code and task prompt are unchanged; `task.json.in` changes only `work.image_tag`. Documentation was chosen over a starter that returns `[]`, because such a starter would raise the baseline from 35.59 to 47.21 and would still leave the message texts undocumented.

| Control | Ver | Public smoke | Hidden raw SCORE | Normalized | Pass rate (cases) | valid | exit |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: |
| (a) shipped starter | v1 | 100.00 (48/48) | 35.59 | 35.59 | 0.3728 (167/448) | true | 0 |
| (a) shipped starter | v2 | 100.00 (48/48) | 35.59 | 35.59 | 0.3728 (167/448) | true | 0 |
| (b) starter, `analyze()` returns `[]` (documented shape only) | v1 | 100.00 | 47.21 | 47.21 | 0.4732 (212/448) | true | 0 |
| (b) | v2 | 100.00 | 47.21 | 47.21 | 0.4732 (212/448) | true | 0 |
| (c) invalid: codegen emits `var result = null;` | v1 | 83.33 (40/48) | 25.79 | 25.79 | 0.2879 (129/448) | true | 0 |
| (c) | v2 | 83.33 (40/48) | 25.79 | 25.79 | 0.2879 (129/448) | true | 0 |
| (d) independent honest analyzer, documented shape | v1 | 100.00 | 69.26 | 69.26 | 0.6585 (295/448) | true | 0 |
| (d) | v2 | 100.00 | 69.26 | 69.26 | 0.6585 (295/448) | true | 0 |
| (e) same analyzer as (d), starter shape `{ok,errors,warnings,program}` | v1 | 100.00 | 35.59 | 35.59 | 0.3728 (167/448) | true | 0 |
| (e) | v2 | 100.00 | 35.59 | 35.59 | 0.3728 (167/448) | true | 0 |

Type-system suites (weight 1000/2970 = 33.67 points):

| Control | round2-type-system /8 | adversarial-1 /40 | adversarial-2 /40 | adversarial-3 /40 |
| --- | ---: | ---: | ---: | ---: |
| (a) starter | 0 | 0 | 0 | 0 |
| (b) `[]` | 5 | 0 | 0 | 40 |
| (d) honest, documented shape | 8 | 40 | 40 | 40 |
| (e) honest, starter shape | 0 | 0 | 0 | 0 |

Per-suite counts are byte-identical between v1 and v2 for every control.

**Score compatibility.** Per-submission scores are comparable: an identical `compiler/src/` scores the same under v1 and v2 (measured for 5 controls), and the rescale (linear 0–100) and anchors are unchanged. Agent-run results are **not** comparable: v2 solvers are told the interface and message texts that v1 solvers lacked, so v1 and v2 agent runs should not be pooled or ranked together.

## Limits and what was not run

- No model or solver re-runs; effects are shown on authored controls and counterexamples only.
- Control (d) was written by an auditor who had read the hidden tests. It shows the documented contract is sufficient, not how a blind solver would perform.
- Format-only credit remains: returning `[]` earns +11.62, and the earlier triage's constant one-diagnostic analyzer scored 57.81 (bun stand-in, not re-run in the image), because some cases check only for an empty or non-empty result. Fixing this needs judge changes that would alter what scores mean.
- The adversarial type-system cases (32% of weight) come from 9 templates; v2 does not change this.
- One paired run per control. The v2 image was built inside the worker and a rebuild is not claimed bit-identical.
- Unexplained detail with no effect on the conclusion: under control (c), `round2-codegen` is 5/8 against the starter's 4/8.

## Reproduce

- Paired evaluation: `repairs/arc_compiler_runtime-v2/paired/run.sh` (controls in `repairs/arc_compiler_runtime-v2/controls/`; per-suite counts in `paired/suites/`).
- Case inventory: `python3 -I evidence/scripts/arc_compiler_runtime/case_inventory.py <evaluator-hidden dir>`.
- Change: `repairs/arc_compiler_runtime-v2/repair.patch`, `Dockerfile`, `task.json.in`.
- Supporting records: `repairs/arc_compiler_runtime-v2/` (`source-lock.json` holds full hashes).

