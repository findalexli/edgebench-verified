# exchange_core_throughput: native addendum (wrong engines through the original correctness check)

> **Note (2026-10-12).** The 2.704 vs 2.254 MT/s difference below is within run-to-run throughput noise: across the three side-by-side runs the unmodified engine ran at 2.008–3.105 MT/s (`repairs/exchange_core_throughput-v2/paired/results.md`).

> **Note (2026-10-12, later).** All runs below used `--cpus 8`. At the publisher's leaderboard setting of 4 grader CPUs the shipped engine scores 939–1,059 raw over seven runs, below the 0-point reference 2,090.6, so 0 out of 100 (`evidence/runs/exchange_core_throughput-cpu4v8-a`, `-b`, `exchange_core_throughput-v2-cpu4m8g-rep{1,2,3}`). See `cases/exchange_core_throughput.md`.

**Question.** Suppose an engine has honest-looking but **wrong** behaviour. Does the
original eval still pass its functional assertions and award throughput credit?

**Verdict.** CONFIRMED. Two one-edit mutations of the shipped engine were tested. Each
one is shown to be wrong by the project's own shipped integration tests. Both still pass
`PerfThroughput#testThroughputPeak` across all 50 asserted rounds, exit Maven with 0, get
`CASE 0000 OK` and `CASES_OK 1`, and receive full throughput credit:

- wrong per-user fee accounting that conserves the global balance
- trade, reject and command events silently dropped before reaching the user results consumer

The correctness check really is partial. It checks only that the global balance is zero
and that the L2 order books are equal (`ThroughputTestsModule.java:52-58`,
`// TODO compare events, balances, positions`). So an incorrect engine is accepted
through the real test path, not only through mocked output.

## Pinned artifacts

- Judge image: `seededge/edgebench.judge.exchange_core_throughput@sha256:6b1617315cd2bdc7248ed057b449042c215b90c7571e302378d3c8b3202bbb8d`. The worker pulled it by digest and its image ID was verified.
- Task JSON: `tasks/exchange_core_throughput.json` sha256 `fc64c74d1aadd48547407dd4ed66d7473dc8d49e05b66fe460d2513361c18e2f`.
  - eval_cmd: `cd /home/workspace/exchange-core && python3 /tmp/eval_exchange_core.py`.
  - Parser: score_sum. Rescale: log_max, baseline 2090.634594076933, expert 6000.
- File hashes in the image:

  | file | sha256 |
  |---|---|
  | `/tmp/eval_exchange_core.py` | `65bfba1129ef022ab3c3712769c335d8d1c42638a18a0e814a660e7647d8140a` |
  | `RiskEngine.java` | `8e7f955e…3c3a` |
  | `ExchangeCore.java` | `f38670ff…37ef` |
  | `ThroughputTestsModule.java` | `dd5a5873…be29` |
  | `PerfThroughput.java` | `e0e45d82…ccc1` |
  | `ITFeesExchange.java` | `8f6de92d…9271` |

## Mutations (each is one minimal, plausible edit)

The mutations are applied by `e2b/jobs/exchange_core_throughput-*/inputs/mutate.py`, which
does exact string replacement and asserts that each replacement happened.

1. **feeswap**, a copy-paste fee bug in `RiskEngine.handleMatcherEventsExchangeSell`.
   - The selling taker is charged `makerFee` instead of `takerFee`.
   - The exchange fee ledger books `makerFee` for the taker side, consistently.
   - Global balance is therefore conserved exactly. Sellers are over-credited and the
     exchange's fee income is under-booked by `(takerFee − makerFee) × size` on every sell-taker trade.
   - The test symbols have random fees with `takerFee ≥ makerFee`.
2. **dropevents**, a "remove the slow results stage" optimisation in `ExchangeCore`.
   - `resultsHandler.onEvent(cmd, seq, eob);` is removed. `api.processResult` is kept, so the synchronous API futures still complete.
   - The user's results consumer then receives no command results and no trade, reduce or reject events.

## Commands

- Jobs:
  - `e2b/jobs/exchange_core_throughput-wrongengine/run.sh` (scored runs)
  - `e2b/jobs/exchange_core_throughput-oracletests/run.sh` (independent oracle)
- E2B workers (8 vCPU), all recorded in `e2b/ledger.jsonl`:

  | worker | job | outcome |
  |---|---|---|
  | `i3bufglzlufrb12w1dbfm` | scored runs | exit 0, 302 s, killed |
  | `i91leq4cpd8kgnhlz1qdo` | oracle tests | exit 0, 81 s, killed |
  | `i473m1szge164upquo69g` | attempt 1, scored runs | see below |

- **Attempt 1 environment finding.** Worker `i473m1szge164upquo69g` ran the pinned image
  strictly offline (`--network none`, matching task `internet: false`).
  - It failed for **every** variant, including the unmodified engine.
  - The image's `~/.m2` lacks `org.apache.maven.surefire:surefire-junit-platform:3.0.0-M3`,
    so the forked JVM raises `ClassNotFoundException: org.apache.maven.surefire.junitplatform.JUnitPlatformProvider`.
  - The eval prints `CASE 0000 RE score=0 / TOTAL_SCORE 0`.
  - Output is saved in `exchange_core_throughput-wrongengine/result-attempt1-offline-provider-missing/`.
  - The earlier audit also found this gap: `exchange-installed-provider-inventory-sol-v2`
    records `fixed_artifact_root_not_present`. **If production judges run without network,
    the original task scores 0 for every submission.** Whether they do is not known from the task files.
- **Provider overlay used for attempt 2.**
  1. Copy the image's `~/.m2` to the host.
  2. Let surefire fetch only what it is missing, by running one tiny shipped unit test (`SimpleEventsProcessorTest`) with network.
  3. The added jars, with sha256 values recorded in `result/out/overlay/added.sha256`:
     - `surefire-junit-platform-3.0.0-M3.jar` `5c1151d3…cb96`
     - `common-java5-3.0.0-M3.jar` `dd7f2319…9acf`
     - `surefire-providers` pom
  4. Then run every scored and oracle run with `--network none` and the overlay mounted at `/root/.m2`.
- Each scored run used a fresh container:
  `docker run --rm --network none --cpus 8 --memory 6g -v m2:/root/.m2 <image@digest> bash -c 'python3 /in/mutate.py <variant> && cd /home/workspace/exchange-core && python3 /tmp/eval_exchange_core.py'`.
  The eval is verbatim.
- Oracle runs used the same container. They ran `mvn -B test -Dtest=<shipped IT class>` with the evaluator's exact Maven flags (`inputs/it_test.sh`).

## Results: scored path (original eval, attempt 2)

| variant | Maven / surefire | eval output | TOTAL_SCORE | normalized (log_max) |
|---|---|---|---|---|
| control (shipped engine) | `Tests run: 1, Failures: 0` (87 s) | `CASE 0000 OK score=2254 # Average=2.254 MT/s`, `CASES_OK 1` | 2254 | **7.14** |
| feeswap (wrong balances) | `Tests run: 1, Failures: 0` (76 s) | `CASE 0000 OK score=2704 # Average=2.704 MT/s`, `CASES_OK 1` | 2704 | **24.40** |
| dropevents (dropped events) | `Tests run: 1, Failures: 0` (76 s) | `CASE 0000 OK score=2465 # Average=2.465 MT/s`, `CASES_OK 1` | 2465 | **15.62** |

Normalized scores use `sforge/harness/score_rescale.py:116-120`:
`100·ln(raw/2090.63)/ln(6000/2090.63)`, clipped to 0–100.

## Results: independent oracle (the project's own shipped integration tests)

| test class | control | mutant | what fails |
|---|---|---|---|
| `ITFeesExchangeBasic` (5 tests) | 5/5 pass, Maven rc 0 | **feeswap: 2/5 fail**, rc 1 | `shouldProcessFees_BidGtcMaker_AskIocTakerPartial`: expected `<199061711100L>`, was `<199063788300L>`. Also `shouldProcessFees_BidGtcMakerPartial_AskIocTaker` |
| `ITExchangeCoreIntegrationRejectionBasic` (28 tests) | 28/28 pass, rc 0 | **dropevents: 28/28 fail**, rc 1 | Mockito `Wanted but not invoked: handler.commandResult(...)`, "there were zero interactions with this mock" |

So both mutants are genuinely incorrect engines. The scored throughput test accepts both
as functionally correct and rewards them.

## Further observation: repeatability

- feeswap does identical work to the control: the same operations, with a different
  constant in two places. It nevertheless measured 2.704 vs 2.254 MT/s, a 20% difference.
- On the log_max scale that is 24.4 vs 7.1 normalized points.
- This is one sample per variant, so it is not a variance estimate. It does suggest that
  single-run scores on this benchmark differ by more than many genuine optimisations would.
  The ranking among the three variants above is noise, not a speed effect of the bugs.

## Disposition assessment

- This confirms and replaces the earlier wording "actual incorrect-engine reward is
  unproved". An incorrect engine is now proved to be rewarded through the real JVM path,
  with no marker injection, and with Maven passing.
- The recommended disposition stays **repair-v2 (withhold original)**.
- The repair should add a judge-side comparison of per-user balances, positions and the
  event stream against a reference run on the same seed. It should also keep the
  rc/marker fixes already listed in the triage.
- The image should ship the surefire JUnit-platform provider, or the task should declare network access for the judge.

## Recommended publishable wording

"The throughput test's correctness check compares only the global balance and the order
books. Engines with wrong per-user fee accounting, or with all result events dropped,
pass it and receive full throughput credit, even though the project's own integration
tests reject them. Separately, the pinned judge image cannot run the test offline,
because a surefire provider is missing."

## Limits

- One run per variant. Speed values are not a variance-controlled comparison.
- The provider overlay adds three public Maven Central artifacts that the image lacks. It
  changes no task file, test or flag.
- The stated rule "mvn test must still pass functional assertions" is met by both mutants
  as the harness defines it. The mutants violate the engine's documented behaviour, as
  shown by the shipped tests, not the evaluated assertions.
