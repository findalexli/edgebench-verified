# EdgeBench Verified

An independent re-verification of the **51 publicly released [EdgeBench](https://github.com/ByteDance-Seed/EdgeBench)
tasks** (of 134 advertised; the other 83 were not available and are out of scope). For every task
we asked one question: **is a good-faith solver scored correctly and repeatably for what the task
promises?** Every claim was checked against the task's original, digest-pinned sources and, where
feasible, reproduced on its original evaluator; each case page states what was run and what rests on
source reading or arithmetic. Every repaired defect ships as a new task version in EdgeBench's own
format, accepted only after a paired before/after check on the same inputs.

**For EdgeBench maintainers:**
[What is wrong and how much it matters](FINDINGS.md) ·
[How to apply the fixes](APPLYING-FIXES.md) ·
[All 51 decisions](DECISIONS.md) ([CSV](decisions.csv)) ·
[Case page per task](cases/INDEX.md) ·
[Method and limits](METHOD.md) ·
browsable version: open [`site/index.html`](site/index.html) in a browser.

Status: release candidate, October 12, 2026. No models were run: score effects are shown on authored
controls and counterexamples, never estimated for historical leaderboard entries.

## Decisions for all 51 tasks

| Decision | Tasks | Meaning |
| --- | ---: | --- |
| Retain | 0 | No defect and nothing to note (every retained task carries at least one note) |
| Retain with note | 28 | Real but immaterial, or disclosed, issue, or a usage note only where no good-faith defect was found; the note ships with the task |
| **Repair (v2)** | **22** | Material defect fixed in a new version; every repair passed a paired before/after check, a native run for all but the prompt-only OpenRCT2 repair ([134 paired rows](paired-results.csv), 4 of them for the excluded task's partial repair) |
| Exclude | 1 | Material defect without a justified repair in this release |
| **Total** | **51** | |

## Selected findings

- **SMT Solver:** the witness checker keys function values by source text, so 27 satisfiable hidden problems are unwinnable for any solver (perfect-solver ceiling 78.61 → 72.40). Fixed; checked with z3.
- **Exchange Core:** two plausible engine bugs (a fee swap, dropped events) pass the correctness check and receive full throughput credit (in single runs they even scored higher than the correct engine, within throughput noise). v2 gates scoring on the project's own integration tests.
- **Order Addition:** a stale integrity hash caps every submission at 4/5 tests, which freezes each run's best score on its first submission. A one-literal fix restores selection of later improvements.
- **Triangulation Coloring:** the flip-legality rule omits the convexity condition the README states; the same rule generated the test cases (all ten overlap) and scores submissions. v2 fixes the rule and regenerates valid cases.
- **Warehouse Routing:** the prompt promises 30 s per test case but the evaluator allows 60 s per five-case input; a Lean-proved lower bound (for a model of the tester that was matched to the tester by testing, not by proof) also shows the top two score anchors are unreachable (ceiling ≈30.3/100).
- **Borden Inversion:** the hidden physics convention is undocumented and non-physical; an honest textbook solver fits the public data equally well but scores at baseline (7.0 vs 31.2). v2 ships the exact forward model.
- **Lean Analysis:** two required theorem statements are false (refuted in Lean inside the task image), and compiler-generated targets make ≥1.69% of points unattainable and scores proof-style dependent. v2 fixes both.

All defects with their measured impact: [FINDINGS.md](FINDINGS.md).

## Relation to the earlier audit

An earlier automated audit (October 7–12) had withheld 18 originals, retained 1 and left 21 scoped
findings. We re-checked every claim from the original bytes. All 18 withheld defects reproduced:
12 needed repair, and 6 are retained with a note because they cannot materially change a good-faith
solver's score or concerned only scorer isolation (out of scope). We also found 8 material defects
the earlier audit had missed. Several earlier "setup blocked" tasks were failures of that audit's own
tooling. The earlier audit's files are preserved at Git tag `earlier-audit-final`.

## Formal checks

Lean 4 (Mathlib) and TLA+ were used where they settle a question exactly: false task statements,
finance identities, a warehouse-routing lower bound (kernel-checked; the coordinator's reported independent recompile has no saved log),
an aliasing bug in an in-place multiply, and a test-credit counting rule. Every main Lean result lists its
axioms (`propext`, `Classical.choice`, `Quot.sound` only); two Lean Analysis demonstrations that use the
task's own sorried statements show `sorryAx` by design, and two one-line CTA fixture inequalities have no
printed axiom list. Every TLA+ model has a negative control.
See [`evidence/formal/`](evidence/formal/).

## Repository layout

| Path | Contents |
| --- | --- |
| `FINDINGS.md`, `APPLYING-FIXES.md`, `METHOD.md`, `DECISIONS.md` | The publication |
| `site/index.html` | The same content as one browsable page |
| `cases/` | One page per task: promise, what we ran, findings, repair, paired results, limits, reproduction |
| `repairs/<task>-v2/` | Repair packages: patch, `materialize.sh`, `Dockerfile` `FROM` the original image digest, `task.json.in`, source lock, paired results |
| `decisions.json`, `decisions.csv`, `paired-results.csv` | Machine-readable decisions and paired evaluations |
| `evidence/` | `reviews/` (per-task review records), `scripts/` (rerunnable checks), `formal/` (Lean, TLA+), `runs/` (native-run jobs and results) |
| `tools/` | Generators for the tables, findings, guide and site; the E2B runner; the pre-commit publish check |
| `tasks/` | The original public task definitions, unchanged |
| `sforge/`, `tests/` | The EdgeBench harness and its grading tests |

## Provenance and licenses

The harness derives from ByteDance Seed EdgeBench at `6e4e5f4aa087a9121aa09a6059e5484e5102c6ff`; its
Apache-2.0 license is in `LICENSE`. Public task definitions derive from the Hugging Face release at
`6cc5a7f1b3288ce52484ad828177b8cc86b05b75`, with a separate license in `tasks/LICENSE`. Task images are
referenced by their public Docker Hub digests and are not redistributed: repair packages contain only
our patches, and each package's `materialize.sh` regenerates the changed files from the pinned image.
