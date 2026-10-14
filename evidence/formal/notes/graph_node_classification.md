# graph_node_classification

## Claim

**Scope:** these claims are about the first fixed verifier (v2, sha256 `32caddb1…`). The current v2.1 verifier (`7b4860ec…`) matches prediction keys by `str()` and rejects files whose keys collide after `str()`; that is not modelled. V1 and V2 do not hold for v2.1: it scores a complete integer-keyed file (`neighbor_intkeys`) that the original scores 0, and it rejects `dupkeys_after_str`, which the original scores. See `repairs/graph_node_classification-v2/paired/results.md`.

- (V1) The fixed `evaluate` succeeds if and only if every test node has a prediction that `_strict_class_id` accepts. Accepted values are: an int (not a bool), an integral finite float, a string `s` with `int(s.strip())` defined, or an `__index__` object.
- (V2) For every accepted prediction file, the original `evaluate` passes the metric code exactly the same arguments, so it returns identical metrics. This holds for **any** metric function.
- Optional (best-of-k): under max selection, adding a random submission never lowers the expected kept score. The expected kept score rises strictly when the new submission beats the current best with positive probability, even if its mean is lower.

## Model and link to the code

`evidence/formal/lean/ebv/Ebv/GraphNodeValidation.lean`, core Lean only. `PyVal` sorts each value by how `int()` (v1 `_to_int_labels`) and `_strict_class_id` (v2) treat it. `origEval` and `fixedEval` follow v1 l.84-100 and v2 l.104-129, with sha256 v1 `044cd50e…` and v2 `32caddb1…`. The metrics are a universally quantified `M`.

Differential check: `probes/graph_node_classification/diff_check.py` ran the real v1 and v2 `evaluate` in the image's Python 3.11 on 20,000 random prediction dicts:

- V1 held on all of them.
- V2 gave identical metrics on all 7,479 accepted files that satisfy StrOK.

## Result

**Proved**, with one boundary, which the case page and the fixed-version README now state. V2 needs `StrOK`: `int(s) = int(s.strip())`. An exhaustive scan of all code points in Python 3.11 finds exactly U+001C..U+001F where this fails: `str.strip` removes these characters but `int()` does not accept them. A string such as `"\x1c0"` is therefore dropped by v1 and scored by v2, so the claim "decimal-integer strings score identically" has this exotic exception (`separator_boundary`).

Precision point on the published wording: v1 does not score "a subset of the test nodes". It pairs the surviving predictions with the **first n labels**, so one bad value early in the file shifts every later prediction (`misaligned`). In the published shrink example the two readings coincide.

## Counter-check

- `shrink`: v1 scores 1/1 accuracy on one node and stays valid; v2 rejects.
- `misaligned` and `separator_boundary`.
- `v1_converts_v2_rejects`: bool, non-integral float and `__int__`-only values.

## Limits

- The judge_eval size check (`len(predictions) == len(gt)`), which together with V1 excludes extra keys, is not formalised.
- `__index__`/`__int__` consistency is assumed (`idx`).
- The best-of-k lemmas are general facts about max selection. `illustration` (a mean of 250 rises to an expected kept score of about 358/1000 against a best of 333) uses an assumed per-split hit rate of 1/4, not a measurement. This supports the claim that best-so-far selection turns variance into expected gain, but it does not show that any real solver benefits. The case page now cites the lemma to that extent and still states that no gain for a real solver was shown.
