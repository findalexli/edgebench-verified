# EdgeBench Verified

**Version 1.0** · Website: **[lishengzhi.com/edgebench-verified](http://lishengzhi.com/edgebench-verified/)**

[EdgeBench](https://github.com/ByteDance-Seed/EdgeBench) ranks AI agents on hard, open-ended
engineering and science tasks. An agent works on each task for up to 12 hours, and an automatic
grader scores its work from 0 to 100. A ranking is only as trustworthy as those graders.

EdgeBench Verified is an independent check of the grader of every one of the 51 publicly released
EdgeBench tasks. For each task we asked one question: **if an agent does honest, correct work, does
it get the score the task promises?**

## The short answer

EdgeBench ranks AI agents on 51 public engineering and science tasks. In each task an agent works
for hours, and a hidden checker program (EdgeBench calls it the grader) scores what it submits, from
0 to 100. We tested each checker the way you would test any program: we gave it correct work, broken
work and work that follows the instructions to the letter. **In 32 of the 51 tasks the checker
scored some submissions wrongly.** It gave correct solutions zero because of time limits stricter
than promised. It rejected correct answers. It gave full credit to broken programs. It enforced rules
the instructions never stated. On one score scale, no submission could score above 21. We published
fixes for 31 of these tasks and removed one. We checked the fixes by grading the same submissions
with the original and the fixed checker side by side. Where a public agent run was available, we
regraded its submissions too: in one task the run's score moves from 3.8 to 41.2 out of 100. The
published averages are not enough to recompute the leaderboard. They are, however, enough to show
that **its top two places can no longer be confirmed.**

| Outcome | Tasks | Meaning |
| --- | ---: | --- |
| **Fixed** | **31** | The checker's logic, data or setup can be corrected; each fix is published as a new version of the task. Some fixes still have an open integration step, listed in [APPLYING-FIXES.md](APPLYING-FIXES.md) |
| Kept, with a note | 19 | No correctable problem found. The note records caveats that no change to the checker removes, such as variation between runs or machines. These are not always small: in ANN Vector Search the measured speed varies between gradings on one machine type by about ±7 of 100 points per grading |
| Removed | 1 | No sound fix was possible |
| **Total** | **51** | |

In numbers:

- **Real agent run.** Of the 9 fixed tasks in one public four-hour run of Claude Opus 5.5, 7 could
  be regraded with both checkers. The run's score changed in 2 (Order Addition 3.79 → 41.24,
  Integer Codec 75.72 → 53.95, out of 100), single submissions changed in 2 more (Juliet, by up to
  25.26 points; Molecular Assembly, by up to 12.22), and the problem never occurred in 3.
- **Leaderboard.** Opus 4.8 leads GPT-5.5 by 1.1 points on the published leaderboard (44.2 against
  43.1). With the per-task limits we documented, their ranges are 45.49–47.30 and 44.30–46.35. These
  overlap, so the public data can no longer confirm which is ahead; this does not show that they
  change places. Details in [IMPACT.md](IMPACT.md).

What each fix has been tested on differs from task to task. Remaining gates: FFmpeg's submission-build
path; Warehouse's backend integration of the final-drain repair; Lean Analysis's image builds and
actual grading path (its grader image needs about 45 GB of disk and was not rebuilt on a clean
machine); PFR's credit on the five actual targets, which needs real proofs; Equivalence's
per-problem checks on all six problems; and Vibrating Path's zero-hit formatting effect, unresolved
on 13 of 50 cases. [APPLYING-FIXES.md](APPLYING-FIXES.md) gives the per-package evidence and
remaining requirements.

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
the machine it runs on. We found problems in all five, and group them below into four categories.

## What we found

Every task with a problem, the 31 fixed tasks and the removed one, has one primary category, set by the
mechanism of its main defect, and may have secondary ones. The four categories:

| Category | Tasks (primary) | In short |
| --- | ---: | --- |
| Engineering and runtime environment | 5 | The checker does not run correctly in the real setup |
| Grader correctness and factual errors | 15 | The checker marks wrong work as right, or right work as wrong |
| Instruction–grader mismatch | 9 | The checker enforces something the instructions do not state, or contradicts them |
| Scoring scale and selection | 3 | The 0–100 scale cannot be reached, a reference point is wrong, or the wrong submission is kept |
| **Total** | **32** | |

Fourteen examples follow, three or four per category; the website shows each with a figure. A task
can appear under a secondary category too.

### 1. Engineering and runtime environment (5 tasks)

The checker's scoring rules may be right, but it does not run correctly in the setting where it is actually used. Typical causes: test cases run at once on fewer CPUs than they need, so honest solutions time out; hidden tests are inserted where they do not compile; files the checker needs are missing from the published images; a test run stops at its first failure and counts the rest as failed; or a result depends on timing. Honest work then loses points for reasons that have nothing to do with its quality.

- *Rust Multicrate: hidden tests that cannot compile.* The agent rebuilds a 14-package Rust project
  and is told not to edit the tests. The checker inserts its hidden tests into two packages, search
  (12 points) and the command-line program (10 points), where they do not compile, so both packages,
  22 of the 100 points, score 0 for every solver who leaves the tests and settings unchanged. A
  complete, correct solution scores 73.99 out of 100 with the original checker and 94.70 with the
  fixed one, a gain of 20.71: search +11.29, the command-line program +9.32, and a test the original
  skipped after an earlier failure +0.10. (A solver could still make search compile by turning on its
  `parallel` setting, which edits no test; nothing in the task points to it.)
- *Grid Robot: eight test cases share four CPUs.* The instructions promise 30 seconds per test case.
  The checker runs eight cases at once, and EdgeBench's official settings give it 4 CPUs
  ([evidence/impact/edgebench-leaderboard-config.md](evidence/impact/edgebench-leaderboard-config.md)),
  so each case gets about half a CPU. An honest solution that computes for 16 seconds per case times
  out on 48 of 50 cases, and one timeout throws out the whole submission; with the fix it scores its
  19.80 out of 100. Five more tasks share this problem: Vibrating Path, Molecular Assembly, Apple
  Game, Triangulation and Warehouse Routing. In a real agent run on Molecular Assembly, single
  submissions rose by up to 12.22 points out of 100 under the fix. The fixes run no more cases at
  once than the checker has CPUs.

### 2. Grader correctness and factual errors (15 tasks)

The task asks for the right thing, but the checker checks it wrongly: it marks wrong work as right, or right work as wrong. Examples: a correctness check that misses real bugs, a validator that misses overlapping shapes, a cost check that leaves out one term, a supplied library that miscalculates, an answer checker that misreads valid answers, a statement to be proved that is false as written, or points taken from numbers the submission reports about itself. Where a wrong submission is accepted, it can score as high as a correct one, or higher.

- *Exchange Core: a broken stock exchange passes.* The agent makes a matching engine faster without
  changing what it does. The checker only confirms that money balances overall, so two realistic
  one-line bugs, a wrong seller fee and trade messages never delivered, are scored as correct, on
  speed (7.77–24.40 and 4.71–15.62 out of 100 over four runs, within the correct engine's speed
  noise). The fixed checker requires the project's own tests, which catch both, and gives them 0.
- *College English: an empty grading report scores 100.* An AI model grades the agent's exam papers
  against 12 rules. If its answer leaves a rule out, the checker gives that rule full marks and still
  calls the result valid, so a report that assesses nothing scores 100 out of 100. The fixed checker
  asks again and otherwise reports a grading failure. How often this happened in real gradings is
  not known.
- *SMT Solver: correct answers rejected.* The checker looks up a value by how it is written, not by
  what it stands for, so 27 hidden puzzles cannot be won and a perfect solver's maximum falls from
  78.61 to 72.40 out of 100. On 42 more it rejects answers written the way the instructions
  describe; the fixed checker accepts correct answers on all 69.
- *FFmpeg Swscale: code that fails instantly earns speed credit.* The speed tests never check the
  output, so a call that fails or does nothing "finishes" almost instantly; unfinished code earned
  up to 18.93 out of 100 under the original checker. The fixed checker checks the output of every
  timed call, and any failed workload makes the total exactly 0.
- *D-ABIC Gravity Inversion (removed).* About 42 of the 100 points (two parts, worth 12 and 30) come
  from the submission's own results file and are never verified. A sound fix would need the checker
  to recompute them from hidden data, so the task was removed.

### 3. Instruction–grader mismatch (9 tasks)

Each rule the checker applies may be reasonable on its own, but it is not the rule the agent was given. The checker enforces something the instructions do not state, or contradicts what they say: a shorter time limit than promised, a geometric condition left out, an undocumented output format or convention, checks the instructions never mention, a function that does not exist, a different formula. An agent that follows the instructions faithfully is then scored by a different rule.

- *Warehouse Routing: promised 150 seconds, cut off at 60.* The instructions promise 30 seconds per
  test case, 150 seconds per input of five cases. The checker stops each input after 60 seconds, and
  one timeout throws out the whole submission, so a test solution taking 13 seconds per case gets no
  score; with the fix all 50 inputs are scored. One part of the fix (counting results that arrive at
  the very end) is tested on its own but not yet in a full EdgeBench run. Separately, a bound proved
  in Lean shows that no valid answer can score above about 30.6 out of 100; that limit is
  documented, not changed.
- *Arc Compiler: the same code scores 69 or 36.* Hidden tests worth 33.67 of 100 points expect error
  reports in a format that nothing the agent sees describes; the same honest code scores 69.26 in that
  format and 35.59 in the starter's. The fixed task documents the format.
- *Juliet Analyzer: the public examples teach the wrong format.* For command-injection bugs, all 38
  public examples mark the start of the bug at the line that runs the command, while all 120 hidden
  answers mark the line that reads the input, and the original checker accepts only the hidden form.
  An analyzer that follows the public examples loses 15.00 points (45.66 instead of 60.66), and up to
  26.47 in the worst case (computed exactly, not run). In a real agent run, 14 of 105 submissions were
  affected, one by 25.26 points (70.00 against 95.26). The fixed checker accepts both forms.
- *Borden Inversion: the checker's physics is not the textbook's.* The checker predicts well readings
  with a physics model whose conventions the instructions never state. An honest textbook fit scores
  7.03 and the same fit with the checker's conventions 31.2 (raw, on this task's 0–109 range); in a real
  agent run (read, not regraded) the best score climbed from 7.01 to 60.10 over 36 submissions while
  the checker reported its error on the hidden wells after each one. The fixed task gives agents the
  checker's model.

### 4. Scoring scale and selection (3 tasks)

The raw result is computed correctly, but the step that turns it into the final score goes wrong. The reference points that convert the raw result to 0–100 cannot be reached or were measured on something else, so scores are compressed or shifted; or the rule that picks each run's best submission keeps the wrong one.

- *Order Addition: later, better work never counts.* One of five tests compares a helper file
  against an outdated fingerprint, so every submission fails it. Each run picks its best submission
  by tests passed first, so it stays on its first valid submission. In a real agent run this kept
  3.79 out of 100 instead of the 41.24 a later submission earned.
- *Treant Forest: no submission can score above 21.* The checker stops each game after a fixed number
  of turns, so no total can exceed 92,304, but the 0–100 scale was set as if 330,195 were possible:
  even a perfect submission would score 21.02. The fixed scale ends at the most the checker allows
  (whether any submission can reach it is not shown); an honest test solution moves from 3.04 to
  16.36.
- *Integer Codec: an impossible reference number.* The checker compares submissions with stored
  results for the starter code; one claims 5.13 bits per number, below the 8-bit minimum for the
  starter's format (the starter needs 38.98), so the starter scores about 0.24 instead of the
  documented 1.0. The fix measures the starter in the same run and sets a new 0–100 scale, which
  moves a real agent run from 75.72 to 53.95: fixes can lower scores as well as raise them.

Other fixed tasks, including Jagua Nesting, PFR Formalization, Triangulation Coloring and Git in Zig,
are listed in [FINDINGS.md](FINDINGS.md) and have their own pages.

Every task is listed in [FINDINGS.md](FINDINGS.md), and each has its own page in [cases/](cases/INDEX.md).

## Effect on the published leaderboard

**How much the published leaderboard changes cannot be determined from public data.** Measuring it
would require rerunning the models on the fixed tasks, which this audit did not do, or, for fixes to
the grader alone, regrading the agents' original submissions, which EdgeBench has not released. What
can be stated precisely, assuming no fix turns a failed run into a scored one or the reverse:

- **Conditional intervals.** [IMPACT.md](IMPACT.md) and [data/impact.csv](data/impact.csv) include public-score rounding, Treant's piecewise scale, and stated assumptions about which runs remain valid. Interval midpoints are descriptive, not identified corrected means.
- **Scope of bounds.** Component-level limits apply only to the named defects. Portfolio's 0.3921-point upper estimate belongs to its restricted numerical sweep and is excluded from the global bounded-effects calculation.
- **Ranking.** Overlapping intervals mean the available evidence does not certify an ordering. They do not establish that any attainable submissions reverse that ordering. The documented-limit intervals separate GPT-5.5, GPT-5.4, GLM-5.1 and DS-V4-Pro only if the 19 direction-only fixes have no effect, because those intervals count them as zero; in the full-domain envelope every neighbouring pair overlaps, so no order is certified.

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
