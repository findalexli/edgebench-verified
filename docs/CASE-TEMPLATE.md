# [Ordinary task name]: [concrete outcome established]

**Decision:** [Original excluded / original retained / task decision pending].
**Repair:** [None / proposed / tested at stated scope / certified exact replacement].
**Evidence:** [Mathematical argument / source inspection / original component / complete task / fresh independent reproduction].

[Two sentences: what failed, why it matters, and the strongest justified conclusion. A result such as “incorrect output accepted” must not be expanded into “leaderboard inflated” without measured evidence.]

## The task's requirement

[Explain the intended capability and the exact obligation that failed. Link the acquired task definition and revision. Explain any ambiguity and the interpretation used.]

## What the original did

[Describe the smallest understandable counterexample, the expected result and the observed result. Link the exact input and result. Distinguish an authored control from an actual corpus occurrence and from a model-generated submission. Include relevant counterevidence.]

## The proposed correction

[Explain the changed behavior, link the native-format task/source patch, and identify the original and candidate work/judge environments. If no fix exists, say so. If the task/scoring rule changes, say that it creates a new benchmark version.]

## The same controls before and after

| Input or submission | Independently justified expected behavior | Original result | Candidate result | Evidence and execution scope |
| --- | --- | --- | --- | --- |
| Triggering failure | [Expected] | [Observed or not run] | [Observed or not run] | [Record] |
| Valid control | [Expected] | [Observed or not run] | [Observed or not run] | [Record] |
| Different valid alternative | [Expected] | [Observed or not run] | [Observed or not run] | [Record] |
| Relevant incorrect/boundary case | [Expected] | [Observed or not run] | [Observed or not run] | [Record] |

[Use relevant controls, not a ritual checklist. Keep inputs, seeds and resources matched where required. Label absent results “not run”; do not infer them from source. Record raw scores, verdicts and any normalization separately.]

## Independent check and replay

[Who or what authored, reviewed and reproduced the result? What was independently rerun, on which frozen artifacts, with which fresh cases? What evidence was reused? A separate agent reviewing a log is a saved-result review, not a fresh execution or a human expert review. Link attempts to refute the claim and their outcomes.]

## What remains uncertain

[State the few material limits: untested corpus incidence, installed-environment parity, generalization, domain truth, remaining false rejection, or lack of historical score evidence. Do not bury an observed regression in a generic disclaimer.]

## Reproduce and reuse

[Provide the exact source/input manifest, runnable commands, dependencies and resource requirements, expected outputs, public-safe logs/results, and licenses/permissions. Keep secrets and restricted raw data out of the bundle. Explain restricted inputs and the resulting limit on public reproducibility. Link the final original/replacement decision.]

---

# Worked example from existing evidence: College English Exam

**Current decision:** original excluded; correction tested offline; replacement not certified.

The supplied grader can accept an assessment that omits a required rule. A versioned correction checks completeness before accepting the assessment. This is a local test of grading behavior under fixed responses, not a live-provider or whole-task performance result.

| Fixed-response assessment | Expected behavior under the controlled rubric | Original supplied source | Candidate source |
| --- | --- | --- | --- |
| Complete assessment | Remain valid with the same score | Valid 96 | Valid 96 |
| One required rule omitted | Reject the incomplete assessment | Valid 96 | Invalid 0 |

The accepted record contains four offline calls through original and candidate source. The earlier 100-point examples belong to an earlier grader copy and must not be presented as results of the final supplied source. Independent final-source inspection and saved-result review are distinct from fresh independent native reproduction; the latter is not established by this example.

**Still needed for a complete repair case:** integrated candidate-environment execution, effective rubric and installed-source binding, relevant fresh valid/invalid alternatives, and independent reproduction of those exact artifacts. Real model-provider behavior and broader educational correctness remain unmeasured. Recover any already accepted evidence before commissioning a rerun.

Evidence: [original decision](../evidence/selected/english-original-exclusion.json), [accepted repair controls](../evidence/selected/english-final-source-repair.json), and [native-format patch](../proposedrepairs/college-english-assessment-completeness/README.md).
