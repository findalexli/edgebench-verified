# EdgeBench Verified

**Version 1.0** · Website: **[lishengzhi.com/edgebench-verified](http://lishengzhi.com/edgebench-verified/)**

[EdgeBench](https://github.com/ByteDance-Seed/EdgeBench) ranks AI agents on hard, open-ended
engineering and science tasks. An agent works on each task for up to 12 hours, and an automatic
grader scores its work from 0 to 100. A ranking is only as trustworthy as those graders.

EdgeBench Verified is an independent check of the grader of every one of the 51 publicly released
EdgeBench tasks. For each task we asked one question: **if an agent does honest, correct work, does
it get the score the task promises?**

## The short answer

For 32 of the 51 tasks, the grader has a problem that changes scores and that a change to the
grader or the task can correct.

| Outcome | Tasks | Meaning |
| --- | ---: | --- |
| **Fixed** | **31** | Historical repair disposition: versioned patches with task-specific evidence. This count is not 31 fully validated releases; current integration limits are listed below and in APPLYING-FIXES.md |
| Kept, with a note | 19 | No correctable problem found. The note records caveats that no change to the grader removes, such as variation between runs or machines. These are not always small: in ANN Vector Search the measured speed varies between gradings on one machine by about ±7 of 100 points per grading |
| Removed | 1 | No sound fix was possible |
| **Total** | **51** | |

The repair count describes task dispositions, not 31 fully certified releases. Current evidence has different scopes. Datagen's year-domain correction passes paired native evaluator controls. FFmpeg's per-call output checks and exact-zero failure rule pass paired native scorer controls. CTA now checks overseas CNY exposure against fund NAV and passes paired native runs through the original scoring command. Warehouse requires a separate host-side drain repair so late evaluations are included or the run fails visibly. A clean-machine rebuild of every package as committed at 83181b7f passed for 31 of 32 packages; Lean Analysis could not be rebuilt, because its grader image needs about 45 GB of disk ([evidence/runs/materialize-check-summary](evidence/runs/materialize-check-summary/README.md)). Remaining gates: FFmpeg's submission-build path; Warehouse's backend integration of the drain repair; Lean Analysis's image builds and actual grading path; PFR's credit on the five actual targets, which needs real proofs; Equivalence's per-problem checks on all six problems; and Vibrating Path's zero-hit formatting effect, unresolved on 13 of 50 cases. Triangulation's regenerated inputs now cover their convex hull exactly (v2.2). [APPLYING-FIXES.md](APPLYING-FIXES.md) gives the per-package evidence and remaining requirements.

The impact analysis uses intervals for Treant Forest because published averages do not identify individual clipped scores. Portfolio Risk's restricted numerical sweep is a sensitivity scenario, not a global bound. Formal models cover specified mechanisms and assumptions; historical proof results do not certify revised implementations.

## How EdgeBench scores an agent

1. The agent receives written instructions and starter files.
2. It can submit many times. A hidden grader program runs each submission on hidden test cases
   and produces a raw result, such as a cost, a speed, or the number of tests passed.
3. The raw result is converted to a 0–100 score using reference points the task's authors chose.
4. Each run keeps its best submission. Each model gets three runs per task, and the scores of the
   valid runs are averaged (a run that failed as a whole, for example by crashing, is dropped). A
   model's headline number is the average over tasks.

A grader can therefore go wrong in four places in its code: what it accepts, what it rejects, how
it converts the raw result to 0–100, and which submission it keeps. A fifth lies outside its code:
the machine it runs on. We found problems in all five.

## What we found

**The grader is given fewer CPUs than it runs work on.** EdgeBench's official leaderboard settings
give each grader 4 CPUs unless the task overrides it
([evidence/impact/edgebench-leaderboard-config.md](evidence/impact/edgebench-leaderboard-config.md)).
Six graders that have no override run 8 test cases at once under the promised time limit per case,
so each case gets about half a CPU. (Treant Forest also runs 8 at once, but its limit is twice the
promised time.) The instructions never state the grader's CPU count; a wall-clock limit alone does not promise dedicated CPU seconds. These repairs choose a more consistent resource policy.
- *Grid Robot* and *Vibrating Path.* The instructions promise 30 seconds per test case. A solution
  that computes for 16 seconds per case (Grid) or 20 seconds (Vibrating) times out on 48 of 50
  cases at 4 CPUs, and one
  timeout voids the whole submission. With 8 CPUs it passes every case.
- *Molecular Assembly, Apple Game, Triangulation, Warehouse Routing.* The same mechanism: CPU-budgeted
  solutions lose most cases, or the whole score, at 4 CPUs. The fixes run no
  more cases at once than the grader has CPUs.
- SMT Solver runs 16 solver processes at once, but the settings give its grader 16 CPUs, so the
  problem does not arise there.

**Correct work is scored too low.**
- *Rust Multicrate.* The grader inserts hidden tests into two parts of the project in a way that
  does not compile, so those parts (22 of 100 points) score 0 for every agent that follows the rule
  not to edit tests. A complete solution scores 73.99 instead of 94.70 in the publisher's grading
  environment. That environment is inferred: with four missing library files restored, the public
  image reproduces the publisher's recorded starter score exactly.
- *Git in Zig.* Undisclosed checks set the score to 0 when an agent leaves an ordinary build file in
  its project or writes a test that compares its output with the real git, which the instructions
  invite.
- *PFR Formalization.* Five of the 423 statements to prove contain a gap marker (Lean's `sorry`)
  hidden inside the statement itself, so no agent can earn them. They are worth 1.18 of the 100
  points, and up to 2.13 with the later proofs that use them (inferred). Only an agent that would
  have proved them loses anything.
- *SMT Solver.* The agent builds a solver for logic formulas. The grader checks the solver's
  example answers by how they are written rather than by their value. Correct answers are
  therefore rejected on 27 hidden problems, and a perfect solver's score falls from 78.61 to
  72.40.
- *Borden Inversion.* The agent works out where groundwater pollution came from. The grader's
  hidden physics model uses an unusual convention; the documentation gives its ingredients but not
  how they combine. The same one-shot honest fit scores 7.0 with textbook physics and 31.2 with the
  grader's convention, though an agent iterating on the grader's feedback reached 60.10.
- *Juliet Analyzer.* For command-injection bugs, all 38 public example answers start the trace at
  the dangerous call, while all 120 hidden answers start at the line that reads the input, and the
  original grader accepts only the hidden form. An analyzer that follows the public examples loses
  15.00 points if it finds only those bugs (45.66 instead of 60.66), and up to 26.47 points in the
  worst case (computed exactly from the grader's formula, not run).

**Wrong work is accepted.**
- *Exchange Core.* The agent speeds up a stock-exchange matching engine. Two realistic bugs pass
  the correctness check and get full credit: charging selling takers the maker fee instead of the
  taker fee, and not delivering trade messages.
- *Jagua Nesting.* The agent packs shapes onto a sheet. The grader accepts layouts in which shapes
  overlap.

**The grader applies a rule the instructions do not state.**
- *Triangulation Coloring.* The grader omits a geometric condition the instructions state, and
  the same faulty rule generated the test cases.
- *Warehouse Routing.* The instructions promise 30 seconds per test case. The grader stops after
  60 seconds per group of five cases, so a solution that uses its promised time scores zero.
- *Portfolio Risk.* The instructions define excess return as the difference of two yearly returns;
  the grader converts the difference of the two period returns to a yearly figure instead. The
  restricted decimal sweep gives a sensitivity envelope of 0.3921 points up or 0.10 down; this is not a global bound.

**The 0–100 scale cannot be reached.**
- *Treant Forest.* The top of the scale lies beyond what the game's own turn limit allows, so no
  submission can score above 21.02.
- *Warehouse Routing.* A lower bound proved in Lean shows that no valid answer can score above about
  30.6 (30.3 at the exact bound).

**Small mistakes with large effects.**
- *Order Addition.* An out-of-date checksum in one test makes every submission fail one of five
  tests. Under the task's rule for picking a run's best (most tests passed first), each run then
  keeps its first valid submission and ignores better later ones.

Every task is listed in [FINDINGS.md](FINDINGS.md), and each has its own page in [cases/](cases/INDEX.md).

## Effect on the published leaderboard

**How much the published leaderboard changes cannot be determined from public data.** Measuring it
would require rerunning the models on the fixed tasks, which this audit did not do, or, for fixes to
the grader alone, regrading the agents' original submissions, which EdgeBench has not released. What
can be stated precisely, assuming no fix turns a failed run into a scored one or the reverse:

- **Conditional intervals.** [IMPACT.md](IMPACT.md) and [data/impact.csv](data/impact.csv) include public-score rounding, Treant's piecewise scale, and stated assumptions about which runs remain valid. Interval midpoints are descriptive, not identified corrected means.
- **Scope of bounds.** Component-level limits apply only to the named defects. Portfolio's 0.3921-point upper estimate belongs to its restricted numerical sweep and is excluded from the global bounded-effects calculation.
- **Ranking.** Overlapping intervals mean the available evidence does not certify an ordering. They do not establish that any attainable submissions reverse that ordering.

A third party has published one run of Claude Opus 5.5 on 16 of the public tasks, with every
submission. Nine of those tasks are ones we fixed. Where a fix changes only the grader, we regraded
the run's saved submissions with both graders: 7 tasks, 314 submissions (349 paired gradings with
repeats). Where a fix changes what the agent sees, regrading old answers would measure nothing,
because the agent would have worked differently; that rules out Borden Inversion. Lean Analysis was
not run, because its grader needs more memory than our machines have; its effect was computed
instead (96.86 → 98.42). Order Addition changes the most: the original grader kept the run's first
agent submission, 3.79, while the fixed grader keeps a later one, 41.24. Integer Codec scores 1.7–4×
higher in raw terms (about 50–54 on the fixed scale, against 75.72 on the old one). On Juliet, the
agent's early submissions lost up to 25 points but its best did not. Tree Block, Graph Node and
Schemathesis show no sign of their defects in this run, and Molecular stays at the top of its scale.
This is one model and one four-hour run per task, so it shows the problems occur in practice but
cannot measure the leaderboard effect. Details: [IMPACT.md](IMPACT.md),
`evidence/runs/opus55-regrade2-summary/`.

## How we checked

Evidence ranges from source inspection and original-helper controls to full native grader runs. Each case states its level; component controls and formal models do not establish complete image integration. Some score effects are computed or inferred rather than measured.

1. **Test submissions.** Where available, we ran correct, triggering and wrong submissions
   through the original grading path. Case pages distinguish full native runs from
   original-helper controls and source arguments.
2. **Formal checks.** Wherever a claim could be stated precisely, we also checked it with **Lean 4**
   (a proof assistant that accepts a claim only with a complete proof) or **TLA+** (a model checker
   that explores every state of a bounded model). Each model is tied to the real grader code and
   has a counter-check that must fail.
   - 26 of the 51 tasks have formal results.
   - The saved inventory classifies 10 repair models as proved or exhaustively model-checked
     within their assumptions, including the modeled SMT answer checker, Triangulation flip rule
     and Order Addition selection. Four more are partly proved. These historical results do not
     certify current repair packages; CPU limits are checked by runs, not formally.
   - The formal checks also corrected our own work: the first College English fix was narrower than
     published, so it was revised, re-proved and re-tested, and eight statements were corrected
     ([evidence/formal/CORRECTIONS.md](evidence/formal/CORRECTIONS.md)).
   - Other checks use exact arithmetic, a second implementation or exhaustive search.
   Every result and its limits: [evidence/formal/SUMMARY.md](evidence/formal/SUMMARY.md).
3. **Following each problem to the final score.** A problem counts only if it changes the 0–100
   score of honest work; problems that change no score are recorded as notes.
4. **Historical paired checks.** Original and repaired components or graders were compared on the same inputs. The intended acceptance checks were:
   - the problem is gone;
   - correct work keeps its score;
   - wrong work is still rejected.
   Most comparisons were run three times. Across 254 graded comparisons (30 fixed tasks and the
   removed task's partial fix; 240 of them run three times; 2 setup runs that prepare inputs are not
   counted), one outcome changed, under the original grader: at 4 CPUs, Vibrating Path's valid deadline-based test submission timed out on 14 cases in one of its nine original-grader gradings, the timing problem the fix removes. No fixed-grader outcome changed. Exceptions: OpenRCT2's fix changes only its instructions and has nothing to run; Lean Analysis repeats ran locally rather than on fresh machines; Integer Codec's final 0–100 scale was applied to the recorded raw results; the revised College English grader was itself run three times; and 14 comparisons ran once: the Rust starter's fixed-version score (each run takes about 40 minutes and nearly fills the machine's disk), the CTA v2.1 standard answer, the six Exchange Core rows at 4 CPUs (one row per run of a three-run job), and the three controls each of Datagen v2.1 and FFmpeg v2.2 (single runs).

The formal runner (`python3 tools/check_formal.py`) reruns supported checks when the required tools are installed; its regression tests validate result parsing separately from recompiling proofs. The full method is in
[METHOD.md](METHOD.md).

## Using the fixed tasks

Each fix is a small patch plus a script that rebuilds the fixed task from the original public
images. No original files are redistributed. Scores from a fixed task should not be mixed with
scores from the original. See [APPLYING-FIXES.md](APPLYING-FIXES.md).

## What is in this repository

| Path | Contents |
| --- | --- |
| [FINDINGS.md](FINDINGS.md) | Every task, grouped by what goes wrong |
| [cases/](cases/INDEX.md) | One page per task: the task, the problem, how much it matters, the fix, how it was checked |
| [IMPACT.md](IMPACT.md) | Effect on the published leaderboard |
| [METHOD.md](METHOD.md) | How findings were established, and the limits |
| [APPLYING-FIXES.md](APPLYING-FIXES.md) | How to build and use the fixed tasks |
| [DECISIONS.md](DECISIONS.md) | The outcome for every task |
| [data/](data/README.md) | Machine-readable outcomes, every side-by-side test and its three repeats, and the leaderboard estimate |
| `repairs/<task>-v2/` | The fixed tasks ("v2" marks the fixed version) |
| `evidence/` | Detailed reviews, scripts, Lean and TLA+ files, and the logs of every test run |
| `site/` | The website |
| `tools/` | Scripts that generate the tables, site and checks |
| `tasks/`, `sforge/` | EdgeBench's original task definitions (Hugging Face ByteDance-Seed/EdgeBench `6cc5a7f`) and grading software (GitHub `6e4e5f4`), byte for byte; hashes in `sforge/UPSTREAM.lock`, checked by `tools/check_upstream.py` |
| `tools/harness_compat/` | The earlier audit's stricter grading patch, kept as a record; not EdgeBench's behaviour and not used for any result |

## Limits

- **Only the 51 public tasks.** EdgeBench has 134 tasks; the other 83 are not released.
- **No AI models were rerun.** Effects are measured with test submissions we wrote. The effect on
  the published leaderboard is calculated where possible and otherwise given as a range.
- **Deliberate cheating is not covered.** A submission written to attack the grader is a separate
  question about how the benchmark isolates its grader.
- **Machines.** Most side-by-side tests ran on E2B cloud sandboxes with 8 virtual CPUs and 8 GiB of
  memory. Lean Analysis ran on a local host with 16 CPUs and 15 GB. The grader's CPU limit ranged
  from 1 to 8 CPUs, as each case page states. Speed-based scores may differ elsewhere.
- **Reviewed by AI agents.** Every claim is tied to a saved evidence file and a rerunnable check.
  Agreement between agents is not the same as independent human reproduction.

## Citation and licenses

Cite with [CITATION.cff](CITATION.cff). This is an independent project, not affiliated with
EdgeBench's authors. The grading software derives from ByteDance Seed EdgeBench at
`6e4e5f4aa087a9121aa09a6059e5484e5102c6ff` (Apache-2.0, `LICENSE`). Task definitions come from the
public Hugging Face release at `6cc5a7f1b3288ce52484ad828177b8cc86b05b75` (`tasks/LICENSE`).
EdgeBench's images are referenced by their public fingerprints and are not redistributed.
