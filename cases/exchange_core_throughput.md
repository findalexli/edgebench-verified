# Exchange Core Throughput (`exchange_core_throughput`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Systems & Software Engineering
- **Decision:** Repair v2. The original correctness check does not detect wrong fees or dropped events, so incorrect engines were scored above the correct one. v2 adds the project's own integration tests as a gate and grades offline.

## What the task promises

The solver optimizes the exchange-core matching engine to "maximize the throughput (MT/s — millions of transactions per second) of `PerfThroughput#testThroughputPeak`". The rules say "Do NOT change behavior: `mvn test` must still pass functional assertions". They also say "`CASES_OK = 1` only when `mvn test` exits 0 AND an MT/s line was parsed". The score is `int(round(Average_MT_s * 1000))`, rescaled with `log_max` (baseline 2090.634594076933, expert 6000).

## What we checked and how

- We made two plausible one-edit changes to the shipped engine and ran each through the task's verbatim `eval_cmd` in the pinned judge image. Each run used an E2B worker with 8 vCPUs, a fresh container, `--network none`, `--cpus 8` and `--memory 6g`.
- Independent oracle: the project's own shipped integration tests (`ITFeesExchangeBasic`, 5 tests, and `ITExchangeCoreIntegrationRejectionBasic`, 28 tests). They ran in the same container with the evaluator's exact Maven flags.
- Paired evaluation: the same submissions, plus valid and invalid controls, were scored by the original (v1) and repaired (v2) evaluators in one E2B job. Both used `--network none`.
- Original identity:
  - Judge image: `seededge/edgebench.judge.exchange_core_throughput@sha256:6b1617315cd2…`.
  - Task JSON: sha256 `fc64c74d1aad…`.
  - `/tmp/eval_exchange_core.py`: sha256 `65bfba1129ef…`.
  - `ThroughputTestsModule.java`: sha256 `dd5a5873…be29`.
  - `PerfThroughput.java`: sha256 `e0e45d82…ccc1`.

## What we found

**Confirmed: incorrect engines pass the correctness check and are rewarded.** The throughput test's correctness check compares only two things: the global balance, which must be zero, and the L2 order books. The test source marks the missing comparisons with `// TODO compare events, balances, positions`. We tested two incorrect engines:

- **feeswap.** A copy-paste fee bug: the selling taker is charged the maker fee instead of the taker fee. The exchange fee ledger books the same wrong amount, so the global balance stays exactly zero. Sellers are over-credited, and the exchange's fee income is under-booked on every sell-taker trade.
- **dropevents.** The results stage no longer forwards command results, trade events, reduce events or reject events to the user's results consumer. The API futures still complete.

Under the original evaluator, both engines passed `testThroughputPeak` in all 50 asserted rounds. Maven exited 0, and the eval printed `CASE 0000 OK` and `CASES_OK 1`. In the native addendum's single runs:

| variant | TOTAL_SCORE | normalized (log_max) |
|---|---|---|
| control (shipped engine) | 2254 | **7.14** |
| feeswap (wrong balances) | 2704 | **24.40** |
| dropevents (dropped events) | 2465 | **15.62** |

The project's integration tests reject both engines and pass the control. With feeswap, 2 of 5 `ITFeesExchangeBasic` tests fail. For example, `shouldProcessFees_BidGtcMaker_AskIocTakerPartial` expected `<199061711100L>` and got `<199063788300L>`. With dropevents, all 28 `ITExchangeCoreIntegrationRejectionBasic` tests fail because the handler receives no command results.

Maximum score effect shown: 7.1 → 24.4 normalized for a buggy engine. feeswap does the same work as the control, so the ranking among these three is throughput noise and not a speed effect of the bugs. The finding is that incorrect engines receive full credit.

**Confirmed: the original judge cannot grade offline.** The pinned image's `~/.m2` lacks `surefire-junit-platform:3.0.0-M3`. With `--network none`, every submission fails, including the unmodified engine (`CASE 0000 RE score=0 / TOTAL_SCORE 0`). The harness gives the judge container network access, and `internet: false` covers only the agent container (coordinator-checked). So v1 grading depends on reaching Maven Central at grading time.

An earlier record said "actual incorrect-engine reward is unproved". This run replaces that wording: the reward is now shown through the real JVM path.

## Repair

Before the unchanged timed test, v2 runs the project's shipped integration tests `ITFeesExchangeBasic` and `ITExchangeCoreIntegrationRejectionBasic` (33 tests) in a separate Maven invocation. If any of them fails, the submission scores 0 (`WA`). The timed run is unchanged. v2 also pre-seeds the missing public Maven Central files into the image's `~/.m2`, so it grades with no network.[^3] For the paired v1 arms, the same files were mounted so that v1 could run offline. The "v1raw" row shows the image without them.

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

Raw score is MT/s × 1000. The controls are:

- `topo21` is the prompt's own example optimization: 4ME+2RE changed to 2ME+1RE.
- `feeleak` charges the wrong fee without booking it consistently, which breaks the global-balance assertion.
- `compileerr` does not compile.

**Score compatibility:** correct engines score as in v1, although throughput is noisy from host to host. Incorrect engines that v1 rewarded now score 0. v2 scores are not comparable with v1 leaderboard entries.

## Limits and what was not run

- No model or solver re-runs were done. Effects are shown only on authored controls and counterexamples.
- Throughput varies by about ±20% from run to run on the same worker: the control ran at 2,050–2,978 raw. The native addendum used one run per variant, so its normalized figures are not a variance-controlled comparison.[^4]
- The two integration test classes cover fees, rejections and events. They do not cover every engine invariant, so an engine with other kinds of wrong behaviour could still pass the v2 gate.
- v2 does not compare per-user balances, positions or the event stream against a reference run. The review suggested that comparison, but v2 uses the shipped integration tests instead.
- Only two incorrect-engine mutations were tested.

## Reproduce

- Original-evaluator runs with incorrect engines: `evidence/runs/exchange_core_throughput-wrongengine/run.sh`.
- Integration-test oracle: `evidence/runs/exchange_core_throughput-oracletests/run.sh`.
- Paired v1/v2 evaluation: `repairs/exchange_core_throughput-v2/paired/run.sh`. The variant definitions are in `paired/mutate.py`.
- Repair package: `repairs/exchange_core_throughput-v2/`, which contains `Dockerfile`, `repair.patch`, `files/` and `source-lock.json`.
- Supporting records: `repairs/exchange_core_throughput-v2/paired/results.md` and `evidence/reviews/exchange_core_throughput-native.md`.

[^3]: The repair README and the native review describe the missing files as "three public Maven artifacts". `source-lock.json` and the paired `run.sh` record 30 added files from Maven Central (surefire, JUnit platform, opentest4j and apiguardian artifacts). This page uses the source-lock record because it is the exact package manifest.
[^4]: The native addendum's single runs (control 2254, feeswap 2704, dropevents 2465) differ from the paired job's v1 runs (control 2050 and 2210, feeswap 2269, dropevents 2234). These are separate runs, and both sets are quoted as recorded. `decisions.json` summarizes the paired trigger runs as "OK ~2250".
