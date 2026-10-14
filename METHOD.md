# Method

## The question

EdgeBench scores an agent's work by running a hidden grader program on it. For each of the 51
public tasks we asked: **if an agent solves the task correctly and by the rules, does it get the
score the task promises, reliably?**

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
3. **Exercise the original grading path.** Where available, we run the task's own grading command
   inside the original image, with no network access, using the following controls. Each case
   distinguishes full native runs from original-helper tests and source arguments:
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
   converts the raw result. Each case page distinguishes measured changes, proved upper bounds and restricted numerical sensitivity estimates. An upper bound need not be attainable.

## Formal verification

Selected mathematical and state-machine claims were checked with Lean 4 (a proof assistant whose
kernel accepts a claim only with a complete proof, and which lists the axioms each proof uses) or TLA+
(a model checker that explores every reachable state of a bounded model). Every formal result is tied to
the real grader code by a source-line mapping and the file's fingerprint, is checked against saved
outputs of the real code wherever possible, has a counter-check that must fail, and states its limits.

26 of the 51 tasks have saved formal results. The summary classifies 9 repair models as proved or exhaustively model-checked within bounds (five of them of an earlier version of the fix) and five as partial, among them the SMT answer checker, which is proved only for a narrow fragment. These counts describe modeled properties and historical versions, not 14 certified current repair packages. In particular, the saved Datagen and FFmpeg proofs do not verify Datagen v2.1 or FFmpeg v2.2, CTA models a gross-exposure denominator rather than the policy's NAV denominator, the Graph Node proof models the first fix (v2) and not v2.1's `str()` key handling or duplicate-key rejection, and the College English model is of v2.1, not v2.2's block selection and decimal-string reading. The CPU limits added to several fixes are checked
by runs, not formally. The
formal checks found that the first College English fix was narrower than published (since revised,
re-proved and re-tested) and led to eight corrections
([evidence/formal/CORRECTIONS.md](evidence/formal/CORRECTIONS.md)).
Every result, its limit and its note: [evidence/formal/SUMMARY.md](evidence/formal/SUMMARY.md).

## Outcomes

| Outcome | Meaning |
| --- | --- |
| **Kept, with a note** | No correctable problem. What varies is run-to-run or machine noise that no change to the grader removes, or an issue too small to change a score; it is recorded in a note with its size, or marked unmeasured. The largest is ANN Vector Search, about ±7 of 100 points per grading. |
| **Repair proposed (`repair-v2`)** | A correctable finding has a versioned repair package. This disposition does not establish full release acceptance: component checks, native paired results and integration status are reported separately. Portfolio's +0.3921/−0.10 numerical envelope is a restricted sensitivity estimate, not a universal bound. Score compatibility is task-specific. |
| **Removed** | A problem that changes scores and has no sound fix. |

## How a fix is validated

Each fix is a folder in `repairs/<task>-v2/`. It contains:
- a patch against the files in the original image;
- a script that rebuilds the changed files from the public image;
- a build file based on the exact original image;
- the fixed task definition, which changes only the fields that must change.

A repair needs side-by-side evidence for the changed behavior; a historical paired run does not accept a later revision. Component tests validate only their exercised path. The same test submissions are graded by the
original and the fixed grader, and three things must hold:
- the submission that showed the problem is now graded correctly;
- correct submissions keep their scores, or the change is explained;
- wrong submissions are still rejected.

Full release acceptance additionally requires the actual task command, dependency path, final work/grader images and result-collection harness to operate together within the task budgets. The remaining gates are FFmpeg's submission-build path, Warehouse's backend integration of the host-side drain repair, Lean Analysis's image builds and actual grading path, PFR's credit on the five actual targets, Equivalence's per-problem checks on all six problems and Vibrating Path's 13 unresolved zero-hit cases. A component result, a formal model or a Docker-only grading run cannot clear those gates. The `validation_status` field records known scope limits independently of the repair disposition.

**Clean-machine rebuild.** Every package as committed at 83181b7f was copied to a fresh E2B worker (21 GB disk, no images at start); its `materialize.sh` ran unchanged, every locked output was rechecked by an independent script, `Dockerfile` and `Dockerfile.work` were built, and every copied file was hashed inside the built image ([evidence/runs/materialize-check-summary](evidence/runs/materialize-check-summary/README.md); six jobs, each ledger `status: exit=0`, results collected). 31 of 32 packages passed. Lean Analysis could not be checked: its grader image unpacks to about 33 GB, and the rebuild needs about 45 GB of free disk. PFR passed with its work-image check moved after the grader steps, which its `materialize.sh` now does itself. Packages revised after 83181b7f are covered only by their later runs, as their case pages state.

When a fix needs new reference points for the 0–100 scale, we never invent them. We keep the
original points and state the limit, or set them from quantities that can be calculated exactly,
such as the maximum possible raw result.

## Repeatability

The historical paired-run inventory below describes the recorded package revisions; it does not cover subsequent candidates or their unresolved integration gates. Most side-by-side comparisons in that inventory were run three times. Across 254 graded comparisons, covering 30
fixed tasks and the removed task's partial fix (240 of them run three times; 2 setup runs that prepare
inputs are not counted), one outcome changed, under the original grader: at 4 CPUs, Vibrating Path's valid deadline-based test submission timed out on 14 cases in one of its nine original-grader gradings, the timing problem the fix removes. No fixed-grader outcome changed. Exceptions: OpenRCT2's fix changes only its instructions and has nothing to run; Lean Analysis repeats ran locally rather than on fresh machines; Integer Codec's final 0–100 scale was applied to the recorded raw results; the revised College English grader was itself run three times; and 14 comparisons ran once: the Rust starter's fixed-version score (each run takes about 40 minutes and nearly fills the machine's disk), the CTA v2.1 standard answer, the six Exchange Core rows at 4 CPUs (one row per run of a three-run job), and the three controls each of Datagen v2.1 and FFmpeg v2.2 (single runs). Graders without randomness or timing reproduce exactly. Scores
based on speed move between runs, by up to 38% for Exchange Core, but no outcome changed. Details:
[data/paired-repeatability.md](data/paired-repeatability.md).

## Effect on the published leaderboard

[IMPACT.md](IMPACT.md) applies the findings to EdgeBench's published per-task scores. It recomputes
the removal of D-ABIC and changes of scale where the published aggregates permit it. Treant conversion is not exact from an average when constituent runs cross clipping or piecewise boundaries. Other effects are conditional bounds or sensitivity estimates because the original submissions are not public. Bounds larger than a ranking gap mean the ranking cannot be certified from those bounds; they do not prove a reversal is attainable.

## Limits

- **No AI models were rerun.** Effects are measured with test submissions we wrote. The only real
  agent submissions used are from one third-party run of one model: for 7 fixed tasks whose fix
  changes only the grader, 314 of them were regraded with both graders
  (`evidence/runs/opus55-regrade2-summary/`; an earlier, smaller regrade is in
  `evidence/runs/opus55-regrade/`). The leaderboard's own submissions
  are not public.
- **Machines.** Most side-by-side tests ran on E2B cloud sandboxes with 8 virtual CPUs and 8 GiB of
  memory; Lean Analysis ran on a local host with 16 CPUs and 15 GB. The grader was limited to the
  CPU count each case page states, from 1 to 8. Where the grader's CPU count was varied (4 against
  8), the case page reports both. The CPU count EdgeBench's leaderboard gives each grader is quoted
  in [evidence/impact/edgebench-leaderboard-config.md](evidence/impact/edgebench-leaderboard-config.md).
  Speed-based scores may move further on other hardware.
- **The harness is EdgeBench's.** The grading code in `sforge/` is EdgeBench's, byte for byte
  (`tools/check_upstream.py`). Two of its three rules for picking a run's best submission
  (`score_first` and `pass_rate_first`) ignore whether a result was marked invalid; only the third
  (`valid_then_score`) drops results marked `valid: false`.
- **CPU policy.** Measurements establish how oversubscription changes available CPU and verdicts under wall-clock limits. A stated wall-clock allowance alone does not promise a dedicated core or the same allowance in CPU-seconds; the parallelism caps are explicit resource-policy choices.
- **Partial checks.** Some findings rest on reading the grader's code or on exact arithmetic,
  rather than a full run of the grader. Their case pages say so.
- **Reviewed by AI agents.** Every published claim is tied to a saved evidence file, but agreement
  between agents is not independent human reproduction.

## Rebuilding the publication

All tables, the findings list, the guide and the website are generated from `data/decisions.json` and
`cases/plain.json`:

```bash
python3 tools/sync_case_figures.py && python3 tools/build_tables.py && python3 tools/build_findings.py && python3 tools/build_applying.py && python3 tools/estimate_impact.py && python3 tools/build_site.py
python3 tools/check_consistency.py   # every published count agrees with data/decisions.json
python3 tools/check_formal.py        # TLA+ models and Lean proofs reproduce their published outcomes
```
