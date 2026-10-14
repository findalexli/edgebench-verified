# Paired results: exchange_core_throughput v1 vs v2

E2B job `evidence/runs/exchange_core_throughput-v2-paired-b` (exit 0, worker killed; first attempt lost
in a host restart), repeated as `-rep2` and `-rep3` with the same verdicts. Original `eval_cmd`, `--network none`; v1 = pinned judge image with the missing
public Maven artifacts copied into `~/.m2` (else every v1 run is `RE`, see "v1raw"); v2 =
image built from this package's Dockerfile. Raw score = MT/s × 1000.

| Submission | Role | v1 | v2 |
| --- | --- | --- | --- |
| unmodified engine, original image without artifacts ("v1raw") | setup control | RE, 0 | — |
| unmodified engine (control, run 1) | valid | OK 2050 | gate OK (33 tests), OK 2153 |
| unmodified engine (control, run 2) | valid | OK 2210 | gate OK, OK 2978 |
| `topo21` honest variant | valid | OK 2524 | gate OK, OK 2481 |
| `feeswap` (fee swap, balance kept at zero) | **trigger** | **OK 2269** | **WA 0 (gate failed)** |
| `dropevents` (user events not forwarded) | **trigger** | **OK 2234** | **WA 0 (gate failed)** |
| `feeleak` | invalid | RE 0 | WA 0 |
| `compileerr` | invalid | RE 0 | WA 0 |

**Verdict: accepted.** Both incorrect engines that v1 rewarded are rejected; valid engines keep
scoring; invalid controls are rejected in both. Throughput noise between runs is large (see Limits).

## Repeatability (`evidence/runs/exchange_core_throughput-v2-paired-b{,-rep2,-rep3}/result/out/summary.txt`)

| Submission | v1 runs 1/2/3 | v2 runs 1/2/3 |
| --- | --- | --- |
| unmodified engine (control, run 1) | OK 2050 / 2008 / 2054 | OK 2153 / 3105 / 2293 |
| unmodified engine (control, run 2) | OK 2210 / 2698 / 2542 | OK 2978 / 2729 / 2750 |
| `topo21` | OK 2524 / 3003 / 2440 | OK 2481 / 3222 / 2387 |
| `feeswap` | OK 2269 / 2643 / 2307 | WA 0 in all three |
| `dropevents` | OK 2234 / 2457 / 2197 | WA 0 in all three |
| `feeleak`, `compileerr` | RE 0 in all three | WA 0 in all three |

## Limits

- Throughput varies by up to 38% between runs; the unmodified engine ran at 2,008–3,105 raw, and
  runs below the 0-point reference 2,090.63 score 0 out of 100.
- The fixed grader also sets the score to 0 when the timed run's status is not `OK`
  (`repair.patch`, `if status != "OK": score = 0`); see the appendix.

## Appendix: the second change (`if status != "OK": score = 0`), tested 2026-10-12

E2B job `evidence/runs/exchange_core_throughput-v2-paired-shutdownfail` (exit 0). Same layout as `run.sh`.
The v2 image is built on the worker from this package: `materialize.sh` reports all 31 outputs match `source-lock.json`, and the v2 eval sha256 is `b957210f…`.
`shutdownbusy` makes `ExchangeCore.shutdown()` throw the core's own "could not stop a disruptor gracefully" exception after
the disruptor stops, only for the `BUSY_SPIN` wait strategy (the throughput configuration). The gate's tests use `BLOCKING`.
`shutdownall` throws in every configuration. Harness = this repo's `grade_output` + `rescale_score`.

| Submission | v1 | v1 harness | v2 | v2 harness |
| --- | --- | --- | --- | --- |
| control | OK 3356 | valid, 44.89 | gate OK, OK 3565 | valid, 50.62 |
| `shutdownbusy` run 1 | **WA 2939** (`CASES_OK 0`) | **valid, 32.31** | gate OK, **WA 0** (Average 3.505 printed) | valid, 0 |
| `shutdownbusy` run 2 | **WA 2943** | **valid, 32.44** | gate OK, **WA 0** (Average 3.917 printed) | valid, 0 |
| `shutdownall` | WA 3382 | valid, 45.62 | WA 0 (gate failed) | valid, 0 |

The original grader credits a run whose `mvn test` fails after the average, and the harness ranks it on `TOTAL_SCORE`.
The fixed grader scores it 0, as the task rule "`CASES_OK = 1` only when `mvn test` exits 0" implies.
No honest engine reached this path: the control and `topo21` were `OK` in all 18 v2 timed runs (paired-b, rep2, rep3, the three shutdown-failure jobs and the six leaderboard-setting runs below).
The arm is a construction, not code from a real solver. The cause of the non-zero exit is inferred from the arm's only difference, because the grader does not print Maven's output on this path.

## Repeatability of the shutdown-failure job (2026-10-13)

`evidence/runs/exchange_core_throughput-v2-paired-shutdownfail` was run three times on fresh E2B workers (`-rep2`, `-rep3`) with the same `run.sh` and `inputs/`. Every run has `status: exit=0`, and its worker was killed. Each worker rebuilt the fixed version with `materialize.sh`. All 8 graded results give the same verdict in all three runs: the control is OK under both graders with the gate OK under v2, every `shutdownbusy` and `shutdownall` run is WA under v1, and every one scores 0 under v2 (gate failed for `shutdownall`, case WA for `shutdownbusy`). The throughput numbers move between runs, as in the main repeatability table: the control 2813–3356 (v1) and 2422–3565 (v2), and the WA triggers' v1 numbers 2354–3382. No verdict depends on them.

## Leaderboard judge setting: `--cpus 4 --memory 8g` (2026-10-13)

E2B jobs `evidence/runs/exchange_core_throughput-v2-cpu4m8g-rep1` (worker `iqucqbtf1ovjiqrpqeld8`, 623 s), `-rep2` (`iylihb2yjojg61k5dgyv9`, 683 s) and `-rep3` (`i7ova1zxddz4t5cvq00ro`, 643 s), each ledger `status: exit=0` with `done fail=0`. Layout of `exchange_core_throughput-cpu4v8-a/run.sh`, with the v2 image built in each worker from this package (`materialize.sh`: all 31 outputs match `source-lock.json`, v2 eval `b957210f…`; then `docker build`). Every arm ran the original `eval_cmd` with `docker run --network none --cpus 4 --memory 8g`, the leaderboard's `judge_cpu_limit: 4` and `judge_mem_limit: 8g` (inside: `nproc` 8, `cpu.max` `400000 100000`, `memory.max` 8589934592). v1 had the same 30 Maven files mounted at `/root/.m2`. Raw score = MT/s × 1000; all are below the 0-point reference 2,090.63, so every one is 0 out of 100.

| Submission (4 CPUs, 8g) | Role | v1 | v2 |
| --- | --- | --- | --- |
| unmodified engine, 4 CPUs run 1 | valid | OK 1059 | gate OK (33 tests), OK 1194 |
| unmodified engine, 4 CPUs run 2 | valid | OK 965 | gate OK (33 tests), OK 811 |
| unmodified engine, 4 CPUs run 3 | valid | OK 972 | gate OK (33 tests), OK 1073 |
| `topo21`, 4 CPUs run 1 | valid | OK 1644 | gate OK (33 tests), OK 1687 |
| `topo21`, 4 CPUs run 2 | valid | OK 1994 | gate OK (33 tests), OK 1684 |
| `topo21`, 4 CPUs run 3 | valid | OK 1894 | gate OK (33 tests), OK 1832 |

The gate passed (`GATE OK ITFeesExchangeBasic,ITExchangeCoreIntegrationRejectionBasic tests=33`) in all six v2 runs. v2 raw scores are within throughput noise of v1 (v2 811–1194 lies partly below and partly above all seven v1 4-CPU runs, 939–1059): unmodified engine 811–1194 (v2) against 965–1059 (v1) and the earlier v1 4-CPU runs at `--memory 4g`, 939–1033; `topo21` 1684–1832 (v2) against 1644–1994 (v1) and the earlier single v1 run, 2091. Wall time per v2 run, gate included, was 168–228 s for the unmodified engine and 116–126 s for `topo21`, against the 2,400 s `eval_timeout`. The gate therefore does not change the 4-CPU result: both honest engines keep scoring as under v1, and both score 0 out of 100 at this setting, as noted in the case page.

