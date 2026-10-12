/-
EdgeBench Verified -- college_english_exam_bank: rubric aggregation of the AI-graded score,
original (v1) and fixed (v2) grader.  Core Lean only (no Mathlib).

Code modelled
  judge image seededge/edgebench.judge.college_english_exam_bank@sha256:8e9eec1057c7ab1b...58a8
  /home/workspace/scoring/grade_with_codex.py
    v1 sha256 b8b2824c0d5483f8f433d4fc59e11efb8c7c18d1126b60987c99a1c2cb0e4b3f (93823 B)
    v2 sha256 1d941b58853dbd89b490b38029de23f306a4138a7c0949360754e5924bf054a6 (98308 B)
       (earlier fixed grader, superseded 2026-10-12; `precheck`/`fixed` below)
    revised v2 sha256 87f0e3406fadd6d09ee156bfdd84a491b0d1b9944a01a645244a3e510aed9d35 (98445 B)
       (`precheck2`/`fixed2` at the end: the deduction check reconciles the normalised rows)
  /home/workspace/scoring/rubrics.json sha256 d05f344e0f76ceeda7fb8c1d927df662b3f5f87c91631cd9b3fdebc6162bf603
Source-to-model mapping (v1 line numbers; v2 adds l.1154-1218 and the loop at l.1679-1709):
  * `vetoFn`      <- _rule_level_veto_triggered               v1 l.1067-1096
  * `normalize`   <- _validate_result, per row                v1 l.1154-1214
                     (score default 0, non-numeric -> 0, clamp to the ROW's max_score, veto flag -> 0;
                      checkpoint score non-numeric -> 0, then max(0, .); veto_reason kept only if the
                      row's veto flag is set, l.1207)
  * `ruleScore`   <- reconcile_result_with_rubrics, deductive rule with scoring_details
                     v1 l.1249-1349 (src = {} for a rule with no row, l.1255)
  * `lastMatch`   <- by_id = {rule_id: row} (last row wins)   v1 l.1251
  * `orig`        <- raw_total over the rubric                v1 l.1403; total = raw_total/max_total*100
                     (l.1652-1656); max_total = 200 half-points here, so total% = orig/2.
  * `rowOK`,`precheck` <- v2 _require_complete_rule_scores, _has_complete_checkpoints,
                     _require_recorded_deductions             v2 l.1154-1218
  * `fixed`       <- v2 _validate_result: precheck, then the unchanged v1 pipeline  v2 l.1219-1221
  * `fixedRun`    <- v2 main() re-ask loop                    v2 l.1679-1709
Units: half-points (every rubric value is a multiple of 0.5), so all arithmetic is exact in Int.
Abstractions: a row's text fields are reduced to the booleans the code derives from them
(veto marker / veto-condition text in veto_reason, in reason; floor wording in reason); the
200-character truncation of `reason` (l.1213) is not modelled (see the note); checkpoint entries
that are not JSON objects are not modelled; all rubric rules are deductive with non-empty
scoring_details (checked below by `decide` on the real rubric).
-/

namespace EbvCollege

/-- A rule-level "score" field as sent by the model. -/
inductive SF | absent | num (v : Int) | junk
  deriving DecidableEq, Repr

def SF.val : SF → Int
  | .num v => v
  | _ => 0

structure Rule where
  id : Nat
  max : Int
  details : List (Int × Bool)   -- (points, repeatable?)
  hasVeto : Bool                -- rule has non-empty veto_conditions
  deriving Repr

/-- A score row as the grading model sent it. `cps`: `some v` = checkpoint with numeric score,
`none` = checkpoint whose score is missing or non-numeric. -/
structure Row where
  id : Nat
  score : SF
  rowMax : Option Int
  cps : List (Option Int)
  rvt : Bool      -- rule_veto_triggered truthy
  vt : Bool       -- veto_triggered truthy
  vr : Bool       -- veto_reason contains a veto marker or a veto-condition text
  rCond : Bool    -- reason contains a veto-condition text
  rMark : Bool    -- reason contains a veto marker word
  floor : Bool    -- reason matches _reason_declares_deductive_floor
  deriving Repr

/-- What reconcile reads from `src`. `score = none` only for the empty src `{}`. -/
structure Src where
  score : Option Int
  cps : List Int
  flag : Bool
  vr : Bool
  rCond : Bool
  rMark : Bool
  floor : Bool

def emptySrc : Src := ⟨none, [], false, false, false, false, false⟩

/-- _rule_level_veto_triggered for a deductive rule. `sz`: rule score is numeric 0;
`cz`: no checkpoint has a nonzero numeric score. -/
def vetoFn (r : Rule) (flag vr rCond rMark sz cz : Bool) : Bool :=
  r.hasVeto && (flag || vr || rCond || (sz && cz && rMark))

/-- _validate_result applied to one row. -/
def normalize (w : Row) : Src :=
  let flag := w.rvt || w.vt
  { score := some (if flag then 0 else max 0 (min w.score.val (w.rowMax.getD 0))),
    cps := w.cps.map (fun c => max 0 (c.getD 0)),
    flag := flag, vr := flag && w.vr, rCond := w.rCond, rMark := w.rMark, floor := w.floor }

def dedTerm (p : Int) (rep : Bool) (c : Int) : Int :=
  if rep then max 0 c else max 0 (min c p)

def dedSum : List (Int × Bool) → List Int → Int
  | [], _ => 0
  | (p, b) :: ds, cs => dedTerm p b (cs.headD 0) + dedSum ds cs.tail

/-- reconcile_result_with_rubrics, one deductive rule with scoring_details. -/
def ruleScore (r : Rule) (s : Src) : Int :=
  let n := r.details.length
  if vetoFn r s.flag s.vr s.rCond s.rMark (s.score == some 0) (s.cps.all (· == 0)) then 0 else
  let d0 := dedSum r.details s.cps
  let d1 := if 0 < n && s.cps.length < n then
              (match s.score with
               | some x => max d0 (r.max - max 0 (min x r.max))
               | none => d0)
            else d0
  let d2 := if s.floor then r.max else d1
  max 0 (r.max - min d2 r.max)

def lastMatch (k : Nat) : List Row → Option Row
  | [] => none
  | x :: xs => match lastMatch k xs with
    | some y => some y
    | none => if x.id == k then some x else none

def srcFor (a : List Row) (k : Nat) : Src :=
  match lastMatch k a with
  | some w => normalize w
  | none => emptySrc

/-- v1: raw_total in half-points. -/
def orig (rules : List Rule) (a : List Row) : Int :=
  (rules.map (fun r => ruleScore r (srcFor a r.id))).foldr (· + ·) 0

/-! ### v2 pre-check -/

def nodupB : List Nat → Bool
  | [] => true
  | x :: xs => xs.all (· != x) && nodupB xs

def complete (r : Rule) (w : Row) : Bool :=
  !r.details.isEmpty && decide (r.details.length ≤ w.cps.length)
    && (w.cps.take r.details.length).all Option.isSome

def rawVeto (r : Rule) (w : Row) : Bool :=
  vetoFn r (w.rvt || w.vt) w.vr w.rCond w.rMark (w.score == .num 0)
    (w.cps.all (fun c => c.getD 0 == 0))

def contradiction (r : Rule) (w : Row) : Bool :=
  !r.details.isEmpty && decide (r.details.length ≤ w.cps.length)
    && !(w.cps.any (fun c => decide (0 < c.getD 0)))
    && !(rawVeto r w || w.rvt) && !w.floor
    && (match w.score with
        | .num s => decide (s < r.max)
        | _ => false)

def rowOK (r : Rule) (w : Row) : Bool :=
  (match w.score with
   | .num _ => true
   | .absent => complete r w
   | .junk => false)
  && !contradiction r w

def precheck (rules : List Rule) (a : List Row) : Bool :=
  nodupB (rules.map (·.id)) && a.length == rules.length && nodupB (a.map (·.id))
    && a.all (fun w => match rules.find? (·.id == w.id) with
                       | some r => rowOK r w
                       | none => false)
    && rules.all (fun r => a.any (·.id == r.id))

def fixed (rules : List Rule) (a : List Row) : Option Int :=
  if precheck rules a then some (orig rules a) else none

/-- v2 re-ask loop: `none` attempt = output without a parseable scoring JSON. -/
def fixedRun (rules : List Rule) : Nat → List (Option (List Row)) → Option Int
  | 0, _ => none
  | _, [] => none
  | k + 1, x :: xs => match x.bind (fixed rules) with
    | some t => some t
    | none => fixedRun rules k xs

/-! ### Claims about the fix -/

/-- C1: an accepted assessment gets exactly the original total (the fix only adds a gate). -/
theorem fixed_eq_orig (rules : List Rule) (a : List Row) (t : Int)
    (h : fixed rules a = some t) : orig rules a = t := by
  unfold fixed at h
  split at h <;> simp_all

theorem fixed_of_precheck (rules : List Rule) (a : List Row)
    (h : precheck rules a = true) : fixed rules a = some (orig rules a) := by
  simp [fixed, h]

/-- C2: if any rubric rule has no row, the fixed grader awards nothing (grading failure). -/
theorem fixed_rejects_unassessed (rules : List Rule) (a : List Row) (r : Rule)
    (hr : r ∈ rules) (hm : ∀ w ∈ a, w.id ≠ r.id) : fixed rules a = none := by
  have : precheck rules a = false := by
    simp only [precheck, Bool.and_eq_false_iff]
    right
    simp only [List.all_eq_false, List.any_eq_false, beq_iff_eq]
    exact ⟨r, hr, by simpa using hm⟩
  simp [fixed, this]

/-- C2': the re-ask loop yields a score only from an accepted attempt. -/
theorem fixedRun_sound (rules : List Rule) :
    ∀ (k : Nat) (xs : List (Option (List Row))) (t : Int), fixedRun rules k xs = some t →
      ∃ a, some a ∈ xs ∧ precheck rules a = true ∧ orig rules a = t := by
  intro k
  induction k with
  | zero => intro xs t h; simp [fixedRun] at h
  | succ k ih =>
    intro xs t h
    cases xs with
    | nil => simp [fixedRun] at h
    | cons x xs =>
      simp only [fixedRun] at h
      split at h
      · rename_i t' ht
        cases x with
        | none => simp at ht
        | some a =>
          simp only [Option.bind_some] at ht
          have hp : precheck rules a = true := by
            unfold fixed at ht; split at ht <;> simp_all
          refine ⟨a, by simp, hp, ?_⟩
          have := fixed_eq_orig rules a t' ht
          simp_all
      · obtain ⟨a, ha, hp, ho⟩ := ih xs t h
        exact ⟨a, List.mem_cons_of_mem _ ha, hp, ho⟩

/-! ### C3: no full marks for a rule whose row reports a deduction (with the gaps excluded) -/

theorem dedTerm_nonneg (p : Int) (b : Bool) (c : Int) : 0 ≤ dedTerm p b c := by
  unfold dedTerm; split <;> omega

theorem dedSum_nonneg : ∀ (ds : List (Int × Bool)) (cs : List Int), 0 ≤ dedSum ds cs
  | [], _ => by simp [dedSum]
  | (p, b) :: ds, cs => by
    simp only [dedSum]
    have := dedTerm_nonneg p b (cs.headD 0); have := dedSum_nonneg ds cs.tail; omega

theorem dedSum_pos : ∀ (ds : List (Int × Bool)) (cs : List Int),
    (∀ d ∈ ds, 0 < d.1) → cs.length ≤ ds.length → cs.any (fun c => decide (0 < c)) = true →
    0 < dedSum ds cs
  | [], cs, _, hl, ha => by
    cases cs with
    | nil => simp at ha
    | cons c cs => simp at hl
  | (p, b) :: ds, [], _, _, ha => by simp at ha
  | (p, b) :: ds, c :: cs, hp, hl, ha => by
    simp only [dedSum, List.headD_cons, List.tail_cons]
    have hp0 : 0 < p := hp (p, b) (by simp)
    have hrest := dedSum_nonneg ds cs
    simp only [List.any_cons, Bool.or_eq_true, decide_eq_true_eq] at ha
    rcases ha with hc | hcs
    · have : 0 < dedTerm p b c := by unfold dedTerm; split <;> omega
      omega
    · have := dedSum_pos ds cs (fun d hd => hp d (by simp [hd])) (by simp at hl; omega) hcs
      have := dedTerm_nonneg p b c; omega

/-- The row reports a deduction: a numeric rule score below max, or a positive checkpoint. -/
def ReportsDeduction (r : Rule) (w : Row) : Prop :=
  (∃ s, w.score = .num s ∧ s < r.max) ∨ w.cps.any (fun c => decide (0 < c.getD 0)) = true

/-- The three paths (found while building this model) where v2 still awards full marks to a
row that reports a deduction; C3 excludes exactly these. -/
def NoGap (r : Rule) (w : Row) : Prop :=
  ¬ (r.hasVeto = true ∧ w.vr = true ∧ w.rvt = false ∧ w.vt = false)   -- gap A
  ∧ w.cps.length ≤ r.details.length                                    -- gap B
  ∧ ¬ (w.rvt = true ∧ r.hasVeto = false)                               -- gap C

theorem any_norm (cs : List (Option Int)) :
    (cs.map (fun c => max 0 (c.getD 0))).any (fun c => decide (0 < c))
      = cs.any (fun c => decide (0 < c.getD 0)) := by
  induction cs with
  | nil => rfl
  | cons c cs ih =>
    simp only [List.map_cons, List.any_cons, ih]
    congr 1
    simp only [decide_eq_decide]; omega

theorem rowOK_no_unearned_full_marks (r : Rule) (w : Row)
    (hok : rowOK r w = true) (hne : r.details ≠ []) (hpts : ∀ d ∈ r.details, 0 < d.1)
    (hmax : 0 < r.max) (hd : ReportsDeduction r w) (hg : NoGap r w) :
    ruleScore r (normalize w) < r.max := by
  obtain ⟨gA, gB, gC⟩ := hg
  unfold ruleScore
  split
  · exact hmax
  · rename_i hv
    -- it suffices to show the effective deduction d2 is positive
    suffices hpos : 0 < (if (normalize w).floor then r.max else
        (if 0 < r.details.length && (normalize w).cps.length < r.details.length then
          (match (normalize w).score with
           | some x => max (dedSum r.details (normalize w).cps) (r.max - max 0 (min x r.max))
           | none => dedSum r.details (normalize w).cps)
         else dedSum r.details (normalize w).cps)) by
      simp only at hpos ⊢
      omega
    have hd0 := dedSum_nonneg r.details (normalize w).cps
    have hlen : (normalize w).cps.length = w.cps.length := by simp [normalize]
    by_cases hf : w.floor = true
    · simp [normalize, hf, hmax]
    · have hf' : (normalize w).floor = false := by simp [normalize]; simpa using hf
      rw [if_neg (by simp [hf'])]
      by_cases hany : w.cps.any (fun c => decide (0 < c.getD 0)) = true
      · have : 0 < dedSum r.details (normalize w).cps := by
          apply dedSum_pos _ _ hpts (by rw [hlen]; exact gB)
          simp only [normalize]; rw [any_norm]; exact hany
        split
        · split <;> omega
        · exact this
      · -- the deduction is reported only by the rule score s < max
        have hs : ∃ s, w.score = .num s ∧ s < r.max := by
          rcases hd with h | h
          · exact h
          · exact absurd h hany
        obtain ⟨s, hsw, hslt⟩ := hs
        by_cases hshort : w.cps.length < r.details.length
        · have hn : 0 < r.details.length := by
            cases hdl : r.details with
            | nil => exact absurd hdl hne
            | cons _ _ => simp
          rw [if_pos (by simp [hlen, hshort, hn])]
          simp only [normalize, hsw, SF.val]
          split <;> omega
        · -- complete-length vector, no positive checkpoint: the contradiction check fired
          -- unless a veto or floor exempted the row; each exemption also holds after
          -- normalization, so the veto branch was taken (contradiction with hv)
          exfalso
          have hcon : contradiction r w = false := by
            unfold rowOK at hok; simp only [Bool.and_eq_true, Bool.not_eq_true'] at hok
            exact hok.2
          have hdl : r.details.isEmpty = false := by
            cases hdl : r.details with
            | nil => exact absurd hdl hne
            | cons _ _ => simp
          have hge : r.details.length ≤ w.cps.length := by omega
          have hany' : w.cps.any (fun c => decide (0 < c.getD 0)) = false := by
            revert hany; cases w.cps.any (fun c => decide (0 < c.getD 0)) <;> simp
          have hfl : w.floor = false := by revert hf; cases w.floor <;> simp
          have hcon' : rawVeto r w = true ∨ w.rvt = true := by
            cases h1 : rawVeto r w <;> cases h2 : w.rvt
            · exfalso
              have : contradiction r w = true := by
                unfold contradiction
                rw [hdl, hany', h1, h2, hfl, hsw]
                simp [hslt, hge]
              rw [hcon] at this; cases this
            · exact Or.inr rfl
            · exact Or.inl rfl
            · exact Or.inl rfl
          apply absurd _ hv
          rcases hcon' with hrv | hrvt
          · simp only [rawVeto, vetoFn, Bool.and_eq_true, Bool.or_eq_true] at hrv
            obtain ⟨hV, h4⟩ := hrv
            rcases h4 with ((hfl | hvr) | hrc) | ⟨⟨hz, hcz⟩, hrm⟩
            · simp [vetoFn, normalize, hV, hfl]
            · -- veto signalled in veto_reason only is gap A unless a flag is set
              have : w.rvt = true ∨ w.vt = true := by
                revert gA; cases w.rvt <;> cases w.vt <;> simp_all
              rcases this with h | h <;> simp [vetoFn, normalize, hV, h]
            · simp [vetoFn, normalize, hV, hrc]
            · have hs0 : s = 0 := by rw [hsw] at hz; simpa using hz
              have hcz' : ∀ c ∈ w.cps, c.getD 0 = 0 := by
                intro c hc; have := List.all_eq_true.mp hcz c hc; simpa using this
              have e1 : (normalize w).score = some 0 := by
                simp only [normalize, hsw, SF.val, hs0]; split <;> simp <;> omega
              have e2 : (normalize w).cps.all (· == 0) = true := by
                simp only [normalize, List.all_map, List.all_eq_true, Function.comp_apply, beq_iff_eq]
                intro c hc; rw [hcz' c hc]; rfl
              rw [e1, e2]
              simp [vetoFn, normalize, hV, hrm]
          · have hV : r.hasVeto = true := by
              revert gC; cases r.hasVeto <;> simp [hrvt]
            simp [vetoFn, normalize, hV, hrvt]

/-! ### Lifting C3 to a whole accepted assessment -/

theorem nodupB_unique {α : Type} (f : α → Nat) :
    ∀ (l : List α) (x y : α), nodupB (l.map f) = true → x ∈ l → y ∈ l → f x = f y → x = y
  | [], _, _, _, hx, _, _ => by simp at hx
  | z :: zs, x, y, hn, hx, hy, he => by
    simp only [List.map_cons, nodupB, Bool.and_eq_true, List.all_eq_true, List.mem_map,
      bne_iff_ne, ne_eq] at hn
    obtain ⟨hz, hzs⟩ := hn
    simp only [List.mem_cons] at hx hy
    rcases hx with rfl | hx <;> rcases hy with rfl | hy
    · rfl
    · exact absurd he.symm (hz _ ⟨y, hy, rfl⟩)
    · exact absurd he (hz _ ⟨x, hx, rfl⟩)
    · exact nodupB_unique f zs x y hzs hx hy he

theorem lastMatch_some (k : Nat) : ∀ (l : List Row) (y : Row),
    lastMatch k l = some y → y ∈ l ∧ y.id = k
  | [], _, h => by simp [lastMatch] at h
  | x :: xs, y, h => by
    simp only [lastMatch] at h
    split at h
    · rename_i y' hy'
      obtain ⟨h1, h2⟩ := lastMatch_some k xs y' hy'
      cases h; exact ⟨List.mem_cons_of_mem _ h1, h2⟩
    · split at h
      · cases h; rename_i hx; exact ⟨by simp, by simpa using hx⟩
      · cases h

theorem lastMatch_none (k : Nat) : ∀ (l : List Row), lastMatch k l = none → ∀ y ∈ l, y.id ≠ k
  | [], _, y, hy => by simp at hy
  | x :: xs, h, y, hy => by
    simp only [lastMatch] at h
    split at h
    · cases h
    · rename_i hn
      simp only [List.mem_cons] at hy
      rcases hy with rfl | hy
      · split at h
        · cases h
        · rename_i hx; simpa using hx
      · exact lastMatch_none k xs hn y hy

theorem srcFor_eq (a : List Row) (w : Row) (hn : nodupB (a.map (·.id)) = true) (hw : w ∈ a) :
    srcFor a w.id = normalize w := by
  unfold srcFor
  split
  · rename_i y hy
    obtain ⟨hy1, hy2⟩ := lastMatch_some _ a y hy
    rw [nodupB_unique (·.id) a y w hn hy1 hw hy2]
  · rename_i hy
    exact absurd rfl (lastMatch_none _ a hy w hw)

/-- C3 for the fixed grader: on an accepted assessment, a rule whose row reports a deduction
(and is not one of gaps A-C) scores strictly below its maximum. -/
theorem fixed_no_unearned_full_marks (rules : List Rule) (a : List Row) (r : Rule) (w : Row)
    (hacc : precheck rules a = true) (hr : r ∈ rules) (hw : w ∈ a) (hid : w.id = r.id)
    (hne : r.details ≠ []) (hpts : ∀ d ∈ r.details, 0 < d.1) (hmax : 0 < r.max)
    (hd : ReportsDeduction r w) (hg : NoGap r w) :
    ruleScore r (srcFor a r.id) < r.max := by
  simp only [precheck, Bool.and_eq_true, beq_iff_eq, List.all_eq_true] at hacc
  obtain ⟨⟨⟨⟨hrn, _⟩, han⟩, hrows⟩, _⟩ := hacc
  have hrow := hrows w hw
  have hfind : rules.find? (·.id == w.id) = some r := by
    cases hf : rules.find? (·.id == w.id) with
    | none =>
      have := List.find?_eq_none.mp hf r hr
      simp [hid] at this
    | some r' =>
      have h1 := List.mem_of_find?_eq_some hf
      have h2 : r'.id = w.id := by simpa using List.find?_some hf
      rw [nodupB_unique (·.id) rules r' r hrn h1 hr (by rw [h2, hid])]
  rw [hfind] at hrow
  rw [← hid, srcFor_eq a w han hw]
  exact rowOK_no_unearned_full_marks r w hrow hne hpts hmax hd hg

/-! ### The real rubric (half-points) and the recorded fixed responses -/

def F : Bool := false
def T : Bool := true
def mk (id : Nat) (mx : Int) (pts : List Int) (rep : List Bool) (v : Bool) : Rule :=
  ⟨id, mx, pts.zip rep, v⟩

def rubric : List Rule := [
  mk 1 6 [2,1,4,2,2,2,3,1] [F,F,T,F,F,F,F,F] T,
  mk 2 24 [8,4,4,2,3,4] [F,F,F,T,F,F] T,
  mk 3 8 [2,2,2,2,2] [F,F,F,F,F] F,
  mk 4 8 [2,2,2,2] [F,F,F,F] F,
  mk 5 20 [8,4,2,4,4,4] [F,F,F,F,F,F] T,
  mk 6 20 [4,6,4,4,10,4] [F,F,F,F,F,F] T,
  mk 7 8 [2,2,2,2] [F,F,F,F] T,
  mk 8 20 [4,4,4,4,4] [F,F,F,F,F] F,
  mk 9 30 [8,8,8,8,8,4,4,44,4] [F,F,F,F,F,F,F,F,F] F,
  mk 10 20 [2,2,1,2,2,2,2] [F,F,F,F,F,F,F] F,
  mk 11 20 [2,2,2,2,2,2,2,2,2,2,4,4] [F,F,F,F,F,F,F,F,F,F,F,F] F,
  mk 12 16 [2,2,10,2] [F,F,F,F] T]

/-- The hypotheses of C3 hold for the real rubric; max_total = 200 half-points = 100. -/
theorem rubric_ok : rubric.all (fun r => !r.details.isEmpty && r.details.all (fun d => decide (0 < d.1))
    && decide (0 < r.max)) = true ∧ (rubric.map (·.max)).foldr (· + ·) 0 = 200
    ∧ nodupB (rubric.map (·.id)) = true := by decide

def plain (id : Nat) (sc : SF) (mx : Int) (cps : List (Option Int)) (floor : Bool := false) : Row :=
  ⟨id, sc, some mx, cps, false, false, false, false, false, floor⟩

/-- Checkpoint vector with detail `hit` triggered (make_responses.py full_cps). -/
def cpsHit (r : Rule) (hit : Option Nat) : List (Option Int) :=
  (List.range r.details.length).zip (r.details.map (·.1)) |>.map
    (fun (i, p) => some (if hit = some i then p else 0))

def respA : List Row := rubric.map (fun r => plain r.id (.num (r.max - (r.details.headD (0, F)).1)) r.max (cpsHit r (some 0)))
def respB : List Row := rubric.map (fun r => plain r.id (.num 0) r.max (cpsHit r none) true)
def respC : List Row := []
def respD : List Row := respA.filter (·.id != 9)
def respE : List Row := respB.filter (·.id != 9)
def r9 : Rule := mk 9 30 [8,8,8,8,8,4,4,44,4] [F,F,F,F,F,F,F,F,F] F
def respF : List Row := respE ++ [plain 9 (.num 0) 30 []]
def respG : List Row := respE ++ [⟨9, .absent, none, [], F, F, F, F, F, F⟩]
def respI : List Row := respE ++ [plain 9 (.num 0) 30 (cpsHit r9 none)]
def respL : List Row := respA.map (fun w => { w with score := .absent })

/-- Differential check against the recorded paired run (repairs/college_english_exam_bank-v2/
paired/result/out/v{1,2}.*.raw.txt, Structured Result `score`): v1 77,0,100,81,15,0,0,15,77;
v2 77,0,fail,fail,fail,0,fail,fail,77.  Values here are half-points. -/
theorem differential :
    [orig rubric respA, orig rubric respB, orig rubric respC, orig rubric respD, orig rubric respE,
     orig rubric respF, orig rubric respG, orig rubric respI, orig rubric respL]
      = [154, 0, 200, 162, 30, 0, 0, 30, 154]
    ∧ [fixed rubric respA, fixed rubric respB, fixed rubric respC, fixed rubric respD,
       fixed rubric respE, fixed rubric respF, fixed rubric respG, fixed rubric respI,
       fixed rubric respL]
      = [some 154, some 0, none, none, none, some 0, none, none, some 154] := by decide

/-- Re-ask rows J (D then A) and K (no JSON then A): v2 recovers 77. -/
theorem differential_reask :
    fixedRun rubric 2 [some respD, some respA] = some 154
    ∧ fixedRun rubric 2 [none, some respA] = some 154 := by decide

/-! ### Counter-checks (must come out against the original / against an over-strong claim) -/

/-- K1: the original awards 100 (200 half-points) to an empty assessment and reports it. -/
theorem orig_empty_is_100 : orig rubric [] = 200 := by decide

/-- K1': the original gives every unassessed rule its full maximum, for any rubric. -/
theorem orig_unassessed_full (r : Rule) (h0 : 0 ≤ r.max) :
    ruleScore r emptySrc = r.max := by
  have hz : dedSum r.details [] = 0 := by
    generalize r.details = ds
    induction ds with
    | nil => rfl
    | cons d ds ih =>
      obtain ⟨p, b⟩ := d
      cases b <;> simp [dedSum, dedTerm, ih] <;> omega
  simp [ruleScore, emptySrc, vetoFn, hz]
  omega

/-- K2 (gap A, refutes the over-strong form of C3 without `NoGap`): R001 row with score 0,
all-zero checkpoints, and the veto stated only in `veto_reason` (flag left at the prompt
template's default `false`). v2 accepts it and awards R001 its full 3 points (6 half-points). -/
def gapA : List Row := (respB.filter (·.id != 1)) ++
  [⟨1, .num 0, some 6, cpsHit (mk 1 6 [2,1,4,2,2,2,3,1] [F,F,T,F,F,F,F,F] T) none,
    F, F, T, F, F, F⟩]
theorem gapA_full_marks : fixed rubric gapA = some 6 := by decide

/-- K3 (gap B): R009 score 0, the nine detail checkpoints 0, a tenth checkpoint carries the
deduction; v2 awards R009 its full 15 points. -/
def gapB : List Row := respE ++ [plain 9 (.num 0) 30 (cpsHit r9 none ++ [some 8])]
theorem gapB_full_marks : fixed rubric gapB = some 30 := by decide

/-- K4 (gap C): R009 (no veto_conditions) with rule_veto_triggered = true, score 0, all-zero
checkpoints; v2 awards R009 its full 15 points. -/
def gapC : List Row := respE ++ [⟨9, .num 0, some 30, cpsHit r9 none, T, F, F, F, F, F⟩]
theorem gapC_full_marks : fixed rubric gapC = some 30 := by decide

/-- So the claim "v2 never awards a rule's maximum to a row that reports a deduction" is false
as stated; C3 holds only with `NoGap`. -/
theorem overstrong_claim_false :
    ¬ ∀ (a : List Row) (w : Row) (r : Rule), r ∈ rubric → w ∈ a → w.id = r.id →
      precheck rubric a = true → ReportsDeduction r w → ruleScore r (srcFor a r.id) < r.max := by
  intro h
  have hw : (⟨1, .num 0, some 6, cpsHit (mk 1 6 [2,1,4,2,2,2,3,1] [F,F,T,F,F,F,F,F] T) none,
    F, F, T, F, F, F⟩ : Row) ∈ gapA := by simp [gapA]
  have := h gapA _ (mk 1 6 [2,1,4,2,2,2,3,1] [F,F,T,F,F,F,F,F] T) (by simp [rubric]) hw rfl
    (by decide) (Or.inl ⟨0, rfl, by decide⟩)
  revert this; decide

/-! ### Revised fix (v2 sha256 87f0e340…, 2026-10-12): the deduction check reads what reconcile reads

Source: revised v2 `_require_recorded_deductions(obj, result, rules)`, called at the end of
`_validate_result` (revised v2 l.1193-1215 and l.1285-1294). It runs
`reconcile_result_with_rubrics` on the NORMALISED rows and rejects the assessment when a
deductive rule's raw row reports a deduction (numeric rule score below max, or a positive
checkpoint) but reconciles to full marks. `_require_complete_rule_scores` keeps every shape
check (`rowShape` below) and no longer runs the raw-row test (`contradiction` above). -/

/-- Bool form of `ReportsDeduction` (the code's `reported`). -/
def reportsB (r : Rule) (w : Row) : Bool :=
  (match w.score with
   | .num s => decide (s < r.max)
   | _ => false)
  || w.cps.any (fun c => decide (0 < c.getD 0))

theorem reportsB_iff (r : Rule) (w : Row) : reportsB r w = true ↔ ReportsDeduction r w := by
  unfold reportsB ReportsDeduction
  cases h : w.score <;> simp

/-- Shape checks of `_require_complete_rule_scores` (unchanged; the contradiction test is gone). -/
def rowShape (r : Rule) (w : Row) : Bool :=
  match w.score with
  | .num _ => true
  | .absent => complete r w
  | .junk => false

/-- The deduction check for any per-row scorer `sc`. The code uses `scoreOf` (reconcile of the
normalised row), i.e. exactly the function that produces the score. -/
def recordedWith (sc : Rule → Row → Int) (rules : List Rule) (a : List Row) : Bool :=
  rules.all (fun r => match lastMatch r.id a with
    | some w => !(reportsB r w) || decide (sc r w < r.max)
    | none => true)

def scoreOf (r : Rule) (w : Row) : Int := ruleScore r (normalize w)

def precheck2 (rules : List Rule) (a : List Row) : Bool :=
  nodupB (rules.map (·.id)) && a.length == rules.length && nodupB (a.map (·.id))
    && a.all (fun w => match rules.find? (·.id == w.id) with
                       | some r => rowShape r w
                       | none => false)
    && rules.all (fun r => a.any (·.id == r.id))
    && recordedWith scoreOf rules a

def fixed2 (rules : List Rule) (a : List Row) : Option Int :=
  if precheck2 rules a then some (orig rules a) else none

def fixedRun2 (rules : List Rule) : Nat → List (Option (List Row)) → Option Int
  | 0, _ => none
  | _, [] => none
  | k + 1, x :: xs => match x.bind (fixed2 rules) with
    | some t => some t
    | none => fixedRun2 rules k xs

/-- C1 (revised): an accepted assessment gets exactly the original total. -/
theorem fixed2_eq_orig (rules : List Rule) (a : List Row) (t : Int)
    (h : fixed2 rules a = some t) : orig rules a = t := by
  unfold fixed2 at h
  split at h <;> simp_all

/-- C2 (revised): an assessment that leaves out a rubric rule is a grading failure. -/
theorem fixed2_rejects_unassessed (rules : List Rule) (a : List Row) (r : Rule)
    (hr : r ∈ rules) (hm : ∀ w ∈ a, w.id ≠ r.id) : fixed2 rules a = none := by
  have : precheck2 rules a = false := by
    simp only [precheck2, Bool.and_eq_false_iff]
    left; right
    simp only [List.all_eq_false, List.any_eq_false, beq_iff_eq]
    exact ⟨r, hr, by simpa using hm⟩
  simp [fixed2, this]

/-- C2' (revised): the re-ask loop yields a score only from an accepted attempt. -/
theorem fixedRun2_sound (rules : List Rule) :
    ∀ (k : Nat) (xs : List (Option (List Row))) (t : Int), fixedRun2 rules k xs = some t →
      ∃ a, some a ∈ xs ∧ precheck2 rules a = true ∧ orig rules a = t := by
  intro k
  induction k with
  | zero => intro xs t h; simp [fixedRun2] at h
  | succ k ih =>
    intro xs t h
    cases xs with
    | nil => simp [fixedRun2] at h
    | cons x xs =>
      simp only [fixedRun2] at h
      split at h
      · rename_i t' ht
        cases x with
        | none => simp at ht
        | some a =>
          simp only [Option.bind_some] at ht
          have hp : precheck2 rules a = true := by
            unfold fixed2 at ht; split at ht <;> simp_all
          refine ⟨a, by simp, hp, ?_⟩
          have := fixed2_eq_orig rules a t' ht
          simp_all
      · obtain ⟨a, ha, hp, ho⟩ := ih xs t h
        exact ⟨a, List.mem_cons_of_mem _ ha, hp, ho⟩

/-- The check is sound for ANY scorer: if it accepts, no rule whose row reports a deduction gets
`sc`'s maximum. No property of `normalize` or `ruleScore` is used, so the result does not depend on
the abstractions of this model (e.g. the 200-character truncation of `reason`, gap D): the code
decides with the same normalise + reconcile functions that produce the score. -/
theorem recordedWith_sound (sc : Rule → Row → Int) (rules : List Rule) (a : List Row)
    (r : Rule) (w : Row) (h : recordedWith sc rules a = true) (hr : r ∈ rules)
    (hl : lastMatch r.id a = some w) (hd : reportsB r w = true) : sc r w < r.max := by
  unfold recordedWith at h
  have h1 := List.all_eq_true.mp h r hr
  rw [hl] at h1
  simpa [hd] using h1

theorem lastMatch_of_mem (a : List Row) (w : Row) (k : Nat) (han : nodupB (a.map (·.id)) = true)
    (hw : w ∈ a) (hid : w.id = k) : lastMatch k a = some w := by
  cases h : lastMatch k a with
  | none => exact absurd hid (lastMatch_none _ a h w hw)
  | some y =>
    obtain ⟨hy1, hy2⟩ := lastMatch_some _ a y h
    rw [nodupB_unique (·.id) a y w han hy1 hw (hy2.trans hid.symm)]

/-- C3 (revised), with NO gap exclusion: on an accepted assessment, a rule whose row reports a
deduction scores strictly below its maximum. -/
theorem fixed2_no_unearned_full_marks (rules : List Rule) (a : List Row) (r : Rule) (w : Row)
    (hacc : precheck2 rules a = true) (hr : r ∈ rules) (hw : w ∈ a) (hid : w.id = r.id)
    (hd : ReportsDeduction r w) :
    ruleScore r (srcFor a r.id) < r.max := by
  simp only [precheck2, Bool.and_eq_true] at hacc
  obtain ⟨⟨⟨⟨⟨_, _⟩, han⟩, _⟩, _⟩, hrec⟩ := hacc
  have hl := lastMatch_of_mem a w r.id han hw hid
  have := recordedWith_sound scoreOf rules a r w hrec hr hl ((reportsB_iff r w).mpr hd)
  rw [← hid, srcFor_eq a w han hw]
  exact this

/-- Outside the gaps the revision changes nothing: every assessment the earlier fixed grader
accepted, with no gap row, is accepted by the revised one (with the same, original, total). -/
theorem precheck2_of_precheck (rules : List Rule) (a : List Row)
    (hrules : ∀ r ∈ rules, r.details ≠ [] ∧ (∀ d ∈ r.details, 0 < d.1) ∧ 0 < r.max)
    (hacc : precheck rules a = true)
    (hng : ∀ w ∈ a, ∀ r ∈ rules, w.id = r.id → NoGap r w) :
    precheck2 rules a = true := by
  have hacc' := hacc
  simp only [precheck, Bool.and_eq_true, List.all_eq_true] at hacc'
  obtain ⟨⟨⟨⟨hrn, hlen⟩, han⟩, hrows⟩, hcov⟩ := hacc'
  simp only [precheck2, Bool.and_eq_true, List.all_eq_true]
  refine ⟨⟨⟨⟨⟨hrn, hlen⟩, han⟩, ?_⟩, hcov⟩, ?_⟩
  · intro w hw
    have h1 := hrows w hw
    revert h1
    cases rules.find? (·.id == w.id) with
    | none => simp
    | some r =>
      intro h1
      simp only [rowOK, Bool.and_eq_true] at h1
      exact h1.1
  · unfold recordedWith
    rw [List.all_eq_true]
    intro r hr
    cases hl : lastMatch r.id a with
    | none => rfl
    | some w =>
      obtain ⟨hw, hid⟩ := lastMatch_some _ a w hl
      by_cases hrep : reportsB r w = true
      · obtain ⟨hne, hpts, hmax⟩ := hrules r hr
        have := fixed_no_unearned_full_marks rules a r w hacc hr hw hid hne hpts hmax
          ((reportsB_iff r w).mp hrep) (hng w hw r hr hid)
        rw [← hid, srcFor_eq a w han hw] at this
        simp [hrep, scoreOf, this]
      · simp [hrep]

/-- Revised fixed grader on the recorded responses: the same results as the earlier fixed grader
(A, B, F, L accepted with the original totals 77, 0, 0, 77; C, D, E, G, I rejected; J, K recover 77). -/
theorem differential2 :
    [fixed2 rubric respA, fixed2 rubric respB, fixed2 rubric respC, fixed2 rubric respD,
     fixed2 rubric respE, fixed2 rubric respF, fixed2 rubric respG, fixed2 rubric respI,
     fixed2 rubric respL]
      = [some 154, some 0, none, none, none, some 0, none, none, some 154]
    ∧ fixedRun2 rubric 2 [some respD, some respA] = some 154
    ∧ fixedRun2 rubric 2 [none, some respA] = some 154 := by decide

/-- Gaps A-C, where the earlier fixed grader awards full marks (`gapA_full_marks` …), are rejected. -/
theorem gaps_rejected2 :
    fixed2 rubric gapA = none ∧ fixed2 rubric gapB = none ∧ fixed2 rubric gapC = none := by decide

/-- Row M (R001 score 0, a negative checkpoint, a veto marker in `reason`): the original reconciles
it as a veto (0); the earlier fixed grader rejected it; the revised one accepts it with the
original total. -/
def respM : List Row := (respB.filter (·.id != 1)) ++
  [⟨1, .num 0, some 6, some (-1) :: (cpsHit (mk 1 6 [2,1,4,2,2,2,3,1] [F,F,T,F,F,F,F,F] T) none).tail,
    F, F, F, F, T, F⟩]
theorem respM_results :
    orig rubric respM = 0 ∧ fixed rubric respM = none ∧ fixed2 rubric respM = some 0 := by decide

end EbvCollege

#print axioms EbvCollege.fixed_eq_orig
#print axioms EbvCollege.fixed_rejects_unassessed
#print axioms EbvCollege.fixedRun_sound
#print axioms EbvCollege.rowOK_no_unearned_full_marks
#print axioms EbvCollege.fixed_no_unearned_full_marks
#print axioms EbvCollege.rubric_ok
#print axioms EbvCollege.differential
#print axioms EbvCollege.differential_reask
#print axioms EbvCollege.orig_empty_is_100
#print axioms EbvCollege.orig_unassessed_full
#print axioms EbvCollege.gapA_full_marks
#print axioms EbvCollege.gapB_full_marks
#print axioms EbvCollege.gapC_full_marks
#print axioms EbvCollege.overstrong_claim_false
#print axioms EbvCollege.reportsB_iff
#print axioms EbvCollege.fixed2_eq_orig
#print axioms EbvCollege.fixed2_rejects_unassessed
#print axioms EbvCollege.fixedRun2_sound
#print axioms EbvCollege.recordedWith_sound
#print axioms EbvCollege.fixed2_no_unearned_full_marks
#print axioms EbvCollege.precheck2_of_precheck
#print axioms EbvCollege.differential2
#print axioms EbvCollege.gaps_rejected2
#print axioms EbvCollege.respM_results
