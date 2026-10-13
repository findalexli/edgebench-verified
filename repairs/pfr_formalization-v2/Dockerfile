# pfr_formalization v2 judge image. Build context: this directory. No network, no installs.
FROM seededge/edgebench.judge.pfr_formalization@sha256:07b51e8e10011654f0c0f79326bb66da05f1e6e2a88b35d0f1418af81d509cc4
# v2 baseline: PFR/WeakPFR.lean with the two `(μ : Measure Ω := by volume_tac) ...` measure binders
# (and their IsProbabilityMeasure instances) moved out of `variable` into the signatures of the five
# lemmas that used them, so their types no longer contain `sorryAx`. The grader (eval_lean.py,
# ListDeclAxiom.lean) and eval_cmd are unchanged.
# The tar holds the fixed source plus every file that `lake build ListDeclAxiom` and `lake build`
# rewrote for it inside the original image (absolute paths under
# home/workspace/judge/se-bmk-intern/pfr, with their mtimes); ADD extracts a local tar.
ADD files/judge/v2-build-artifacts.tar /
