# college_english_exam_bank v2: paired offline evaluation

## Job

- **Run:** one E2B worker (`sandbox iy7agj4pn02655jn16bco`) ran `run.sh` in 61 s, exit 0, then was killed by its exact ID.
  Raw captures are in `result/out/`.
- **v1:** the original judge `seededge/edgebench.judge.college_english_exam_bank@sha256:8e9eec10…`.
  In-image `grade_with_codex.py` is `b8b2824c…` and `rubrics.json` is `d05f344e…`.
- **v2:** built in the worker from `v2ctx/Dockerfile` (image `sha256:fc67e54a3c84…`).
  In-image grader is `1d941b58…`, the fixed grader at that time (superseded on 2026-10-12, see the revision section below). `rubrics.json` is unchanged.

## Method

- **Command:** each fixed response runs the original eval_cmd through the TaskSpec-generated
  `eval.sh`, with `--network none`.
- **Model stand-in:** only the `codex` executable is replaced, by `fake_codex.sh`. It prints
  response k on call k and counts its calls. No model API or credential was used; dummy key
  strings get past the credential check.
- **Responses:** generated from the in-image `rubrics.json` by the reviewer's
  `make_responses.py` (A–I), plus `make_responses_v2.py` (L).
- **J and K** are two-call sequences that test the re-ask path.
- **Grading:** the captures were graded offline by `grade.py` with this repo's
  `sforge/harness/grading.py` and `selection.py`. This task has no `rescale`, so the
  normalized score is the raw 0–100 score.

## Paired table

| Fixed response | Role | v1 valid | v1 score | v2 valid | v2 score | v2 model calls | v1 = v2 output |
| --- | --- | --- | ---: | --- | ---: | ---: | --- |
| A all 12 rules, one deduction each | valid control | true | 77 | true | 77 | 1 | byte-identical |
| B all 12 rules floored to 0 | valid control (bad work) | true | 0 | true | 0 | 1 | byte-identical |
| F R009 rule-level score 0, no checkpoints | valid control | true | 0 | true | 0 | 1 | byte-identical |
| L A without any rule-level score (complete checkpoints) | valid control | true | 77 | true | 77 | 1 | byte-identical |
| C empty `scores` | **trigger** | **true** | **100** | false (grading failure) | – | 2 | – |
| D A minus R009 | **trigger** | **true** | **81** | false | – | 2 | – |
| E B minus R009 | **trigger** | **true** | **15** | false | – | 2 | – |
| G R009 row with no score and no checkpoints | trigger (malformed row) | true | 0 | false | – | 2 | – |
| I R009 score 0 with all-zero checkpoints | **trigger (caveat b)** | **true** | **15** | false | – | 2 | – |
| H no JSON | invalid control | false | – | false | – | 2 | same structured result |
| J D, then A on re-ask | re-ask recovers | true | 81 | true | 77 | 2 | – |
| K no JSON, then A on re-ask | re-ask recovers | false | – | true | 77 | 2 | – |

"–" means the harness exposes no score: `_invalidate` sets `score=None` and the entry is
excluded from selection.

## Selection effect (harness `score_first`)

```
history ['A_complete_one_deduction_each', 'C_empty_scores'] v1 (score_first): best_round=C_empty_scores best_score=100.0 best_valid=True
history ['A_complete_one_deduction_each', 'C_empty_scores'] v2 (score_first): best_round=A_complete_one_deduction_each best_score=77.0 best_valid=True
history ['A_complete_one_deduction_each', 'D_A_minus_R009'] v1 (score_first): best_round=D_A_minus_R009 best_score=81.0 best_valid=True
history ['A_complete_one_deduction_each', 'D_A_minus_R009'] v2 (score_first): best_round=A_complete_one_deduction_each best_score=77.0 best_valid=True
history ['B_complete_all_zero', 'I_B_R009_score0_zero_checkpoints'] v1 (score_first): best_round=I_B_R009_score0_zero_checkpoints best_score=15.0 best_valid=True
history ['B_complete_all_zero', 'I_B_R009_score0_zero_checkpoints'] v2 (score_first): best_round=B_complete_all_zero best_score=0.0 best_valid=True
```

## Spec checks

- **Triggers.** Under v1, omitted or contradictory rows silently become full marks: C gives 100,
  D gives 81 instead of 77, E and I give 15 instead of 0. Each is reported valid and wins
  selection. Under v2 each of these is re-asked once and then reported `valid=false`, which
  the harness excludes rather than counting as the solver's 0. When the re-ask returns a
  complete assessment, v2 scores it (J, K).
- **Valid controls.** A, B, F and L give byte-identical structured results and identical scores,
  with one model call in v1 and v2.
- **Invalid control.** Unparseable output (H) is invalid in both versions. v2 re-asks once
  first.
- **Verdict:** **accepted.**

## Not run

- No live grading model was used.
- A real 22-file submission was not graded; the fixed responses do not read it.
- The harness `judge_server` was not run live. Grading and selection used the repo code
  offline on the saved captures.

## Revision (2026-10-12): the deduction check reads what reconciliation reads

**Why.** A formal check (`evidence/formal/notes/college_english_exam_bank.md`) found that the
earlier fixed grader (`1d941b58…`, the "v2" above) decided its deduction check (caveat b) on
the raw row, while reconciliation scores the normalised row from `_validate_result`. Four
rows that report a deduction therefore still got full marks: (A) the veto stated only in
`veto_reason` with `rule_veto_triggered=false`; (B) the deduction in an extra checkpoint
beyond the rubric's details; (C) `rule_veto_triggered=true` on a rule without
`veto_conditions`; (D) the floor wording after character 200 of `reason`.

**Change.** `_require_recorded_deductions` now runs at the end of `_validate_result`: it
reconciles the normalised rows with the unchanged `reconcile_result_with_rubrics` and rejects
the assessment when a deductive rule's row reports a deduction (numeric score below max, or a
positive checkpoint) but reconciles to full marks. The shape checks and the re-ask loop are
unchanged. Revised grader: `87f0e340…` (98445 B); `repair.patch`, `materialize.sh` and
`source-lock.json` regenerated with `tools/make_materialize.py`, and a clean-copy
`./materialize.sh` reproduced the file byte for byte.

**Job.** `evidence/runs/college_english_exam_bank-v2-paired-fix2/`: one E2B worker
(`sandbox ienavt7ep9ffuybau8nap`), `run.sh` exit 0 in 41 s, worker killed by its exact ID.
Three arms on the same responses: v1 original (`b8b2824c…`), v2prev the earlier fixed grader
(`1d941b58…`, built from `v2prevctx/`) and v2 the revised grader (`87f0e340…`, built from
`v2ctx/`); `rubrics.json` `d05f344e…` in all three. New responses from
`make_responses_gaps.py`: GA–GD (gaps A–D, each built from B by changing one row) and M (R001
score 0 with a negative checkpoint and a veto marker in `reason`). Graded with `grade.py`
(output in that job's `graded.md`).

| Fixed response | v1 valid | v1 score | v2prev valid | v2prev score | v2 valid | v2 score | v2 model calls | v1 = v2 output |
| --- | --- | ---: | --- | ---: | --- | ---: | ---: | --- |
| A all 12 rules, one deduction each | true | 77 | true | 77 | true | 77 | 1 | byte-identical |
| B all 12 rules floored to 0 | true | 0 | true | 0 | true | 0 | 1 | byte-identical |
| C empty `scores` | true | 100 | false | – | false | – | 2 | – |
| D A minus R009 | true | 81 | false | – | false | – | 2 | – |
| E B minus R009 | true | 15 | false | – | false | – | 2 | – |
| F R009 rule-level score 0, no checkpoints | true | 0 | true | 0 | true | 0 | 1 | byte-identical |
| G R009 row with no score and no checkpoints | true | 0 | false | – | false | – | 2 | – |
| H no JSON | false | – | false | – | false | – | 2 | same structured result |
| I R009 score 0 with all-zero checkpoints | true | 15 | false | – | false | – | 2 | – |
| J D, then A on re-ask | true | 81 | true | 77 | true | 77 | 2 | – |
| K no JSON, then A on re-ask | false | – | true | 77 | true | 77 | 2 | – |
| L A without any rule-level score | true | 77 | true | 77 | true | 77 | 1 | byte-identical |
| **GA** R001 veto only in `veto_reason` | **true** | **3** | **true** | **3** | false | – | 2 | – |
| **GB** R009 deduction in an extra checkpoint | **true** | **15** | **true** | **15** | false | – | 2 | – |
| **GC** R009 veto flag, rule has no veto conditions | **true** | **15** | **true** | **15** | false | – | 2 | – |
| **GD** R009 floor wording after character 200 | **true** | **15** | **true** | **15** | false | – | 2 | – |
| M R001 negative checkpoint + veto marker | true | 0 | false | – | true | 0 | 1 | byte-identical |

Selection (`score_first`) on history [B, GA]: v1 and v2prev pick GA at 3.0; v2 picks B at 0.0.

**Spec checks.**

- **Earlier arms unchanged.** For A–L the revised grader's structured results are identical to
  the earlier fixed grader's, and the raw capture of A is byte-identical to the earlier
  repeat run (`college_english_exam_bank-v2-paired-rep3`).
- **Gaps closed.** GA–GD are valid with full marks for the changed rule under the original and
  the earlier fixed grader, and are re-asked once and then reported `valid=false` by the
  revised grader.
- **Side effect removed.** M was a grading failure under the earlier fixed grader although its
  row is consistent with a veto; the revised grader scores it 0, byte-identical to the original.
- Formal result: C3 (no full marks for a rule whose row reports a deduction) is now proved in
  Lean for all inputs, without the gap exclusion (`fixed2_no_unearned_full_marks`).

**Verdict:** **accepted** (revised grader `87f0e340…`).

## Repeatability of the revised grader

The revised side-by-side job was run three times on fresh E2B workers (`evidence/runs/college_english_exam_bank-v2-paired-fix2`,
`-fix2-rep2`, `-fix2-rep3`). The graded results (`graded.json`) are identical in all three runs, apart from timing fields:
every arm keeps its validity and score under the original, the earlier fixed and the revised grader.
