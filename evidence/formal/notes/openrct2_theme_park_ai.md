# openrct2_theme_park_ai (time-budget arithmetic)

## Claim

- The first-principles model gives 1225/2048 ≈ 0.598 game days/s at speed 4 (0.075 at speed 1
  and 0.299 at speed 3), so 992 target days need 2031616/1225 ≈ 1,658 s.
- At the observed 0.595 days/s they need ≈ 1,667 s (27.8 min); at the observed 0.593–0.597
  they need 1,661–1,673 s.
- Three scenarios in sequence need ≈ 83 min.
- 120 s covers at most 72 days; 68–69 days are ≈ 7% of 992, and 992 days ≈ 4.05 years.
- Four years in 120 s would need ≈ 4,423 ticks/s, which is ≈ 110× the 40 Hz base and ≈ 14×
  speed 4. The observed rate corresponds to ≈ 318 ticks/s.

## Model and link to the code

`Ebv/TimeBudgets.lean` (output `TimeBudgets.out`), OpenRCT2 section. The constants come from
`repairs/openrct2_theme_park_ai-v2/paired/check_horizon.py`, which takes them from
`openrct2.d.ts`: 16,384 ticks per month, 8 months of 245 days in all, a 40 Hz base rate and
2^(k−1) updates per frame at speed k. The budgets are `OPENRCT2_TIMEOUT=120`,
`TOTAL_TIMEOUT=1800` and `eval_timeout` 2400; the monitor's `targetDays` is 992. The observed
rates are from the case-page table.

## Result

**Proved** as arithmetic on the documented inputs. Every number in the case page and the
review reproduces.

**Discrepancy in wording.** The case page says the ≈1,667 s *per scenario* is "far beyond the
120 s scenario budget, the 1,800 s wrapper cap and the 2,400 s manifest timeout".
`counter_single_scenario_fits` shows that one scenario, even at 0.593 days/s (1,673 s), fits
under 1,800 s and under 2,400 s. Only the three-scenario total (≈ 4,975–5,019 s) exceeds them,
as the review correctly says ("about 83 min for all three").

Minor point: at the 0.25-CPU rate of 0.582 days/s, 992 days need 1,704.5 s, slightly above the
review's suggested per-scenario minimum of 1,700 s.

## Counter-check

`counter_single_scenario_fits` (above) and `counter_1660`: 992/0.595 ≤ 1,660 is false.

## Limits

- The proofs are arithmetic only. That the engine keeps real time and that the rates hold on
  other hosts come from measurement, not proof.
- The rates are taken as published, rounded to three decimals.
