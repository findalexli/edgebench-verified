# ANN Vector Search QPS (`ann_vector_search_qps`)

**Decision:** Retain with note. Honest submissions are scored as documented, but measured QPS depends on the host.

## What the task asks for

The solver must "maximize **QPS** (queries per second) on the SIFT-1M dataset (1M × 128-d vectors, 10K queries) under the ann-benchmarks framework, while keeping **Recall@10 ≥ 0.95**". The work happens in `ann_benchmarks/algorithms/custom/module.py`. The rescale is `log_max` with baseline 3108 and expert 21472, so any raw QPS of 21472 or more normalizes to 100. Category: Systems & Software Engineering.

## What goes wrong

No good-faith scoring defect. What was checked and found correct:

- Exact labels and distances over all 10,000 queries.
- A FAISS flat control is accepted and an empty control is rejected.
- The recall threshold and the selection of the best valid QPS behave as documented.

Note: QPS is measured in a single run and depends on the host. Repeated honest IVF-flat runs varied from 875 to 1,222 QPS (±17%) on one shared host. The rescale anchors (3108 / 21472) come from the authors' hardware.

The note says: QPS is host-dependent, and repeated honest IVF-flat runs varied 875–1,222 QPS (±17%) on one shared host. The rescale anchors come from the authors' hardware, so scores are not comparable across hosts.

## Impact

All solvers are affected equally by host variation. On one shared host, the same honest submission moved by ±17% in raw QPS. Normalized scores are not comparable across hosts.

## Fix (v2)

No change; the note above ships with the task.

## How we know

- **Original evaluator in the pinned judge image** (`sha256:aa2856a379c1…`), unchanged, run with 2 CPUs, `--memory 3g` and no network on a shared host. The evaluator `/tmp/eval_ann_search.py` inside the image matches the extracted copy by hash.

| Honest control | Recall | QPS |
|---|---|---|
| exact FAISS flat search | 0.9993 | 31 |
| FAISS IVF-flat (nlist 1024, nprobe 32) | 0.9777 | 875–1,222 across runs |

- **Independent check.** Exact labels and distances were checked over all 10,000 queries.

## Limits

- No model or solver runs. Score effects are shown only on authored controls.
- Each QPS figure is from a single run on a shared local host. Nothing was measured on the authors' hardware or on a dedicated judge.
- Scorer isolation is outside this release's scope (EdgeBench design choice) and was not assessed.

## Reproduce

- Run the unchanged original evaluator in the pinned judge image with an honest `custom/` module mounted at `ann_benchmarks/algorithms/custom`. Use `--network none --cpus 2 --memory 3g`, and run `python3 /tmp/eval_ann_search.py` from `/home/workspace/ann-benchmarks`.
- For local development, the prompt's own command is `python run.py --local --algorithm custom --dataset sift-128-euclidean -k 10 --runs 1 --run-disabled`.
- Full image digest and evaluator hash: `evidence/reviews/ann_vector_search_qps.md`.
