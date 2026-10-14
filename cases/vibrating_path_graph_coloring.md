# Vibrating Path Graph Coloring (`vibrating_path_graph_coloring`)

**Outcome:** Fixed. <mark>On the publisher's 4-CPU grader, a valid solution using more than about 14 s of CPU per case times out, although the README promises 30 s per case, and one timeout leaves the whole submission without a score. The fixed version runs at most as many cases at once as the grader has CPUs and allows 900 s instead of 600 s for the whole run. The tester's rejection of the README's three-line zero-hit form remains as a note; its score effect is ruled out on 37 certified cases and remains unresolved on 13 cases.</mark>

## What the task asks

The agent solves graph-colouring puzzles. It colours the points (vertices) of a network so that linked points differ, and may "hit" vertices along the way. The prompt says "Your solution is scored on **50 fixed test cases**. Final score = sum of individual case scores. **Lower is better.**" It defers to "`README.md` and `tools/README.md` for full problem details". The README's output format has three lines.

- "Line 1: number of hits $Q$"
- "Line 2: the vertices hit in order (1-indexed)"
- "Line 3: coloring of each vertex ($1 \leq x_i \leq K$)"

The README gives no exception for the case with no hits. `tools/README.md` contains no output-format text and no exception. Category: Combinatorial Optimization.

## What we checked

For zero hits, the README form is three lines with an empty hit line. The tester accepts zero hits only in a two-line form. The shipped baseline `solution.py` prints the two-line form, and `tools/src/verifier.py` reads it the same way.

The original tester gives these results.

| Input | Output | Original tester |
|---|---|---|
| bipartite 4-path we wrote, K=2 | `0\n1 2 1 2` (two-line) | `Score = 0`, exit 0 |
| same | `0\n\n1 2 1 2` (three-line, README form) | `wrong answer: expected 4 colors, got 0`, exit 1 |
| same | two-line with invalid colors | WA same-color edge, exit 1 (known-bad) |
| single edge we wrote, K=1 | `1\n1\n1 1` (Q>0, three-line) | `Score = 9`, exit 0 (known-good answer with hits) |
| official cases 0001,0002,0003,0004,0007,0008 | Q=0, baseline coloring, **two-line** | WA "edge (...) has same color" in every case |
| same cases | Q=0, same coloring, **three-line** | WA "expected N colors, got 0" in every case |

On 37 of the 50 official cases, the input graph provably cannot be coloured with K colours without hits. A zero-hit answer on those cases is wrong in either format. We have no certificate for the remaining 13 fixed graphs; a probability bound under an assumed generator does not establish their actual colourability. A solver can use hits on the certified cases and zero hits elsewhere, so the 37 certificates do not establish zero effect on a complete submission.

- 37/50 cases have exact certificates (short proofs that the graph cannot be coloured with K colours):
  - 13 cases with K=1: any edge;
  - 12 cases with K=2: an odd cycle;
  - 6 cases with N=1000, K=3: an explicit K4 clique (four mutually linked vertices; we also checked the K4 in case 0043 separately);
  - 6 cases with N=1000, K=4: an explicit K5 clique.
- The other 13 cases have N=10000, K∈{3,4} and average degree 20, and admit no small certificate. A union bound (adding up the probabilities of every possible valid colouring) gives ln P ≤ −14895 for K=4 and ≤ −29550 for K=3. This assumes the cases came from the published uniform generator.

A single failed case voids the whole submission. The evaluator gives every wrong answer, timeout or runtime error a case score of `float('inf')` and adds it to the total (`/tmp/eval_vibrating_path.py`, lines 20, 35, 37, 39 and 54). One failed case therefore makes `TOTAL_SCORE inf`. EdgeBench's harness accepts it as raw infinity, for which `rescale_score` gives no score out of 100 (`sforge/harness/score_rescale.py:75-76`). That submission gets no score, although under `score_first` the run still keeps an earlier submission with no failed case. The prompt says only "Final score = sum of individual case scores" and does not say what a failed case scores.

On a 4-CPU grader, the promised 30 s per case shrinks to about 14 s of CPU; the fixed version corrects this. The README promises "Time limit | 30 seconds / test case" (line 54). The limit is wall-clock time (`TIME_LIMIT = 30`, line 9), and 8 cases run at once (`ProcessPoolExecutor(max_workers=min(8, len(case_files)))`, line 45). The task sets no CPU count. In EdgeBench's leaderboard configuration `examples/all-tasks-k8s/experiment.yaml` (quoted in [`evidence/impact/edgebench-leaderboard-config.md`](../evidence/impact/edgebench-leaderboard-config.md)) (sha256 `d9d299794ba946cae8d2b7f68a7879a35bb8565d95e78107edf79802993643be`), the grader inherits `judge_cpu_limit: 4`. Eight cases on 4 CPUs get about half a CPU each, and they share it with the task's Python tester, which takes 5.6 to 19.0 s of CPU per case (579.6 s for all 50 cases, measured one case at a time at 1 CPU on the greedy control's outputs, `repairs/vibrating_path_graph_coloring-v2/paired/tester_time.out`).

We measured this on the original grader at `--cpus 4` (`evidence/runs/vibrating_path_graph_coloring-cpu4v8-a/result/out/summary.txt`, `-b`; repeated in `vibrating_path_graph_coloring-v2-paired-a`).

| Valid solution (greedy control's output, preceded by fixed work) | 4 CPUs | 8 CPUs |
|---|---|---|
| 12 or 14 s of CPU per case | 50 OK, TOTAL 24,650,014 (slowest 14 s case: 29.9 s) | 50 OK, TOTAL 24,650,014 |
| 20 s of CPU per case (measured on two machines) | **2 OK, 48 TLE, TOTAL `inf` (no score)** | 50 OK, TOTAL 24,650,014 (2.06 out of 100) |
| works until a 25 s wall-clock deadline | 50 OK, TOTAL 24,650,014; median 12.7 s of CPU per case | 50 OK, TOTAL 24,650,014; median 24.9 s |

In one more original-grader run at 4 CPUs (`evidence/runs/vibrating_path_graph_coloring-v2-paired-b`), the 25 s deadline solution lost 14 cases (36 OK, 14 TLE, TOTAL `inf`). Every solution process in that run ended at most 27.14 s after its start, and all 14 timed-out cases are among the 25 cases with the slowest tester. The evaluator reports a timeout of the tester (its own `timeout=60`) with the same `TLE` label as a timeout of the solution. The likely cause is therefore the tester reaching its 60 s timeout with about half a CPU. We infer this cause and did not observe it, because that run did not log tester starts, and a repeat on another worker that did (`vibrating_path_graph_coloring-v2-paired-c`) passed 50/50 twice. Across all nine original-grader gradings of this solution (three runs each of `-b` and `-c`, the latter grading it twice per run), it failed only this once; under the fixed version it passed all six of its gradings ([repeatability](../repairs/vibrating_path_graph_coloring-v2/paired/results.md)).

The task ships with a note. For zero hits, the tester accepts a two-line output and rejects the README's three-line form with an empty hit line. Zero-hit answers are proved invalid for 37 official cases; the other 13 remain unresolved. Accepting both forms would remove the format mismatch, but such a parser repair is not part of this package, and we have not demonstrated that it leaves official scores identical.

## How much it matters

- On the original grader at the publisher's 4 CPUs, any valid solution using about 14 to 30 s of CPU per case loses its whole score (measured with 20 and 28 s per case); the fixed version scores these solutions. A solution that stops at a wall-clock deadline gets about twice the CPU per case under the fixed version (mean 12.84 s → 24.98 s for the 25 s deadline solution, `vibrating_path_graph_coloring-v2-paired-b`); we did not measure how much that changes its score. A solver sees the per-case TLE results after each submission, and the run keeps its best valid submission, so a run loses its score only if it never submits a faster valid solution.
- The all-or-nothing rule for one failed case is unchanged and still undisclosed.
- The zero-hit format has no score effect on the 37 certified cases. On the other 13 the effect is unresolved, because a valid zero-hit answer rejected for formatting would make the whole submission nonfinite. We have neither such an official-case witness nor a universal proof of zero effect.

## The fix

The fixed version (`repairs/vibrating_path_graph_coloring-v2/`) changes how many cases `/tmp/eval_vibrating_path.py` runs at once. A new function `cpu_quota_workers()`, the same as in `repairs/grid_turing_robot-v2/`, reads the grader's CPU quota from the cgroup (`cpu.max`, or the cgroup v1 quota and period), rounds it down to whole CPUs, falls back to `os.cpu_count()` when there is no quota, and keeps the result between 1 and 8. The pool becomes `ProcessPoolExecutor(max_workers=min(cpu_quota_workers(), len(case_files)))`. `docker run --cpus N` and the publisher's k8s backend both set this quota. With 8 or more CPUs the fixed grader runs 8 cases at once, exactly as the original.

The task JSON changes `judge.image_tag` and raises `judge.eval_timeout` from 600 to 900 s. With whole CPUs per case the grading takes longer, and this task's tester is slow. For valid solutions near the 30 s limit the worst case at 4 CPUs is (50 × 30 s + 579.6 s) / 4 + 3/4 × 49 s ≈ 557 s, only 7% under 600 s. The longest grading measured under the fixed version was 558.0 s (the 25 s deadline solution, `vibrating_path_graph_coloring-v2-paired-b`), so 600 s is too close. The 30 s limit, the README, the tester, the cases, the parser and the score scale are unchanged, and so is the rule that one failed case voids the submission.

The paired run used `--cpus 4` (one pair at `--cpus 8`) and the same solutions on both graders (`evidence/runs/vibrating_path_graph_coloring-v2-paired-a`, `-b`, `-c`, `result/out/summary.txt`; `repairs/vibrating_path_graph_coloring-v2/paired/results.md`).

| Solution | CPUs | Original grader | Fixed version |
| --- | ---: | --- | --- |
| greedy control, no extra work | 4 | 50 OK, TOTAL 24,650,014 (2.06) | 50 OK, TOTAL 24,650,014 (2.06) |
| **20 s of CPU per case** | 4 | **2 OK, 48 TLE, TOTAL `inf` (no score)** | **50 OK, TOTAL 24,650,014 (2.06)** |
| **28 s of CPU per case** | 4 | **2 OK, 48 TLE, TOTAL `inf` (no score)** | **50 OK, TOTAL 24,650,014 (2.06)** |
| works until a 25 s wall-clock deadline (job `-b`) | 4 | **36 OK, 14 TLE, TOTAL `inf`**; mean 12.84 s CPU per case | 50 OK, TOTAL 24,650,014; mean 24.98 s CPU per case |
| same, two more original runs and one fixed (job `-c`) | 4 | 50 OK, TOTAL 24,650,014 (both); 12.77 / 12.81 s CPU | 50 OK, TOTAL 24,650,014; 24.92 s CPU |
| 40 s of CPU per case (bad control) | 4 | 50 TLE, TOTAL `inf` | 50 TLE, TOTAL `inf` |
| 20 s of CPU per case | 8 | 50 OK, TOTAL 24,650,014 | 50 OK, TOTAL 24,650,014 |

Under the fixed version the slowest 28 s case took 28.12 s from start to end. Grading at 4 CPUs took 438.4 s (20 s per case), 508.6 s (28 s per case) and at most 558.0 s (25 s deadline), all inside the new 900 s `eval_timeout`. At `--cpus 1/2/3/4/8` the fixed grader runs 1/2/3/4/8 cases at once (`result/out/v2_workers.txt`).

At 8 or more grader CPUs the two versions grade the same way. At 4 CPUs a deterministic solution that finished every case in time under the original gets the same output and score under the fixed version, and a solution needing about 14 to 30 s of CPU per case is scored instead of getting no score. A solution that searches until a wall-clock deadline gets about twice the CPU per case, so its scores under the two graders at 4 CPUs are not comparable. Per-case CPU never decreases under the fixed version.

Two notes still ship with the fixed version.

1. For zero hits, the tester accepts only the two-line form, not the README's three-line form. A zero-hit answer is proved wrong on 37 official cases; score effects on the other 13 are unresolved.
2. One crashed, timed-out or malformed case makes the total `inf`, so the whole submission gets no score.

## How we checked it

- For the CPU runs and paired runs on E2B, valid solutions doing 12 to 28 s of CPU work per case, a 25 s wall-clock-deadline solution and a 40 s bad control ran on the original grader at `--cpus 4` and `--cpus 8` (`evidence/runs/vibrating_path_graph_coloring-cpu4v8-a`, `-b`) and side by side on the original and fixed graders (`vibrating_path_graph_coloring-v2-paired-a`, `-b`, `-c`), each job `status: exit=0`, in the digest-pinned grader image with `--network none --memory 4g`. Each solution runs our greedy control (greedy K-colouring, hits simulated by the shipped tester's rule), then does its extra work, then prints the control's answer, and logs its own start, end and CPU time per case (`result/out/timing/`). We measured the tester time per case separately at `--cpus 1` (`paired/tester_time.out`).

- The original tester and helper ran in the original public image, pinned by digest, with `--network none`. The inputs were graphs we wrote with two-line and three-line zero-hit outputs, a known-bad colouring, a known-good output with hits, and six official cases. `tools/bin/tester` is identical in the grader image and the agent's working image. We read `tools/README.md` from the working image.
- The exact certificates give, for 37 of the 50 official cases, a proof that the graph cannot be coloured with K colours (the other 13 have no certificate): an edge for K=1, an odd cycle for K=2, and explicit K4 or K5 cliques checked pair by pair.
- For the remaining large, sparse cases, we used a closed-form union bound under the published generator's model.

## Limits

- The fixed grader reads its CPU quota from the cgroup (`cpu.max`). We tested this with `docker run --cpus` only, not inside a Kubernetes pod, which is the backend EdgeBench's leaderboard settings use.
- Without a cgroup quota the fixed grader falls back to `os.cpu_count()`, which counts all of the host's CPUs, not the ones the grader may use (`os.sched_getaffinity`). Under a CPU-set limit with no quota (for example `docker run --cpuset-cpus`), or where the pod cannot see its own `cpu.max`, it can still run more cases at once than it has CPUs, as the original does. Using the affinity count would need a new paired run, so we did not change it.
- We ran no AI model or solver. The effects shown come only from test submissions and counterexamples we wrote.
- 13/50 cases rely on a probabilistic bound and assume the cases came from the published uniform generator. We did not find the exact seeds and ran no SAT refutation (a machine proof by a satisfiability solver).
- We did not review the vibrating-path graph rules themselves or examine past submissions.
- We measured the CPU dependence at 4 and 8 CPUs, on E2B workers with 8 vCPUs, with single-threaded fixed-work and deadline test solutions. We did not test multi-threaded solvers, or 3, 5, 6 and 7 CPUs.
- Deadline-based solvers get about twice the CPU per case under the fixed version at 4 CPUs, so their scores under the two graders are not comparable. We did not measure how much their scores change.
- We infer, and did not observe, the cause of the 14 timeouts of the 25 s deadline solution in one original-grader run (the tester's own 60 s timeout at half a CPU).
- The tester times, and so the 557 s bound behind the 900 s `eval_timeout`, are for the greedy control's outputs; other outputs may take longer to check. Below 3 grader CPUs the 900 s `eval_timeout` can bind before the 30 s per case (about 1,065 s of work at 2 CPUs). The quota is rounded down, so 2.5 CPUs run 2 cases at once.

## Reproduce

- Fixed version: `repairs/vibrating_path_graph_coloring-v2/` (`materialize.sh`, `repair.patch`, `source-lock.json`; fixed grader sha256 `3b72b9ed…bd23`). Paired runs: `repairs/vibrating_path_graph_coloring-v2/paired/run.sh` and `run-tester-log.sh` (as run: `evidence/runs/vibrating_path_graph_coloring-v2-paired-a/run.sh`, `-b`, `-c`); CPU runs on the original grader: `evidence/runs/vibrating_path_graph_coloring-cpu4v8-a/run.sh`, `-b`; tester time: `paired/tester_time.sh`.

- Tester forms: `evidence/scripts/vibrating_path_graph_coloring/run_tester_forms.sh` (inputs in `inputs/`; output `run_tester_forms.out`)
- Zero-hit certificates and bound: `evidence/scripts/vibrating_path_graph_coloring/zero_hit_reachability.py` (output `zero_hit_reachability.out`)
- Working-image documentation: `evidence/scripts/vibrating_path_graph_coloring/work_image_docs.out`
- Pinned identity:
  - Grader image: `seededge/edgebench.judge.vibrating_path_graph_coloring@sha256:db8a9741831762040afb7e9819f997eb5f5293641fd5cd97d27fce3880ce084e`.
  - Working image: `seededge/edgebench.work.vibrating_path_graph_coloring@sha256:ea4a4f4a959a5b0fcd4c884979f5a379b7ef73e3793719c4f80146a599e91c9e`.
  - Task JSON: sha256 `d3bba054…a9c5`.
  - `tools/bin/tester`: `b1c7694b8de3444c0459393b967851ad7d61e38a9a320222ce01ba7a1b446463`.
  - `README.md`: `d7a4af29cb6af5158aebaebadc3b7b991c505d3528bf523e715c6e340e719218`.
  - `/tmp/eval_vibrating_path.py`: `934a2b9de14bc1e155adab2a114d3dcf4d6fdbf48bedc860b78ca602ba3e9350`.
