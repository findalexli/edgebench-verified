# CTA risk budget v2.1: overseas CNY notional divided by fund NAV

The policy requires overseas investment no greater than 40% of fund NAV, with overseas positions converted to CNY. The original grader mixed currencies and divided by gross notional. The historical v2 repair corrected currency conversion only. v2.1 retains that conversion and uses each holdings date's **total CNY NAV** as the denominator.

The original `_check_schema_compliance` explicitly requires total CNY NAV (approximately 1.5 billion), not unit NAV. `_compute_exposure_stats` already reads the submitted `date`/`nav` fields (including its existing aliases). v2.1 uses those fields and exact same-date alignment, with the last row for duplicate dates as in the existing exposure helper. This does not replace the original accounting/replay/authenticity checks, and does not establish that every submitted NAV is truthful.

## Holdings dates without a same-date NAV

A holdings date whose same-date NAV is missing, nonfinite or nonpositive counts as **one violation day**, exactly like a day over the 40% limit, under the original day allowance (no violation day: 2 ratio checks; violation days below 2% of holdings dates: 1; otherwise 0). No denominator is invented or forward-filled, so such a day can never be shown compliant, but it costs no more than any other violation day.

The first v2.1 candidate (`9f5149da…`, kept as `paired/superseded-v2.1-strict-nav.patch`) instead removed all ratio credit when any single holdings date lacked a valid NAV. That is stricter than the original grader, which tolerates violation days on under 2% of days, and than `_compute_exposure_stats`, which looks NAV up with `asof`. The shipped standard answer has 1565 NAV dates and 1565 holdings dates, all aligned. But an honest engine can easily write one holdings date that its NAV file lacks (for example a final mark written after the last NAV row). The native control `unleveraged-navgap` does exactly that, 1 of 1564 holdings dates: the strict candidate scored it like a breaching portfolio (`cross_border` 1, TOTAL_SCORE 66.25), while v2.1 gives the one tolerated day 3 (TOTAL_SCORE 68.75; 5 and 71.25 with the date present). The strict candidate was therefore replaced before release.

## Changes and version boundary

`repair.patch` changes only `/home/workspace/scoring/eval_script.py` (original `252f864a…` → `5090b56a…`). `task.json.in` changes the judge tag to `a9651058ecef-ebv-v2.1`; the original task and harness remain unchanged. The source lock records the current output, the superseded strict candidate and the superseded FX-only output. Build with `./materialize.sh && docker build -t ebv/cta_risk_budget_optimization:v2.1 .`.

The 40% threshold, day-count allowance, other risk gates and score mapping remain unchanged. The ratio denominator correction can increase or decrease credit. For example, CNY overseas exposure 1050 million, gross exposure 3150 million and NAV 1500 million passes the gross-share test (1/3) but violates the policy (70%). Overseas exposure 420 million, gross 570 million and NAV 1500 million fails the gross-share test but complies with the policy (28%). At most four raw cross-border points out of 80 (five points out of 100) can change.

## Native paired run (full original `eval_cmd`)

Three E2B jobs, `evidence/runs/cta_risk_budget_optimization-v2.1-native-rep{1,2,3}`, each ledger `status: exit=0`. In each worker the v2.1 image was built from this package (`materialize.sh` pulled the pinned image, extracted and patched `eval_script.py` and verified `5090b56a…`; then `docker build`). Every arm ran the task's original `eval_cmd` (`cd /home/workspace && python3 scoring/score.py`) at `--network none --memory 3g --cpus 2`. Full submissions are `paired/full_submission/main.py` with `config-<arm>.json`: a synthetic but internally consistent constant-weight portfolio whose NAV, positions, trades, costs and FX follow the grader's own replay (authenticity check 10/10), with annual volatility in [5%, 20%], maximum drawdown under 20% and participation passing, so the risk gate reaches the cross-border block. Results: [paired/results.md](paired/results.md).

| Submission | Original | v2.1 |
|---|---|---|
| shipped standard answer | 20 (risk vetoed: annual vol 1.3%) | 20, same veto |
| `leveraged`: overseas 45% of NAV, 37.5% of CNY gross | 58.75, `cross_border` 5 | **53.75**, `cross_border` 1 |
| `unleveraged`: overseas 28% of NAV, 87.5% of CNY gross | 66.25, `cross_border` 1 | **71.25**, `cross_border` 5 |
| `unleveraged-navgap`: as above, last NAV row missing | 66.25, `cross_border` 1 | 68.75, `cross_border` 3 |

The same scores came out in all three jobs. The weights' signs were chosen with hindsight so the NAV passes the drawdown and volatility gates; the portfolios are scorer controls, not strategies.

## Component checks

`paired/check_nav_candidate.py ORIGINAL_EVAL_SCRIPT` verifies the original source hash, applies the historical, superseded and current patches in temporary directories, checks the current output hash, and calls the genuine `_evaluate_risk_constraints` method for all four versions. Ten single-day controls (leveraged violation, unleveraged compliant, compliant/bad, domestic only, exact 40% boundary, missing NAV, wrong-date NAV, zero NAV, nonfinite NAV) and three 100-day NAV-date controls (0, 1 or 2 holdings dates without NAV) pass against an exact rational oracle. Results: [paired/nav-candidate-results.json](paired/nav-candidate-results.json). Participation is stubbed there.

## Historical evidence and remaining limits

The second half of [paired/results.md](paired/results.md) and its cloud logs validate the **FX-only v2** repair, not v2.1. `paired/fx-only-v2.patch` preserves that earlier source change, and `paired/run.sh` is retained as a historical recipe requiring explicit opt-in.

The full submissions are authored controls; no AI model or solver output was graded. The working image has not been inspected for a scorer copy. The old formal FX-only theorem is not a proof of the NAV implementation.
