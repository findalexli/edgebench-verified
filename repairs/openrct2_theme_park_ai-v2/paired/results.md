# Paired check: openrct2_theme_park_ai v2 (prompt-only)

## What a paired run would test, and why it was not repeated

v2 changes only `work.agent_query`. The judge image, work image, `eval_cmd`, timeouts,
parser and rescale are byte-identical to v1 (see `../source-lock.json`). Any fixed
`my_plugin.js` therefore gets the same score under v1 and v2 by construction. The
original monitor runs were not repeated. The check below asks a different question:
**does the new prompt text match the measured horizon and the real speed rule?**

| Spec item | Status |
|---|---|
| Trigger: v1 states a false horizon, v2 states the measured one | Checked: table below |
| Valid control: score unchanged v1 to v2 | Holds by construction. Evaluator bytes are unchanged. No new scoring run |
| Invalid control: rejected in both | Holds by construction. Not re-run |
| E2B paired job | Not run. Not needed because nothing executable changed |

## Measured horizon and recomputation

`check_horizon.py` reads the saved driver logs and recomputes game days per wall-second. It
compares them with a first-principles model:

- One month is 65536/4 = **16,384 ticks**. Source: `openrct2.d.ts` in the work image says
  `monthProgress` runs from 0 to 65536 and is "incremented by 4 each tick, so every month
  takes ~6.8 minutes".
- A year is 8 months, March to October, with 245 days. That gives a mean of **535 ticks per day**.
- The base rate is 40 ticks/s, since 16384/40 s = 6.83 min, which matches the d.ts comment.
  Speed `s` multiplies it by 2^(s-1), so speed 4 runs at **320 ticks/s**.
- The model gives **0.598 days/s** at speed 4. 120 s is therefore at most 71.8 days, minus
  engine start-up. Reaching the monitor's `targetDays = 992` would take **1,658 s** per scenario.

Output (`check_horizon.out`, rerun with
`python3 -I check_horizon.py ../../../evidence/scripts/openrct2_theme_park_ai/run_*.log logs/run_*.log`):

```
model speed 1: 0.075 game days / wall-s; 120 s -> 9.0 days
model speed 3: 0.299 game days / wall-s; 120 s -> 35.9 days
model speed 4: 0.598 game days / wall-s; 120 s -> 71.8 days
model: 992 target days at speed 4 need 1658 s

log                          scenario             budget spd t_first t_last  days(samples) d/s   model
run_120s_cpus2.log           scenario_large.park    120   4    4.6  117.8   68(41)   0.595  0.598  DONE=False
run_120s_cpus2.log           scenario_medium.park   120   4    4.5  117.3   69(42)   0.595  0.598  DONE=False
run_120s_cpus2.log           scenario_small.park    120   4    4.7  117.6   68(41)   0.593  0.598  DONE=False
run_60s_speed4_cpus2.log     scenario_small.park     60   4    4.6   59.8   33(20)   0.597  0.598  DONE=False
run_60s_speed4_cpus0.25.log  scenario_small.park     60   4   11.5   57.9   27(17)   0.582  0.598  DONE=False
run_60s_speed1_cpus2.log     scenario_small.park     60   1   27.2   53.0    2(2)    0.077  0.075  DONE=False
run_60s_speed3.log (new)     scenario_small.park     60   3    7.5   59.1   15(10)   0.291  0.299  DONE=False
run_60s_speed8.log (new)     scenario_small.park     60   8    5.0   59.9   33(20)   0.602  0.598  DONE=False
```

These are the source log lines for the 120 s run (`scripts/openrct2_theme_park_ai/run_120s_cpus2.log`):

- large: `"done_seen": false, "first_date": [41, 0, 19], "last_date": [41, 2, 26], "game_days_elapsed": 68, ... "game_days_per_wall_s": 0.595`
- medium: `"first_date": [8, 4, 25], "last_date": [8, 7, 2]`, 69 days, 0.595 days/s
- small: `"first_date": [61, 1, 27], "last_date": [61, 4, 4]`, 68 days, 0.593 days/s
- Diagnostics line: `judge diagnostics: start companyValue 123,280, final companyValue 114,810, ... samples 41`

**Agreement.** The measured rate at speed 4 is 0.593 to 0.597 days/s, against 0.598 from the
model, within 1%. The first sample arrives at tick 1024, about 3.2 s of game time at speed 4,
so the game starts roughly 2 game days before it. From scenario start to the scored last
sample is therefore about 68 + 2 = **about 70 game days**. That is the figure in the v2 prompt
("about 70 game days, a little over 2 game months"). The 120 s budget covers about 7% of the
992-day monitor target and about 29% of one 245-day game year. The v1 statement of "~4 game
years" is false by a factor of about 14.

**Speed rule, checked in the original judge image.**

- The monitor `00_sebench_monitor.js` calls `gamesetspeed {speed: 4}` in its `main`. Source:
  `/tmp/openrct2_original_eval.py`, `write_monitor`.
- The log shows it starts before the submitted `zz_submitted_plugin.js`:
  `[SEBenchJudgeMonitor] Started` and then `[AuditControl] Started`.
- `gamesetspeed` is on `ALLOWED_ACTIONS`. `validate_plugin` places no restriction on its argument.
- Speed 1 gives 0.077 days/s and speed 3 gives 0.291 days/s, so the submission's later call
  takes effect.
- Speed 8 is rejected: `GameSetSpeedAction.cpp:47 (Query)]: Invalid speed 8`. The game
  stays at the monitor's speed 4 (0.602 days/s).
- CPU throttling to 0.25 changed the rate by about 2%. The game is limited by real time,
  not by CPU, in these runs.

The new runs (`logs/`) used the unchanged driver and original image, with
`docker run --rm --network none --memory 2g --cpus 2`, one 60 s small-scenario run each.

## Verdict

The v2 prompt text matches the measured horizon and the measured speed rule. The scores are
identical by construction. The repair is accepted as a prompt correction. The limits are in
`../README.md`.
