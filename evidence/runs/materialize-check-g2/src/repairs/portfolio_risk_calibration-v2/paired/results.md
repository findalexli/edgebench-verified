# Paired results: portfolio_risk_calibration, original grader vs fixed version

**Verdict: accepted.**
- The test strategy that follows the instructions gains 0.07 points in the fixed version (32.45 → 32.52, full `score.py`), and its printed excess equals its own figure by the instructions' formula (3.47%).
- At the stated 12% full-marks line, the excess part goes from 19.85 to 20.00 (installed functions, T1).
- The wrong strategy, the starter and the image's own example score 0 in both versions. All three runs are identical.

Original grader: `seededge/edgebench.judge.portfolio_risk_calibration@sha256:42997fb5…e9458d`, with `eval_script.py` sha256 `829eeee1…a4f9b`.
Fixed version: built on each worker from this package (`./materialize.sh && docker build`), with `eval_script.py` sha256 `5494c343…6829a`. Both hashes, and lines 925–928 of each file, are recorded in `eval_sha-v1.txt` and `eval_sha-v2.txt` in each job.

Every full arm runs the task's own `eval_cmd` (`cd /home/workspace && python3 scoring/score.py`) in a fresh container with `--network none --memory 2g --cpus 2`, one container at a time. Jobs: `evidence/runs/portfolio_risk_calibration-v2-paired`, `-paired-rep2` and `-paired-rep3`. Each job has `status: exit=0` (`result/worker.json`) and "done" at the end of `result/out/summary.txt`. Script: `run.sh` (here and in each job directory).

## Arms

| Arm | What it is | Role |
| --- | --- | --- |
| (a) instructions' formula | `fixture_optimizer.py`, our momentum strategy with risk scaling, VaR, shorts and rebalancing records; `GROSS = 2.0`; reports its own excess with the instructions' formula | correct submission |
| (b) grader's formula | the same strategy and the same trades; reports its own excess with the original grader's formula | good-faith control |
| (c) wrong | the same code with the momentum signal reversed (`SIGN = -1`) | wrong submission |
| (d) starter | the work image's `/home/workspace` as shipped (`seededge/edgebench.work.portfolio_risk_calibration@sha256:f8e9371d…`): it has `requirements.txt` and no `portfolio_optimizer.py` | starter |
| (e) image example | the judge image's own `scoring/portfolio_optimizer.py` | reference from the image |

The arm settings are in `arms_resolved.txt` and the file hashes in `fixtures_sha.txt`. Arms (a)–(c) produce the same `backtest_results.json` under both graders and on all three workers (one distinct sha256 per arm across the six runs). So both graders scored identical inputs.

## Full grader (`score.py`)

| Arm | Original grader: final | Fixed version: final | Excess, original → fixed | Excess part (of 20) | Sortino ratio → part (of 10) | Information ratio → part (of 10) |
| --- | --- | --- | --- | --- | --- | --- |
| (a) instructions' formula | 32.45 | **32.52** | 3.44% → 3.47% | 5.73 → 5.78 | 0.7157 → 0.7214; 0.62 → 0.63 | 0.4385 → 0.4420; 0 → 0 |
| (b) grader's formula | 32.45 | **32.52** | 3.44% → 3.47% | 5.73 → 5.78 | as (a) | as (a) |
| (c) wrong | 0 | 0 | −21.14% → −21.33% | −10 → −10 (floor) | 0 → 0 | 0 → 0 |
| (d) starter | 0 | 0 | not computed: "missing submission files: portfolio_optimizer.py" | – | – | – |
| (e) image example | 0 | 0 | −9.28% → −9.37% | −9.28 → −9.37 | 0 → 0 | 0 → 0 |

Sources: final scores from `TOTAL_SCORE` in `summary.txt` and `summary_parsed.txt` (the harness's `structured_json` parser, `summarize.py`). All arms are `valid=True`. Component values come from `reports/<arm>-v1|v2/score_report.json` (`calculated_metrics`, `scores`).

- (a) gains 0.07 points: 0.05 from the excess part and 0.016 from the Sortino part. Its information ratio stays below the 0.5 pass line. Nothing else in the report changes (Sharpe 18.0, drawdown 13.23, the same penalties of 5 and 4).
- (a) reports its own excess as 0.034722 and (b) as 0.034448 (`backtest_results.json` → `metrics`). The original grader prints 3.44%, which is (b)'s figure. The fixed version prints 3.47%, which is (a)'s figure. The grader never reads the self-reported value, so (a) and (b) get the same score under each version.
- (c) and (d) still score 0. (e) scores 0 under both graders because anti-fraud checks zero its core score. Its excess, −9.28% vs −9.37%, matches the review's earlier run (`evidence/scripts/portfolio_risk_calibration/run_full.out`).

## Near the 12% full-marks line (installed functions)

`threshold_paths.py` runs inside each image and calls that image's own `calculate_metrics_from_data` and score functions on NAV paths we wrote. Each path grows at a constant daily rate over the real 243-date test calendar and is compared with the grader's own benchmark (period return 0.242755, k = 252/243). Source: `logs/threshold-v1.log` and `logs/threshold-v2.log`.

| Row | Strategy period return | Excess, original → fixed | Excess part | Information ratio part | Sortino part | Sum of the three, original → fixed |
| --- | --- | --- | --- | --- | --- | --- |
| T1 instructions' formula gives exactly 12% | 35.7351% | 11.91% → 12.00% | 19.85 → **20.00** | 2.5515 → 2.5905 | 4.0691 → 4.1114 | 26.4706 → **26.7019** |
| T2 original grader's formula gives exactly 12% | 35.8231% | 12.00% → 12.09% | 20.00 → 20.00 | 2.5905 → 2.6295 | 4.1114 → 4.1540 | 26.7019 → 26.7835 |
| T3 equal to the benchmark | 24.2755% | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| T4 | 30% | 5.94% → 5.99% | 9.90 → 9.98 | 0.021 → 0.041 | 1.3086 → 1.3303 | 11.2296 → 11.3546 |
| T5 | 20% | −4.43% → −4.47% | −4.43 → −4.47 | 0 → 0 | 0 → 0 | −4.43 → −4.47 |

T1 is a solver that reaches the instructions' full-marks line by the instructions' own formula. The original grader scores it 0.23 points lower on these three parts. The fixed version gives it full excess marks.

**Independent check.** `oracle.py` recomputes both formulas in 60-digit decimal arithmetic from the benchmark return and date count in the logs (`oracle.out`). For T1 it gives 0.1200000000 by the instructions' formula and 0.1190841879 by the original grader's. The installed values (rounded to 4 decimals by the grader) are 0.1191 in the original grader and 0.12 in the fixed version, and the excess part from the oracle (19.85 / 20.00) matches every row in both logs.

## Repeatability

All three workers (`-paired`, `-paired-rep2`, `-paired-rep3`; 8 vCPUs, 7.9 GB, Docker 29.4.1, every grader container at `--cpus 2`) gave the same results:
- `summary_parsed.txt` is identical in all three jobs;
- the threshold logs are identical apart from the module path line;
- each arm's `backtest_results.json` has one sha256 across all six runs.

## Limits

- No AI model or solver was run. (a)–(c) are a test strategy we wrote. Its exposure setting was chosen by us after looking at the test period, so it is a test input, not a solver result.
- Our test strategy reaches 3.5% excess, not the 12% cap where the gap is largest. The cap is checked on authored NAV paths through the installed functions (T1, T2), not through the full grader.
- The size bound of about 0.4 points (`bound.out`) is a decimal sweep over strategy returns from −30% to +100%, for this test period's benchmark and date counts of 242 and 243. It is not a proof.
- The first attempt of each job stopped before grading because GNU `patch` was missing on the worker (`attempt1-no-patch/` in each job; ledger entries at 09:21–09:22 UTC). `run.sh` now installs `patch` on the worker. No task image was changed.
