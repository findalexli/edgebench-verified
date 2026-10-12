# College English exam bank (`college_english_exam_bank`)

**Outcome:** Fixed. <mark>The original grader gave full marks for any rubric rule that the AI grading model did not assess, and still reported the result as valid.</mark>

![Bars show the original grader scoring an empty assessment 100, and assessments with one rule left out 81 instead of 77 and 15 instead of 0; the fixed version rejects all three.](figures/college_english_exam_bank.svg)

*When the AI grader skipped rules, the original grader gave those rules full marks and called the result valid; the fixed version rejects incomplete assessments.*

## What the task asks

The solver is told to "Read the complete task instructions in `/home/workspace/task_instruction.md`". Those instructions ask for 22 deliverables: five exam papers (A to E) as Word and PDF files, answer keys and scoring guides, a blueprint workbook and a workbook of repetition rates across papers. An AI grading agent (a large language model) scores the work against `rubrics.json`. That file has 12 rules (R001 to R012) worth 100 points in total. Every rule is `deductive`: it starts at full marks and loses points for faults found. The grader's prompt tells the grading model to use the `rules` array strictly as the scoring list and not to add, delete or merge rules. The docstring of the grader's reconciliation step says "Force result coverage/order/max_score to match rubrics.json". Category: Professional Knowledge Work.

## What goes wrong

**Rules left out get full marks.** When a rule's row is missing from the grading model's JSON answer, the reconciliation step finds no recorded deductions. Because every rule is deductive, the rule keeps its full maximum. The grader writes the reason "Missing deductive detail scores; unreported deduction triggers treated as not triggered." and reports `grader_status: ok`, `valid: true`.

| Fixed model response | Expected | Result on the original grader |
| --- | --- | --- |
| C: `{"scores": []}` (no rule assessed) | grading failure | valid, **100.0** |
| D: response A (77.0) with R009 (15 pts) left out | 77 or failure | valid, **81.0** (R009 → 15/15) |
| E: response B (0.0) with R009 left out | 0 or failure | valid, **15.0** (R009 → 15/15) |

**A self-contradicting row gets full marks.** Case I is a row whose own `score` is 0 but whose checkpoints all report no deduction. The original reconciliation step trusts the checkpoints and awards the rule full marks (15.0 instead of 0).

**When it happens.** The problem needs the grading model to return JSON that parses but lacks some rule rows. One example is a truncated or abandoned assessment of a heavy 22-file submission. The grader's prompt itself anticipates the model running short of time or context. That a solver could cause an omission is plausible but not demonstrated. The fault is in fixed post-processing code owned by the task, which fails open when the model's output is incomplete.

## How much it matters

A score can rise by up to the value of the rules left out; an empty assessment scores 100. For this task the error only pushes scores up, because its rubric has no additive rules (rules that start at zero, which would push scores down instead). Any submission can be affected whenever the grading model returns an incomplete assessment.

## The fix

The fixed version changes only `/home/workspace/scoring/grade_with_codex.py`:

- It rejects score lists that are incomplete, duplicated, unknown or non-numeric. A row may leave out the rule-level score when it has a complete numeric list of checkpoints, which the original version scored correctly.
- It rejects a deductive row whose score contradicts an all-zero list of checkpoints (case I).
- An incomplete assessment becomes a grading failure (`valid: false`). The harness drops such an entry from selection rather than counting it as the solver's 0. Scoring a missing rule at zero was not chosen, because it would turn an upward error into a downward one.
- Because the harness does not retry, the fixed version asks the grading model again before giving up. It makes at most `1 + SEBENCH_CODEX_ASSESSMENT_RETRIES` calls (default 2), all within the original time budget.

The rubric, reference attachments and work image are unchanged. In `task.json.in` only `judge.image_tag` changes.

| Fixed model response | Role | Original: valid | Original: score | Fixed: valid | Fixed: score | Fixed: model calls | Original = fixed output |
| --- | --- | --- | ---: | --- | ---: | ---: | --- |
| A all 12 rules, one deduction each | correct test submission | true | 77 | true | 77 | 1 | byte-identical |
| B all 12 rules floored to 0 | correct test submission (bad work) | true | 0 | true | 0 | 1 | byte-identical |
| F R009 rule-level score 0, no checkpoints | correct test submission | true | 0 | true | 0 | 1 | byte-identical |
| L A without any rule-level score (complete checkpoints) | correct test submission | true | 77 | true | 77 | 1 | byte-identical |
| C empty `scores` | **shows the problem** | **true** | **100** | false (grading failure) | – | 2 | – |
| D A minus R009 | **shows the problem** | **true** | **81** | false | – | 2 | – |
| E B minus R009 | **shows the problem** | **true** | **15** | false | – | 2 | – |
| G R009 row with no score and no checkpoints | shows the problem (malformed row) | true | 0 | false | – | 2 | – |
| I R009 score 0 with all-zero checkpoints | **shows the problem (caveat b)** | **true** | **15** | false | – | 2 | – |
| H no JSON | invalid test submission | false | – | false | – | 2 | same structured result |
| J D, then A when asked again | asking again recovers | true | 81 | true | 77 | 2 | – |
| K no JSON, then A when asked again | asking again recovers | false | – | true | 77 | 2 | – |

"–" means the harness exposes no score: the entry is marked invalid and left out of selection. The harness uses `score_first` selection: the run keeps the submission with the highest score. Under it, the original version picks the inflated round (C at 100, D at 81, I at 15) over the honest one. The fixed version picks the honest one (77, 77, 0).

**Are scores comparable?** The original and fixed versions give the same score for complete, internally consistent assessments (rows A, B, F, L). Those come from byte-identical structured results and one model call. The scores are not comparable when the grading model leaves out, duplicates or invents a rule. They are also not comparable when it returns a row with neither a score nor a complete list of checkpoints, or a deductive row whose score contradicts all-zero checkpoints. The original version filled those cases with full marks. The fixed version asks again and otherwise reports a grading failure.

## How we checked it

- **Original grader, from the public image pinned by digest.** The original `main()` ran end to end with `--network none --memory 2g --cpus 1`. Only the `codex` executable was replaced, by a stub that prints a fixed model response. No model API or credential was used. The fixed responses were generated from the original `rubrics.json`. They include correct responses, responses for known-bad work and the responses that show the problem (rules left out, an empty score list, malformed rows). The fixed-version runs used the same eval_cmd in the fixed image.
- **Harness check.** The repository harness's handling of `valid: false` (`sforge/harness/grading.py`, `selection.py`) was read and used offline to grade and select on the saved results.
- **Repeatability.** The side-by-side run of the original and fixed graders was repeated three times. No response changed its result (see `data/paired-repeatability.md`).

## Limits

- No AI solver was run. Effects are shown only on the fixed responses and counterexamples we wrote.
- No live grading model was used. How often real models leave out rows, and whether any past EdgeBench score was inflated, were not measured. The problem is not evidence that past scores were inflated.
- No real 22-file submission was graded. The fixed responses do not read the submission.
- The harness `judge_server` was not run live.
- In production, asking again may cost extra paid grading calls. Whether a second attempt is usually complete is unknown. A model that keeps returning incomplete output still yields no measurement for that submission.
- Other risks of AI graders (prompt injection, grading variance) are out of scope.

## Reproduce

- Grader image: `sha256:8e9eec10…`.
- Fixed-response run on the original grader: `evidence/scripts/college_english_exam_bank/run_fixed.sh`, with `fake_codex.sh` and `make_responses.py` (log: `run_in_judge_image.log`).
- Side-by-side run of the original and fixed graders: `repairs/college_english_exam_bank-v2/paired/run.sh` (`repairs/college_english_exam_bank-v2/` is the folder holding the fixed version). Results are in `paired/results.md`, and the offline harness grading is in `paired/grade.py`.
- Fix: `repairs/college_english_exam_bank-v2/repair.patch`, `Dockerfile`, `source-lock.json`.
- Supporting records: `repairs/college_english_exam_bank-v2/` and `evidence/reviews/college_english_exam_bank.md`.
