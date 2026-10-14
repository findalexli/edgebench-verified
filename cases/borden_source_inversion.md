# Borden Source Inversion (`borden_source_inversion`)

**Outcome:** Fixed. <mark>The grader predicts well readings with a hidden model whose conventions are unstated and not physical, so a one-shot fit with a textbook model scores at the baseline level.</mark>

![Two boxes contrast what the instructions say (build the textbook groundwater model; C0 in mg/L) with five unstated conventions of the checker's model, such as ignoring soil porosity. Below, bars of raw scores (0 to 109) for a one-shot fit to the public data: a baseline at the middle of the allowed ranges, 7.01, textbook model 7.03, checker's model 31.2; beside them, the 36 submissions of a real agent run as dots, with the best score so far rising from 7.01 to 60.10 and a dashed line at 31.2. A note converts raw scores to scores out of 100 (raw × 100/109) and states the fix.](figures/borden_source_inversion.svg)

*A textbook answer scores about 7, because the checker's physics model follows conventions the instructions never state. The agent locates an underground pollution source from monitoring-well readings. Among other things, the checker's model ignores soil porosity and treats a mass rate as a mass, and the public data fit it and the textbook model equally well. A one-shot fit with the textbook model scores 7.03 raw; the same method with the checker's model scores 31.2 (raw results run from 0 to 109; out of 100 these are 6.45 and 28.62). A real agent run climbed from 7.01 to 60.10 raw over 36 submissions, with the checker reporting its error on hidden wells after each one. The fixed task gives agents the checker's own model with its conventions written out, and reports the score out of 100 as raw × 100/109.*

## What the task asks

The agent receives readings from groundwater monitoring wells and must work out a hidden pollution source. The prompt says the solver must "infer a **finite-duration rectangular-region contaminant source** from public monitoring-well readings". It defines `C0` as "effective source concentration/intensity, in mg/L". It gives the governing equation `R*dC/dt = div(D grad C) - v dot grad C - lambda*C + source`. This is the advection–dispersion equation (ADE), the textbook model of a dissolved substance that flows and spreads in groundwater.

The README says to "construct the groundwater solute transport equation, build an ADE/AdePy or equivalent forward approximation". It also says the grader will "Use a hidden Borden-ADE region-source forward model". A forward model predicts well readings from a proposed source. Category: Scientific Problems & ML.

## What goes wrong

**The grader's forward model uses unstated, non-physical conventions.** The hidden model:

- gives each of 225 pulses an amplitude `C0·q·1000/225`, which uses a mass rate (mg/d) as if it were a mass;
- does not use porosity (the share of soil volume that holds water);
- gives the same total mass whatever `duration` is;
- reports mg/m³ as mg/L;
- with `nz=1`, places the source plane at `z_center − half_length_z`, not at the box centre (this looks like an unintended `linspace(num=1)` artifact).

The documentation gives the ingredients but not how they are combined. `public_problem_config.json` lists q (`q_source_m3_per_day`), a factor of 1000 (`fallback_source_scale_factor`), a 5×5×1 grid of sub-points with 9 release steps, and a note that the grader superposes point-source responses. It does not give the per-pulse normalisation, the missing porosity, the duration-independent mass, the unit reading or the resulting plane position. At the true source, on the 24 public readings above 0.01 mg/L, a textbook ADE model differs from the grader's model by 10.9× to 323× (median 33×). The difference comes from an amplitude factor of duration/(1000·n) ≈ 8.5 at the true source, plus the plane offset. Yet the public data cannot tell the conventions apart. The textbook model and the grader's convention fit the public data equally well (RMS log residual 0.0079 for both).

- Example on the original grader: the textbook ADE fit scores **7.03**. The baseline, which answers with the midpoint of every parameter's bounds, scores 7.01. The same least-squares fit with the grader's exact convention scores **31.2**. Using the grader's convention except for the source plane (placed at `z_center`, the natural reading) scores 12.9. So the plane placement alone costs about 18 points.

**The raw result has no defined score out of 100 (a reporting inconsistency).** The true source scores 109 on the raw result (before conversion to 0–100). The task had no score scale, so `score_0_100` was undefined and raw results were reported on 0–109. No recorded submission reaches 100 raw: our best public-data fit reaches 31.2, and the best submission in a third-party Claude Opus 5.5 run reached 60.10 (below). So the missing ceiling clips no recorded score; it leaves results on a 0–109 scale.

Checked and found correct: the agent's working files hold no `scoring/` directory and no hidden file.

## How much it matters

About 24 points on the 0–109 raw scale (7.0 against 31.2), for a one-shot least-squares fit to the public data with one textbook model variant. Other textbook variants were not tested.

For an agent that submits repeatedly, the effect is smaller, and its size was not measured. The grader's per-test output includes the hidden-well and future rRMSE as `CASE feedback_…` lines, so an agent can tune towards the hidden convention. In a third-party Claude Opus 5.5 run on the original grader (36 submissions over 4 hours), the best submission, `agent-23`, describes its model as a textbook point-source ADE solution and scores 60.10 raw, with hidden-well rRMSE 0.223 and future rRMSE 0.101 (`evidence/runs/opus55-rollouts-meta/result/meta/opus-16x4h-1009-0036-w1/borden_source_inversion/final_result.json` and `submissions/agent-23/test_output.txt`). Our grader-convention fit has 0.552 and 0.200. The published 12-hour results for this task are 48.4, 38.5 and 38.2 for three models and 8.0 and 15.1 for two others (`evidence/impact/leaderboard_12h.json`).

## The fix

The fixed version changes only the agent's working image and the task JSON. The answer key, the grader and the grader image are unchanged.

- The working image adds `forward_model.py`. This is the grader's forward model, with function bodies byte-identical and only the 2-line header comment replaced.
- A README section states the convention exactly: sub-points and the `z_center − half_length_z` plane, release offsets, pulse amplitude, no porosity, no dependence on duration, units as reported. The same section is inserted into `work.agent_query`. A revision (2026-10-12) also says, in the file list, scoring steps and rules, that `forward_model.py` is an exact copy of the grader's model and may be used freely; the first published fixed prompt still called the model "hidden" and forbade reading hidden scoring files without that statement. Grading the same seven test submissions in the first and revised fixed working directories gave byte-identical results (`evidence/runs/borden_source_inversion-v2-paired-r3`).
- `task.json.in` adds `judge.rescale = {"kind": "linear", "lower": 0, "upper": 109}`. This sets the score scale: 0 maps to 0 and 109 maps to 100. It keeps results above 100 in order instead of tying them at a cap.

In the table, "Cap" is the score ceiling the grader applies to that submission; it is the same under both graders. The last column is the relative RMS error on the hidden wells and on future readings.

| Test submission | Kind | Original grader, raw | Fixed grader, raw | Original grader, out of 100 | Fixed grader, out of 100 | Cap (both) | Hidden / future rRMSE |
|---|---|---|---|---|---|---|---|
| textbook ADE fit (review regression case) | good faith, wrong convention | 7.031 | 7.031 | None | 6.45 | cap15 | 2.583 / 1.852 |
| grader-convention fit (review, own re-implementation) | good faith | 31.200 | 31.200 | None | 28.62 | cap45 | 0.552 / 0.200 |
| **fixed-version fit using only the shipped `forward_model.py`** (fitted inside the fixed working image) | good faith | 31.199 | 31.199 | None | 28.62 | cap45 | 0.552 / 0.200 |
| bound-midpoint baseline | shipped baseline | 7.012 | 7.012 | None | 6.43 | cap15 | 2.622 / 1.925 |
| hidden true source | reference point for 100 (not a good-faith submission) | 109.000 | 109.000 | None | 100.00 | none | 0 / 0 |
| out-of-bounds answer (C0=5000, half_length_x=500) | invalid | 4.000 | 4.000 | None | 3.67 | cap15 | 9.265 / 2.671 |
| no `answer.json` | invalid | 0 | 0 | None | 0.00 | — | — |

The shipped `forward_model.py` matches the grader's model with max |diff| = 0.0 over all 656 answer-key rows. The fixed-version solver ran in the fixed working image with no network, using only files the agent can see. It converged to the same point as the grader-convention fit.

**Score compatibility.** For any given `answer.json`, raw results are identical under the original and fixed versions. The fixed version reports `score_0_100 = raw·100/109`, which the original version did not define. Original raw results are on 0–109. Agent runs on the fixed version are **not** comparable with agent runs on the original version, because the fixed version tells solvers the convention (the same least-squares fit: 7.0 → about 31 raw).

## How we checked it

- **Original grader.** All test submissions ran on the original public image, pinned by digest and unchanged in the fixed version. Each ran the original grading command with `--network none`, against the original and fixed working directories.
- **Independent forward model.** A separate implementation (5×5×1 sub-points, 9 pulses, Gaussian kernel) reproduces all 656 clean answer-key readings from the hidden true source (rerun with `evidence/scripts/borden_source_inversion/forward_check.py`). The grader's own model, run in the grader image, matches the stored readings to 8.9e-13 relative.
- **Good-faith solver experiments.** These used multi-start bounded least squares (60–80 starts) on the public noisy, censored data only. One run used a textbook ADE model built from the documentation. The other used the grader's exact convention. The original `evaluate.py` scored each fitted `answer.json` with the original arguments (local Python; numpy 1.24.4, scipy 1.10.1, pandas 2.0.3).
- **Repeatability.** The side-by-side run of the original and fixed graders was repeated three times. No test submission changed verdict (see `data/paired-repeatability.md`).

## Limits

- We ran no AI model. The paired results use test submissions and fits we wrote. One third-party Claude Opus 5.5 run on the original grader was read but not regraded (raw results are identical under both graders for the same answer); its best raw score climbed from 7.01 to 60.10 over 36 submissions while the grader reported its error on the hidden wells after each one. How the agent used that feedback was not verified, and the run does not test the fix.
- The inverse problem is still weakly determined by the data. The best public-data fit with the exact model reaches 31.2 raw (28.6 out of 100). The fix removes the penalty for the hidden convention, not the difficulty.
- `C0` remains an "effective intensity" in a non-physical convention. The fixed version documents it rather than fixing it, because fixing the physics would require regenerating the answer key.
- One fitting method (multi-start least squares, log/hinge loss, one seeded run of 60 or 80 starts) and one textbook model variant were used. The 24-point gap is for that variant.
- The prompt says parameters "must stay within" the bounds, but the original grader does not reject the out-of-bounds test submission outright (4 raw, capped at 15). This is unchanged.
- Only the `/home/workspace` working files were listed for the hidden-file check.
- The grader imports its own copy of the model from the scoring directory (`hidden_forward_model.py`), not the `forward_model.py` in the work directory, so a submission that edits the shipped `forward_model.py` cannot change its own score. This follows from the grader code; no such submission was graded.
- The package was rebuilt from scratch on a clean machine (`evidence/runs/materialize-check-g3`, `status: exit=0`): `materialize.sh` ran unchanged, all 5 outputs matched the lock and the built image holds the locked files. The fixed work image tag `f389fcf94240-ebv-v2.1` is a local build tag; no image is published to a registry.

## Reproduce

- Original grader image: `sha256:b1a08348…` (unchanged in the fixed version).
- Good-faith solver experiments: `python3 evidence/scripts/borden_source_inversion/textbook_solver_check.py <judge_root> <out_dir>` (also `judge_convention_solver_check.py`, `judge_convention_truthstart.py`, `variant_zmid_solver_check.py`, `textbook_own_prediction.py`, `forward_check.py` in the same folder).
- Side-by-side run: `repairs/borden_source_inversion-v2/paired/run.sh` (inputs in `paired/inputs/`, solver in `paired/tools/v2_solver.py`).
- Change: `repairs/borden_source_inversion-v2/repair.patch`, `Dockerfile`, `task.json.in`.
- Supporting records: `repairs/borden_source_inversion-v2/` (the folder holding the fixed version; `source-lock.json` holds full hashes).
