# lean_analysis_proofs: formal note

## Claim

1. Two target statements are false as installed: `Chapter11.MajorizesOn.anti_symm` and
   `Chapter11.PiecewiseConstantOn.div`. No `sorry`-free submission can earn them.
2. The corrected statements of the fixed version are true and have `sorry`-free proofs.
3. The rest of the fix, which stops scoring 560 compiler-generated helpers and 3 placeholder
   statements, is not a formal claim. It rests on the side-by-side run.

## Model and link to the code

There is no separate model: the theorems are stated against the task's own definitions.

- `scripts/lean_analysis_proofs/Refute.lean` (in `evidence/scripts/`), run with `lake env lean` inside the pinned
  grader image (`sha256:41ece9c4…513b`, Lean 4.28.0, `--network none --memory 4g --cpus 2`), imports
  the task's `Chapter11` and refutes the installed statements. Output: `judge-repo-run.log`.
- `evidence/formal/lean/ebv/Ebv/LeanAnalysisLocal.lean` (output `LeanAnalysisLocal.out`) is a local
  mirror under the project's Lean 4.34.1. It copies the definitions the two statements depend on,
  verbatim, and no task lemma. It proves `anti_symm_false`, `div_false` and `anti_symm_corrected`.
- `repairs/lean_analysis_proofs-v2/paired/lean/EbvV2Proofs.lean` (output
  `repairs/lean_analysis_proofs-v2/paired/out/v2-proofs.out`) runs in the fixed grader's
  repository. `#check` prints the corrected installed types, and it proves `EbvV2.anti_symm_corrected`
  and `EbvV2.div_corrected` (with the helper `EbvV2.inter'`) from task definitions only.

## Result: proved for the two statements

- `anti_symm_false`, `div_false`: the negation of each installed statement, with the
  counterexamples I = Icc 0 1, f = 0, g = id, x = 0 and I = Icc 1 2, f = 1, g = id. Axioms:
  `propext`, `Classical.choice`, `Quot.sound`.
- `EbvV2.anti_symm_corrected`, `EbvV2.div_corrected`: the corrected statements, in the fixed
  grader's repository. Axioms: `propext`, `Classical.choice`, `Quot.sound`
  (`paired/out/v2-proofs.out`). Variant A of the side-by-side run also has both credited by the fixed grader.

## Counter-check

`EbvRefute.installed_anti_symm_inconsistent` and `EbvRefute.installed_div_inconsistent` derive
`False` from the installed, sorried constants. They depend on `sorryAx` by design, and show that
the installed statements contradict the refutations.

## Limits

- The exclusion of the 560 generated helpers and 3 placeholders, which removes the dependence on
  proof style and changes the denominator from 2901 to 2338, has no formal model. It is supported by
  the side-by-side run on one module in three proof styles (`paired/out/style_check.txt`) and by
  checks of the name pattern on all 560 excluded names.
- The local mirror uses Lean 4.34.1, not the task's 4.28.0; the run inside the grader image is the
  authoritative one.
- `LeanAnalysisLocal.out` has no `lean exit=0` line, unlike the other outputs, and
  `EbvV2Proofs.lean` is outside `evidence/formal/` and is not part of the one-command recheck.
- Other false statements among the 2338 targets were not checked.
