# wireless_electricity_layout: formal note

## Claim
Under the task's `score_first`/`minimize` selection and `piecewise_log_min` rescale, inserting the
compile-failure entry (raw total 1e17) at any position of a non-empty submission history changes
neither the score out of 100 of the selected entry nor the maximum score out of 100 over entries.
It can change the raw `best_score` and the round named best.

## Model and link to the code
Lean 4: `evidence/formal/lean/ebv/Ebv/WirelessCeInvariance.lean` (output `WirelessCeInvariance.out`).
- `rescale` = `sforge/harness/score_rescale.py` lines 60-63 and 173-194 (sha256 98feb630…4b19, the
  same file upstream and in the earlier audit's patched harness, now removed), with `math.log` replaced by an arbitrary function `lg`.
- `step`/`selectScore` = upstream `sforge/harness/selection.py` lines 45-48 and 83-103 (sha256
  abb55b7b…cf0a; this matches EdgeBench's file at `6e4e5f4`, rechecked 2026-10-12 and recorded in `sforge/UPSTREAM.lock`).
- `bestMax` = upstream `sforge/visualizer/scanner.py` lines 467-468 (sha256 f124d340…a866).
- Anchors are the exact rational values of the doubles in `tasks/wireless_electricity_layout.json`
  (sha256 050ab35f…0809). The CE total is 1e17, from `eval_wirel.sh` (c670ff6d…).
- Differential check: the model selects `ce` for [baseline, ce], [ce, baseline] and
  [baseline, re_some, ce], and gives 0 for all three saved raw totals in `observed/`. This matches
  `grade_and_select.py` as recorded in the review.

## Result
**Proved.** `selected_norm_invariant` and `bestMax_invariant` hold for any entry with raw ≥ baseline
and any `lg`. `task_ce_invariant` instantiates them for the CE entry. The proof uses only two facts
from the source: the scan returns a minimum element, and the rescale is 0 at or above the baseline
(lines 175-178). `bestMax_attained` shows the fold equals Python's `max` because every rescaled
value is ≥ 0.

## Counter-check
- `counter_raw_changes`: the raw `best_score` of [baseline] differs from that of [baseline, ce].
- `counter_low_penalty`: with a hypothetical CE penalty of 1e15 (below the baseline anchor), the
  selected score would rise from 0 to at least 20, for every `lg`. So the hypothesis is necessary.

## Limits
- Raw scores are modelled as rationals. This is exact for these magnitudes, but there is no
  NaN/inf modelling, and score-less entries are dropped before the scan.
- Empty history: without CE nothing is selected (`none`); with CE alone the score is 0
  (`task_ce_only`). This is not covered by the invariance theorem.
- Whether the downstream leaderboard reads one of these two consumers is taken from the source;
  it was not run.
