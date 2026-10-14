# lean_analysis_proofs v2 judge image. Build context: this directory. No network, no installs.
FROM seededge/edgebench.judge.lean_analysis_proofs@sha256:41ece9c40d197540af701c6a9bd592101126708c3f3c46e8f6b0da531597513b
# v2 grader: scores user-facing declarations only (compiler-generated auxiliaries and
# `... sorry`-typed statement placeholders are excluded from the target set).
COPY files/judge/eval_lean.py /home/workspace/judge/se-bmk-intern/eval_lean.py
# Corrected sources (anti_symm parenthesised; div hypothesis on g) plus every build artifact
# that `lake build ListDeclAxiom` rewrote for them inside the original image (paired/run_local.sh,
# out/v2-changed-files.txt). The tar holds absolute paths under home/workspace/judge/se-bmk-intern/analysis
# with their mtimes; ADD extracts a local tar.
ADD files/judge/v2-build-artifacts.tar /
