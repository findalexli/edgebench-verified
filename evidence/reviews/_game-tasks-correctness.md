# Game tasks: good-faith scoring correctness (10 tasks)

Reviewer: Claude (critical re-verification). Date: 2026-10-11. Scope: does the original task score an
**honest** solver correctly and repeatably? This review does not cover ways a submission could
tamper with or bypass the scorer. Scorer isolation: see the separate robustness review.

Method: I read the sources first. I made no image pulls and started no cloud or native game runs.
Local checks were small (less than 2 GB, under `timeout`). I reused accepted earlier native results
and did not rerun them. To read two library contracts at source level, I downloaded the public
upstream packages into scratch:

- NLE 1.2.0 wheel, sha256 `5bbc7bc2fc3b4f2769c25acab99603146222e3b2fd3a82a514a6d8542c985170`
- Jericho 3.3.1 sdist, sha256 `032dde60a155dd9984d6db05b2c6ac22897446fb13a6a248cff8086001185571`

Jericho 3.3.1 is the version the earlier six-session runtime lock names. For NLE, `nle==1.2.0` is the
version the prompt states; I did not read it from the image.

Reproduce: `python3 scripts/_game-tasks-correctness/check_arith.py <treant cases dir>`. Its output is
saved as `check_arith.out.json`. `bash scripts/_game-tasks-correctness/run_treant_baseline.sh ...` runs
the original Treant evaluator, tester and shipped baseline (see the header for arguments).

## Pinned sources

All copies under `$W/work/task-sources/merged/<id>/` match, byte for byte, the hash-pinned copies in
`scripts/_game-tasks-triage/`.

| file | sha256 |
|---|---|
| `sforge/harness/game_server_app.py` | `379572e99bbff5f89dbad92b81b88093a79a5fcee34ddefe809e821b01d8b983` |
| `sforge/harness/judge_server.py` | `77410d7e4705df03418d0676ddbb74241da7746190807cb073fbcdae3edf4e04` |
| `sforge/harness/grading.py` | `b3eeac727152eee941dc892a49aaaa7ba68ed9b249b1eb74076b2c511b6d04d7` |
| `sforge/harness/selection.py` | `3338ed2461118d22cf0b6f9d9b01b77a0255561ca01b3827a426c1cc585e2fba` |
| `sforge/harness/score_rescale.py` | `98feb630390f217cb67e21315b5ca8a4f2eb6d1bb28cc9822152b3ed58be4b19` |
| `tmp/eval_dcss.py` | `101e8858c5c952bf8cd8b4ae1d4889420b0e35448522e42e2f29b85607ad2218` |
| `tmp/eval_nethack.py` | `5bd47b4f4eea5d15b4033a1a11d4fde1eede800af5e61d4aa4468d6fd4514787` |
| `tmp/eval_openttd.py` / `tmp/openttd_original_eval.py` | `167e480ac2046406999b297a122c196d28160748942aba9a35f622cefb70ba56` / `76dae84357c7cf0baf1d712bd88086ce12c0475129d29c9daa1656cb6b123634` |
| `tmp/eval_wesnoth.py` | `b1cbe456fc1595c28cee023d9a4955fe5c7aa7e5a75151614dd69b83e5e16165` |
| `tmp/eval_treants_forest.py` | `ce2833ac1fadf2fc531901b4a168b31942530a8ac64decf7b762252983682048` |
| treant `tools/bin/tester` (image layer `7091930b…`, from `treant-selected-source.tar.gz` `264e1699…`) | `6cbb3a729d0899495bf924f39d34b5cb2767ec167dffa727e1c064911e0e8551` |
| treant 50 cases (sha256 of the sorted `sha256sum` listing) | `bc256294fcbd5fe2850fc5c7d568430bafa95489f8a64f8de35903c401dafbb0` |
| `tmp/eval_apple_incremental_game.py` | `c33f5257323029aa6bda5ddec61f3ea81853e07c11dfc4d833aea11c21f6d70c` |
| loco-rl `sebench_eval.py` / `eval/evaluate_policy.py` / `task_prompt.md` | `9bb2f8bf44ac02849ae723bd1035bfd0194042daa5b132b305ecd2e526c2838a` / `431053573adce4dd51a647171b440c14933af0060ac94eaa1dc5141561ba7b68` / `e4023718e500912b17e9d8285ad34055ce9a80706304697b96f6e150f36aadcf` |
| NLE 1.2.0 `nle/env/tasks.py` | `b51cd124dfa896f45d5e4522656fdb2a7d964d66012ba56ec1f631036a5123c3` |
| Jericho 3.3.1 `jericho/jericho.py` / `game_info.py` | `94f2e745cfd96deffaa95f7ea24b6be34a6ef29a2bc5c4b2bce891c1315353f8` / `70abb19e75e9f390d2109d5d772285d07ad102a33b298b96b911ee87bf89dceb` |

Task JSON sha256 values match the `manifest_sha256` values on the task cards. They are listed in the
per-task sections.

Harness facts used throughout:

- **Best-of-N selection.** `score_first` takes the maximum valid score over every submission or game
  (`selection.py:106-117`).
- **Validity gate.** A result marked `valid:false`, or one where the harness timed out, gets no score
  (`grading.py:292-293,314-315`; `selection.py:64`).
- **`score_sum` parser.** The score is the `TOTAL_SCORE` line. A failed case does not invalidate the
  result (`grading.py:138-200`).
- **No task-level CPU limit.** None of the ten task JSONs sets `cpu_limit`, so the CPU allocation is
  whatever the operator configures (`task_spec.py:231`).

---

## 1-3. Anchorhead / Trinity / Tryst (Jericho text adventures)

Task JSON sha256: `4b92b45a…31cb2`, `7364a012…c0ee`, `a6e4815a…1b5f`.

**(1) Score definition.**

- **Engine score.** Each step reads `env.get_score()` into `current_score` (`game_server_app.py:131-134`).
  Jericho reads it from Z-machine memory (for example `anchor.c` `zmp[38024]`).
- **Archived game score.** When a session ends, the archived entry's `score` is `final_score =
  current_score`, **not** `peak_score` (`judge_server.py:247-260`).
  - Sessions end in four ways: done (auto-close, `:735-769`), explicit close, idle reap, or eviction
    (`:216-239`).
  - All four paths archive the score.
- **Selection.** `score_first` takes the maximum final score over all games in the run.
- **Rescale.** Linear from 0 to `upper` (`score_rescale.py:80-84`): 100, 100 and 350. These equal
  Jericho's `max_score` (`anchor.c:84-86`, `trinity.c:71-73`, `tryst.c:97`). The lower anchor of 0 is
  the start score.
- **Earlier native result (reused):** 99/100, 100/100 and 350/350 normalize to 99, 100 and 100.

There is no shipped baseline, and the anchors are the game's own scale, so they are consistent.

The one open item is Anchorhead. The supplied walkthrough ends at 99 with game_over=true and
victory=false. Whether 100 is reachable is unverified, so the ceiling uncertainty is at most 1
normalized point.

**(2) Promise vs. budget.**

The prompt promises only "maximize your score". It states no horizon, step cap or number of games.
There is no engine step cap. The 531, 610 and 518 commands of the full walkthroughs replayed in
about 3 s of engine time.

The real limits are harness limits the prompt does not disclose:

- 10 s HTTP timeout per step (`judge_server.py:714`)
- at most 3 concurrent sessions per run, with the oldest evicted (`:158,563-573`)
- **600 s idle reaping** (`:156,216-224`)

Reaping and eviction archive the current score, so no score is lost. However, an agent that pauses
for more than 10 minutes mid-game loses the live game and must replay it. Replaying is cheap because
the games are deterministic. There is no OpenRCT2-class horizon problem.

**(3) Repeatability.**

- **Deterministic engine.** `FrotzEnv(rom)` with `seed=None` falls back to the binding seed, which is
  0 for all three games (`jericho.py:444`, `game_info.py`).
- **Fixed RNG start.** Seed 0 sets `user_random_seed=0`, so `os_random_seed()` returns 0 rather than
  the time (`dumb_init.c:278-284`).
- **Independent corroboration.** The earlier six sessions saw identical prefix trajectories
  (`prefix_numeric_equal=true`).

The game is therefore fully deterministic given the command sequence.

**(4) Honest-play scoring issue.** None found.

- The score is *final*, not *peak*, while the API also returns `peak_score`, which could mislead an
  agent. This matters only in a game where points can be lost. All three supplied trajectories had
  final equal to peak, so it is a documentation note.
- Best-of-games selection is intended ("maximize").

**(5) Recommendation: retain with a note** for all three.

Notes to publish:

- The score is the final in-game score of the best completed or closed session, out of the game's
  max_score.
- Sessions are reaped after 600 s idle.
- Anchorhead's reference walkthrough reaches 99/100, and full score was not demonstrated.

Remaining check: none would change the disposition. The only open question that could change a
note is whether Anchorhead can actually reach 100/100: a command sequence that attains 100 in the
pinned ROM would remove the caveat. The HANDOFF items still pending (refreezing derived pins,
`ReleaseCheck.task()`, approvals) are release bookkeeping, not science.

---

## 4. DCSS (`dcss_dungeon_ai`)

Task JSON sha256 `7d89425a7b6e072e3ff3b4faf4cd171b60946584c4dd33cabdad298af20a42a4`. Evaluator `eval_dcss.py`, sha256 `101e8858…2218`.

**(1) Score definition.**

- **Per game:** the integer on morgue line 5 (`:81-91`), zeroed if wizard or explore mode appears.
- **Aggregate:** mean of 5, rounded to 0.1 (`:210`). Emitted as `structured_json` with
  `"valid": ok == total` (`:217-219`).
- **Rescale:** `log1p_max`, `100*log1p(raw/400)/log1p(125)`.

| Raw mean score | Normalized |
|---|---|
| 0 (idle bot; accepted earlier) | 0 |
| 12.4 (accepted earlier five games: 2, 21, 18, 7, 14) | 0.63 |
| 400 | 14.3 |
| 5,000 | 53.8 |
| 20,000 | 81.3 |
| 50,000 | 100 |

The shipped baseline sits at essentially 0. Whether 50,000 is reachable in 900 s is **unverified**:
I found no strong-bot run.

**(2) Promise vs. budget.**

The prompt promises 5 hidden seeds, 900 s per game in parallel, the mean, and a forced quit at the
deadline. The code matches: 5 seeds at `:15`, `TIMEOUT=900` at `:16`, parallel 5 at `:185`, the
quit sequence at `:141-153`.

Sleep schedule per game:

| Path | Seconds |
|---|---|
| Setup | ~11 |
| Normal path (forced quit 9.5 s plus a morgue wait of at most 18 s) | ≤ ~948 |
| Hard-timeout path (`TIMEOUT+90`, `:131`) | ≤ ~1008 |

All of these fit `eval_timeout` 1100. The accepted idle run took 962 s in total. This fits, with a
margin of about 90-140 s.

**(3) Repeatability.** The seeds are fixed, but **the result is wall-clock and host-speed dependent
by design.**

- Score is roughly turn_rate × 900 s, and turn rate depends on the CPU given to 5 concurrent crawl
  and screen processes. No CPU limit is set.
- `_dismiss_loop` injects space, CR and Esc every 1.5 s of wall time throughout play (`:68-75,127`).
  This puts a timing-dependent input stream into the game.

The prompt admits "small score noise". The size of that noise has never been measured: there is one
positive five-game run and no repeat.

**(4) Honest-play scoring issue (conditional).**

The prompt says the score is the "mean score across all 5 games" and calls Pass rate "a validity
check". However, the evaluator sets `valid = ok == total` (`:218`), and the harness voids invalid
results (`grading.py:292`, `selection.py:64`).

So if a single game fails to produce a morgue, the whole submission gets no score, rather than that
game counting as 0. A game fails this way when the forced-quit sequence fails twice (`pkill` at
`:135`, then `WA`).

This path was not observed in the accepted runs ("No missing-morgue case was observed"). Best-of-N
selection softens the impact.

**Recommendation: retain with a note.** The notes cover wall-clock dependence, the all-5-morgues
validity rule, and the fact that the 50,000 anchor is unverified.

Decisive remaining check: rerun the same positive bot through the same five-game evaluation twice on
one fixed CPU allocation of at least 5 cores, and once on half that. If the run-to-run spread is
comparable to the differences between bots, the disposition moves to repair or withhold (fixed
turn budget instead of wall time).

---

## 5. NetHack (`nethack_dungeon_agent`)

Task JSON sha256 `90a9ba87c5f50d17f8a369c34477818035b3d8e2f792076e8cb06d672f958fcb`. Evaluator sha256 `5bd47b4f…4787`.

**(1) Score definition.**

- **Per game:** the **peak over steps** of `blstats[9]`, the bottom-line score (`:57-67,133`).
  - Positive → OK.
  - 0 → WA with score 0 (`:144-146`).
  - Timeout → TLE with score 0 for the whole game (`:152-154`).
- **Aggregate:** `TOTAL_SCORE` is the mean of 20 games, zeros included (`:212-215`).
- **Rescale:** linear from 0 to 1000.

The shipped `agent.py` (sha256 `0692d319…`) is a random walk. The accepted native trajectory scored 0
(5,000 steps, peak 0), which gives 0 and is consistent with the lower anchor. The 1000 anchor is
plausible for a competent agent within 5,000 steps, but **unverified**: no positive control exists.

**(2) Promise vs. budget.** The prompt states **no horizon and no time limit.**

The evaluator enforces two hidden limits:

- `MAX_STEPS=5000` (`:21`; it appears only as the skeleton's `--max-steps` default)
- `GAME_TIMEOUT=120` s of wall time per game, including imports (`:22,152`)

With 5,000 steps, 120 s is about **24 ms per step** for the agent plus NLE. An honest agent that
does per-step planning above that rate loses the *entire* game's score: TLE gives 0, with no partial
credit for the peak already reached.

20 sequential games × 120 s = 2,400 s, which is within 3,600 s. The overall budget is fine. The
issue is the undisclosed per-game cliff.

**(3) Repeatability — not seeded (source-confirmed).**

- `NetHackChallenge.seed()` raises `RuntimeError("NetHackChallenge doesn't allow seed changes")`
  (NLE 1.2.0 `nle/env/tasks.py:371-372`). The core seed setters are also replaced with raising stubs
  (`:343-348`).
- `reset_env` swallows the exception (`eval_nethack.py:71-74`) and calls `env.reset()` without a
  seed (`:75`).

So the "10 seeds × 2 repeats" are **20 independent unseeded games**, and the starting character is
random too (`character="@"`). Only Python's `random`/`numpy`, which the agent uses, are seeded
(`:50-54`). NetHack scores are heavy-tailed, so the 20-game mean has run-to-run variance that has
never been measured. The prompt does not claim seeding.

**(4) Honest-play issue.**

- The ineffective seeding makes results non-reproducible.
- The undisclosed 120 s per-game TLE cliff can zero an honest game.

Peak versus final is a definitional choice: botl score can fall when gold is spent. The prompt says
only "maximize game score", which is loosely consistent with peak.

**Recommendation: retain with a note.** The note should say the 20 games are unseeded random games,
and give the 5,000-step and 120 s per-game limits. If publication needs reproducible numbers, the
fix is to repair the evaluator or disclose the variance; the fix is not to repeat runs.

Decisive remaining check: run a simple positive agent (for example, descend-and-fight) through the
default 20-game evaluation twice. This measures the spread of the mean, and the per-step wall time
against 24 ms.

---

## 6. OpenTTD (`openttd_transport_ai`)

Task JSON sha256 `7ec35c5f0065dd4b2e621077cc38491382899611a4c5fee9398dc62148bb0bd5`. Evaluators sha256 `167e480a…ba56` and `76dae843…3634`.

**(1) Score definition.**

- **Per seed:** the last monthly autosave whose `old_economy[0].company_value > 1`
  (`openttd_original_eval.py:58-77`). That value is the most recent quarterly value, about Oct 1969,
  for a 7,300-day run.
- **Aggregate:** the mean over the seeds that *returned*, printed as `{avg:,.0f}`
  (`:150-166`). The wrapper parses it with `最终得分.*?:\s*([\d,]+)` (`eval_openttd.py:43-51`).
- **Seeds:** `OPENTTD_N_SEEDS=5` gives seeds 0-4, the same seeds as the prompt's local-testing
  snippet. There is no holdout, but this is not a correctness issue.
- **Rescale:** `log_max`, 100·log(raw/1e5)/log(1e4). 1e5 → 0, 1e6 → 25, 1e7 → 50, 1e9 → 100.

For the shipped do-nothing AI, I reasoned from engine source and did not run it. Money starts equal
to the loan and interest is paid on the loan, so OpenTTD's `CalculateCompanyValue` clamps the value
to 1. The evaluator filters that out, giving score 0 → 0, which is consistent. Whether 1e9 is
reachable is **unverified**.

**(2) Horizon vs. budget.**

- 20 years × 365 days × 74 ticks/day = 540,200 ticks per seed.
- The 5 seeds run in parallel (`max_workers=min(5, os.cpu_count())`, `:120`).
- Finishing within 3,600 s needs only about 150 ticks/s per game. A headless null-video OpenTTD run
  is normally much faster.

This is not an OpenRCT2-class problem, but no native run has measured it. Note that
`os.cpu_count()` sees the host's CPUs, not the cgroup's. Also, the wrapper's internal `TIMEOUT=3600`
equals the harness `eval_timeout` 3600, so a slow run ends as a harness timeout (invalid), not as
`TLE`.

**(3) Repeatability.** Good in principle. OpenTTD is deterministic (lockstep multiplayer design), and
Squirrel AIs are opcode-scheduled with no wall clock. This is not measured.

**(4) Honest-play issues (minor or conditional).**

- The mean uses the number of seeds that returned, not the number requested (`:153`). The earlier
  library review showed that an existing empty save directory returns no rows, and reachability with
  a real game is unresolved.
- A company whose final value is ≤ 1 (negative net value) is scored at its last positive quarter,
  not 0 (`:75`).
- The prompt's metric is `GetCompanyValue`. The evaluator's is the last quarterly snapshot, which is
  close but not identical.

**Recommendation: retain with a note.** This is provisional until one native run exists.

Decisive remaining check: one native 5-seed evaluation of the baseline and one simple road-vehicle
AI. Record the wall time against 3,600 s, check that every seed returns about 240 saves, and confirm
the score is nonzero for the simple AI.

---

## 7. Wesnoth (`wesnoth_tactical_ai`)

Task JSON sha256 `b03e7eaafb4bddc146b82d80c38eb7222d4b2d3d7130253a2fc5b4903324cf63`. Evaluator sha256 `b1cbe456…6165`.

**(1) Score definition.**

- **Per game:** `WINNER:` and `GAME_END_TURN:` are parsed from the `ai/testing` debug log
  (`:126-130`). I did not check from Wesnoth source that the engine prints these markers.
- **Aggregate:** `TOTAL_SCORE = int(round(80*wins/60 + 20*mean_over_wins(min(1, base/turns))))`
  (`:167-184`). A win with no turn marker counts as a win with efficiency 0 (`:172-175`).
- **Rescale:** linear from 0 to 100, which is an identity map of the integer.

The prompt says the baseline "typically scores 0-20". That is plausible because the shipped cfg
lacks the main `move_to_targets` CA, but it is not measured.

**(2) Promise vs. budget — likely OpenRCT2-class.**

The default configuration runs 3 maps × 10 seeds × 2 repeats = **60 sequential games**
(`:27-28,145-151`). Each has `TIMEOUT=180` and `--turns 50`, under `eval_timeout` **900 s**. That
requires a **mean of ≤ 15 s per game, including Wesnoth start-up**.

| Mean wall time per game | Total for 60 games |
|---|---|
| 15 s | 900 s |
| 20 s | 1,200 s |
| 30 s | 1,800 s |
| 180 s (worst case) | 10,800 s |

A headless default-RCA-versus-RCA game of about 15-20 turns on these maps very plausibly takes more
than 15 s. If it does, every evaluation hits the harness timeout and is invalid, and no score can be
obtained.

Not measured: both earlier engine attempts failed during setup, so there is no valid game timing.

**(3) Repeatability.**

- `--rng-seed` is fixed.
- The sandbox header pins `math.randomseed` and `os.time` (`:36-38`).
- With a fixed seed, the 2 repeats are expected to be identical. They double the runtime without
  adding information, though this is unverified.

**(4) Honest-play issues.**

- The time budget above.
- Only top-level `*.lua` files are installed, with the sandbox header prepended (`:100-105`). An
  honest AI that keeps Lua files in subdirectories would fail to load.

**Recommendation: pending. Withhold the original if the decisive check fails; repair is easy.** The
repair is either an `eval_timeout` of at least 60 × the measured game time with margin, or
`N_REPEATS=1`, or fewer seeds.

Decisive remaining check: time one original `run_game` with the shipped baseline cfg on one map in
the judge image, and confirm `WINNER`/`GAME_END_TURN` are printed. If the measured time is more than
about 14 s, the default evaluation cannot finish in 900 s.

---

## 8. Treant forest (`treant_forest`, AHC054 adaptation)

Task JSON sha256 `2fdb98ce1166a1fea4743c2ae1613479bdf9eaf755cab190bfd931bc547a615e`. Evaluator sha256 `ce2833ac…2048`. Tester sha256 `6cbb3a72…8551`.

**(1) Score definition.**

- **Per case:** the tester's `Score = turns` (tester:249-250), parsed by the evaluator (`:26-34`).
- **Aggregate:** the sum over the 50 shipped cases (`:50-58`).
- **Rescale:** `piecewise_max`, with baseline 5,369, rank30 88,189, rank1 330,195 and super 451,198.

**Turn cap.** The tester caps turns at `max_turns = N*N*2` (tester:63, loop at :140). The README
does not mention this cap, so the per-case score is at most 2N².

**Anchor problem (confirmed by exact arithmetic on the 50 shipped cases):**

- The sum of 2N² over the 50 cases is **92,304**. This is the maximum attainable raw score.
- That maximum maps to **21.02/100** (exactly 2543510/121003).
- rank1 (330,195) is **3.58×** the attainable maximum. Every normalized score above 21.02 is
  therefore **unreachable** by any submission.
- Control: the original evaluator with the original tester and shipped baseline gave TOTAL_SCORE
  **3,418** with 50/50 cases OK, which maps to 0 and is consistent with the lower anchor.

The anchors appear to come from a different scoring scale or case set; their provenance was not
recovered.

**(2) Promise vs. budget.** Fine.

- README: 60 s per case. Evaluator: 120 s per case, with 8 workers.
- Worst case is 7 waves × 120 = 840 s, under 870 s (tight). At the README's 60 s it is 420 s.

**(3) Repeatability.**

- The tester is deterministic, because destination candidates are embedded in the input.
- Solutions that run on a wall-clock time budget depend on the CPU available to the 8 parallel
  workers, and no CPU limit is set.

**(4) Honest-play issues.**

- The **rescale ceiling is 21**, so the normalized scores are compressed. Ordering is preserved.
- The 2N² cap is undisclosed.
- The earlier movement-semantics question (tester versus primary game) remains unresolved.

**Recommendation: repair the rescale anchors**, which needs only a rescale change and leaves the
evaluator bytes alone. Re-derive the anchors under this tester and these 50 cases, with the ceiling
at or below 92,304. Otherwise, publish with an explicit "maximum 21.0" note.

Decisive remaining check: recover where the anchors came from. Were they computed on the original
AtCoder scorer or case count? If they were meant for this tester, then the defect is confirmed as an
anchor error.

---

## 9. Apple incremental game (`apple_incremental_game`, AHC058)

Task JSON sha256 `19021ddcbcaf966d7d43300b439862290a5c6c283aa6e6641f96efa07b34a25c`. Evaluator sha256 `c33f5257…d70c`.

**(1) Score definition.**

- **Per case:** `round(1e5·log2 S)` (README:34-36), computed by the tester. I did not have the tester
  binary.
- **Aggregate:** the sum over 50 cases, with the same evaluator code as Treant and `TIME_LIMIT=30`.
- **Rescale:** `piecewise_max`, with baseline 45,000,000 (900,000 per case, that is S = 2⁹) and rank1
  282,791,094.
- **Shipped do-nothing baseline:** S = K = 1, so the score is 0, which maps to 0.

Independent check: the earlier one-step-lookahead greedy simulator (`triage/apple/greedy_lookahead.py`)
was rerun on all 50 shipped cases.

- It scored a sum of **237,518,875** (4.75M per case), which maps to **17.7**.
- That is below rank30 (5.25M per case) and in the expected order. The anchors are consistent with
  honest strong play.
- Limit: the simulator follows the README rules. It is not the pinned tester.

**(2) Budget.** 7 waves × 30 s = 210 s, within 600 s.

The README states a 1 GB memory limit, but the evaluator does not enforce it. This is the earlier
open question, and an honest solution is unaffected.

**(3) Repeatability.** Deterministic, apart from time-budgeted solutions under the 8-way
parallelism.

**(4) Honest-play issue.** None found.

**Recommendation: retain, with a note on the memory limit.**

Decisive remaining check: score one greedy output with the pinned `tools/bin/tester` and confirm it
matches the simulator. This would close the "simulator is not the tester" limit.

---

## 10. BipedalWalker (`bipedalwalker_locomotion_rl`)

Task JSON sha256 `48c3ebf72861e30c116494df5258c278454fd503caba16de9adf971c1bc03ecb`. `sebench_eval.py` sha256 `9bb2f8bf…838a`.

**(1) Score definition.**

The two environments score as follows (`:39-48`):

- **Normal:** `clip(R_normal/300) × 100`.
- **Hardcore:** `clip((R_hard+100)/400) × 100`.
- **Combined:** `raw = 0.4·normal + 0.6·hard`.

The task score is `min(30, 2.5·(engineering checks passed, max 4) + 0.2·raw)` (`:122-138`). The
rescale is linear from 0 to 100, so the task score maps to the same number.

Computed with the original functions:

| Case | Normalized |
|---|---|
| Missing checkpoint | 2.5 |
| Loadable but untrained | **10** |
| Solves normal only (300, −100) | 18 |
| **Perfect policy** | **30** |

The cap of 30 is disclosed in `task_prompt.md:117-118`, so it is by design. But the **0-100 range is
reachable only from 0 to 30**, and a third of that comes from passing the loading checks. The upper
anchor of 100 is inconsistent with what any policy can reach.

**(2) Budget.**

- 10 episodes per environment (`EVAL_EPISODES`, `:16-17`; the eval_cmd default is 10) using the first
  10 fixed seeds (`:19-28,75-77`).
- At most about 1,600-2,000 steps per episode gives about 36k steps in total. That takes seconds,
  against 300 s per environment and an `eval_timeout` of 900 s.

**(3) Repeatability.**

- The seeds are fixed (`env.reset(seed=…)`, `evaluate_policy.py:249`).
- The action is deterministic (`:214-223,255`).
- The result is expected to be bit-reproducible on the same build. The 20 accepted earlier episodes
  (zero-policy overlay) are consistent with this.

**(4) Honest-play issue (minor).**

- Every loader path uses `load_state_dict(strict=False)`, and the default path silently drops
  mismatched-shape tensors (`evaluate_policy.py:119,141,188-196`). An honest checkpoint with renamed
  keys (for example a `module.` prefix) would quietly be evaluated as a randomly initialized network
  but still collect the loading bonus. The "Skipping" message is only shown in aggregate feedback.
- The `mean_reward=` regex takes the first match in the child process output (`:114`), which is
  harmless for honest code.

**Recommendation: retain with a note.** The note should state that the normalized range is 0-30, that
10 points come from loadability, and that partial checkpoint loading is silent. Alternatively, repair
the rescale, setting upper to 30 or rescaling raw_loco directly.

Decisive remaining check: none needed for correctness. If a repair is wanted, evaluating one trained
policy confirms the reward-to-score mapping natively.

---

## Summary

| task | score definition | horizon vs budget | repeatability | honest-play scoring issue | recommended disposition | decisive remaining check |
|---|---|---|---|---|---|---|
| anchorhead_text_adventure | final in-game score of best session / 100 (Jericho max) | no horizon; 600 s idle reap undisclosed (no score loss) | deterministic (binding seed 0) | final not peak (doc only); 100/100 not demonstrated (walkthrough 99) | **retain with note** | none for disposition; a 100-point command sequence only removes the note |
| trinity_text_adventure | same / 100 | same | deterministic | none (100/100 observed) | **retain with note** | none |
| tryst_text_adventure | same / 350 | same | deterministic | none (350/350 observed) | **retain with note** | none |
| dcss_dungeon_ai | mean of 5 morgue scores, log1p(raw/400) to 50k | 900 s/game parallel; normal path ≤ ~948 s, worst ≤ ~1008 s vs 1100 s; fits | fixed seeds but wall-clock / CPU dependent; 1.5 s key injection; noise never measured | a single missing morgue voids the whole submission (`valid=ok==total`) despite "mean of 5" wording; 50k anchor unverified | **retain with note** | 2× repeat of one positive bot on fixed ≥5-CPU allocation (+ one half-CPU run) to size noise |
| nethack_dungeon_agent | mean of 20 games' peak `blstats[9]`, linear /1000 | undisclosed 5,000 steps & 120 s/game (~24 ms/step); TLE zeroes whole game; 2,400 s ≤ 3,600 s | **unseeded**: NLE Challenge forbids seeding, exception swallowed → 20 random games, random role | non-reproducible scores; hidden TLE cliff | **retain with note** (or repair evaluator) | default 20-game eval of a simple positive agent, twice: spread of mean + per-step time |
| openttd_transport_ai | mean over *returned* seeds (0-4) of last quarterly company value > 1; log 1e5→1e9 | 540,200 ticks/seed, needs ~150 ticks/s; likely fits 3,600 s (unmeasured); inner timeout = harness timeout | deterministic engine (unmeasured) | mean divides by returned seeds; value ≤ 1 → last positive quarter (minor) | **retain with note** (provisional) | one native 5-seed baseline + simple AI: wall time, ~240 saves/seed, nonzero score |
| wesnoth_tactical_ai | int(80·win_rate + 20·eff), identity rescale | **60 sequential games in 900 s → ≤ 15 s/game incl. start-up**; likely exceeded → invalid | fixed rng-seed; repeats likely redundant | budget (likely unscoreable at defaults); subdir Lua not installed | **pending → withhold original if timing fails; small repair available** | time one original baseline `run_game` in judge image (> ~14 s ⇒ cannot finish) |
| treant_forest | sum of 50 case turns, piecewise anchors | 7 waves×120 s = 840 s vs 870 s (tight); README 60 s → 420 s | deterministic tester; time-budgeted solutions CPU dependent | **anchors unreachable: tester cap Σ2N² = 92,304 → max 21.02/100** (rank1 = 3.58× cap); cap undisclosed; movement semantics still open | **repair rescale anchors** (or note "max 21") | recover anchor provenance (scorer/case set they were computed on) |
| apple_incremental_game | sum of 50 × round(1e5·log2 S), piecewise anchors | 210 s ≤ 600 s | deterministic | none; greedy gets 17.7 (anchors consistent) | **retain** (note 1 GB not enforced) | score one greedy output with pinned tester to confirm simulator parity |
| bipedalwalker_locomotion_rl | min(30, eng bonus + 0.2·raw), linear /100 | ~36k steps vs 2×300 s; fits | fixed seeds, deterministic action | normalized range only 0-30 (10 free for loading); silent `strict=False` partial loads | **retain with note** (or repair upper→30) | none for correctness |

Counts:

- **Task decisions recommended: 10.**
  - Retain or retain-with-note: 8 (Anchorhead, Trinity, Tryst, DCSS, NetHack, OpenTTD, Apple,
    Bipedal).
  - Repair: 1 (Treant rescale).
  - Pending, with withhold-if-check-fails: 1 (Wesnoth).
- **Findings confirmed from source and exact arithmetic: 3.**
  - Treant anchors are unreachable.
  - NetHack seeding is ineffective.
  - Bipedal's normalized ceiling is 30.
- **Conditional findings: 2.**
  - DCSS: one missing morgue invalidates the submission.
  - Wesnoth: the time budget, which is arithmetic plus an unmeasured game time.
- **Local tests actually run: 3.**
  - Original Treant evaluator with the original tester and shipped baseline: 3,418, 50/50 OK.
  - Rerun of the Apple greedy simulator on all 50 cases.
  - Arithmetic script.
- **Repairs written: 0.**

## Limits

- No native game was run here. Every timing claim for Wesnoth, OpenTTD and NetHack is arithmetic
  from source constants plus an engine-speed estimate.
- The NLE and Jericho behavior comes from upstream package sources at the stated versions. The
  installed bytes in the image were not hashed by me. The earlier accepted runtime lock names
  Jericho 3.3.1, and the NLE version is the one the prompt states.
- Wesnoth's emission of the `WINNER:`/`GAME_END_TURN:` markers was not verified against Wesnoth
  source.
- The DCSS 50k, OpenTTD 1e9 and NetHack 1000 upper anchors are untested for reachability.
- The Apple check uses an independent simulator, not the pinned tester.
- The Treant anchors' provenance was not recovered.
