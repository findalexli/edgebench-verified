# Method

## The question

EdgeBench scores a submission by running a task's evaluator inside a pinned container image. For
each of the 51 public tasks we asked one question: **does a good-faith solver get the score the
task promises, reliably?** A task fails this test if the evaluator applies a different rule from the
one the solver is told, rejects correct work, accepts incorrect work, uses data that violates its own
contract, promises something its time or score budget cannot deliver, or produces scores that change
between identical runs without saying so.

Out of scope:

- **Deliberate tampering.** EdgeBench runs submissions inside the judge container, so a submission
  written to attack the scorer can interfere with it. That is a harness design choice, not a task
  defect.
- **The 83 unreleased tasks.** EdgeBench advertises 134 tasks, of which 51 are public.

## What counts as evidence

1. **Pin the original.** The task definition from the public release, the judge and work images by
   OCI digest, and the sha256 of every evaluator file a finding relies on.
2. **Read the contract.** The prompt, the README files shipped to the solver, and the evaluator
   code, so that "what the task promises" is quoted, not paraphrased.
3. **Run the original evaluator.** The task's own `eval_cmd` in the pulled image, with no network,
   on three kinds of input:
   - a correct submission (it must score as promised);
   - the trigger (a small, concrete input that shows the defect);
   - an incorrect submission (it must be rejected).
4. **Check with an independent oracle** where a finding is mathematical or combinatorial: exact
   rational or integer arithmetic, a second implementation, exhaustive search, or a formal tool.
   - **Lean 4 + Mathlib:** whether a required theorem is false, finance identities, and a
     routing lower bound. Every proof lists its axioms.
   - **TLA+ (TLC):** an aliasing bug and a test-credit counting rule, each with a negative control
     and stated bounds.
5. **Trace to the reported score.** A defect matters only through the task's parser, selection
   policy and rescale to the 0–100 score. "Max effect" on each case page is the largest change we
   demonstrated or proved on that scale.

## Decisions

| Decision | Meaning |
| --- | --- |
| **Retain with note** | No defect that materially changes a good-faith solver's score. Immaterial issues, disclosed design choices and run conditions are recorded as notes that ship with the task. |
| **Repair (v2)** | A material, fixable defect. A new task version ships in EdgeBench's own format; the original is superseded, and v2 scores are not comparable with v1. |
| **Exclude** | A material defect without a sound repair in this release. |

## How a repair is accepted

Each repair is a package in `repairs/<task>-v2/`:

- a patch against the files in the original image;
- `materialize.sh`, which rebuilds the changed files from the pinned public image;
- a `Dockerfile` `FROM` the original digest;
- `task.json.in`, changing only the necessary fields.

A repair is accepted only if one paired evaluation, the same inputs scored by the original and the
repaired evaluator, shows three things: the trigger is fixed, correct controls keep their scores
(or the change is explained), and incorrect controls are still rejected. Score anchors that came
from historical leaderboard runs are never re-invented: they are kept with the limit stated, or set
from exactly computable quantities.

## Repeatability

Every paired evaluation was run three times on fresh workers. Across 132 executed arms in 22
repair packages, no verdict changed. Deterministic evaluators reproduce exactly. Throughput and
timing scores move (up to 38% for Exchange Core throughput) without changing any verdict. Details
are in [paired-repeatability.md](paired-repeatability.md).

## Limits

- **No model runs.** Score effects are measured on authored controls and counterexamples, not on
  historical leaderboard submissions or fresh model attempts.
- **One hardware class.** Paired evaluations ran on 8-vCPU / 8 GiB workers. Timing-based scores may
  move further on other hardware.
- **Partial checks.** Some findings rest on source reading or exact arithmetic rather than a full
  native run. Their case pages say so.
- **AI review.** The reviews were carried out by AI agents. Every published claim is traced to a
  saved evidence file, but agreement between agents is not independent human reproduction.

## Rebuilding the publication

All tables, the findings list, the guide and the site are generated from `decisions.json`:

```bash
python3 tools/build_tables.py && python3 tools/build_findings.py && python3 tools/build_applying.py && python3 tools/build_site.py
python3 tools/check_consistency.py   # every published count agrees with decisions.json
python3 tools/check_formal.py        # TLA+ models and Lean proofs reproduce their published outcomes
```
