# warehouse_forklift_routing v2: paired results

**Verdict: accepted** (time contract and CPU share). See "Paired run" (time limit, earlier fixed version, `--cpus 2`) and "CPU share at 4 CPUs" (current fixed version) below.

**History.** The first paired E2B job (`evidence/runs/warehouse_forklift_routing-v2-paired/`, launched
2026-10-12) lost its connection to the coordinator host during the host's out-of-memory restart
(launcher status `error:ReadTimeout elapsed 1838 s, killed: True`;
`../../../evidence/runs/warehouse_forklift_routing-v2-paired.launch.log`). It returned no `out/` archive and
no result. The unchanged job was re-run from a fresh directory as `-paired-b`.

## Paired run (time limit; earlier fixed version)

The first paired job was lost when the host restarted. Re-run on E2B
(`evidence/runs/warehouse_forklift_routing-v2-paired-b`, exit 0, worker killed), and repeated as `-rep2` and
`-rep3` (both `status: exit=0`). Every arm's counts and TOTAL_SCORE in `result/out/summary.txt` are the
same in all three runs. These runs used `--cpus 2` and the earlier fixed version (`TIME_LIMIT = 150`, 8 inputs at once, sha256 `eff6a69b…7b95`); "v2" in this table is that version.

| Submission | Role | v1 | v2 |
| --- | --- | --- | --- |
| generic valid control | valid | OK 50/50, TOTAL 46676.8 | OK 50/50, TOTAL 46676.8 |
| one honest bug | invalid | 49 OK + 1 WA → inf | 49 OK + 1 WA → inf |
| shipped starter | invalid | 50 WA → inf | 50 WA → inf |
| **13 s per test case (uses the promised budget)** | **trigger** | **50 TLE → inf** | **50 OK, TOTAL 46676.8** |
| near the 150 s per-input limit | trigger | 50 TLE → inf | 50 OK, TOTAL 46676.8 |

## CPU share at 4 CPUs (current fixed version, 2026-10-12)

**Question.** The grader runs 8 inputs at once under a wall-clock limit. At the publisher's leaderboard setting of 4 grader CPUs (`judge_cpu_limit: 4`) each input gets about half a CPU, so a solver needing more than about 75 s of CPU per input would time out under the 150 s limit. The current fixed version also limits parallelism to the cgroup CPU quota (`cpu_quota_workers()`, 1..8).

**Runs.** Four E2B jobs, `evidence/runs/warehouse_forklift_routing-v2-cpu4-a` to `-d` (`run.sh`, also copied as `paired/run-cpu4.sh`; `arms.txt`), each on one worker with 8 vCPUs and 7.9 GB RAM, each `status: exit=0` with its worker killed (`result/worker.json`). Every arm ran the task's original `eval_cmd` with `--network none --memory 4g --cpus N`, one container at a time, on three images (`result/out/eval_sha.txt`):

- **original grader:** pinned judge image, `/tmp/eval_warehouse_manager.py` sha256 `c5ff0c26…82fb` (`TIME_LIMIT = 60`, 8 at once);
- **earlier fixed version:** sha256 `eff6a69b…7b95` (`TIME_LIMIT = 150`, 8 at once);
- **current fixed version:** sha256 `afccb3bb…5a76` (`TIME_LIMIT = 150`, at most the CPU quota at once), the `materialize.outputs` value in `source-lock.json`.

`result/out/v2_workers.txt`: at `--cpus 1/2/4/8` the current fixed version reads `cpu.max` `100000/200000/400000/800000 100000` and runs 1/2/4/8 inputs at once. New submissions: `cpu80.py` and `cpu140.py` do a fixed 80 s or 140 s of single-thread CPU work per input and then run the generic valid control (both within the promised 150 s); they log start/end times to `result/out/timing/<arm>/`. The other submissions are the files of the runs above (same sha256 in `result/out/solutions_sha.txt`); the shipped starter was taken from the pinned work image and removed from the job directory after the run.

| Submission | CPUs | Original grader | Earlier fixed version | Current fixed version | Source |
| --- | ---: | --- | --- | --- | --- |
| **`cpu80` (80 s CPU per input)** | 4 | 50 TLE → inf, 421.1 s | **2 OK + 48 TLE → inf**, 981.3 s | **50 OK, TOTAL 46676.8**, 1070.8 s | `-cpu4-b` |
| **`cpu140` (140 s CPU per input)** | 4 | 50 TLE → inf, 421.1 s | **2 OK + 48 TLE → inf**, 1041.4 s | **50 OK, TOTAL 46676.8**, 1825.2 s | `-cpu4-c` (original), `-cpu4-a` |
| `cpu80` | 8 | not run | 50 OK, TOTAL 46676.8, 562.6 s | 50 OK, TOTAL 46676.8, 562.7 s | `-cpu4-c` |
| generic valid control | 4 | 50 OK, TOTAL 46676.8, 3.8 s | not run | 50 OK, TOTAL 46676.8, 4.1 s | `-cpu4-c` |
| one honest bug | 4 | 49 OK + 1 WA → inf | not run | 49 OK + 1 WA → inf | `-cpu4-c` |
| shipped starter | 4 | 50 WA → inf | not run | 50 WA → inf | `-cpu4-c` |
| 13 s per test case (sleep, 65 s per input) | 4 | 50 TLE → inf, 420.8 s | not run | 50 OK, TOTAL 46676.8, 847.2 s | `-cpu4-c` |
| near the limit (sleep, 135 s per input) | 4 | 50 TLE → inf, 420.8 s | not run | 50 OK, TOTAL 46676.8, 1757.4 s | `-cpu4-d` |

Times are the wall time of the whole grading run; counts and TOTAL are from each job's `result/out/summary.txt`.

**Per-input times** (`result/out/timing/`): under the current fixed version at 4 CPUs the slowest `cpu140` input took 140.58 s and the slowest `cpu80` input 83.23 s from start of work to end; under the earlier fixed version only 2 of 50 inputs finished in each arm. At 8 CPUs the earlier and current fixed versions gave the same per-input maximum (80.52 s and 80.63 s).

**Grading time** at 4 CPUs stayed inside the 3600 s `eval_timeout`: at most 1825.2 s.

**Verdict: accepted** (time contract and CPU share). Anchors unchanged by decision; ceiling ≈30.3 (≈30.6 after display rounding) documented.

## Repeatability (2026-10-13)

| job | arms | runs | identical? |
| --- | --- | --- | --- |
| `…-v2-paired-b`, `-rep2`, `-rep3` | the five arms of "Paired run" | 3 | yes (earlier) |
| `evidence/runs/warehouse_forklift_routing-v2-cpu4-a`, `-rep2`, `-rep3` | `cpu140` at 4 CPUs, current and earlier fixed version | 3 | yes |
| `…-cpu4-b`, `-rep2`, `-rep3` | `cpu80` at 4 CPUs, all three versions | 3 | yes |
| `…-cpu4-c`, `-rep2`, `-rep3` | 11 arms: the earlier controls at 4 CPUs under the original and current fixed version, `cpu80` at 8 CPUs, `cpu140` under the original | 3 | yes |
| `…-cpu4-d`, `-rep2`, `-rep3` | near-limit control at 4 CPUs, original and current fixed version | 3 | yes |

Each rerun used the job's `run.sh`, `arms.txt` and `sol/` unchanged, on a fresh E2B worker (8 vCPU). Every rerun has `status: exit=0`, and its worker was killed. Every arm gives the same OK/TLE/WA/RE counts and TOTAL in all three runs (`result/out/summary.txt`). Under the current fixed version, `cpu80` and `cpu140` at 4 CPUs pass 50/50 (TOTAL 46676.8) in every run. Under the original they time out on all 50, and under the earlier fixed version on 48 of 50, in every run. The `cpu140` arm at 4 CPUs is the one closest to its limit (slowest input 140.58 s against 150 s). Its grading time was 1824.8–1825.2 s in the three runs.

Staged inputs, removed after collection: both graders' evaluators (`pkg/files/`, `pkg-prev/files/`, sha256 `afccb3bb…` and `eff6a69b…`, as in each run's `eval_sha.txt`), and in `-cpu4-c` the shipped starter, an image file restored from the internal copy (sha256 `51149282…`, as in run 1's `solutions_sha.txt`).
