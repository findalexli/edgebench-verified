# Method

EdgeBench Verified re-examines the 51 publicly released EdgeBench tasks (of 134 advertised;
the other 83 were not available and are out of scope). For each task we asked one question:
**would a good-faith solver be scored correctly and repeatably for what the task promises?**

## Scope

- **In scope:** wrong scoring rules, wrong or invalid data, promises the evaluator cannot
  keep (time horizons, budgets, formats), undocumented conventions an honest solver cannot
  reproduce, weak checks that accept plausibly incorrect solutions, mis-calibrated score
  scales, and non-repeatable scoring.
- **Out of scope:** tampering with the scorer by a deliberately malicious submission. EdgeBench
  runs submissions inside the judge container; isolating them is a harness design choice, not
  a task defect. We recorded such observations internally and do not publish them.
- **Not attempted:** fresh model/agent runs. Score effects are measured on authored controls and
  counterexamples, never estimated for historical leaderboard entries.

## How a claim becomes a finding

An earlier audit (Codex agents, October 7–12, 2026) left 21 scoped findings and 18 "withhold"
decisions. We treated every earlier claim as a hypothesis and every task as unreviewed:

1. **Pin the original.** Task JSON from the public release, the judge/work images by OCI digest
   from Docker Hub, and sha256 of every source file relied on.
2. **Read the contract first.** Prompt, shipped READMEs and evaluator, before earlier evidence.
3. **Reproduce on the original evaluator path.** Pulled judge image, the task's own `eval_cmd`,
   `--network none`, with a known-good control, the trigger, and a known-bad control. Heavy runs
   used isolated E2B cloud workers (8 vCPU, 8 GiB), one job per worker, killed by exact ID.
4. **Use an independent oracle** where the claim is mathematical or combinatorial: exact
   rational/integer arithmetic, a second implementation, brute force, or a formal tool.
   - **Lean 4 + Mathlib** for statement truth (e.g. two false theorem statements refuted inside
     the task's own image), finance identities, and corrected-statement proofs; every main proof is
     reported with `#print axioms` (only `propext`, `Classical.choice`, `Quot.sound`). Two
     demonstrations built on the task's own sorried statements show `sorryAx` by design, and two
     one-line CTA fixture inequalities have no printed axiom list.
   - **TLA+ (TLC)** for state/counting logic (aliasing in an in-place multiply; test-credit
     counting), each with a negative control and stated bounds.
5. **Trace to the reported score.** Through the task parser, selection policy and rescale to
   the 0–100 score. Several real defects turned out to be immaterial (rescale erases them);
   one small one turned out to freeze every run (selection amplifies it).
6. **Coordinator re-check.** The coordinating reviewer re-read the decisive code line or reran
   the decisive check for published findings before recording them. A re-check is documented only
   where a case page or review records it (for example "coordinator-checked"); some pages note
   where it was not done.

## Decisions

| Decision | Meaning |
| --- | --- |
| **Retain** | No defect affecting good-faith solvers was found. |
| **Retain with note** | A real but immaterial or disclosed issue; the note is part of the release. |
| **Repair (v2)** | A material, fixable defect. A new task version ships; the original is superseded. v2 scores are not comparable with v1. |
| **Exclude** | A material defect without a justified repair in this release. |

## How a repair is accepted

Each repair is a package in EdgeBench's native format (`repairs/<task>-v2/`): a Dockerfile
`FROM` the original image digest plus only the changed files, a generated patch, a `task.json.in`
changing only the needed fields, and a source lock. It is **accepted** only if, on the same inputs
scored by the original (v1) and repaired (v2) evaluator in one run: the trigger is fixed, valid
controls keep their scores (or the change is explained), and invalid controls are still rejected.
Two repairs were accepted on a narrower check: the prompt-only OpenRCT2 repair changes no executable
file, so its controls hold by construction and were not re-run, and the CTA trigger was paired at
component level because no eligible full submission exists.
Where rescale anchors came from historical leaderboard runs, we did not invent new ones; we kept
them with a non-comparability note, or set them from exactly computable quantities.

## Repeatability

Every repair's paired evaluation was run three times on fresh workers (the published run plus two
reruns). Across 132 executed arms in 22 packages, no verdict changed: every trigger stayed fixed by
v2, every valid control stayed valid, every invalid control stayed rejected. Deterministic evaluators
reproduce exactly; throughput and timing scores move (up to 38% for Exchange Core throughput)
without changing any verdict. Details: [paired-repeatability.md](paired-repeatability.md); rebuild
with `tools/repeatability/` (the Treant row needs the original cases extracted from the pinned image).

## Limits

- One run per arm in most paired checks; timing-based scores are host-dependent.
- Controls are authored; they establish the stated behaviour, not a defect rate in real solver
  populations or historical leaderboard impact.
- AI agents performed the reviews; agreement between agents reviewing the same evidence is not
  independent reproduction. Each case states what was re-run and what was reused.
