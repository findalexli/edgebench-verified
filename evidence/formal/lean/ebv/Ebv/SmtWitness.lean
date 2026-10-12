/-
EdgeBench Verified -- smt_solver: the SAT-witness checker, original and fixed (kernel-checked).

Modelled source (judge image
  seededge/edgebench.judge.smt_solver@sha256:2bf3482a5b2952eeadecf16e33041c13c284b7ce5d93f3491b7cfd5088d91fc6):
  /home/workspace/smt_judge/scripts/evaluate.py
  * ORIGINAL  sha256 f4be8e8dd0e4d2991189b4a9512504eb7c5db105ffbe4ff2650b7873eb0ece9b (38278 bytes)
  * FIXED v2  sha256 bbc730f89b9eb822ebda73f092bbe10beac8662b0f9b44130e0407649d9f2998 (41286 bytes)
    (= original + repairs/smt_solver-v2/repair.patch)
Line numbers: [o:N] original, [v:N] fixed.

Fragment: logic QF_UF, one uninterpreted sort U (values = atoms, here `Nat`), declared nullary
constants, ONE unary uninterpreted function f : U -> U, `let` in formulas and in terms, `=`, `not`,
`and`.  `(distinct s t)` with two arguments is encoded as `not (= s t)` (same evaluation order and
same value, [o:584-589]).

Source-to-model map
  * `Tm.sym x`: a symbol.  eval looks in the let-environment first [o:530 / v:599], then the
    declared constants via `model_lookup` [o:547-551 / v:616-620] ("missing model value").
    The witness "values" dict is `Wit` (first match = dict lookup); keys are modelled as parsed
    terms, i.e. canonical text [o:379-382].
  * `Tm.app t` = `(f t)`.  ORIGINAL [o:619-631]: evaluate the argument (for congruence), look up
    the value by the canonical TEXT of the application, ignoring the environment, and record
    (arg value, result) in `uf_apps`.  `expanded_canonical_term` only differs from the text when
    nullary define-funs occur; the fragment has none.  FIXED [v:692-702]: first `uf_table` at the
    EVALUATED argument value; if absent, the same textual lookup (fallback).
    Both are `cT` below; the original is `cT` with the empty table (then [v:693] always misses and
    the code is exactly [o:623-631]).
  * `let` [o:566-572 / v:635-641]: bound terms evaluated in the outer env, then shadowing.
  * `and` [o:575-576]: Python `all(...)` over a generator short-circuits at the first false;
    `=` [o:584-586] evaluates all arguments left to right.
  * table construction `_load_ground_uf_values` [v:527-564]: for every witness key that parses to
    a ground application `(f g)` (`is_ground_term` [v:505-525]: declared nullary symbols and nested
    applications; `let` is not ground), evaluate g in the EMPTY env, then insert (value -> result),
    or reject "congruence violation" if the slot holds a different value; keys whose evaluation
    raises are skipped (`except Exception: continue`).  Keys are processed sorted by text length
    [v:552]; `build` takes the processing order `ks` as a parameter and every theorem below holds
    for ALL orders, so in particular for the real one.
  * `validate` [o:633-643 / v:704-714]: evaluate each assertion in order (uf_apps accumulates),
    reject "assertion is false" if one is false, then the congruence pass: `seen` starts empty
    (original) or as the table (fixed); for each recorded app, reject if `seen` has the key with a
    different value, then overwrite.  `congr` is that loop literally.
Abstractions (each stated again in evidence/formal/notes/smt_solver.md):
  * when a table-construction evaluation raises, the real code keeps the uf_apps entries recorded
    before the exception; the model drops them.  The model therefore accepts a SUPERSET of what the
    real code accepts, so the soundness theorem transfers; the completeness witness never raises.
  * an undeclared, unbound symbol is an atom in real QF_UF [o:556-557]; here it is an error (both in
    the checker and in the reference semantics).  Closed formulas never reach it.
  * one sort, one unary f; no define-fun, ite, or, =>, arithmetic, Bool-sorted UF, perturbation.
-/

namespace EbvSmt

inductive Tm where
  | sym : Nat → Tm
  | app : Tm → Tm
  | letT : Nat → Tm → Tm → Tm
  deriving DecidableEq, Repr

inductive Fm where
  | eq : Tm → Tm → Fm
  | not : Fm → Fm
  | and : Fm → Fm → Fm
  | letF : Nat → Tm → Fm → Fm
  deriving DecidableEq, Repr

inductive Err where
  | missing | unknownSym | falseAssert | congruence
  deriving DecidableEq, Repr

inductive Verdict where
  | accept
  | reject (e : Err)
  deriving DecidableEq, Repr

abbrev Tab := List (Nat × Nat)   -- environments, the UF table, recorded uf_apps
abbrev Wit := List (Tm × Nat)    -- the witness "values" dict

def lk : Tab → Nat → Option Nat
  | [], _ => none
  | (a, r) :: l, v => if a = v then some r else lk l v

def wget : Wit → Tm → Option Nat
  | [], _ => none
  | (k, r) :: w, t => if k = t then some r else wget w t

/-! ## Reference semantics (a model = constant values `c`, a total function `F`) -/

def rT (decls : List Nat) (c F : Nat → Nat) : Tab → Tm → Option Nat
  | ρ, .sym x => match lk ρ x with
    | some v => some v
    | none => if x ∈ decls then some (c x) else none
  | ρ, .app t => match rT decls c F ρ t with
    | some v => some (F v)
    | none => none
  | ρ, .letT x t b => match rT decls c F ρ t with
    | some v => rT decls c F ((x, v) :: ρ) b
    | none => none

def rF (decls : List Nat) (c F : Nat → Nat) : Tab → Fm → Option Bool
  | ρ, .eq s t => match rT decls c F ρ s, rT decls c F ρ t with
    | some a, some b => some (decide (a = b))
    | _, _ => none
  | ρ, .not φ => match rF decls c F ρ φ with
    | some b => some (!b)
    | none => none
  | ρ, .and φ ψ => match rF decls c F ρ φ with
    | some false => some false
    | some true => rF decls c F ρ ψ
    | none => none
  | ρ, .letF x t φ => match rT decls c F ρ t with
    | some v => rF decls c F ((x, v) :: ρ) φ
    | none => none

/-! ## The checker (`T = []`: original; `T` = uf_table: fixed) -/

def cT (decls : List Nat) (W : Wit) (T : Tab) : Tab → Tm → Tab → Except Err (Nat × Tab)
  | ρ, .sym x, as => match lk ρ x with
    | some v => .ok (v, as)
    | none => if x ∈ decls then
        (match wget W (.sym x) with
         | some v => .ok (v, as)
         | none => .error .missing)
      else .error .unknownSym
  | ρ, .app t, as => match cT decls W T ρ t as with
    | .error e => .error e
    | .ok (v, as1) => match lk T v with
      | some r => .ok (r, (v, r) :: as1)
      | none => match wget W (.app t) with
        | some r => .ok (r, (v, r) :: as1)
        | none => .error .missing
  | ρ, .letT x t b, as => match cT decls W T ρ t as with
    | .error e => .error e
    | .ok (v, as1) => cT decls W T ((x, v) :: ρ) b as1

def cF (decls : List Nat) (W : Wit) (T : Tab) : Tab → Fm → Tab → Except Err (Bool × Tab)
  | ρ, .eq s t, as => match cT decls W T ρ s as with
    | .error e => .error e
    | .ok (a, as1) => match cT decls W T ρ t as1 with
      | .error e => .error e
      | .ok (b, as2) => .ok (decide (a = b), as2)
  | ρ, .not φ, as => match cF decls W T ρ φ as with
    | .error e => .error e
    | .ok (b, as1) => .ok (!b, as1)
  | ρ, .and φ ψ, as => match cF decls W T ρ φ as with
    | .error e => .error e
    | .ok (false, as1) => .ok (false, as1)
    | .ok (true, as1) => cF decls W T ρ ψ as1
  | ρ, .letF x t φ, as => match cT decls W T ρ t as with
    | .error e => .error e
    | .ok (v, as1) => cF decls W T ((x, v) :: ρ) φ as1

def ground (decls : List Nat) : Tm → Bool
  | .sym x => decide (x ∈ decls)
  | .app g => ground decls g
  | .letT _ _ _ => false

def build (decls : List Nat) (W : Wit) : Wit → Tab → Tab → Except Err (Tab × Tab)
  | [], T, as => .ok (T, as)
  | (k, r) :: ks, T, as =>
    match k with
    | .app g =>
      if ground decls g = true then
        match cT decls W T [] g as with
        | .error _ => build decls W ks T as
        | .ok (v, as1) => match lk T v with
          | some r' => if r' = r then build decls W ks T as1 else .error .congruence
          | none => build decls W ks ((v, r) :: T) as1
      else build decls W ks T as
    | _ => build decls W ks T as

def congr : Tab → Tab → Bool
  | _, [] => true
  | seen, (a, r) :: l =>
    (match lk seen a with
     | some r' => decide (r' = r)
     | none => true) && congr ((a, r) :: seen) l

def runAsserts (decls : List Nat) (W : Wit) (T : Tab) : List Fm → Tab → Except Err Tab
  | [], as => .ok as
  | φ :: φs, as => match cF decls W T [] φ as with
    | .error e => .error e
    | .ok (false, _) => .error .falseAssert
    | .ok (true, as1) => runAsserts decls W T φs as1

/-- the original `WitnessChecker(...).validate()` -/
def origCheck (decls : List Nat) (W : Wit) (φs : List Fm) : Verdict :=
  match runAsserts decls W [] φs [] with
  | .error e => .reject e
  | .ok as => if congr [] as.reverse then .accept else .reject .congruence

/-- the fixed checker; `ks` is the order in which witness keys are loaded into the table -/
def fixedCheck (decls : List Nat) (W : Wit) (ks : Wit) (φs : List Fm) : Verdict :=
  match build decls W ks [] [] with
  | .error e => .reject e
  | .ok (T, as0) => match runAsserts decls W T φs as0 with
    | .error e => .reject e
    | .ok as => if congr T as.reverse then .accept else .reject .congruence

/-- the original checker is the fixed one with no table entries -/
theorem orig_eq_fixed_empty (decls : List Nat) (W : Wit) (φs : List Fm) :
    origCheck decls W φs = fixedCheck decls W [] φs := rfl

/-! ## Generic list lemmas -/

def Good (F : Nat → Nat) (l : Tab) : Prop := ∀ e ∈ l, F e.1 = e.2
def Pw (l : Tab) : Prop := ∀ p ∈ l, ∀ q ∈ l, p.1 = q.1 → p.2 = q.2

theorem lk_some_mem : ∀ (l : Tab) (a r : Nat), lk l a = some r → (a, r) ∈ l := by
  intro l; induction l with
  | nil => intro a r h; simp [lk] at h
  | cons p l ih =>
    intro a r h
    obtain ⟨b, s⟩ := p
    simp only [lk] at h
    split at h
    · rename_i hb; subst hb; simp at h; subst h; simp
    · exact List.mem_cons_of_mem _ (ih a r h)

theorem lk_none : ∀ (l : Tab) (a : Nat), lk l a = none → ∀ e ∈ l, e.1 ≠ a := by
  intro l; induction l with
  | nil => intro a _ e he; simp at he
  | cons p l ih =>
    intro a h e he
    obtain ⟨b, s⟩ := p
    simp only [lk] at h
    split at h
    · simp at h
    · rename_i hb
      rcases List.mem_cons.mp he with he | he
      · subst he; exact hb
      · exact ih a h e he

theorem lk_of_mem : ∀ (l : Tab) (a r : Nat), (a, r) ∈ l → ∃ r', lk l a = some r' := by
  intro l a r h
  cases hl : lk l a with
  | some r' => exact ⟨r', rfl⟩
  | none => exact absurd rfl (lk_none l a hl (a, r) h)

theorem wget_of : ∀ (w : Wit) (t : Tm) (r : Nat), (t, r) ∈ w →
    (∀ r', (t, r') ∈ w → r' = r) → wget w t = some r := by
  intro w; induction w with
  | nil => intro t r h; simp at h
  | cons p w ih =>
    intro t r h hu
    obtain ⟨k, s⟩ := p
    simp only [wget]
    split
    · rename_i hk; subst hk; rw [hu s (by simp)]
    · rename_i hk
      have h' : (t, r) ∈ w := by
        rcases List.mem_cons.mp h with h | h
        · cases h; exact absurd rfl hk
        · exact h
      exact ih t r h' (fun r' hr => hu r' (List.mem_cons_of_mem _ hr))

theorem good_of_lk {F : Nat → Nat} {T : Tab} {v r : Nat} (hT : Good F T) (h : lk T v = some r) :
    F v = r := hT (v, r) (lk_some_mem T v r h)

/-! ## Soundness of the fixed checker (and hence of the original) -/

def cOf (W : Wit) (k : Nat) : Nat := (wget W (.sym k)).getD 0

theorem cT_sound (decls : List Nat) (W : Wit) (T : Tab) (F : Nat → Nat) :
    ∀ (t : Tm) (ρ as : Tab) (v : Nat) (as' : Tab),
    cT decls W T ρ t as = .ok (v, as') →
    (∀ e ∈ as, e ∈ as') ∧ (Good F as' → rT decls (cOf W) F ρ t = some v) := by
  intro t
  induction t with
  | sym x =>
    intro ρ as v as' h
    simp only [cT] at h
    split at h
    · rename_i v0 hx
      simp only [Except.ok.injEq, Prod.mk.injEq] at h
      obtain ⟨rfl, rfl⟩ := h
      exact ⟨fun e he => he, fun _ => by simp [rT, hx]⟩
    · rename_i hx
      split at h
      · rename_i hd
        split at h
        · rename_i v0 hw
          simp only [Except.ok.injEq, Prod.mk.injEq] at h
          obtain ⟨rfl, rfl⟩ := h
          exact ⟨fun e he => he, fun _ => by simp [rT, hx, hd, cOf, hw]⟩
        · simp at h
      · simp at h
  | app t ih =>
    intro ρ as v as' h
    simp only [cT] at h
    split at h
    · simp at h
    · rename_i v0 as1 h0
      obtain ⟨hsub, hval⟩ := ih ρ as v0 as1 h0
      have fin : ∀ r, (Except.ok (r, (v0, r) :: as1) : Except Err (Nat × Tab)) = .ok (v, as') →
          (∀ e ∈ as, e ∈ as') ∧ (Good F as' → rT decls (cOf W) F ρ (.app t) = some v) := by
        intro r hr
        simp only [Except.ok.injEq, Prod.mk.injEq] at hr
        obtain ⟨rfl, rfl⟩ := hr
        refine ⟨fun e he => List.mem_cons_of_mem _ (hsub e he), fun hg => ?_⟩
        have h1 : Good F as1 := fun e he => hg e (List.mem_cons_of_mem _ he)
        have h2 : F v0 = r := hg (v0, r) (by simp)
        simp [rT, hval h1, h2]
      split at h
      · exact fin _ h
      · split at h
        · exact fin _ h
        · simp at h
  | letT x t b iht ihb =>
    intro ρ as v as' h
    simp only [cT] at h
    split at h
    · simp at h
    · rename_i v0 as1 h0
      obtain ⟨hs1, hv1⟩ := iht ρ as v0 as1 h0
      obtain ⟨hs2, hv2⟩ := ihb ((x, v0) :: ρ) as1 v as' h
      refine ⟨fun e he => hs2 e (hs1 e he), fun hg => ?_⟩
      have h1 : Good F as1 := fun e he => hg e (hs2 e he)
      simp [rT, hv1 h1, hv2 hg]

theorem cF_sound (decls : List Nat) (W : Wit) (T : Tab) (F : Nat → Nat) :
    ∀ (φ : Fm) (ρ as : Tab) (b : Bool) (as' : Tab),
    cF decls W T ρ φ as = .ok (b, as') →
    (∀ e ∈ as, e ∈ as') ∧ (Good F as' → rF decls (cOf W) F ρ φ = some b) := by
  intro φ
  induction φ with
  | eq s t =>
    intro ρ as b as' h
    simp only [cF] at h
    split at h
    · simp at h
    · rename_i a1 as1 h1
      split at h
      · simp at h
      · rename_i a2 as2 h2
        simp only [Except.ok.injEq, Prod.mk.injEq] at h
        obtain ⟨rfl, rfl⟩ := h
        obtain ⟨hs1, hv1⟩ := cT_sound decls W T F s ρ as a1 as1 h1
        obtain ⟨hs2, hv2⟩ := cT_sound decls W T F t ρ as1 a2 as2 h2
        refine ⟨fun e he => hs2 e (hs1 e he), fun hg => ?_⟩
        have g1 : Good F as1 := fun e he => hg e (hs2 e he)
        simp [rF, hv1 g1, hv2 hg]
  | not φ ih =>
    intro ρ as b as' h
    simp only [cF] at h
    split at h
    · simp at h
    · rename_i b1 as1 h1
      simp only [Except.ok.injEq, Prod.mk.injEq] at h
      obtain ⟨rfl, rfl⟩ := h
      obtain ⟨hs, hv⟩ := ih ρ as b1 as1 h1
      exact ⟨hs, fun hg => by simp [rF, hv hg]⟩
  | and φ ψ ih1 ih2 =>
    intro ρ as b as' h
    simp only [cF] at h
    split at h
    · simp at h
    · rename_i as1 h1
      simp only [Except.ok.injEq, Prod.mk.injEq] at h
      obtain ⟨rfl, rfl⟩ := h
      obtain ⟨hs, hv⟩ := ih1 ρ as false as1 h1
      exact ⟨hs, fun hg => by simp [rF, hv hg]⟩
    · rename_i as1 h1
      obtain ⟨hs1, hv1⟩ := ih1 ρ as true as1 h1
      obtain ⟨hs2, hv2⟩ := ih2 ρ as1 b as' h
      refine ⟨fun e he => hs2 e (hs1 e he), fun hg => ?_⟩
      have g1 : Good F as1 := fun e he => hg e (hs2 e he)
      simp [rF, hv1 g1, hv2 hg]
  | letF x t φ ih =>
    intro ρ as b as' h
    simp only [cF] at h
    split at h
    · simp at h
    · rename_i v0 as1 h0
      obtain ⟨hs1, hv1⟩ := cT_sound decls W T F t ρ as v0 as1 h0
      obtain ⟨hs2, hv2⟩ := ih ((x, v0) :: ρ) as1 b as' h
      refine ⟨fun e he => hs2 e (hs1 e he), fun hg => ?_⟩
      have g1 : Good F as1 := fun e he => hg e (hs2 e he)
      simp [rF, hv1 g1, hv2 hg]

theorem runAsserts_sound (decls : List Nat) (W : Wit) (T : Tab) (F : Nat → Nat) :
    ∀ (φs : List Fm) (as as' : Tab), runAsserts decls W T φs as = .ok as' →
    (∀ e ∈ as, e ∈ as') ∧ (Good F as' → ∀ φ ∈ φs, rF decls (cOf W) F [] φ = some true) := by
  intro φs
  induction φs with
  | nil =>
    intro as as' h
    simp only [runAsserts, Except.ok.injEq] at h
    subst h
    exact ⟨fun e he => he, fun _ φ hφ => by simp at hφ⟩
  | cons φ φs ih =>
    intro as as' h
    simp only [runAsserts] at h
    split at h
    · simp at h
    · simp at h
    · rename_i as1 h1
      obtain ⟨hs1, hv1⟩ := cF_sound decls W T F φ [] as true as1 h1
      obtain ⟨hs2, hv2⟩ := ih as1 as' h
      refine ⟨fun e he => hs2 e (hs1 e he), fun hg ψ hψ => ?_⟩
      rcases List.mem_cons.mp hψ with hψ | hψ
      · subst hψ; exact hv1 (fun e he => hg e (hs2 e he))
      · exact hv2 hg ψ hψ

theorem build_pw (decls : List Nat) (W : Wit) :
    ∀ (ks : Wit) (T as T' as' : Tab), Pw T → build decls W ks T as = .ok (T', as') → Pw T' := by
  intro ks
  induction ks with
  | nil =>
    intro T as T' as' hp h
    simp only [build, Except.ok.injEq, Prod.mk.injEq] at h
    obtain ⟨rfl, rfl⟩ := h
    exact hp
  | cons p ks ih =>
    intro T as T' as' hp h
    obtain ⟨k, r⟩ := p
    simp only [build] at h
    split at h
    · split at h
      · split at h
        · exact ih T as T' as' hp h
        · rename_i v as1 _
          split at h
          · split at h
            · exact ih T as1 T' as' hp h
            · simp at h
          · rename_i hn
            refine ih ((v, r) :: T) as1 T' as' ?_ h
            intro p hpm q hqm hpq
            have hno := lk_none T v hn
            rcases List.mem_cons.mp hpm with hpm | hpm <;>
              rcases List.mem_cons.mp hqm with hqm | hqm
            · rw [hpm, hqm]
            · subst hpm; exact absurd hpq.symm (hno q hqm)
            · subst hqm; exact absurd hpq (hno p hpm)
            · exact hp p hpm q hqm hpq
      · exact ih T as T' as' hp h
    · exact ih T as T' as' hp h

theorem congr_pw : ∀ (l seen : Tab), Pw seen → congr seen l = true →
    ∀ p, (p ∈ seen ∨ p ∈ l) → ∀ q, (q ∈ seen ∨ q ∈ l) → p.1 = q.1 → p.2 = q.2 := by
  intro l
  induction l with
  | nil =>
    intro seen hp _ p hpm q hqm hpq
    simp at hpm hqm
    exact hp p hpm q hqm hpq
  | cons e l ih =>
    intro seen hp h
    obtain ⟨a, r⟩ := e
    simp only [congr, Bool.and_eq_true] at h
    obtain ⟨hc, hrest⟩ := h
    have hp' : Pw ((a, r) :: seen) := by
      intro p hpm q hqm hpq
      have key : ∀ s, (a, s) ∈ seen → s = r := by
        intro s hs
        obtain ⟨r', hr'⟩ := lk_of_mem seen a s hs
        rw [hr'] at hc
        have : r' = r := of_decide_eq_true hc
        have hm := lk_some_mem seen a r' hr'
        exact (hp (a, s) hs (a, r') hm rfl).trans this
      rcases List.mem_cons.mp hpm with hp1 | hp1 <;>
        rcases List.mem_cons.mp hqm with hq1 | hq1
      · rw [hp1, hq1]
      · rw [hp1] at hpq ⊢
        have hq : q = (a, q.2) := Prod.ext hpq.symm rfl
        exact (key q.2 (hq ▸ hq1)).symm
      · rw [hq1] at hpq ⊢
        have hp2 : p = (a, p.2) := Prod.ext hpq rfl
        exact key p.2 (hp2 ▸ hp1)
      · exact hp p hp1 q hq1 hpq
    intro p hpm q hqm hpq
    have conv : ∀ z, (z ∈ seen ∨ z ∈ (a, r) :: l) → (z ∈ (a, r) :: seen ∨ z ∈ l) := by
      intro z hz
      rcases hz with hz | hz
      · exact Or.inl (List.mem_cons_of_mem _ hz)
      · rcases List.mem_cons.mp hz with hz | hz
        · exact Or.inl (by rw [hz]; simp)
        · exact Or.inr hz
    exact ih ((a, r) :: seen) hp' hrest p (conv p hpm) q (conv q hqm) hpq

theorem pw_good (L : Tab) (hp : Pw L) : Good (fun a => (lk L a).getD 0) L := by
  intro e he
  obtain ⟨r', hr'⟩ := lk_of_mem L e.1 e.2 he
  have hm := lk_some_mem L e.1 r' hr'
  simp only [hr', Option.getD_some]
  exact hp (e.1, r') hm e he rfl

/-- **Soundness (fixed).** For every witness, every key-loading order and every list of
assertions in the fragment: if the fixed checker accepts, the witness constants together with the
function defined by the table and the recorded applications form a genuine model.  This covers the
textual-fallback path and mixed textual/ground witnesses. -/
theorem fixed_sound (decls : List Nat) (W ks : Wit) (φs : List Fm)
    (h : fixedCheck decls W ks φs = .accept) :
    ∃ c F : Nat → Nat, ∀ φ ∈ φs, rF decls c F [] φ = some true := by
  unfold fixedCheck at h
  split at h
  · simp at h
  · rename_i T as0 hb
    split at h
    · simp at h
    · rename_i as ha
      split at h
      · rename_i hc
        have hpT : Pw T := build_pw decls W ks [] [] T as0
          (by intro p hp; simp at hp) hb
        have hall := congr_pw as.reverse T hpT hc
        let L := T ++ as.reverse
        have hpL : Pw L := by
          intro p hp q hq hpq
          exact hall p (List.mem_append.mp hp) q (List.mem_append.mp hq) hpq
        have hg := pw_good L hpL
        refine ⟨cOf W, fun a => (lk L a).getD 0, ?_⟩
        refine (runAsserts_sound decls W T _ φs as0 as ha).2 ?_
        intro e he
        exact hg e (List.mem_append_right _ (List.mem_reverse.mpr he))
      · simp at h

/-- **Soundness (original)**, as a corollary: the original checker never accepts a non-model in
the fragment either (the published "direction" claim). -/
theorem orig_sound (decls : List Nat) (W : Wit) (φs : List Fm)
    (h : origCheck decls W φs = .accept) :
    ∃ c F : Nat → Nat, ∀ φ ∈ φs, rF decls c F [] φ = some true :=
  fixed_sound decls W [] φs h

/-! ## Completeness of the fixed checker for ground-key witnesses -/

def gval (c F : Nat → Nat) : Tm → Nat
  | .sym x => c x
  | .app g => F (gval c F g)
  | .letT _ _ _ => 0

/-- values denoted by some ground term -/
def Den (decls : List Nat) (c F : Nat → Nat) (v : Nat) : Prop :=
  ∃ g, ground decls g = true ∧ gval c F g = v

theorem cT_build (decls : List Nat) (W : Wit) (T : Tab) (c F : Nat → Nat) (G : List Tm)
    (hT : Good F T)
    (hconst : ∀ k ∈ decls, wget W (.sym k) = some (c k))
    (hG : ∀ g ∈ G, ground decls g = true ∧ ∀ s, g = .app s → s ∈ G)
    (happ : ∀ s ∈ G, wget W (.app s) = some (F (gval c F s))) :
    ∀ g, g ∈ G → ∀ as, Good F as →
      ∃ as', cT decls W T [] g as = .ok (gval c F g, as') ∧ Good F as' := by
  intro g
  induction g with
  | sym x =>
    intro hx as hg
    have hd : x ∈ decls := of_decide_eq_true (hG _ hx).1
    exact ⟨as, by simp [cT, lk, hd, hconst x hd, gval], hg⟩
  | app s ih =>
    intro hs as hg
    have hsG : s ∈ G := (hG _ hs).2 s rfl
    obtain ⟨as1, h1, hg1⟩ := ih hsG as hg
    cases hl : lk T (gval c F s) with
    | some r =>
      have hr : F (gval c F s) = r := good_of_lk hT hl
      refine ⟨(gval c F s, r) :: as1, ?_, ?_⟩
      · simp [cT, h1, hl, gval, hr]
      · intro e he
        rcases List.mem_cons.mp he with he | he
        · subst he; exact hr
        · exact hg1 e he
    | none =>
      refine ⟨(gval c F s, F (gval c F s)) :: as1, ?_, ?_⟩
      · simp [cT, h1, hl, happ s hsG, gval]
      · intro e he
        rcases List.mem_cons.mp he with he | he
        · subst he; rfl
        · exact hg1 e he
  | letT x t b _ _ =>
    intro hx
    have := (hG _ hx).1
    simp [ground] at this

theorem build_complete (decls : List Nat) (W : Wit) (c F : Nat → Nat) (G : List Tm)
    (hconst : ∀ k ∈ decls, wget W (.sym k) = some (c k))
    (hG : ∀ g ∈ G, ground decls g = true ∧ ∀ s, g = .app s → s ∈ G)
    (happ : ∀ s ∈ G, wget W (.app s) = some (F (gval c F s))) :
    ∀ (ks : Wit),
    (∀ g r, (Tm.app g, r) ∈ ks → ground decls g = true → g ∈ G ∧ r = F (gval c F g)) →
    ∀ (T as : Tab), Good F T → Good F as →
    ∃ T' as', build decls W ks T as = .ok (T', as') ∧ Good F T' ∧ Good F as' ∧
      (∀ v r, lk T v = some r → ∃ r', lk T' v = some r') ∧
      (∀ g, (Tm.app g, F (gval c F g)) ∈ ks → g ∈ G → ∃ r', lk T' (gval c F g) = some r') := by
  intro ks
  induction ks with
  | nil =>
    intro _ T as hT has
    exact ⟨T, as, rfl, hT, has, fun v r h => ⟨r, h⟩, fun g hg => by simp at hg⟩
  | cons p ks ih =>
    intro hks T as hT has
    obtain ⟨k, r⟩ := p
    have hks' : ∀ g r, (Tm.app g, r) ∈ ks → ground decls g = true → g ∈ G ∧ r = F (gval c F g) :=
      fun g r h hg => hks g r (List.mem_cons_of_mem _ h) hg
    cases k with
    | app g =>
      by_cases hgr : ground decls g = true
      · obtain ⟨hgG, hr⟩ := hks g r (by simp) hgr
        subst hr
        obtain ⟨as1, h1, hg1⟩ := cT_build decls W T c F G hT hconst hG happ g hgG as has
        cases hl : lk T (gval c F g) with
        | some r' =>
          have hr' : F (gval c F g) = r' := good_of_lk hT hl
          obtain ⟨T', as', hb, hT', has', hmono, hcov⟩ := ih hks' T as1 hT hg1
          refine ⟨T', as', ?_, hT', has', hmono, ?_⟩
          · simp only [build, hgr, ite_true, h1, hl, hr', ite_true]; exact hb
          · intro g' hg' hg'G
            rcases List.mem_cons.mp hg' with hg' | hg'
            · simp at hg'
              have : g' = g := hg'.1
              subst this
              exact hmono _ _ hl
            · exact hcov g' hg' hg'G
        | none =>
          have hT2 : Good F ((gval c F g, F (gval c F g)) :: T) := by
            intro e he
            rcases List.mem_cons.mp he with he | he
            · subst he; rfl
            · exact hT e he
          obtain ⟨T', as', hb, hT', has', hmono, hcov⟩ := ih hks' _ as1 hT2 hg1
          refine ⟨T', as', ?_, hT', has', ?_, ?_⟩
          · simp only [build, hgr, ite_true, h1, hl]; exact hb
          · intro v r0 hv
            by_cases hv' : gval c F g = v
            · exact hmono v (F (gval c F g)) (by simp [lk, hv'])
            · exact hmono v r0 (by simp [lk, hv', hv])
          · intro g' hg' hg'G
            rcases List.mem_cons.mp hg' with hg' | hg'
            · simp at hg'
              have : g' = g := hg'.1
              subst this
              exact hmono _ (F (gval c F g')) (by simp [lk])
            · exact hcov g' hg' hg'G
      · obtain ⟨T', as', hb, hT', has', hmono, hcov⟩ := ih hks' T as hT has
        refine ⟨T', as', ?_, hT', has', hmono, ?_⟩
        · simp only [build, hgr]; exact hb
        · intro g' hg' hg'G
          rcases List.mem_cons.mp hg' with hg' | hg'
          · simp at hg'
            have : g' = g := hg'.1
            subst this
            exact absurd (hG g' hg'G).1 hgr
          · exact hcov g' hg' hg'G
    | sym x =>
      obtain ⟨T', as', hb, hT', has', hmono, hcov⟩ := ih hks' T as hT has
      refine ⟨T', as', by simp only [build]; exact hb, hT', has', hmono, ?_⟩
      intro g' hg' hg'G
      rcases List.mem_cons.mp hg' with hg' | hg'
      · simp at hg'
      · exact hcov g' hg' hg'G
    | letT x t b =>
      obtain ⟨T', as', hb, hT', has', hmono, hcov⟩ := ih hks' T as hT has
      refine ⟨T', as', by simp only [build]; exact hb, hT', has', hmono, ?_⟩
      intro g' hg' hg'G
      rcases List.mem_cons.mp hg' with hg' | hg'
      · simp at hg'
      · exact hcov g' hg' hg'G

theorem cT_complete (decls : List Nat) (W : Wit) (T : Tab) (c F : Nat → Nat)
    (hT : Good F T) (hcov : ∀ v, Den decls c F v → ∃ r, lk T v = some r)
    (hconst : ∀ k ∈ decls, wget W (.sym k) = some (c k)) :
    ∀ (t : Tm) (ρ : Tab) (v : Nat), (∀ e ∈ ρ, Den decls c F e.2) →
    rT decls c F ρ t = some v → ∀ as, Good F as →
    ∃ as', cT decls W T ρ t as = .ok (v, as') ∧ Good F as' ∧ Den decls c F v := by
  intro t
  induction t with
  | sym x =>
    intro ρ v hρ h as hg
    simp only [rT] at h
    split at h
    · rename_i v0 hx
      simp at h; subst h
      exact ⟨as, by simp [cT, hx], hg, hρ (x, v0) (lk_some_mem ρ x v0 hx)⟩
    · rename_i hx
      split at h
      · rename_i hd
        simp at h; subst h
        exact ⟨as, by simp [cT, hx, hd, hconst x hd], hg,
          ⟨.sym x, by simp [ground, hd], rfl⟩⟩
      · simp at h
  | app t ih =>
    intro ρ v hρ h as hg
    simp only [rT] at h
    split at h
    · rename_i v0 h0
      simp at h; subst h
      obtain ⟨as1, h1, hg1, ⟨g0, hg0, hv0⟩⟩ := ih ρ v0 hρ h0 as hg
      obtain ⟨r, hr⟩ := hcov v0 ⟨g0, hg0, hv0⟩
      have hFr : F v0 = r := good_of_lk hT hr
      refine ⟨(v0, r) :: as1, by simp [cT, h1, hr, hFr], ?_, ⟨.app g0, by simp [ground, hg0],
        by simp [gval, hv0]⟩⟩
      intro e he
      rcases List.mem_cons.mp he with he | he
      · subst he; exact hFr
      · exact hg1 e he
    · simp at h
  | letT x t b iht ihb =>
    intro ρ v hρ h as hg
    simp only [rT] at h
    split at h
    · rename_i v0 h0
      obtain ⟨as1, h1, hg1, hd0⟩ := iht ρ v0 hρ h0 as hg
      have hρ' : ∀ e ∈ (x, v0) :: ρ, Den decls c F e.2 := by
        intro e he
        rcases List.mem_cons.mp he with he | he
        · subst he; exact hd0
        · exact hρ e he
      obtain ⟨as2, h2, hg2, hd2⟩ := ihb ((x, v0) :: ρ) v hρ' h as1 hg1
      exact ⟨as2, by simp [cT, h1, h2], hg2, hd2⟩
    · simp at h

theorem cF_complete (decls : List Nat) (W : Wit) (T : Tab) (c F : Nat → Nat)
    (hT : Good F T) (hcov : ∀ v, Den decls c F v → ∃ r, lk T v = some r)
    (hconst : ∀ k ∈ decls, wget W (.sym k) = some (c k)) :
    ∀ (φ : Fm) (ρ : Tab) (b : Bool), (∀ e ∈ ρ, Den decls c F e.2) →
    rF decls c F ρ φ = some b → ∀ as, Good F as →
    ∃ as', cF decls W T ρ φ as = .ok (b, as') ∧ Good F as' := by
  intro φ
  induction φ with
  | eq s t =>
    intro ρ b hρ h as hg
    simp only [rF] at h
    split at h
    · rename_i a1 a2 h1 h2
      simp at h; subst h
      obtain ⟨as1, e1, g1, _⟩ := cT_complete decls W T c F hT hcov hconst s ρ a1 hρ h1 as hg
      obtain ⟨as2, e2, g2, _⟩ := cT_complete decls W T c F hT hcov hconst t ρ a2 hρ h2 as1 g1
      exact ⟨as2, by simp [cF, e1, e2], g2⟩
    · simp at h
  | not φ ih =>
    intro ρ b hρ h as hg
    simp only [rF] at h
    cases h0 : rF decls c F ρ φ with
    | none => rw [h0] at h; simp at h
    | some b0 =>
      rw [h0] at h
      obtain rfl : (!b0) = b := Option.some.inj h
      obtain ⟨as1, e1, g1⟩ := ih ρ b0 hρ h0 as hg
      exact ⟨as1, by simp [cF, e1], g1⟩
  | and φ ψ ih1 ih2 =>
    intro ρ b hρ h as hg
    simp only [rF] at h
    split at h
    · rename_i h0
      simp at h; subst h
      obtain ⟨as1, e1, g1⟩ := ih1 ρ false hρ h0 as hg
      exact ⟨as1, by simp [cF, e1], g1⟩
    · rename_i h0
      obtain ⟨as1, e1, g1⟩ := ih1 ρ true hρ h0 as hg
      obtain ⟨as2, e2, g2⟩ := ih2 ρ b hρ h as1 g1
      exact ⟨as2, by simp [cF, e1, e2], g2⟩
    · simp at h
  | letF x t φ ih =>
    intro ρ b hρ h as hg
    simp only [rF] at h
    split at h
    · rename_i v0 h0
      obtain ⟨as1, e1, g1, hd0⟩ := cT_complete decls W T c F hT hcov hconst t ρ v0 hρ h0 as hg
      have hρ' : ∀ e ∈ (x, v0) :: ρ, Den decls c F e.2 := by
        intro e he
        rcases List.mem_cons.mp he with he | he
        · subst he; exact hd0
        · exact hρ e he
      obtain ⟨as2, e2, g2⟩ := ih ((x, v0) :: ρ) b hρ' h as1 g1
      exact ⟨as2, by simp [cF, e1, e2], g2⟩
    · simp at h

theorem runAsserts_complete (decls : List Nat) (W : Wit) (T : Tab) (c F : Nat → Nat)
    (hT : Good F T) (hcov : ∀ v, Den decls c F v → ∃ r, lk T v = some r)
    (hconst : ∀ k ∈ decls, wget W (.sym k) = some (c k)) :
    ∀ (φs : List Fm), (∀ φ ∈ φs, rF decls c F [] φ = some true) → ∀ as, Good F as →
    ∃ as', runAsserts decls W T φs as = .ok as' ∧ Good F as' := by
  intro φs
  induction φs with
  | nil => intro _ as hg; exact ⟨as, rfl, hg⟩
  | cons φ φs ih =>
    intro hs as hg
    obtain ⟨as1, e1, g1⟩ := cF_complete decls W T c F hT hcov hconst φ [] true
      (by intro e he; simp at he) (hs φ (by simp)) as hg
    obtain ⟨as2, e2, g2⟩ := ih (fun ψ hψ => hs ψ (List.mem_cons_of_mem _ hψ)) as1 g1
    exact ⟨as2, by simp [runAsserts, e1, e2], g2⟩

theorem congr_good (F : Nat → Nat) : ∀ (l seen : Tab), Good F seen → Good F l →
    congr seen l = true := by
  intro l
  induction l with
  | nil => intro seen _ _; rfl
  | cons e l ih =>
    intro seen hs hl
    obtain ⟨a, r⟩ := e
    have hr : F a = r := hl (a, r) (by simp)
    have hs' : Good F ((a, r) :: seen) := by
      intro e he
      rcases List.mem_cons.mp he with he | he
      · subst he; exact hr
      · exact hs e he
    have hrest := ih ((a, r) :: seen) hs' (fun e he => hl e (List.mem_cons_of_mem _ he))
    simp only [congr, Bool.and_eq_true]
    refine ⟨?_, hrest⟩
    split
    · rename_i r' hr'
      have : F a = r' := good_of_lk hs hr'
      exact decide_eq_true (this.symm.trans hr)
    · rfl

/-- **Completeness (fixed), general form.**  Let (c, F) be a genuine model of the assertions.
Suppose the witness gives every declared constant its value (`hconst`) and gives, for every term
g of a list G of ground terms closed under taking the argument (`hG`), the key `(f g)` with the
true value F(gval g) (`happ`); suppose every ground application key loaded into the table is one
of these (`hks`) and all of them are loaded (`hall`), in any order; and suppose G names every value
that some ground term denotes (`hcovG`).  Then the fixed checker accepts. -/
theorem fixed_complete (decls : List Nat) (W ks : Wit) (φs : List Fm) (c F : Nat → Nat)
    (G : List Tm)
    (hsat : ∀ φ ∈ φs, rF decls c F [] φ = some true)
    (hconst : ∀ k ∈ decls, wget W (.sym k) = some (c k))
    (hG : ∀ g ∈ G, ground decls g = true ∧ ∀ s, g = .app s → s ∈ G)
    (happ : ∀ s ∈ G, wget W (.app s) = some (F (gval c F s)))
    (hks : ∀ g r, (Tm.app g, r) ∈ ks → ground decls g = true → g ∈ G ∧ r = F (gval c F g))
    (hall : ∀ g ∈ G, (Tm.app g, F (gval c F g)) ∈ ks)
    (hcovG : ∀ g, ground decls g = true → ∃ g' ∈ G, gval c F g' = gval c F g) :
    fixedCheck decls W ks φs = .accept := by
  obtain ⟨T, as0, hb, hT, has0, _, hcovks⟩ :=
    build_complete decls W c F G hconst hG happ ks hks [] [] (by intro e he; simp at he)
      (by intro e he; simp at he)
  have hcov : ∀ v, Den decls c F v → ∃ r, lk T v = some r := by
    intro v ⟨g, hg, hv⟩
    obtain ⟨g', hg'G, hg'v⟩ := hcovG g hg
    obtain ⟨r, hr⟩ := hcovks g' (hall g' hg'G) hg'G
    exact ⟨r, by rw [← hv, ← hg'v]; exact hr⟩
  obtain ⟨as, ha, hgas⟩ := runAsserts_complete decls W T c F hT hcov hconst φs hsat as0 has0
  have hc : congr T as.reverse = true :=
    congr_good F as.reverse T hT (fun e he => hgas e (List.mem_reverse.mp he))
  simp [fixedCheck, hb, ha, hc]

/-- the canonical ground-key encoding of a model: constants, then `(f g) ↦ F(gval g)` for g ∈ G -/
def canonW (decls : List Nat) (c F : Nat → Nat) (G : List Tm) : Wit :=
  decls.map (fun k => (Tm.sym k, c k)) ++ G.map (fun g => (Tm.app g, F (gval c F g)))

/-- **Completeness (fixed), canonical encoding.**  For every model (c, F) of the assertions and
every argument-closed list G of ground terms that names every ground-denoted value, the canonical
ground-key witness is accepted, whatever order (any permutation of the witness) the keys are
loaded in, e.g. the real sort by key length. -/
theorem fixed_complete_canon (decls : List Nat) (φs : List Fm) (c F : Nat → Nat) (G : List Tm)
    (ks : Wit) (hperm : ∀ e, e ∈ ks ↔ e ∈ canonW decls c F G)
    (hsat : ∀ φ ∈ φs, rF decls c F [] φ = some true)
    (hG : ∀ g ∈ G, ground decls g = true ∧ ∀ s, g = .app s → s ∈ G)
    (hcovG : ∀ g, ground decls g = true → ∃ g' ∈ G, gval c F g' = gval c F g) :
    fixedCheck decls (canonW decls c F G) ks φs = .accept := by
  apply fixed_complete decls _ ks φs c F G hsat
  · intro k hk
    apply wget_of
    · exact List.mem_append_left _ (List.mem_map.mpr ⟨k, hk, rfl⟩)
    · intro r' hr'
      rcases List.mem_append.mp hr' with h | h
      · obtain ⟨k', _, he⟩ := List.mem_map.mp h
        simp only [Prod.mk.injEq, Tm.sym.injEq] at he
        obtain ⟨rfl, rfl⟩ := he
        rfl
      · obtain ⟨g, _, he⟩ := List.mem_map.mp h
        simp at he
  · exact hG
  · intro s hs
    apply wget_of
    · exact List.mem_append_right _ (List.mem_map.mpr ⟨s, hs, rfl⟩)
    · intro r' hr'
      rcases List.mem_append.mp hr' with h | h
      · obtain ⟨k', _, he⟩ := List.mem_map.mp h
        simp at he
      · obtain ⟨g, _, he⟩ := List.mem_map.mp h
        simp only [Prod.mk.injEq, Tm.app.injEq] at he
        obtain ⟨rfl, rfl⟩ := he
        rfl
  · intro g r h _
    rcases List.mem_append.mp ((hperm _).mp h) with h' | h'
    · obtain ⟨k', _, he⟩ := List.mem_map.mp h'
      simp at he
    · obtain ⟨g', hg', he⟩ := List.mem_map.mp h'
      simp only [Prod.mk.injEq, Tm.app.injEq] at he
      obtain ⟨rfl, rfl⟩ := he
      exact ⟨hg', rfl⟩
  · intro g hg
    exact (hperm _).mpr (List.mem_append_right _ (List.mem_map.mpr ⟨g, hg, rfl⟩))
  · exact hcovG

/-! ## (a) The published counterexample: original rejects every witness -/

-- names: a = 0, b = 1, c = 2, let-variable x = 10; atoms "@a" = 0, "@b" = 1
def a : Tm := .sym 0
def b : Tm := .sym 1
def cc : Tm := .sym 2
def x : Tm := .sym 10
def f (t : Tm) : Tm := .app t
def neq (s t : Tm) : Fm := .not (.eq s t)

/-- `(distinct a b)`, `(let ((x a)) (= (f x) a))`, `(let ((x b)) (= (f x) b))` -/
def scopeConflict : List Fm :=
  [neq a b, .letF 10 a (.eq (f x) a), .letF 10 b (.eq (f x) b)]

theorem scopeConflict_sat :
    ∀ φ ∈ scopeConflict, rF [0, 1] (fun k => k) (fun v => v) [] φ = some true := by decide

/-- **(a) Original: no witness at all passes**, although the formula is satisfiable. -/
theorem orig_scopeConflict_unwinnable (W : Wit) : origCheck [0, 1] W scopeConflict ≠ .accept := by
  intro h
  unfold origCheck at h
  rcases ha : wget W a with _ | va <;> rcases hb : wget W b with _ | vb <;>
    rcases hx : wget W (f x) with _ | r <;>
    simp [runAsserts, scopeConflict, neq, cF, cT, lk, a, b, x, f] at h ha hb hx <;>
    simp [ha, hb, hx] at h
  · by_cases h1 : va = vb <;> simp [h1] at h
  · by_cases h1 : va = vb <;> by_cases h2 : r = va <;> by_cases h3 : r = vb <;>
      simp [h1, h2, h3] at h
    all_goals simp_all

/-- (a') and the fixed checker accepts the spec-form (ground-key) answer on it -/
def scGround : Wit := [(a, 0), (b, 1), (f a, 0), (f b, 1)]
theorem fixed_scopeConflict_ground : fixedCheck [0, 1] scGround scGround scopeConflict = .accept := by
  decide

/-! ## Differential check against the real evaluate.py (v1 and v2)
Expected verdicts: `repairs/smt_solver-v2/paired/results.md` (mini table) and
`evidence/scripts/smt_solver/mini_native_output.txt`; the same cases plus four new ones were
re-run on both real files (see the note); every row agrees, including the error class.
For these witnesses all ground app keys have equal text length, so the real length sort leaves the
dict order: `ks = W`. -/

def v1 (d : List Nat) (W : Wit) (φs : List Fm) : Verdict := origCheck d W φs
def v2 (d : List Nat) (W : Wit) (φs : List Fm) : Verdict := fixedCheck d W W φs

def singleLet : List Fm := [neq a b, .letF 10 a (.eq (f x) b)]
def groundCtl : List Fm := [neq a b, .eq (f a) a, .eq (f b) b]
def aliasC : List Fm := [neq a b, .eq a cc, .eq (f a) a, .eq (f cc) b]
def aliasCLet : List Fm := [neq a b, .eq a cc, .eq (f a) a, .letF 10 cc (.eq (f x) b)]
def unusedC : List Fm := [.eq a cc, .eq (f a) a]
/-- `(distinct a b)`, `(let ((a b)) (= (f a) a))`, `(= (f c) c)`: the let-binder shadows `a` -/
def shadow : List Fm := [neq a b, .letF 0 b (.eq (f a) a), .eq (f cc) cc]
/-- `(distinct a b)`, `(= (f a) b)`, `(let ((x (f a))) (= (f x) a))` -/
def nested : List Fm := [neq a b, .eq (f a) b, .letF 10 (f a) (.eq (f x) a)]

-- scope_conflict: v1 missing (f x) | v2 accept
example : v1 [0,1] scGround scopeConflict = .reject .missing ∧ v2 [0,1] scGround scopeConflict = .accept := by decide
-- scope_conflict_textkeys: v1 assertion false | v2 accept
example : v1 [0,1] (scGround ++ [(f x, 0)]) scopeConflict = .reject .falseAssert ∧
    v2 [0,1] (scGround ++ [(f x, 0)]) scopeConflict = .accept := by decide
-- scope_conflict_wrong: v1 missing | v2 assertion false
example : v1 [0,1] [(a,0),(b,1),(f a,0),(f b,0)] scopeConflict = .reject .missing ∧
    v2 [0,1] [(a,0),(b,1),(f a,0),(f b,0)] scopeConflict = .reject .falseAssert := by decide
-- single_let: v1 missing | v2 accept
example : v1 [0,1] [(a,0),(b,1),(f a,1)] singleLet = .reject .missing ∧
    v2 [0,1] [(a,0),(b,1),(f a,1)] singleLet = .accept := by decide
-- single_let_textkey: accept | accept
example : v1 [0,1] [(a,0),(b,1),(f x,1)] singleLet = .accept ∧
    v2 [0,1] [(a,0),(b,1),(f x,1)] singleLet = .accept := by decide
-- single_let_wrong: v1 missing | v2 assertion false
example : v1 [0,1] [(a,0),(b,1),(f a,0)] singleLet = .reject .missing ∧
    v2 [0,1] [(a,0),(b,1),(f a,0)] singleLet = .reject .falseAssert := by decide
-- ground_control: accept | accept ; ground_control_wrong: false | false
example : v1 [0,1] scGround groundCtl = .accept ∧ v2 [0,1] scGround groundCtl = .accept := by decide
example : v1 [0,1] [(a,0),(b,1),(f a,0),(f b,0)] groundCtl = .reject .falseAssert ∧
    v2 [0,1] [(a,0),(b,1),(f a,0),(f b,0)] groundCtl = .reject .falseAssert := by decide
-- alias_conflict: congruence | congruence ; alias_conflict_let: missing | congruence
def aliasW : Wit := [(a,0),(b,1),(cc,0),(f a,0),(f cc,1)]
example : v1 [0,1,2] aliasW aliasC = .reject .congruence ∧ v2 [0,1,2] aliasW aliasC = .reject .congruence := by decide
example : v1 [0,1,2] aliasW aliasCLet = .reject .missing ∧ v2 [0,1,2] aliasW aliasCLet = .reject .congruence := by decide

/-! ## (c) Counter-checks -/

/-- (c1) a deliberately wrong model (f b ↦ @a in scope_conflict) is rejected by both checkers,
and indeed no model with those values exists: f(b) = a contradicts `(let ((x b)) (= (f x) b))`. -/
theorem wrong_rejected_both :
    v1 [0,1] [(a,0),(b,1),(f a,0),(f b,0)] scopeConflict ≠ .accept ∧
    v2 [0,1] [(a,0),(b,1),(f a,0),(f b,0)] scopeConflict ≠ .accept := by decide

/-- (c2) Too strong: "the fixed checker accepts every witness the original accepts".  False on the
published intended change `unused_conflict` (f gets two values at one point via an unused key). -/
theorem too_strong_unused :
    v1 [0,1,2] [(a,0),(cc,0),(f a,0),(f cc,1)] unusedC = .accept ∧
    v2 [0,1,2] [(a,0),(cc,0),(f a,0),(f cc,1)] unusedC = .reject .congruence := by decide

/-- (c3) **Narrower than the published compatibility claim.**  A genuine model, written with
textual keys only (every key text occurs in the assertions), is ACCEPTED by the original and
REJECTED by the fixed checker, because the let-binder `a` shadows the declared constant `a`:
the textual key "(f a)" (meaning f at the shadowed a = b) is ground, so v2 loads it at f(val a). -/
def shadowText : Wit := [(a,0),(b,1),(cc,0),(f a,1),(f cc,0)]
theorem shadow_genuine :
    ∀ φ ∈ shadow, rF [0,1,2] (fun k => if k = 1 then 1 else 0) (fun v => v) [] φ = some true := by
  decide
theorem shadow_textual_regression :
    v1 [0,1,2] shadowText shadow = .accept ∧ v2 [0,1,2] shadowText shadow = .reject .congruence := by
  decide
/-- ... but it is not unwinnable: the ground-key encoding of the same model passes v2. -/
theorem shadow_ground_ok :
    v1 [0,1,2] [(a,0),(b,1),(cc,0),(f a,0),(f b,1)] shadow = .reject .falseAssert ∧
    v2 [0,1,2] [(a,0),(b,1),(cc,0),(f a,0),(f b,1)] shadow = .accept := by decide

/-- (c4) Too strong: "completeness without the coverage hypothesis": ground keys only for the
constants' arguments are not enough when a value is reached only through f; with the nested key
"(f (f a))" (sorted after "(f a)" by length) the same model passes. -/
theorem coverage_needed :
    v2 [0,1] [(a,0),(b,1),(f a,1)] nested = .reject .missing ∧
    fixedCheck [0,1] [(a,0),(b,1),(f a,1),(f (f a),0)] [(a,0),(b,1),(f a,1),(f (f a),0)] nested
      = .accept := by decide

#print axioms orig_eq_fixed_empty
#print axioms fixed_sound
#print axioms orig_sound
#print axioms fixed_complete
#print axioms fixed_complete_canon
#print axioms scopeConflict_sat
#print axioms orig_scopeConflict_unwinnable
#print axioms fixed_scopeConflict_ground
#print axioms wrong_rejected_both
#print axioms too_strong_unused
#print axioms shadow_genuine
#print axioms shadow_textual_regression
#print axioms shadow_ground_ok
#print axioms coverage_needed

end EbvSmt
