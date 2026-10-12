# lean_analysis_proofs v2 (repair package)

## Defects repaired

1. **Two false statements** (`reviews/lean_analysis_proofs.md`). `Chapter11.MajorizesOn.anti_symm`
   parses as `∀ x ∈ I, (f x = g x ↔ …)` because of operator precedence. `Chapter11.PiecewiseConstantOn.div`
   puts both hypotheses on `f`, so `g` is unconstrained. Both negations are kernel-checked against the
   task's own definitions, so no sorry-free submission can earn these 2 targets. A correct proof of
   the intended statement is scored "type changed".
2. **Compiler-generated auxiliary targets** (`reviews/lean_aux_name_scoring.md`). 560 of the 2901
   targets are names the compiler generates (`X._proof_N`, `X._simp_N`, `X.eq_N`, `X.match_N`,
   `X.congr_simp`, `X._sizeOf_*`, `X._sunfold`, `X._unsafe_rec`). They are credited only if the
   generated name and the printed type match exactly. Honest proofs renumber, merge or reshape them,
   so the score depends on proof style. In the native sample, a tactic-mode `omega` proof scored 1
   point less than an equally correct term proof. At least 49 points are unattainable.
3. **Three statement placeholders** (`Chapter3.empty_function_{bijective,onto,one_to_one}_iff : … ↔ sorry`).
   The solver has to fill in the statement. Any filled statement changes the type text, so these
   targets can never be credited.

## Exact change

- `Analysis/Section_11_3.lean`: `∀ x ∈ (I:Set ℝ), f x = g x ↔ …` becomes `(∀ x ∈ (I:Set ℝ), f x = g x) ↔ …`.
- `Analysis/Section_11_2.lean`: `(hg: PiecewiseConstantOn f I)` becomes `(hg: PiecewiseConstantOn g I)`
  (Tao, *Analysis I*, Lemma 11.2.8).
- `eval_lean.py` (judge) excludes two kinds of baseline target:
  - names with a component that is compiler-generated: it starts with `_`, or it is `match_N`,
    `eq_N`, `eq_def`, `congr_simp` or `proof_N`;
  - targets whose baseline type text contains the token `sorry`.

  These names are also not reported as "new bad". `metrics.excluded_baseline_count` is added.
  Scoring logic is otherwise unchanged.
- The two Lean edits go into the judge baseline repo, which is the only copy in the judge image
  (`/home/workspace/judge/se-bmk-intern/analysis`). They also go into the solver starter
  (`Dockerfile.work`, `files/work/`).
- The baseline listing is regenerated with the task's own tooling. `lake build ListDeclAxiom` ran
  in the judge image (`paired/run_local.sh`, step 2). It rebuilt Section_11_2 through 11_10,
  `Analysis` and `ListDeclAxiom`. All 90 rewritten files (sources, oleans, ileans, traces, IR) are
  in `files/judge/v2-build-artifacts.tar`, and the `Dockerfile` `ADD`s them at their original paths.
  The grader regenerates the baseline at eval time (`--baseline-repo`), and the new build makes that
  a replay of the v2 listing.

**Target set.** The raw listing still has 2901 BAD/sorry declarations. The only listing difference
is the two corrected type strings. The v2 scored set has **2338 targets**: 2901 − 560 generated −
3 placeholders.
- The reviewer's 559 plus `Chapter5.ExtendedReal._sizeOf_inst`, whose parent `Chapter5.ExtendedReal`
  is a target.
- Every excluded auxiliary has a parent that is itself a target. The parent's transitive axiom check
  covers the auxiliary's sorry-dependence, so no proof obligation goes unchecked.

**Placeholder decision: exclude.** I did not score the 3 placeholders by the axiom check alone.
That would accept any filled statement, including a trivial one such as `P ↔ P`. Scoring them
properly would need a hidden intended answer, and the task has none. They remain in the starter as
ungraded exercises.

## Why it is minimal

- Two one-token source edits.
- One target-set filter of about 20 lines in the grader, with no change to type matching, the axiom
  allow-list, the HASH logic or the denominator rule.
- No new data, no reweighting, and no change to `eval_cmd`, the timeout, the parser or rescale.

## Score compatibility and anchor decision

**v2 scores are not comparable with v1.**
- The denominator changes from 2901 to 2338.
- Auxiliary credit is no longer awarded. Partial instance proofs that earned `_proof_N` points in v1
  now earn nothing until the instance is complete.
- Two targets become attainable.
- In the paired sample, the same honest submission scores 26/2901 = 0.00896 in v1 and
  15/2338 = 0.00642 in v2.

The `rescale` anchors are kept unchanged: `linear`, lower 0.0, upper 1.0. They are not leaderboard
rank anchors. They are the exact bounds of the pass rate, which is a fraction of targets, so they
are exactly computable for v2 as well. No new rank anchors are invented. Historical v1 leaderboard
numbers must not be placed on the same scale as v2.

## Files

`Dockerfile` (judge v2), `Dockerfile.work` (solver v2; not built), `files/`, `orig/` (in-image
originals), `repair.patch` (generated `diff -ruN`, text files only; the artifact tar is binary),
`task.json.in` (only `work.image_tag` and `judge.image_tag` change, to placeholders until images
are published), `source-lock.json`, and `paired/` (`run_local.sh`, `results.md`, inputs and
outputs).

## Limits

- **The work image was not pulled** (33 GB judge image only).
  - `Dockerfile.work` assumes that the starter lives at `/home/workspace/se-bmk-intern/analysis` and
    equals the judge sources. It also assumes the files are owned by `agent`.
  - None of these is verified.
- **`docker build` was not run.** The equivalent installation was tested: the same tar was
  extracted over the original image paths plus `eval_lean.py` (paired run, resume step). Lake then
  rebuilt 0 modules and produced a listing byte-identical to the regenerated one.
- **Paired runs were local, not E2B.** Each submission build started from the judge repo's prebuilt
  `.lake/build` with Mathlib `491a409`. The original `eval_cmd` instead copies
  `/home/workspace/baseline/.lake`, which has Mathlib `3203991`, and does a full rebuild. This is the
  same deviation as in the earlier reviews.
- Other false targets among the 2338 were not audited.
- The name filter is lexical. A user-named declaration with a final component like `eq_1` would be
  excluded too. None exists in this baseline: all 560 matches were checked.

## Build

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t ebv/lean_analysis_proofs-judge:v2 .
```

`materialize.sh` takes the following steps:

1. Pull the pinned image(s) by digest, unless already present.
2. Extract the original files with `docker create` and `docker cp`. No container runs in this step.
3. Check each original against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of every file under `files/` (and `orig/`) against `source-lock.json` → `materialize.outputs`. Any mismatch fails loudly.

After that, the `Dockerfile` builds without changes. Regenerated files keep the file mode they have in the image.
See `../MATERIALIZE-CHECK.md` for how each package was verified.

`files/judge/v2-build-artifacts.tar` is not stored either. `materialize.sh` rebuilds it inside the original 33 GB judge image: it copies the patched sources in place, runs `lake build ListDeclAxiom` and `lake build` (offline, `--network none --memory 4g --cpus 2`, a few minutes) and packs the 90 artifact paths listed in `source-lock.json`. The oleans are not expected to be byte-identical, so the tar is accepted when two checks pass. The rebuilt file set must equal the locked member list. The regenerated ListDeclAxiom listing must be byte-identical to `paired/out/v2-listing.txt` (sha256 in `materialize.lean_build`). The script holds the machine-wide heavy-job lock `/tmp/ebv-heavy.lock` for the whole run. `MATERIALIZE_SKIP_LEAN_BUILD=1` regenerates only the text files; `docker build` then fails until the tar exists. `files/work/` is copied from the patched judge sources, and `orig/` is regenerated too. Build the solver image with `docker build -f Dockerfile.work -t ebv/lean_analysis_proofs-work:v2 .`. That build is still unverified, as noted above.
