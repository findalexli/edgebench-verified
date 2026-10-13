# CTA risk budget v2.1 candidate: overseas CNY notional divided by fund NAV

The policy requires overseas investment no greater than 40% of fund NAV, with overseas positions converted to CNY. The original grader mixed currencies and divided by gross notional. The historical v2 repair corrected currency conversion only. This v2.1 candidate retains that conversion and uses each holdings date's **total CNY NAV** as the denominator.

The original `_check_schema_compliance` explicitly requires total CNY NAV (approximately 1.5 billion), not unit NAV. `_compute_exposure_stats` already reads the submitted `date`/`nav` fields (including its existing aliases). The candidate uses those fields and exact same-date alignment, with the last row for duplicate dates as in the existing exposure helper. Missing, nonfinite, or nonpositive NAV on any holdings date earns no ratio credit. This does not replace the original accounting/replay/authenticity checks, and does not establish that every submitted NAV is truthful.

## Changes and version boundary

`repair.patch` changes only `/home/workspace/scoring/eval_script.py`. `task.json.in` changes the judge tag to `a9651058ecef-ebv-v2.1`; the original task and harness remain unchanged. The source lock records both the current candidate and the superseded FX-only output. Build with the existing `materialize.sh` and Dockerfile as usual; a fresh image build has not been run for v2.1.

The 40% threshold, day-count allowance, other risk gates and score mapping remain unchanged. The ratio denominator correction can increase or decrease credit. For example, CNY overseas exposure 1050 million, gross exposure 3150 million and NAV 1500 million passes the gross-share test (1/3) but violates the policy (70%). Overseas exposure 420 million, gross 570 million and NAV 1500 million fails the gross-share test but complies with the policy (28%). At most four raw cross-border points (five normalized points) can change; actual full-score movement remains unmeasured.

## Current candidate checks

`paired/check_nav_candidate.py ORIGINAL_EVAL_SCRIPT` verifies the original source hash, applies the actual historical/current patches in temporary directories, checks the candidate output hash, and calls the genuine `_evaluate_risk_constraints` method for all three versions. It requires the original evaluator's Python dependencies; no Docker or cloud calls occur.

Ten controls passed: leveraged violation, unleveraged compliant portfolio, compliant/bad controls, domestic only, exact 40% boundary, missing NAV, wrong-date NAV, zero NAV, and nonfinite NAV. The oracle uses exact rational CNY exposure/NAV. Results are in [paired/nav-candidate-results.json](paired/nav-candidate-results.json). Participation is stubbed; a single NAV day avoids the volatility gate. These are **source/helper component checks**, not a full task or native image run.

## Historical evidence and remaining gates

[paired/results.md](paired/results.md) and its cloud logs validate the **FX-only v2** repair, not this NAV candidate. The old fixture scripts intentionally omitted NAV, so their results must not be cited as v2.1 results. `paired/fx-only-v2.patch` preserves that earlier source change, and `paired/run.sh` is retained as a historical recipe requiring explicit opt-in. The complete historical reference scored identically because an earlier risk veto masked the changed block.

The candidate still needs a rebuilt image and full evaluator controls whose risk gates permit the changed block. The working image has not been inspected for a scorer copy. This patch does not resolve other task constraints, or strengthen the old formal FX-only theorem into a proof of the NAV implementation.
