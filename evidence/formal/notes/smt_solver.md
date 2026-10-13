# smt_solver: SAT-witness checker, original and fixed

## Claim

(a) The original checker reads `(f x)` by its text, so on `(distinct a b)`, `(let ((x a)) (= (f x) a))`,
`(let ((x b)) (= (f x) b))` (satisfiable, f = identity) it rejects every witness. (b) The fixed checker is
sound for every witness and every key order **within the modeled fragment below**. It is complete for ground-key witnesses subject to the coverage hypothesis below. These are not whole-evaluator soundness or completeness claims. (c) Our
compatibility claim for textual keys is too broad (see Result).

## Model and link to the code

`lean/ebv/Ebv/SmtWitness.lean` models `WitnessChecker` in `/home/workspace/smt_judge/scripts/evaluate.py`
(original sha256 `f4be8e8d…0ece9b`, fixed `bbc730f8…8f2998`). The source line map is in the file
header. The fragment is QF_UF with one sort, constants, one unary `f`, `let` in formulas and terms, `=`,
`not` and short-circuit `and`. The original checker is the fixed one with an empty table
(`orig_eq_fixed_empty`). Table loading takes the key order as a parameter, so the real length sort is
covered. Differential check: 15 cases run on both real files (`smt_solver/diff_real_checkers.py`). The
verdicts and error classes match the `decide` examples and the published mini table.

## Lean constructors and the checker's branches

Line numbers are in the fixed `evaluate.py` (sha256 `bbc730f8…8f2998`, `[v:N]`); the Lean file header also
gives the original's (`[o:N]`). The correspondence is argued from this map and the differential check; it is
not machine-proved.

| Lean (`SmtWitness.lean`) | Checker code (fixed `evaluate.py`) |
| --- | --- |
| `Tm.sym x` in `cT` / `rT` | `WitnessChecker.eval`, string branch: let-environment first (`if term in env`, v:599), then a declared nullary constant through `model_lookup` (v:610-614, v:566-569; "missing model value") |
| `Tm.app t` in `cT` | `eval`, declared-function branch (v:686-702): evaluate the argument, look up `uf_table` at the evaluated value (v:693), else the textual key via `model_lookup_any` (with `expanded_canonical_term`), then append to `uf_apps`. The original is this branch with an empty table |
| `Tm.letT` / `Fm.letF` | `eval`, `let` branch (v:635-640): bound terms evaluated in the outer environment, then shadowing |
| `Fm.eq` | `eval`, `=` branch (v:653-655), all arguments evaluated left to right; two-argument `distinct` (v:656-658) is encoded as `not (= …)` |
| `Fm.not` | `eval`, `not` branch (v:642-643) |
| `Fm.and` (short-circuit) | `eval`, `and` branch (v:644-645): `all(...)` over a generator stops at the first false |
| `ground` | `is_ground_term` (v:505-525), restricted to declared nullary symbols and nested applications |
| `build` (key order `ks` a parameter) | `_load_ground_uf_values` (v:527-564): ground keys sorted by text length (v:552), evaluated in the empty environment; a clash is "congruence violation"; a key whose evaluation raises is skipped |
| `runAsserts` + `congr` | `validate` (v:704-715): each assertion in order ("assertion is false"), then the congruence pass with `seen` starting as the table (fixed) or empty (original, v:709) |
| `Err.missing` / `falseAssert` / `congruence` | the three `ModelValidationError` messages above |

What the fixed checker does with the features the model leaves out. None of these is covered by a Lean
theorem; the fix does not change any of these branches.

| Feature | Handling in the fixed checker | Evidence beyond reading the code |
| --- | --- | --- |
| `define-fun` without parameters | evaluated by substituting its body (v:615-623), cached when the environment is empty; the textual fallback also expands it (`expanded_canonical_term`, v:577-593) | hidden-corpus runs only |
| `define-fun` with parameters | applied by binding each parameter to the evaluated argument and evaluating the body (v:681-685); a UF application in the body is then found through `uf_table` at the evaluated argument | the constructed `define_conflict` case (`evidence/scripts/smt_solver/v2_paired/mini/bench/QF_UF/`, a parameterised define over `f`); the hidden corpus has parameterised defines only in QF_LIA/QF_LRA, which have no UF symbols (`evidence/reviews/smt_solver.md`) |
| `ite` | evaluates the condition as Bool and then only the chosen branch (v:650-652), so an application in the other branch is never recorded | hidden-corpus runs only |
| `or`, `=>` | `any(...)` short-circuits at the first true; `=>` evaluates the consequent only when the premise is true (v:646-649) | hidden-corpus runs only |
| arithmetic (`+ - * /`, `< > <= >=`) | exact rationals (`Fraction`, v:659-680); division by zero is an error; numerals are read only outside QF_UF (v:604-607); `Int` values must be integral (`parse_model_value`, v:434-447) | QF_UFLRA files in the hidden-corpus runs |
| Bool-valued UF, several sorts, n-ary `f` | the same declared-function branch (v:686-702), keyed by the tuple of evaluated argument values; results parsed by sort | hidden-corpus runs only |
| perturbation (`--perturb`) | the witness is validated against the perturbed input file (`run_solver_case`, v:771), which adds fresh Bool (and arithmetic) constants and tautological assertions (`perturbation_blocks`, v:182-223); a witness must give values for those constants | the official-flag paired runs |

"Hidden-corpus runs only" means the 69-file corpus comparison and the full `eval_cmd` arm in the case page,
which exercise these branches only as far as the hidden files use them; no targeted test was written.

## Result

Proved, no `sorry`:
- `fixed_sound`: if the fixed checker accepts, a genuine model exists. This covers the textual
  fallback path, mixed textual and ground keys, and the congruence pass. `orig_sound` follows.
- `fixed_complete_canon`: every model is accepted when the witness gives ground keys `(f g)` for a
  set G of ground terms that is closed under taking arguments and names every value a ground term can
  have.
- `orig_scopeConflict_unwinnable`: the original accepts no witness on the formula above (for all W).

**The fix is narrower than published.** `shadow_textual_regression`: when a `let` binder reuses a
declared constant's name (`(let ((a b)) (= (f a) a))`), the textual key `"(f a)"` is also ground. The
fixed checker therefore stores it as f at the global `a`. A genuine textual-key model that the original
accepts is then rejected as a congruence violation. This contradicts "comparable for any solver whose
answers use only textual keys". The real code shows the same behaviour. The ground-key form still
passes (`shadow_ground_ok`), so the formula is not unwinnable. A scan of the 774 hidden files (zip
`d51f1ee9…`, `shadow_scan.py`) found 0 files with this shadowing, so published scores are not affected.

## Counter-check

- `wrong_rejected_both`: both checkers reject a wrong model.
- `too_strong_unused`: "the fixed checker accepts everything the original accepts" is false.
- `coverage_needed`: completeness fails without the coverage hypothesis.

## Limits

- Only one sort and one unary f. Not modelled: define-fun (`define_conflict`), ite, or, arithmetic,
  Bool-valued UF and perturbation.
- When a table evaluation raises, the model drops the applications it had already recorded, so the
  model accepts a superset of what the real code accepts. Within the modeled fragment, the correspondence argument transfers soundness to the real code;
  completeness is unaffected by this particular difference. The correspondence itself is not machine-proved.
- An undeclared, unbound symbol is an error in the model but an atom in the real code.
- Keys are modelled as parsed terms, not as their spacing.
- That a finite G with the coverage property exists is not proved. It holds for finite models.
- `fixed_sound` and `orig_sound` state that a model *exists* when the checker accepts. They do not
  state that the submitted witness is itself a model; the file's docstring says more than the
  statement. The original accepts `unused_conflict`, whose witness is not a function.
