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

### Design decisions (review caveats a and b, edge cases e2 and e1)

**(a) What happens to an invalid grading result.** EdgeBench's harness (`sforge` at `6e4e5f4`) keeps a
`valid: false` result's score: `_grade_structured` copies `score` (0 here), and the task's `score_first`
selection ranks it without looking at `valid` (`sforge/harness/grading.py:200-217`,
`sforge/harness/selection.py:83-103`). A grading failure therefore counts as 0 for that submission. The run
still keeps its best other submission, so a failure can only cost the solver that one submission's score; if
every submission of a run fails grading, the run's result is 0.

The original grader already reports grading-side failures (model timeout, invocation failure, JSON that does
not parse) the same way, as `valid: false` with score 0. Missing deliverables are scored through the rubric.
The fixed version reuses that channel. It does not score a missing rule at zero inside an otherwise scored
assessment, because that would silently understate a complete answer.

The harness does not retry a failed grading. For that reason the fixed version also **asks the grading model
again** before giving up:

- It makes at most `1 + SEBENCH_CODEX_ASSESSMENT_RETRIES` calls (the variable defaults to 1, so 2 calls).
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
before `_validate_result` normalised it. Four rows still got full marks (the Lean model found
the first three, a probe of the real code the fourth): a veto stated only in `veto_reason` while `rule_veto_triggered` is false, a deduction in
an extra checkpoint beyond the rubric's details, a veto flag on a rule without veto conditions,
and floor wording after character 200 of `reason`. Each of these is dropped or ignored by
normalisation or reconciliation. The check now reads the normalised rows, which closes all four.

**(c) Which JSON block is scored (review edge case e2, revision v2.2, 2026-10-13).** The grading
prompt's step 5 asks the model to check its work and then output the corrected final JSON. A model
output can therefore hold a draft block followed by the final one. The original grader scores the
last block that has `scores`. Version v2.1 skipped a last block that failed its checks and scored an
earlier block that passed, without asking again. That earlier block may be the draft from before the
model's own check, so its score can be higher or lower than the model's final assessment (row NZ in
`paired/results.md`: a full-marks draft before an incomplete final block scored 100 under v2.1).
The fixed version now follows the original's rule that the last `scores` object decides:

- If the last block parses and passes the checks, it is scored, as in the original.
- If the last block parses but fails the checks, the output has no usable assessment. The fixed
  version asks again once (the same bounded re-ask as in (a)) and otherwise reports a grading failure.
  It never scores an earlier block in this case.
- Only if the last block is truncated, does not parse, or is not a `scores` object does it fall back
  to the latest earlier block, as the original also does. A truncated block is not an assessment the
  model can have meant as final, while a block that parses is the model's last word.

The same rule applies to the unfenced fallback that scans the output for raw JSON objects.

**(d) A rule score written as a number in a string (review edge case e1, revision v2.2).** Version
v2.1 rejected a row whose rule `score` was not a JSON number, even when its checkpoint list was
complete and consistent, although the original scores such a row correctly from its checkpoints.
That turned a correct score into a grading failure when the second answer had the same form. The
fixed version now reads a plain decimal string (`"12"`, `" 12.0 "`: optional sign, digits, optional
decimal point, surrounding spaces) as that number, but only when the row's checkpoint list is
complete; the converted number then goes through the same consistency check as a JSON number (b).
Everything else stays rejected: booleans (`true` is not a score), other strings (`"twelve"`, `"12分"`,
`"nan"`), and a decimal string on a row without a complete checkpoint list, where reconciliation
would have to trust the rule score itself.

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
5. **Added (v2.2).** `extract_json_from_output` lets the last `scores` object decide (c), through
   `_parse_scores_object` and `_validate_or_reject`.
6. **Added (v2.2).** `_require_complete_rule_scores` converts a plain decimal-string rule score on a
   row with complete checkpoints (`_decimal_string_value`) and returns the converted rows, which
   `_validate_result` then normalises and checks (d).
7. **Comment and message (v2.2).** The comment in `main()` now says what the harness does with a
   grading failure (ranked as 0 by `score_first`; the run keeps its best other submission), and a
   timeout of the second call reports that call's own time limit.

`task.json.in` changes only `judge.image_tag` (`6628b6d3f834` to `6628b6d3f834-ebv-v2.2`). Tags `6628b6d3f834-ebv-v2`
(v1.0 package, the first fix) and `6628b6d3f834-ebv-v2.1` (the revision of 2026-10-12) are superseded, because the
current grader scores differently; rebuild.

The Dockerfile is `FROM` the pinned digest of the original grader image plus one `COPY`. The rubric, the
reference attachments and the work image are unchanged. Hashes are in `source-lock.json`.

### Are scores comparable?

Complete, internally consistent assessments produce byte-identical structured results and the
same score in the original and fixed versions, with one model call (rows A, B, F, L). Scores from the fixed version are not comparable with
the original when the grading model:

- leaves out, duplicates or invents a rule;
- gives a row with neither a score nor a complete list of checkpoints;
- or gives a deductive row that reports a deduction but would be scored at full marks;
- or ends its output with a `scores` block that fails these checks, after an earlier block (c);
- or gives a rule score that is a boolean or a string that is not a plain decimal number, or a
  decimal string on a row without a complete checkpoint list (d).

The original version scored the first four cases with silently filled full marks (in the fourth it
scores the failing last block, row N: 81). It scored rows of the last kind from their checkpoints or
rule score (rows QC, QD, QF in `paired/results.md`: 77, 77 and 0, correctly). For that last kind the
fixed version turns a correct score into a grading failure if asking again does not help. Booleans
and words are not scores in the prompt's format, and a string score without checkpoints is the only
evidence for its rule, so we accept that cost rather than guess; how often a real model writes such
rows is not measured. A plain decimal-string rule score with complete checkpoints scores exactly as
the original (rows QA, QB: byte-identical). In the five listed cases the fixed version asks again
and otherwise reports a grading failure. Runs with a real model may make extra grading calls (paid API
cost) when the first assessment is incomplete.

## How it was checked

See `paired/results.md`. It is an offline run with fixed model responses and no model API. It uses the original
eval_cmd in the original image and in the image built from this Dockerfile. **Accepted.**

In plain words: complete, consistent responses (A, B, F, L) give byte-identical results and the same scores (77, 0, 0, 77) under both graders. The responses that show the problem (an empty list, a rule left out, or a self-contradicting row) are reported valid with inflated scores by the original grader (100, 81, 15) and as grading failures by the fixed one. When the model's second answer is complete, the fixed grader recovers the honest score of 77.

The revision was checked the same way, three times on fresh workers with identical graded results
(`evidence/runs/college_english_exam_bank-v2-paired-fix2`, `-fix2-rep2`, `-fix2-rep3`), with the original grader, the first
published fixed version and the revised one side by side (`paired/results.md`, revision
section). All earlier responses give the same results as before. The four rows get full marks for the changed rule under the original grader and the first fixed
version (3 or 15 points), and are grading failures under the revised one. A row that the first
fixed version rejected although the original scores it consistently (a veto, score 0) is now
scored 0, the same as the original.

Formal check (`evidence/formal/notes/college_english_exam_bank.md`, Lean 4): for every
parsed assessment the fixed version accepts, the score equals the original grader's, an assessment
that leaves out a rule is rejected, and a deductive rule whose row reports a deduction never
gets full marks. The last result holds for all inputs. It does not depend on how the Lean model
represents normalisation, because the check uses the same functions as the score.

The model starts from the parsed rows, so it does not cover which JSON block is parsed or the
decimal-string conversion; both were tested on the real code instead.

Revision v2.2 (2026-10-13) was checked the same way, three times on fresh workers with identical graded
results (`evidence/runs/college_english_exam_bank-v2-paired-fix3`, `-fix3-rep2`, `-fix3-rep3`), with
the original grader, the v2.1 fixed grader and the v2.2 one side by side on 29 responses
(`paired/results.md`, section "Revision v2.2"). In each run the package's own `materialize.sh`
regenerated the v2.2 grader from the pinned image and `repair.patch` (sha256 `a0af4360…`, as locked)
before the image was built. Every response of the earlier runs except N gives the same result and
the same structured output under v2.2 as under v2.1. The changed rows:

- A complete block followed by an incomplete one in one output (N) scores 81 under the original, 77
  under v2.1 (the earlier block, no second call) and is asked again under v2.2: a grading failure if
  the second answer is the same, 77 if the second answer is complete (NA). A full-marks draft before
  an incomplete block (NZ) scores 100 under v2.1 and fails under v2.2; the same holds for unfenced
  blocks (NU). A truncated last block (P) still falls back to the complete one: 77 in all three.
- A plain decimal-string rule score with complete checkpoints (QA, QB) scores 77 under the original
  and v2.2 (byte-identical structured result, one call) and was a grading failure under v2.1. A
  boolean, a word, an inconsistent "0" and a "0" without checkpoints (QC–QF) stay grading failures.

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
- As in the original, a fenced block takes priority over unfenced JSON: if a model writes a fenced
  draft and then an unfenced final JSON object, the fenced block is the one checked. This ordering is
  unchanged from the original and was not tested.
- Whether `codex exec` output in this image ever holds more than one `scores` block, and how often a
  real model writes a rule score as a string or boolean, are not measured.

- No live grading model was used. How often real models produce incomplete rows, and whether
  past scores were inflated, are not measured.
- Asking again costs extra paid calls in production. Whether a second attempt is usually complete
  is unknown.
- A model that keeps returning incomplete output still yields no measurement for that
  submission. This is now explicit, instead of silently becoming 100.
- Other risks of AI graders (prompt injection, grading variance) are out of scope.
