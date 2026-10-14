# Exchange Core Throughput (`exchange_core_throughput`)

**Outcome:** Fixed. <mark>The original correctness check does not catch wrong fees or lost messages, so incorrect engines receive full credit; the fixed version requires the project's own integration tests to pass and grades without network access.</mark>

![A grid of pass and fail marks. Rows: the correct engine, an engine that charges sellers the wrong fee rate (the rate for orders that wait on the book instead of the rate for orders that trade at once), and an engine that never delivers trade messages. Under the original checker all three pass and are scored on speed; under the fixed checker, which also runs 33 of the project's own tests, the correct engine passes and both broken engines are rejected with a score of 0. Notes explain the speed score (0 at 2.09 million transactions per second or slower, 100 at 6 million), give the overlapping speed scores (correct engine 0–24.19, wrong fee 7.77–24.40, lost messages 4.71–15.62 out of 100), and say that at 4 CPUs even the correct engine scores 0 for speed.](figures/exchange_core_throughput.svg)

*Two engines with realistic bugs pass the original checker and are scored on speed; the fixed checker rejects them. The agent must make a stock-exchange matching engine faster without changing what it does, but the original checker only confirms that money balances overall and that the order books match, so an engine that charges selling traders the wrong fee and one that never delivers trade messages both pass and get a speed score out of 100 (7.77–24.40 and 4.71–15.62 over four runs each, against 0–24.19 for the correct engine over seven; the differences are run-to-run variation). The fixed checker first runs 33 of the project's own tests: both broken engines score 0 in all three side-by-side runs, and the correct engine still passes, also in three runs at the leaderboard's 4 CPUs, where it is too slow to score above 0 for speed.*

## What the task asks

The agent speeds up exchange-core, a stock-exchange matching engine (software that pairs buy and sell orders). The goal is to "maximize the throughput (MT/s — millions of transactions per second) of `PerfThroughput#testThroughputPeak`".

The rules say "Do NOT change behavior: `mvn test` must still pass functional assertions". They also say "`CASES_OK = 1` only when `mvn test` exits 0 AND an MT/s line was parsed". The raw result (before conversion to 0–100) is `int(round(Average_MT_s * 1000))`. It is converted to a score out of 100 on a logarithmic scale (`log_max`). The reference point for 0 is 2090.634594076933 and the reference point for 100 is 6000. Category: Systems & Software Engineering.

## What goes wrong

**Incorrect engines pass the correctness check and are rewarded.** The throughput test's correctness check compares only two things. The global balance must be zero, and the L2 order books (the price levels of resting orders) must match. The test source marks the missing comparisons with `// TODO compare events, balances, positions`. Two plausible one-edit changes to the shipped engine show the effect:

- **feeswap.** A copy-paste fee bug: the selling taker (the trader whose order executes immediately) is charged the maker fee instead of the taker fee. The exchange fee ledger books the same wrong amount, so the global balance stays exactly zero. Sellers are over-credited, and the exchange's fee income is under-booked on every sell-taker trade.
- **dropevents.** The results stage no longer forwards command results, trade events, reduce events or reject events to the user's results consumer. The API futures (the calls' return values) still complete.

Under the original grader, both engines passed `testThroughputPeak` in all 50 checked rounds. Maven exited 0, and the grader printed `CASE 0000 OK` and `CASES_OK 1`. Single runs:

| Engine | TOTAL_SCORE (raw result) | Score out of 100 (log_max) |
|---|---|---|
| correct test submission (shipped engine) | 2254 | **7.14** |
| feeswap (wrong balances) | 2704 | **24.40** |
| dropevents (dropped events) | 2465 | **15.62** |

The project's integration tests reject both engines and pass the correct one. With feeswap, 2 of 5 `ITFeesExchangeBasic` tests fail. For example, `shouldProcessFees_BidGtcMaker_AskIocTakerPartial` expected `<199061711100L>` and got `<199063788300L>`. With dropevents, all 28 `ITExchangeCoreIntegrationRejectionBasic` tests fail because the handler receives no command results.

feeswap does the same work as the correct engine. So the ranking among these three is throughput noise, not a speed effect of the bugs. The finding is that incorrect engines receive full credit.

**The original grader cannot grade offline.** The pinned image's `~/.m2` (the local Maven cache) lacks `surefire-junit-platform:3.0.0-M3`. With `--network none`, every submission fails, including the unmodified engine (`CASE 0000 RE score=0 / TOTAL_SCORE 0`). The harness gives the grader container network access, and `internet: false` covers only the agent container. So the original grading depends on reaching Maven Central at grading time.

**Note: the grader's CPU budget is not stated, and at 4 CPUs the shipped engine scores 0.** The prompt describes the engine's thread topology ("builder defaults (4ME+2RE, msgsInGroupLimit=4096, BUSY_SPIN wait, DirectImpl orderbook, AffinityThreadFactory)") and says "thread topology changes (e.g. 4ME+2RE → 2ME+1RE) can have dramatic impact", but it states no CPU count. In EdgeBench's leaderboard configuration `examples/all-tasks-k8s/experiment.yaml` (quoted in [`evidence/impact/edgebench-leaderboard-config.md`](../evidence/impact/edgebench-leaderboard-config.md)) (sha256 `d9d299794ba946cae8d2b7f68a7879a35bb8565d95e78107edf79802993643be`), the grader inherits `judge_cpu_limit: 4`. That limit is a CPU quota: inside the grader container at `--cpus 4`, `nproc` still reports 8 while `/sys/fs/cgroup/cpu.max` reads `400000 100000` (recorded by `evidence/runs/exchange_core_throughput-cpu4v8-a/run.sh`, line 17; the output file is kept out of the repository with the image excerpts). So an engine that sizes itself by `nproc` sees 8 CPUs.

Measured on the original grader with the original eval_cmd (`--network none`, with the same `~/.m2` files mounted as in `exchange_core_throughput-v2-paired-b`). The 4-CPU column merges two sets of runs: four of the shipped engine and one of the tip at `--memory 4g` (`evidence/runs/exchange_core_throughput-cpu4v8-a/result/out/summary.txt`, `-b`), and three of each at the leaderboard's `--memory 8g` (`evidence/runs/exchange_core_throughput-v2-cpu4m8g-rep{1,2,3}`). The 8-CPU column is from the first set only.

| Engine | 4 CPUs, raw (MT/s × 1000) | 4 CPUs, out of 100 | 8 CPUs, raw | 8 CPUs, out of 100 |
|---|---|---|---|---|
| shipped engine (7 runs at 4 CPUs, 4 at 8 CPUs) | 939, 965, 972, 983, 1,006, 1,033, 1,059 | 0 | 3,418, 3,617, 4,155, 4,638 | 46.63–75.58 |
| prompt's tip, 2ME+1RE (4 runs at 4 CPUs, 1 at 8 CPUs) | 1,644, 1,894, 1,994, 2,091 | 0–0.02 | 4,122 | 64.39 |

At 4 CPUs the shipped engine runs below the 0-point reference (2,090.63), so it scores 0. The prompt's own tip roughly doubles throughput at 4 CPUs (1,644–2,091 raw), but three of its four runs stay below the 0-point and the fourth is 0.4 above it, so it scores 0–0.02 out of 100; at 8 CPUs its single run (4,122) lies within the shipped engine's range (3,418–4,638). So the ranking of honest strategies depends on the CPU count, and at the leaderboard setting every engine below about 2.09 MT/s scores 0. The source of the 0-point reference (the hardware it was measured on) is unknown. It is kept unchanged, because no exactly computable replacement exists; setting a new one from these runs would be a separate decision. The fixed version does not change this. At the same setting (`--cpus 4 --memory 8g`, the leaderboard's `judge_cpu_limit` and `judge_mem_limit`), three runs of the fixed version passed the integration-test step (`GATE OK … tests=33`) every time and scored the shipped engine 811, 1,073 and 1,194 raw and the 2ME+1RE tip 1,684, 1,687 and 1,832, against 965–1,059 and 1,644–1,994 for the original grader on the same workers; all are 0 out of 100. The fixed version's scores are within throughput noise of the original's (shipped engine 811–1,194 against 939–1,059 over all seven original-grader runs) (`evidence/runs/exchange_core_throughput-v2-cpu4m8g-rep{1,2,3}`).

## How much it matters

A broken engine gets full throughput credit instead of 0. Across the four original-grader runs of each broken engine (the single run above and the three side-by-side runs), feeswap scored 7.77–24.40 and dropevents 4.71–15.62 out of 100 (raw 2,269–2,704 and 2,197–2,465); the unmodified engine scored 0–24.19 (raw 2,008–2,698) in the seven original-grader runs made alongside them (the correct test submission above and the original-grader side of the three side-by-side runs), so these scores are within throughput noise. Any solver whose optimization breaks fees or event delivery while keeping the global balance at zero gets full credit instead of 0.

## The fix

Before the unchanged timed test, the fixed grader runs the project's shipped integration tests `ITFeesExchangeBasic` and `ITExchangeCoreIntegrationRejectionBasic` (33 tests) in a separate Maven run. If any of them fails, the submission scores 0 (`WA`, wrong answer). The timed Maven run is unchanged.

The fixed version also changes how the timed run is scored. The original grader marks a run `WA` when Maven exits non-zero but still prints its throughput as the score (`CASE 0000 WA score=<MT/s × 1000>` and `TOTAL_SCORE <MT/s × 1000>`), and the harness ranks on `TOTAL_SCORE` regardless of the case status (`sforge/harness/grading.py` `extract_score`; `selection.py` `_score_first`). The fixed version sets the score to 0 whenever the status is not `OK` (`if status != "OK": score = 0` in `repair.patch`). The throughput is parsed from the `Average: … MT/s` line, which the test logs only after all rounds pass their checks (`ThroughputTestsModule.java:42-69`); the per-round lines carry a logger prefix and do not match the grader's start-of-line pattern. So this path is reached only when Maven exits non-zero after the average is logged, for example when the engine fails while shutting down. The rules say "`mvn test` must still pass functional assertions". A side-by-side arm reaches this path (`shutdownbusy`). All 50 rounds pass and the average is logged, and then the engine's shutdown throws, but only in the throughput configuration, so the integration tests still pass. The original grader prints `CASE 0000 WA score=2939` and the harness scores it as valid at 32.31 out of 100; the fixed version passes the integration tests, prints `WA score=0` and scores 0 (2939 and 2943 in the first job's two runs under the original grader; 0 in all six fixed-version runs over three jobs). If the shutdown also fails in the integration tests' configuration (`shutdownall`), the integration-test step rejects it first. No honest test submission has reached this path: the unmodified engine and `topo21` were `OK` in all 18 fixed-version timed runs.

The fixed version also pre-loads 30 missing public files from Maven Central (surefire, JUnit platform, opentest4j and apiguardian artifacts) into the image's `~/.m2`, so it grades with no network. For the original-grader runs below, the same files were mounted so that the original grader could run offline. The row "original image without the added files" shows the original image without them.

| Submission | Role | Original grader | Fixed grader |
| --- | --- | --- | --- |
| unmodified engine, original image without the added files | setup check | RE, 0 | — |
| unmodified engine (correct test submission, run 1) | valid | OK 2050 | integration tests OK (33 tests), OK 2153 |
| unmodified engine (correct test submission, run 2) | valid | OK 2210 | integration tests OK, OK 2978 |
| `topo21` honest variant | valid | OK 2524 | integration tests OK, OK 2481 |
| `feeswap` (fee swap, balance kept at zero) | **shows the problem** | **OK 2269** | **WA 0 (integration tests failed)** |
| `dropevents` (user events not forwarded) | **shows the problem** | **OK 2234** | **WA 0 (integration tests failed)** |
| `feeleak` | invalid | RE 0 | WA 0 |
| `compileerr` | invalid | RE 0 | WA 0 |
| `shutdownbusy` (all rounds pass, then shutdown fails in the throughput configuration; two runs) | **rule violation** | **WA, scored 2939 / 2943** (harness: valid, 32.31 / 32.44) | **integration tests OK, WA 0** |
| `shutdownall` (shutdown fails in every configuration) | rule violation | WA, scored 3382 (45.62) | WA 0 (integration tests failed) |

The raw result is MT/s × 1000. RE means a run error. The single-run results in the previous section and the original-grader results here come from separate runs; both are quoted as recorded. The other test submissions are:

- `topo21` is the prompt's own example optimization: 4ME+2RE changed to 2ME+1RE.
- `feeleak` charges the wrong fee without booking it consistently, which breaks the global-balance check.
- `compileerr` does not compile.

**Score compatibility:** correct engines score as under the original version, although throughput is noisy from machine to machine. Incorrect engines that the original version rewarded now score 0. A run whose timed Maven test fails after logging its average scores 0 instead of its throughput. Fixed-version scores are not comparable with original leaderboard entries.

## How we checked it

- **Original grader.** The checks ran on the original public image, pinned by digest. Each submission ran through the task's exact `eval_cmd` in a fresh container with `--network none`, `--cpus 8` and `--memory 6g`.
- **Independent check:** the project's own shipped integration tests (`ITFeesExchangeBasic`, 5 tests, and `ITExchangeCoreIntegrationRejectionBasic`, 28 tests). They ran in the same container with the grader's exact Maven flags.
- **Side-by-side run.** The original and fixed graders scored the same submissions, plus valid and invalid test submissions, both with `--network none`. This was repeated three times. No test submission changed verdict (see `data/paired-repeatability.md`). Throughput moves between runs, but the integration-test verdicts never change.

## Limits

- No AI model or solver was run. Effects are shown only on test submissions and counterexamples we wrote.
- Throughput varies by up to 38% between runs of one submission on the same machine type (`data/paired-repeatability.md`). Across the three side-by-side runs, under either grader, the unmodified engine ran at 2,008–3,105 raw (0–37.52 out of 100; 0–24.19 under the original grader alone); 2,008 and 2,050 are below the 0-point reference (2,090.63), so a correct engine can score 0. The single-run scores out of 100 above are not a comparison controlled for that variation.
- The second change (score 0 when the timed test's Maven run fails after printing an average) is tested only on a constructed shutdown failure (`shutdownbusy`, `evidence/runs/exchange_core_throughput-v2-paired-shutdownfail`), not on code from a real solver.
- The two integration test classes cover fees, rejections and events. They do not cover every property a correct engine must keep, so an engine with other kinds of wrong behaviour could still pass the fixed grader's test step.
- The fixed version does not compare per-user balances, positions or the event stream against a reference run. It uses the shipped integration tests instead.
- Only two incorrect-engine changes were tested.
- The integration tests run only in the project's non-default Maven profile `it`, not in the default `mvn test` the rules name, and the work image has no copy of them, so a solver cannot run them before submitting. The fixed version enforces the rule "Do NOT change behavior" through them.
- The CPU-count note rests on one machine type (E2B, 8 vCPU Xeon 2.6 GHz): 7 original-grader runs at 4 CPUs and 4 at 8 CPUs for the shipped engine, 4 at 4 CPUs and 1 at 8 CPUs for the 2ME+1RE tip. The 4-CPU runs used `--memory 4g` (4 shipped, 1 tip) or `--memory 8g` (3 of each). Throughput at 8 CPUs varied by up to 36% between runs and workers (3,418–4,638), and these 8-CPU runs (`--memory 4g`) were faster than the earlier paired runs (2,008–3,105, `--memory 6g`, other workers).

## Reproduce

- Original grader image: `sha256:6b1617315cd2…`.
- Original-grader runs with incorrect engines: `evidence/runs/exchange_core_throughput-wrongengine/run.sh`.
- Integration-test check: `evidence/runs/exchange_core_throughput-oracletests/run.sh`.
- Side-by-side run of the original and fixed graders: `repairs/exchange_core_throughput-v2/paired/run.sh`. The variant definitions are in `paired/mutate.py`.
- Second-change arm: `evidence/runs/exchange_core_throughput-v2-paired-shutdownfail/run.sh` (variants in `inputs/mutate.py`).
- Fixed version at the leaderboard setting (`--cpus 4 --memory 8g`): `evidence/runs/exchange_core_throughput-v2-cpu4m8g-rep{1,2,3}/run.sh`, results at the end of `paired/results.md`.
- Fix package: `repairs/exchange_core_throughput-v2/` (the folder holding the fixed version), which contains `Dockerfile`, `repair.patch`, `files/` and `source-lock.json`.
- Supporting records: `repairs/exchange_core_throughput-v2/paired/results.md` and `evidence/reviews/exchange_core_throughput-native.md`.
