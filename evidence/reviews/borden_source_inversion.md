# borden_source_inversion: physics convention, honest-solver impact, score ceiling

Reviewer: Claude (groundwater-transport domain review). Scope is good-faith correctness only, per `BRIEF-FOR-REVIEWERS.md`. No tamper analysis. Local CPU only: no images, no E2B, no credentials.

## Claim under review

From `reviews/_science-systems-triage.md` §2 (Borden):

> "An independent forward model reproduces all 656 clean labels from the true source (≤2e-15 relative). The convention is **not unit-consistent** (porosity unused, mg/d treated as mg); a textbook ADE model is 1e4× off." … "**There is no clamp to 100.** The true source scores 109." … "A solver must reverse-engineer the judge's convention."

Earlier disposition: **withhold pending leak check**. If leaked, exclude or repair-v2; otherwise retain-with-note.

## Pinned artifacts

| File | SHA-256 |
|---|---|
| `tasks/borden_source_inversion.json` | 92186582…7195 (from the triage; not re-hashed) |
| work layer `layer.tgz` (`/home/workspace` COPY) | 3ef683eef44458f3c7c09b167a6ea3e741ff9213c7692550aac6a9081ada2b4f (69,443 B) |
| work `README.md` | d19d0c1b5a741c970af859b8412c661903a80b214855bdbb45458bb0b7831982 |
| work `public_problem_config.json` | 27241f47ee3f093bc178019164dc422290de3a55dbd73fe5c15f041cd68d5720 |
| work `public_monitoring_data.csv` | 8a1ed41a9c8b1e07b9f4cd031cfaf703477241b7dd13f3437b34f86096888fb8 |
| judge `opt/borden_scoring/evaluate.py` | 12124bc4a1482595612e1adc34cbb3600c415181b505c81d06bd9bc3f4f75e58 |
| judge `hidden_forward_model.py` | 769ac556b86d283044f5b06edb41a25453410c6a2bde19d88632bc47f243dfd3 |
| judge `hidden_true_region_source.json` | 0aeb75c84c33a9cce7c5460b89c0fffd7e3f8a3998fe335bfc3aa3a3078c42ab |
| judge `hidden_monitoring_data.csv` | 3030ead90e936af5985f9c3cbaeb6c6ba354cf5b594a5500446510d5ef3c179f |
| judge `hidden_wells.csv` | 4d264d9819338abbfe4d6f1f2323f61f7b46a53a151426780e341ef17ba2161c |

The judge files used for execution came from the scratch extraction `src/b/opt/borden_scoring`. Its evaluator, forward model, config and truth hashes are identical to `$W/work/task-sources/merged/borden_source_inversion/opt/borden_scoring`.

**Leak check (side result).** I listed the whole work layer 3ef683… (`tar tzvf`). It holds only `.git/`, `README.md`, `answer.json`, `answer_template.json`, `baseline_solver.py`, `borden_grid.npz`, `public_*` and `requirements.txt`. There is **no `scoring/` directory and no hidden file.** The leak hypothesis is refuted for this layer.

Limit: I did not list the other work-image layers. The triage identified this layer as the `/home/workspace` COPY, which is where `scoring/` sits in the judge image.

## Contract (what the solver is told)

- README: "Use a hidden Borden-ADE region-source forward model to predict concentrations at hidden monitoring wells and hidden future times."
- README: "`C0`: effective source concentration/intensity, in mg/L." The template's governing equation is `R*dC/dt = div(D grad C) - v dot grad C - lambda*C + source`, and the README says to "construct the groundwater solute transport equation, build an ADE/AdePy or equivalent forward approximation".
- `public_problem_config.json`:
  - Hydrogeology: `porosity 0.3`, `velocity 0.02778 m/d`, α = 10 / 0.5 / 0.01 m, `q_source_m3_per_day 0.0676`, and an unexplained `fallback_source_scale_factor 1000`.
  - `region_source_discretization {nx 5, ny 5, nz 1, release_steps 9}`, with the note "Judge approximates rectangular-region finite release by superposing point-source ADE responses over sub-source points and release times."
- **Not disclosed:**
  - the pulse-mass formula;
  - that porosity is not used;
  - that total mass does not depend on `duration`;
  - that with `nz=1` the single source plane sits at `z_center − half_length_z`;
  - that scores can exceed 100.

## What the hidden forward model actually computes

From `hidden_forward_model.py`:

- `_region_subpoints` uses `np.linspace(zc−hz, zc+hz, 1)`, which is `[zc−hz]`. The source is a 5×5 grid of points on the plane **z = z_center − half_length_z**, not at the box centre.
- `_release_offsets` gives 9 instants `linspace(0, duration, 9)`.
- Each of the 225 pulses is an instantaneous 3-D Gaussian with "mass" `C0/225 · q · 1000` (`_fallback_point3`). Porosity is passed in but never used.

Units, with C0 in mg/L, q in m³/d and 1000 in L/m³:

- `C0·q·1000` is a **mass rate in mg/d**, but the model uses it as a total mass in mg.
- Dividing by the kernel volume gives mg/m³, but the model reports that value as **mg/L**.
- The total "mass" is the same whatever `duration` is.

Compare a textbook ADE solution from the same docs. A box source receives fluid at concentration C0 and rate q for `duration`. The dissolved mass is diluted into pore water (÷n), and mg/m³ is converted to mg/L (÷1000). Its plume amplitude differs from the judge's by

**textbook / judge = duration / (1000 · n)** = 2555 / 300 = **8.5** at the true source.

On top of that come the vertical offset (the plane at z_c−h_z versus a box centred on z_c, with D_V = 2.8e-4 m²/d) and the 9-pulse/5-point discretisation. Point by point at the true parameters, my textbook model sits **10.9× to 323× (median 33×) above the labels** on public rows with label > 0.01.

**Correction to the triage:** it reported "1e4×" (9.2e3–4.7e4). Its own `physical_continuous` in `forward_check.py` returns mg/m³ but compares the result with mg/L labels without the ÷1000. The real offset is about one order of magnitude in amplitude plus a geometry offset, not four orders. The triage's qualitative point stands: the model is not unit-consistent physics, and porosity and duration do not enter as physics requires.

## Independent reproduction (EXEC-LOCAL, original evaluate.py)

All scripts are in `evidence/scripts/borden_source_inversion/`:

- `textbook_solver_check.py`
- `textbook_own_prediction.py`
- `judge_convention_solver_check.py`
- `judge_convention_truthstart.py`
- `variant_zmid_solver_check.py`

Each solver fits all 9 parameters inside the public bounds. The method is multi-start bounded least squares (60–80 starts) on **public noisy, censored data only**: log1p residuals on detected rows and a hinge on censored rows. The fitted `answer.json` is then scored by the **original `evaluate.py`** with the original eval_cmd arguments, run on a temporary copy of the public directory.

Run: `python3 <script> <scratch>/src/b <out_dir>`. Outputs (answers and full `score.json` files) are in the scratchpad dirs `borden-textbook-out/`, `borden-judgeconv-out/`, `borden-zmid-out/` and `borden-truthstart-out/`.

| Submission | Fit to public data (RMS log residual) | Hidden-well rRMSE | Future-public rRMSE | Cap | **Score** |
|---|---|---|---|---|---|
| True source (control) | 0.0112 | 1e-13 | 6e-14 | none | **109.0** |
| Baseline (bound midpoints) | — | 2.62 | 1.93 | cap15 | **7.01** |
| Honest **textbook ADE** fit (C0 = 47.4, h_x = 5, h_z = 0.61, t_s = 504, dur = 3057) | **0.0079** | 2.58 | 1.85 | cap15 | **7.03** |
| Textbook fit, C0 rescaled by dur/(1000n) | — | 2.11 | 1.18 | cap15 | 9.89 |
| Textbook fit, C0 rescaled + z_c moved by +h_z | — | 1.69 | 0.32 | cap15 | 15.0 (raw 17.0) |
| Same least squares with the **judge's exact convention** | **0.0079** | 0.55 | 0.20 | cap45 | **31.2** |
| Judge convention, started from the truth | 0.0079 (converges to the same point) | 0.55 | 0.20 | cap45 | 31.19 |
| Judge convention except the nz=1 plane at z_center (natural reading) | 0.0079 | 1.44 | 1.02 | cap30 | **12.9** |

Own-model check (`textbook_own_prediction.py`): the textbook solver's **own** predictions at the hidden rows reach future-public rRMSE **0.23** and hidden-well rRMSE 1.72. Its forecasts of the future public wells are therefore good. The judge reinterprets its parameters through a different convention, and that turns future rRMSE 0.23 into 1.85.

## Refutation attempts

1. **"The public data let an honest solver calibrate the convention away."** Refuted. The textbook model and the judge's convention fit the public data **equally well** (RMS 0.0079 for both, better than the noisy truth at 0.0112). The data cannot tell the conventions apart. The difference shows up only in how the submitted parameters (C0, z_center/half_length_z, duration) are read. The C0 bounds [20, 800] give no warning either: the textbook C0 of 47 is in bounds.
2. **"The docs disclose the convention."** Partly. The discretisation counts and the superposition idea are disclosed, along with q and a factor of 1000. The rest is not:
   - the per-pulse normalisation C0·q·1000/225, which is independent of duration;
   - the missing porosity;
   - the mg/m³-as-mg/L reading;
   - the z_c−h_z plane.

   "Effective … intensity" hints at a fudge factor but does not specify one. The z-plane quirk alone costs about 18 points (31.2 versus 12.9) for a solver that otherwise copies the judge's disclosed discretisation exactly. It looks like an unintended `np.linspace(num=1)` artifact rather than a design choice.
3. **"It is immaterial because the task is ill-posed anyway."** Partly true, and still material. Even the convention-exact solver reaches only 31.2 (hidden-well rRMSE 0.55; the transverse source shape is poorly constrained by the public wells). Within that compressed range, however, the convention decides whether an honest physically correct solver scores like the baseline (7.0) or about 4× higher (31.2). That is a 24-point swing, caused by an undisclosed rule.
4. **Is 109 reachable by an honest solver, and does it matter?**
   - The task JSON has no `rescale`, so `run_evaluation.py:265` sets `score_0_100 = None`. The raw score (0–109) is reported without clipping. The `score_rescale.py` docstring promises a "fallback to clip(raw, 0, 100)", but the code returns None.
   - A score above 100 needs the metric part above 83 of 92, i.e. hidden and future rRMSE near 0.04–0.05. The best public-data fit with the exact convention, even when started at the truth, gets 0.55 / 0.20 and 31.2.
   - So 109 is reachable only by submitting (close to) the hidden truth. That is out of good-faith scope, and the leak route is refuted for the work layer.
   - Verdict on this point: **immaterial for honest solvers**. It is a reporting inconsistency: an unnormalised 0–109 scale, and a null `score_0_100` while 44 of 55 tasks define a rescale. It is worth fixing with a clamp or rescale.

   Not explored: solvers with stronger priors or regularisation might beat 31. I see no route to above 100 from 128 noisy public rows.

## Formal check

None. The question is about modelling conventions and how they affect the score. Execution against the original evaluator answers it directly.

## Verdict

**CONFIRMED-NARROWER (defect).**

- The hidden forward model uses a non-physical, under-disclosed parameter convention:
  - amplitude: pulse mass uses a rate as a mass, has no porosity, reads mg/m³ as mg/L, and ignores duration;
  - geometry: the source plane sits at z_c−h_z.
- An honest solver who builds a textbook ADE model from the docs fits the public data as well as the judge's own model does, yet scores **7.0**, the baseline level. The same solver using the judge's convention scores **31.2**.
- The triage's "1e4×" magnitude is wrong by a factor of about 1000. The correct figure is an amplitude factor of duration/(1000·n) ≈ 8.5 plus a vertical-offset bug, which together give 11–323× pointwise.
- The 109 ceiling is real but immaterial to honest solvers.
- The ground-truth-leak hypothesis is refuted for work layer 3ef683….

## Disposition assessment

I disagree with "retain-with-note" if the note is only a caveat. The defect is an undisclosed scoring rule, and an honest solver cannot discover it from the data. Recommendation: **withhold the original and repair (documentation-level, labels unchanged)**:

1. Ship the judge's forward function to solvers, or state it exactly in the README. That means the per-pulse mass `C0·q·1000/(nx·ny·nz·release_steps)`, no porosity, the output read as mg/L, the offsets `linspace(0, duration, 9)`, and the sub-source z plane. The function contains no secrets. The labels need not change, because they are exactly this model (656/656 to 2e-15).
2. Either document the `nz=1 → z_center−half_length_z` placement, or fix it to the centre **and regenerate the labels**. Fixing the code without regenerating would break agreement with the labels.
3. Add `rescale` (linear 0–109) or clamp to 100, so `score_0_100` is defined.
4. Optional, not required for correctness: state that the inverse problem is weakly identified (the best public-data fit is about 31). That calibrates expectations.

Regression case for the repair: the textbook-fit answer (`borden-textbook-out/answer_textbook_fit.json`) scores 7.03 on the original. Once the forward model is disclosed, a solver re-fitting with it should reach about 31.

## Material limits

- Each conclusion rests on one fitting method (least squares with a log/hinge loss) and one textbook model variant. Other honest textbook variants, such as no porosity or an instantaneous initial-mass source, would land on different wrong C0/z values. The sign of the conclusion does not change.
- I ran the evaluator as plain Python on the host (numpy 1.24.4, scipy 1.10.1, pandas 2.0.3), not inside the pinned judge image. No candidate code runs in the evaluator, and I saw no version-sensitive branch in the scoring path.
- Only the `/home/workspace` work layer was listed for the leak check.
