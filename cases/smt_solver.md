# SMT Solver (`smt_solver`)

**Outcome:** Fixed. <mark>The answer checker looks up a function's value by its literal text, so no solver can win 27 satisfiable hidden problems.</mark>

![Two panels. Original checker: two lines, 'let x = a, (f x) = a' and 'let x = b, (f x) = b', both point to one key '(f x)', labelled one text key, two values, no correct answer passes. Fixed checker: the same two lines point to separate keys '(f a)' and '(f b)', correct answer accepted. A note gives 27 unwinnable problems, a perfect solver's maximum of 72.40 instead of 78.61, and 42 more problems where answers in the documented form were rejected.](figures/smt_solver.svg)

*The SMT Solver checker looks up a function's value by how the expression is written rather than by what its argument stands for, so 27 solvable hidden problems can never be passed. The agent builds a logic solver that must print an example solution for each solvable problem. When the same text, such as (f x), stands for two different values, every correct solution is rejected; on 42 more problems, solutions written the way the instructions describe were rejected. This lowers the most a perfect solver can score from 78.61 to 72.40 out of 100. (A correct "no solution" answer earns at most a fifth of a problem's credit, so even a perfect solver tops out at 78.61.) The fixed checker evaluates the argument first and accepts the correct solutions on all 69 problems.*

## What the task asks

The agent builds an SMT solver, a program that decides whether a set of logical constraints can be satisfied ("sat") and, if so, prints values that satisfy them (a model). The solver must print "sat followed by a JSON model witness that validates the assertions".

The shipped `smtlib_spec.md` says "Keys are SMT-LIB symbols or canonical ground terms that appear in the assertions". It says the model gives values of uninterpreted functions (UF, functions whose meaning the solver chooses) "for ground applications needed to evaluate the assertions, such as `"(f a)"`". It says "The evaluator checks every assertion under the witness and enforces congruence". Congruence means a function gives the same output for the same inputs. It also says that "an invalid or missing model receives 0 for that case". A problem expected to be sat earns credit only when its model is valid. Category: Combinatorial Optimization.

## What goes wrong

The hidden grader's checking code reads a UF application's value only by its source text, for example `(f x)`. It does not substitute `let` bindings (local names such as "let x stand for a"). When the same text appears under different `let` bindings, every occurrence must share a single value.

Take the assertions `(distinct a b)`, `(let ((x a)) (= (f x) a))` and `(let ((x b)) (= (f x) b))`, which f = identity satisfies. The original grader gives these verdicts.

- With ground keys `(f a)` and `(f b)`, as the spec describes, the verdict is `invalid_model: missing model value for (f x)`.
- With the textual key `(f x)` added, the verdict is `invalid_model: assertion is false`.

No answer can pass, because both applications read the one key `(f x)`.

The hidden problem set has 774 files (546 sat / 228 unsat).

- No solver can win 27 sat QF_UF files (15 medium, 12 hard). These are quasigroup files that re-bind `?v_0 … ?v_n` in each assertion. In all 27, the formula as the checker reads it is unsat, while the real formula is sat. On the original image, `QF_UF/79f4ca54c7f5a5f0.smt2` rejects a true z3 model under both key styles.
- On 42 more hidden sat files, the checker rejects keys in the form the spec gives. A solver that follows the spec literally and emits ground-term keys fails there, and only the undocumented textual-key convention works.

The demonstrated keying defect rejects correct answers. Lean `orig_sound` and `fixed_sound` prove that acceptance implies satisfiability in the modeled one-sort, unary-function QF_UF fragment. They do not prove this for the entire Python evaluator or all supported SMT-LIB features; we argue the correspondence with the implementation and test it differentially, but it is not machine-proved. The original checker can, however, accept a witness that is not itself a function. The original grader accepts `unused_conflict` below, which gives f two values at one argument value.

A separate note on the grader's CPU count is not part of the fix. The eval_cmd runs `evaluate.py --timeout 60 --parallel 16`, and the timeout is wall-clock time (`proc.communicate(timeout=timeout)`, line 690); a timeout earns 0. All four official leaderboard configs (`examples/all-tasks-k8s/experiment*.yaml` at EdgeBench commit 6e4e5f4) set `judge_cpu_limit: 16` for `smt_solver`, so the 16 solver processes get one CPU each. On a grader with fewer CPUs, for example the configs' default of 4, each problem gets proportionally less CPU in its 60 s. We measured this on the original grader with the grader's exact flags, on a 32-problem subset of the hidden set (QF_LIA, hard, expected unsat) and a stand-in solver. At 4 CPUs a solver needing 20 s of CPU per problem timed out on all 32, while at 8 CPUs it passed (`evidence/runs/smt_solver-cpu4v8-a`, `-b`; `evidence/runs/smt_solver-v2-paired-cpu`, `smt_solver-v2-paired-b-cpu`, `-c-cpu`). The task text also disagrees with itself. The prompt says "16 evaluator workers", while the work image's `smtlib_spec.md:118` says "4 evaluator workers". Neither affects grading at the official 16 CPUs, so we keep this as a note.

## How much it matters

- A perfect solver's maximum falls from 78.61 to 72.40, a loss of 6.21 points. The 15 unwinnable medium problems are 15/61 of the medium tier.
- All solvers lose the 27 files where the same text has several meanings. Solvers that emit ground-term keys as the spec describes also lose the 42 files where it has one.

## The fix

The fixed version changes one file, `evaluate.py`. When it builds the checker, it evaluates each answer key that is a ground application and records the value against the function and the *evaluated* argument values. During checking, the checker evaluates a UF application's arguments in the current scope and looks up that table entry first. If there is no entry, it falls back to the original textual lookup. The checker tests congruence over the table entries and over every evaluated application. Parsing, perturbation, timeouts and scoring are unchanged. The only task JSON change is `judge.image_tag`.

The table gives side-by-side results of the original and fixed graders. Both images run with the official flags and `--network none`, the hidden zip is identical in both, and the problem set is the 69 affected hidden sat files. "Multi-context" files reuse the same text under different bindings; "single-context" files do not.

| Test submission | Files | Original grader | Fixed grader | Expected | As expected |
| --- | --- | --- | --- | --- | --- |
| ground (correct, spec keys) | 27 multi-context | invalid_model 27 | **correct 27** | original wrong, fixed accepts | yes |
| ground (correct, spec keys) | 42 single-context | invalid_model 42 | **correct 42** | fixed accepts | yes |
| textual (correct test submission) | 42 single-context | correct 42 | correct 42 | unchanged | yes |
| textual (correct test submission) | 27 multi-context | unknown 27 (no witness) | unknown 27 | unchanged | yes |
| textual_true (correct model) | 27 multi-context | invalid_model 27 | **correct 27** | fixed may accept (genuine model) | yes |
| textual_true (correct model) | 42 single-context | correct 42 | correct 42 | unchanged | yes |
| ground_wrong (invalid, `-c`) | 27 multi-context | invalid_model 27 | invalid_model 27 | rejected by both | yes |
| ground_wrong (invalid, `-c`) | 42 single-context | invalid_model 42 | invalid_model 42 | rejected by both | yes |

We also ran the full original `eval_cmd` (all 774 hidden files, `--parallel 16`) with the ground test submission. The stand-in solver answers `unknown` on the 705 files that have no prepared answer.

| Grader | Raw score (0 to 1) | Score out of 100 | Pass | Exit |
| --- | --- | --- | --- | --- |
| Original | 0.0000 | 0.00 | 0/774 | 0 |
| Fixed | 0.1249 | 12.49 | 69/774 | 0 |

The task's rescale is linear from 0 to 1 (`tasks/smt_solver.json`), so the score out of 100 is 100 × raw; the grader's own summary line reads `score=0.124948 (12.49/100)` (`repairs/smt_solver-v2/paired/evidence/b/fulleval_lines.txt`).

No corpus test submission went from correct to rejected. Among the 13 small constructed cases, only `unused_conflict` did, as intended, because that answer gives f two values at one argument value through an unused key and so does not define a function. On the small cases the raw score (0 to 1 scale) is 0.1615 under the original grader and 0.3231 under the fixed grader (16.15 and 32.31 out of 100).

Score compatibility depends on how a solver writes its keys.

- Fixed-version scores are comparable with original scores for solvers whose answers use only textual keys, with one exception proved in Lean. A textual key under a `let` that reuses the name of a declared constant can be rejected by the fixed checker (the same model written with ground keys passes). None of the 774 hidden files contains such a `let` (`evidence/formal/notes/smt_solver.md`).
- Scores are not comparable:
  - for solvers that emit ground-term keys;
  - on the 27 multi-context files, which the original grader cannot award at all.
- The fixed checker newly rejects an answer that gives a function two values at the same argument values, which the spec's "enforces congruence" already rules out.

## How we checked it

- We ran constructed and real hidden problems through the original grader in the original public image, pinned by digest, with the official flags (`--perturb --perturb-salt hidden-sebench`). A stand-in solver that prints fixed answers took the place of a correct solver. The grader accepted the most deeply nested sat file (parenthesis depth 2621).
- For an independent check we used z3, a widely used SMT solver. We encoded the checker's acceptance condition exactly and solved it with z3, outside the grader. To validate the encoding, we converted z3 models into answers on all 42 hidden files where the encoding is sat, and the original checker accepted all 42. Our scan of all 774 hidden files used the original tokenizer rules. z3 confirmed that all 69 ground answers are genuine models and proved that all 69 wrong-model answers are not models.
- We recomputed the score effect from the task's tier weights.
- We repeated the side-by-side run three times, and no verdict changed (`data/paired-repeatability.md`).

## Limits

- We ran no AI model or solver. The effects shown come only from test submissions and counterexamples we wrote, and we did not estimate a leaderboard impact.
- The answers are z3 models replayed by a stand-in solver, not output from a complete solver built for the task.
- The claim that the checker encoding rejects exactly what the checker rejects rests on an exactness argument and runs on the original image. It is not machine-proved.
- The "not a model" status of the wrong-model test submissions depends on z3 4.13.0.0. Each wrong answer changes one UF value, so these test submissions do not cover every possible kind of wrong model.
- The public development set is reported to contain 2 unwinnable sat problems, but this repository includes no scan output for it.
- We did not reword the spec text; its "canonical ground terms" wording now matches the checker.
- We examined only the UF keying in depth and spot-checked perturbation and the preflight scan. We measured how the timeout depends on the grader's CPU count on a 32-problem subset with a stand-in solver (note above).

## Reproduce

- Original grader image: `sha256:2bf3482a…`.
- Constructed cases (original image): `evidence/scripts/smt_solver/run_mini_native.sh`; output in `evidence/scripts/smt_solver/mini_native_output.txt`
- Real hidden problems (original image): `evidence/scripts/smt_solver/run_corpus_native.sh` and `run_deep_native.sh`
- Problem-set scan and checker encoding: `evidence/scripts/smt_solver/scan_corpus.py --z3`; encoding validation: `witness_roundtrip.py`; outputs in `evidence/scripts/smt_solver/results/`
- Score effect: `evidence/scripts/smt_solver/score_impact.py`
- Side-by-side run of the original and fixed graders: `repairs/smt_solver-v2/paired/run.sh` (wrong-model test submission: `run_wrongarm_c.sh`); patch: `repairs/smt_solver-v2/repair.patch`; fixed `evaluate.py` sha256 `bbc730f8…2998`
- CPU-count note: `evidence/runs/smt_solver-cpu4v8-a/run.sh`, `-b` (original grader at 4 and 8 CPUs)

Supporting records: `repairs/smt_solver-v2/` (the folder holding the fixed version: README, `source-lock.json`, `paired/results.md`, `paired/evidence/`).
