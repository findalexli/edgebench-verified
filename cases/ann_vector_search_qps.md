# ANN Vector Search QPS (`ann_vector_search_qps`)

**Outcome:** Kept, with a note. Honest submissions are scored as documented, but the measured speed depends on the machine the grader runs on.

## What the task asks

The agent must speed up an approximate nearest-neighbour search: a search that finds the vectors closest to a query without comparing against every vector. The prompt says: "maximize **QPS** (queries per second) on the SIFT-1M dataset (1M × 128-d vectors, 10K queries) under the ann-benchmarks framework, while keeping **Recall@10 ≥ 0.95**". Recall@10 is the share of the true 10 nearest matches that the search finds.

The work happens in `ann_benchmarks/algorithms/custom/module.py`. The grader converts the raw result (before conversion to 0–100), here the QPS, to a score out of 100 on a logarithmic scale (`log_max`). The reference point for 0 is 3108 QPS and the reference point for 100 is 21472 QPS. Any raw result of 21472 QPS or more scores 100. Category: Systems & Software Engineering.

## What we checked

There is no scoring problem for an honest solver. These checks found the grader correct:

- The grader's exact answer key (labels and distances) is correct over all 10,000 queries.
- A correct test submission using FAISS flat search (an exact, brute-force search) is accepted. An empty test submission is rejected.
- The recall threshold works as documented.
- The grader keeps the fastest valid submission, as documented.

The note concerns speed measurement. QPS is measured in a single run and depends on the machine. Repeated honest runs of one IVF-flat submission (a FAISS index that searches only a few clusters of vectors) varied from 875 to 1,222 QPS (±17%) on one shared machine. The reference points of the score scale (3108 / 21472) come from the authors' hardware.

The note that ships with the task says: QPS depends on the machine, and repeated honest IVF-flat runs varied 875–1,222 QPS (±17%) on one shared machine. The reference points of the score scale come from the authors' hardware, so scores are not comparable across machines.

## How much it matters

Variation between machines affects all solvers equally. On one shared machine, the same honest submission's raw result moved by ±17%. Scores out of 100 are not comparable across machines.

The task does not change; the note above ships with it.

## How we checked it

- **Original grader.** The grader ran unchanged in the original public image, pinned by digest. It ran with 2 CPUs, `--memory 3g` and no network on a shared machine. The grader file `/tmp/eval_ann_search.py` inside the image matches the extracted copy by hash.

| Honest test submission | Recall | QPS |
|---|---|---|
| exact FAISS flat search | 0.9993 | 31 |
| FAISS IVF-flat (nlist 1024, nprobe 32) | 0.9777 | 875–1,222 across runs |

- **Independent check.** The exact labels and distances were checked over all 10,000 queries.

## Limits

- No AI model or solver was run. Score effects are shown only on test submissions we wrote.
- Each QPS figure comes from a single run on a shared local machine. Nothing was measured on the authors' hardware or on a dedicated grading machine.
- Whether the grader is protected from tampering by a deliberately malicious submission is outside this release's scope (an EdgeBench design choice) and was not assessed.

## Reproduce

- Run the unchanged original grader in the pinned image (`sha256:aa2856a379c1…`) with an honest `custom/` module mounted at `ann_benchmarks/algorithms/custom`. Use `--network none --cpus 2 --memory 3g`, and run `python3 /tmp/eval_ann_search.py` from `/home/workspace/ann-benchmarks`.
- For local development, the prompt's own command is `python run.py --local --algorithm custom --dataset sift-128-euclidean -k 10 --runs 1 --run-disabled`.
- Full image digest and grader hash: `evidence/reviews/ann_vector_search_qps.md`.
