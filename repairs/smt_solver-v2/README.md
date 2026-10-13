# smt_solver, fixed version: function values in answers are keyed by evaluated arguments

## What this fixes

When the grader checks a solver's proposed model (its answer), it looks up a function's value by the literal text of the call, such as `"(f x)"`, and ignores what `x` currently stands for. As a result, 27 satisfiable hidden problems cannot be won, and answers written in the documented format are rejected on 42 more. The fixed checker works out a function's actual inputs before looking up its value; wrong answers are still rejected.

### The problem in detail

See the [review](../../evidence/reviews/smt_solver.md). The SAT-model checker (`WitnessChecker` in
`/home/workspace/smt_judge/scripts/evaluate.py`) looks up the value of an uninterpreted-function (UF)
application by the application's source text, for example `"(f x)"`. When the same text appears under
different `let` bindings, every occurrence has to share one value. On 27 of the 546 hidden satisfiable
problems, no answer is accepted, not even a correct model. The shipped `smtlib_spec.md` says something
different: keys are "SMT-LIB symbols or canonical ground terms", UF values are given "for ground
applications needed to evaluate the assertions, such as `"(f a)"`", and the evaluator "checks every
assertion under the witness and enforces congruence". A solver that follows the spec literally and
supplies ground keys is also rejected on 42 more hidden SAT problems.

## What changes

One file, `evaluate.py` (`repair.patch`). Every other part of the grader is unchanged:
parsing, perturbation, timeouts, scoring and the rest of the answer format.
- **Ground keys become a function table.** When the checker is built, each answer key that parses as
  a ground application of a declared function is evaluated. A ground application is `(g t1 … tn)`
  whose arguments contain only declared constants, ground defines, literals, the core/arithmetic
  operators and nested ground applications. The checker records g's value at the *evaluated* argument
  values. Two such keys that give g different values at the same argument values are rejected as a
  congruence violation (a function giving two outputs for the same inputs).
- **Lookup order.** When an assertion applies g, the checker evaluates the arguments in the current
  scope, then uses the table entry for (g, argument values). If no entry exists, it falls back to the
  original textual lookup, so the old key convention still works.
- **Congruence check.** The final congruence check now starts from the table entries. The function
  defined by the answer must therefore be single-valued over both the ground keys and every
  application that was evaluated.
- **Task JSON.** `task.json.in` changes only `judge.image_tag`. The agent's working image and the files the agent can see
  are unchanged.

**Why minimal and sound.**
- **Minimal.** The checker already computed `arg_values` for its congruence check, and the fix
  keys values by them. The textual path is kept as a fallback.
- **Sound.** An answer is accepted only if every assertion evaluates to true under a single-valued
  interpretation of each function. Lean proves that whenever the fixed checker accepts, the formula is
  satisfiable (`fixed_sound`); the proved statement asserts that a model exists, not that the submitted
  witness is itself one. The
  wrong-model test submissions in the side-by-side run test this direction (see results).

**Score compatibility.**
- **Comparable:** fixed-version scores are comparable with original scores for any solver whose answers use only textual
  keys, except when a `let` reuses the name of a declared constant: the textual key is then read as the global term, and
  the fixed checker can reject a genuine model that the original accepted. The same model written with ground keys passes.
  None of the 774 hidden files contains such a `let` (proved and scanned: `../../evidence/formal/notes/smt_solver.md`).
- **Not comparable:**
  - for solvers that emit ground-term keys, which the fixed version accepts where the original rejected them;
  - on the 27 hidden files that reuse the same text under different bindings, which the original grader cannot award at all.
- **Newly rejected:** an answer that the original grader accepted but that assigns a function two different values at
  the same argument values through an unused ground key. That answer does not define a function, so
  the spec's "enforces congruence" covers this case.

## How it was checked

A side-by-side run of the original and fixed graders on the same answers: [paired/results.md](paired/results.md). Correct answers with ground keys, rejected by the original grader, are accepted by the fixed grader; wrong models are rejected by both.

## Limits

- The answers come from z3 models replayed by a stand-in solver. No complete solver built for the task
  was used.
- The "z3-proven not a model" status of the wrong-model answers depends on z3 4.13.0.0.
- The spec text was not reworded. Its "canonical ground terms" wording now matches the checker.
- Each side-by-side job was run three times on fresh E2B workers, with identical verdicts and scores
  (`paired/results.md`, Limits).

## Build and use

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
