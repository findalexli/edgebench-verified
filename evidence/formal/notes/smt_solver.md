# smt_solver: SAT-witness checker, original and fixed

## Claim

(a) The original checker reads `(f x)` by its text, so on `(distinct a b)`, `(let ((x a)) (= (f x) a))`,
`(let ((x b)) (= (f x) b))` (satisfiable, f = identity) it rejects every witness. (b) The fixed checker is
sound for every witness and every key order. It is complete for ground-key witnesses. (c) Our
compatibility claim for textual keys is too broad (see Result).

## Model and link to the code

`lean/ebv/Ebv/SmtWitness.lean` models `WitnessChecker` in `/home/workspace/smt_judge/scripts/evaluate.py`
(original sha256 `f4be8e8d…0ece9b`, fixed `bbc730f8…8f2998`). The source line map is in the file
header. The fragment is QF_UF with one sort, constants, one unary `f`, `let` in formulas and terms, `=`,
`not` and short-circuit `and`. The original checker is the fixed one with an empty table
(`orig_eq_fixed_empty`). Table loading takes the key order as a parameter, so the real length sort is
covered. Differential check: 15 cases run on both real files (`smt_solver/diff_real_checkers.py`). The
verdicts and error classes match the `decide` examples and the published mini table.

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
  model accepts a superset of what the real code accepts. Soundness carries over to the real code;
  completeness is unaffected.
- An undeclared, unbound symbol is an error in the model but an atom in the real code.
- Keys are modelled as parsed terms, not as their spacing.
- That a finite G with the coverage property exists is not proved. It holds for finite models.
