# College English exam bank, fixed version: an incomplete assessment is a grading failure, not full marks

## What this fixes

The task is graded by an AI model that scores 12 rubric rules, and the grader's own code then checks that answer against the rubric. In the original grader, any rule the model leaves out keeps full marks and the result is still reported as valid, so an empty assessment scores 100/100. The fixed version asks the model again and otherwise reports a grading failure; complete assessments score exactly as before.

## What changes

### The problem in detail

The grader `scoring/grade_with_codex.py` asks an AI agent (a large language model) for a JSON `scores` array covering
the 12 rubric rules (R001 to R012, all `deductive`, 100 points in total). A deductive rule starts at full marks and
loses points for faults found. Python code then reconciles that array against `rubrics.json`. When a rule's row is missing,
the reconciliation finds no recorded deductions and gives the rule its full maximum. The result is still labelled
`valid: true`. With a fixed empty response (`{"scores": []}`) the original grader returns
100/100. A related remaining path has the same effect. Suppose a row's own `score` says points
were deducted, but every checkpoint is reported as not triggered. The reconciliation trusts the
checkpoints and again awards full marks. Review: `evidence/reviews/college_english_exam_bank.md`.

### Design decision (review caveats a and b)

**(a) What happens to an invalid grading result.** The repository's harness was checked:
`sforge/harness/grading.py::_grade_structured` and `sforge/harness/selection.py`.

- A grader result with `valid: false` goes through `_invalidate`, which sets `score = None` and
  `pass_rate = 0`.
- `_completed_submissions` then drops the entry from every selection policy.
- It is not counted as the solver's 0. It is simply not a measurement.

This grader already uses `valid: false` only for failures on the grading side: model timeout, invocation
failure and JSON that does not parse. Missing deliverables are scored through the rubric. So `valid: false`
is already this task's channel for "grading infrastructure failure", and the fixed version reuses it.

The harness does not retry a failed grading. A grading failure on a solver's only or last
submission would therefore leave that run with no measurement. For that reason the fixed version also **asks
the grading model again** before giving up:

- It makes at most `1 + SEBENCH_CODEX_ASSESSMENT_RETRIES` calls (default 2).
- It asks again only while at least 120 s of the original `--timeout` budget remain.
- Later calls get only the remaining budget, so total model time stays within the bound of the original version's single call.

Scoring the missing rule was rejected in both directions. Full marks is the problem itself. Zero would
turn an upward error into a downward one.

**(b) The path where a row reports a deduction but no checkpoint does.** A row reports a
deduction when its own rule `score` is below `max_score` or one of its checkpoints is positive.
The fixed version rejects an assessment when such a row, for a `deductive` rule, would still be
scored at full marks. To decide this it runs the original reconciliation step on the normalised
rows, so it looks at exactly the data that produces the score. A typical case is a row with
score 0 whose checkpoints all report no deduction: it contradicts the prompt's own rule 4a
(`score = max - min(sum deductions, max)`), and reconciling it would award full marks.

Rows that reconciliation already scores below full marks are left alone, for example a veto,
repeatable deductions or a "deductions reach the floor" reason. Rejecting them could invalidate
ordinary model outputs.

*Revision (2026-10-12).* The first published fixed version made this decision on the raw row,
before `_validate_result` normalised it. A formal check found four rows that still got full
marks: a veto stated only in `veto_reason` while `rule_veto_triggered` is false, a deduction in
an extra checkpoint beyond the rubric's details, a veto flag on a rule without veto conditions,
and floor wording after character 200 of `reason`. Each of these is dropped or ignored by
normalisation or reconciliation. The check now reads the normalised rows, which closes all four.

### Exact change (`repair.patch`, generated with `diff -u`)

Only `/home/workspace/scoring/grade_with_codex.py` changes.

1. The earlier proposed patch (`proposedrepairs/college-english-assessment-completeness/patch.diff`,
   sha256 `8560cdf6...`) is applied unchanged. The authoritative rules are passed to the parser,
   and `_require_complete_rule_scores` rejects lists that are incomplete, duplicated, unknown or
   non-numeric.
2. **Relaxed.** A row may leave out the rule-level `score` if it has a complete numeric list of
   checkpoints, because the original reconciliation step computes the score from the checkpoints. The earlier
   patch would have invalidated such outputs, which the original version scored correctly (row L in `paired/results.md`). The
   redundant re-check inside `reconcile_result_with_rubrics` was removed: it ran on normalized
   rows where a missing score had already become 0.
3. **Added.** `_require_recorded_deductions` covers caveat (b). It runs at the end of
   `_validate_result`, reconciles the normalised rows with the unchanged
   `reconcile_result_with_rubrics`, and raises when a deductive row that reports a deduction
   reconciles to full marks.
4. **Added.** The bounded loop in `main()` that asks again covers caveat (a). After it, the existing
   `emit_all_failed(..., status="json_parse_failed")` path reports `valid: false`.

`task.json.in` changes only `judge.image_tag` (`6628b6d3f834` to `6628b6d3f834-ebv-v2`).

The Dockerfile is `FROM` the pinned digest of the original grader image plus one `COPY`. The rubric, the
reference attachments and the work image are unchanged. Hashes are in `source-lock.json`.

### Are scores comparable?

Complete, internally consistent assessments produce byte-identical structured results and the
same score in the original and fixed versions, with one model call (rows A, B, F, L). Scores from the fixed version are not comparable with
the original when the grading model:

- leaves out, duplicates or invents a rule;
- gives a row with neither a score nor a complete list of checkpoints;
- or gives a deductive row that reports a deduction but would be scored at full marks.

The original version scored those cases with silently filled full marks. The fixed version asks again and otherwise reports a
grading failure. Runs with a real model may make extra grading calls (paid API cost) when the first
assessment is incomplete.

## How it was checked

See `paired/results.md`. It is an offline run with fixed model responses and no model API. It uses the original
eval_cmd in the original image and in the image built from this Dockerfile. **Accepted.**

In plain words: complete, consistent responses (A, B, F, L) give byte-identical results and the same scores (77, 0, 0, 77) under both graders. The responses that show the problem (an empty list, a rule left out, or a self-contradicting row) are reported valid with inflated scores by the original grader (100, 81, 15) and as grading failures by the fixed one. When the model's second answer is complete, the fixed grader recovers the honest score of 77.

The revision was checked the same way, on one worker, with the original grader, the first
published fixed version and the revised one side by side (`paired/results.md`, revision
section). All earlier responses give the same results as before. The four rows found by the
formal check get full marks for the changed rule under the original grader and the first fixed
version (3 or 15 points), and are grading failures under the revised one. A row that the first
fixed version rejected although the original scores it consistently (a veto, score 0) is now
scored 0, the same as the original.

Formal check (`evidence/formal/notes/college_english_exam_bank.md`, Lean 4): for every
assessment the fixed version accepts, the score equals the original grader's, an assessment
that leaves out a rule is rejected, and a deductive rule whose row reports a deduction never
gets full marks. The last result holds for all inputs. It does not depend on how the Lean model
represents normalisation, because the check uses the same functions as the score.

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t ebv/college_english_exam_bank-judge:v2 .
```

`materialize.sh` takes the following steps:

1. Pull the pinned image(s) by digest, unless already present.
2. Extract the original files with `docker create` and `docker cp`. No container runs in this step.
3. Check each original against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of every file under `files/` (and `orig/`) against `source-lock.json` → `materialize.outputs`. Any mismatch fails loudly.

After that, the `Dockerfile` builds without changes. Regenerated files keep the file mode they have in the image.
See `../MATERIALIZE-CHECK.md` for how each package was verified.

The task JSON change is in `task-json.diff`.

## Limits

- The deduction check covers rules the rubric marks `deductive` (all 12 in this task), not
  additive or penalty rules.

- No live grading model was used. How often real models produce incomplete rows, and whether
  past scores were inflated, are not measured.
- Asking again costs extra paid calls in production. Whether a second attempt is usually complete
  is unknown.
- A model that keeps returning incomplete output still yields no measurement for that
  submission. This is now explicit, instead of silently becoming 100.
- Other risks of AI graders (prompt injection, grading variance) are out of scope.
