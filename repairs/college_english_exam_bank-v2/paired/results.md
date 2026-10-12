# college_english_exam_bank v2: paired offline evaluation

## Job

- **Run:** one E2B worker (`sandbox iy7agj4pn02655jn16bco`) ran `run.sh` in 61 s, exit 0, then was killed by its exact ID.
  Raw captures are in `result/out/`.
- **v1:** the original judge `seededge/edgebench.judge.college_english_exam_bank@sha256:8e9eec10…`.
  In-image `grade_with_codex.py` is `b8b2824c…` and `rubrics.json` is `d05f344e…`.
- **v2:** built in the worker from `v2ctx/Dockerfile` (image `sha256:fc67e54a3c84…`).
  In-image grader is `1d941b58…`, the same as `files/`. `rubrics.json` is unchanged.

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
