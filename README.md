# EdgeBench Verified

**Version 1.1** · Website: **[lishengzhi.com/edgebench-verified](http://lishengzhi.com/edgebench-verified/)**

[EdgeBench](https://github.com/ByteDance-Seed/EdgeBench) ranks AI agents on hard engineering and
science tasks. A hidden checker program scores each agent's work from 0 to 100, so the ranking can
be only as trustworthy as those checkers.

**12 tasks hold up as problems that matter**, out of the 51 public ones: a good-faith solver is scored wrongly or
non-repeatably, and we measured how much on the current `community` judge. Scores are out of 100 unless stated
otherwise.

<!-- confirmed:start -->
| Task | What goes wrong | Measured effect | Upstream |
| --- | --- | --- | --- |
| [Apple Incremental Game](cases/apple_incremental_game.md) | The same eight-at-once pool costs real files points at 4 CPUs and many cases under load. | At true 4 CPUs a real file scores 68.10-70.60, against 73.25-73.92 with a smaller pool, with no timeouts (n=5). In an overload test, five judges sharing 8 CPUs, it scored 3.09-19.78 with the original pool and 17.81-68.87 with the smaller one across three workers (n=20 each). The smaller pool also lost cases on the noisiest worker. | Same mechanism as PR #36; not reported separately. |
| [Arc Compiler Runtime](cases/arc_compiler_runtime.md) | Hidden tests expect an `analyze()` return shape that nothing the agent sees describes. | A real Opus submission scores 61.31 as submitted and 94.81 with only the return shape changed (n=2 each). One real run each: best 61.31 on the original task, 96.06 with the shape documented. | Not yet reported. |
| [Integer Compression Codec](cases/integer_compression_codec.md) | A stored baseline figure is impossible for the documented starter, which distorts how the datasets are weighted. | The starter gets 0.25 raw against the documented 1.0, and 0.855 with the exact figures. A real submission scores 73.60 today; with the figures corrected its raw score is 164.4, which clips to 100 on the existing scale, or gives 51.22 on a new 1..320 scale. So the size of the fix depends on the scale. No ranking change was shown, and real runs reach 73.78 today. | Not yet reported. Choosing a fix means choosing a new scale, which is the maintainers' call. |
| [Juliet Vulnerability Analyzer](cases/juliet_vulnerability_analyzer.md) | Any `.py` or `.sh` file containing the word `infer`, even in a comment, loses 100 points. Separately, CWE-416 findings that start at the release are rejected. | A real analyzer scores 0 and would score 79.59 with the fix; another goes from 90.70 to 0 with one added comment (n=6). CWE-416: a real analyzer loses 3.34, from 89.00 to 85.66 (n=3), though that solver turned the option off and its best score lost nothing. | Reported: issue #39 and PR #35 (the `infer` part). |
| [NetHack Dungeon Agent](cases/nethack_dungeon_agent.md) | Seeding silently fails, so the 20 graded games differ every time. | Our bot scores 6.8-15.5 over 12 gradings, and 14.5 on all 12 once seeding works, all on one day; NetHack also reads the clock, so repeatability across dates is untested. The bot is ours; there is no real submission to test. | Listed in upstream's known issues. |
| [OpenRCT2 Theme Park AI](cases/openrct2_theme_park_ai.md) | The instruction promises about four game years, but the 120 seconds per scenario fit 68 to 69 of 992 game days. | A real plugin scores 27.50 under the official budget (n=3). Direct evaluator runs continued to 992 days score 16.44 (n=2), so for this plugin the short run inflates the score. No judge fix was tested. Real files also vary between gradings, up to 11.40-44.73, but randomness in the plugins may cause that, so we don't count it against the judge. | The short run is listed in upstream's known issues; issue #12 raises a separate question about this task's scale. |
| [Rust Multicrate Reconstruction](cases/rust_multicrate_reconstruction.md) | Four source files are missing, which blocks nine scored crates. | At 8 vCPUs, restoring the files raises a real submission from 17.20 to 27.17 and a reference we rebuilt from upstream code from 27.61 to 73.99 (n=2). Original-judge scores matched 4-CPU results, but the restored arm wasn't run at 4 CPUs. Two crates still fail because of separate hidden-test defects. The starter also rises, from 1.47 to 3.82, so old scores don't carry over. | Listed in upstream's known issues. |
| [Schemathesis Datagen Pipeline](cases/schemathesis_datagen_pipeline.md) | The hidden header test imports names and expects format keys that `TODO.md` never gives, so every real `headers` module scores 0 of 15 on it. | Once those are supplied, a real submission goes from 72.31 to 85.64 or 86.67; the two values come from a flaky test. The 8 real modules are 2 distinct versions. | Not yet reported. |
| [SMT Solver](cases/smt_solver.md) | The validator's recursion crashes on 5 hard files when a solver answers `sat`; no score file gets written, and the judge still reports a valid 0. | A real solver scores 0.00 on the shipped judge and 47.04 and 46.17 with a larger validator stack. The 5 crashing answers still fail validation; preventing the crash restores credit earned on other cases. Measured at 8 CPUs and 7 GB, not the official 16 and 16 GB, with 6 to 7 solver OOM kills per run. No real run shows it. | Not yet reported. |
| [Treant Forest](cases/treant_forest.md) | The tester stops each game at an undocumented turn cap, so no submission can pass 21.02, while the 0-100 scale assumes totals the cap rules out. | All 87 archived real reports sit at 20.46-21.02, so the cap hides real differences between them. Removing the cap with the scale unchanged raises one real submission by 15.83 and reorders the ones we tested, though some long replays hit the tester's time limit. The four real submissions we measured read a destination list the README says solutions don't use; a grid-only control scores 3.04 with or without the cap. | Listed in upstream's known issues. Whether to change the cap, the scale or both is the maintainers' call. |
| [Vibrating Path Graph Coloring](cases/vibrating_path_graph_coloring.md) | Eight cases run at once on the official 4 CPUs, and one timeout makes the whole total `inf`. | A real Opus solver gets `inf` on all 15 gradings and 19.77-19.98 with 4 cases at once. The same file passed all 7 grades during its own run on the published judge image, so the grading is non-repeatable. | Reported: issue #40 and PR #36. |
| [Wesnoth Tactical AI](cases/wesnoth_tactical_ai.md) | The same file gets different scores despite fixed seeds. | Wesnoth's stock AI scores 36 to 43 over 8 gradings with no timeouts. We haven't found the cause, and there is no real submission to test. | Listed in upstream's known issues. |
<!-- confirmed:end -->

## How we reviewed

1. **Attack.** An independent model (GPT-6 Astra) reviewed 146 claims in the current code, rechecked 48 from scratch and attacked 46, trying to refute them. It ran pure functions but no containers.
2. **Measure.** Where we could, we built the judge from `community` at `1187e2c` and graded a control and a trigger differing only at the defect, repeated at least twice; repeatability claims used at least three gradings of one file. Other evidence includes single agent runs, direct evaluator runs, local scoring tests and calculations, and each result says which.
3. **Check against real runs.** A claim counts for less if real solvers score well despite it. On
   Borden Inversion, a claim the reviewer accepted fell this way: a real run reached raw 108.97 of 109.

**How a task qualifies.** A task is confirmed when the measured change reaches real work: regrading a real submission shows it, or a repeatability failure affects any submission. A defect that is large only on a trigger no real submission we hold uses stays with the others. Graph Node, for example, drops from 90.52-90.57 to 1.95-2.01 if predictions use integer keys, which the task permits.

**A correction.** Our first audit reported problems in 32 of the 51 tasks. Of those 32, 10 are confirmed, 13 are real but small or unseen, 1 has changed upstream and 8 are not confirmed. The other 2 confirmed
tasks are ones the first audit kept with a note. [FINDINGS.md](FINDINGS.md) lists the other 39 tasks and why each is there, and
[first-audit/](first-audit/README.md) keeps that audit's documents. Its leaderboard estimate counts fixes this
review did not confirm, and we have not recomputed it.

## What we have reported upstream

- [#39](https://github.com/ByteDance-Seed/EdgeBench/issues/39) and [#35](https://github.com/ByteDance-Seed/EdgeBench/pull/35): Juliet, the word `infer`.
- [#40](https://github.com/ByteDance-Seed/EdgeBench/issues/40) and [#36](https://github.com/ByteDance-Seed/EdgeBench/pull/36): Vibrating Path, eight cases on four CPUs.
- Drafts: [#37](https://github.com/ByteDance-Seed/EdgeBench/pull/37) Graph Node and [#38](https://github.com/ByteDance-Seed/EdgeBench/pull/38) Warehouse Routing.

## What is in this repository

| Path | Contents |
| --- | --- |
| [FINDINGS.md](FINDINGS.md) | The confirmed tasks, then the other 39 and why each is there |
| [cases/](cases/INDEX.md) | One page per task |
| [METHOD.md](METHOD.md) | How findings were established, and the limits |
| [data/](data/README.md) | Each task's status, with the measured effect, and every side-by-side test |
| `evidence/` | Verdicts, scripts, Lean and TLA+ files, and logs. [What reproduces from this repository](evidence/reviews/second-review/README.md) |
| [first-audit/](first-audit/README.md), `repairs/` | The first audit's documents and fix packages |
| `site/`, `tools/` | The website and the scripts that generate it |
| `tasks/`, `sforge/` | EdgeBench's original task definitions and grading software, byte for byte |

## Limits

- The audit covers only the 51 public tasks. EdgeBench has 134 tasks; the other 83 are not released.
- Most tasks have one model's real runs, or none. Where no real submission exists we say so, and the
  witness is ours.
- The SMT results ran at 8 CPUs and 7 GB, not the official 16 and 16 GB. Lean Analysis and PFR were not
  rerun.
- Deliberate cheating is not covered. A submission written to attack the grader raises a separate
  question, about how the benchmark isolates its grader.
- Most side-by-side tests ran on E2B cloud sandboxes with 8 virtual CPUs and 8 GiB of memory. Lean
  Analysis ran on a local host with 16 CPUs and 15 GB. The grader's CPU limit ranged from 1 to 8
  CPUs, as each case page states. Speed-based scores may differ on other machines.
- AI agents did most of this review, and agreement between agents is not independent human reproduction.
  Volunteers have begun checking findings by hand; PFR Formalization, outside the 12, has a recorded human pass.

## Citation and licenses

Cite with [CITATION.cff](CITATION.cff). This is an independent project, not affiliated with
EdgeBench's authors. The grading software derives from ByteDance Seed EdgeBench at
`6e4e5f4aa087a9121aa09a6059e5484e5102c6ff` (Apache-2.0, `LICENSE`). Task definitions come from the
public Hugging Face release at `6cc5a7f1b3288ce52484ad828177b8cc86b05b75` (`tasks/LICENSE`).
EdgeBench's images are referenced by their public fingerprints and are not redistributed.
