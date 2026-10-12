/-!
# schemathesis_datagen_pipeline: the HTTP-date check

Source modelled (judge image
`seededge/edgebench.judge.schemathesis_datagen_pipeline@sha256:16b21364d67906d802e24d0b3b4505c42a6ac0f91cd5b382bb4c9d1d20224d37`):

* Original `/tests/test_01_header_strategies.py`, sha256
  `f2bf937f58549d6a82468883cf5a199357cef2caaf5dc9da865f962648bdeec6`:
  l.33 `HTTP_DATE_RE = re.compile(r"^\w{3}, \d{2} \w{3} \d{4} \d{2}:\d{2}:\d{2} GMT$")`,
  l.64-68 `assert HTTP_DATE_RE.match(value)` (50 examples)            -> `origShape`.
* Fixed `files/tests/test_01_header_strategies.py`, sha256
  `07848bce6266964ba7d09b57b55af4f719b7ff6935dbe73287f2d39017f9f830`:
  l.34-38 `HTTP_DATE_RE` (named weekdays and months, `[0-9]` digits), l.50 `fullmatch`,
  l.53-56 groups / `months.index`                                      -> `fixedParse`;
  l.57 `year < 1 or not 1 <= day <= calendar.monthrange(year, month)[1]`,
  l.60 `weekdays[calendar.weekday(year, month, day)] == weekday`,
  l.61-64 clock bounds, second 60 only at 23:59                       -> `fixedAccepts`.
* Python 3.11.15 stdlib (in the image): `calendar.monthrange` = `mdays[month] + (month ==
  February and isleap(year))`; `calendar.weekday` = `datetime.date(y,m,d).weekday()` for
  1 <= y <= 9999, i.e. `(_ymd2ord(y,m,d) + 6) % 7` with
  `_ymd2ord = 365*(y-1) + (y-1)//4 - (y-1)//100 + (y-1)//400 + _days_before_month + d`
                                                                       -> `isLeap`, `dim`, `pyWeekday`.

Specification (`Spec`), written independently: RFC 9110 §5.6.7 IMF-fixdate, with RFC 5322 §3.3
semantic validity: a real Gregorian day of the month, the matching weekday computed by
Zeller's congruence (not by day counting), hour 00-23, minute 00-59, second 00-59 or a leap
second 23:59:60. Year >= 1 is the fix's stated choice (TODO.md gives no lower bound).
-/

namespace Ebv.HttpDate

/-! ## Python's calendar, as the fixed check uses it (Python ints -> `Int`) -/

def isLeap (y : Nat) : Bool := y % 4 == 0 && (y % 100 != 0 || y % 400 == 0)

def mdays : Nat → Nat
  | 1 => 31 | 2 => 28 | 3 => 31 | 4 => 30 | 5 => 31 | 6 => 30
  | 7 => 31 | 8 => 31 | 9 => 30 | 10 => 31 | 11 => 30 | 12 => 31 | _ => 0

/-- `calendar.monthrange(y, m)[1]`. -/
def dim (y m : Nat) : Nat := mdays m + (if m == 2 && isLeap y then 1 else 0)

/-- `_DAYS_BEFORE_MONTH[m]` (cumulative `mdays`). -/
def dbmTable : Nat → Int
  | 1 => 0 | 2 => 31 | 3 => 59 | 4 => 90 | 5 => 120 | 6 => 151
  | 7 => 181 | 8 => 212 | 9 => 243 | 10 => 273 | 11 => 304 | _ => 334

/-- `_days_before_month(y, m)`. -/
def daysBeforeMonth (y m : Nat) : Int := dbmTable m + (if m > 2 && isLeap y then 1 else 0)

/-- `_ymd2ord(y, m, d)`; `//` on nonnegative ints is `Int` division. -/
def ymd2ord (y m d : Nat) : Int :=
  let n : Int := (y : Int) - 1
  365 * n + n / 4 - n / 100 + n / 400 + daysBeforeMonth y m + d

/-- `calendar.weekday` = `date.weekday()` = `(toordinal() + 6) % 7` (0 = Monday). -/
def pyWeekday (y m d : Nat) : Int := (ymd2ord y m d + 6) % 7

/-! ## Independent specification -/

/-- Gregorian leap rule (Prop form). -/
def GregLeap (y : Nat) : Prop := (y % 4 = 0 ∧ y % 100 ≠ 0) ∨ y % 400 = 0

instance (y : Nat) : Decidable (GregLeap y) := by unfold GregLeap; infer_instance

/-- "Thirty days hath September, April, June and November ...". -/
def monthLen (y m : Nat) : Nat :=
  if m = 2 then (if GregLeap y then 29 else 28)
  else if m = 4 ∨ m = 6 ∨ m = 9 ∨ m = 11 then 30 else 31

/-- Zeller's congruence for the Gregorian calendar (January and February counted as months
13 and 14 of the previous year), re-based so that 0 = Monday. -/
def zeller (y m d : Nat) : Int :=
  let Y : Int := if m ≤ 2 then (y : Int) - 1 else y
  let M : Int := if m ≤ 2 then m + 12 else m
  let K := Y % 100
  let J := Y / 100
  ((d + 13 * (M + 1) / 5 + K + K / 4 + J / 4 + 5 * J) + 5) % 7

/-- Parsed fields of a string that matched the fixed regex (`wd` = index in
`("Mon",...,"Sun")`, `mon` = `months.index + 1`). -/
structure Fields where
  wd : Nat
  day : Nat
  mon : Nat
  year : Nat
  h : Nat
  mi : Nat
  s : Nat
deriving DecidableEq, Repr

def Spec (f : Fields) : Prop :=
  1 ≤ f.year ∧ 1 ≤ f.day ∧ f.day ≤ monthLen f.year f.mon ∧ zeller f.year f.mon f.day = f.wd ∧
  f.h ≤ 23 ∧ f.mi ≤ 59 ∧ (f.s ≤ 59 ∨ (f.s = 60 ∧ f.h = 23 ∧ f.mi = 59))

instance (f : Fields) : Decidable (Spec f) := by unfold Spec; infer_instance

/-- `is_imf_fixdate` l.56-65 after a successful regex match:
`if year < 1 or not 1 <= day <= monthrange(...)[1]: return False` then the conjunction. -/
def fixedAccepts (f : Fields) : Bool :=
  decide (¬ (f.year < 1 ∨ ¬ (1 ≤ f.day ∧ f.day ≤ dim f.year f.mon)) ∧
    pyWeekday f.year f.mon f.day = f.wd ∧ f.h ≤ 23 ∧ f.mi ≤ 59 ∧ f.s ≤ 60 ∧
    (f.s ≠ 60 ∨ (f.h = 23 ∧ f.mi = 59)))

/-! ## Calendar lemmas -/

theorem isLeap_iff (y : Nat) : isLeap y = true ↔ GregLeap y := by
  unfold isLeap GregLeap
  by_cases h4 : y % 4 = 0 <;> by_cases h1 : y % 100 = 0 <;> by_cases h400 : y % 400 = 0 <;>
    simp [h4, h1, h400] <;> omega

theorem dim_eq_monthLen (y m : Nat) (hm1 : 1 ≤ m) (hm : m ≤ 12) : dim y m = monthLen y m := by
  have hl := isLeap_iff y
  unfold dim monthLen
  cases h : isLeap y <;> simp only [h] at hl <;>
  (rcases (by omega : m = 1 ∨ m = 2 ∨ m = 3 ∨ m = 4 ∨ m = 5 ∨ m = 6 ∨ m = 7 ∨ m = 8 ∨
      m = 9 ∨ m = 10 ∨ m = 11 ∨ m = 12) with rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl |
      rfl | rfl | rfl | rfl <;> simp_all [mdays])

theorem mod7_congr (A B : Int) (h : 7 ∣ A - B) : A % 7 = B % 7 := by omega

/-- Decomposition Y = 100 J + K: Y/4 = 25 J + K/4 and Y/400 = J/4. -/
theorem dec (Y : Int) (_h : 0 ≤ Y) : Y / 4 = 25 * (Y / 100) + Y % 100 / 4 ∧ Y / 400 = Y / 100 / 4 := by
  constructor <;> omega

/-- Python's day-count weekday agrees with Zeller's congruence for every year >= 1, every
month and every day number. -/
theorem pyWeekday_eq_zeller (y m d : Nat) (hy : 1 ≤ y) (hm1 : 1 ≤ m) (hm : m ≤ 12) :
    pyWeekday y m d = zeller y m d := by
  have hl := isLeap_iff y
  unfold GregLeap at hl
  have dn := dec ((y : Int) - 1) (by omega)
  have dy := dec (y : Int) (by omega)
  have a4 : ((y : Int) - 1) / 4 = (y : Int) / 4 - (if y % 4 = 0 then 1 else 0) := by split <;> omega
  have a100 : ((y : Int) - 1) / 100 = (y : Int) / 100 - (if y % 100 = 0 then 1 else 0) := by
    split <;> omega
  have a400 : ((y : Int) - 1) / 400 = (y : Int) / 400 - (if y % 400 = 0 then 1 else 0) := by
    split <;> omega
  unfold pyWeekday ymd2ord daysBeforeMonth zeller
  rcases (by omega : m = 1 ∨ m = 2 ∨ m = 3 ∨ m = 4 ∨ m = 5 ∨ m = 6 ∨ m = 7 ∨ m = 8 ∨
      m = 9 ∨ m = 10 ∨ m = 11 ∨ m = 12) with rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl |
      rfl | rfl | rfl | rfl <;>
  (cases h : isLeap y <;> simp only [h, Bool.false_eq_true, false_iff, true_iff] at hl <;>
    simp [dbmTable] <;> apply mod7_congr <;>
    (by_cases h4 : y % 4 = 0 <;> by_cases h1 : y % 100 = 0 <;> by_cases h400 : y % 400 = 0 <;>
      simp only [h4, h1, h400, ite_true, ite_false] at a4 a100 a400 <;> omega))

/-- Main theorem: on every parse of the fixed regex, the fixed check accepts exactly the
specification-valid IMF-fixdates (unbounded year, day and clock fields). -/
theorem fixedAccepts_iff_spec (f : Fields) (hm1 : 1 ≤ f.mon) (hm : f.mon ≤ 12) :
    fixedAccepts f = true ↔ Spec f := by
  unfold fixedAccepts Spec
  rw [decide_eq_true_iff, dim_eq_monthLen f.year f.mon hm1 hm]
  by_cases hy : 1 ≤ f.year
  · rw [pyWeekday_eq_zeller f.year f.mon f.day hy hm1 hm]
    omega
  · constructor
    · intro h; omega
    · intro h; omega

/-! ## The strings: both regexes, character-level -/

def wdNames : List String := ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
def monNames : List String :=
  ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

/-- Original l.33, ASCII approximation of `\w` and `\d` (Python's are Unicode-wider, so the
real original accepts at least what this accepts). `$` before a final newline is ignored. -/
def origShape (s : String) : Bool :=
  let p := "w, dd w dddd dd:dd:dd GMT".toList   -- `w` stands for \w{3}
  let p := p.flatMap (fun c => if c = 'w' then ['w', 'w', 'w'] else [c])
  let cs := s.toList
  cs.length == p.length &&
    (p.zip cs).all (fun (pc, c) =>
      if pc = 'w' then c.isAlphanum || c = '_' else if pc = 'd' then c.isDigit else c = pc)

def digitsVal (cs : List Char) : Option Nat :=
  if cs.all Char.isDigit then some (cs.foldl (fun n c => 10 * n + (c.toNat - '0'.toNat)) 0) else none

def idx (names : List String) (cs : List Char) : Option Nat :=
  names.findIdx? (fun n => n.toList == cs)

/-- Fixed l.34-38 + l.50 `fullmatch` + l.53-56 group conversion. -/
def fixedParse (s : String) : Option Fields := do
  let cs := s.toList
  guard (cs.length = 29)
  let sl (i n : Nat) := (cs.drop i).take n
  guard (sl 3 2 = [',', ' '] ∧ sl 7 1 = [' '] ∧ sl 11 1 = [' '] ∧ sl 16 1 = [' '] ∧
    sl 19 1 = [':'] ∧ sl 22 1 = [':'] ∧ sl 25 4 = [' ', 'G', 'M', 'T'])
  let wd ← idx wdNames (sl 0 3)
  let day ← digitsVal (sl 5 2)
  let mon ← idx monNames (sl 8 3)
  let year ← digitsVal (sl 12 4)
  let h ← digitsVal (sl 17 2)
  let mi ← digitsVal (sl 20 2)
  let sec ← digitsVal (sl 23 2)
  pure ⟨wd, day, mon + 1, year, h, mi, sec⟩

def isImfFixdate (s : String) : Bool :=
  match fixedParse s with
  | none => false
  | some f => fixedAccepts f

/-- Differential check against `evidence/scripts/schemathesis_datagen_pipeline/observed_witnesses.txt`
(original_regex / v2_predicate columns, produced by running the real test code). -/
def witnesses : List (String × Bool × Bool) :=
  [("Sun, 06 Nov 1994 08:49:37 GMT", true, true),
   ("Mon, 31 Apr 2023 12:00:00 GMT", true, false),
   ("Mon, 01 Jan 2024 24:00:00 GMT", true, false),
   ("Fri, 01 Jan 2024 12:00:00 GMT", true, false),
   ("Thu, 29 Feb 2024 00:00:00 GMT", true, true),
   ("Thu, 29 Feb 2023 00:00:00 GMT", true, false),
   ("Abc, 99 Xyz 0000 99:99:99 GMT", true, false),
   ("Sat, 31 Dec 2016 23:59:60 GMT", true, true)]

theorem witnesses_agree :
    witnesses.all (fun (s, o, v) => origShape s == o && isImfFixdate s == v) = true := by
  decide

/-- Counter-check: the original accepts the nonsense string, which has no parse at all under
the fixed regex (so is not an IMF-fixdate). -/
theorem orig_accepts_garbage :
    origShape "Abc, 99 Xyz 0000 99:99:99 GMT" = true ∧
    fixedParse "Abc, 99 Xyz 0000 99:99:99 GMT" = none := by decide

/-- Counter-check at the field level: a well-shaped but impossible date (31 April) violates
the specification, though the original's shape test accepts it. -/
theorem apr31_not_spec : ¬ Spec ⟨0, 31, 4, 2023, 12, 0, 0⟩ := by decide

end Ebv.HttpDate

#print axioms Ebv.HttpDate.isLeap_iff
#print axioms Ebv.HttpDate.dim_eq_monthLen
#print axioms Ebv.HttpDate.pyWeekday_eq_zeller
#print axioms Ebv.HttpDate.fixedAccepts_iff_spec
#print axioms Ebv.HttpDate.witnesses_agree
#print axioms Ebv.HttpDate.orig_accepts_garbage
#print axioms Ebv.HttpDate.apr31_not_spec

