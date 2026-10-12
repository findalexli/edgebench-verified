# Review: `openrct2_theme_park_ai`

## Claim under review

> "The default 120-second scenario call returned positive credit without verifying the promised approximately four-game-year endpoint. Genuine monitor samples support this finite result. This does not prove the engine never completed internally, score inflation or whole-task failure."

Earlier disposition: **pending (finding confirmed)**.

## Pinned artifacts

| Artifact | Identity |
|---|---|
| Task manifest `tasks/openrct2_theme_park_ai.json` | sha256 `09e2a4d83cb14b735a04f43a40764806d05cadc4206d293c5bd3f211cc051449` |
| Judge image | `seededge/edgebench.judge.openrct2_theme_park_ai@sha256:a5263578c1d4b1cf1c693d182254fdbd7f0bd07631edadf3523467b1cfd43c7f` (pulled and run locally) |
| `/tmp/eval_openrct2.py` (wrapper) | `7fdde3e0fe0e2fbdc06cb03fa792552ac17e92901a3e75d5b015cf46778d133c` (identical in image and cloud export) |
| `/tmp/openrct2_original_eval.py` (helper, monitor and scorer) | `bfcf7ab998eb1136e5e54f52416c47f3c9b659fa72c5c5c2044b3a88859c155b` (identical) |
| `openrct2-cli` | `b103227e3f195f6ac7effa0559c4af527502b5917357ae53b1b209fc9cc74fcb` |
| Scenarios small / medium / large | `83c824c7…5f44` / `a951f00e…ed11` / `821a75cc…e585e` |

## Contract

- Prompt, in the agent_query Rules section: **"The engine runs each scenario for ~4 game years at speed 4 (host --headless)"**. It also says "Scoring is performed by a hidden judge monitor that reads the real in-game `park.companyValue`". The Key APIs section says `gamesetspeed {speed: 4}` is "max speed (host mode cap is 4)". The prompt does not *require* the solver to set speed 4.
- `eval_cmd`: `OPENRCT2_TIMEOUT=120 python3 /tmp/eval_openrct2.py`. The wrapper passes `--timeout 120` per scenario and caps the whole run at `TOTAL_TIMEOUT = 1800` s. The manifest's `eval_timeout` is 2400 s.
- Monitor (`write_monitor`): `targetDays = 992`, about 4.05 OpenRCT2 years of 245 days. It emits `DONE` only when `days >= targetDays`, and emits a `SCORE` sample every 14 game days or every 1024 ticks.
- Scorer (`run_scenario` → `score_scenario`): `final_value` is the company value from the **last sample seen**, whether `SCORE` or `DONE`. `run_scenario` leaves its loop when `time.time() - t0 > timeout` *or* when it sees `DONE`. **Nothing records or checks whether `DONE` was reached**, and the returned metrics contain no date or completion field. The score is `value / BASELINE × operation multiplier`, with a cap of 1.10 when the plugin has not built and opened an expansion ride, and a ceiling of 2.0.

So the value is scored at whatever game date the 120-second wall clock reaches. It is not the value at the promised end date.

## Independent reproduction

`scripts/openrct2_theme_park_ai/driver.py` imports the original helper unchanged and calls its own `validate_plugin`, `run_scenario` and `score_scenario`. The only addition is a wrapper on `Popen` that copies engine stdout lines (a tee) so the monitor's date fields and any `DONE` line are recorded. `plugin.js` is my own ordinary plugin: it sets speed 4 and periodically opens rides with `ridesetstatus`. Its `staffhire` call failed with "Invalid action parameters", so the staff gate failed in every run. That does not affect the horizon question. Runs used `docker run --rm --network none --memory 2g --cpus 2`, or `--cpus 0.25` where noted.

| Run | Scenario | Monitor samples | DONE seen | First → last date (y,m,d) | Game days | Days per wall-second | Company value first → last | Normalized score |
|---|---|---|---|---|---|---|---|---|
| 120 s, speed 4 | large | 41 | no | 41,0,19 → 41,2,26 | 68 | 0.595 | 123,280 → 114,810 | 1.10 (capped) |
| 120 s, speed 4 | medium | 42 | no | 8,4,25 → 8,7,2 | 69 | 0.595 | 198,010 → 133,260 | 0.915 |
| 120 s, speed 4 | small | 41 | no | 61,1,27 → 61,4,4 | 68 | 0.593 | 124,540 → 96,680 | 1.10 (capped) |
| 60 s, speed 4 | small | 20 | no | → 61,2,30 | 33 | 0.597 | → 111,940 | 1.10 |
| 60 s, speed 4, 0.25 CPU | small | 17 | no | → 61,2,24 | 27 | 0.582 | → 116,840 | 1.10 |
| 60 s, plugin sets **speed 1** | small | 2 | no | → 61,1,29 | 2 | 0.077 | → 124,470 | 1.10 |

The three-scenario average was **1.038**. The wrapper prints that as `TOTAL_SCORE 10384`, which is positive credit. The earlier audit's small-scenario result reproduces closely: 68 days, last date 61,4,4, score 1.1.

### Quantification

- The observed rate at speed 4 is 0.595 game days per wall-second, about 318 ticks/s. That matches OpenRCT2 running in real time at 8× (40 ticks/s × 8; 16,384 ticks per month). Speed 1 ran 8× slower (0.077 days/s). Cutting CPU to 0.25 changed the rate by only about 2%. **The engine is limited by real time, not by host CPU**, at least for these scenarios and this plugin.
- Reaching 992 days at that rate takes about **1,667 s (27.8 min) per scenario**, or about 83 min for all three. That is far beyond the 120 s scenario budget, the 1,800 s wrapper cap and the 2,400 s manifest timeout.
- In 120 s each scenario covers **68 to 69 game days, about 7% of the promised horizon**, roughly 2.2 game months.
- Fitting 4 game years into 120 s would need about 4,400 ticks/s. That is about 110× normal speed and about 14× the speed-4 rate. The host-mode cap of speed 4 cannot reach it.

## Refutation attempts

1. *Maybe the engine finishes internally and the DONE line is just lost?* No. At 0.595 days/s the engine can reach only about 71 days in 120 s. Completing 992 days would need 14× the measured rate. Given the measured real-time cap, I rule out completion inside the budget, although no engine-internal state was read directly. The earlier claim's caveat ("does not prove the engine never completed internally") is more cautious than necessary.
2. *Is it only a documented wall-clock cap?* No. The prompt states a game-time horizon of about 4 years and never mentions a 120 s wall budget. The 4-year statement is false for the shipped configuration by a factor of about 14.
3. *Do scores depend on host speed?* Only weakly in these runs: 0.25 CPU gave 27 days instead of 33 in 60 s. Slower or heavily loaded hosts, or heavier plugins, could fall further behind real time. Host dependence is a secondary concern. The primary problem is that the horizon is set by the wall clock and is about 14× shorter than promised.
4. *Does it matter for scores?* Yes, in principle. The scored value is a snapshot at about game day 68 instead of about day 992, and the value trajectory moves throughout the window. In my runs it fell steadily, for example from 198,010 to 133,260 on medium. Strategies that pay off over years, such as building rides, repaying loans or slow guest growth, are scored before they can pay off, and front-loaded strategies are favoured. That changes *what* is measured. I did not show that it inflates or deflates any particular solver's score, and the 1.10 cap often hides the differences.
5. *New observation: the solver controls the horizon.* `gamesetspeed` is on the allowlist and the prompt does not require speed 4. A plugin that sets speed 1 reaches only about 9 game days in 120 s, and a lower speed can freeze the park near its starting value (124,470 at speed 1 against 111,940 at speed 4 after 60 s). Here the 1.10 cap masked the difference, but uncapped scenarios could reward slowing the game down. Whether that is "cheating" is not stated in the prompt. This is another consequence of scoring at a wall-clock cutoff.

## Formal check

None. The horizon gap is arithmetic on measured rates.

## Verdict

**CONFIRMED.** The score comes from a wall-clock snapshot at about 7% of the promised horizon, and nothing checks completion. I would make the claim stronger than the earlier wording: with the shipped budgets, the promised horizon is **infeasible**, not merely unverified.

## Disposition assessment

I disagree with leaving it pending for open-ended native work. The defect is a contract and evaluator mismatch: the prompt promises about 4 years, while the evaluator scores about 68 days through an untracked wall-clock cutoff. It is confirmed by inspecting the source and by native runs in the original image. Either option would be proportionate:
- **(a) Repair the prompt**, so it states the real horizon, for example "each scenario runs for 120 wall-seconds (about 2 game months at speed 4); the score is the company value at the last monitor sample", and says whether solvers may lower the speed. That keeps the evaluator and existing scores comparable.
- **(b) Repair the evaluator** to enforce the 4-year horizon. That needs about 28 min per scenario plus larger wrapper and manifest timeouts, and changes scores incomparably.

The earlier completion-gate patch, which gives zero to incomplete runs, would score **every** submission 0 under the shipped 120 s budget, because DONE is unreachable. It is unusable unless the budgets are also raised about 14×. Its own limits note says this ("Original 120-second scenario… do not establish full-horizon feasibility"), but the consequence should be stated plainly.

## Recommended publishable wording

"The prompt says each scenario runs for about four game years. The evaluator actually stops each scenario after 120 wall-clock seconds, about 68 game days (around 7% of that horizon) at the engine's real-time-limited speed 4. It then scores the last sampled company value, without checking completion. Effects on individual solver scores were not measured."

## Repair note

The smallest correct fix is to the prompt (option a), plus requiring speed 4 or recording the reached date. A completion gate alone (the earlier proposal) is not a correct fix under the current timeouts. If the 4-year horizon is kept, raise `OPENRCT2_TIMEOUT` to at least 1,700 s, the wrapper `TOTAL_TIMEOUT` to at least 5,200 s and `eval_timeout` to match, and validate with a completed run.

## Limits

Each configuration ran once with a single simple plugin whose staff hiring failed. I did not use a competitive plugin and made no claims about score distributions. Engine stdout was observed only through the monitor lines. The real-time-cap inference rests on rates measured at speeds 1 and 4 and at 0.25 and 2 CPUs on one host. The 40000 rescale anchor was not examined. I ran the full three-scenario sequence through the helper's own functions, not through `eval_openrct2.py`. The wrapper only parses those same printed lines.
