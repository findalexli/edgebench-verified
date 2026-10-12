# ANN vector search (`ann_vector_search_qps`): re-verification

Reviewer: Claude (coordinator), 2026-10-12. Earlier disposition: **retain unchanged under maintained core-v2**
(the only retained task).

## Pinned artifacts

- Judge image `seededge/edgebench.judge.ann_vector_search_qps@sha256:aa2856a379c10b93b0661a0b91b729a80fc2cf9bf119cc1385beea6b93eef288`
- Evaluator `/tmp/eval_ann_search.py` sha256 `cfc64011510f2a556f933b9e79de8d77788d4de48e68b9cfb61ead946a57249d` (in-image hash matches the extracted copy)
- Rescale `log_max`, baseline 3108, expert 21472 (`tasks/ann_vector_search_qps.json`); any raw QPS ≥ 21472 normalizes to 100.

## Good-faith correctness

The earlier accepted evidence (exact label/distance checks over all 10,000 queries; FAISS flat
control accepted, empty control rejected) is reused, not repeated. This re-check adds a native
honest control in the same runs: exact FAISS flat search, recall 0.9993, 31 QPS; FAISS IVF-flat
(nlist 1024, nprobe 32), recall 0.9777, 875–1,222 QPS across runs (2 CPUs, `--memory 3g`, shared
host). Recall, threshold and best-valid-QPS selection behave as documented. No good-faith scoring
defect was found.

**Limit (measurement):** QPS is host-dependent and single-run; repeated honest IVF runs varied
875–1,222 QPS (±17%) on this shared host. The rescale anchors (3108 / 21472) come from the
authors' hardware; scores are not comparable across hosts. This is a property of the task design,
to be stated in the release notes.

## Scorer isolation (out of release scope, recorded internally)

Per the user's 2026-10-12 scope decision, scorer-isolation weaknesses are a known EdgeBench design
choice and are not release defects. For the record: in native runs on the unchanged evaluator, two
non-legitimate submissions were accepted above the expert anchor (normalized 100), and a candidate
evaluator change (`scripts/ann_vector_search_qps/repair/eval_ann_search_v2.patch`) blocked both in a
paired run while keeping honest IVF accepted. Details are internal-only (see workspace README).
In-process timer replacement is not addressed by that change.

## Verdict and disposition

- Earlier numerical/label conclusions: **CONFIRMED** (reused; no contrary evidence).
- Disposition: **retain with note** (host-dependent QPS; scorer isolation per EdgeBench design).
- Earlier wording to correct: "Inclusion decision complete" should add the host-dependence limit.

## Paired-run record

| Config | v1 original | v2 candidate |
| --- | --- | --- |
| honest IVF | OK 1,094 QPS, recall 0.9777 | OK 875 QPS, recall 0.9777 |
| non-legitimate A | OK, normalized 100 | rejected |
| non-legitimate B | OK, normalized 100 | OK 34 QPS (true speed) |

Outputs: `scripts/ann_vector_search_qps/paired3-20261012T034333Z/{v1,v2}/judge-stdout.txt`.
