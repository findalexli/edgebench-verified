/-
EdgeBench Verified -- time-budget arithmetic for openrct2_theme_park_ai and
warehouse_forklift_routing (exact rationals). Only the arithmetic is checked; every input is a
number documented in the case pages / reviews, cited below.

openrct2_theme_park_ai
  * eval_cmd `OPENRCT2_TIMEOUT=120 python3 /tmp/eval_openrct2.py` (tasks/openrct2_theme_park_ai.json,
    sha256 09e2a4d8...1449); wrapper /tmp/eval_openrct2.py (sha256 7fdde3e0...133c):
    `--timeout 120` per scenario, `TOTAL_TIMEOUT = 1800`; manifest eval_timeout 2400; 3 scenarios
    run one after another (review: TOTAL_TIMEOUT would need ≥ 5,200 s for the 4-year horizon).
  * Monitor in /tmp/openrct2_original_eval.py (sha256 bfcf7ab9...155b): `targetDays = 992`.
  * Timing constants (repairs/openrct2_theme_park_ai-v2/paired/check_horizon.py, from
    openrct2.d.ts): month = 65536/4 = 16384 ticks; 8 months of 31,30,31,30,31,31,30,31 days
    (245 days/year); 40 Hz base update; speed k runs 2^(k-1) updates per frame.
  * Observed rates at speed 4 (case page table): 0.593, 0.595, 0.595 days/s (120 s runs),
    0.597 (60 s), 0.582 (60 s at 0.25 CPU).
warehouse_forklift_routing
  * /tmp/eval_warehouse_manager.py original `TIME_LIMIT = 60`, fixed `TIME_LIMIT = 150`
    (fixed copy sha256 eff6a69b5bea0ccbddb62633a08b18ad931b8b01188731595c8935fa7c537b95):
    solver subprocess timeout TIME_LIMIT [9, 16-18], tester timeout 30 [24-25],
    `ProcessPoolExecutor(max_workers=min(8, len(case_files)))` [42]; eval_timeout 3600
    (tasks/warehouse_forklift_routing.json:20); 50 inputs, T = 5 test cases per input,
    "30 seconds per test case" (prompt, case page).
-/
import Mathlib.Algebra.Order.Field.Rat
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Linarith

namespace Ebv.TimeBudgets

/-! ## OpenRCT2 -/

def ticksPerMonth : ℚ := 65536 / 4
def daysPerYear : ℚ := 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31
def ticksPerDay : ℚ := ticksPerMonth * 8 / daysPerYear
def updatesPerSec (speed : ℕ) : ℚ := 40 * 2 ^ (speed - 1)
def modelRate (speed : ℕ) : ℚ := updatesPerSec speed / ticksPerDay
def targetDays : ℚ := 992

theorem year_len : daysPerYear = 245 ∧ ticksPerDay = 131072 / 245 := by
  norm_num [daysPerYear, ticksPerDay, ticksPerMonth]

theorem model_rates :
    modelRate 1 = 1225 / 16384 ∧ modelRate 3 = 1225 / 4096 ∧ modelRate 4 = 1225 / 2048 := by
  refine ⟨?_, ?_, ?_⟩ <;> norm_num [modelRate, updatesPerSec, ticksPerDay, ticksPerMonth, daysPerYear]

/-- "model: 992 target days at speed 4 need 1658 s": exactly 2031616/1225 ≈ 1658.46 s. -/
theorem model_need : targetDays / modelRate 4 = 2031616 / 1225 ∧
    (1658 : ℚ) ≤ 2031616 / 1225 ∧ (2031616 : ℚ) / 1225 < 1659 := by
  rw [(model_rates).2.2]; norm_num [targetDays]

/-- 120 s at the model rates: 9.0, 35.9, 71.8 days (one decimal). -/
theorem model_120s :
    (895 : ℚ)/100 ≤ 120 * (1225/16384) ∧ 120 * (1225/16384 : ℚ) < 905/100 ∧
    (3585 : ℚ)/100 ≤ 120 * (1225/4096) ∧ 120 * (1225/4096 : ℚ) < 3595/100 ∧
    (7175 : ℚ)/100 ≤ 120 * (1225/2048) ∧ 120 * (1225/2048 : ℚ) < 7185/100 := by norm_num

/-- At the observed mean rate 0.595 days/s, 992 days need ≈ 1,667 s (27.8 min); over the
observed 120 s range 0.593–0.597 they need between 1,661 and 1,673 s. -/
theorem observed_need :
    (1667 : ℚ) ≤ 992 / 0.595 ∧ (992 : ℚ) / 0.595 < 1668 ∧
    (2775 : ℚ)/100 ≤ 992 / 0.595 / 60 ∧ (992 : ℚ) / 0.595 / 60 < 2785/100 ∧
    (1661 : ℚ) ≤ 992 / 0.597 ∧ (992 : ℚ) / 0.593 < 1673 := by norm_num

/-- Three scenarios in sequence need about 83 min (≥ 4,975 s even at the model rate), beyond
both the 1,800 s wrapper cap and the 2,400 s manifest timeout. -/
theorem three_scenarios :
    1800 < 3 * (targetDays / modelRate 4) ∧ 2400 < 3 * (targetDays / modelRate 4) ∧
    (83 : ℚ) ≤ 3 * (992 / 0.595) / 60 ∧ 3 * (992 / 0.595 : ℚ) / 60 < 84 := by
  rw [(model_need).1]; norm_num

/-- 120 s per scenario reaches at most 72 days even at the fastest observed rate, < 992. -/
theorem budget_short : 120 * (0.597 : ℚ) < 72 ∧ (72 : ℚ) < targetDays := by norm_num [targetDays]

/-- 68–69 days are about 7% of 992; 992 days ≈ 4.05 years. -/
theorem fractions :
    (65 : ℚ)/1000 ≤ 68/992 ∧ (69 : ℚ)/992 < 75/1000 ∧
    (4045 : ℚ)/1000 ≤ 992/245 ∧ (992 : ℚ)/245 < 4055/1000 := by norm_num

/-- 4 years in 120 s need 992·131072/245/120 ≈ 4,423 ticks/s: ≈ 110.6× the 40 Hz base and
≈ 13.8× the speed-4 rate of 320 updates/s. Observed 0.595 days/s ≈ 318 ticks/s. -/
theorem ticks_needed :
    (4422 : ℚ) ≤ 992 * (131072/245) / 120 ∧ 992 * (131072/245 : ℚ) / 120 < 4423 ∧
    (110 : ℚ) ≤ 992 * (131072/245) / 120 / 40 ∧ 992 * (131072/245 : ℚ) / 120 / 40 < 111 ∧
    (13 : ℚ) ≤ 992 * (131072/245) / 120 / 320 ∧ 992 * (131072/245 : ℚ) / 120 / 320 < 14 ∧
    (318 : ℚ) ≤ 0.595 * (131072/245) ∧ 0.595 * (131072/245 : ℚ) < 319 := by norm_num

/-- Counter-check (wording): a SINGLE scenario's ≈1,667 s does not exceed the 1,800 s wrapper
cap or the 2,400 s manifest timeout, even at the slowest observed 120 s rate (0.593). Only the
three-scenario total does. -/
theorem counter_single_scenario_fits :
    (992 : ℚ) / 0.593 < 1800 ∧ (992 : ℚ) / 0.593 < 2400 := by norm_num

/-- Counter-check: a too-strong claim fails — 992 days do not fit in 1,660 s at 0.595 days/s. -/
theorem counter_1660 : ¬ ((992 : ℚ) / 0.595 ≤ 1660) := by norm_num

/-- Side note: at the 0.25-CPU rate 0.582 days/s, 992 days need ≈ 1,704.5 s, slightly above
the review's suggested per-scenario minimum of 1,700 s. -/
theorem slow_rate_need : (1700 : ℚ) < 992 / 0.582 ∧ (992 : ℚ) / 0.582 < 1705 := by norm_num

/-! ## Warehouse forklift routing -/

def T : ℚ := 5
def perCase : ℚ := 30
def origLimit : ℚ := 60
def fixedLimit : ℚ := 150
def testerLimit : ℚ := 30
def inputs : ℕ := 50
def workers : ℕ := 8
def evalTimeout : ℚ := 3600

/-- The promise is 5 × 30 s = 150 s per input; the fixed limit equals it; the original 60 s
is 2.5× too short. -/
theorem promise : T * perCase = 150 ∧ fixedLimit = T * perCase ∧ origLimit < T * perCase ∧
    T * perCase / origLimit = 5 / 2 := by
  norm_num [T, perCase, fixedLimit, origLimit]

/-- The test submission's 13 s per test case (65 s per input) is within the promise but over
the original limit. -/
theorem sleep_witness : origLimit < T * 13 ∧ T * 13 ≤ fixedLimit ∧ (13 : ℚ) ≤ perCase := by
  norm_num [T, origLimit, fixedLimit, perCase]

/-- Waves: ⌈50 / 8⌉ = 7. Worst case under the fixed limit 7 × (150 + 30) = 1,260 s < 3,600 s
(original: 7 × (60 + 30) = 630 s). -/
theorem waves : (inputs + workers - 1) / workers = 7 := by decide

theorem worst_case :
    7 * (fixedLimit + testerLimit) = 1260 ∧ 7 * (fixedLimit + testerLimit) < evalTimeout ∧
    7 * (origLimit + testerLimit) = 630 := by
  norm_num [fixedLimit, testerLimit, evalTimeout, origLimit]

/-- Counter-check: 6 waves would not cover 50 inputs on 8 workers (6 × 8 = 48 < 50), so the
seventh wave is needed; and a limit of 60 s cannot hold a 5 × 30 s budget. -/
theorem counter_six_waves : 6 * workers < inputs := by decide
theorem counter_orig_limit : ¬ (T * perCase ≤ origLimit) := by norm_num [T, perCase, origLimit]

end Ebv.TimeBudgets

#print axioms Ebv.TimeBudgets.year_len
#print axioms Ebv.TimeBudgets.model_rates
#print axioms Ebv.TimeBudgets.model_need
#print axioms Ebv.TimeBudgets.model_120s
#print axioms Ebv.TimeBudgets.observed_need
#print axioms Ebv.TimeBudgets.three_scenarios
#print axioms Ebv.TimeBudgets.budget_short
#print axioms Ebv.TimeBudgets.fractions
#print axioms Ebv.TimeBudgets.ticks_needed
#print axioms Ebv.TimeBudgets.counter_single_scenario_fits
#print axioms Ebv.TimeBudgets.counter_1660
#print axioms Ebv.TimeBudgets.slow_rate_need
#print axioms Ebv.TimeBudgets.promise
#print axioms Ebv.TimeBudgets.sleep_witness
#print axioms Ebv.TimeBudgets.waves
#print axioms Ebv.TimeBudgets.worst_case
#print axioms Ebv.TimeBudgets.counter_six_waves
#print axioms Ebv.TimeBudgets.counter_orig_limit
