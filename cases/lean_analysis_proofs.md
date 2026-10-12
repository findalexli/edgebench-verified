# Lean Analysis Proofs (`lean_analysis_proofs`)

**Decision:** Repair (v2). Two target statements are false, and the original grader scores compiler-generated helper names, so honest proofs of the same theorem can score differently depending on proof style.

## What the task asks for

The prompt asks the solver to "finish **all** sorries in this folder" of a Lean 4 formalisation of Tao's *Analysis I*, says "we value minor progress", and warns: "do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation." The grader (`eval_lean.py` with the task's `ListDeclAxiom.lean`) treats every declaration that depends on `sorryAx` in the baseline repo as one target worth 1 point. A target is credited only if, in the submission, the same name uses only `propext`, `Classical.choice` and `Quot.sound`, and its printed type text equals the baseline text exactly. In v1 there are 2901 targets. Category: Formal Math & Theorem Proving.

## What goes wrong

**1. Two target statements are false.** As installed, the task's own Lean prints:

```
@Chapter11.MajorizesOn.anti_symm : ∀ {f g : ℝ → ℝ} {I : Chapter11.BoundedInterval},
  ∀ x ∈ ↑I, f x = g x ↔ Chapter11.MajorizesOn f g I ∧ Chapter11.MajorizesOn g f I
@Chapter11.PiecewiseConstantOn.div : ∀ {f g : ℝ → ℝ} {I : Chapter11.BoundedInterval},
  Chapter11.PiecewiseConstantOn f I → Chapter11.PiecewiseConstantOn f I → Chapter11.PiecewiseConstantOn (f / g) I
```

- In `anti_symm`, the binder `∀ x ∈ I,` extends over the whole `↔`. So it says that equality at a single point is equivalent to two-sided majorization on all of `I`. Counterexample: I = Icc 0 1, f = 0, g = id, x = 0.
- In `div`, both hypotheses are about `f`, so `g` is unconstrained. Counterexample: I = Icc 1 2, f = 1, g = id.
- Expected: a correct proof of the intended statement earns the point. Observed: it prints a different type and is scored "type changed". No sorry-free submission can earn these two points. Using the false lemmas elsewhere leaks no credit, because axiom checks are transitive.

**2. Compiler-generated helper targets make scoring depend on proof style.** When Lean compiles a definition or instance, it also creates hidden helper declarations with generated names, such as `X._proof_N`, `X._simp_N`, `X.eq_N` and `X.match_N`. While the parent contains `sorry`, these helpers depend on `sorryAx` too, so the grader lists them as separate targets. 559 of the 2901 targets are such names. The task never mentions them. A helper is credited only if an honest build produces a helper with the **same generated name and the same printed type**, and that depends on how the parent was proved:

- **Same facts, different tactic.** `PreInt.instSetoid._proof_1` was credited when the setoid's reflexivity and symmetry were proved in term or tactic mode. When the same facts were closed by `omega`, `omega` generated its own helpers first, the original obligation moved to `_proof_3`, and the target was scored "type changed". Both proofs are correct; the `omega` one scored 1 point less.
- **Lost in every style tried.** The parent `Int.equivInt` was credited, but `Int.equivInt._proof_1..4` were lost in every variant: "type changed" in T, S, W and X, and three "type changed" plus one "disappeared" in U. Some were renumbered, some merged into one helper, and one printed its binders as `∀ (h : PreInt) (b : PreInt)` instead of `∀ (a b : PreInt)`.
- **Unattainable whatever the proof.** 35 targets have `sorry` in their baseline type text (32 helpers plus 3 statement placeholders such as `Chapter3.empty_function_bijective_iff : … ↔ sorry`), so any sorry-free solution changes the type. At least 12 more helpers omit a case hypothesis, so their recorded types are false.

Sample on one module (Section_4_1, original grader):

| variant | style | score | repaired | type_changed | disappeared |
|---|---|---|---|---|---|
| orig (control) | starter unchanged | 0 | 0/2901 | 0 | 0 |
| T `3c7b39d1…` | term mode (`Iff.rfl`, `fun _ => rfl`, `⟨…, …⟩`); equivInt via `omega` | 26/2901 | 26 | 4 | 0 |
| S `c00db26b…` | tactic mode (`constructor`, `rw`, `omega`) | 26/2901 | 26 (same set as T) | 4 | 0 |
| U `ea9f1cd2…` | as T, but the equivInt congruence proved without omega; inverse laws left as sorry | 25/2901 | 25 | 3 | 1 |
| W `852fa9dd…` | as T, but setoid refl/symm closed by `omega` | 25/2901 | 25 | 5 | 0 |
| X `878e14c8…` | as T, plus the `Int.decidableRel` holes proved | 28/2901 | 28 | 7 | 0 |

Every honestly proved parent earned its own point. Of 15 helper targets under the completed parents, the best honest variant earned 8.

## Impact

- False statements: 2 of 2901 points for every solver; the ceiling is 2899/2901 = **99.93%**.
- Overall, **at least 49 of 2901 points (1.69%) are unattainable** for a fully honest, complete solution (the 35 sorry-typed, 12 hypothesis-dropped and the 2 false statements); about 57 (1.96%) is the likely figure.
- Up to 466 helper points under definition parents could in principle be won or lost by proof style. In the sample, 3 of 15 were lost that way. This was not measured across the whole repository.

## Fix (v2)

v2 makes two one-token source edits and adds one target filter to the grader.

- `Section_11_3.lean` now reads `(∀ x ∈ (I:Set ℝ), f x = g x) ↔ …`.
- `Section_11_2.lean` takes `(hg: PiecewiseConstantOn g I)` (Tao, Lemma 11.2.8).
- Both edits go into the judge baseline repo and the solver starter.
- The grader excludes targets whose name has a compiler-generated component (starts with `_`, or is `match_N`, `eq_N`, `eq_def`, `congr_simp` or `proof_N`) and targets whose baseline type contains `sorry`. Every excluded helper has a parent that is still a target, and the parent's transitive axiom check still covers it.
- The 3 placeholder statements stay in the starter as ungraded exercises: scoring them would accept any filled statement, including a trivial one.
- Type matching, the axiom allow-list and the denominator rule are otherwise unchanged. The scored set is **2338 targets**: 2901 − 560 generated − 3 placeholders.

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

\* The v1 S and W rows come from separate native runs on the same image and grader bytes.

In v2 the term, tactic and `omega` styles credit the identical 15 parents, with 0 type_changed, 0 disappeared and 0 new_bad. Every parent credited in v1 is credited in v2, and v2 credits nothing new apart from the two corrected statements. The proof routed through a sorried lemma stays uncredited in both versions, and the type-incorrect proof fails `lake build` in both.

**Score compatibility: v2 scores are not comparable with v1.** The denominator changes from 2901 to 2338, helper credit is removed (partial instance proofs that earned `_proof_N` points in v1 earn nothing until the instance is complete), and two targets become attainable. The same honest submission scores 26/2901 = 0.00896 in v1 and 15/2338 = 0.00642 in v2. The `rescale` bounds (linear, 0.0 to 1.0) are unchanged because they are the exact bounds of a pass rate. v1 numbers must not be placed on the v2 scale.

## How we know

- **Original evaluator in the pinned image.** The unmodified grader ran in the judge image (`sha256:41ece9c4…513b`, Lean 4.28.0) on the six Section_4_1 variants above. `lake build ListDeclAxiom` in the judge repo printed `SUMMARY checked=4743 bad=2901`. The helper targets were counted by name pattern, and each helper's parent was queried in the image.
- **Formal check (Lean).** A refutation file importing the task's own `Chapter11` definitions was run with `lake env lean` in the judge image (`--network none --memory 4g --cpus 2`). It kernel-proves the negation of each literal statement, stated against the installed definitions, not Mathlib analogues. A local mirror under Lean 4.34.1 gave the same results. Both corrected statements were proved sorry-free in the v2 judge repo. All of these proofs use only the axioms `propext`, `Classical.choice` and `Quot.sound`.
- **Paired evaluation.** v1 and v2 ran in the judge image with the controls above. The paired evaluation was repeated three times with no verdict change ([`paired-repeatability.md`](../paired-repeatability.md)).

## Limits

- No model or solver runs. Effects are shown on authored controls and counterexamples only.
- **The v2 work image was not built,** and the original work image was not pulled. `Dockerfile.work` assumes the solver starter is at `/home/workspace/se-bmk-intern/analysis`, equals the judge sources and is owned by `agent`; none of this is verified.
- `docker build` of the v2 judge image was not run. An equivalent installation was tested instead: the same artifact tar and `eval_lean.py` were placed over the original image paths, Lake rebuilt 0 modules, and the listing was byte-identical to the regenerated one.
- **Paired runs used the judge repo's prebuilt Mathlib (`491a409`).** The original `eval_cmd` copies `/home/workspace/baseline/.lake` (Mathlib `3203991`) and does a full rebuild; that path was not run.
- The style test covers one module (Section_4_1) and six variants. The hypothesis-dropped and duplicate counts are lexical lower bounds or estimates.
- Other false statements among the 2338 v2 targets were not checked; "two" is a lower bound.
- The v2 name filter is lexical. A user-named declaration ending in, for example, `eq_1` would also be excluded; all 560 matches in this baseline were checked and none is user-named.

## Reproduce

- Refutations: `evidence/scripts/lean_analysis_proofs/run_in_judge_image.sh` (runs `Refute.lean`; output `judge-repo-run.log`). Baseline dump: `evidence/scripts/lean_analysis_proofs/baseline-ListDeclAxiom.out`.
- Helper-name test: `evidence/scripts/lean_aux_names/` (`make_variants.py`, `check_variants.sh`, `run_eval.sh`, `summarize.py`; results in `results.txt`).
- Paired v1/v2: `repairs/lean_analysis_proofs-v2/paired/run_local.sh`; corrected-statement proofs in `paired/lean/EbvV2Proofs.lean`.
- Reviews: `evidence/reviews/lean_analysis_proofs.md`, `evidence/reviews/lean_aux_name_scoring.md`.
- Supporting records: `repairs/lean_analysis_proofs-v2/` (`README.md`, `paired/results.md`, `source-lock.json`).
