# Paired v1/v2 results — triangulation_coloring_optimization-v2

One E2B job (`run.sh`; job dir `evidence/runs/triangulation-v2-paired`, worker
killed by exact ID, exit 0, ~41 s). v1 = original judge/work images pulled by digest; v2 = images
built in the worker from `../Dockerfile` and `../Dockerfile.work`. Original `eval_cmd`,
`--network none --memory 4g`. Raw logs in `result/out/`. Parsed with the maintained
`score_sum` parser rules and rescaled with `score_rescale.py` and the (unchanged) anchors
(`normalize.py` → `normalize.out.jsonl`). In-image sha256 checks (`result/out/hashes_*.txt`):
v2 differs from v1 exactly in `triangulation.py`, the 10 cases and the 3 sample inputs.

## Full judge (`eval_cmd`, 10 hidden cases)

| submission | role | v1 raw | v1 cases OK | v1 normalized | v2 raw | v2 cases OK | v2 normalized |
|---|---|---:|---|---:|---:|---|---:|
| shipped `solution.py` (do nothing) | valid control | 6,092,430 | 10/10 | 0.055 | 6,092,622 | 10/10 | 0.054 |
| `greedy.py` (greedy recolour + greedy README-legal convex flips) | independent honest control | 866,166 | 10/10 | 48.87 | 863,058 | 10/10 | 48.95 |
| `nonconvex_flip.py` (do nothing + one README-forbidden non-convex flip per case) | **trigger** | 6,093,050 | 10/10 accepted | 0.052 | inf | 0/10 (WA "Invalid flip") | none (raw inf) |
| `wrong_count.py` (recolours vertex 1, claims C=0) | invalid control | inf | 0/10 (WA) | none (raw inf) | inf | 0/10 (WA) | none (raw inf) |

Docker exit 0 for all eight runs (the evaluator always exits 0). `TOTAL_SCORE inf` gives no score
out of 100: EdgeBench's harness keeps the raw `inf`, and `rescale_score` returns None for it. Valid controls: normalized scores change by ≤0.08 points;
raw changes are fully explained by the new instances for cases 0001–0009 (same anchors).
The earlier review also showed a v1 forbidden flip that *improves* the score
(case 0009, edge 39–52: 644,809 → 641,611); re-scoring that saved output
(`scripts/triangulation_coloring_optimization/case0009_one_nonconvex_flip.out`) on the original
case 0009 locally: original verifier `Score: 641611`; verifier with v2 `triangulation.py`
`INVALID: Invalid flip (39,52)`.

## Same inputs, rule only (tester in each judge image; `rule_v1.log`, `rule_v2.log`)

| input | v1 tester | v2 tester |
|---|---|---|
| N=4 valid 2-triangle input with reflex quadrilateral, flip 1–2 (review control) | accepted, `Score = 41` (result overlaps) | `wrong answer: Invalid flip (1,2)` |
| each v2 hidden case + its first non-convex flippable-under-v1 edge (10 inputs) | 10/10 accepted | 10/10 `Invalid flip` |

## Solver-visible loop (work image `eval_sample_data.sh` + `tools/bin/tester`)

| submission | v1 SAMPLE_TOTAL | v2 SAMPLE_TOTAL |
|---|---:|---:|
| do nothing | 1,780,251 | 1,802,171 |
| greedy | 263,500 | 258,183 |
| nonconvex_flip | 1,780,471 (accepted) | all 3 `wrong answer: Invalid flip` |

So the local tester the prompt says "applies flips exactly like the judge" now enforces the
same README rule as the v2 judge.

## Input validity (review's exact-integer checker, `geometry_v2.jsonl`)

All 13 regenerated files: 0 overlapping triangle pairs, 0 crossing edge pairs, 0 folded edges,
0 duplicate/degenerate triangles, 0 non-manifold edges, 0 vertices strictly inside a triangle,
V−E+F = 1, 0 bad vertex links, 0 unused vertices, 0 collinear triples (checked during
generation). Residual: 12/13 miss 1–3 convex-hull triangles (shipped Delaunay artifact; see README).
Originals for comparison: 17–583 overlapping pairs per file (review).

## Flip predicate equivalence (`rule_check.jsonl`, 26 files)

On every original and v2 input: v2 predicate == the exact convex-quadrilateral test in
`rule_check.py` on every edge (0 mismatches), and v2 ⊆ v1 (0 edges allowed by v2 but not v1). That
test includes the v2 guards `a != b` and "edge ab does not exist", so it is not independent of them.
Without those guards (`convex_flippable` in `flip_rules.jsonl`), the original hidden cases have
2, 1, 2, 2, 2, 19, 17, 24, 20 and 23 on hidden cases 0000–0009 strictly convex flips that v2 rejects because ab already exists in
the folded mesh. The v2 inputs are valid triangulations and have none. v1 allows
1,250–1,503 edges per file; v2 allows 861–1,171.

## CPU-quota parallelism (added 2026-10-12)

**Runs.** Two E2B jobs, both `status: exit=0`, workers killed (`result/worker.json`, ledger `evidence/runs/ledger.jsonl`):

- `evidence/runs/triangulation-v2-paired-cpu` (904 s; `run-cpu4.sh` and `arms-cpu4.txt` in this directory are copies of its `run.sh` and `arms.txt`). Three graders on the same solutions, original `eval_cmd`, `--network none --memory 4g --cpus N`, one container at a time: the **original grader** (digest-pinned image, evaluator sha256 `1c5100f5…c009`), the **previous fixed version** (`v2prev`: flip rule and regenerated inputs, original evaluator) and the **fixed version** (`v2`: the same plus the evaluator with `cpu_quota_workers()`, sha256 `082d72b2…acb1`). The fixed version and the previous fixed version have identical cases and tools (`result/out/eval_sha.txt`). The fixed grader computes 1/2/3/4/8 cases at once at `--cpus 1/2/3/4/8` (`result/out/v2_workers.txt`). Each solution is a wrapper around the honest `greedy.py` control (mounted as `/ebvsol/base.py`): it runs the control, then works until W CPU-seconds in total (`cpuW`) or W seconds of wall clock (`wall25`), then prints the control's answer. `cpu0` is the control alone; `spin40` (40 s of CPU) must time out.
- `evidence/runs/triangulation-v2-paired-cpu-controls` (61 s): the package's own `run.sh` (above) unchanged except for `--cpus` and the output directory, run against the fixed version at `--cpus 8` (as originally) and at `--cpus 4`.

**Results** (source: `evidence/runs/triangulation-v2-paired-cpu/result/out/summary.txt`, per-case times `timing_summary.txt`; score out of 100 via `sforge/harness/score_rescale.py`). The original grader scores the original cases; both fixed graders score the regenerated cases, so valid totals differ (866,166 against 863,058; 48.87 against 48.95), as in the table at the top.

| Solution | CPUs | Original grader | Previous fixed version | Fixed version |
| --- | ---: | --- | --- | --- |
| `cpu0` (control alone) | 4 | 10 OK, 866,166 | 10 OK, 863,058 | 10 OK, 863,058 |
| **`cpu20` (20 s CPU per case)** | 4 | **2 OK, 8 TLE, inf (no score)** | **2 OK, 8 TLE, inf** | **10 OK, 863,058 (48.95)** |
| **`cpu28` (28 s CPU per case)** | 4 | **2 OK, 8 TLE, inf** | **2 OK, 8 TLE, inf** | **10 OK, 863,058** |
| `wall25` (works until 25 s wall clock) | 4 | 10 OK, 866,166 | 10 OK, 863,058 | 10 OK, 863,058 |
| `spin40` (bad control, 40 s CPU per case) | 4 | 10 TLE, inf, 60.5 s | 10 TLE, inf, 60.5 s | 10 TLE, inf, 90.5 s |
| `cpu20` | 8 | 10 OK, 866,166, 40.8 s | 10 OK, 863,058, 40.8 s | 10 OK, 863,058, 40.7 s |

The previous fixed version fails `cpu20` and `cpu28` exactly as the original does, so the cap, not the flip-rule change, is what restores them. Under the fixed version at 4 CPUs the slowest `cpu28` case finished in 28.03 s of wall time. The `wall25` solution got a mean of 15.00 s of CPU per case under the original grader (median 12.50 s; 2 of 10 cases ran alone at the end) and 24.91 s under the fixed version. Grading the bad control took 90.5 s under the fixed version (3 rounds × 30 s), inside the 1200 s `eval_timeout`.

**Existing controls re-run against the fixed version** (source: `evidence/runs/triangulation-v2-paired-cpu-controls/result/out/c8/`, `c4/`). At both `--cpus 8` and `--cpus 4`, every result in the tables above is reproduced exactly: do-nothing 6,092,430 (original) and 6,092,622 (fixed), 10/10 OK; `greedy` 866,166 and 863,058; `nonconvex_flip` 6,093,050 accepted by the original and `inf` (10 × WA "Invalid flip") under the fixed version; `wrong_count` `inf` under both; the rule-only check (`rule_v1`/`rule_v2`: 0 and 11 `Invalid flip`); and the solver-visible sample totals (1,780,251 / 1,802,171, 263,500 / 258,183, `nonconvex_flip` 1,780,471 accepted and 3 × `Invalid flip`). The in-image hashes (`hashes_judge.txt`) differ from the previous fixed version only in `/tmp/eval_triangulation_coloring.py`.

**Limits.** Single-threaded test solutions only; multi-threaded solvers were not tested. Deadline-based solvers get more CPU at 4 CPUs under the fixed version, so their scores there are not comparable with the original grader's. The previous fixed version was run only in this job; it is not shipped.

## Verdict

Trigger: v1 wrong (accepts forbidden flip), v2 right (rejects). Valid controls: accepted in both,
normalized score unchanged within 0.08. Invalid control: rejected in both. CPU-quota addition: at 4 CPUs the 20 s and 28 s fixed-work solutions go from 8 TLE (no score) to 10 OK; the control, deadline and 8-CPU arms keep their results; the 40 s bad control times out under both; all earlier controls reproduce exactly. **Accepted.**

## Repeatability (2026-10-13)

| job | arms | runs | identical? |
| --- | --- | --- | --- |
| `…-v2-paired`, `-rep2`, `-rep3` | the four flip-rule controls (full judge) | 3 | yes (earlier) |
| `evidence/runs/triangulation-v2-paired-cpu`, `-rep2`, `-rep3` | the six CPU-quota arms × original, earlier fixed and current fixed version (18 results) | 3 | yes |
| `evidence/runs/triangulation-v2-paired-cpu-controls`, `-rep2`, `-rep3` | the four flip-rule controls against the current fixed version, at 8 and 4 CPUs (16 results) | 3 | yes |

Each rerun used the job's `run.sh` and inputs unchanged, on a fresh E2B worker. Every rerun has `status: exit=0`, and its worker was killed. Every arm gives the same OK/TLE/WA/RE counts and TOTAL in all three runs, and the controls give the same `cases_ok`, validity and normalized score. Only wall times differ. Staged inputs, removed after collection: the materialized `pkg/files/` and `pkgprev/files/` (evaluator sha256 `082d72b2…`, `triangulation.py` `8b5b9cbb…`, cases equal to run 1's `hashes_judge.txt`), and the shipped `donothing.py`, an image file.
