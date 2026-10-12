# Review: lean_analysis_proofs

## Claim under review

Earlier claim (verbatim): "Two required statements in the acquired source are mathematically
false; sound completion requires changing them. This is an acquired-source contract decision:
installed theorem types and Lean compiler behavior remain unverified. Other targets can earn
legitimate partial credit."

Earlier disposition: **withhold original** (`evidence/selected/12-finding-decisions.json`,
decision `CONFIRMED_MATHEMATICAL_EXCLUSION`; the task card says "exclude exact acquired version").
The two statements are `Chapter11.MajorizesOn.anti_symm` and `Chapter11.PiecewiseConstantOn.div`.

## Pinned artifacts

- Task definition `tasks/lean_analysis_proofs.json`, sha256 `393385a2…8d` (matches task card).
- Judge image `seededge/edgebench.judge.lean_analysis_proofs@sha256:41ece9c40d197540af701c6a9bd592101126708c3f3c46e8f6b0da531597513b`
  (pulled and run locally). The work image was **not** pulled: the coordinator capped local pulls.
- In the image: Lean `4.28.0` (commit `7e01a1bf5c70`), `lean-toolchain` = `leanprover/lean4:v4.28.0`.
  - Judge baseline repo `/home/workspace/judge/se-bmk-intern/analysis`, Mathlib rev `491a4092…`
    (inputRev `v4.28.0`). This repo produces the baseline target list and types.
  - `/home/workspace/baseline/.lake` + `lake-manifest.json` (Mathlib rev `3203991b…`) is copied
    into the solver's repo by `eval_cmd` before `lake build`. Both Mathlib revisions are pinned
    to the `v4.28.0` input revision but are different commits (noted, not investigated).
- Source hashes inside the image (they match the earlier bindings):
  - `Analysis/Section_11_1.lean` `e726bcb6…2020`
  - `Analysis/Section_11_2.lean` `7c33452c…c12b`
  - `Analysis/Section_11_3.lean` `224ae648…9e4a`
  - `../eval_lean.py` `3319767e…cc29`
  - `ListDeclAxiom.lean` in the image is `af482b7a…dfdf1`. This differs from the earlier
    cloud-export copy (`32a40406…`); I used the in-image file.
- Refutation file `scripts/lean_analysis_proofs/Refute.lean`, sha256 `618d86c4…3261`.
  Local mirror `formal/lean/ebv/Ebv/LeanAnalysisLocal.lean`, sha256 `01ae674b…6fad3e`.
  Baseline target dump `scripts/lean_analysis_proofs/baseline-ListDeclAxiom.out`, sha256 `29fcde1b…2f`.

## Contract

The prompt says: "finish **all** sorries in this folder … we value minor progress … do not
modify the signature of existing lemma/theorem/def as these changes will not pass the judge
evaluation."

How the grader works, read from `eval_lean.py` and `ListDeclAxiom.lean`:
- Every declaration in an `Analysis*` module whose transitive axioms include `sorryAx` in the
  judge baseline repo is a target. Scoring is **unweighted** (the default; `eval_cmd` passes no
  `--mode`), so each target is worth 1 point. Score = repaired targets / baseline targets.
- A target counts as repaired only if it is `OK` (axioms limited to `propext`,
  `Classical.choice`, `Quot.sound`) **and** its pretty-printed type string equals the baseline
  string. A changed statement is marked `FAILED` with "type changed". The `HASH` check is
  inactive because this `ListDeclAxiom` prints no `HASH` lines.

Installed statements, printed by the task's own Lean in the judge image:
```
@Chapter11.MajorizesOn.anti_symm : ∀ {f g : ℝ → ℝ} {I : Chapter11.BoundedInterval},
  ∀ x ∈ ↑I, f x = g x ↔ Chapter11.MajorizesOn f g I ∧ Chapter11.MajorizesOn g f I
@Chapter11.PiecewiseConstantOn.div : ∀ {f g : ℝ → ℝ} {I : Chapter11.BoundedInterval},
  Chapter11.PiecewiseConstantOn f I → Chapter11.PiecewiseConstantOn f I → Chapter11.PiecewiseConstantOn (f / g) I
```
The binder of `∀ x ∈ I,` extends over the whole `↔`, so the first statement says that for each
x the pointwise equality is equivalent to global two-sided majorization. In the second statement
both hypotheses are about `f`, so `g` is unconstrained. The source comment says only "I believe
the hypothesis that `g` does not vanish is not needed", which is about a different change.

## Independent reproduction

1. `bash scripts/lean_analysis_proofs/run_in_judge_image.sh` runs the pinned judge image with
   `--network none --memory 4g --cpus 2` and the container removed afterwards. It copies
   `Refute.lean` into the judge baseline repo and runs `lake env lean`, which uses the image's
   prebuilt `Analysis` oleans. `Refute.lean` imports `Analysis.Section_11_3`. The refuted
   propositions are therefore stated with the installed `Chapter11` definitions
   (`BoundedInterval`, `Partition`, `ConstantOn`, `PiecewiseConstantOn`, `MajorizesOn`), not
   Mathlib analogues. Output is in `scripts/lean_analysis_proofs/judge-repo-run.log` (rc 0, about
   40 s).
2. Baseline target count: running `lake build ListDeclAxiom` in the same judge repo (4 GB, 2
   CPUs) printed `SUMMARY checked=4743 bad=2901`. All 2901 BAD lines contain `sorryAx`, so the
   denominator is **2901**. Both refuted declarations are in it, each as a single target. No
   auxiliary declaration is derived from them.
3. Local mirror under Lean 4.34.1 and the ebv Mathlib, using verbatim excerpts of the definitions:
   `lake env lean Ebv/LeanAnalysisLocal.lean` gave the same results. Output is in
   `Ebv/LeanAnalysisLocal.out`.

## Formal check

Kernel-checked in the task's own toolchain and definitions:

| theorem | statement | axioms |
|---|---|---|
| `EbvRefute.anti_symm_false` | `¬ (literal anti_symm type)`; witness I=Icc 0 1, f=0, g=id, x=0 | propext, Classical.choice, Quot.sound |
| `EbvRefute.div_false` | `¬ (literal div type)`; witness I=Icc 1 2, f=1, g=id | propext, Classical.choice, Quot.sound |
| `EbvRefute.anti_symm_corrected` | `(∀ x ∈ I, f x = g x) ↔ MajorizesOn f g I ∧ MajorizesOn g f I` | propext, Classical.choice, Quot.sound |
| `installed_*_inconsistent : False` | `*_false @Chapter11.…` (the installed constants) | adds sorryAx (expected) |

The `installed_*_inconsistent` lines show by elaboration that the refuted propositions are
exactly the installed declarations' types. They depend on `sorryAx` only through the task's
starter `sorry`.

`div_false` argument: P0 = {Icc 1 2} is a partition built in the file (the task's sorried `⊥`
lemmas are not used), so `f = 1` is piecewise constant. If `1/x` were constant on a cell J, J
would be a subsingleton, because `1/a = 1/b → a = b` holds in ℝ under Lean's convention
`0⁻¹ = 0`. A finite union of subsingletons is finite, but it would have to cover the infinite
set `Icc 1 2`. Neither proof uses any lemma from the task, all of which may be `sorry`.

## Refutation attempts

- **Precedence or parsing:** settled by the in-image `#check` and by the kernel proof against the
  installed constant. The reading is not an artifact of the extracted source.
- **Hidden hypotheses the grader accepts:** none. A target scores only if its printed type equals
  the baseline and it is sorry-free. A sorry-free proof of a refuted proposition would derive
  `False` from the three standard axioms. A corrected statement prints differently and scores 0
  for that target ("type changed"). Adding hypotheses or fixing the typo cannot earn the point.
- **Decidable-style exercises:** some nearby exercises (`MajorizesOn.of_add`, …) are `Decidable P`
  holes where `isFalse` is a legitimate answer. These two are plain theorems that assert P.
- **Score effect:** this is where the earlier claim is materially weakened. The two targets are
  2 of 2901, so the attainable maximum is 2899/2901 = **99.93%**, a ceiling 0.069 points below
  full marks. The prompt's "we value minor progress" and the 2901-target size make the task a
  partial-credit task in practice. All other targets remain independently earnable. Proving
  other theorems by using the sorried false lemmas leaves those theorems BAD (axioms are
  transitive), so no credit leaks.
- **Other false targets:** not audited. 2901 targets taken from Tao's *Analysis I* formalisation
  may contain further mis-stated holes; "two" is a lower bound.

## Verdict

**CONFIRMED-NARROWER.** Both statements are false. This is now kernel-checked against the
installed task definitions in the pinned judge image's Lean 4.28.0, so the earlier caveat
"installed theorem types and Lean compiler behavior remain unverified" is resolved. The defect's
effect is narrow: it removes 2 of 2901 equal-weight points (0.07%) and nothing else.

## Disposition assessment

I disagree with "withhold original". VERIFICATION.md says exclusion needs a specific, evidenced
reason, and the evidence here shows a 0.07% ceiling defect in a task whose scoring is designed
around partial credit. Withholding the whole task removes a large formal-math target set over 2
unreachable points, which is disproportionate. Preferred: **repair (small, new version)**.
Acceptable fallback: **retain with a published note** that the maximum score is 2899/2901.
"Withhold" would be defensible only if the release policy requires every target to be
attainable. If so, that policy should be stated and applied consistently, and an audit for
other false targets would then be needed.

## Recommended publishable wording

"Two of the 2901 scored declarations in lean_analysis_proofs (`MajorizesOn.anti_symm` and
`PiecewiseConstantOn.div`) state false propositions. Their negations are kernel-checked
against the task's own definitions in its Lean 4.28 image, so no submission can soundly earn
those two points, which caps the score at 99.93%. All other targets are unaffected."

## Repair note

There is no earlier patch; the earlier record only names "corrected parentheses/divisor
hypothesis". Smallest correct fix, as a new task version:
- `theorem MajorizesOn.anti_symm {f g: ℝ → ℝ} {I: BoundedInterval}: (∀ x ∈ (I:Set ℝ), f x = g x) ↔ MajorizesOn f g I ∧ MajorizesOn g f I`.
  This is kernel-proved here (`anti_symm_corrected`) with only the standard axioms.
- `theorem PiecewiseConstantOn.div … (hf: PiecewiseConstantOn f I) (hg: PiecewiseConstantOn g I) : PiecewiseConstantOn (f / g) I`.
  This is Tao Lemma 11.2.8. It is true without a nonvanishing hypothesis because Lean sets
  x/0 = 0: on each cell of a common refinement f and g are constant, so f/g is constant. It is
  **not** kernel-proved here, because that needs the common-refinement construction (the
  task's own refinement lemmas are sorried). The literal witness g = id no longer satisfies the
  hypotheses.
- Apply the same edit to the work-image starter and to the judge baseline repo, then rebuild the
  judge baseline so that the baseline type strings match. A zero-source-change alternative is
  to drop the two names from the scored set (weighted mode, giving 2899 targets).

## Limits

- Work image not pulled (coordinator resource cap). I did not verify that the solver's starter
  files equal the judge baseline sources.
- The check ran in the judge baseline repo (Mathlib `491a409…`). The solver-side build uses
  baseline `.lake` Mathlib `3203991…`; I did not rebuild there. The refutations use only
  task-local definitions and basic real-number facts, and they also hold under Lean 4.34.1
  (local mirror), so a difference between these Mathlib revisions is very unlikely to matter.
- I did not audit the other 2899 targets for further false statements, and I did not measure
  historical scores.
- The corrected `div` is not kernel-checked.
