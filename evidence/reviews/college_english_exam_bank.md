# Review: `college_english_exam_bank`

## Claim under review

> "The grader accepts an assessment missing required rules as complete. Fixed-response local calls support this. Earlier 100-point examples used an earlier grader copy."

Earlier disposition: **withhold original** (card decision `exclude`: "On the normal valid nonempty-rubric route, a successfully parsed empty assessment is silently filled in and reported as completed grading.")

## Pinned artifacts

| Artifact | Identity |
|---|---|
| Task manifest `tasks/college_english_exam_bank.json` | sha256 `93e112ed…0406f` |
| Judge image | `seededge/edgebench.judge.college_english_exam_bank@sha256:8e9eec1057c7ab1b9b48d95cb493aa336b3ec3cea84df5bd80ad04d3009d58a8` (pulled, run locally) |
| Grader in judge image `/home/workspace/scoring/grade_with_codex.py` | sha256 `b8b2824c0d5483f8f433d4fc59e11efb8c7c18d1126b60987c99a1c2cb0e4b3f`, 93,823 bytes |
| `rubrics.json` (image and cloud export are identical) | sha256 `d05f344e0f76ceeda7fb8c1d927df662b3f5f87c91631cd9b3fdebc6162bf603` |
| Earlier grader copy (`cloud-exports/merged/.../grade_with_codex.py`) | sha256 `55f148e0…cb0e`, 93,879 bytes |
| Proposed patch `proposedrepairs/college-english-assessment-completeness/patch.diff` | applies cleanly to the image grader; result sha256 `87de3790…9dec` (matches the manifest's `after`) |

The earlier copy differs from the image copy **only** in credential and model environment-variable names (`SFORGE_JUDGE_*` and `OPENROUTER_*`/`SEBENCH_*`). Every parsing, validation, reconciliation and scoring line is identical (`diff` output: lines 10-12, 890-959, 1643 only). So the caveat about results from the earlier copy does not matter for scoring. I reproduced every result on the image copy.

## Contract

- Solver: the solver gets `task_instruction.md` and must produce 22 deliverables: five exam papers (A to E) as Word and PDF, answer keys and scoring guides as Word and PDF, a blueprint workbook and a cross-paper repetition-rate workbook.
- Grader: `eval_cmd` runs `scoring/grade_with_codex.py`. It launches the Codex CLI as an LLM agent through a paid provider (OpenRouter by default). The agent reads `rubrics.json`, the hidden reference files and the submission, then prints a JSON `scores` array. Python code then reconciles that JSON against `rubrics.json` and computes `raw_total / max_total × 100`.
- **What "required rules" means:** `rubrics.json` lists 12 rules, R001 to R012, with max scores 3+12+4+4+10+10+4+10+15+10+10+8 = 100. **All 12 are `scoring_mode: "deductive"`**: each rule starts at its maximum and loses points for triggered deduction details.
- Where the requirement is stated: the grader's own prompt to the grading model says (CODEX_GRADING_PROMPT, step 1) "严格以 `rules` 数组为评分清单。不要新增、删除、合并 rule". In English: use the `rules` array strictly as the scoring list, and do not add, delete or merge rules. The output spec says checkpoint_scores "如果该 rule 有 scoring_details，必须逐 detail 返回一项", i.e. one entry per detail. The docstring of `reconcile_result_with_rubrics` says "Force result coverage/order/max_score to match rubrics.json". The **grader's design** therefore requires every rule to be assessed. No solver-facing document mentions this requirement, because it concerns the grader and not the solver.

## Independent reproduction

Method: the original `main()` runs end to end inside the pulled judge image (`--network none --memory 2g --cpus 1`). Only the `codex` executable on `PATH` is replaced, by `fake_codex.sh`, which prints a fixed response file. Dummy key and model environment variables get past the credential check. Responses are generated from the original `rubrics.json` by `make_responses.py`. Scripts are in `evidence/scripts/college_english_exam_bank/` and the log is in `run_in_judge_image.log`.

```
docker run --rm --network none --memory 2g --cpus 1 -v scripts/college_english_exam_bank:/audit:ro -v <resp>:/m:ro \
  --entrypoint sh <judge image> -c '/audit/run_fixed.sh /home/workspace/scoring/grade_with_codex.py /home/workspace/scoring /home/workspace/input /m/resp /tmp/wo'
```

| Fixed response | Original image grader | With proposed patch |
|---|---|---|
| A: all 12 rules, first deduction triggered in each (control) | valid, **77.0** | valid, 77.0 (unchanged) |
| B: all 12 rules, all floored to 0 (known-bad control) | valid, **0.0** | valid, 0.0 |
| C: `{"scores": []}` (no rule assessed) | **valid, 100.0** | invalid, 0 |
| D: A with R009 (15 pts) omitted | **valid, 81.0** (R009 → 15/15) | invalid, 0 |
| E: B with R009 omitted | **valid, 15.0** (R009 → 15/15) | invalid, 0 |
| F: B, R009 given rule-level score 0 with no checkpoints | valid, 0.0 | valid, 0.0 |
| G: B, R009 row present with neither score nor checkpoints | valid, 0.0 | invalid, 0 |
| H: no JSON at all (control) | invalid, 0 | invalid, 0 |
| I: B, R009 score 0 but a complete all-zero checkpoint vector | valid, 15.0 (R009 → 15/15) | valid, 15.0 |

For the omitted rules the grader writes this reason: "Missing deductive detail scores; unreported deduction triggers treated as not triggered." Mechanism (`reconcile_result_with_rubrics`): when a rule is missing, `src = {}`, so there are no checkpoints and no `score`. In deductive mode `deduction_total` stays 0, so `score = max_score`. The result is reported with `grader_status: ok` and `valid: true`.

## Refutation attempts

1. *Is the 100 an artefact of the earlier copy?* No. The results are identical on the image copy (sha `b8b2…`), and the two copies differ only in environment-variable names.
2. *Does missing data perhaps lower the score instead?* Not for this task. For an **additive** rule the same code gives 0 for unreported details, so it would deflate the score. Because all 12 rules are deductive, any omission here can only **raise** the score. The bias always points upward, and each omitted rule is worth up to its full maximum (up to 15 points for R009).
3. *Is the trigger reachable?* It requires the grading model to return parseable JSON that lacks some rule rows. Nothing in the solver's path can produce that directly. It depends on the grading model's behaviour: truncated, abandoned or partial assessments of a heavy 22-file submission with many visual checks. The prompt itself anticipates the model running short of time or context ("不得因为工作量大而不输出 JSON"). A solver could also try prompt injection through submission text that the agent reads. That is a generic risk of LLM graders. The omission fail-open lowers the bar for it a little, because "stop early" is enough and no fake high scores are needed, but it does not create the risk. I treat solver exploitation as **plausible but undemonstrated**.
4. *Is it in the task or in model robustness?* The defect is in **task-owned grader code**: deterministic post-processing that fails open on incomplete model output. The model's tendency to omit rows is a model-robustness question. Turning an omission into full credit labelled `valid` is a grader bug, and the reconciler is meant to prevent exactly that ("Force result coverage").
5. *Residual path the earlier audit did not mention (case I):* if a rule row carries `score: 0` together with a complete all-zero checkpoint vector, the reconciler trusts the checkpoints and awards full marks. The proposed patch does not change this. It is an inconsistent model output rather than an omission. I list it as a related observation and not as part of the confirmed claim.

## What fixed-response evaluation does and does not establish

It **establishes** deterministic facts about the original grader code on the original rubric and image: what score it reports for a given model output. That includes 100/100 labelled valid for an empty assessment, and the exact credit for each omitted rule. It **does not establish** how often the real grading model emits incomplete assessments, whether any historical EdgeBench score was inflated, what a real submission would score, or whether a solver can induce omission. No provider call was made (no credentials, no paid API).

## Formal check

None needed. The behaviour is a direct, deterministic code path, checked by execution.

## Verdict

**CONFIRMED.** The original grader accepts an assessment that omits required rules, scores each omitted rule at full marks, and reports the result as valid (an empty assessment scores 100). The impact is conditional on grading-model behaviour, and its incidence is unmeasured.

## Disposition assessment

I agree with withholding the exact original unchanged. Under VERIFICATION.md, "Exclude" means withhold this original unchanged, with a repair as a separate version. A grader that fails open toward full credit on any incomplete model output cannot be certified. The *task content* is not implicated, though, and the defect is a small local repair. The proportionate path is withhold original plus repair, not dropping the task. Withholding must not be described as evidence that historical scores were inflated.

## Recommended publishable wording

"In the original grader, any rubric rule the grading model failed to assess received full marks, and the result was still reported as valid. With a fixed, empty model response the grader returned 100/100. Real-model incidence and historical score effects were not measured."

## Repair note

The proposed patch rejects score lists that are incomplete, duplicated, unknown or non-numeric before normalization. I verified it in the image: valid outputs are unchanged (77 and 0) and omissions become invalid (C, D, E, G). It is correct and minimal for the claim. Limits:
- An omission now yields `valid: false, score 0`, the same as a parse failure. The harness must treat that as a grader failure to retry, not as the solver's 0. Otherwise the patch turns an upward bias into a downward one. In this repository's harness (`sforge/harness/grading.py`, `_grade_structured`), `valid: false` goes through `_invalidate(report, "Evaluator marked submission invalid")`. Whether a run with an invalid report is retried or counted as 0 depends on the runner policy, which I did not check.
- Case I (complete zero checkpoints that contradict a rule score) remains. An optional extra check would flag rows whose stated `score` disagrees with `max_score − sum(checkpoints)`.
- I did not test it with a live model.

## Limits

No live grading-model calls, so incidence is unknown. I did not run the harness's handling of `valid:false`. The submission was a one-file placeholder, which is irrelevant here because the fixed response does not read it. I ran in the original image with `--network none` and a stubbed `codex`. The real path also installs or uses `/usr/local/bin/codex` and contacts the provider.
