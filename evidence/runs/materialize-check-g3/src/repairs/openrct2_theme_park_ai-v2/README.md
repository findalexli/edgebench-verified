# OpenRCT2 Theme Park AI, fixed version: state the real length of play and the speed rule

## What this fixes

The original prompt says each scenario runs for about 4 game years, but the grader stops each scenario after 120 real seconds, which is about 70 game days at speed 4. The prompt also does not say that the plugin can lower the game speed. The fixed version corrects the prompt text only; the grader, images and scores are unchanged.

## What changes

### The problem in detail

The original prompt says "The engine runs each scenario for ~4 game years at speed 4". The grader
runs each scenario for `OPENRCT2_TIMEOUT=120` wall-clock seconds and scores the company value
at the last sample of the grader's monitor. It never checks that the monitor's 992-day target was reached.

OpenRCT2 advances at a fixed real-time rate: 40 ticks/s × 2^(speed-1), with 16,384 ticks per
month. At speed 4 that gives about 0.6 game days per wall-clock second, so a scenario covers about
**70 game days**, not about 980. The prompt also never says the solver can lower the speed,
which shortens the length of play further. Review: `../../evidence/reviews/openrct2_theme_park_ai.md`.
Measurements and arithmetic: `paired/results.md`.

### Exact change

One Rules bullet in `work.agent_query` (the task prompt) is replaced by two. Nothing else in the task JSON or
either image changes. `repair.patch` is generated from `orig/agent_query.md` to
`files/agent_query.md`, and from `tasks/openrct2_theme_park_ai.json` to `task.json.in`.

> - The engine runs each scenario (host --headless) for **120 wall-clock seconds**, not to a
>   fixed game date. Game time advances at a fixed real-time rate, so at speed 4 one scenario
>   covers only about **70 game days** (a little over 2 game months), not years. The score uses
>   the company value from the judge monitor's last sample before the 120-second cutoff
> - The judge monitor sets speed 4 when each scenario starts. Your plugin may also call
>   `gamesetspeed` with speed 1-4 (higher values are rejected); the most recent call takes
>   effect. A lower speed simulates proportionally fewer game days in the same 120 seconds
>   (speed 3 about half, speed 1 about one eighth)

`Dockerfile` is a documented no-op that pins the unchanged grader image. `task.json.in` keeps
both original `image_tag` values.

A search of the solver-visible files for other statements of the length of play found none:

- The work image's `/home` and `/tmp` hold `my_plugin.js`, `openrct2.d.ts` and four `samples/*.js`. There is no README.
- The grader image has only OpenRCT2's own `doc/` files.
- `openrct2.d.ts` already says a month takes about 6.8 minutes at speed 1, which agrees with the fix.

### Why a prompt fix, not a larger time budget

Reaching 992 days at the measured rate (0.595 days/s) takes about 1,667 s per scenario, about 83 minutes for
three. That exceeds the 120 s scenario budget by 14×, the wrapper's 1,800 s `TOTAL_TIMEOUT`
and the manifest's 2,400 s `eval_timeout`. Raising all three would multiply grading cost
about 14×. It would also change what is measured: value after about 4 years instead of about
2 months. Every score and score-scale reference point of the original version would stop being comparable, and the change would need
new validation runs over the full length. The prompt fix makes the task's promise true at zero cost and
keeps the grader byte-identical.

### Are scores comparable? The score scale

- The grader, images, timeouts and parser are unchanged. A given `my_plugin.js` gets the
  same score under the original and fixed versions, up to the usual run-to-run variation of a real-time game.
- The reference points of the score scale stay as they are: linear, 0 to 40000. They come from the original task and
  past runs. No new reference points were introduced.
- Runs of the original version had the same real 120 s length, so scores from the fixed version are comparable with the original's as
  measurements of the same grader. They are **not comparable as measurements of solver
  ability where a solver's strategy depended on the prompt.** A solver of the original version that planned for
  4 years of play may have invested in strategies that only pay off over years. A solver of the fixed version,
  told about the 70-day length, can front-load. It may also lower the speed
  deliberately. In those cases the fixed version's numbers reflect a better-informed solver, not the same
  task.

## How it was checked

Nothing executable changed, so no side-by-side scoring run on E2B (cloud machines) was made. Scores are unchanged by construction, so none was needed. The check is a measurement of the length of play on the original grader, in `paired/results.md`. In plain words: at speed 4 every 120 s scenario reached only 68 to 69 game days, and the 992-day target was never reached. A rate model built from the game's tick constants predicts the measured rates at speeds 1, 3 and 4.

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh
```

`materialize.sh` takes the following steps:

1. Pull the pinned image(s) by digest, unless already present.
2. Extract the original files with `docker create` and `docker cp`. No container runs in this step.
3. Check each original against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of every file under `files/` (and `orig/`) against `source-lock.json` → `materialize.outputs`. Any mismatch fails loudly.

After that, the `Dockerfile` builds without changes. Regenerated files keep the file mode they have in the image.
See `../MATERIALIZE-CHECK.md` for how each package was verified.

This fix changes only the prompt and pulls no image. `materialize.sh` takes `work.agent_query` from the EdgeBench repo's `tasks/openrct2_theme_park_ai.json` (set `EDGEBENCH_ROOT` if needed), writes `orig/agent_query.md`, and applies `repair.patch` to produce `files/agent_query.md`. The `Dockerfile` is a no-op, so there is nothing to build. The task JSON change is in `task-json.diff`.

## Limits

- **The incentive to lower the speed remains.** A submission may still lower the speed. On scenarios without a cap,
  that can freeze company value near its start, which may beat a declining park.
  The fixed version now states this honestly but does not prevent it. Removing the incentive needs a
  change to the grader, which is outside this prompt-only fix. Two options would work:
  re-assert speed 4 in the monitor every tick, or score at a fixed game date with a budget
  that is long enough.
- The number "about 70 days" assumes the engine keeps real time. With 0.25 CPU the measured
  rate fell about 2%. A slower or overloaded host, or a heavy plugin, could fall further
  behind real time. Hosts are not pinned.
- The measurements of the length of play come from one simple test plugin, with one run per configuration.
  No competitive plugin was run.
- No side-by-side run on E2B was made. Scores are unchanged by construction, so none was needed.
