# Paired v1 / v2 results: lean_analysis_proofs-v2

## Setup

- **How it ran.** Locally, not on E2B. Each step used one container of the pinned judge image
  `seededge/edgebench.judge.lean_analysis_proofs@sha256:41ece9c4…513b`, which was already local.
  - Flags: `--network none --memory 4g --cpus 2`; every container was removed afterwards.
  - The machine-wide `flock /tmp/ebv-heavy.lock` was held after the host restart.
- **Script.** `run_local.sh` ran in two parts. `run_local.part1.log` covers v1/v2 orig, A and BAD,
  and v1 T. A host out-of-memory restart then killed the container while it was running v2 T.
  `run_local.part2.log` (`RESUME=1`) covers v2 T, S and W.
  - The resume did not rebuild v2. It installed v2 exactly as the `Dockerfile` does: the
    `eval_lean.py` copy plus extraction of `files/judge/v2-build-artifacts.tar`.
  - Lake then rebuilt **0** modules. The v2 listing was **byte-identical** to the one regenerated in
    part 1 (`out/v2-listing.resume.txt` = `out/v2-listing.txt`).
- **Grader steps.** These are the `eval_cmd` steps. The submission sits at
  `/home/workspace/se-bmk-intern/analysis` and the run does `lake build`, copies the judge
  `ListDeclAxiom.lean`, then runs `python3 eval_lean.py --baseline-repo <judge repo> --current-repo <sub>`.
  - **Deviation:** the submission builds incrementally from the judge repo's `.lake/build` (Mathlib
    `491a409`). The original `eval_cmd` instead copies `/home/workspace/baseline/.lake` (Mathlib
    `3203991`) and does a full rebuild.
  - v1 runs use a relocated, untouched copy of the judge repo and of `eval_lean.py`.
- **Normalized score.** `rescale` is `linear` 0..1, so the normalized score equals the raw score.
- **Exit statuses.** `eval_lean.py` exited 0 in every scored case. In the BAD case `lake build`
  exited 1, so `eval_cmd` (joined with `&&`) never reaches the grader.

## Baseline (regenerated with the task's tooling)

| | v1 | v2 |
|---|---|---|
| `ListDeclAxiom` SUMMARY | checked=4743 bad=2901 | checked=4743 bad=2901 |
| listing diff | – | exactly 2 lines (the anti_symm and div type strings) |
| scored targets (`baseline_total`) | 2901 | **2338** (560 generated + 3 `↔ sorry` placeholders excluded) |

## Corrected statements (step 3, `lean/EbvV2Proofs.lean`, in the v2 judge repo, Lean 4.28.0)

`#check` prints the corrected installed types:
- `(∀ x ∈ ↑I, f x = g x) ↔ MajorizesOn f g I ∧ MajorizesOn g f I`
- `PiecewiseConstantOn f I → PiecewiseConstantOn g I → PiecewiseConstantOn (f / g) I`

Sorry-free proofs, which use task definitions only and no task lemma:

| theorem | axioms |
|---|---|
| `EbvV2.anti_symm_corrected` | propext, Classical.choice, Quot.sound |
| `EbvV2.div_corrected` | propext, Classical.choice, Quot.sound |
| `EbvV2.inter'` (helper: intersection of two bounded intervals, via `IsPreconnected.mem_intervals`) | propext, Classical.choice, Quot.sound |

The earlier refutation witness of `div` (f = 1, g = id) no longer satisfies the hypotheses: `id`
is not piecewise constant on [1,2]. The statement is now proved outright. Variant A also proves both
statements **inside the real grader**: they are PASSED in v2.

## Paired table

| variant | what it is | version | lake build | score | repaired / targets | type_changed |
|---|---|---|---|---|---|---|
| orig | unchanged starter (valid baseline control) | v1 | ok | 0 | 0/2901 | 0 |
| | | v2 | ok | 0 | 0/2338 | 0 |
| **A** (trigger + controls) | corrected div and anti_symm proved; `MajorizesOn.trans` proved; `ConstantOn.const_eq` "proved" via the sorried `Constant.const_eq` | v1 | ok | 0.000345 | 1/2901 (trans only) | 2 (anti_symm, div) |
| | | v2 | ok | 0.001283 | 3/2338 (anti_symm, div, trans) | 0 |
| BAD (invalid) | `MajorizesOn.trans` with the composition reversed (type error) | v1 | **rc=1** | no score | – | – |
| | | v2 | **rc=1** | no score | – | – |
| T | honest Section_4_1, term style | v1 | ok | 0.008962 | 26/2901 (15 parents + 11 aux) | 4 |
| | | v2 | ok | 0.006416 | 15/2338 | 0 |
| S | honest Section_4_1, tactic style | v1 | ok* | 0.008962 | 26/2901 (15 + 11) | 4 |
| | | v2 | ok | 0.006416 | 15/2338 | 0 |
| W | honest Section_4_1, setoid via `omega` | v1 | ok* | 0.008618 | 25/2901 (15 + 10) | 5 |
| | | v2 | ok | 0.006416 | 15/2338 | 0 |

\* The v1 S and W rows reuse the reviewer's native runs (`scripts/lean_aux_names/out/report_{S,W}.json.gz`).
They ran on the same image with the same grader bytes and procedure. I did not rerun them after the
OOM restart. This run's v1 T repaired set is identical to the reviewer's v1 T set, which checks
that the two harnesses agree.

Further detail is in `out/style_check.txt`:
- In every style, every v1-credited parent is credited in v2.
- v2 credits nothing that v1 did not credit, apart from A's two corrected statements.
- The v2 repaired sets for T, S and W are **identical** (15 parents), so the score no longer depends
  on proof style.
- v2 reports 0 type_changed, 0 disappeared and 0 new_bad for T, S and W.
- In A, `ConstantOn.const_eq` stays BAD (`still bad: unexpected=[sorryAx]`) in both versions, so
  proving a target from a sorried lemma is still not credited.

## Acceptance

1. **Trigger:** passes.
   - Correct proofs of the intended statements score 0 for those targets in v1 ("type changed").
     The literal v1 statements are refuted.
   - The same proofs are credited in v2.
   - Style-dependent auxiliary scoring in v1 (T/S 26 vs W 25) is gone in v2 (15 = 15 = 15).
2. **Valid controls:** pass.
   - The unchanged starter scores 0 in both versions.
   - `MajorizesOn.trans` and all 15 honest Section_4_1 parents are credited in both versions.
   - The changes between v1 and v2 come only from the denominator (2901 → 2338) and the removal of
     auxiliary credit, which is the intended change.
3. **Invalid controls:** pass.
   - The type-incorrect proof fails `lake build` in both versions.
   - The proof via a sorried lemma is not credited in either version.

**Accepted**, subject to the limits in `../README.md`: the work image was not built, `docker build`
was not run (an equivalent installation was tested), and the baseline `.lake` Mathlib deviation.
