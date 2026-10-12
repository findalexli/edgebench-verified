# arc_compiler_runtime v2: paired results

E2B job `evidence/runs/arc_compiler_runtime-v2-paired/` (one worker, 242 s, exit 0,
worker killed; raw logs in that job's `result/out/`). For each control, `compiler/src/` was taken from
the v1 work image (original digest) or the v2 work image (built from `../Dockerfile` inside the worker),
the control overlay was applied, and the submission was scored by the **original judge image** with the
**original `judge.eval_cmd`** under `--network none`. Public = `bash score.sh` inside the matching work image.
Normalized = `sforge/harness/score_rescale.py` with the task's `linear 0..100` (identity here).

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

Per-suite counts (`suites/suites_<ver>_<control>.txt`) are byte-identical between v1 and v2 for every control.

Type-system suites (weight 1000/2970 = 33.67 points):

| Control | round2-type-system /8 | adversarial-1 /40 | adversarial-2 /40 | adversarial-3 /40 |
| --- | ---: | ---: | ---: | ---: |
| (a) starter | 0 | 0 | 0 | 0 |
| (b) `[]` | 5 | 0 | 0 | 40 |
| (d) honest, documented shape | 8 | 40 | 40 | 40 |
| (e) honest, starter shape | 0 | 0 | 0 | 0 |

## What this shows

- **Scoring is unchanged.** v2 changes only two solver-visible Markdown files (`solver_visible_v1_v2.diff`:
  `TASK.md`, `problem.md`; `git status` in the v2 work image shows exactly these two as modified). Every
  submission scores identically under v1 and v2.
- **Trigger (the defect, and why the docs fix it).** (d) vs (e): the same honest analysis scores 69.26 in the
  shape the hidden tests use and 35.59 in the starter's own shape. The 33.67-point gap is the entire
  type-system weight, lost silently. Under v1 nothing tells the solver which shape is right; v2 TASK.md
  states it. (d) is a general token-level scope/mutability/arity checker (~120 lines). It emits only
  the message texts the v2 TASK.md names, and it gets 128/128 type-system cases. So the documented
  contract is sufficient to earn those points. Caveat: its author had read the hidden tests, so (d) is not
  a blind-solver result.
- **Format alone** (b) moves 35.59 to 47.21 (+11.62). That gain comes only from the return shape: an empty
  array passes the "no error expected" cases. v2 now discloses the shape. This is a weak-oracle property of
  the original tests that v2 does not remove (see README limits).
- **Invalid control** (c): broken codegen is caught by the public smoke tests (40/48) and by the hidden
  codegen suites (0/30, 0/12, 0/40). It scores 25.79, below the starter, in both versions.
- **Measured starter value.** The shipped starter scores public `SCORE=100.00` (48/48), not the `SCORE=0.00`
  that v1 TASK.md states. v2 states the measured value.

Unexplained detail (no effect on the conclusion): with (c), `round2-codegen` is 5/8 against the starter's 4/8.
One round2-codegen case evidently passes when the generated JS yields `null`. Not investigated.
