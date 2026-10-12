# dabic_gravity_inversion: native addendum (data-space vs model-space form)

**Question.** The prompt permits either a model-space or a data-space D-ABIC. Does the
original evaluator, run natively, score an honest model-space implementation below
the same implementation written in data-space form? In particular, is the model-space
form capped at 0.5×?

**Verdict.** CONFIRMED-NARROWER.

- Natively, an honest model-space directive is classified `is_data_space=false` and
  `structural_failure=true`. That directive computes exactly the same ABIC curve as its
  data-space twin and gives the same hidden-case results (C 17.41 vs 17.39).
- The classification always costs it 3.2 raw points (E1). It also makes the
  uncapped penalty of 1.0 unreachable, so the model-space form is capped at 0.5×.
- The 0.5× cap only *binds* once a submission reaches the "strong" tier: C ≥ 26, D ≥ 20, F ≥ 10.
- In this run, neither arm reached C ≥ 26. Both were penalised at 0.334, and the observed
  gap was only 26.82 vs 25.76.
- At the strong tier, the same work would score about 89 in data form and about 43 in
  model form. This figure comes from the evaluator's own penalty function applied to the
  native breakdowns.

## Contract (quoted)

- Task prompt (`tasks/dabic_gravity_inversion.json` agent_query, sha256 `d4094161…eb34`):
  "Decide for yourself whether to use the model-space or data-space form, how to compute
  determinants, and in which space to optimize beta."
- `starter/README.md`, work image `seededge/edgebench.work.dabic_gravity_inversion@sha256:3b9c3629…4e57`, file sha256 `a81886fc…7d94`:
  - Line 48: "Whether to use model-space or data-space formulation, how to compute the determinant, and in which space to optimize beta are all to be determined by the implementer."
- Caveat a skeptic should weigh: README line 5 says "D-ABIC stands for Data-space
  variant of Akaike's Bayesian Information Criterion". The method's name therefore
  points to data space, but the task text twice explicitly leaves the choice to the solver.
- No solver-visible text says that a model-space form forfeits the uncapped score. No
  such text says that the matrix shapes are inspected, either.

## Pinned artifacts

- Judge image: `seededge/edgebench.judge.dabic_gravity_inversion@sha256:fe3dc29058385bb3f44101df77fc935d8dd7859bbe8aa0add21fc93e83c0731d`, pulled by digest on the worker.
- Evaluator: `/opt/evaluator/eval_dabic_v2.py` sha256 `71ca4da82c850baf49206e16c79023210c58429c3b1f17154c02dfbec57b2409`.
- Gate source:
  - `BehaviorMonitor.report`, `:345-379`: `is_data_space` requires that most captured square
    matrices passed to `np.linalg.eigh`/`slogdet`/`eigvalsh`/`svd` or `scipy.linalg.cho_factor`
    have the hidden *data* count as their dimension. The rule is `structural_failure = (not is_data_space) or …`.
  - `structural_penalty_v34`, `:1369`: the 1.0 penalty requires `not structural_failure`.

## Inputs

All inputs are in `e2b/jobs/dabic_gravity_inversion-forms/inputs/`.

- `dabic_directive_template.py` is one D-ABIC directive. At each `endIter` it builds the
  noise-whitened linearised system `J = W G` with `R = ½ reg.deriv2(m)`, which carries the
  IRLS and sensitivity weights.
- It then chooses β on a log grid around the current β by minimising
  `ABIC(β) = F(β) + log det(I + J R⁻¹ Jᵀ/β)`. This is −2·log evidence for known
  (whitened) noise.
- There are two forms:
  - **data:** factorise R (sparse LU), form `S = J R⁻¹ Jᵀ` (N×N), and call `np.linalg.eigh(S)`.
  - **model:** take the Cholesky factor `R = LLᵀ`, form `H = L⁻¹JᵀJL⁻ᵀ` (M×M), and call `np.linalg.eigh(H)`.
- By Sylvester's identity both forms produce the same ABIC curve. The two generated
  files differ only in the line `FORM = "data"` / `FORM = "model"`.
- `results_fixture.json` and `report_fixture.md` are **audit fixtures**, identical in both
  arms. They hold the self-reported components (B, D) and the keyword-scored report (F)
  constant, so that only the directive form varies.
  - They are not Vinton or synthetic inversion results.
  - The B, D and F totals below are fixture values and must not be read as task performance.

## Command

- Job: `e2b/jobs/dabic_gravity_inversion-forms/run.sh`.
- E2B worker: `iv13fsomz2tpfw6rf5sp1` (8 vCPU). It exited 0 after 121 s and was killed, as recorded in `e2b/ledger.jsonl`.
- Per arm, the job ran the verbatim eval_cmd:
  `docker run --rm --network none --cpus 8 --memory 6g -v <arm>/outputs:/home/workspace/dabic_gravity_vinton/outputs <image@digest> bash -c 'cd /home/workspace/dabic_gravity_vinton && PYTHONPATH=/opt/evaluator python /opt/evaluator/eval_dabic_v2.py /home/workspace/dabic_gravity_vinton/outputs/'`.

## Native results

Raw output is in `result/out/{data,model}/stdout.txt` and `outputs/eval_result.json`.

| arm | A | B* | C (judge-run hidden) | D* | E | F* | raw | penalty (reason) | **score** | valid | is_data_space | structural_failure | matrix dims captured |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| data | 1.0 | 12.0 | 17.39 | 29.92 | **8.0** | 12.0 | 80.31 | 0.334 (immature: C<19.5) | **26.82** | true | true | false | 84, all N×N (80/252/500) |
| model | 1.0 | 12.0 | 17.41 | 29.92 | **4.8** | 12.0 | 77.13 | 0.334 (immature: C<19.5) | **25.76** | true | false | **true** | 84, all M×M (600/1800/4480) |

\* B, D and F are fixture-driven and identical in both arms.

- The hidden-case metrics agree to within numerical noise. For example, negative_small L1
  has RMSE ratio 0.982 and IoU 0.376 in both arms.
- There were no timeouts. The model form's medium cases took about 30 s each, against 4 s for the data form.
- The data arm is not better science than the model arm. It differs only in the shape of the matrix passed to `eigh`.

**Counterfactual through the evaluator's own `structural_penalty_v34`.** This applies the
penalty function to each arm's native breakdown with only the C score replaced. It is
derived, not executed end to end.

| C | data arm: penalty → total | model arm: penalty → total |
|---|---|---|
| 20 | 0.5 → 41.46 | 0.5 → 39.86 |
| 26 | **1.0 → 88.92** | **0.5 → 42.86** |
| 30 | 1.0 → 92.92 | 0.5 → 44.86 |

## Refutation attempts

- **Is the model form honest and equivalent?**
  - Yes. Same file, same math, one constant changed.
  - The judge-run hidden metrics are equal to within floating-point noise.
  - It satisfies every other monitor check: `uses_proper_logdet`, `beta_truly_updated`, no `det`, and `valid_for_selection=true`.
- **Does the gate matter for scores?**
  - It always removes 3.2 of 100 raw points (E1's 4 points × 0.8).
  - It removes 50% of the score only in the strong tier. With this implementation (C≈17.4) that tier was not reached. The observed effect in this run was therefore −1.06 points.
  - Whether real solvers reach C ≥ 26 is unknown.
- **Was the defect reached through the real harness?** Yes. It went through the verbatim eval_cmd in the pinned image, with no fixture in the gate path.

## Disposition assessment

- This confirms the contract mismatch the triage reported. The narrowing: the 0.5× cap is
  a ceiling that binds only for strong submissions, while a smaller, always-on loss of
  3.2 raw points applies at every tier.
- This finding alone would support "repair" rather than exclusion. The smallest fix is either:
  - drop `not is_data_space` from `structural_failure` and E1, or
  - disclose in the prompt that data-space is required, matching README line 5.
- The triage's **exclude original** recommendation also rests on B and D (42 points) being
  self-reported and on in-process execution of the submission. Those concerns are unaffected
  by this run. The exclude recommendation stands.

## Recommended publishable wording

"The prompt lets solvers choose a model-space or data-space D-ABIC. The evaluator, however,
classifies the form by the shape of the matrices passed to the log-determinant routines.
It denies any model-space implementation 3.2 points and the uncapped score tier, so a
strong model-space solution is capped at half the score of an otherwise identical
data-space one."

## Limits

- This is one honest implementation, and it is moderate (C 17.4/35). The strong-tier
  effect is computed with the evaluator's penalty function on native breakdowns, not
  observed with a strong submission.
- B, D and F are fixtures. No Vinton or synthetic inversion was run for them.
- There was one run per arm. Hidden cases use fixed seeds.
