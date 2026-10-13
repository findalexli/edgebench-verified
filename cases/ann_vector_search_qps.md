# ANN Vector Search QPS (`ann_vector_search_qps`)

**Outcome:** Kept, with a note. <mark>Honest submissions are scored as documented, but the measured speed depends on the machine the grader runs on and varies between gradings on one machine (935–1,222 QPS, worth 13.9 points out of 100 on the scale).</mark>

## What the task asks

The agent must speed up an approximate nearest-neighbour search: a search that finds the vectors closest to a query without comparing against every vector. The prompt says: "maximize **QPS** (queries per second) on the SIFT-1M dataset (1M × 128-d vectors, 10K queries) under the ann-benchmarks framework, while keeping **Recall@10 ≥ 0.95**". Recall@10 is the share of the true 10 nearest matches that the search finds.

The work happens in `ann_benchmarks/algorithms/custom/module.py`. The grader converts the raw result (before conversion to 0–100), here the QPS, to a score out of 100 on a logarithmic scale (`log_max`). The reference point for 0 is 3108 QPS and the reference point for 100 is 21472 QPS. Any raw result of 21472 QPS or more scores 100. Category: Systems & Software Engineering.

## What we checked

The grader computes the documented result correctly for an honest solver. These checks found it correct:

- The grader's exact answer key (labels and distances) is correct over all 10,000 queries.
- A correct test submission using FAISS flat search (an exact, brute-force search) is accepted. An empty test submission is rejected.
- The recall threshold works as documented. Recall counts the overlap of returned and true neighbour IDs, so ties in distance count as misses: the exact flat search scores recall 0.9993, not 1.0. Upstream ann-benchmarks instead accepts any neighbour within the 10th true distance. The difference is at most 0.07 percentage points of recall.
- Within one grading, the grader keeps the fastest valid configuration, as documented.

The note concerns speed measurement. QPS is measured in a single run and depends on the machine. On the original grader, three gradings of one IVF-flat configuration (a FAISS index that searches only a few clusters of vectors) gave 935, 1,222 and 1,094 QPS (±13% about the midpoint; the fastest is 1.31 times the slowest) on one shared machine. The reference points of the score scale (3108 / 21472) come from the authors' hardware.

The note that ships with the task says: QPS depends on the machine, and three gradings of one honest IVF-flat configuration on the original grader gave 935–1,222 QPS (±13%) on one shared machine. On the logarithmic scale, a speed ratio of 1.31 is 13.9 points out of 100 for a submission between the reference points. The reference points of the score scale come from the authors' hardware, so scores are not comparable across machines.

## How much it matters

On one shared machine, the same honest configuration's raw result moved between 935 and 1,222 QPS across three gradings. The scale is logarithmic, `100 · ln(QPS / 3108) / ln(21472 / 3108)`, so a speed ratio of 1.31 moves a score by 13.9 points out of 100 (about ±7 points per grading) for any submission between 3108 and 21472 QPS. The test submissions here are all below 3108 QPS and score 0, so this effect is computed from the scale, not observed in a score. Recorded agent runs on this task score 23.8–59.7 out of 100 (`tasks/README.md`), inside that range, so the effect applies at the scores agents reach. The task keeps each run's best submission (`score_first`), so variation between gradings can raise a run's recorded best. Whether variation between machines changes every algorithm's speed by the same factor was not tested. Scores out of 100 are not comparable across machines, and repeated gradings on one machine are not exactly repeatable.

The task does not change; the note above ships with it.

## How we checked it

- **Original grader.** The grader ran unchanged in the original public image, pinned by digest. It ran with 2 CPUs, `--memory 3g` and no network on a shared machine. The grader file `/tmp/eval_ann_search.py` inside the image matches the extracted copy by hash.

| Honest test submission | Recall | QPS |
|---|---|---|
| exact FAISS flat search | 0.9993 | 31 |
| FAISS IVF-flat (nlist 1024, nprobe 32) | 0.9777 | 935, 1,222, 1,094 (three gradings) |

- **Test design.** Each grading ran one `custom` module whose `config.yml` lists several configurations, so the IVF-flat result shares one ann-benchmarks process with other test configurations we wrote, which are not honest submissions. ann-benchmarks runs the configurations of one grading in random order in that process, so one configuration can affect the timing of a later one. The three IVF values on the original grader are within a factor of 1.31 of each other. A fourth IVF value, 875 QPS, came from a modified evaluator and is not counted here, and neither are other IVF values from that modified evaluator. No grading of a standalone honest submission was repeated.

- **Independent check.** The exact labels and distances were checked over all 10,000 queries.

## Limits

- No AI model or solver was run. Score effects are shown only on test submissions we wrote.
- Each QPS figure comes from a single run on a shared local machine. Nothing was measured on the authors' hardware or on a dedicated grading machine.
- The spread of 935–1,222 QPS comes from three gradings that each also ran other test configurations in the same process (see the test design above), not from isolated repeats of an honest submission.
- Whether the grader is protected from tampering by a deliberately malicious submission is outside this release's scope (an EdgeBench design choice) and was not assessed.

## Reproduce

- Run the unchanged original grader in the pinned image (`sha256:aa2856a379c1…`) with an honest `custom/` module mounted at `ann_benchmarks/algorithms/custom`. Use `--network none --cpus 2 --memory 3g`, and run `python3 /tmp/eval_ann_search.py` from `/home/workspace/ann-benchmarks`.
- For local development, the prompt's own command is `python run.py --local --algorithm custom --dataset sift-128-euclidean -k 10 --runs 1 --run-disabled`.
- Full image digest and grader hash: `evidence/reviews/ann_vector_search_qps.md`.
