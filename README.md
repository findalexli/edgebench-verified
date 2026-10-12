# EdgeBench Verified

**Version 1.0** · Website: **[lishengzhi.com/edgebench-verified](http://lishengzhi.com/edgebench-verified/)**

[EdgeBench](https://github.com/ByteDance-Seed/EdgeBench) ranks AI agents on hard, open-ended
engineering and science tasks. An agent works on each task for up to 12 hours, and an automatic
grader scores its work from 0 to 100. A ranking is only as trustworthy as those graders.

EdgeBench Verified is an independent check of the grader of every one of the 51 publicly released
EdgeBench tasks. For each task we asked one question: **if an agent does honest, correct work, does
it get the score the task promises?**

## The short answer

For 23 of the 51 tasks, the grader has a problem that changes scores.

| Outcome | Tasks | Meaning |
| --- | ---: | --- |
| **Fixed** | **22** | We publish a fixed version and tested it against the original on the same submissions |
| Kept, with a note | 28 | The grader works as intended; the note records smaller caveats |
| Removed | 1 | No sound fix was possible |
| **Total** | **51** | |

## How EdgeBench scores an agent

1. The agent receives written instructions and starter files.
2. It can submit many times. A hidden grader program runs each submission on hidden test cases
   and produces a raw result, such as a cost, a speed, or the number of tests passed.
3. The raw result is converted to a 0–100 score using reference points the task's authors chose.
4. Each run keeps its best submission. Each model gets three runs per task, and the scores are
   averaged. A model's headline number is the average over tasks.

A grader can therefore go wrong in four places: what it accepts, what it rejects, how it converts
the raw result to 0–100, and which submission it keeps. We found problems in all four.

## What we found

**Correct work is scored too low.**
- *SMT Solver.* The agent builds a solver for logic formulas. The grader checks the solver's
  example answers by how they are written rather than by their value. Correct answers are
  therefore rejected on 27 hidden problems, and a perfect solver's score falls from 78.61 to
  72.40.
- *Borden Inversion.* The agent works out where groundwater pollution came from. The grader's
  hidden physics model uses an unusual convention that the instructions never mention. The same
  honest fit scores 7.0 with textbook physics and 31.2 with the grader's convention.

**Wrong work is accepted.**
- *Exchange Core.* The agent speeds up a stock-exchange matching engine. Two realistic bugs pass
  the correctness check and get full credit: swapping buyer and seller fees, and dropping event
  messages.
- *Jagua Nesting.* The agent packs shapes onto a sheet. The grader accepts layouts in which shapes
  overlap.

**The grader applies a different rule from the one the agent is told.**
- *Triangulation Coloring.* The grader omits a geometric condition the instructions state, and
  the same faulty rule generated the test cases.
- *Warehouse Routing.* The instructions promise 30 seconds per test case. The grader stops after
  60 seconds per group of five cases, so a solution that uses its promised time scores zero.

**The 0–100 scale cannot be reached.**
- *Treant Forest.* The top of the scale lies beyond what the game's own turn limit allows, so no
  submission can score above 21.02.
- *Warehouse Routing.* A machine-checked proof shows the best possible score is about 30.3.

**Small mistakes with large effects.**
- *Order Addition.* An out-of-date checksum in one test makes every submission fail one of five
  tests. The grader then keeps each run's first submission and ignores better later ones.

Every task is listed in [FINDINGS.md](FINDINGS.md), and each has its own page in [cases/](cases/INDEX.md).

## Effect on the published leaderboard

**How much the published leaderboard changes cannot be determined from public data.** Measuring it
would require regrading the agents' original submissions, which EdgeBench has not released, or
rerunning the models on the fixed tasks, which this audit did not do. What can be stated precisely:

- **Outer range.** For 12 fixed tasks only the direction of the effect is known. Letting each take
  its largest possible effect moves a model's average by as much as 9.3 points down or 13.5 up. This
  is a limit, not a prediction.
- **Known maximum.** Fixes with a proved or demonstrated maximum move an average by at most 0.3
  points down or 1.4 up. That alone is enough to swap Opus 4.8 (44.2) and GPT-5.5 (43.1), so the
  public tasks do not establish which of the two is ahead.
- **Lower limit.** Changes of scale convert exactly and raise every average by 1.2–1.9 points. This
  is the certain part, not an estimate of the total; several of the largest effects are among those
  whose size is unknown.

A third party has published one run of Claude Opus 5.5 on 16 of the public tasks, with every
submission. Regrading it confirmed the Order Addition defect in practice: the run kept its first
submission, 3.79, instead of a later 41.24. It also showed that our first Integer Codec fix needed a
new 0–100 scale, because real submissions saturated the old one. Details: [IMPACT.md](IMPACT.md).

## How we checked

Every finding was established on EdgeBench's own grader software, the exact public images the
leaderboard used.

1. **Test submissions.** For each suspected problem we wrote a correct submission, one that
   triggers the problem, and a wrong one, and ran all three through the original grader.
2. **Formal proofs.** Wherever a claim could be stated precisely, we also checked it with **Lean 4**
   (a proof checker that accepts a claim only with a complete proof) or **TLA+** (a model checker that
   explores every state of a bounded model). Each model is tied to the real grader code and has a
   counter-check that must fail.
   - 26 of the 51 tasks have formal results.
   - For 12 of the 22 fixes, the fix itself is proved correct within its model, for example the SMT
     answer checker, the Triangulation flip rule and the Order Addition selection. One more is partly
     proved.
   - The proofs also checked our own work. They showed the first College English fix was narrower
     than published, so it was revised, re-proved and re-tested; and they led to eight wording
     corrections.
   - The rest of the checks use exact arithmetic, a second implementation or exhaustive search.
   Every result and its limits: [evidence/formal/SUMMARY.md](evidence/formal/SUMMARY.md).
3. **Following each problem to the final score.** A problem counts only if it changes the 0–100
   score of honest work. Problems that do not are recorded as notes.
4. **Testing every fix side by side.** The same test submissions were graded by the original and
   the fixed grader. Each fix had to pass three checks:
   - the problem is gone;
   - correct work keeps its score;
   - wrong work is still rejected.
   Each comparison was repeated three times on fresh machines; across 132 graded comparisons, no
   outcome changed.

All formal results rerun with one command (`python3 tools/check_formal.py`). The full method is in
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
| `tasks/`, `sforge/`, `tests/` | EdgeBench's original task definitions and grading software, unchanged |

## Limits

- **Only the 51 public tasks.** EdgeBench has 134 tasks; the other 83 are not released.
- **No AI models were rerun.** Effects are measured with test submissions we wrote. The effect on
  the published leaderboard is calculated where possible and otherwise given as a range.
- **Deliberate cheating is not covered.** A submission written to attack the grader is a separate
  question about how the benchmark isolates its grader.
- **One machine type.** Side-by-side tests ran on machines with 8 virtual CPUs and 8 GiB of memory.
  Speed-based scores may differ elsewhere.
- **Reviewed by AI agents.** Every claim is tied to a saved evidence file and a rerunnable check.
  Agreement between agents is not the same as independent human reproduction.

## Citation and licenses

Cite with [CITATION.cff](CITATION.cff). This is an independent project, not affiliated with
EdgeBench's authors. The grading software derives from ByteDance Seed EdgeBench at
`6e4e5f4aa087a9121aa09a6059e5484e5102c6ff` (Apache-2.0, `LICENSE`). Task definitions come from the
public Hugging Face release at `6cc5a7f1b3288ce52484ad828177b8cc86b05b75` (`tasks/LICENSE`).
EdgeBench's images are referenced by their public fingerprints and are not redistributed.
