# Borden Source Inversion (`borden_source_inversion`)

**Decision:** Repair (v2). The hidden forward model uses an undisclosed, non-physical convention, so an honest textbook solver scores at baseline; v2 ships the judge's forward model and adds a rescale.

## What the task asks for

The solver must "infer a **finite-duration rectangular-region contaminant source** from public monitoring-well readings", with `C0` defined as "effective source concentration/intensity, in mg/L" and a governing equation `R*dC/dt = div(D grad C) - v dot grad C - lambda*C + source`. The README says to "construct the groundwater solute transport equation, build an ADE/AdePy or equivalent forward approximation", and that the judge will "Use a hidden Borden-ADE region-source forward model". Category: Scientific Problems & ML.

## What goes wrong

**Undisclosed, non-physical forward-model convention.** The hidden model:

- gives each of 225 pulses an amplitude `C0·q·1000/225`, which is a mass rate (mg/d) used as a mass;
- does not use porosity;
- gives the same total mass whatever `duration` is;
- reports mg/m³ as mg/L;
- with `nz=1`, places the source plane at `z_center − half_length_z`, not at the box centre (this looks like an unintended `linspace(num=1)` artifact).

None of this is in the docs. A textbook ADE model differs from the judge's model by 10.9× to 323× pointwise (median 33×): an amplitude factor of duration/(1000·n) ≈ 8.5 at the true source plus the plane offset. Yet the public data cannot tell the conventions apart: the textbook model and the judge's convention fit the public data equally well (RMS log residual 0.0079 for both).

- Example, original evaluator: the honest textbook ADE fit scores **7.03** (bound-midpoint baseline 7.01). The same least squares with the judge's exact convention scores **31.2**. Using the judge's convention except for the source plane (placed at `z_center`, the natural reading) scores 12.9, so the plane placement alone costs about 18 points.

**Raw score uncapped (reporting inconsistency).** The true source scores 109, and the task had no rescale, so `score_0_100` was undefined. An honest fit reaches only about 31, so the ceiling is immaterial to honest solvers.

Checked and found correct: the solver's work layer holds no `scoring/` directory and no hidden file.

## Impact

About 24 points (7.0 vs 31.2 for the same honest fit). This affects every solver who builds the forward model from the documentation rather than guessing the judge's convention.

## Fix (v2)

v2 changes the work image and the task JSON only; labels, evaluator and judge image are unchanged.

- The work image adds `forward_model.py`, the judge's forward model with function bodies byte-identical and only the 2-line header comment replaced.
- A README section states the convention exactly: sub-points and the `z_center − half_length_z` plane, release offsets, pulse amplitude, no porosity, no duration dependence, units as reported. The same section is inserted into `work.agent_query`.
- `task.json.in` adds `judge.rescale = {"kind": "linear", "lower": 0, "upper": 109}`, which keeps ordering above 100 instead of tying scores at a clamp.

| Arm | Kind | v1 raw | v2 raw | v1 normalised | v2 normalised | Cap (both) | hidden / future rRMSE |
|---|---|---|---|---|---|---|---|
| textbook ADE fit (review regression case) | honest, wrong convention | 7.031 | 7.031 | None | 6.45 | cap15 | 2.583 / 1.852 |
| judge-convention fit (review, own re-implementation) | honest | 31.200 | 31.200 | None | 28.62 | cap45 | 0.552 / 0.200 |
| **v2 fit using only the shipped `forward_model.py`** (fitted in the worker) | honest | 31.199 | 31.199 | None | 28.62 | cap45 | 0.552 / 0.200 |
| bound-midpoint baseline | shipped baseline | 7.012 | 7.012 | None | 6.43 | cap15 | 2.622 / 1.925 |
| hidden true source | ceiling anchor (not an honest submission) | 109.000 | 109.000 | None | 100.00 | none | 0 / 0 |
| out-of-bounds answer (C0=5000, half_length_x=500) | invalid | 4.000 | 4.000 | None | 3.67 | cap15 | 9.265 / 2.671 |
| no `answer.json` | invalid | 0 | 0 | None | 0.00 | — | — |

The shipped `forward_model.py` matches the judge's model with max |diff| = 0.0 over all 656 label rows. The v2 solver ran in the v2 work image with no network, using only solver-visible files, and converged to the same point as the judge-convention fit.

**Score compatibility.** Raw scores are identical v1 → v2 for any given `answer.json`. v2 reports `score_0_100 = raw·100/109`, which v1 did not define; v1 raw scores are on 0–109. v2 solver runs are **not** comparable with v1 solver runs, because v2 solvers are told the convention (honest fit 7.0 → about 31 raw).

## How we know

- **Original evaluator in the pinned judge image** (`sha256:b1a08348…`, unchanged in v2). Every arm ran the original eval command with `--network none`, against the v1 and v2 work directories.
- **Independent forward model.** A separate implementation (5×5×1 sub-points, 9 pulses, Gaussian kernel) reproduces all 656 clean labels from the hidden truth (rerun with `evidence/scripts/borden_source_inversion/forward_check.py`). The judge's own model, run in the judge image, matches the stored labels to 8.9e-13 relative.
- **Honest-solver experiments.** Multi-start bounded least squares (60–80 starts) on public noisy, censored data only, once with a textbook ADE model built from the docs and once with the judge's exact convention. Each fitted `answer.json` was scored by the original `evaluate.py` with the original arguments (local Python; numpy 1.24.4, scipy 1.10.1, pandas 2.0.3).
- **Repeatability.** The paired evaluation was repeated three times; no arm changed verdict (see `paired-repeatability.md`).

## Limits

- No model or solver runs. Effects are shown only on authored controls and counterexamples.
- The inverse problem stays weakly identified: the best public-data fit with the exact model reaches 31.2 raw (28.6 normalised). The repair removes the hidden-convention penalty, not the difficulty.
- `C0` remains an "effective intensity" in an unphysical convention. v2 documents it rather than fixing it, because fixing the physics would require regenerating labels.
- One fitting method (multi-start least squares, log/hinge loss) and one textbook model variant were used.
- The prompt says parameters "must stay within" the bounds, but the out-of-bounds control is not hard-rejected by the original evaluator (4 raw, capped at 15). This is unchanged.
- Only the `/home/workspace` work layer was listed for the hidden-file check.

## Reproduce

- Honest-solver experiments: `python3 evidence/scripts/borden_source_inversion/textbook_solver_check.py <judge_root> <out_dir>` (also `judge_convention_solver_check.py`, `judge_convention_truthstart.py`, `variant_zmid_solver_check.py`, `textbook_own_prediction.py`, `forward_check.py` in the same folder).
- Paired evaluation: `repairs/borden_source_inversion-v2/paired/run.sh` (inputs in `paired/inputs/`, solver in `paired/tools/v2_solver.py`).
- Change: `repairs/borden_source_inversion-v2/repair.patch`, `Dockerfile`, `task.json.in`.
- Supporting records: `repairs/borden_source_inversion-v2/` (`source-lock.json` holds full hashes).
