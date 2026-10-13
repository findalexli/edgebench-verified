# smt_solver: critical re-verification

> **Note (2026-10-12).** Two statements below are superseded. (1) "6.21 points (0.0621 normalized)": 0.0621 is the raw score on the 0–1 scale; normalized (out of 100) it is 6.21. (2) "an accepted witness is a genuine model": Lean proves only that a model exists when the checker accepts; the original grader accepts `unused_conflict`, whose witness is not a function (`repairs/smt_solver-v2/paired/results.md`, mini cases).

> **Note (2026-10-12, later).** Superseded below: "timeouts … were only spot-checked". The grader runs 16 solver processes at once under a 60 s wall-clock timeout. The official leaderboard configs give the smt_solver grader 16 CPUs (`judge_cpu_limit: 16`), one per process; on a grader with fewer CPUs each problem gets proportionally less CPU, and at 4 CPUs a solver needing 20 s of CPU per problem timed out on a 32-problem subset (`evidence/runs/smt_solver-cpu4v8-a`, `-b`). This is recorded as a note on `cases/smt_solver.md`, not as part of the fix.

## Claim under review

Earlier finding (`docs/FINDINGS.md`, "SMT Solver"; `evidence/selected/12-finding-decisions.json`,
decision `CONFIRMED_SOURCE_LOCAL`):

> "The recovered witness lookup merges expressions from different variable scopes. It cannot
> represent the different values required by a constructed satisfiable example. Native failure and
> score impact remain unobserved."

Decisive versioned claim: "Recovered SMT UF witness lookup collapses distinct legal let scopes to
one textual (f x) key, so it cannot represent the required distinct values in the constructed
satisfiable case." The record's own limits: "not … native image/corpus incidence or score impact".
TASKS.md: "Review pending … Held; no follow-up."

Questions for this review: (1) Is the lookup part of the **scorer** or of a reference? (2) Can it
wrongly reject a correct model or accept a wrong one? (3) Native reproduction. (4) Corpus incidence
and score impact.

## Pinned artifacts

- Task `tasks/smt_solver.json` (sha256 3dd31c12…). Rescale is linear 0..1, applied to
  `final_score/100`.
- Judge image `seededge/edgebench.judge.smt_solver@sha256:2bf3482a5b2952eeadecf16e33041c13c284b7ce5d93f3491b7cfd5088d91fc6`
  (pulled, about 0.66 GB, run locally). Contents:
  - `/home/workspace/smt_judge/scripts/evaluate.py` sha256 **f4be8e8d…**. This file is byte-identical
    to the public `scripts/evaluate.py` in the work export and is copied as
    `scripts/smt_solver/evaluate_original.py`.
  - `SMT-hidden_benchmarks.zip` sha256 d51f1ee9…: 774 cases, 546 sat / 228 unsat.
- Python 3.10.20 in the image. The independent oracle is z3 4.x (`z3-solver` 5.1.0 wheel) in a local
  scratch venv. z3 never runs inside the judge.

## Contract

`smtlib_spec.md` (shipped to the solver):

- "Assertions may contain `let` and annotated terms like `(! term :named name)`."
- "Keys are SMT-LIB symbols or canonical ground terms that appear in the assertions … For
  uninterpreted functions, provide values for ground applications needed to evaluate the
  assertions, such as `"(f a)"`. The evaluator checks every assertion under the witness and enforces
  congruence."
- "SAT cases receive full credit only when the `sat` label is paired with a valid JSON model
  witness. An invalid or missing model receives 0 for that case."

## Where the lookup sits

It is part of the **scorer**. `run_solver_case` calls `validate_sat_witness` (that is,
`WitnessChecker.validate`) on the solver's JSON. `classify_result` gives credit 1.0 to an
expected-sat case only if `model_valid is True`; otherwise the verdict is `invalid_model` with
credit 0. In `WitnessChecker.eval`, a UF application is looked up only by
`canonical_term(term)`, which is the **source text** of the application (for example
`(op ?v_0 ?v_0)`). The fallback `expanded_canonical_term` expands only zero-argument `define-fun`
symbols. It does not substitute `let` bindings or `define-fun` parameters. Every occurrence of the
same text, in any scope, therefore gets the same model value.

## Independent reproduction

1. **Constructed cases, original evaluator, official flags** (`--perturb --perturb-salt hidden-sebench`),
   in the judge image (`run_mini_native.sh` → `mini_native_output.txt`). A fixed-witness stub plays
   the role of a correct solver.

   | Case | Witness | Verdict |
   |---|---|---|
   | `(distinct a b)`, `(let ((x a)) (= (f x) a))`, `(let ((x b)) (= (f x) b))` (sat: f = id) | ground keys `(f a)`,`(f b)` as the spec describes | invalid_model: missing model value for (f x) |
   | same | plus textual key `(f x)` | invalid_model: assertion is false |
   | `(define-fun g ((y U)) U (f y))`, `(= (g a) a)`, `(= (g b) b)` | ground keys | invalid_model: missing (f y) |
   | single `let` | ground key `(f a)` | invalid_model: missing (f x) |
   | single `let` | textual key `(f x)` | correct |
   | ground control, no `let` | ground keys | correct |
   | known-bad model | ground keys | invalid_model: assertion is false |

   In the first case **no** witness can pass. Both applications are read from the single key
   `(f x)`, so they get one value v, and the assertions need v = a and v = b with a ≠ b.

2. **Exact checker-semantics encoding with an independent solver** (`scan_corpus.py --z3`). Every UF
   occurrence is replaced by one constant per textual key, c_K, and the constraint f(args) = c_K is
   added for each occurrence. The constraint also captures the checker's congruence check over
   evaluated argument values, so the formula is satisfiable exactly when some JSON witness exists
   that the checker accepts.

   Validation of the encoding (`witness_roundtrip.py` → `results/roundtrip.jsonl`). On all 42 hidden
   files where the encoding is sat, the z3 model converted to a witness is **accepted by the original
   `WitnessChecker`** (42/42). On every file where it is unsat, the true formula is sat according to
   z3.

3. **Corpus scan** of all 774 hidden files with the original tokenizer rules (`results/scan_syntax.jsonl`):

   - No operator outside the evaluator's supported set appears.
   - UF-relevant files: QF_UF 192 (175 with UF symbols), QF_UFLRA 142 (141).
   - Files with UF applications whose arguments use a let-bound variable ("scoped"): QF_UF 53 sat /
     48 unsat; QF_UFLRA 16 sat / 2 unsat.
   - `define-fun` with parameters appears only in QF_LIA/QF_LRA, which have no UF symbols, so that
     path is not exercised by the corpus.
   - Same text under ≥ 2 different `let` bindings ("multi-context"): **27 expected-sat QF_UF files**
     (15 medium, 12 hard) and 9 unsat. These are the quasigroup files in which each assertion re-binds
     `?v_0 … ?v_n`; for example, `?v_0` is bound to `(op e0 e0)` in one assertion and `(op e1 e1)` in
     another.

4. **Result.** For **all 27** multi-context sat files, the checker-semantics encoding is **unsat**
   while the real formula is **sat** (`results/scan_z3.jsonl`, each under 8 s). No correct solver can
   earn credit on these cases. Every scoped file with a single binding context is checker-sat.

5. **Native confirmation on real hidden cases** (`run_corpus_native.sh` → `native_corpus_output.txt`;
   the cases are extracted at run time from the image's zip):
   - `QF_UF/79f4ca54c7f5a5f0.smt2` (medium, sat): a z3 true model keyed textually gives
     `invalid_model: congruence violation for op`. Keyed with ground terms as the spec describes, it
     gives `missing model value for (op ?v_0 ?v_0)`. No checker-model exists.
   - `QF_UFLRA/ad3c3eb45d5837cf.smt2` (hard, sat, scoped, single context): textual keys give
     `correct`, ground keys give `invalid_model`.
   - The deepest sat file (`QF_LRA/1454d3dc…`, parenthesis depth 2621) is accepted natively
     (`run_deep_native.sh`), so recursion depth is not a problem.

6. **Score impact** (`score_impact.py` → `score_impact_output.txt`). Score =
   100·(0.1·easy + 0.2·medium + 0.7·hard), where unsat cases are capped at 0.2 credit. A perfect
   solver's maximum falls from **78.61 to 72.40, a loss of 6.21 points** (0.0621 normalized). The
   15 unwinnable medium cases are 15/61 of the medium tier.

## Refutation attempts

- *Is this only a reference or baseline helper?* No. It is the hidden scorer's validation path (see above).
- *Could it accept a wrong model?* Not through this mechanism. A witness is accepted only if every
  assertion evaluates to true under the checker's lookups and the recorded (function,
  argument-values) → value pairs are functional. Those pairs define a real interpretation of each
  UF, so an accepted witness is a genuine model. The defect only causes **false rejection**.
- *Could a smarter honest solver work around it by emitting textual keys?* Yes for the 42
  single-context files, and the public `evaluate.py` shows that convention. No for the 27
  multi-context files, which have no accepted witness at all.
- *Is the trigger only a constructed fixture?* No. It is the standard SMT-LIB quasigroup let style,
  and it appears in 27 of 546 hidden sat cases. The public dev set also contains 2 unwinnable sat
  cases (`QF_UF/2e86f158…`, `QF_UF/641f8f56…`).
- *Does the earlier source-only claim overstate?* No. It **understated**: native failure, corpus
  incidence and score impact are now all observed.

## Formal check

z3 serves as the independent decision procedure for an exact encoding of the checker's acceptance
condition. Mapping: the encoding's c_K is the checker's `values[canonical_term]`, and
f(args) = c_K is the checker's congruence over `uf_apps`. The encoding is validated in the positive
direction against the original code on 42 files. The negative direction rests on the exactness
argument and on the native runs. The encoding omits the evaluator's dynamic scoping of
`define-fun` bodies, which is irrelevant here because the corpus has no parameterised defines with
UF.

## Verdict

**CONFIRMED (stronger than stated).** The scorer rejects every correct model on 27 hidden sat cases
(15 medium, 12 hard). A perfect solver loses 6.21 points. Separately, the witness-key convention
the scorer requires (textual keys containing let-variables) contradicts the spec's "canonical
ground terms" on 42 more hidden sat cases. A solver that follows the spec literally fails those as
well.

## Disposition assessment

Earlier: held, no disposition. Recommended: **withhold the original; repair as v2.** The problem is
a deterministic, measurable scorer defect against honest solvers (more than 6% of the attainable
range). It is concentrated in the medium tier, where a quarter of the cases are affected. A
"retain with note" disposition would leave unwinnable cases in the score.

## Recommended publishable wording

"The SAT-model checker looks up uninterpreted-function values by the application's source text, so
the same text under different `let` bindings must share one value. On 27 of 546 hidden satisfiable
cases (15 of 61 medium) no witness is accepted, even for a correct model. A perfect solver's maximum
drops from 78.6 to 72.4."

## Repair note

The earlier record proposed no patch. The smallest correct fix is to key UF applications by
function symbol and **evaluated argument values**. The evaluator already computes these as
`arg_values` for its congruence check. Then accept a witness that supplies either a ground-term key
or a function table, and check congruence as it does now. A backward-compatible variant: try the
textual key first; if it is absent, try a ground key built from the argument values; and report
textual keys that are bound under different contexts. After the repair, re-run the 69 scoped sat
files (all must admit an accepted model) and update the spec's key wording to match.

## Limits

- The witnesses come from z3 models replayed by a stub, not from an end-to-end SMT solver built for
  the task.
- The encoding's negative direction is argued, not machine-proved.
- Evaluator surface outside UF keying (perturbation, preflight scan, timeouts) was only spot-checked.
  The deepest file is fine.
