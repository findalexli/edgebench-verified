# college_english_exam_bank

## Claim

- (C1) The fixed grader gives exactly the original total for every assessment it accepts.
- (C2) It never scores an assessment that leaves out a rubric rule: such an assessment becomes a grading failure (`valid: false`). The re-ask loop returns a score only from an accepted attempt.
- (C3) On an accepted assessment, a rule whose row reports a deduction cannot get full marks. A row reports a deduction when its numeric score is below max, or when one of its checkpoints is positive.

## Model and link to the code

`evidence/formal/lean/ebv/Ebv/CollegeEnglishGrader.lean`, core Lean only. The model covers:

- `_validate_result` normalisation;
- the deductive branch of `reconcile_result_with_rubrics`;
- the pre-checks of the earlier fixed grader (`precheck`, `fixed`) and of the revised one (`precheck2`, `fixed2`);
- the re-ask loop (`fixedRun`, `fixedRun2`).

The header gives line numbers and sha256 values (original `b8b2824c…`, earlier fixed grader `1d941b58…`, revised fixed grader `87f0e340…`, rubric `d05f344e…`). The real 12-rule rubric is encoded in half-points. Differential check: `decide` reproduces the recorded paired results for responses A, B, C, D, E, F, G, I, L, J and K under all three graders (original 77/0/100/81/15/0/0/15/77). `probes/college_english_exam_bank/probe.py` runs the real functions on the gap cases below: `probe.out` with the earlier fixed grader, `probe-after-fix.out` with the revised one.

## Result

**Proved for the revised fixed grader (2026-10-12). The earlier fixed grader was narrower than published.**

### Earlier fixed grader (`1d941b58…`, superseded)

C1 and C2 are proved for all inputs. C3 is proved only when three gaps are excluded (`NoGap`). In each gap, the earlier fixed grader still awards full marks to a row with score 0 and all-zero checkpoints, and the real code confirms it (`probe.out`):

- **A (most plausible):** the rule has `veto_conditions`, and the veto is stated only in `veto_reason`, with `rule_veto_triggered` left at the prompt template's default `false`. The pre-check reads the raw row, sees a veto, and skips the rejection. `_validate_result` drops `veto_reason` when the flag is false (l.1207), so reconcile sees no veto and awards full marks. Example: R001 receives 3/3 (`gapA_full_marks`).
- **B:** an extra checkpoint beyond the rubric's details carries the deduction. The pre-check counts it; reconcile ignores it.
- **C:** `rule_veto_triggered=true` on a rule that has no `veto_conditions`.
- **D (probe only):** the floor wording appears after character 200 of `reason`, which `_validate_result` truncates.

All four come from one root cause: the pre-check exempts on the raw row, but reconcile reads the normalised row. Omitted rules, the headline defect, were fully fixed.

### Revised fixed grader (`87f0e340…`)

The deduction check now runs at the end of `_validate_result` on the normalised rows: it reconciles them exactly as scoring does, and rejects the assessment when a deductive rule's row reports a deduction (numeric score below max, or a positive checkpoint) but reconciles to full marks. The shape checks are unchanged.

- C1, C2 and the re-ask soundness are proved again (`fixed2_eq_orig`, `fixed2_rejects_unassessed`, `fixedRun2_sound`).
- **C3 is proved for all inputs, with no gap exclusion** (`fixed2_no_unearned_full_marks`). The core lemma `recordedWith_sound` holds for any per-row scorer, so it uses no property of the modelled normalisation; it therefore also covers gap D (truncation), which the model does not represent, because the code decides with the same functions that produce the score.
- **Nothing else changes outside the gaps** (`precheck2_of_precheck`): every assessment the earlier fixed grader accepted, with no gap row, is accepted by the revised one, with the same (original) total. `differential2` reproduces the recorded results for A–L.
- Gaps A–C are rejected (`gaps_rejected2`). The probe confirms A–D on the real code (`probe-after-fix.out`).
- One earlier side effect is gone: a row with score 0, a negative checkpoint and a veto marker (row M) was rejected by the earlier fixed grader although the original scores it 0 as a veto. The revised grader accepts it with 0, the original total (`respM_results`).

## Counter-check

- `orig_empty_is_100`: the original scores an empty assessment 100.
- `orig_unassessed_full`: for any rubric, the original gives full marks to a rule with no row.
- `gapA_full_marks`, `gapB_full_marks`, `gapC_full_marks`: the earlier fixed grader awards full marks in gaps A–C.
- `overstrong_claim_false`: for the earlier fixed grader, C3 without `NoGap` is false.

## Limits

- Text fields are abstracted to booleans. Non-dict checkpoints, the model's own `max_score` beyond clamping, and JSON block selection are not modelled; the original and fixed graders can pick different blocks when the last JSON block is incomplete.
- C3 is about the rules the rubric marks `deductive` (all 12 here); the check does not cover additive or penalty rules.
- A random differential run on the real functions (`probes/college_english_exam_bank/fuzz.py`, 20,000 assessments, `fuzz.out`) found no accepted assessment whose total differs from the original and no violation of C3 under the revised grader. The revised grader rejects 1,472 assessments the earlier one accepted (each has a row in the C3 failure pattern) and accepts 276 the earlier one rejected (its raw-row test fired although reconciliation does not give full marks, as in row M), all with the original total. It is a test, not a proof.
