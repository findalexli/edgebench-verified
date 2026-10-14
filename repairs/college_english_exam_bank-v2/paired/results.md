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
- **Grading:** the captures were graded offline by `grade.py` with EdgeBench's
  `sforge/harness/grading.py` and `selection.py` (`6e4e5f4`). This task has no `rescale`, so the
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

"–" marks a grading failure: the grader reports `valid: false` with score 0 (shown as 0 in
`graded.md`). EdgeBench's `score_first` does not read `valid` and ranks that 0, which never beats a
graded submission.

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
  selection. Under v2 each of these is re-asked once and then reported `valid=false` with score
  0, which never beats the honest round under `score_first`. When the re-ask returns a
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
`veto_conditions`; (D) the floor wording after character 200 of `reason`. A–C were found in the
Lean model; D only by the probe of the real code (`probe.out`).

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

## Appendix: several JSON blocks in one model output (2026-10-12)

E2B job `evidence/runs/college_english_exam_bank-v2-paired-multiblock` (exit 0). Same harness and graders as
`-fix2` (pins: v1 `b8b2824c…`, v2prev `1d941b58…`, v2 `87f0e340…`). New responses come from `make_responses_multiblock.py`.

| Fixed response | v1 valid | v1 score | v2prev valid | v2prev score | v2 valid | v2 score | v2 model calls | v1 = v2 output |
| --- | --- | ---: | --- | ---: | --- | ---: | ---: | --- |
| A (control) | true | 77 | true | 77 | true | 77 | 1 | byte-identical |
| D (control) | true | 81 | false | – | false | – | 2 | – |
| **N** A's block, then D's block, one output | **true** | **81** | true | 77 | true | 77 | 1 | – |
| O D's block, then A's block, one output | true | 77 | true | 77 | true | 77 | 1 | byte-identical |
| P A's block, then a truncated block, one output | true | 77 | true | 77 | true | 77 | 1 | byte-identical |

The original grader scores the last block with `scores`. Both fixed graders skip a block that fails their checks and fall
back to the earlier complete block. The result is the honest 77, with no extra model call.

## Repeatability of the multi-block job (2026-10-13)

`evidence/runs/college_english_exam_bank-v2-paired-multiblock` was run three times on fresh E2B workers (`-rep2`, `-rep3`) with the same `run.sh`, responses and stand-in `codex`. Every run has `status: exit=0`. Each rerun's `graded.json` and `graded.md` were produced by the job's `grade.py` from that run's own `result/out/`. All 15 results (5 responses × original, earlier fixed and fixed grader) are identical to run 1's, and so are both files. The staged grader files (`v2ctx/files/`, sha256 `87f0e340…`; `v2prevctx/files/`, `1d941b58…`) were removed after collection.

## Revision v2.2 (2026-10-13): the last JSON block decides; decimal-string rule scores

**Why.** An independent review (GitHub issue #63) found two behaviours of the v2.1 grader
(`87f0e340…`) that did not follow the contract. (e2) When the last JSON block of an output failed
the checks, v2.1 scored an earlier block that passed, without asking again; that block can be a draft
from before the model's own check (row N in the appendix above). (e1) A rule score written as a
numeric string was rejected even when the row's checkpoints were complete and consistent, although
the original scores such a row correctly.

**Change.** Only the last `scores` object decides: if it parses but fails the checks, the grader asks
again once and otherwise reports a grading failure; it falls back to an earlier block only when every
later one is truncated, unparseable or not a `scores` object. A plain decimal-string rule score
(`"11"`, `" 11.0 "`) on a row with a complete checkpoint list is read as that number and then checked
like any number. Booleans, other strings, and decimal strings without a complete checkpoint list stay
rejected. The code comment that said the harness "excludes" a failed grading now says that
`score_first` ranks it as 0. Revised grader: `a0af4360…` (100451 B), tag `6628b6d3f834-ebv-v2.2`.

**Job.** `evidence/runs/college_english_exam_bank-v2-paired-fix3/`: one E2B worker (sandbox
`i2jrsmeeq41ds10gemfoz`), `run.sh` exit 0 in 61 s, worker killed by its exact ID. The v2 image was
built from a copy of this package: the package's own `materialize.sh` pulled the pinned image,
extracted the original grader, applied `repair.patch` and verified the output against
`source-lock.json` (`materialize_rc=0`, `a0af4360…`; `result/out/materialized_sha256.txt`), and
the package `Dockerfile` built it (image `sha256:c86f7521…`). Three arms on the same responses: v1 the
original (`b8b2824c…`), v2prev the v2.1 grader (`87f0e340…`, built from `v2prevctx/`, image
`sha256:85cd17b3…`) and v2 the v2.2 grader (`a0af4360…`); `rubrics.json` `d05f344e…` in all
three (`*.pins.txt`). Responses: all of `-fix2` and `-multiblock`, a re-ask sequence NA, and new ones
from `make_responses_e1e2.py`. Graded with `grade.py` (that job's `graded.md`).

| Fixed response | v1 valid | v1 score | v2.1 valid | v2.1 score | v2.2 valid | v2.2 score | v2.1 model calls | v2.2 model calls | v1 = v2.2 output |
| --- | --- | ---: | --- | ---: | --- | ---: | ---: | ---: | --- |
| A all 12 rules, one deduction each | true | 77 | true | 77 | true | 77 | 1 | 1 | byte-identical |
| B all 12 rules floored to 0 | true | 0 | true | 0 | true | 0 | 1 | 1 | byte-identical |
| C empty `scores` | true | 100 | false | – | false | – | 2 | 2 | – |
| D A minus R009 | true | 81 | false | – | false | – | 2 | 2 | – |
| E B minus R009 | true | 15 | false | – | false | – | 2 | 2 | – |
| F R009 rule-level score 0, no checkpoints | true | 0 | true | 0 | true | 0 | 1 | 1 | byte-identical |
| G R009 row with no score and no checkpoints | true | 0 | false | – | false | – | 2 | 2 | – |
| H no JSON | false | – | false | – | false | – | 2 | 2 | same structured result |
| I R009 score 0 with all-zero checkpoints | true | 15 | false | – | false | – | 2 | 2 | – |
| J D, then A on re-ask | true | 81 | true | 77 | true | 77 | 2 | 2 | – |
| K no JSON, then A on re-ask | false | – | true | 77 | true | 77 | 2 | 2 | – |
| L A without any rule-level score | true | 77 | true | 77 | true | 77 | 1 | 1 | byte-identical |
| GA R001 veto only in `veto_reason` | true | 3 | false | – | false | – | 2 | 2 | – |
| GB R009 deduction in an extra checkpoint | true | 15 | false | – | false | – | 2 | 2 | – |
| GC R009 veto flag, rule has no veto conditions | true | 15 | false | – | false | – | 2 | 2 | – |
| GD R009 floor wording after character 200 | true | 15 | false | – | false | – | 2 | 2 | – |
| M R001 negative checkpoint + veto marker | true | 0 | true | 0 | true | 0 | 1 | 1 | byte-identical |
| **N** A's block, then D's block, one output | **true** | **81** | **true** | **77** | false | – | 1 | 2 | – |
| O D's block, then A's block, one output | true | 77 | true | 77 | true | 77 | 1 | 1 | byte-identical |
| P A's block, then a truncated block, one output | true | 77 | true | 77 | true | 77 | 1 | 1 | byte-identical |
| NA N, then A on re-ask | true | 81 | true | 77 | true | 77 | 1 | 2 | – |
| **NZ** full-marks block, then D's block, one output | **true** | **81** | **true** | **100** | false | – | 1 | 2 | – |
| **NU** A's JSON, then D's JSON, unfenced, one output | **true** | **81** | **true** | **77** | false | – | 1 | 2 | – |
| **QA** A with R009's rule score as the string `"11"` | true | 77 | **false** | – | true | 77 | 2 | 1 | byte-identical |
| **QB** A with every rule score as a padded string such as `" 11.0 "` | true | 77 | **false** | – | true | 77 | 2 | 1 | byte-identical |
| QC A with R009's rule score `true` | true | 77 | false | – | false | – | 2 | 2 | – |
| QD A with R009's rule score `"twelve"` | true | 77 | false | – | false | – | 2 | 2 | – |
| QE I with R009's score `"0"` and all-zero checkpoints | true | 15 | false | – | false | – | 2 | 2 | – |
| QF F with R009's score `"0"` and no checkpoints | true | 0 | false | – | false | – | 2 | 2 | – |

Selection (`score_first`) on history [A, NZ]: v1 picks NZ at 81.0, v2.1 picks NZ at 100.0, v2.2
picks A at 77.0. The histories of the earlier sections ([A, C], [A, D], [B, I], [B, GA]) select as
before under v2.1 and v2.2.

**Spec checks.**

- **Earlier arms unchanged.** For every response of `-fix2` (A–M) and for O and P, the v2.2
  structured result is identical to v2.1's in this run, and v1 and v2.1 give the same validity and
  score as in `-fix2` and `-multiblock`.
- **e2 closed.** When the last block parses but fails the checks (N, NZ, NU), v2.2 asks again
  (2 calls) and reports a grading failure if the second answer is the same, instead of scoring an
  earlier block as v2.1 did (77, 100, 77 with one call). When the second answer is complete (NA), it
  scores 77. A truncated last block (P) still falls back to the complete earlier block, as in the
  original. Where an earlier draft is honest (N), v2.2 can therefore cost a submission its score when
  asking again does not help; a draft cannot be told from a final answer, so we do not score it.
- **e1 closed.** A plain decimal-string rule score with complete, consistent checkpoints (QA, QB)
  scores 77 with one call, byte-identical to the original; v2.1 reported a grading failure. A boolean
  (QC) and a word (QD) stay rejected, although the original scores both rows correctly from their
  checkpoints (77). A string `"0"` that contradicts all-zero checkpoints (QE) stays rejected, like
  its JSON-number twin I. A string `"0"` on a row without checkpoints (QF) also stays rejected,
  while its JSON-number twin F is scored 0 and the original scores QF 0 as well: without a
  complete checkpoint list the rule score itself carries the assessment, and the fixed version
  reads it only from a JSON number.
- **Verdict:** **accepted** (grader v2.2, `a0af4360…`).

## Repeatability of revision v2.2

The v2.2 job was run three times on fresh E2B workers: `evidence/runs/college_english_exam_bank-v2-paired-fix3`
(sandbox `i2jrsmeeq41ds10gemfoz`), `-fix3-rep2` (`ijojlt7llg4hp5p9x88j2`) and `-fix3-rep3`
(`ifg0a4z0erneo40j6ihu8`). Each closed with `status: exit=0`, `materialize_rc=0` and `build_rc=0` for
both fixed images, and its results were collected. Each run's `graded.json` and `graded.md` were
produced by `grade.py` from that run's own `result/out/`; both files are byte-identical across the
three runs. All 87 results (29 responses × original, v2.1 and v2.2) and all model-call counts are the
same in every run. The staged v2.1 grader (`v2prevctx/files/`, `87f0e340…`) was removed after
collection.
