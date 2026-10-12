# Review: how lean_analysis_proofs scores compiler-generated auxiliary targets

## Question

`eval_lean.py` treats every declaration in the baseline `ListDeclAxiom` output that depends on
`sorryAx` as one target worth 1 point. 2901 targets qualify, and many are compiler-generated
auxiliary names (`X._proof_N`, `X._simp_N`, `X.eq_N`, `X.match_N`, ...). If a solver honestly
proves the parent, does the unmodified grader give credit for these auxiliary targets? If some are
lost, how much of the maximum score can a fully honest, complete solution never reach?

This review covers only good-faith solver fairness. No tampering or exploit submissions were built.

## Pinned artifacts

- Judge image: `seededge/edgebench.judge.lean_analysis_proofs@sha256:41ece9c40d197540af701c6a9bd592101126708c3f3c46e8f6b0da531597513b`.
  It was already local and not pulled. Every run used one container at a time with
  `--rm --network none --memory 4g --cpus 2`. No containers were left behind.
- In-image grader files, hashed at runtime (`scripts/lean_aux_names/out/hashes.txt`):
  - `eval_lean.py`: `3319767e470e165395bf9538db1d7d1fabf01c94eb1f0b43ceca0281d35acc29`.
  - `ListDeclAxiom.lean`: `af482b7af56a231f1b18400ecb7922fa96016bb9b5407f81526c822f677dfdf1`.
  - `Analysis/Section_4_1.lean`: `72d9935ea0cd42d7c6673aeb9eb24f63e3e46d7f687fb37f7c9e5bbd291bb1f1`.
- Baseline dump: `scripts/lean_analysis_proofs/baseline-ListDeclAxiom.out`, with 2901 BAD+sorryAx targets.
- Variant sources: `scripts/lean_aux_names/Section_4_1.{T,S,U,W,X}.lean`, built by `make_variants.py`.
  Their sha256 values are listed in `results.txt` and in the table below.

## Grader behaviour (eval_lean.py L540-640, read from the source)

- Targets are the names that are BAD and use `sorryAx` in the baseline. The baseline type text is
  stored for each one.
- **Denominator:** the total baseline weight, 2901, fixed. Targets that are missing from the
  submission's output (`disappeared`) and targets whose printed type differs (`type_changed`) stay in
  the denominator and score 0. There is no further penalty, and nothing is renormalized.
- **Credit:** a target scores only if the same *name* is OK and its printed type text equals the
  baseline text exactly.
- New declarations are never credited. New OK names are ignored, and new BAD names are listed with
  weight 0.
- Consequence: an auxiliary target can be earned only if the honest build produces an auxiliary
  lemma with the **same generated name and the same pretty-printed type**.

## Static census of the baseline (scripts: classify_baseline.py, WhereAux.lean / run_where.sh)

**How many targets are auxiliary.** 559 of the 2901 targets are auxiliary names:

| kind | count |
|---|---|
| `_proof_N` | 439 |
| `_simp_N` | 101 |
| `eq_N` | 9 |
| `congr_simp` | 4 |
| `match_N` | 3 |
| `_sunfold` | 1 |
| `_unsafe_rec` | 1 |
| `_sizeOf_N` | 1 |

The earlier figures of ≈544 and 569 come from different name regexes. The parent of every
auxiliary target is itself a target. Running in the image shows the parent kinds are 466 `def`
(instances or structures with proof fields), 92 `theorem` (91 of them are `_simp_N` lemmas
generated for `@[simp]` iff-lemmas) and 1 inductive.

There are three structural classes of unattainable or fragile auxiliary targets.

**A. The baseline type text contains `sorry`.** There are 35 such targets: 32 auxiliary and 3 main.
- The auxiliary ones are proof obligations stated over a data hole. Examples are
  `Function.LeftInverse sorry P.natCast` and `{ toFun := …, invFun := sorry, … } … = …`.
- The 3 main ones (`Chapter3.empty_function_{bijective,onto,one_to_one}_iff : … ↔ sorry`) have
  statement placeholders that the solver is supposed to fill in.
- Any sorry-free solution changes this text, so these targets can only end as "type changed" or
  "still bad". List: `sorry_type_targets.txt`.

**B. The hypothesis is dropped, so the type is false.** There are 12 such targets.
- A `sorry` inside a case branch does not use the case hypothesis. The abstracted auxiliary lemma
  therefore omits that hypothesis.
- The baseline then contains pairs such as `Int.decidableRel._proof_2 : ∀ a b c d, a —— b ≤ c —— d`
  and `_proof_1 : ∀ a b c d, ¬ a —— b ≤ c —— d`. The same happens in `Chapter2.Nat.decLe` (6 targets)
  and `Section_4_2.Rat.decidableRel` (4).
- A real proof must use the hypothesis, which changes the type.
- `contradictory_aux.py` detects these as literal P / ¬P pairs, so 12 is a lower bound for this class.

**C. Duplicate copies.** There are 13 such targets.
- In 11 cases one parent has several `_proof_N` targets with identical type text. These are copies
  of the same sorried obligation.
- Once the obligation is proved, Lean may produce one deduplicated auxiliary lemma instead of
  several (observed natively below).
- I list these as likely lost, not proven lost. Script: `dup_aux.py`.

## Native reproduction (unmodified grader, judge image)

**Setup.** `run_eval.sh` builds a submission repo at the `eval_cmd` path
`/home/workspace/se-bmk-intern/analysis`:
- It is a copy of the judge baseline repo, with the same sources and oleans and the Mathlib
  packages symlinked.
- `Analysis/Section_4_1.lean` is replaced by a variant. This module is a leaf, so only it and its
  dependents rebuild.

The script then runs the original steps from `eval_cmd`:

```
lake build
cp $J/ListDeclAxiom.lean $SUB/
cd /home/workspace/judge/se-bmk-intern
python3 eval_lean.py --baseline-repo $J --current-repo $SUB
```

**Deviation.** I skipped `cp -r /home/workspace/baseline/.lake` and the manifest copy. That step
swaps in Mathlib `3203991…` and forces a full rebuild of the Analysis tree. Here the build used
the judge repo's Mathlib `491a409…`. Scoring logic and helper are byte-identical to the image's.

**Commands:**

```
cd evidence/scripts/lean_aux_names
python3 -I make_variants.py Section_4_1.orig.lean
CHECK="T S X" ./check_variants.sh                     # elaboration check, no errors
./run_eval.sh                                       # VARIANTS="orig T S" (default)
VARIANTS=U ./run_eval.sh; VARIANTS=W ./run_eval.sh; VARIANTS=X ./run_eval.sh
python3 -I summarize.py orig T S U W X; python3 -I passed_sets.py T S U W X
```

Outputs are in `results.txt`, `out/report_*.json.gz` (the full structured grader output), and
`out/listdecl_S41_*.txt` (the raw OK/BAD lines for Section_4_1).

**Honest proofs used.** All of them are sorry-free, use only the standard axioms, and leave every
signature unchanged:
- `PreInt.instSetoid` refl/symm.
- `PreInt.eq`, `Int.eq`, `Int.natCast_inj`, `Int.ofNat_inj`.
- `Int.equivInt`: the toFun congruence proof, `invFun n := n.toNat —— (-n).toNat`, and left_inv/right_inv.
- In X only, the two `Int.decidableRel` holes.

| variant | style | score | repaired | type_changed | disappeared |
|---|---|---|---|---|---|
| orig (control) | starter unchanged | 0 | 0/2901 | 0 | 0 |
| T `3c7b39d1…` | term mode (`Iff.rfl`, `fun _ => rfl`, `⟨…, …⟩`); equivInt via `omega` | 26/2901 | 26 | 4 | 0 |
| S `c00db26b…` | tactic mode (`constructor`, `rw`, `omega`) | 26/2901 | 26 (same set as T) | 4 | 0 |
| U `ea9f1cd2…` | as T, but the equivInt congruence proved without omega; inverse laws left as sorry | 25/2901 | 25 | 3 | 1 |
| W `852fa9dd…` | as T, but setoid refl/symm closed by `omega` | 25/2901 | 25 | 5 | 0 |
| X `878e14c8…` | as T, plus the `Int.decidableRel` holes proved | 28/2901 | 28 | 7 | 0 |

**Per-target outcomes**, for the auxiliary targets of the parents I completed:

- **Earned in every style.** `PreInt.eq._simp_1`, `Int.natCast_inj._simp_1`,
  `Int.ofNat_inj._simp_1`, `Int.instAdd._proof_1`, `Int.instAdd._simp_1` and
  `Int.decidableEq._proof_1/_2` were PASSED together with their parents.
  - `@[simp]` `_simp_N` auxiliaries, and auxiliaries of instances whose own proofs were already
    written, are stable.
  - Auxiliaries can also earn points while the parent stays BAD: `Int.instCommRing._proof_8/_9`,
    and in X `Int.instLinearOrder._proof_6/_7`.
- **Lost depending on style:** `PreInt.instSetoid._proof_1` (`Equivalence …`).
  - It is PASSED in T, S and X.
  - In W, `omega` emits its own auxiliaries first (`instSetoid._proof_1 : ∀ x, ¬… → False`,
    `_proof_2`). The original obligation moves to `_proof_3`, so the target is "type changed".
  - The two proofs are equally correct, but the W proof scores 1 point less.
- **Lost in every style tried:** `Int.equivInt._proof_1.._4` (T, S, W, X: all type changed; U: 3
  type changed and 1 disappeared).
  - `_proof_3/_4` are class A, with `sorry` in the type.
  - `_proof_1/_2` have sorry-free types. With omega (T, S) they are renumbered: omega's lemmas
    come first, and the congruence proof lands at `_proof_4`.
  - Without omega (U) the two baseline copies collapse into one `_proof_1`. Its printed binders
    are `∀ (h : PreInt) (b : PreInt)` instead of the baseline's `∀ (a b : PreInt)`, so even this
    does not match.
  - The parent `Int.equivInt` is PASSED (T, S, W, X).
- **Lost because the typed statement is false (class B):** `Int.decidableRel._proof_1/_2`.
  - In X their current types include the case hypothesis, for example
    `∀ a b c d, a + d ≤ b + c → ¬… → False`.
  - Also in X, the previously earned `Int.decidableRel._proof_4` (`Subsingleton …`) was
    renumbered to `_proof_6` and lost.
  - So filling the two remaining holes honestly gained the parent (+1) and two unrelated
    `instLinearOrder` auxiliaries, but lost a point already earned. The net change was +2 rather than +3.

**Summary of the native sample.** I completed 8 parents carrying 15 auxiliary targets
(instSetoid 1, PreInt.eq 1, natCast_inj 1, ofNat_inj 1, instAdd 2, decidableEq 2, decidableRel 3,
equivInt 4):
- Every parent proved honestly earned its own point.
- The best honest variant (X) earned 8 of the 15 auxiliary targets.
- 7 were lost: 2 class A, 2 class B, and 3 through renumbering, deduplication or binder names.
- Which auxiliaries are earned depends on tactic choice (W vs T).

## Effect on the attainable maximum (exact fractions, `attainability.py`, `union.py`)

| set unattainable for a complete honest solution | targets lost | ceiling |
|---|---|---|
| A (sorry in type) | 35 | 2866/2901 = 98.79% |
| A + B (lower bound) + the 2 false main statements (`reviews/lean_analysis_proofs.md`) | 49 | **2852/2901 = 98.31%** |
| + C duplicate copies + the observed `equivInt._proof_1` (probable) | 57 | 2844/2901 = 98.04% |
| worst case: every def-parent auxiliary is exposed to renumbering, plus the 3 sorry-typed main + 2 false | 471 | 2430/2901 = 83.76% |

The established, natively supported figure is that **at least 49 of 2901 points (1.69%) are
unattainable** for a fully honest, complete solution. About 57 (1.96%) is the likely figure.
Beyond that, up to 466 def-parent auxiliary points (16%) can be won or lost depending on proof
style, through renumbering, deduplication and printed binder names. The native sample suggests
this effect is real but partial: 3 of 15 sampled auxiliaries were lost this way, so the true size
lies somewhere between the last two rows. I did not measure it across the whole repository.

## Verdict

**CONFIRMED, as a material good-faith scoring defect, but bounded.**
- The grader keys auxiliary targets by generated name plus printed type text. Neither is part of
  the task contract.
- Honest, correct proofs of a parent can leave its auxiliary targets unearnable:
  - the type contains `sorry`;
  - the type omits a hypothesis and is false;
  - the target is renumbered or deduplicated;
  - the printed binders differ.
- They are then scored as `type changed` or `disappeared`, and they stay in the denominator.
- The earlier claim (`_lean-formalization-tasks.md`) that "If a correct proof removes or renames
  one, that target is counted `disappeared` and scores 0" is **slightly inaccurate**. Natively,
  renaming mostly shows up as **`type changed`**, because the old name is reused for a different
  lemma. `disappeared` occurs only when the count of auxiliaries shrinks (variant U).
- The size of the effect is a hard ceiling of at least 1.7% and probably about 2%, plus
  style-dependent noise of up to about 16%. That is larger than the 0.07% ceiling from the two
  false statements, and it adds variance that has nothing to do with mathematical progress. It
  matters for rankings between strong solvers. It does not make low or mid-range partial-credit
  scores meaningless: honest parents always earned their own point, and most stable auxiliaries
  (`_simp_N`, pre-proved instance fields) were earned.

## Repair note

- **Smallest correct fix.** Drop compiler-generated names from the target set and score only
  user-facing declarations, for example by excluding names with a component that starts with `_`,
  `match_N`, `eq_N`, `congr_simp` or `proof_N`. This is the earlier recommendation item 5.
  - The parent's transitive axiom check already covers its auxiliaries, so no soundness is lost.
  - The denominator becomes about 2342 (2901 − 559).
- **Separately**, the 3 main targets whose statement contains `sorry` need a decision. Either
  score them by the axiom check alone (accepting any filled statement, which is risky because a
  solver could fill in a trivial answer), or exclude them.
- A weighted-mode weights file that omits the auxiliaries is a zero-code alternative.

## Limits

- The native test covers one leaf module (Section_4_1, 116 targets) and 6 variants. Class B and C
  counts are lexical lower bounds or estimates from the baseline dump. Only the Int instances
  (decidableRel, equivInt) were confirmed natively.
- The build used the judge repo's Mathlib (`491a409…`), not the baseline `.lake` Mathlib
  (`3203991…`) that `eval_cmd` copies in. The same Lean 4.28.0 and the same grader files were used.
  Auxiliary naming is a Lean elaborator behaviour, so I expect the same results, but this was not
  rerun under `3203991…`.
- I did not verify that the work-image starter equals the judge baseline sources (the work image
  was not pulled).
- I did not search for a proof style that would recover `equivInt._proof_1/_2` (for example
  matching binder names and avoiding deduplication). They were not recovered in any of the 4 styles
  tried. Recovering them would require shaping proofs around the grader, not around mathematics.
