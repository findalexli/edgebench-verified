# smt_solver v2: UF witness values keyed by evaluated arguments

**Defect** ([review](../../evidence/reviews/smt_solver.md)). The SAT-model checker (`WitnessChecker` in
`/home/workspace/smt_judge/scripts/evaluate.py`) looks up the value of an uninterpreted-function
application by the application's source text, for example `"(f x)"`. When the same text appears under
different `let` bindings, every occurrence has to share one value. On 27 of the 546 hidden satisfiable
cases, no witness is accepted, not even a correct model. The shipped `smtlib_spec.md` says something
different: keys are "SMT-LIB symbols or canonical ground terms", UF values are given "for ground
applications needed to evaluate the assertions, such as `"(f a)"`", and the evaluator "checks every
assertion under the witness and enforces congruence". A solver that follows the spec literally and
supplies ground keys is also rejected on 42 more hidden SAT cases.

**Change.** One file, `evaluate.py` (`repair.patch`). Every other part of the evaluator is unchanged:
parsing, perturbation, timeouts, scoring and the rest of the witness format.
- **Ground keys become a function table.** When the checker is built, each witness key that parses as
  a ground application of a declared function is evaluated. A ground application is `(g t1 … tn)`
  whose arguments contain only declared constants, ground defines, literals, the core/arithmetic
  operators and nested ground applications. The checker records g's value at the *evaluated* argument
  values. Two such keys that give g different values at the same argument values are rejected as a
  congruence violation.
- **Lookup order.** When an assertion applies g, the checker evaluates the arguments in the current
  scope, then uses the table entry for (g, argument values). If no entry exists, it falls back to the
  original textual lookup, so the old key convention still works.
- **Congruence check.** The final congruence check now starts from the table entries. The function
  defined by the witness must therefore be single-valued over both the ground keys and every
  application that was evaluated.
- **Task JSON.** `task.json.in` changes only `judge.image_tag`. The work image and the solver-visible
  files are unchanged.

**Why minimal and sound.**
- **Minimal.** The checker already computed `arg_values` for its congruence check, and the repair
  keys values by them. The textual path is kept as a fallback.
- **Sound.** A witness is accepted only if every assertion evaluates to true under a single-valued
  interpretation of each function, so an accepted witness is still a genuine model. The paired
  wrong-model controls test this direction (see results).

**Score compatibility.**
- **Comparable:** v2 scores are comparable with v1 for any solver whose witnesses use only textual
  keys.
- **Not comparable:**
  - for solvers that emit ground-term keys, which v2 accepts where v1 rejected them;
  - on the 27 multi-context hidden files, which v1 cannot award at all.
- **Newly rejected:** a witness that v1 accepted but that assigns a function two different values at
  the same argument values through an unused ground key. That witness does not define a function, so
  the spec's "enforces congruence" covers this case.

**Paired evaluation:** [paired/results.md](paired/results.md).

**Limits.**
- The corpus witnesses come from z3 models replayed by a stub. No end-to-end solver built for the task
  was used.
- The "z3-proven not a model" status of the wrong-model witnesses depends on z3 4.13.0.0.
- The spec text was not reworded. Its "canonical ground terms" wording now matches the checker.
- Each arm ran once on one E2B worker.

## Build

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t ebv/smt_solver-judge:v2 .
```

`materialize.sh` takes the following steps:

1. Pull the pinned image(s) by digest, unless already present.
2. Extract the original files with `docker create` and `docker cp`. No container runs in this step.
3. Check each original against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of every file under `files/` (and `orig/`) against `source-lock.json` → `materialize.outputs`. Any mismatch fails loudly.

After that, the `Dockerfile` builds without changes. Regenerated files keep the file mode they have in the image.
See `../MATERIALIZE-CHECK.md` for how each package was verified.
