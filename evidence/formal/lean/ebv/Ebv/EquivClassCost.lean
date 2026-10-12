/-
EdgeBench Verified -- equivalence_class_divide_and_conquer, sub-problem T3 (P8204) checker.

Source modelled (ORIGINAL):
  image  seededge/edgebench.judge.equivalence_class_divide_and_conquer@sha256:f793d805d7e2adcec68355343230db3ea15b1010a98678850d2fe89e9ba767e6
  path   /opt/p2_judge/prob/P2/T3_P8204/data/checker.cpp
  sha256 f92b52cc37615e28e906d461cf9607ad42e8ea7bdac2a56fd215fc070edd4145 (2054 bytes)
Source modelled (FIXED, v2): same path after repairs/equivalence_class_divide_and_conquer-v2/repair.patch,
  sha256 14734cf3d870a92d12175398531cef7e3291e8049d9251358dbad17f0d7f299e (2059 bytes)

Source-to-model mapping (line numbers of the original file; the fix only edits lines 41-42):
  * line 8   `const long long W = 2.5e9`                         -> `W`
  * line 14  a state t = (x, y); t[0] is zero-initialised (x=0, y=0=d[0]), i.e. the empty
             neighbourhood, so its size is 0                     -> `init.sz 0 = 0`
  * line 32-33 op 2: `ensuref(tp--, ...)` rejects when tp = 0, else pops
                                                                  -> `step _ .revoke`
  * line 34-36 op 3 (mark): only legality checks, no cost        -> `step _ .mark`
  * line 37-38 op 1: `t[++tt].read(...)`, legality check, then
             `ct[st[tp]]--, ct[st[++tp]=tt]++`                   -> `step _ (.expand s)`
  * line 39  "every query marked" check: a legality check shared verbatim by both versions
  * line 40-43 the cost sum.  For each index k in `oq[0 .. tt-1]` (original, line 41-42) or
             `oq[0 .. tt]` (fixed) the loop adds `ct[k] * (qr(ot[x])-qr(in[x]))`.  The BIT
             difference is |N(t[k])|, the size of state k; the BIT/two-pointer machinery is the
             same code in both versions and is abstracted as the value `sz k` carried by the
             state (it is recorded when the state is created).  `oq` is `iota` then `sort`, so
             it is some permutation of `0..tt-1` (resp. `0..tt`)  -> `checkerSum`, with
             theorems `checkerSum_orig` / `checkerSum_fixed` for EVERY such permutation.
  * line 44  `ensuref(w <= W, ...)`                               -> `origAccepts`/`fixedAccepts`
The statement's cost ("true cost"): op 1 costs |new| - |current top|; ops 2, 3 are free.
The model accumulates this independently in the field `cost` (it is not read from `ct`).
-/

namespace EbvEquivClass

/-- Output operations.  `expand s`: op 1 to a new state whose neighbourhood has size `s`. -/
inductive Op
  | expand (size : Nat)
  | revoke
  | mark

structure St where
  tt : Nat               -- number of states created by op 1 (C++ `tt`)
  stack : List Nat       -- `st[0..tp]`, head = top `st[tp]`
  ct : Nat → Int         -- `ct[]`
  sz : Nat → Int         -- |N(t[k])|
  cost : Int             -- true cost per the statement (ghost, independent of `ct`)

def init : St := ⟨0, [0], fun _ => 0, fun _ => 0, 0⟩

def step (s : St) : Op → Option St
  | .expand n =>
    match s.stack with
    | [] => none
    | cur :: _ => some
        { tt := s.tt + 1
          stack := (s.tt + 1) :: s.stack
          ct := fun k => if k = s.tt + 1 then s.ct k + 1 else if k = cur then s.ct k - 1 else s.ct k
          sz := fun k => if k = s.tt + 1 then (n : Int) else s.sz k
          cost := s.cost + ((n : Int) - s.sz cur) }
  | .revoke =>
    match s.stack with
    | _ :: b :: rest => some { s with stack := b :: rest }
    | _ => none
  | .mark => some s

def runFrom : St → List Op → Option St
  | s, [] => some s
  | s, o :: os => match step s o with
    | none => none
    | some s' => runFrom s' os

def run (ops : List Op) : Option St := runFrom init ops

/-- `Σ_{k < n} f k` -/
def sumTo (f : Nat → Int) : Nat → Int
  | 0 => 0
  | n + 1 => sumTo f n + f n

def term (s : St) (k : Nat) : Int := s.ct k * s.sz k

/-- What the C++ loop accumulates into `w` for an index list `oq`. -/
def checkerSum (s : St) (oq : List Nat) : Int := (oq.map (term s)).sum

def origCounted (s : St) : Int := sumTo (term s) s.tt          -- indices 0..tt-1
def fixedCounted (s : St) : Int := sumTo (term s) (s.tt + 1)   -- indices 0..tt

/-- |N_last|: size of t[tt], the target of the last op 1 (0 when there is no op 1). -/
def nLast (s : St) : Int := if s.tt = 0 then 0 else s.sz s.tt

def W : Int := 2500000000
def origAccepts (s : St) : Prop := origCounted s ≤ W
def fixedAccepts (s : St) : Prop := fixedCounted s ≤ W

/-! ### The sort: any permutation of the index range gives the same sum -/

theorem sum_perm {l₁ l₂ : List Int} (h : l₁.Perm l₂) : l₁.sum = l₂.sum := by
  induction h with
  | nil => rfl
  | cons x _ ih => simp [List.sum_cons, ih]
  | swap x y l => simp [List.sum_cons]; omega
  | trans _ _ ih₁ ih₂ => exact ih₁.trans ih₂

theorem range_sum (f : Nat → Int) (n : Nat) : ((List.range n).map f).sum = sumTo f n := by
  induction n with
  | zero => rfl
  | succ n ih => simp [List.range_succ, List.sum_append, ih, sumTo]

theorem checkerSum_perm (s : St) (oq : List Nat) (n : Nat) (h : oq.Perm (List.range n)) :
    checkerSum s oq = sumTo (term s) n := by
  unfold checkerSum; rw [sum_perm (h.map _), range_sum]

/-- Original loop (`oq[0..tt-1]`, `i<tt`), for every order `std::sort` may produce. -/
theorem checkerSum_orig (s : St) (oq : List Nat) (h : oq.Perm (List.range s.tt)) :
    checkerSum s oq = origCounted s := checkerSum_perm s oq _ h

/-- Fixed loop (`oq[0..tt]`, `i<=tt`), for every order `std::sort` may produce. -/
theorem checkerSum_fixed (s : St) (oq : List Nat) (h : oq.Perm (List.range (s.tt + 1))) :
    checkerSum s oq = fixedCounted s := checkerSum_perm s oq _ h

/-! ### Invariant of every reachable state -/

structure Inv (s : St) : Prop where
  stack_ne : s.stack ≠ []
  stack_le : ∀ k ∈ s.stack, k ≤ s.tt
  ct_above : ∀ k, s.tt < k → s.ct k = 0
  ct_last : s.ct s.tt = if s.tt = 0 then 0 else 1
  sz_nonneg : ∀ k, 0 ≤ s.sz k
  cost_eq : s.cost = sumTo (term s) (s.tt + 1)

theorem sumTo_congr (f g : Nat → Int) (n : Nat) (h : ∀ k, k < n → f k = g k) :
    sumTo f n = sumTo g n := by
  induction n with
  | zero => rfl
  | succ n ih =>
    simp only [sumTo]
    rw [ih (fun k hk => h k (by omega)), h n (by omega)]

/-- Changing one term `c < n` by `d` changes the sum by `d`. -/
theorem sumTo_bump (f : Nat → Int) (c : Nat) (d : Int) (n : Nat) (hc : c < n) :
    sumTo (fun k => if k = c then f k + d else f k) n = sumTo f n + d := by
  induction n with
  | zero => omega
  | succ n ih =>
    simp only [sumTo]
    by_cases hcn : c = n
    · subst hcn
      rw [sumTo_congr _ f c (fun k hk => by simp [show k ≠ c by omega])]
      simp; omega
    · rw [ih (by omega)]; simp [show n ≠ c from fun h => hcn h.symm]; omega

theorem inv_init : Inv init where
  stack_ne := by simp [init]
  stack_le := by simp [init]
  ct_above := by simp [init]
  ct_last := by simp [init]
  sz_nonneg := by simp [init]
  cost_eq := by simp [init, sumTo, term]

theorem inv_step (s s' : St) (o : Op) (hi : Inv s) (h : step s o = some s') : Inv s' := by
  cases o with
  | mark => simp [step] at h; subst h; exact hi
  | revoke =>
    unfold step at h
    match hs : s.stack, h with
    | _ :: b :: rest, h =>
      simp at h; subst h
      exact { stack_ne := by simp
              stack_le := fun k hk => hi.stack_le k (by rw [hs]; exact List.mem_cons_of_mem _ hk)
              ct_above := hi.ct_above, ct_last := hi.ct_last,
              sz_nonneg := hi.sz_nonneg, cost_eq := hi.cost_eq }
  | expand n =>
    unfold step at h
    match hs : s.stack, h with
    | cur :: tl, h =>
      simp only [Option.some.injEq] at h; subst h
      have hcur : cur ≤ s.tt := hi.stack_le cur (by rw [hs]; simp)
      refine ⟨by simp, ?_, ?_, ?_, ?_, ?_⟩
      · intro k hk
        dsimp only at hk ⊢
        rcases List.mem_cons.1 hk with hk | hk
        · omega
        · have := hi.stack_le k (by rw [hs]; exact hk); omega
      · intro k hk
        dsimp only at hk ⊢
        simp [show k ≠ s.tt + 1 by omega, show k ≠ cur by omega, hi.ct_above k (by omega)]
      · dsimp only
        simp [hi.ct_above (s.tt + 1) (by omega)]
      · intro k; dsimp only; split
        · omega
        · exact hi.sz_nonneg k
      · -- new cost = old cost - |cur| + n; the new sum loses |cur| at index cur, gains n at tt+1
        dsimp only
        have e : ∀ f : Nat → Int, sumTo f (s.tt + 1 + 1) = sumTo f (s.tt + 1) + f (s.tt + 1) :=
          fun _ => rfl
        rw [e, sumTo_congr (term _)
            (fun k => if k = cur then term s k + (- s.sz cur) else term s k) (s.tt + 1) ?hh,
          sumTo_bump _ _ _ _ (by omega), ← hi.cost_eq]
        · simp [term, hi.ct_above (s.tt + 1) (by omega)]
          omega
        · intro k hk
          by_cases hkc : k = cur
          · subst hkc
            simp [term, show k ≠ s.tt + 1 by omega]
            rw [Int.sub_mul, Int.one_mul, Int.sub_eq_add_neg]
          · simp [term, show k ≠ s.tt + 1 by omega, hkc]

theorem inv_runFrom (s s' : St) (ops : List Op) (hi : Inv s) (h : runFrom s ops = some s') :
    Inv s' := by
  induction ops generalizing s with
  | nil => simp [runFrom] at h; subst h; exact hi
  | cons o os ih =>
    unfold runFrom at h
    match hs : step s o, h with
    | some t, h => simp at h; exact ih t (inv_step s t o hi hs) h

theorem inv_run (ops : List Op) (s : St) (h : run ops = some s) : Inv s :=
  inv_runFrom init s ops inv_init h

/-! ### (i), (ii): counted cost vs true cost -/

/-- (ii) The fixed checker counts exactly the true cost. -/
theorem fixed_counts_true (ops : List Op) (s : St) (h : run ops = some s) :
    fixedCounted s = s.cost := (inv_run ops s h).cost_eq.symm

/-- (i) The original checker counts the true cost minus |N_last|. -/
theorem orig_counts_true_minus_last (ops : List Op) (s : St) (h : run ops = some s) :
    origCounted s = s.cost - nLast s := by
  have hi := inv_run ops s h
  rw [hi.cost_eq]; simp only [sumTo, origCounted, nLast, term]
  rw [hi.ct_last]; split <;> simp

theorem nLast_nonneg (ops : List Op) (s : St) (h : run ops = some s) : 0 ≤ nLast s := by
  have hi := inv_run ops s h; unfold nLast; split
  · exact Int.le_refl 0
  · exact hi.sz_nonneg _

/-! ### (iii) verdicts -/

/-- The fixed checker satisfies the statement's contract: accept iff true cost ≤ W. -/
theorem fixed_contract (ops : List Op) (s : St) (h : run ops = some s) :
    fixedAccepts s ↔ s.cost ≤ W := by
  unfold fixedAccepts; rw [fixed_counts_true ops s h]

theorem orig_accepts_iff (ops : List Op) (s : St) (h : run ops = some s) :
    origAccepts s ↔ s.cost ≤ W + nLast s := by
  unfold origAccepts; rw [orig_counts_true_minus_last ops s h]; omega

theorem agree_below (ops : List Op) (s : St) (h : run ops = some s) (hc : s.cost ≤ W) :
    origAccepts s ∧ fixedAccepts s := by
  rw [orig_accepts_iff ops s h, fixed_contract ops s h]
  have := nLast_nonneg ops s h; omega

theorem agree_above (ops : List Op) (s : St) (h : run ops = some s) (hc : W + nLast s < s.cost) :
    ¬ origAccepts s ∧ ¬ fixedAccepts s := by
  rw [orig_accepts_iff ops s h, fixed_contract ops s h]
  have := nLast_nonneg ops s h; omega

/-- The verdicts differ exactly in the window (W, W + |N_last|]; there the original accepts
and the fixed checker rejects. -/
theorem differ_iff_window (ops : List Op) (s : St) (h : run ops = some s) :
    (origAccepts s ∧ ¬ fixedAccepts s) ↔ (W < s.cost ∧ s.cost ≤ W + nLast s) := by
  rw [orig_accepts_iff ops s h, fixed_contract ops s h]; omega

theorem never_fixed_only (ops : List Op) (s : St) (h : run ops = some s) :
    ¬ (fixedAccepts s ∧ ¬ origAccepts s) := by
  rw [orig_accepts_iff ops s h, fixed_contract ops s h]
  have := nLast_nonneg ops s h; omega

/-- Weaker but true: agreement for every true cost ≤ W - |N_last|. -/
theorem agree_below_weak (ops : List Op) (s : St) (h : run ops = some s)
    (hc : s.cost ≤ W - nLast s) : (origAccepts s ↔ fixedAccepts s) := by
  have := nLast_nonneg ops s h
  have ⟨a, b⟩ := agree_below ops s h (by omega)
  exact ⟨fun _ => b, fun _ => a⟩

/-! ### Concrete runs: the crafted cases of evidence/scripts/equivalence_class_divide_and_conquer
(gen_crafted.py; observed results in run_crafted_output.txt).  Star, n = 10^6; each query
uses op 1 "1 1 2" (empty -> whole tree, size 10^6), "3 i", "2". -/

def roundOps (n : Nat) : List Op := [.expand n, .mark, .revoke]
def rounds (n : Nat) : Nat → List Op
  | 0 => []
  | k + 1 => rounds n k ++ roundOps n

theorem runFrom_append (s : St) (a b : List Op) :
    runFrom s (a ++ b) = (runFrom s a).bind (fun t => runFrom t b) := by
  induction a generalizing s with
  | nil => simp [runFrom]
  | cons o os ih =>
    simp only [List.cons_append, runFrom]
    cases step s o with
    | none => rfl
    | some t => exact ih t

theorem run_rounds (n k : Nat) : ∃ s, run (rounds n k) = some s ∧ s.stack = [0] ∧ s.tt = k ∧
    s.cost = k * n ∧ s.sz 0 = 0 ∧ (k ≠ 0 → s.sz k = n) := by
  induction k with
  | zero => exact ⟨init, rfl, rfl, rfl, by simp [init], rfl, by simp⟩
  | succ k ih =>
    obtain ⟨s, hs, hst, htt, hc, hz, _⟩ := ih
    refine ⟨{ tt := s.tt + 1, stack := [0],
              ct := fun j => if j = s.tt + 1 then s.ct j + 1 else if j = 0 then s.ct j - 1 else s.ct j,
              sz := fun j => if j = s.tt + 1 then (n : Int) else s.sz j,
              cost := s.cost + ((n : Int) - s.sz 0) }, ?_, rfl, by simp [htt], ?_, ?_, ?_⟩
    · simp only [run, rounds, runFrom_append] at hs ⊢
      rw [hs]; simp [roundOps, runFrom, step, hst]
    · simp [hc, hz]; push_cast; rw [Int.add_mul]; omega
    · simp [hz]
    · intro _; simp [htt]

theorem crafted_rounds (k : Nat) (hk : k ≠ 0) : ∃ s, run (rounds 1000000 k) = some s ∧
    s.cost = (k : Int) * 1000000 ∧ nLast s = 1000000 ∧
    (origAccepts s ↔ (k : Int) * 1000000 ≤ W + 1000000) ∧
    (fixedAccepts s ↔ (k : Int) * 1000000 ≤ W) := by
  obtain ⟨s, hs, _, htt, hc, _, hl⟩ := run_rounds 1000000 k
  have hn : nLast s = 1000000 := by
    unfold nLast; rw [ite_eq_right_of_eq_false _ _ (by simp; omega), htt, hl hk]; rfl
  refine ⟨s, hs, by rw [hc]; rfl, hn, ?_, ?_⟩
  · rw [orig_accepts_iff _ s hs, hc, hn]; exact Iff.rfl
  · rw [fixed_contract _ s hs, hc]; exact Iff.rfl

/-- A_at_limit (m = 2500): true cost 2.5e9, both accept. -/
theorem case_A : ∃ s, run (rounds 1000000 2500) = some s ∧ s.cost = 2500000000 ∧
    origAccepts s ∧ fixedAccepts s := by
  obtain ⟨s, hs, hc, _, ho, hf⟩ := crafted_rounds 2500 (by decide +kernel)
  exact ⟨s, hs, by rw [hc]; rfl, ho.2 (by decide +kernel), hf.2 (by decide +kernel)⟩

/-- B_over_by_n (m = 2501): true cost 2.501e9 > W; original accepts, fixed rejects. -/
theorem case_B : ∃ s, run (rounds 1000000 2501) = some s ∧ s.cost = 2501000000 ∧
    nLast s = 1000000 ∧ origAccepts s ∧ ¬ fixedAccepts s := by
  obtain ⟨s, hs, hc, hl, ho, hf⟩ := crafted_rounds 2501 (by decide +kernel)
  exact ⟨s, hs, by rw [hc]; rfl, hl, ho.2 (by decide +kernel), fun h => absurd (hf.1 h) (by decide +kernel)⟩

/-- C_over_by_2n (m = 2502): both reject. -/
theorem case_C : ∃ s, run (rounds 1000000 2502) = some s ∧ s.cost = 2502000000 ∧
    ¬ origAccepts s ∧ ¬ fixedAccepts s := by
  obtain ⟨s, hs, hc, _, ho, hf⟩ := crafted_rounds 2502 (by decide +kernel)
  exact ⟨s, hs, by rw [hc]; rfl, fun h => absurd (ho.1 h) (by decide +kernel),
    fun h => absurd (hf.1 h) (by decide +kernel)⟩

/-- D_over_by_n_trailer: case B plus a final op 1 "1 1 0" to the empty neighbourhood (cost 0
from the top, which is the root state of size 0).  |N_last| = 0, so both reject. -/
theorem case_D : ∃ s, run (rounds 1000000 2501 ++ [.expand 0]) = some s ∧ s.cost = 2501000000 ∧
    nLast s = 0 ∧ ¬ origAccepts s ∧ ¬ fixedAccepts s := by
  obtain ⟨s, hs, hst, htt, hc, hz, _⟩ := run_rounds 1000000 2501
  have hr : run (rounds 1000000 2501 ++ [.expand 0]) = some
      { tt := s.tt + 1, stack := [s.tt + 1, 0],
        ct := fun j => if j = s.tt + 1 then s.ct j + 1 else if j = 0 then s.ct j - 1 else s.ct j,
        sz := fun j => if j = s.tt + 1 then ((0 : Nat) : Int) else s.sz j,
        cost := s.cost + (((0 : Nat) : Int) - s.sz 0) } := by
    simp only [run, runFrom_append] at hs ⊢; rw [hs]; simp [runFrom, step, hst]
  refine ⟨_, hr, by simp [hc, hz], by simp [nLast], ?_, ?_⟩
  · rw [orig_accepts_iff _ _ hr]; simp [nLast, hc, hz, W]
  · rw [fixed_contract _ _ hr]; simp [hc, hz, W]

def caseE_state : St :=
  { tt := 1, stack := [1, 0],
    ct := fun k => if k = 0 + 1 then (0 : Int) + 1 else if k = 0 then (0 : Int) - 1 else 0,
    sz := fun k => if k = 0 + 1 then ((1000000 : Nat) : Int) else 0,
    cost := 0 + (((1000000 : Nat) : Int) - 0) }

/-- E_efficient (m = 2501): one op 1 to the whole tree, then all marks.  True cost 10^6;
the original counts 0 (= true - |N_last|). -/
theorem case_E : ∃ s, run (.expand 1000000 :: List.replicate 2501 .mark) = some s ∧
    s.cost = 1000000 ∧ origCounted s = 0 ∧ origAccepts s ∧ fixedAccepts s := by
  have hm : ∀ (t : St) (j : Nat), runFrom t (List.replicate j .mark) = some t := by
    intro t j; induction j with
    | zero => rfl
    | succ j ih => simp [List.replicate_succ, runFrom, step, ih]
  let s1 : St := caseE_state
  have hr : run (.expand 1000000 :: List.replicate 2501 .mark) = some s1 := by
    simp only [run, runFrom, step, init]; exact hm _ _
  have hc : s1.cost = 1000000 := by decide +kernel
  refine ⟨s1, hr, hc, ?_, ?_, ?_⟩
  · rw [orig_counts_true_minus_last _ _ hr]; decide
  · rw [orig_accepts_iff _ _ hr]; decide
  · rw [fixed_contract _ _ hr]; decide

/-! ### Counter-checks (must come out the other way) -/

/-- Too strong: "the original and fixed verdicts always agree" is false (witness: case B). -/
theorem not_always_agree :
    ¬ ∀ ops s, run ops = some s → (origAccepts s ↔ fixedAccepts s) := by
  intro hall
  obtain ⟨s, hs, _, _, ho, hf⟩ := case_B
  exact hf ((hall _ s hs).1 ho)

/-- Too strong: "the original checker counts the true cost" is false (witness: case E). -/
theorem orig_not_true_cost :
    ¬ ∀ ops s, run ops = some s → origCounted s = s.cost := by
  intro hall
  obtain ⟨s, hs, hc, ho, _⟩ := case_E
  have := hall _ s hs; rw [ho, hc] at this; exact absurd this (by decide +kernel)

/-- Too strong: "the original satisfies the contract (accept iff cost ≤ W)" is false. -/
theorem orig_violates_contract :
    ¬ ∀ ops s, run ops = some s → (origAccepts s ↔ s.cost ≤ W) := by
  intro hall
  obtain ⟨s, hs, hc, _, ho, _⟩ := case_B
  have := (hall _ s hs).1 ho; rw [hc] at this; exact absurd this (by decide +kernel)

end EbvEquivClass

#print axioms EbvEquivClass.checkerSum_orig
#print axioms EbvEquivClass.checkerSum_fixed
#print axioms EbvEquivClass.fixed_counts_true
#print axioms EbvEquivClass.orig_counts_true_minus_last
#print axioms EbvEquivClass.fixed_contract
#print axioms EbvEquivClass.agree_below
#print axioms EbvEquivClass.agree_above
#print axioms EbvEquivClass.differ_iff_window
#print axioms EbvEquivClass.never_fixed_only
#print axioms EbvEquivClass.agree_below_weak
#print axioms EbvEquivClass.case_A
#print axioms EbvEquivClass.case_B
#print axioms EbvEquivClass.case_C
#print axioms EbvEquivClass.case_D
#print axioms EbvEquivClass.case_E
#print axioms EbvEquivClass.not_always_agree
#print axioms EbvEquivClass.orig_not_true_cost
#print axioms EbvEquivClass.orig_violates_contract
