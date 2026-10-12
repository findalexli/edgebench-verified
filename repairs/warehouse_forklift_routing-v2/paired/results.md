# warehouse_forklift_routing v2: paired results

**Verdict: NOT ACCEPTED (paired evaluation not collected).** The package is built, but no paired
result exists yet, so acceptance conditions 1-3 of REPAIR-SPEC are unverified.

The one paired E2B job (`e2b/jobs/warehouse_forklift_routing-v2-paired/`, launched 2026-10-12) lost its connection to the
coordinator host during the host's out-of-memory restart: launcher status `error:ReadTimeout elapsed 1838 s, killed: True`
(`e2b/jobs/warehouse_forklift_routing-v2-paired/result/worker.json`, `../../../evidence/runs/warehouse_forklift_routing-v2-paired.launch.log`).
`result/` holds only `worker.json`; no `out/` archive was retrieved, and the worker is gone, so
no arm's score is known. Nothing here says whether the repair works.

| arm | v1 | v2 | expected | ok |
| --- | --- | --- | --- | --- |
| all arms in `paired/run.sh` | not run (lost) | not run (lost) | see run.sh | not run |

**Next step.** Re-launch the unchanged job from a fresh directory (copy
`e2b/jobs/warehouse_forklift_routing-v2-paired/` without `result/` to `e2b/jobs/warehouse_forklift_routing-v2-paired-b/`); the launcher
refuses to reuse an existing `result/`. This is a collection failure, not a scientific result.

## Paired run

The first paired job was lost when the host restarted. Re-run on E2B
(`e2b/jobs/warehouse_forklift_routing-v2-paired-b`, exit 0, worker killed):

| Submission | Role | v1 | v2 |
| --- | --- | --- | --- |
| generic valid control | valid | OK 50/50, TOTAL 46676.8 | OK 50/50, TOTAL 46676.8 |
| one honest bug | invalid | 49 OK + 1 WA → inf | 49 OK + 1 WA → inf |
| shipped starter | invalid | 50 WA → inf | 50 WA → inf |
| **13 s per test case (uses the promised budget)** | **trigger** | **50 TLE → inf** | **50 OK, TOTAL 46676.8** |
| near the 150 s per-input limit | trigger | 50 TLE → inf | 50 OK, TOTAL 46676.8 |

**Verdict: accepted** (time contract). Anchors unchanged by decision; ceiling ≈30.3 documented.
