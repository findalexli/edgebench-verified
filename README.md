# EdgeBench Verified

**Version 1.0.** A verified edition of the 51 publicly released
[EdgeBench](https://github.com/ByteDance-Seed/EdgeBench) tasks.

A benchmark task is only as good as its evaluator: if the evaluator applies a different rule from
the one the solver is told, accepts wrong work, rejects right work, or cannot deliver what the
prompt promises, the score stops measuring the skill. For each public EdgeBench task we checked
whether a good-faith solver gets the score the task promises, reliably. We reproduced every finding
on the task's original, digest-pinned evaluator. Every material defect was repaired as a new task
version in EdgeBench's own format, or the task was excluded.

| Read | For |
| --- | --- |
| [FINDINGS.md](FINDINGS.md) | What is wrong in each task and how much it changes the score |
| [APPLYING-FIXES.md](APPLYING-FIXES.md) | How to build and use the repaired task versions |
| [DECISIONS.md](DECISIONS.md) · [decisions.csv](decisions.csv) | The decision for all 51 tasks |
| [cases/](cases/INDEX.md) | One page per task: the problem, its impact, the fix, the evidence |
| [METHOD.md](METHOD.md) | How findings were established, decision rules, and limits |
| [site/index.html](site/index.html) | All of the above as one browsable page |

## Decisions

| Decision | Tasks | Meaning |
| --- | ---: | --- |
| **Repair (v2)** | **22** | Material defect, fixed in a new version |
| Retain with note | 28 | No defect that materially changes a good-faith solver's score; notes ship with the task |
| Exclude | 1 | Material defect without a sound repair in this release |
| **Total** | **51** | |

Every repair was checked by scoring the same inputs with the original and the repaired evaluator:
the defect's trigger is fixed, correct controls keep their scores, and incorrect controls are still
rejected ([134 paired rows](paired-results.csv)). Each paired evaluation was run three times, and
none of the 132 executed arms changed verdict ([repeatability](paired-repeatability.md)).

## What the defects look like

- **Correct work scored too low.** SMT Solver's witness checker keys function values by their source
  text, so 27 satisfiable hidden problems are unwinnable for any solver (perfect-solver ceiling
  78.61 → 72.40). Borden Inversion's hidden physics convention is undocumented: an honest textbook
  model fits the public data equally well but scores 7.0, against 31.2 under the judge's convention.
- **Incorrect work accepted.** In Exchange Core, two plausible engine bugs (a fee swap, dropped
  events) pass the correctness check and get full credit. In Jagua Nesting, overlapping shapes are
  accepted as valid layouts.
- **Rules that differ from the prompt.** Triangulation Coloring's flip rule omits the convexity
  condition the README states, and the same rule generated its test cases. Warehouse Routing
  promises 30 s per test case but allows 60 s per five-case input.
- **Scales that cannot be reached.** A Lean-proved lower bound shows Warehouse Routing's top score
  anchors are unreachable (ceiling ≈30.3/100). Treant Forest's anchors exceed its own turn cap
  (ceiling 21.02/100).
- **Small defects with large effects.** In Order Addition, a stale integrity hash caps every
  submission at 4 of 5 tests, so each run's best score freezes on its first submission.

All 51 tasks with their measured impact: [FINDINGS.md](FINDINGS.md).

## Formal checks

Lean 4 (Mathlib) and TLA+ settle questions that testing cannot. They show that two required theorem
statements are false, prove finance identities and a routing lower bound, and check an aliasing bug
and a test-credit counting rule. Every Lean proof lists its axioms, and every TLA+ model has a
negative control. All 21 formal results reproduce with `python3 tools/check_formal.py`
([log](evidence/formal/RECHECK.md)).

## Repository layout

| Path | Contents |
| --- | --- |
| `FINDINGS.md`, `APPLYING-FIXES.md`, `METHOD.md`, `DECISIONS.md`, `cases/` | The publication |
| `site/` | The browsable page (deployed with GitHub Pages) |
| `repairs/<task>-v2/` | Repair packages: patch, `materialize.sh`, `Dockerfile` `FROM` the original image digest, `task.json.in`, source lock, paired results |
| `decisions.json`, `decisions.csv`, `paired-results.csv`, `paired-repeatability.csv` | Machine-readable decisions and paired evaluations |
| `evidence/` | `reviews/` (per-task analyses), `scripts/` (rerunnable checks), `formal/` (Lean, TLA+), `runs/` (native-run jobs and results) |
| `tools/` | Generators for the tables, findings, guide and site; consistency, publish and formal checks; the E2B runner |
| `tasks/` | The original public task definitions, unchanged |
| `sforge/`, `tests/` | The EdgeBench harness and its grading tests |

## Scope and limits

- The 83 unreleased EdgeBench tasks are out of scope.
- No model runs: score effects are measured on authored controls and counterexamples, not on
  historical leaderboard submissions.
- Deliberate tampering with the scorer by a malicious submission is a harness design choice and is
  out of scope.
- v2 scores are not comparable with v1 leaderboard scores.

See [METHOD.md](METHOD.md) for the full list.

## Citation and licenses

Cite with [CITATION.cff](CITATION.cff). The harness derives from ByteDance Seed EdgeBench at
`6e4e5f4aa087a9121aa09a6059e5484e5102c6ff` (Apache-2.0, `LICENSE`). Task definitions derive from the
public Hugging Face release at `6cc5a7f1b3288ce52484ad828177b8cc86b05b75` (`tasks/LICENSE`). Task
images are referenced by their public Docker Hub digests and are not redistributed: repair packages
contain only patches, and `materialize.sh` rebuilds the changed files from the pinned images.
