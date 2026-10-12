/-
EdgeBench Verified -- warehouse_forklift_routing lower bound (kernel-checked).

Source of the rules: the ORIGINAL tester `tools/bin/tester` shipped in
  seededge/edgebench.judge.warehouse_forklift_routing@sha256:ac7fdf03bb73d0f9ded21662c7c3ac246ce521ee5e6b237978a2799c7bc29cb3
  sha256(tools/bin/tester) = 277f4841a25a11a9e9d7cbb751e2b407bd7cbf7f1eeba47c9821085db646bdd3
Source-to-model mapping (tester line numbers in brackets):
  * grid R x C, cells (r,c) with 0<=r<R, 0<=c<C; forklift starts at (0,0) empty  [49-51]
  * N/S/W/E: destination must be in bounds; if carrying, destination must be empty;
    an EMPTY forklift may enter an occupied cell (the tester's `pass`)            [63-76]
  * P: at (0,0), not carrying, fewer than n=R*C-1 goods arrived; picks ship[arr]  [78-92]
  * D: at (0,0), carrying, all n arrived, carried id = dispatched+1              [94-111]
  * L<d>: neighbour in bounds, not carrying, neighbour occupied -> carry it       [113-135]
  * U<d>: neighbour in bounds, carrying, neighbour empty -> store it              [137-159]
  * any other character, or L/U without a following direction: reject           [115-121,161]
  * accept iff the whole string executes and dispatched = n                      [165-167]
  * S = number of characters of the (stripped) line                              [41-42]
  The tester encodes "not carrying" as 0 and good ids as positive integers; the model
  uses `Option ℕ`.  This is faithful because every input arrival line is a permutation
  of 1..n (checked on the 50 inputs by scripts/warehouse_forklift_routing/lean_check.py).
  The tester's `all_arrived` flag equals `arr ≥ n` because arr starts at 0 < n and only
  P increments it.  The 500000-character cap only rejects more strings, so it is omitted
  (omitting a rejection condition only strengthens a lower bound on accepted strings).
-/
import Mathlib.Tactic

namespace EbvWarehouse

open Finset

inductive Dir | N | S | W | E
  deriving DecidableEq, Repr

inductive Cmd | mv (d : Dir) | P | D | L (d : Dir) | U (d : Dir)
  deriving DecidableEq, Repr

def Cmd.cost : Cmd → ℕ
  | .L _ => 2
  | .U _ => 2
  | _ => 1

def charDir : Char → Option Dir
  | 'N' => some .N
  | 'S' => some .S
  | 'W' => some .W
  | 'E' => some .E
  | _ => none

def cmdLU (c : Char) (d : Dir) : Cmd := if c = 'L' then Cmd.L d else Cmd.U d

theorem cmdLU_cost (c : Char) (d : Dir) : (cmdLU c d).cost = 2 := by
  unfold cmdLU; split <;> rfl

/-- Tokeniser identical to the tester's character loop. -/
def parse : List Char → Option (List Cmd)
  | [] => some []
  | c :: rest =>
    if c = 'P' then (parse rest).map (Cmd.P :: ·)
    else if c = 'D' then (parse rest).map (Cmd.D :: ·)
    else if c = 'L' ∨ c = 'U' then
      match rest with
      | [] => none
      | c2 :: rest2 =>
        match charDir c2 with
        | none => none
        | some d => (parse rest2).map (cmdLU c d :: ·)
    else
      match charDir c with
      | none => none
      | some d => (parse rest).map (Cmd.mv d :: ·)

def cost (cs : List Cmd) : ℕ := (cs.map Cmd.cost).sum

theorem cost_cons (c : Cmd) (cs : List Cmd) : cost (c :: cs) = c.cost + cost cs := by
  simp [cost]

/-- The command list produced by the tokeniser has total cost = string length. -/
theorem parse_cost : ∀ (n : ℕ) (s : List Char), s.length = n → ∀ (cs : List Cmd),
    parse s = some cs → cost cs = s.length := by
  intro n
  induction n using Nat.strong_induction_on with
  | _ n ih =>
  intro s hn cs h
  cases s with
  | nil => simp [parse] at h; subst h; rfl
  | cons c rest =>
    have ihr : ∀ t : List Char, t.length < n → ∀ cs, parse t = some cs → cost cs = t.length :=
      fun t ht cs h => ih t.length ht t rfl cs h
    simp only [List.length_cons] at hn
    unfold parse at h
    split_ifs at h with h1 h2 h3
    · obtain ⟨a, ha, rfl⟩ := Option.map_eq_some_iff.1 h
      rw [cost_cons, ihr rest (by omega) a ha]; simp [Cmd.cost]; omega
    · obtain ⟨a, ha, rfl⟩ := Option.map_eq_some_iff.1 h
      rw [cost_cons, ihr rest (by omega) a ha]; simp [Cmd.cost]; omega
    · split at h
      · simp at h
      · rename_i c2 rest2
        split at h
        · simp at h
        · obtain ⟨a, ha, rfl⟩ := Option.map_eq_some_iff.1 h
          simp only [List.length_cons] at hn
          rw [cost_cons, ihr rest2 (by omega) a ha, cmdLU_cost]; simp; omega
    · split at h
      · simp at h
      · obtain ⟨a, ha, rfl⟩ := Option.map_eq_some_iff.1 h
        rw [cost_cons, ihr rest (by omega) a ha]; simp [Cmd.cost]; omega

structure St where
  r : ℕ
  c : ℕ
  carry : Option ℕ
  grid : ℕ × ℕ → Option ℕ
  arr : ℕ
  disp : ℕ

section Model
variable (R C : ℕ) (ship : ℕ → ℕ)

def nbr : Dir → ℕ → ℕ → Option (ℕ × ℕ)
  | .N, r, c => if 0 < r then some (r - 1, c) else none
  | .S, r, c => if r + 1 < R then some (r + 1, c) else none
  | .W, r, c => if 0 < c then some (r, c - 1) else none
  | .E, r, c => if c + 1 < C then some (r, c + 1) else none

def step (s : St) : Cmd → Option St
  | .mv d =>
      match nbr R C d s.r s.c with
      | none => none
      | some q =>
          if s.carry.isSome ∧ (s.grid q).isSome then none
          else some { s with r := q.1, c := q.2 }
  | .P =>
      if s.r = 0 ∧ s.c = 0 ∧ s.carry = none ∧ s.arr < R * C - 1 then
        some { s with carry := some (ship s.arr), arr := s.arr + 1 }
      else none
  | .D =>
      match s.carry with
      | none => none
      | some g =>
          if s.r = 0 ∧ s.c = 0 ∧ R * C - 1 ≤ s.arr ∧ g = s.disp + 1 then
            some { s with carry := none, disp := s.disp + 1 }
          else none
  | .L d =>
      match nbr R C d s.r s.c with
      | none => none
      | some q =>
          match s.carry, s.grid q with
          | none, some g => some { s with carry := some g, grid := Function.update s.grid q none }
          | _, _ => none
  | .U d =>
      match nbr R C d s.r s.c with
      | none => none
      | some q =>
          match s.carry, s.grid q with
          | some g, none => some { s with carry := none, grid := Function.update s.grid q (some g) }
          | _, _ => none

def run : St → List Cmd → Option St
  | s, [] => some s
  | s, c :: cs =>
      match step R C ship s c with
      | none => none
      | some t => run t cs

def init : St := ⟨0, 0, none, fun _ => none, 0, 0⟩

/-- The tester accepts the command string `str` for this case. -/
def Accepts (str : List Char) : Prop :=
  ∃ cs e, parse str = some cs ∧ run R C ship init cs = some e ∧ e.disp = R * C - 1

/-! ### Potential function -/

def cells : Finset (ℕ × ℕ) := range R ×ˢ range C

def occ (s : St) : Finset (ℕ × ℕ) := (cells R C).filter (fun p => (s.grid p).isSome)

def fpos (s : St) : ℤ := (s.r : ℤ) + s.c

def wt (p : ℕ × ℕ) : ℤ := (p.1 : ℤ) + p.2

/-- Φ = sum over goods present in the warehouse of r+c (stored goods + carried good). -/
def Phi (s : St) : ℤ := (∑ p ∈ occ R C s, wt p) + (if s.carry.isSome then fpos s else 0)

def Inv (s : St) : Prop :=
  s.r < R ∧ s.c < C ∧ (∀ p, (s.grid p).isSome → p.1 < R ∧ p.2 < C) ∧
  (occ R C s).card + (if s.carry.isSome then 1 else 0) + s.disp = s.arr ∧ s.arr ≤ R * C - 1

theorem nbr_spec {d : Dir} {r c : ℕ} {q : ℕ × ℕ} (hr : r < R) (hc : c < C)
    (h : nbr R C d r c = some q) :
    q.1 < R ∧ q.2 < C ∧ (wt q = (r : ℤ) + c + 1 ∨ wt q = (r : ℤ) + c - 1) := by
  cases d <;> simp only [nbr] at h <;> split_ifs at h with h1 <;> simp at h <;> subst h <;>
    simp [wt] <;> omega

theorem occ_congr {s t : St} (h : t.grid = s.grid) : occ R C t = occ R C s := by
  simp [occ, h]

theorem mem_occ (s : St) (q : ℕ × ℕ) : q ∈ occ R C s ↔ (q.1 < R ∧ q.2 < C) ∧ (s.grid q).isSome := by
  simp [occ, cells]

theorem occ_erase {s t : St} {q : ℕ × ℕ} (hgrid : t.grid = Function.update s.grid q none) :
    occ R C t = (occ R C s).erase q := by
  ext p
  by_cases hp : p = q
  · subst hp; simp [occ, hgrid]
  · simp [occ, cells, hgrid, hp]

theorem occ_insert {s t : St} {q : ℕ × ℕ} (hq : q.1 < R ∧ q.2 < C) (g : ℕ)
    (hgrid : t.grid = Function.update s.grid q (some g)) :
    occ R C t = insert q (occ R C s) := by
  ext p
  by_cases hp : p = q
  · subst hp; simp [occ, cells, hgrid, hq]
  · simp [occ, cells, hgrid, hp]

/-- One step preserves the invariant and bounds the change of both potentials:
    V1 = 2Φ - f(forklift) + arrived,  V2 = -2Φ + f(forklift) + dispatched. -/
theorem step_props (s t : St) (cmd : Cmd) (hs : Inv R C s) (h : step R C ship s cmd = some t) :
    Inv R C t ∧
    2 * Phi R C t - fpos t + t.arr ≤ 2 * Phi R C s - fpos s + s.arr + cmd.cost ∧
    -2 * Phi R C t + fpos t + t.disp ≤ -2 * Phi R C s + fpos s + s.disp + cmd.cost := by
  obtain ⟨hr, hc, hg, hcard, harr⟩ := hs
  cases cmd with
  | mv d =>
      simp only [step] at h
      split at h
      · simp at h
      · rename_i q hq
        obtain ⟨hq1, hq2, hw⟩ := nbr_spec R C hr hc hq
        split_ifs at h with hblk
        simp only [Option.some.injEq] at h
        have hocc : occ R C t = occ R C s := occ_congr R C (by rw [← h])
        have e1 : t.r = q.1 := by rw [← h]
        have e2 : t.c = q.2 := by rw [← h]
        have e3 : t.carry = s.carry := by rw [← h]
        have e4 : t.grid = s.grid := by rw [← h]
        have e5 : t.arr = s.arr := by rw [← h]
        have e6 : t.disp = s.disp := by rw [← h]
        simp only [wt] at hw
        refine ⟨⟨by omega, by omega, by rw [e4]; exact hg, by rw [hocc, e3, e6, e5]; exact hcard,
          by omega⟩, ?_, ?_⟩
        · simp only [Phi, fpos, hocc, e1, e2, e3, e5, Cmd.cost]
          split_ifs <;> push_cast <;> omega
        · simp only [Phi, fpos, hocc, e1, e2, e3, e6, Cmd.cost]
          split_ifs <;> push_cast <;> omega
  | P =>
      simp only [step] at h
      split_ifs at h with hP
      obtain ⟨h0, h0', hnone, hlt⟩ := hP
      simp only [Option.some.injEq] at h
      have hocc : occ R C t = occ R C s := occ_congr R C (by rw [← h])
      have e1 : t.r = s.r := by rw [← h]
      have e2 : t.c = s.c := by rw [← h]
      have e3 : t.carry = some (ship s.arr) := by rw [← h]
      have e4 : t.grid = s.grid := by rw [← h]
      have e5 : t.arr = s.arr + 1 := by rw [← h]
      have e6 : t.disp = s.disp := by rw [← h]
      simp [hnone] at hcard
      refine ⟨⟨by omega, by omega, by rw [e4]; exact hg, ?_, by omega⟩, ?_, ?_⟩
      · rw [hocc, e3, e6, e5]; simp; omega
      · simp only [Phi, fpos, hocc, e1, e2, e3, e5, hnone, h0, h0', Cmd.cost]; simp; linarith
      · simp only [Phi, fpos, hocc, e1, e2, e3, e6, hnone, h0, h0', Cmd.cost]; simp
  | D =>
      simp only [step] at h
      split at h
      · simp at h
      · rename_i g hcs
        split_ifs at h with hD
        obtain ⟨h0, h0', hle, hgd⟩ := hD
        simp only [Option.some.injEq] at h
        have hocc : occ R C t = occ R C s := occ_congr R C (by rw [← h])
        have e1 : t.r = s.r := by rw [← h]
        have e2 : t.c = s.c := by rw [← h]
        have e3 : t.carry = none := by rw [← h]
        have e4 : t.grid = s.grid := by rw [← h]
        have e5 : t.arr = s.arr := by rw [← h]
        have e6 : t.disp = s.disp + 1 := by rw [← h]
        simp [hcs] at hcard
        refine ⟨⟨by omega, by omega, by rw [e4]; exact hg, ?_, by omega⟩, ?_, ?_⟩
        · rw [hocc, e3, e6, e5]; simp; omega
        · simp only [Phi, fpos, hocc, e1, e2, e3, e5, hcs, h0, h0', Cmd.cost]; simp
        · simp only [Phi, fpos, hocc, e1, e2, e3, e6, hcs, h0, h0', Cmd.cost]; simp; omega
  | L d =>
      simp only [step] at h
      split at h
      · simp at h
      · rename_i q hq
        obtain ⟨hq1, hq2, hw⟩ := nbr_spec R C hr hc hq
        split at h
        · rename_i g hcs hgq
          simp only [Option.some.injEq] at h
          have e1 : t.r = s.r := by rw [← h]
          have e2 : t.c = s.c := by rw [← h]
          have e3 : t.carry = some g := by rw [← h]
          have e4 : t.grid = Function.update s.grid q none := by rw [← h]
          have e5 : t.arr = s.arr := by rw [← h]
          have e6 : t.disp = s.disp := by rw [← h]
          have hocc := occ_erase R C e4
          have hmem : q ∈ occ R C s := (mem_occ R C s q).2 ⟨⟨hq1, hq2⟩, by simp [hgq]⟩
          have hsum := Finset.sum_erase_eq_sub (f := wt) hmem
          have hcard' := Finset.card_erase_of_mem hmem
          have hpos : 0 < (occ R C s).card := Finset.card_pos.2 ⟨q, hmem⟩
          simp [hcs] at hcard
          simp only [wt] at hw hsum
          refine ⟨⟨by omega, by omega, ?_, ?_, by omega⟩, ?_, ?_⟩
          · intro p hp
            rw [e4] at hp
            by_cases hpq : p = q
            · subst hpq; simp at hp
            · rw [Function.update_of_ne hpq] at hp; exact hg p hp
          · rw [hocc, hcard', e3, e6, e5]; simp; omega
          · simp only [Phi, fpos, Cmd.cost, hocc, e1, e2, e3, e5, hcs, wt]; rw [hsum]; simp; omega
          · simp only [Phi, fpos, Cmd.cost, hocc, e1, e2, e3, e6, hcs, wt]; rw [hsum]; simp; omega
        · simp at h
  | U d =>
      simp only [step] at h
      split at h
      · simp at h
      · rename_i q hq
        obtain ⟨hq1, hq2, hw⟩ := nbr_spec R C hr hc hq
        split at h
        · rename_i g hcs hgq
          simp only [Option.some.injEq] at h
          have e1 : t.r = s.r := by rw [← h]
          have e2 : t.c = s.c := by rw [← h]
          have e3 : t.carry = none := by rw [← h]
          have e4 : t.grid = Function.update s.grid q (some g) := by rw [← h]
          have e5 : t.arr = s.arr := by rw [← h]
          have e6 : t.disp = s.disp := by rw [← h]
          have hocc := occ_insert R C ⟨hq1, hq2⟩ g e4
          have hnmem : q ∉ occ R C s := by rw [mem_occ]; simp [hgq]
          have hsum := Finset.sum_insert (f := wt) hnmem
          have hcard' := Finset.card_insert_of_notMem hnmem
          simp [hcs] at hcard
          simp only [wt] at hw hsum
          refine ⟨⟨by omega, by omega, ?_, ?_, by omega⟩, ?_, ?_⟩
          · intro p hp
            rw [e4] at hp
            by_cases hpq : p = q
            · subst hpq; exact ⟨hq1, hq2⟩
            · rw [Function.update_of_ne hpq] at hp; exact hg p hp
          · rw [hocc, hcard', e3, e6, e5]; simp; omega
          · simp only [Phi, fpos, Cmd.cost, hocc, e1, e2, e3, e5, hcs, wt]; rw [hsum]; simp; omega
          · simp only [Phi, fpos, Cmd.cost, hocc, e1, e2, e3, e6, hcs, wt]; rw [hsum]; simp; omega
        · simp at h

theorem run_props : ∀ (cs : List Cmd) (s e : St), Inv R C s → run R C ship s cs = some e →
    Inv R C e ∧
    2 * Phi R C e - fpos e + e.arr ≤ 2 * Phi R C s - fpos s + s.arr + cost cs ∧
    -2 * Phi R C e + fpos e + e.disp ≤ -2 * Phi R C s + fpos s + s.disp + cost cs := by
  intro cs
  induction cs with
  | nil => intro s e _ h; simp [run] at h; subst h; simp_all [cost]
  | cons c cs ih =>
      intro s e hs h
      simp only [run] at h
      split at h
      · simp at h
      · rename_i t ht
        obtain ⟨ht1, ht2, ht3⟩ := step_props R C ship s t c hs ht
        obtain ⟨he1, he2, he3⟩ := ih t e ht1 h
        refine ⟨he1, ?_, ?_⟩ <;> rw [cost_cons] <;> push_cast <;> omega

/-! ### The moment τ: just after the first U following the last P -/

def Pre (s : St) : Prop :=
  s.disp = 0 ∧ (s.arr < R * C - 1 ∨ (s.arr = R * C - 1 ∧ s.carry = some (ship (R * C - 2))))

def Goal (s : St) : Prop := s.carry = none ∧ s.arr = R * C - 1 ∧ s.disp = 0

theorem pre_step (hn : 2 ≤ R * C) (hlast : ship (R * C - 2) ≠ 1) (s t : St) (cmd : Cmd)
    (hs : Pre R C ship s) (h : step R C ship s cmd = some t) : Pre R C ship t ∨ Goal R C t := by
  obtain ⟨hd, hpre⟩ := hs
  cases cmd with
  | mv d =>
      simp only [step] at h
      split at h
      · simp at h
      · split_ifs at h; simp at h; subst h; left; exact ⟨hd, hpre⟩
  | P =>
      simp only [step] at h
      split_ifs at h with hP
      simp at h; subst h
      left; refine ⟨hd, ?_⟩
      simp only
      by_cases hlt : s.arr + 1 < R * C - 1
      · left; exact hlt
      · right; refine ⟨by omega, ?_⟩
        have : s.arr = R * C - 2 := by omega
        rw [this]
  | D =>
      simp only [step] at h
      split at h
      · simp at h
      · rename_i g hcs
        split_ifs at h with hD
        exfalso
        rcases hpre with hlt | ⟨_, hc⟩
        · omega
        · rw [hcs] at hc; simp at hc; subst hc; apply hlast; omega
  | L d =>
      simp only [step] at h
      split at h
      · simp at h
      · split at h
        · rename_i g hcs _
          simp at h; subst h; left
          rcases hpre with hlt | ⟨_, hc⟩
          · exact ⟨hd, Or.inl hlt⟩
          · rw [hcs] at hc; simp at hc
        · simp at h
  | U d =>
      simp only [step] at h
      split at h
      · simp at h
      · split at h
        · simp at h; subst h
          rcases hpre with hlt | ⟨heq, _⟩
          · left; exact ⟨hd, Or.inl hlt⟩
          · right; exact ⟨rfl, heq, hd⟩
        · simp at h

theorem split_tau (hn : 2 ≤ R * C) (hlast : ship (R * C - 2) ≠ 1) :
    ∀ (cs : List Cmd) (s e : St), Pre R C ship s → run R C ship s cs = some e → ¬ Pre R C ship e →
    ∃ c1 c2 t, cs = c1 ++ c2 ∧ run R C ship s c1 = some t ∧ run R C ship t c2 = some e ∧ Goal R C t := by
  intro cs
  induction cs with
  | nil => intro s e hs h hne; simp [run] at h; subst h; exact absurd hs hne
  | cons c cs ih =>
      intro s e hs h hne
      simp only [run] at h
      split at h
      · simp at h
      · rename_i t ht
        rcases pre_step R C ship hn hlast s t c hs ht with hp | hg
        · obtain ⟨c1, c2, u, rfl, h1, h2, hgu⟩ := ih t e hp h hne
          refine ⟨c :: c1, c2, u, rfl, ?_, h2, hgu⟩
          simp [run, ht, h1]
        · refine ⟨[c], cs, t, rfl, ?_, h, hg⟩
          simp [run, ht]

/-! ### Counting -/

theorem sum_cells_two : 2 * (∑ p ∈ cells R C, wt p) = (R : ℤ) * C * ((R : ℤ) + C - 2) := by
  have h1 : (∑ p ∈ cells R C, wt p) =
      (C : ℤ) * (∑ i ∈ range R, (i : ℤ)) + (R : ℤ) * (∑ j ∈ range C, (j : ℤ)) := by
    simp only [cells, wt, Finset.sum_product, Finset.sum_add_distrib, Finset.sum_const,
      Finset.card_range, nsmul_eq_mul, Finset.mul_sum]
  have hR := Finset.sum_range_id_mul_two R
  have hC := Finset.sum_range_id_mul_two C
  have eR : (∑ i ∈ range R, (i : ℤ)) * 2 = (R : ℤ) * ((R : ℤ) - 1) := by
    have : ((∑ i ∈ range R, i : ℕ) : ℤ) * 2 = ((R * (R - 1) : ℕ) : ℤ) := by exact_mod_cast hR
    rcases Nat.eq_zero_or_pos R with h0 | hpos
    · subst h0; simp
    · push_cast [Nat.cast_sub hpos] at this; exact this
  have eC : (∑ j ∈ range C, (j : ℤ)) * 2 = (C : ℤ) * ((C : ℤ) - 1) := by
    have : ((∑ i ∈ range C, i : ℕ) : ℤ) * 2 = ((C * (C - 1) : ℕ) : ℤ) := by exact_mod_cast hC
    rcases Nat.eq_zero_or_pos C with h0 | hpos
    · subst h0; simp
    · push_cast [Nat.cast_sub hpos] at this; exact this
  rw [h1]; linear_combination (C : ℤ) * eR + (R : ℤ) * eC

/-- At τ the n = RC-1 stored goods fill all cells but one, so Φ(τ) ≥ Σ_cells (r+c) - (R+C-2). -/
theorem phi_tau (hR : 1 ≤ R) (hC : 1 ≤ C) (t : St) (hi : Inv R C t) (hg : Goal R C t) :
    (∑ p ∈ cells R C, wt p) - ((R : ℤ) + C - 2) ≤ Phi R C t := by
  obtain ⟨_, _, _, hcard, _⟩ := hi
  obtain ⟨hcn, harr, hd⟩ := hg
  have hsub : occ R C t ⊆ cells R C := Finset.filter_subset _ _
  have hcells : (cells R C).card = R * C := by simp [cells]
  have hocard : (occ R C t).card = R * C - 1 := by simp [hcn] at hcard; omega
  have hsd : (cells R C \ occ R C t).card = 1 := by
    rw [Finset.card_sdiff, Finset.inter_eq_left.2 hsub, hcells, hocard]
    have : 1 ≤ R * C := Nat.one_le_iff_ne_zero.2 (by positivity)
    omega
  obtain ⟨p, hp⟩ := Finset.card_eq_one.1 hsd
  have hsum := Finset.sum_sdiff (f := wt) hsub
  rw [hp, Finset.sum_singleton] at hsum
  have hpmem : p ∈ cells R C := by
    have : p ∈ cells R C \ occ R C t := by rw [hp]; simp
    exact (Finset.mem_sdiff.1 this).1
  simp [cells] at hpmem
  have hwp : wt p ≤ (R : ℤ) + C - 2 := by simp [wt]; omega
  simp only [Phi, hcn]; simp
  linarith

theorem phi_end (e : St) (hi : Inv R C e) (hd : e.disp = R * C - 1) : Phi R C e = 0 := by
  obtain ⟨_, _, _, hcard, harr⟩ := hi
  have h0 : (occ R C e).card = 0 := by omega
  have hc : e.carry = none := by
    cases hce : e.carry with
    | none => rfl
    | some g => simp [hce] at hcard; omega
  rw [Finset.card_eq_zero] at h0
  simp [Phi, h0, hc]

/-- **Main theorem.** Every command string that the tester accepts as completing the case
    has length S ≥ 2RC(R+C-1) - 6(R+C-2) - 2, provided the last arrival is not good 1. -/
theorem lower_bound (hR : 1 ≤ R) (hC : 1 ≤ C) (hn : 2 ≤ R * C) (hlast : ship (R * C - 2) ≠ 1)
    (str : List Char) (hacc : Accepts R C ship str) :
    2 * (R : ℤ) * C * ((R : ℤ) + C - 1) - 6 * ((R : ℤ) + C - 2) - 2 ≤ (str.length : ℤ) := by
  obtain ⟨cs, e, hp, hrun, hd⟩ := hacc
  have hcost := parse_cost _ str rfl cs hp
  have hinit : Inv R C init := by
    refine ⟨show 0 < R by omega, show 0 < C by omega, by simp [init], ?_, by simp [init]⟩
    simp [init, occ]
  have hpre : Pre R C ship init := ⟨rfl, Or.inl (by simp [init]; omega)⟩
  have hne : ¬ Pre R C ship e := by intro h; have := h.1; omega
  obtain ⟨c1, c2, t, rfl, h1, h2, hg⟩ := split_tau R C ship hn hlast cs init e hpre hrun hne
  obtain ⟨hti, ht1, -⟩ := run_props R C ship c1 init t hinit h1
  obtain ⟨hei, -, he2⟩ := run_props R C ship c2 t e hti h2
  have hphi_t := phi_tau R C hR hC t hti hg
  have hphi_e := phi_end R C e hei hd
  have hsc := sum_cells_two R C
  obtain ⟨htr, htc, _, _, _⟩ := hti
  obtain ⟨hcn, harr, hdt⟩ := hg
  have hfe : 0 ≤ fpos e := by simp [fpos]; positivity
  have hft : fpos t ≤ (R : ℤ) + C - 2 := by simp [fpos]; omega
  have hPhi0 : Phi R C init = 0 := by simp [Phi, init, occ]
  have hf0 : fpos init = 0 := by simp [fpos, init]
  have hlen : (str.length : ℤ) = (cost c1 : ℤ) + cost c2 := by
    rw [← hcost]; simp [cost, List.map_append, List.sum_append]
  rw [hlen]
  rw [hPhi0, hf0, harr] at ht1
  rw [hphi_e, hd, hdt] at he2
  simp [init] at ht1
  have hn' : ((R * C - 1 : ℕ) : ℤ) = (R : ℤ) * C - 1 := by push_cast [Nat.cast_sub (by omega : 1 ≤ R * C)]; ring
  rw [hn'] at ht1 he2
  push_cast at ht1 he2
  linarith

/-- Corollary: per-case score bound (exact rationals). -/
theorem score_bound (hR : 1 ≤ R) (hC : 1 ≤ C) (hn : 2 ≤ R * C) (hlast : ship (R * C - 2) ≠ 1)
    (str : List Char) (hacc : Accepts R C ship str) :
    (20 : ℚ) - 6 * ((R : ℚ) + C - 2) / ((R : ℚ) + C - 1) ≤
      ((str.length : ℚ) + 2) / ((R : ℚ) + C - 1) - 2 * R * C + 20 := by
  have hb := lower_bound R C ship hR hC hn hlast str hacc
  have hb' : 2 * (R : ℚ) * C * ((R : ℚ) + C - 1) - 6 * ((R : ℚ) + C - 2) - 2 ≤ (str.length : ℚ) := by
    exact_mod_cast hb
  have hpos : (0 : ℚ) < (R : ℚ) + C - 1 := by
    have : (1 : ℚ) ≤ R := by exact_mod_cast hR
    have : (1 : ℚ) ≤ C := by exact_mod_cast hC
    linarith
  have key : (20 : ℚ) - 6 * ((R : ℚ) + C - 2) / ((R : ℚ) + C - 1) + 2 * R * C - 20 ≤
      ((str.length : ℚ) + 2) / ((R : ℚ) + C - 1) := by
    rw [le_div_iff₀ hpos]
    have : (20 - 6 * ((R : ℚ) + C - 2) / ((R : ℚ) + C - 1) + 2 * R * C - 20) * ((R : ℚ) + C - 1) =
        2 * R * C * ((R : ℚ) + C - 1) - 6 * ((R : ℚ) + C - 2) := by
      field_simp; ring
    rw [this]; linarith
  linarith

end Model


end EbvWarehouse

#print axioms EbvWarehouse.parse_cost
#print axioms EbvWarehouse.lower_bound
#print axioms EbvWarehouse.score_bound
