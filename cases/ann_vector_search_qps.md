# ANN Vector Search QPS (`ann_vector_search_qps`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Systems & Software Engineering
- **Decision:** Retain with note. Honest submissions are scored as documented. Measured QPS depends on the host.

## What the task promises

The solver must "maximize **QPS** (queries per second) on the SIFT-1M dataset (1M × 128-d vectors, 10K queries) under the ann-benchmarks framework, while keeping **Recall@10 ≥ 0.95**". The work happens in `ann_benchmarks/algorithms/custom/module.py`. The rescale is `log_max` with baseline 3108 and expert 21472, so any raw QPS of 21472 or more normalizes to 100.

## What we checked and how

- We reused the earlier accepted evidence without repeating it. That evidence checked exact labels and distances over all 10,000 queries. It found that a FAISS flat control was accepted and an empty control was rejected.
- We added native honest controls on the unchanged original evaluator in the pinned judge image. The runs used 2 CPUs, `--memory 3g` and no network, on a shared host:
  - exact FAISS flat search;
  - FAISS IVF-flat with nlist 1024 and nprobe 32, run several times.
- **Original identity.**
  - Judge image: `seededge/edgebench.judge.ann_vector_search_qps@sha256:aa2856a379c10b93b0661a0b91b729a80fc2cf9bf119cc1385beea6b93eef288`.
  - Evaluator `/tmp/eval_ann_search.py`: sha256 `cfc64011510f2a556f933b9e79de8d77788d4de48e68b9cfb61ead946a57249d`. The hash inside the image matches the extracted copy.

## What we found

**Confirmed: earlier numerical and label checks.** No contrary evidence was found.

**Honest controls on the original evaluator.**

| Honest control | Recall | QPS |
|---|---|---|
| exact FAISS flat search | 0.9993 | 31 |
| FAISS IVF-flat (nlist 1024, nprobe 32) | 0.9777 | 875–1,222 across runs |

The recall threshold and the selection of the best valid QPS behave as documented. No good-faith scoring defect was found.

**Scorer isolation.** Scorer isolation is outside this release's scope (EdgeBench design choice); no good-faith scoring defect was found.

**Measurement limit.** QPS is measured in a single run and depends on the host. Repeated honest IVF runs varied from 875 to 1,222 QPS (±17%) on our shared host. The rescale anchors (3108 / 21472) come from the authors' hardware, so normalized scores are not comparable across hosts.

## Note for users

No repair. The note says: QPS is host-dependent, and repeated honest IVF-flat runs varied 875–1,222 QPS (±17%) on one shared host. The rescale anchors come from the authors' hardware, so scores are not comparable across hosts.

An earlier record called this task's inclusion decision "complete". That statement should carry this host-dependence limit.

## Limits and what was not run

- No model or solver re-runs were done. Score effects are shown only on authored controls.
- Each QPS figure is from a single run on a shared local host. We did not measure on the authors' hardware or on a dedicated judge.
- We did not repeat the earlier exact label and distance checks. They were reused as accepted evidence.
- Scorer isolation was not assessed for this release. It is outside scope.

## Reproduce

- Run the unchanged original evaluator in the pinned judge image with an honest `custom/` module mounted at `ann_benchmarks/algorithms/custom`. Use `--network none --cpus 2 --memory 3g`, and run `python3 /tmp/eval_ann_search.py` from `/home/workspace/ann-benchmarks`.
- For local development, the prompt's own command is `python run.py --local --algorithm custom --dataset sift-128-euclidean -k 10 --runs 1 --run-disabled`.
- The workspace script folder for this task also holds internal-only audit material and is not part of the public bundle.
