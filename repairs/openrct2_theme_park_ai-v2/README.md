# openrct2_theme_park_ai v2: state the real horizon and speed rule

## Defect

The v1 prompt says "The engine runs each scenario for ~4 game years at speed 4". The evaluator
runs each scenario for `OPENRCT2_TIMEOUT=120` wall-clock seconds and scores the company value
at the judge monitor's last sample. It never checks that the monitor's 992-day target was reached.

OpenRCT2 advances at a fixed real-time rate: 40 ticks/s × 2^(speed-1), with 16,384 ticks per
month. At speed 4 that gives about 0.6 game days per wall-second, so a scenario covers about
**70 game days**, not about 980. The prompt also never says the solver can lower the speed,
which shortens the horizon further. Review: `../../evidence/reviews/openrct2_theme_park_ai.md`.
Measurements and arithmetic: `paired/results.md`.

## Change

One Rules bullet in `work.agent_query` is replaced by two. Nothing else in the task JSON or
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

`Dockerfile` is a documented no-op that pins the unchanged judge image. `task.json.in` keeps
both original `image_tag` values.

I searched the solver-visible files for other horizon statements and found none:

- The work image's `/home` and `/tmp` hold `my_plugin.js`, `openrct2.d.ts` and four `samples/*.js`. There is no README.
- The judge image has only OpenRCT2's own `doc/` files.
- `openrct2.d.ts` already says a month takes about 6.8 minutes at speed 1, which agrees with the fix.

## Why a prompt fix, not a budget increase

Reaching 992 days at the measured rate takes about 1,660 s per scenario, about 83 minutes for
three. That exceeds the 120 s scenario budget by 14×, the wrapper's 1,800 s `TOTAL_TIMEOUT`
and the manifest's 2,400 s `eval_timeout`. Raising all three would multiply evaluation cost
about 14×. It would also change what is measured: value after about 4 years instead of about
2 months. Every v1 score and anchor would become non-comparable, and the change would need
new full-horizon validation runs. The prompt fix makes the contract true at zero cost and
keeps the evaluator byte-identical.

## Score compatibility and anchors

- The evaluator, images, timeouts and parser are unchanged. A given `my_plugin.js` gets the
  same score under v1 and v2, up to the usual run-to-run variation of a real-time game.
- Rescale anchors stay as they are: linear, 0 to 40000. They come from the original task and
  historical runs. No new anchors were introduced.
- v1 runs had the same real 120 s horizon, so v2 scores are comparable with v1 scores as
  measurements of the same harness. They are **not comparable as measurements of solver
  ability where a solver's strategy depended on the prompt.** A v1 solver that planned for a
  4-year horizon may have invested in strategies that only pay off over years. A v2 solver
  told about the 70-day horizon can front-load. A v2 solver may also use speed lowering
  deliberately. In those cases the v2 numbers reflect a better-informed solver, not the same
  task.

## Limits

- **The speed incentive remains.** A submission may still lower the speed. On uncapped
  scenarios that can freeze company value near its start, which may beat a declining park.
  v2 now states this honestly but does not prevent it. Removing the incentive needs an
  evaluator change, which is outside this prompt-only repair. Two options would work:
  re-assert speed 4 in the monitor every tick, or score at a fixed game date with a budget
  that is long enough.
- The number "about 70 days" assumes the engine keeps real time. With 0.25 CPU the measured
  rate fell about 2%. A slower or overloaded host, or a heavy plugin, could fall further
  behind real time. Hosts are not pinned.
- Horizon measurements come from one simple control plugin, with one run per configuration.
  No competitive plugin was run.
- No E2B paired run was made. Scores are unchanged by construction, so none was needed.

## Build

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

This repair changes only the prompt and pulls no image. `materialize.sh` takes `work.agent_query` from the EdgeBench repo's `tasks/openrct2_theme_park_ai.json` (set `EDGEBENCH_ROOT` if needed), writes `orig/agent_query.md`, and applies `repair.patch` to produce `files/agent_query.md`. The `Dockerfile` is a no-op, so there is nothing to build. The task JSON change is in `task-json.diff`.
