# SMT Solver (`smt_solver`)

**Decision:** Repair (v2). The witness checker looks up uninterpreted-function (UF) values by source text, so 27 satisfiable hidden files cannot be won by any solver.

## What the task asks for

The solver must print "sat followed by a JSON model witness that validates the assertions". The shipped `smtlib_spec.md` says "Keys are SMT-LIB symbols or canonical ground terms that appear in the assertions", that UF values are given "for ground applications needed to evaluate the assertions, such as `"(f a)"`", and that "The evaluator checks every assertion under the witness and enforces congruence". It also says that "an invalid or missing model receives 0 for that case". An expected-sat case earns credit only when its model is valid. Category: Combinatorial Optimization.

## What goes wrong

**Rule.** The hidden scorer's validation path reads a UF application's value only by its source text, for example `(f x)`. It does not substitute `let` bindings. When the same text appears under different `let` bindings, every occurrence must share a single value.

**Example.** The assertions are `(distinct a b)`, `(let ((x a)) (= (f x) a))` and `(let ((x b)) (= (f x) b))`. They are satisfiable with f = identity. Under the original evaluator:

- With ground keys `(f a)` and `(f b)`, as the spec describes, the verdict is `invalid_model: missing model value for (f x)`.
- With the textual key `(f x)` added, the verdict is `invalid_model: assertion is false`.

No witness can pass, because both applications read the one key `(f x)`.

**In the hidden corpus** (774 files: 546 sat / 228 unsat):

- **27 expected-sat QF_UF files (15 medium, 12 hard) are unwinnable.** These are quasigroup files that re-bind `?v_0 … ?v_n` in each assertion. In all 27, the checker-semantics encoding is unsat while the real formula is sat. Natively, `QF_UF/79f4ca54c7f5a5f0.smt2` rejects a true z3 model under both key styles.
- **42 more hidden sat files reject spec-form keys.** On these files, a solver that follows the spec literally and emits ground-term keys is rejected. Only the undocumented textual-key convention works there.

**Direction.** The defect only causes false rejection. Any witness the checker accepts still defines a genuine model, so no wrong model is accepted through this mechanism.

## Impact

- A perfect solver's maximum falls from 78.61 to 72.40, a loss of 6.21 points. The 15 unwinnable medium cases are 15/61 of the medium tier.
- All solvers lose the 27 multi-context files. Solvers that emit spec-form ground-term keys also lose the 42 single-context files.

## Fix (v2)

v2 changes one file, `evaluate.py`. When the checker is built, each witness key that is a ground application is evaluated, and its value is recorded against the function and the *evaluated* argument values. During checking, the checker evaluates a UF application's arguments in the current scope and looks up that table entry first. If there is no entry, it falls back to the original textual lookup. Congruence is checked over the table entries and over every evaluated application. Parsing, perturbation, timeouts and scoring are unchanged. The only task JSON change is `judge.image_tag`.

Paired results. Both images are run with the official flags and `--network none`; the hidden zip is identical in both. Corpus: the 69 scoped hidden sat files.

| arm | class | v1 | v2 | expected | ok |
| --- | --- | --- | --- | --- | --- |
| ground (correct, spec keys) | 27 multi-context | invalid_model 27 | **correct 27** | v1 wrong, v2 accepted | yes |
| ground (correct, spec keys) | 42 single-context | invalid_model 42 | **correct 42** | v2 accepted | yes |
| textual (valid control) | 42 single-context | correct 42 | correct 42 | unchanged | yes |
| textual (valid control) | 27 multi-context | unknown 27 (no witness) | unknown 27 | unchanged | yes |
| textual_true (correct model) | 27 multi-context | invalid_model 27 | **correct 27** | v2 may accept (genuine model) | yes |
| textual_true (correct model) | 42 single-context | correct 42 | correct 42 | unchanged | yes |
| ground_wrong (invalid, `-c`) | 27 multi-context | invalid_model 27 | invalid_model 27 | rejected in both | yes |
| ground_wrong (invalid, `-c`) | 42 single-context | invalid_model 42 | invalid_model 42 | rejected in both | yes |

Full original `eval_cmd` (all 774 hidden files, `--parallel 16`), ground arm. The stub answers `unknown` on the 705 files that have no witness.

| version | score | normalized | pass | exit |
| --- | --- | --- | --- | --- |
| v1 | 0.0000 | 0.0000 | 0/774 | 0 |
| v2 | 0.1249 | 0.1249 | 69/774 | 0 |

No arm went from correct to rejected. Of 13 constructed mini cases, the only intended v1-to-v2 rejection is `unused_conflict`. That witness gives f two values at one argument value through an unused key, so it does not define a function. Mini final score: v1 0.1615, v2 0.3231.

**Score compatibility.**

- **Comparable:** v2 scores are comparable with v1 for solvers whose witnesses use only textual keys.
- **Not comparable:**
  - for solvers that emit ground-term keys;
  - on the 27 multi-context files, which v1 cannot award at all.
- **Newly rejected:** a witness that gives a function two values at the same argument values. The spec's "enforces congruence" already rules this out.

## How we know

- **Original evaluator in the pinned image.** Constructed and real hidden cases ran through the original evaluator in the judge image (`sha256:2bf3482a…`) with the official flags (`--perturb --perturb-salt hidden-sebench`). A fixed-witness stub stood in for a correct solver. The deepest sat file (parenthesis depth 2621) was accepted.
- **Independent oracle (z3).** The checker's acceptance condition was encoded exactly and solved with z3, outside the judge. To validate the encoding, z3 models were converted into witnesses on all 42 hidden files where the encoding is sat; the original checker accepted all 42. A scan of all 774 hidden files used the original tokenizer rules. z3 confirmed that all 69 ground witnesses are genuine models and proved that all 69 wrong-model witnesses are not models.
- **Arithmetic.** The score impact was recomputed from the task's tier weights.
- **Repeatability.** The paired evaluation was run three times; no verdict changed (`paired-repeatability.md`).

## Limits

- No model or solver was run. The effects shown here are on authored controls and counterexamples only, and no leaderboard impact is estimated.
- The witnesses are z3 models replayed by a stub, not output from an end-to-end solver built for the task.
- The negative direction of the checker encoding rests on an exactness argument and native runs. It is not machine-proved.
- The "not a model" status of the wrong-model controls depends on z3 4.13.0.0. Each wrong witness changes one UF value, so the controls do not cover every possible wrong-model shape.
- The public dev set is reported to contain 2 unwinnable sat cases; no dev-set scan output is included.
- The spec text was not reworded; its "canonical ground terms" wording now matches the checker.
- Only the UF keying was examined in depth. Perturbation, the preflight scan and timeouts were spot-checked.

## Reproduce

- Constructed cases (native): `evidence/scripts/smt_solver/run_mini_native.sh`; output in `evidence/scripts/smt_solver/mini_native_output.txt`
- Real hidden cases (native): `evidence/scripts/smt_solver/run_corpus_native.sh` and `run_deep_native.sh`
- Corpus scan and checker encoding: `evidence/scripts/smt_solver/scan_corpus.py --z3`; encoding validation: `witness_roundtrip.py`; outputs in `evidence/scripts/smt_solver/results/`
- Score impact: `evidence/scripts/smt_solver/score_impact.py`
- Paired v1/v2: `repairs/smt_solver-v2/paired/run.sh` (wrong-model arm: `run_wrongarm_c.sh`); patch: `repairs/smt_solver-v2/repair.patch`

Supporting records: `repairs/smt_solver-v2/` (README, `source-lock.json`, `paired/results.md`, `paired/evidence/`).
