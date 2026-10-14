# FLT Regular Formalization (`flt_regular_formalization`)

**Outcome:** Kept, with a note. <mark>The weighted list of scored statements matches the task's own list exactly and contains no compiler-generated names, so we found no statement out of reach for a complete, correct solution.</mark>

## What the task asks

The solver works in a project on Fermat's Last Theorem written in Lean 4, a language for machine-checked math proofs. The prompt asks the solver to "finish **all** sorries in this folder" (a `sorry` is a placeholder for a missing proof) and says "we value minor progress". It warns, "Do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation." It also says that "finishing `fermatLastTheoremSeven` without completeing `isRegularPrime_seven` and `flt_regular` will not count." Unlike the other Lean tasks, this one is scored in weighted mode, with a weights file that lists 25 declarations of total weight 87. The task is in the Formal Math & Theorem Proving category.

## What we checked

We found no problem that changes scores. We checked the following:

- The Lean grader shared by several tasks credits targets that the compiler generates (names such as `X._proof_N`, `X._simp_N`, …) only when the exact generated name and printed type match. In `lean_analysis_proofs` this puts at least 44 helper targets (49 of 2901 targets in total, 1.69%, counting also 3 placeholder and 2 false statements) out of reach for any complete, correct solution. That problem cannot arise here, because no target is compiler-generated:

| Targets (weight) | Compiler-generated targets | Their share of the score | Fragile generated targets | `sorry` in type | P/¬P pairs | Lower bound on targets out of reach |
|---|---|---|---|---|---|---|
| 25 (weight 87) | **0** | 0% | 0 | 0 | 0 | **0** |

- The weights file has 25 entries, with weights from 1 to 6 and a total of 87. Those entries are exactly the 25 declarations marked BAD and containing `sorry` in the starting listing, and all 25 type texts equal the listing's.

The README groups the score into 100 points, but the grader uses weights totalling 87. The mismatch is in the documentation only.

The note says, "Census: 25 weighted targets (total weight 87) match the listing exactly; no aux targets; 0 unattainable".

The task does not change; the note above ships with it.

## How much it matters

No target is out of reach for a complete, correct solution (lower bound 0). The README's grouping into 100 points does not change any score.

## How we checked it

- We ran the original grader from the public image pinned by digest (toolchain v4.28.0), one container at a time, with `--network none --memory 4g --cpus 2`. The task's `judge.eval_cmd` ran verbatim on the unmodified baseline sources in the grader image. The command copies `/home/workspace/baseline/.lake` and `/home/workspace/baseline/lake-manifest.json` into the submission and rebuilds the whole project. The two manifests differ. In the grader image, `baseline/lake-manifest.json` has sha256 `7758d921…` and the grader repository's `FltRegular/lake-manifest.json` has `880c7aa4…` (`out/flt_regular_formalization/census.log`). We did not record the Mathlib (Lean's math library) revisions inside them. The unmodified starter scored 0/25 (weight 0/87) under this swap, with no `type_changed` and no `disappeared`. The full grading run, build included, took about 2.5 minutes with 2 CPUs (`native.log`, 06:43:30–06:46:03) against the 2,400 s limit.
- For the count inside the image, we recorded the grader files actually used and built the baseline `ListDeclAxiom` listing. The listing prints a HASH line for `flt_regular`, which was true on the baseline. We compared the weights-file entries with the listing's BAD declarations that contain `sorry`, and with their printed types.
- Credit requires declarations that use no extra axioms, which the grader checks through `ListDeclAxiom`.

## Limits

- We ran no AI model or solver. The effects shown come only from the test submissions we wrote.
- We scored only the unmodified starter on the grader, and no variant with real proofs for this task.
- We built submissions from the baseline sources in the grader image. We did not check whether the starter in the work image is identical to them.
- We did not check whether the work image builds against the same Mathlib as `/home/workspace/baseline`. If it does not, a proof that compiles in the work image can fail to build at grading, and a failed build scores 0. We built only the starter, whose proofs are all `sorry`, under the swap. Recorded agent runs on this task score up to 75.1 out of 100 (`tasks/README.md`), so their proofs did build under the swap.
- We did not measure build time with complete proofs; a run over the 2,400 s limit scores 0.
- We did not check whether each individual target is true.
- We did not check whether the work image exposes the upstream proofs. The upstream project is complete and public, and parts of it are in Mathlib.
- Scorer isolation is outside this release's scope (EdgeBench design choice).

## Reproduce

- Grader image: `sha256:c8b50a05…`.
- Count of targets: `evidence/scripts/lean_family_census/pipeline.sh <task_id> <image@digest> <project dir> <root module> FltRegular_weight.json`.
- Exact `eval_cmd` run: `evidence/scripts/lean_family_census/run_native.sh`. Its usage line is in the script header.
- Outputs: `evidence/scripts/lean_family_census/out/flt_regular_formalization/`. The weights-file entries and their weights are listed in `classify.txt`; the weights file itself is not included.
- Supporting records: `evidence/reviews/lean_family_aux_census.md`.
