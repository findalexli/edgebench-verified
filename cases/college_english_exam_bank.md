# College English exam bank (`college_english_exam_bank`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Professional Knowledge Work
- **Decision:** Repair v2. The original grader gave full marks for any rubric rule the grading model did not assess, and still reported the result as valid.

## What the task promises

The solver is told to "Read the complete task instructions in `/home/workspace/task_instruction.md`". Those instructions ask for 22 deliverables: five exam papers (A to E) as Word and PDF, answer keys and scoring guides, a blueprint workbook and a cross-paper repetition-rate workbook. An LLM grading agent scores the work against `rubrics.json`. That file has 12 rules (R001 to R012) worth 100 points in total, and every rule is `deductive`. The grader's own prompt to the grading model says to use the `rules` array strictly as the scoring list and not to add, delete or merge rules. The docstring of its reconciliation step says "Force result coverage/order/max_score to match rubrics.json".

## What we checked and how

- We ran the original `main()` end to end inside the pulled judge image (`--network none --memory 2g --cpus 1`). Only the `codex` executable was replaced, by a stub that prints a fixed model response. No model API or credential was used.
- Fixed responses were generated from the original `rubrics.json`. They included valid controls, known-bad controls and the trigger cases (omitted rules, an empty score list, malformed rows).
- We compared the in-image grader with an earlier grader copy used in prior examples. They differ only in credential and model environment-variable names. Every parsing, validation, reconciliation and scoring line is identical.
- We checked the repository harness's handling of `valid: false` (`sforge/harness/grading.py`, `selection.py`) for the repair design.
- Paired v1/v2 evaluation ran on one E2B worker, with the original eval_cmd in the original image and in the v2 image.
- Original identity: judge image `seededge/edgebench.judge.college_english_exam_bank@sha256:8e9eec10…`. Key files: `grade_with_codex.py` sha256 `b8b2824c…`, `rubrics.json` sha256 `d05f344e…`, task manifest sha256 `93e112ed…0406f`.

## What we found

**Confirmed.** When a rule row is missing from the grading model's JSON, reconciliation finds no recorded deductions. Because every rule is deductive, the rule then keeps its full maximum. The grader writes the reason "Missing deductive detail scores; unreported deduction triggers treated as not triggered." and reports `grader_status: ok`, `valid: true`.

Results from the original evaluator, with fixed model responses:

| Fixed response | Expected | Observed (original grader) |
| --- | --- | --- |
| C: `{"scores": []}` (no rule assessed) | grading failure | valid, **100.0** |
| D: control A (77.0) with R009 (15 pts) omitted | 77 or failure | valid, **81.0** (R009 → 15/15) |
| E: control B (0.0) with R009 omitted | 0 or failure | valid, **15.0** (R009 → 15/15) |

**Maximum score effect:** up to the value of the omitted rules. An empty assessment scores 100. The bias only ever points upward for this task, because additive rules (which would deflate) do not occur in its rubric.

**Related residual path (fixed in v2).** Case I: a row whose own `score` is 0 but whose checkpoints all report no deduction. The original reconciler trusts the checkpoints and awards the rule full marks (15.0 instead of 0). The earlier proposed patch left this path open; v2 closes it.

**Reachability.** The trigger needs the grading model to return parseable JSON that lacks some rule rows, for example a truncated or abandoned assessment of a heavy 22-file submission. The grader's prompt itself anticipates the model running short of time or context. We could not establish that a solver could induce an omission (it is plausible but was not demonstrated). How often real models do it was not measured. The defect is in deterministic, task-owned post-processing that fails open on incomplete model output.

**Earlier caveat re-checked.** The earlier 100-point examples used a different grader copy. Re-checking showed the two copies differ only in environment-variable names, and every result reproduces on the image copy.

## Repair

v2 changes only `/home/workspace/scoring/grade_with_codex.py`. It applies the earlier proposed completeness patch, which rejects score lists that are incomplete, duplicated, unknown or non-numeric. The patch is relaxed in one place: a row may omit the rule-level score when it has a complete numeric checkpoint vector, which v1 scored correctly. v2 also adds a check that rejects a deductive row whose score contradicts an all-zero checkpoint vector (case I). Scoring a missing rule at zero was rejected, because it would turn an upward bias into a downward one. Instead, an incomplete assessment becomes a grading failure (`valid: false`). The harness drops such an entry from selection rather than counting it as the solver's 0. Because the harness does not retry, v2 re-asks the grading model before giving up. It makes at most `1 + SEBENCH_CODEX_ASSESSMENT_RETRIES` calls (default 2), all within the original timeout budget. The rubric, reference attachments and work image are unchanged. In `task.json.in` only `judge.image_tag` changes.

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

"–" means the harness exposes no score: the entry is invalidated and excluded from selection. Under the harness's `score_first` selection, v1 picks the inflated trigger round (C at 100, D at 81, I at 15) over the honest control. v2 picks the control (77, 77, 0).

**Score compatibility.** v1 and v2 give the same score, from byte-identical structured results and one model call, for complete, internally consistent assessments (rows A, B, F, L). The scores are not comparable when the grading model omits, duplicates or invents a rule, returns a row with neither a score nor a complete checkpoint vector, or returns a deductive row whose score contradicts all-zero checkpoints. v1 filled those cases with full marks; v2 re-asks and otherwise reports a grading failure.

## Limits and what was not run

- No model or solver re-runs. Effects are shown on authored fixed responses and counterexamples only.
- No live grading model was used. How often real models omit rows, and whether any historical EdgeBench score was inflated, were not measured. Withholding the original is not evidence of inflated past scores.
- No real 22-file submission was graded. The fixed responses do not read the submission.
- The harness `judge_server` was not run live. Grading and selection used the repository code offline on the saved captures.
- In production, re-asking may cost extra paid grading calls. Whether a second attempt is usually complete is unknown. A model that keeps returning incomplete output still yields no measurement for that submission.
- Other LLM-grader risks (prompt injection, grading variance) are out of scope.

## Reproduce

- Original-grader fixed-response run: `evidence/scripts/college_english_exam_bank/run_fixed.sh`, with `fake_codex.sh` and `make_responses.py` (log: `run_in_judge_image.log`).
- Paired v1/v2 run: `repairs/college_english_exam_bank-v2/paired/run.sh`. Results are in `paired/results.md`, and the offline harness grading is in `paired/grade.py`.
- Repair: `repairs/college_english_exam_bank-v2/repair.patch`, `Dockerfile`, `source-lock.json`.

Supporting records: `repairs/college_english_exam_bank-v2/` and `evidence/reviews/college_english_exam_bank.md`.
