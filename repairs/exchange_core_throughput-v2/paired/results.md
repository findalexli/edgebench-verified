# Paired results: exchange_core_throughput v1 vs v2

E2B job `e2b/jobs/exchange_core_throughput-v2-paired-b` (exit 0, worker killed; first attempt lost
in a host restart). Original `eval_cmd`, `--network none`; v1 = pinned judge image with the missing
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
