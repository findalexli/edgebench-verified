# Method

## The question

EdgeBench scores an agent's work by running a hidden grader program on it. For each of the 51
public tasks we asked: **if an agent does honest, correct work, does it get the score the task
promises, reliably?**

A task fails this test in any of these cases:
- the grader applies a different rule from the one the agent is told;
- it rejects correct work;
- it accepts wrong work;
- it uses test data that breaks its own rules;
- it promises something its time limit or score scale cannot deliver;
- it gives different scores to identical work without saying so.

Not covered:

- **Deliberate cheating.** EdgeBench runs submissions next to the grader, so a submission written
  to attack the grader could interfere with it. That is a question about how the benchmark isolates
  its grader, not about whether a task is graded correctly.
- **The 83 unreleased tasks.** EdgeBench has 134 tasks, of which 51 are public.

## How a finding is established

1. **Pin the original.** We use the task definition from the public release and EdgeBench's
   published grader and agent images. Each image is identified by its digest, a fingerprint that
   changes if any byte changes. We also record a fingerprint of every grader file a finding relies on.
2. **Read the contract.** We quote the instructions and documents the agent receives, next to the
   grader's code, so that "what the task promises" is the task's own wording.
3. **Run the original grader.** We run the task's own grading command inside the original image,
   with no network access, on three kinds of test submission:
   - a correct submission, which must score as promised;
   - a submission that shows the problem, as small and concrete as possible;
   - a wrong submission, which must be rejected.
4. **Check it a second way.** Where a finding is mathematical or combinatorial, we confirm it
   independently, with exact arithmetic, a second implementation, exhaustive search, or a formal tool:
   - **Lean 4 with Mathlib** checks mathematical proofs by machine. It shows that two theorem
     statements in Lean Analysis are false. It also proves a lower bound on every valid Warehouse
     Routing answer, and the arithmetic behind the CTA and Portfolio findings. Each proof lists
     the basic assumptions (axioms) it relies on.
   - **TLA+ (with its model checker TLC)** explores every reachable state of a small model. It
     checks the in-place multiplication bug in Tree Block Partitioning and the test-credit rule
     in Rust Multicrate. Each model has a counter-check: the corrected version must pass where
     the original fails.
5. **Follow it to the final score.** A problem matters only through how the grader turns results
   into the published 0–100 score: how it reads the output, which submission it keeps, and how it
   converts the raw result. "How much it matters" on each case page is the largest change we
   demonstrated or proved on that scale.

## Formal verification

Wherever a claim could be stated precisely, it was also checked with Lean 4 (a proof assistant whose
kernel accepts a claim only with a complete proof, and which lists the axioms each proof uses) or TLA+
(a model checker that explores every reachable state of a bounded model). Every formal result is tied to
the real grader code by a source-line mapping and the file's fingerprint, is checked against saved
outputs of the real code wherever possible, has a counter-check that must fail, and states its limits.

26 of the 51 tasks have formal results. For 12 of the 22 fixes the fix itself is proved correct within
its model, and one more is partly proved. The formal checks found that the first College English fix was
narrower than published (since revised, re-proved and re-tested) and led to eight wording corrections.
Every result, its limit and its note: [evidence/formal/SUMMARY.md](evidence/formal/SUMMARY.md).

## Outcomes

| Outcome | Meaning |
| --- | --- |
| **Kept, with a note** | No problem that changes an honest agent's score enough to matter. Smaller issues, openly stated design choices and run conditions are recorded in a note. |
| **Fixed** | A problem that changes scores and can be fixed. A new version of the task is published in EdgeBench's own format. Scores from it are not comparable with the original. |
| **Removed** | A problem that changes scores and has no sound fix. |

## How a fix is accepted

Each fix is a folder in `repairs/<task>-v2/`. It contains:
- a patch against the files in the original image;
- a script that rebuilds the changed files from the public image;
- a build file based on the exact original image;
- the fixed task definition, which changes only the fields that must change.

A fix is accepted only after a side-by-side test. The same test submissions are graded by the
original and the fixed grader, and three things must hold:
- the submission that showed the problem is now graded correctly;
- correct submissions keep their scores, or the change is explained;
- wrong submissions are still rejected.

When a fix needs new reference points for the 0–100 scale, we never invent them. We keep the
original points and state the limit, or set them from quantities that can be calculated exactly,
such as the maximum possible raw result.

## Repeatability

Every side-by-side test was run three times on fresh machines. Across 132 graded comparisons in 22
fixed tasks, no outcome changed. Graders without randomness or timing reproduce exactly. Scores
based on speed move between runs, by up to 38% for Exchange Core, but no outcome changed. Details:
[data/paired-repeatability.md](data/paired-repeatability.md).

## Effect on the published leaderboard

[IMPACT.md](IMPACT.md) applies the findings to EdgeBench's published per-task scores. It corrects
changes of scale exactly, and gives the rest as a range, because the original submissions are not
public.

## Limits

- **No AI models were rerun.** Effects are measured with test submissions we wrote, not with
  historical leaderboard submissions or new model runs.
- **One machine type.** Side-by-side tests ran on machines with 8 virtual CPUs and 8 GiB of memory.
  Speed-based scores may move further on other hardware.
- **Partial checks.** Some findings rest on reading the grader's code or on exact arithmetic,
  rather than a full run of the grader. Their case pages say so.
- **Reviewed by AI agents.** Every published claim is tied to a saved evidence file, but agreement
  between agents is not independent human reproduction.

## Rebuilding the publication

All tables, the findings list, the guide and the website are generated from `data/decisions.json` and
`cases/plain.json`:

```bash
python3 tools/build_tables.py && python3 tools/build_findings.py && python3 tools/build_applying.py && python3 tools/estimate_impact.py && python3 tools/build_site.py
python3 tools/check_consistency.py   # every published count agrees with data/decisions.json
python3 tools/check_formal.py        # TLA+ models and Lean proofs reproduce their published outcomes
```
