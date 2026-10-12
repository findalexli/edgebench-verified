/-
EdgeBench Verified -- graph_node_classification: prediction validation in `evaluate`,
original (v1) and fixed (v2) verifier.  Core Lean only (no Mathlib).

Code modelled
  judge image seededge/edgebench.judge.graph_node_classification@sha256:518c105ec283ea92...c3bd
  /home/workspace/045_graph_node_classification/verifier.py
    v1 sha256 044cd50e2e00187adbafc5d0b669af76589fa169578f6e290da39c233c40299e
    v2 sha256 32caddb12cc8684fce8104133dd07a9c53a9fff9a5be01022d92ff224580d998
  callers (unchanged): runner.py (sha256 2004a53f...5db) l.369-372 passes the solver's in-process
  `predictions`/`confidences` dicts; judge_eval.py (sha256 1a508d71...3e9) l.174-190 requires
  len(predictions) == len(ground_truth) per split.
Source-to-model mapping
  * `PyVal`       the Python value a solver may put in `predictions[nid]` (in-process object,
                  not JSON), classified by how the two conversions treat it
  * `toInt`       <- int(x) inside v1 _to_int_labels (l.7-14): failure = value DROPPED
  * `strict`      <- v2 _strict_class_id (v2 l.17-33): failure = ValueError (run invalid)
  * `origEval`    <- v1 evaluate l.84-100: ordered_ids = gt ids present in predictions;
                  y_true/y_pred via _to_int_labels; n = min(len); truncate both; conf_arr from
                  ordered_ids[:n]
  * `fixedEval`   <- v2 evaluate l.104-129: every gt id present (l.112-115), strict conversion
                  of every prediction (l.119), no truncation
  * `M`           the metric computation (_micro_f1, _macro_f1, _balanced_accuracy, _ece and
                  everything downstream); the identity theorem holds for EVERY M, so the metric
                  code need not be modelled.
Abstractions: ground-truth labels are integers (true for the shipped data; v2 l.116-118 rejects
otherwise); `predictions` is a dict, modelled as an association list looked up by first match
(dict keys are unique).  `str p ps`: p = int(s), ps = int(s.strip()).  `idx k`: an object whose
__index__ and __int__ both give k (e.g. numpy integers); `intOnly k`: __int__ but no __index__
(Decimal, Fraction).  Finite floats: `fint k` integral (incl. numpy float64), `fnon t`
non-integral with int() = t.
-/

namespace EbvGraph

inductive PyVal
  | int (k : Int) | bool (b : Bool) | fint (k : Int) | fnon (t : Int) | nan | inf
  | str (p ps : Option Int) | idx (k : Int) | intOnly (k : Int) | none_ | other
  deriving DecidableEq, Repr

/-- int(x): `none` = exception, so v1 drops the value. -/
def toInt : PyVal → Option Int
  | .int k => some k
  | .bool b => some (if b then 1 else 0)
  | .fint k => some k
  | .fnon t => some t
  | .nan => none
  | .inf => none
  | .str p _ => p
  | .idx k => some k
  | .intOnly k => some k
  | .none_ => none
  | .other => none

/-- v2 _strict_class_id: `none` = ValueError. -/
def strict : PyVal → Option Int
  | .int k => some k
  | .fint k => some k
  | .str _ ps => ps
  | .idx k => some k
  | _ => none

abbrev Pred := List (String × PyVal)

def look (pred : Pred) (id : String) : Option PyVal := (pred.find? (·.1 == id)).map (·.2)

def collect {α β : Type} (f : α → Option β) : List α → Option (List β)
  | [] => some []
  | x :: xs => match f x, collect f xs with
    | some y, some ys => some (y :: ys)
    | _, _ => none

variable {C R : Type}

/-- v1 evaluate. -/
def origEval (gt : List (String × Int)) (pred : Pred) (cf : String → C)
    (M : List Int → List Int → List C → R) : R :=
  let kept := gt.filter (fun p => (look pred p.1).isSome)
  let ids := kept.map (·.1)
  let yt := kept.map (·.2)
  let yp := ids.filterMap (fun id => (look pred id).bind toInt)
  let n := min yt.length yp.length
  M (yt.take n) (yp.take n) ((ids.take n).map cf)

/-- v2 evaluate: `none` = ValueError, which runner/judge_eval report as valid=false. -/
def fixedEval (gt : List (String × Int)) (pred : Pred) (cf : String → C)
    (M : List Int → List Int → List C → R) : Option R :=
  match collect (fun p => (look pred p.1).bind strict) gt with
  | some yp => some (M (gt.map (·.2)) yp ((gt.map (·.1)).map cf))
  | none => none

/-! ### V1: the fixed validation accepts exactly "one integer class id per test node" -/

theorem collect_isSome {α β : Type} (f : α → Option β) :
    ∀ l : List α, (collect f l).isSome = true ↔ ∀ x ∈ l, (f x).isSome = true
  | [] => by simp [collect]
  | x :: xs => by
    have ih := collect_isSome f xs
    simp only [collect, List.mem_cons, forall_eq_or_imp]
    cases hx : f x <;> cases hc : collect f xs <;> simp_all

theorem fixed_accepts_iff (gt : List (String × Int)) (pred : Pred) (cf : String → C)
    (M : List Int → List Int → List C → R) :
    (fixedEval gt pred cf M).isSome = true ↔
      ∀ p ∈ gt, ∃ v, look pred p.1 = some v ∧ (strict v).isSome = true := by
  have h := collect_isSome (fun p : String × Int => (look pred p.1).bind strict) gt
  have e : (fixedEval gt pred cf M).isSome = (collect (fun p => (look pred p.1).bind strict) gt).isSome := by
    unfold fixedEval; split <;> simp_all
  rw [e, h]
  constructor
  · intro H p hp
    have := H p hp
    cases hl : look pred p.1 with
    | none => simp [hl] at this
    | some v => exact ⟨v, rfl, by simpa [hl] using this⟩
  · intro H p hp
    obtain ⟨v, hv, hs⟩ := H p hp
    simp [hv, hs]

/-- What `strict` accepts, value class by value class. -/
theorem strict_accepts (v : PyVal) : (strict v).isSome = true ↔
    (∃ k, v = .int k) ∨ (∃ k, v = .fint k) ∨ (∃ p k, v = .str p (some k)) ∨ (∃ k, v = .idx k) := by
  cases v <;> simp [strict]
  rename_i p ps; cases ps <;> simp

/-! ### V2: on every accepted file, v1 and v2 compute the metrics on identical inputs -/

/-- int(s) and int(s.strip()) agree.  Fails only for strings padded with U+001C..U+001F
(see `separator_boundary`); checked exhaustively over all code points in the image's Python
3.11 (note). -/
def StrOK : PyVal → Prop
  | .str p ps => p = ps
  | _ => True

theorem strict_toInt (v : PyVal) (k : Int) (h : strict v = some k) (hs : StrOK v) :
    toInt v = some k := by
  cases v <;> simp_all [strict, toInt, StrOK]

theorem collect_spec (pred : Pred) :
    ∀ (gt : List (String × Int)) (yp : List Int),
      collect (fun p => (look pred p.1).bind strict) gt = some yp →
      (∀ p ∈ gt, ∀ v, look pred p.1 = some v → StrOK v) →
      gt.filter (fun p => (look pred p.1).isSome) = gt
      ∧ (gt.map (·.1)).filterMap (fun id => (look pred id).bind toInt) = yp
      ∧ yp.length = gt.length
  | [], yp, h, _ => by simp [collect] at h; subst h; simp
  | x :: xs, yp, h, hs => by
    simp only [collect] at h
    split at h
    · rename_i y ys hy hys
      cases h
      have ih := collect_spec pred xs ys hys (fun p hp => hs p (List.mem_cons_of_mem _ hp))
      cases hl : look pred x.1 with
      | none => simp [hl] at hy
      | some v =>
        have hsv : strict v = some y := by simpa [hl] using hy
        have hti := strict_toInt v y hsv (hs x (by simp) v hl)
        refine ⟨?_, ?_, ?_⟩
        · simp [List.filter_cons, hl, ih.1]
        · simp [List.map_cons, List.filterMap_cons, hl, hti, ih.2.1]
        · simp [ih.2.2]
    · cases h

theorem fixed_eq_orig (gt : List (String × Int)) (pred : Pred) (cf : String → C)
    (M : List Int → List Int → List C → R) (r : R)
    (hacc : fixedEval gt pred cf M = some r)
    (hs : ∀ p ∈ gt, ∀ v, look pred p.1 = some v → StrOK v) :
    origEval gt pred cf M = r := by
  unfold fixedEval at hacc
  split at hacc
  · rename_i yp hyp
    cases hacc
    obtain ⟨h1, h2, h3⟩ := collect_spec pred gt yp hyp hs
    unfold origEval
    have e1 : yp.take gt.length = yp := List.take_of_length_le (by omega)
    have e2 : (gt.map (·.1)).take gt.length = gt.map (·.1) := List.take_of_length_le (by simp)
    simp only [h1, h2, List.length_map, h3, Nat.min_self]
    have e3 : (gt.map (·.2)).take gt.length = gt.map (·.2) := List.take_of_length_le (by simp)
    rw [e1, e2, e3]
  · cases hacc

/-! ### Counter-checks: the original rule, and the boundary of V2 -/

/-- accuracy as (correct, scored) — enough to see what v1 scores. -/
def acc (yt yp : List Int) (_ : List Unit) : Nat × Nat :=
  ((yt.zip yp).countP (fun q => q.1 == q.2), yt.length)

def gt3 : List (String × Int) := [("a", 0), ("b", 1), ("c", 1)]
def x : PyVal := .str none none   -- the string "x"

/-- K1 (shrink): one correct prediction, the rest "x": v1 scores 1/1 = 100% accuracy on a
single node and the run stays valid; v2 rejects it. -/
theorem shrink : origEval gt3 [("a", .int 0), ("b", x), ("c", x)] (fun _ => ()) acc = (1, 1)
    ∧ fixedEval gt3 [("a", .int 0), ("b", x), ("c", x)] (fun _ => ()) acc = none := by decide

/-- K2 (misalignment): v1 does not score "the subset of nodes with valid predictions"; it
pairs the surviving predictions with the FIRST n labels.  Here node b's correct prediction 1
is scored against node a's label 0. -/
theorem misaligned : origEval [("a", 0), ("b", 1)] [("a", x), ("b", .int 1)] (fun _ => ()) acc
    = (0, 1) := by decide

/-- K3 (V2 needs StrOK): a string padded with U+001C fails int(s) but passes int(s.strip()):
v2 accepts and scores it, v1 dropped it, so the scores differ. -/
theorem separator_boundary :
    fixedEval [("a", 0), ("b", 1)] [("a", .str none (some 0)), ("b", .int 1)] (fun _ => ()) acc
      = some (2, 2)
    ∧ origEval [("a", 0), ("b", 1)] [("a", .str none (some 0)), ("b", .int 1)] (fun _ => ()) acc
      = (0, 1) := by decide

/-- K4: values v1 converted but v2 rejects (bool, non-integral float, __int__-only objects). -/
theorem v1_converts_v2_rejects :
    toInt (.bool true) = some 1 ∧ strict (.bool true) = none
    ∧ toInt (.fnon 2) = some 2 ∧ strict (.fnon 2) = none
    ∧ toInt (.intOnly 3) = some 3 ∧ strict (.intOnly 3) = none := by decide

/-! ### Best-of-k selection turns variance into expected gain (selection `valid_then_score`)

A finite distribution is a list of (weight, value) with natural weights (probability =
weight / total).  If the run's kept score is the maximum over valid submissions and the current
best is `c`, adding one more submission with random score X gives expected kept score
E[max(c, X)].  -/

def wsum : List (Nat × Int) → Int
  | [] => 0
  | (w, _) :: xs => (w : Int) + wsum xs

/-- total · E[max(c, X)] -/
def emax (c : Int) : List (Nat × Int) → Int
  | [] => 0
  | (w, v) :: xs => (w : Int) * max c v + emax c xs

/-- total · E[X] -/
def emean : List (Nat × Int) → Int
  | [] => 0
  | (w, v) :: xs => (w : Int) * v + emean xs

/-- E[max(c, X)] ≥ c and ≥ E[X], for every distribution. -/
theorem emax_ge (c : Int) : ∀ d : List (Nat × Int), wsum d * c ≤ emax c d ∧ emean d ≤ emax c d
  | [] => by simp [wsum, emax, emean]
  | (w, v) :: xs => by
    obtain ⟨ih1, ih2⟩ := emax_ge c xs
    have hw : (0 : Int) ≤ w := Int.natCast_nonneg w
    have a1 : (w : Int) * c ≤ w * max c v := Int.mul_le_mul_of_nonneg_left (Int.le_max_left c v) hw
    have a2 : (w : Int) * v ≤ w * max c v := Int.mul_le_mul_of_nonneg_left (Int.le_max_right c v) hw
    simp only [wsum, emax, emean, Int.add_mul]
    constructor <;> omega

/-- Strict gain: if X beats the current best with positive probability, the expected kept
score is strictly above c -- whatever E[X] is (even E[X] < c). -/
theorem emax_gt (c : Int) : ∀ d : List (Nat × Int), (∃ w v, (w, v) ∈ d ∧ 0 < w ∧ c < v) →
    wsum d * c < emax c d
  | [], h => by simp at h
  | (w, v) :: xs, h => by
    have hw : (0 : Int) ≤ w := Int.natCast_nonneg w
    have a1 : (w : Int) * c ≤ w * max c v := Int.mul_le_mul_of_nonneg_left (Int.le_max_left c v) hw
    have ih1 := (emax_ge c xs).1
    simp only [wsum, emax, Int.add_mul]
    obtain ⟨w', v', hm, hw', hv'⟩ := h
    simp only [List.mem_cons, Prod.mk.injEq] at hm
    rcases hm with ⟨rfl, rfl⟩ | hm
    · have hwpos : (0 : Int) < w' := by omega
      have : (w' : Int) * c < w' * max c v' := by
        apply Int.mul_lt_mul_of_pos_left _ hwpos
        omega
      omega
    · have := emax_gt c xs ⟨w', v', hm, hw', hv'⟩
      omega

/-- Two independent outcomes: E[max(X, Y)] ≥ max(E[X], E[Y]) (Y = a constant is the case
above; here X is fixed at one value per branch and Y is a distribution). -/
theorem two_outcomes (x : Int) (d : List (Nat × Int)) :
    max (wsum d * x) (emean d) ≤ emax x d := by
  have := emax_ge x d; omega

/-- Illustration (not a measurement): honest run kept at 333/1000; a shrink-style submission
scores (number of the 10 splits whose single scored node is guessed right)/10, each split right
with probability 1/4 (weights C(10,k)·3^(10-k), total 4^10).  Its mean is 250 < 333, yet
keeping the best raises the expected kept score to about 358/1000. -/
def binom10 : List (Nat × Int) :=
  [(59049, 0), (196830, 100), (295245, 200), (262440, 300), (153090, 400), (61236, 500),
   (17010, 600), (3240, 700), (405, 800), (30, 900), (1, 1000)]

theorem illustration :
    wsum binom10 = 1048576 ∧ emean binom10 = 1048576 * 250
    ∧ emax 333 binom10 = 375596812 ∧ wsum binom10 * 333 < emax 333 binom10 := by decide

end EbvGraph

#print axioms EbvGraph.fixed_accepts_iff
#print axioms EbvGraph.strict_accepts
#print axioms EbvGraph.fixed_eq_orig
#print axioms EbvGraph.shrink
#print axioms EbvGraph.misaligned
#print axioms EbvGraph.separator_boundary
#print axioms EbvGraph.v1_converts_v2_rejects
#print axioms EbvGraph.emax_ge
#print axioms EbvGraph.emax_gt
#print axioms EbvGraph.two_outcomes
#print axioms EbvGraph.illustration
