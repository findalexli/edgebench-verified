# Review: graph_node_classification

## Claim under review

Earlier claim (docs/FINDINGS.md): "Conservative policy choice: the checker silently replaces NaN confidence with zero. Acceptance violates the supplied numerical range, but tolerance may be intended. Mandatory total rejection and score inflation are unproved."
Earlier disposition: **withhold the original**. Evidence: `evidence/selected/eq-graph-original-exclusions.json` and `evidence/selected/graph-confidence-qualification.json`. The qualification gives the decision as `RETAIN_ORIGINAL_EXCLUSION_QUALIFY_REASON`, with the reason "undocumented nonconforming-value substitution".

## Pinned artifacts

- Task: `tasks/graph_node_classification.json`. eval_cmd `python judge_eval.py`, parser `structured_json`, rescale 0..1, selection `valid_then_score`.
- Judge image (pulled, executed): `seededge/edgebench.judge.graph_node_classification@sha256:518c105ec283ea9231ecb87886e0937c14a7bd937d8e385afaa3369800c5c3bd`.
- Evaluator files. Each matches between the image and `$W/work/task-sources/merged/graph_node_classification/` (sha256):
  - `verifier.py` 044cd50e2e00187adbafc5d0b669af76589fa169578f6e290da39c233c40299e
  - `runner.py` 2004a53ffbdba3beea5e5fe00398896a121587b2aa7bcc90facde763001a85db
  - `judge_eval.py` 1a508d716beaaa980691e1db95a60b030cb3b22114e010f59bd8cd52f50a63e9
  - `config.yaml` 1d04a91523232dfb12c8f7de94a3688c021ed552cc09a1ede7b27ea0f0842789
- Prompt documents. The image ships English `README.md` and `solution/problem.md`, which differ by hash from the Chinese copies in `merged/`. The contract sentences below are the same in both languages.

## Contract

From `problem.md` / `README.md`:

- "`confidences` is optional; if provided, values must be in `[0, 1]`."
- "`confidences` participates in the computation of the calibration metrics `ece` / `one_minus_ece`."
- "If `confidences` is not provided, the evaluator will use a default confidence value, which typically hurts the calibration score."
- "`predictions` values must be integer class ids … should cover all test nodes of the current split."
- `overall = 0.4·macro_f1 + 0.3·micro_f1 + 0.2·balanced_accuracy + 0.1·one_minus_ece`. The split score is `final = overall − 0.01·log(time) − memory penalty`, averaged over 10 splits.

The contract does not say what happens to an out-of-range confidence: rejection, clipping or zero.

## Exactly how confidence is used

From `verifier.py`:

- `evaluate()`: `conf_arr = [float(confidences.get(nid, 1.0)) ...]`. A missing key becomes 1.0.
- `_ece()`: `confs = [min(1.0, max(0.0, float(c))) for c in confs]`. With the arguments in this order, Python gives `max(0.0, nan) == 0.0`. The resulting mapping is:
  - NaN → 0
  - −inf or any negative → 0
  - >1 or +inf → 1
- The bin is `min(9, int(c*10))`.
- Confidence enters **only** `ece`, which has weight 0.1 through `one_minus_ece`. `macro_f1`, `micro_f1` and `balanced_accuracy` never read it.

So the score depends on confidences only through `clip(c)`, and `clip(c)` always lies in [0,1]. **Every out-of-range submission therefore scores exactly the same as a contract-conforming submission:** NaN or negative behaves like 0.0, and >1 behaves like 1.0. No out-of-range value can achieve a score that a legal value cannot.

## Independent reproduction

Scripts are in `evidence/scripts/graph_node_classification/`.

**1. Pure-function checks against the original `verifier.py` (`check_confidence_mapping.py`).**
- **Point probes.** With uniform confidence and accuracy 0.6:
  - NaN, −inf, −0.5 and 0.0 all give ECE 0.6.
  - +inf, 1.7 and 1.0 all give ECE 0.4.
  - 0.6 gives ECE 0.0.
- **Random equivalence.** 20,000 random vectors with 40 % special values (NaN, ±inf, ±1e9, −0.3, 1.3). Raw scores and scores of the in-range image showed **0 mismatches**.
- **Exhaustive search.** All binary cases with n ≤ 3 (84 label/prediction pairs) over a 21-point legal grid plus 5 illegal values. In **0** cases did an illegal value beat the best legal one.
- The classification metrics are identical under NaN vs legal confidences.

**2. The real judge command in the pinned image (`run_judge_variants.sh`, `wrapper_solution.py`, results in `judge_variants_out.jsonl`).** The submission is the image's own baseline (`solution_template.py`). Its confidences were post-processed into the modes below. Runs used `--network none`. The first two used 4 GiB with the default 4 workers. After the coordinator capped memory at 2 GiB, the rest used 2 GiB with `SEB_PARALLEL_WORKERS=1`, because 4 workers ran out of memory at 2 GiB. Worker count changes only the time penalty, not the quality metrics.

| mode | valid | one_minus_ece | overall (quality) |
|---|---|---|---|
| baseline confidences (legal) | true | 0.92503 | **0.33262** |
| all NaN | true | 0.71316 | 0.31144 |
| all 0.0 (legal) | true | 0.71316 | 0.31144 |
| all 7.5 (>1) | true | 0.28684 | 0.26880 |
| all 1.0 (legal) | true | 0.28684 | 0.26880 |

NaN produces results identical to 0.0, and 7.5 identical to 1.0, down to the last digit. Every illegal mode scores **below** the baseline's own legal confidences. macro_f1, micro_f1 and balanced accuracy are identical in all modes.

## Refutation attempts

- *Can NaN, inf, negative or >1 raise a score?* No, as proven above: the score is a function of the clipped value, and every clipped value is legal. The real harness confirms this.
- *Is confidence even scored?* Yes, but only through ECE, with weight 0.1. The worst case for any confidence vector is a 0.1 difference.
- *Is "total rejection" mandated?* No. The text says values "must be in [0,1]" but gives no consequence. Clipping is a reasonable reading of "tolerant evaluator". Accepting NaN as 0 gives no advantage over a solver that writes 0.0.
- *Is the payload accepted as `valid`?* Yes. `judge_eval.py`'s `valid` flag only checks that the payload is present, that this is the full 10-split run, that prediction counts cover the split, and that a score is present. It does not attest value ranges.

## Side observation (outside the claim; more substantive than the NaN point)

`verifier._to_int_labels` silently **drops** prediction values that cannot be converted to `int`, such as the string `"x"` or a NaN float. `evaluate()` then truncates `y_true` to the shorter list. Meanwhile, `runner`'s coverage count uses `len(predictions)`, the dictionary size, so it still passes. A submission can therefore make only the first k test nodes count.

- **Pure function** (`check_invalid_prediction_shrink.py`): 1000 nodes; the first prediction is correct and the rest are `"x"`. Result: macro_f1 = micro_f1 = balanced accuracy = 1.0 and ECE 0.
- **Real judge** (mode `shrink`, in `shrink_out.jsonl`): `valid: true`, with every split scored on a single node. The baseline's first-node guess was right in 2 of 10 splits, giving overall 0.20. That is below the honest 0.333 for this weak baseline. The expected value of the gamble is about 0.1 + 0.9·p per split (confidences set to match), where p is the accuracy on one fixed node. So there is no clear expected gain for typical models, but the variance is greatly inflated, and the run is accepted as valid while it violates "integer class ids". This contract gap is real and reachable. Its score impact, for example under best-of-several selection, is **not established**. It deserves its own reviewed question; it is not a basis for this NaN claim.

## Formal check

Not needed. The property "score(c) = score(clip(c)) with clip(c) ∈ [0,1]" follows directly from the single line in `_ece`. It was confirmed by exhaustive and random comparison and by the real harness. A Lean proof would only restate Python's `max`/`min` semantics on NaN, and running Python checks those semantics directly.

## Verdict

**CONFIRMED (fact) / WEAKENED (as an exclusion ground).** The fact is reproduced: NaN becomes 0, negatives become 0, and values above 1 become 1, all silently, and the run is reported valid. It is provably score-neutral relative to legal submissions, so it cannot inflate any score. It affects only a component weighted 0.1, and a tolerant reading of the contract is reasonable.

## Disposition assessment

**Disagree** with withholding the original on this ground. Under VERIFICATION.md, exclusion requires a specific, evidenced reason. "Undocumented clipping of out-of-range confidences" changes no achievable score, and any such submission is weakly dominated by a legal one. Withholding the whole task for it is disproportionate. On this ground alone, the defensible disposition is **retain with a note**: out-of-range confidences are clipped, and NaN is treated as 0.

The task should still not be released as "retained" without addressing the side observation above. Silent dropping of non-integer predictions, combined with truncation of the ground truth, is a real contract-violating acceptance that can shrink the scored set. It is the stronger reason to **repair** (see below). I did not establish that it inflates scores, so it should not be published as score inflation.

## Recommended publishable wording

"The original evaluator clips out-of-range confidence values into [0,1] (NaN is treated as 0) instead of rejecting them. This is score-neutral: any such submission scores exactly as the corresponding in-range submission would. Separately, prediction values that are not integers are silently dropped and the ground-truth list is truncated, so a run can be scored on fewer test nodes than required while still reported valid. Its effect on scores was not established."

## Repair note

No earlier repair for this task exists in `proposedrepairs/`. The minimal fixes are:

1. **Confidence (optional, cosmetic):** reject non-finite or out-of-range values, or document the clipping. Either choice is score-neutral for conforming submissions.
2. **Predictions (recommended):** in `verifier.evaluate`, require every ground-truth node id to have an `int`-convertible prediction. A missing or invalid value should count as an error, with `valid=false` or the node scored as wrong. Pairs must be aligned by node id, not by truncating two independently filtered lists. Regression controls:
   - the baseline is unchanged;
   - the `shrink` mode (`wrapper_solution.py`) is rejected or scored over all nodes;
   - NaN, 0.0, 7.5 and 1.0 confidence modes are unchanged.

## Limits

- Only the image baseline was run through the real harness, plus synthetic confidence vectors against the original verifier function. Stronger solvers were not run.
- The side observation's expected-value analysis is analytic, plus one 10-split run.
- I did not check how `selection: valid_then_score` is applied across attempts, which determines whether the variance is exploitable.
- The work image was not pulled because of the coordinator's resource limit. The prompt text was read from the judge image's English copy and the merged Chinese copy, which agree on the contract sentences.
