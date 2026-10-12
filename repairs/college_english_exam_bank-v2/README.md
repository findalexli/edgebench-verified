# college_english_exam_bank v2: an incomplete assessment is a grading failure, not full marks

## Defect

The grader `scoring/grade_with_codex.py` asks an LLM agent for a JSON `scores` array covering
the 12 rubric rules (R001 to R012, all `deductive`, 100 points in total). Python code then
reconciles that array against `rubrics.json`. When a rule row is missing, reconciliation finds
no recorded deductions and gives the rule its full maximum. The result is still labelled
`valid: true`. With a fixed empty response (`{"scores": []}`) the original grader returns
100/100. A related residual path has the same effect. Suppose a row's own `score` says points
were deducted, but every checkpoint is reported as not triggered. Reconciliation trusts the
checkpoints and again awards full marks. Review: `evidence/reviews/college_english_exam_bank.md`.

## Design decision (review caveats a and b)

**(a) What happens to an invalid grading result.** The repo harness was checked:
`sforge/harness/grading.py::_grade_structured` and `sforge/harness/selection.py`.

- An evaluator `valid: false` goes through `_invalidate`, which sets `score = None` and
  `pass_rate = 0`.
- `_completed_submissions` then drops the entry from every selection policy.
- It is not counted as the solver's 0. It is simply not a measurement.

This grader already uses `valid: false` only for grading-side failures: model timeout, invocation
failure and unparseable JSON. Missing deliverables are scored through the rubric. So `valid: false`
is already this task's "grading infrastructure failure" channel, and v2 reuses it.

The harness does not retry a failed judgement. A grading failure on a solver's only or last
submission would therefore leave that run with no measurement. For that reason v2 also **re-asks**
the grading model before giving up:

- It makes at most `1 + SEBENCH_CODEX_ASSESSMENT_RETRIES` calls (default 2).
- It re-asks only while at least 120 s of the original `--timeout` budget remain.
- Later calls get only the remaining budget, so total model time stays within the v1 single-call
  bound.

Scoring the missing rule was rejected in both directions. Full marks is the defect. Zero would
turn an upward bias into a downward one.

**(b) The zero-deduction residual path.** A `deductive` row is now rejected when all of these
hold:

- its checkpoint vector is complete;
- every checkpoint reports no deduction;
- no rule-level veto or "deductions reach the floor" reason applies;
- its own rule `score` is below `max_score`.

That row contradicts the prompt's own rule 4a (`score = max - min(sum deductions, max)`), and
reconciling it would award full marks. Narrower inconsistencies were deliberately left alone,
for example repeatable deductions or floor reasons the reconciler already handles. Rejecting
them could invalidate ordinary model outputs.

## Exact change (`repair.patch`, generated with `diff -u`)

Only `/home/workspace/scoring/grade_with_codex.py` changes.

1. The earlier proposed patch (`proposedrepairs/college-english-assessment-completeness/patch.diff`,
   sha256 `8560cdf6...`) is applied unchanged. The authoritative rules are passed to the parser,
   and `_require_complete_rule_scores` rejects lists that are incomplete, duplicated, unknown or
   non-numeric.
2. **Relaxed.** A row may omit the rule-level `score` if it has a complete numeric checkpoint
   vector, because the original reconciler computes the score from checkpoints. The earlier
   patch would have invalidated such outputs, which v1 scored correctly (row L below). The
   redundant re-check inside `reconcile_result_with_rubrics` was removed: it ran on normalized
   rows where a missing score had already become 0.
3. **Added.** `_require_recorded_deductions` covers caveat (b).
4. **Added.** The bounded re-ask loop in `main()` covers caveat (a). After it, the existing
   `emit_all_failed(..., status="json_parse_failed")` path reports `valid: false`.

`task.json.in` changes only `judge.image_tag` (`6628b6d3f834` to `6628b6d3f834-ebv-v2`).

The Dockerfile is `FROM` the pinned original judge digest plus one `COPY`. The rubric, the
reference attachments and the work image are unchanged. Hashes are in `source-lock.json`.

## Score compatibility

Complete, internally consistent assessments produce byte-identical structured results and the
same score in v1 and v2, with one model call (rows A, B, F, L). v2 scores are not comparable with
v1 when the grading model:

- omits, duplicates or invents a rule;
- gives a row with neither a score nor a complete checkpoint vector;
- or gives a deductive row whose score contradicts an all-zero checkpoint vector.

v1 scored those cases with silently filled full marks. v2 re-asks and otherwise reports a
grading failure. Real-model runs may make extra grading calls (paid API cost) when the first
assessment is incomplete.

## Paired evaluation

See `paired/results.md`. It is a fixed-response offline run with no model API, using the original
eval_cmd in the original image and in the image built from this Dockerfile. **Accepted.**

## Limits

- No live grading model was used. How often real models produce incomplete rows, and whether
  historical scores were inflated, are not measured.
- Re-asking costs extra paid calls in production. Whether a second attempt is usually complete
  is unknown.
- A model that keeps returning incomplete output still yields no measurement for that
  submission. This is now explicit instead of silently becoming 100.
- Other LLM-grader risks (prompt injection, grading variance) are out of scope.

## Build

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
