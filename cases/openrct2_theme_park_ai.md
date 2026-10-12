# OpenRCT2 Theme Park AI (`openrct2_theme_park_ai`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Interactive Games & Simulators
- **Decision:** Repair v2 (prompt correction)[^1]. The prompt promises about 4 game years per scenario, but the 120 s budget covers about 68 game days, so the score is a snapshot taken early in the game.

## What the task promises

The solver writes an OpenRCT2 plugin that "maximizes **normalized company value** across 3 scenarios". The v1 Rules section says: "The engine runs each scenario for ~4 game years at speed 4 (host --headless)". It also says scoring "reads the real in-game `park.companyValue`". The Key APIs section describes `gamesetspeed {speed: 4}` as "max speed (host mode cap is 4)", but the prompt does not require the solver to use speed 4.

## What we checked and how

- **Source reading.** We read the evaluator path: the wrapper (`OPENRCT2_TIMEOUT=120`, whole run capped at 1,800 s; the manifest's `eval_timeout` is 2,400 s), the judge monitor (`targetDays = 992`, emits `DONE` only at that date) and the scorer. The scorer uses the last monitor sample. Nothing in it records or checks whether `DONE` was reached.
- **Native runs in the pinned judge image.** We ran the original helper's own `validate_plugin`, `run_scenario` and `score_scenario` functions, with only a tee added on engine stdout. The plugin was a simple control. Runs used `--network none --memory 2g --cpus 2`, plus one run at `--cpus 0.25`. We ran 120 s on all three scenarios and 60 s at speeds 1, 3, 4 and 8.
- **Independent rate model.** We built a first-principles rate model from the tick and month constants documented in `openrct2.d.ts` and compared its predictions with the measured logs.
- **Original identity.**
  - Judge image `seededge/edgebench.judge.openrct2_theme_park_ai@sha256:a5263578…`.
  - `/tmp/eval_openrct2.py` sha256 `7fdde3e0…`.
  - `/tmp/openrct2_original_eval.py` sha256 `bfcf7ab9…`.
  - Task JSON sha256 `09e2a4d8…`.

## What we found

**Confirmed (stronger than the earlier claim).** The earlier claim was that the promised horizon was "unverified". With the shipped budgets it is in fact infeasible.

- **Measured coverage.** At speed 4 the engine advances 0.593 to 0.597 game days per wall-second. The rate is limited by real time, not by host CPU: cutting to 0.25 CPU changed it by about 2%. Each 120 s scenario covered 68 to 69 game days, about 7% of the 992-day target, and `DONE` was never seen.
- **Time needed for the promised horizon.** Reaching 992 days would take about 1,667 s per scenario. That is far beyond the 120 s scenario budget, the 1,800 s wrapper cap and the 2,400 s manifest timeout.
- **Example under the original evaluator** (120 s, speed 4, medium scenario):
  - The game ran from date 8,4,25 to 8,7,2, which is 69 game days.
  - Company value went from 198,010 to 133,260.
  - The normalized score was 0.915.
  - The three-scenario average was 1.038, printed as `TOTAL_SCORE 10384`.
- **Speed is under the solver's control.** `gamesetspeed` is allowlisted. The submission's later call overrides the monitor's speed 4: speed 1 ran at 0.077 days/s and speed 3 at 0.291 days/s. Speed 8 is rejected. A slower game can hold company value near its starting value. In our runs the 1.10 cap masked this.
- **Maximum score effect:** not measured. The defect changes *what* is measured: value after about 2 months instead of about 4 years. We did not show that it raises or lowers any particular solver's score.
- **Earlier repair.** An earlier audit proposed a completion gate. Re-checking showed that under the shipped 120 s budget the gate would score every submission 0, because `DONE` is unreachable.

## Repair

v2 replaces one Rules bullet in `work.agent_query` with two. The new text says:

- Each scenario runs for "**120 wall-clock seconds**, not to a fixed game date". At speed 4 that covers "only about **70 game days**".
- The score uses the monitor's last sample before the cutoff.
- The plugin may call `gamesetspeed` with speed 1-4, the most recent call takes effect, and a lower speed simulates proportionally fewer days.

The images, `eval_cmd`, timeouts, parser and rescale anchors (linear, 0 to 40000) are unchanged. No other solver-visible file states a horizon.

Paired check (prompt-only; copied from `paired/results.md`):

| Spec item | Status |
|---|---|
| Trigger: v1 states a false horizon, v2 states the measured one | Checked: table below |
| Valid control: score unchanged v1 to v2 | Holds by construction. Evaluator bytes are unchanged. No new scoring run |
| Invalid control: rejected in both | Holds by construction. Not re-run |
| E2B paired job | Not run. Not needed because nothing executable changed |

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

**Score compatibility.**

- **Same harness, same scores.** A given `my_plugin.js` gets the same score under v1 and v2, up to the usual run-to-run variation of a real-time game. v1 runs already had the same real 120 s horizon.
- **Not comparable as measures of solver ability** where a solver's strategy depended on the prompt. A v1 solver may have planned for 4 years. A v2 solver can front-load its strategy or deliberately lower the speed.

## Limits and what was not run

- **No re-runs of a real solver.** No model or solver was re-run. The effects shown here are on authored controls only, and no leaderboard impact is estimated.
- **The speed incentive remains.** v2 states the speed rule honestly but does not stop a plugin from lowering the speed. Removing the incentive needs an evaluator change: re-assert speed 4 every tick, or score at a fixed game date with a long enough budget.
- **About 70 days assumes the engine keeps real time.** Hosts are not pinned. A slower host, an overloaded host or a heavy plugin could fall further behind.
- **Small run set.** Each configuration ran once, with one simple control plugin whose staff hiring failed. No competitive plugin was run.
- **Not run through the wrapper.** The full three-scenario sequence ran through the helper's functions, not through `eval_openrct2.py`. The rescale anchor of 40000 was not examined.
- **No paired scoring run.** None was made, because nothing executable changed.

## Reproduce

- Native driver and control plugins: `evidence/scripts/openrct2_theme_park_ai/driver.py`, `plugin.js` and `plugin_speed1.js`. Saved logs are `run_*.log` in the same folder.
- Horizon check, run from `repairs/openrct2_theme_park_ai-v2/paired/`: `python3 -I check_horizon.py ../../../evidence/scripts/openrct2_theme_park_ai/run_*.log logs/run_*.log`
- Prompt diff: `repairs/openrct2_theme_park_ai-v2/repair.patch`, which goes from `orig/agent_query.md` to `files/agent_query.md`.

Supporting records: `repairs/openrct2_theme_park_ai-v2/` (README, `source-lock.json`, `paired/results.md`).

[^1]: The repair's `source-lock.json` records its status as "accepted-candidate (not yet adopted into tasks/)": the v2 prompt is accepted but not yet written into the task records. `decisions.json` ("accepted (prompt correction)", provisional) and `paired/results.md` agree.
