# ANN Vector Search QPS (`ann_vector_search_qps`)

**Outcome:** Kept, with a note. <mark>Honest submissions are scored as documented, but the measured speed depends on the machine the grader runs on and varies between gradings: three isolated gradings of one honest configuration at the leaderboard's grader setting gave 551–713 QPS, worth 13.3 points out of 100 on the scale (about ±7).</mark>

## What the task asks

The agent must speed up an approximate nearest-neighbour search: a search that finds the vectors closest to a query without comparing against every vector. The prompt says: "maximize **QPS** (queries per second) on the SIFT-1M dataset (1M × 128-d vectors, 10K queries) under the ann-benchmarks framework, while keeping **Recall@10 ≥ 0.95**". Recall@10 is the share of the true 10 nearest matches that the search finds.

The work happens in `ann_benchmarks/algorithms/custom/module.py`. The grader converts the raw result (before conversion to 0–100), here the QPS, to a score out of 100 on a logarithmic scale (`log_max`). The reference point for 0 is 3108 QPS and the reference point for 100 is 21472 QPS. Any raw result of 21472 QPS or more scores 100. Category: Systems & Software Engineering.

## What we checked

The grader computes the documented result correctly for an honest solver. These checks found it correct:

- The grader's exact answer key (labels and distances) is correct over all 10,000 queries.
- A correct test submission using FAISS flat search (an exact, brute-force search) is accepted. An empty test submission is rejected.
- A fast but inaccurate submission is rejected: the same IVF-flat index searching one cluster per query (`nprobe=1`) reaches 11,237–12,988 QPS but recall 0.3642, and the grader reports it as a wrong answer with total score 0 in each of three separate gradings. Without the recall check that speed would be worth 66.5–74.0 points out of 100.
- The recall threshold works as documented. Recall counts the overlap of returned and true neighbour IDs, so ties in distance count as misses: the exact flat search scores recall 0.9993, not 1.0. Upstream ann-benchmarks instead accepts any neighbour within the 10th true distance. The difference is at most 0.07 percentage points of recall.
- Within one grading, the grader keeps the fastest valid configuration, as documented.

The note concerns speed measurement. QPS is measured in a single run and depends on the machine. On the original grader, at the leaderboard's grader setting of 4 CPUs and 8 GiB, three gradings of one honest IVF-flat configuration (a FAISS index that searches only a few clusters of vectors), each alone in its own grading on a fresh cloud worker, gave 713, 650 and 551 QPS (±13% about the midpoint; the fastest is 1.29 times the slowest). Earlier gradings of the same configuration on a shared local machine at 2 CPUs, each sharing its process with other test configurations, gave 935, 1,222 and 1,094 QPS (1.31 times). The reference points of the score scale (3108 / 21472) come from the authors' hardware.

The note that ships with the task says: QPS depends on the machine, and three isolated gradings of one honest IVF-flat configuration on the original grader at 4 CPUs and 8 GiB gave 551–713 QPS (±13%). On the logarithmic scale, a speed ratio of 1.29 is 13.3 points out of 100 (about ±7 per grading) for a submission between the reference points. The reference points of the score scale come from the authors' hardware, so scores are not comparable across machines.

## How much it matters

Across three isolated gradings on three fresh workers with the same CPU model, the same honest configuration's raw result moved between 551 and 713 QPS. The scale is logarithmic, `100 · ln(QPS / 3108) / ln(21472 / 3108)`, so a speed ratio of 1.29 moves a score by 13.3 points out of 100 (about ±7 points per grading) for any submission between 3108 and 21472 QPS. The earlier shared-process gradings on one local machine gave a ratio of 1.31, or 13.9 points, so the isolated repeats confirm the size of the effect. The honest test submissions here are all below 3108 QPS and score 0, so this effect is computed from the scale, not observed in a score. Recorded agent runs on this task score 23.8–59.7 out of 100 (`tasks/README.md`), inside that range, so the effect applies at the scores agents reach. The task keeps each run's best submission (`score_first`), so variation between gradings can raise a run's recorded best. Whether variation between machines changes every algorithm's speed by the same factor was not tested. Scores out of 100 are not comparable across machines, and repeated gradings on one machine are not exactly repeatable.

The task does not change; the note above ships with it.

## How we checked it

- **Original grader.** The grader ran unchanged in the original public image, pinned by digest (`sha256:aa2856a379c1…`), with the task's own `eval_cmd` (`cd /home/workspace/ann-benchmarks && python3 /tmp/eval_ann_search.py`). Inside the image, `/tmp/eval_ann_search.py` has sha256 `cfc64011510f2a556f933b9e79de8d77788d4de48e68b9cfb61ead946a57249d`, the same as the extracted copy. The image runs Python 3.10.20, faiss 1.14.2, numpy 2.2.4 and h5py 3.13.0, with ann-benchmarks at commit `b61544cdf0576b0c0a784d90078498812e128194`.
- **Isolated repeats (2026-10-13).** Three E2B cloud jobs, `evidence/runs/ann_vector_search_qps-ivf-isolated-cpu4m8g-rep{1,2,3}`, each on its own fresh worker (CPU model `Intel(R) Xeon(R) Processor @ 2.60GHz`, 8 vCPUs). Each job ran two separate gradings, each in a new `docker run --rm --network none --cpus 4 --memory 8g` container: first the honest submission, then the `nprobe=1` control. 4 CPUs and 8 GiB are the leaderboard's `judge_cpu_limit` and `judge_mem_limit`; inside the container `cpu.max` reads `400000 100000` and `memory.max` 8589934592, while `nproc` still reports 8. Every job closed with `status: exit=0` in `evidence/runs/ledger.jsonl`, and its grader output was collected. Both test submissions use the same `module.py` (sha256 `3e7682072a469f3158bb44ab5296ddc204be8d269d12659cfab6380cbac08cf7`, empty `__init__.py`). The `config.yml` lists exactly one configuration: nprobe 32 for the honest submission (sha256 `1b397ea5a561abcbc2d3d588ecd30ba402833f447f7caea73e91613ffcf321a3`) and nprobe 1 for the control (sha256 `aba475e2360423ea22e7a5892317f16d92347f0247807e796887e819831c4ac2`). The index is the one graded earlier: IVF-flat, nlist 1024, trained on 60,000 training vectors drawn with seed 0, one search thread. The 0–100 scores come from `sforge/harness/score_rescale.py` with the task's `log_max` scale.

| Worker | Test submission | Grader verdict | Recall | QPS | Raw score (`TOTAL_SCORE`) | Score out of 100 |
|---|---|---|---|---|---|---|
| rep1 | IVF-flat, nprobe 32 (honest) | OK | 0.9777 | 713 | 713 | 0 |
| rep2 | IVF-flat, nprobe 32 (honest) | OK | 0.9777 | 650 | 650 | 0 |
| rep3 | IVF-flat, nprobe 32 (honest) | OK | 0.9777 | 551 | 551 | 0 |
| rep1 | IVF-flat, nprobe 1 (control) | WA | 0.3642 | 12,761 | 0 | 0 |
| rep2 | IVF-flat, nprobe 1 (control) | WA | 0.3642 | 12,988 | 0 | 0 |
| rep3 | IVF-flat, nprobe 1 (control) | WA | 0.3642 | 11,237 | 0 | 0 |

- **Earlier gradings (2026-10-12).** On a shared local machine with 2 CPUs, `--memory 3g` and no network:

| Honest test submission | Recall | QPS |
|---|---|---|
| exact FAISS flat search | 0.9993 | 31 |
| FAISS IVF-flat (nlist 1024, nprobe 32) | 0.9777 | 935, 1,222, 1,094 (three gradings) |

- **Earlier test design.** Each of those gradings ran one `custom` module whose `config.yml` lists several configurations, so the IVF-flat result shares one ann-benchmarks process with other test configurations we wrote, which are not honest submissions. ann-benchmarks runs the configurations of one grading in random order in that process, so one configuration can affect the timing of a later one. The three IVF values on the original grader are within a factor of 1.31 of each other. A fourth IVF value, 875 QPS, came from a modified evaluator and is not counted here, and neither are other IVF values from that modified evaluator. Those gradings have no entry in the run ledger. The isolated repeats above replace them as the measure of the spread.

- **Independent check.** The exact labels and distances were checked over all 10,000 queries.

## Limits

- No AI model or solver was run. Score effects are shown only on test submissions we wrote.
- Each QPS figure comes from a single run. The isolated repeats ran on shared cloud workers with one CPU model. Nothing was measured on the authors' hardware or on a dedicated grading machine.
- Three repeats bound the spread only roughly; more repeats or other CPU models could show a wider one.
- Only the single-threaded IVF-flat configuration was repeated. Its QPS (551–713) is below the 0-point reference, so the 13.3-point effect is computed from the scale, not observed in a score. Whether faster or multi-threaded submissions vary by the same factor was not tested.
- Whether the grader is protected from tampering by a deliberately malicious submission is outside this release's scope (an EdgeBench design choice) and was not assessed.

## Reproduce

- Run the unchanged original grader in the pinned image (`sha256:aa2856a379c1…`) with an honest `custom/` module mounted at `ann_benchmarks/algorithms/custom`. Use `--network none --cpus 4 --memory 8g`, and run `python3 /tmp/eval_ann_search.py` from `/home/workspace/ann-benchmarks`.
- The isolated repeats: `evidence/runs/ann_vector_search_qps-ivf-isolated-cpu4m8g-rep{1,2,3}/run.sh` with the test submissions in `inputs/`, run with `tools/e2b_run.py --job <dir>`.
- For local development, the prompt's own command is `python run.py --local --algorithm custom --dataset sift-128-euclidean -k 10 --runs 1 --run-disabled`.
- Full image digest and grader hash: `evidence/reviews/ann_vector_search_qps.md`.
