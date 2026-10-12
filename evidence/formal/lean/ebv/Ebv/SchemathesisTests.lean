import Mathlib.Tactic.NormNum
import Mathlib.Data.Rat.Defs

/-!
# schemathesis_config_modernization, schemathesis_reporting_observability (and datagen score)

Two pieces: (1) the phase-weighted reward of both `test.sh` files, to check the published score
changes exactly; (2) the never-failing body test of reporting_observability.

Sources:
* config, fixed `/tests/test.sh` sha256 `0fd4de0a5f88a62fe3fdec73b8566c8bebe8a70ac68fe67c6f410cfd0f331871`
  (original in `seededge/edgebench.judge.schemathesis_config_modernization@sha256:ff71a766c254fc62f6ffd12d877297cb22223a0bb2190e91f95fe6b3231d519e`):
  `weights = [3, 1, 1, 2, 2, 1]`, `score = sum(w * p / t) / sum(weights)`, printed `:.6f`;
  l.19 / l.98 `PHASE3_TOTAL` / `PHASE3_EXPECTED` 15 -> 16 (the only diff).
  Fixed `/tests/test_03_metric_system.py` sha256 `27d754251b9d1748745ced071c8f1c1d3c38325747539277ac9b2d765dd2530c`
  adds l.190-198 `assert metric(f) is f`.
* reporting, original `/tests/test.sh` sha256 `c74c6c42a1c63799f6bf16496c1288aa135f00c51426123500f97aab210dc428`,
  fixed sha256 `5f3a136b109129147897ad7a0bfa3a90c4bc2fc1d6a607db5735f836d5859b5e`:
  l.164 `weights = [2, 2, 3, 2, 1]`; `PHASE5_TOTAL` 10 -> 12, Phase 2 stays 14.
  Original `/tests/test_05_email_coverage.py` sha256 `8f1831e4597df47ed6e68fecceead5bdbbfb309e0c32018988519c1636632839`
  (image `seededge/edgebench.judge.schemathesis_reporting_observability@sha256:b1e16633e75b2a21ef805961bb190c0a71afb75225986997340185eb7d67fc54`):
  l.98 `from schemathesis.specs.openapi.negative import GeneratedValue`,
  l.117 `scenarios = {v.scenario for v in cover_schema_iter(...) if isinstance(v, GeneratedValue)}`,
  l.118 `assert OBJECT_UNEXPECTED_PROPERTIES not in scenarios`        -> `origBodyTest`.
  Fixed `test_05_email_coverage.py` sha256 `10401e449a2ad57a6bca52e46da1dafff7b15372d0ce4182dc4c1a693a0e0dc3`:
  l.95 imports `GeneratedValue` from `schemathesis.generation.coverage`; l.117-121 non-empty,
  all of that class, `(UNEXPECTED in scenarios) == allow_extra_parameters` -> `fixedBodyTest`.
-/

namespace Ebv.Schemathesis

/-- One phase's term of the reward (`w * (p / t if t else 0)`). -/
def term (w p t : ℚ) : ℚ := if t = 0 then 0 else w * (p / t)

/-! ## Config: Phase 3 has weight 1 of 10 and goes from 15 to 16 tests -/

/-- Reward change caused by Phase 3 alone (the other five terms are identical in both versions). -/
def cfgDelta (pOrig pFixed : ℚ) : ℚ := (term 1 pOrig 15 - term 1 pFixed 16) / 10

/-- identity: 15/15 -> 16/16, no change (published 0.135313 -> 0.135313). -/
theorem cfg_identity : cfgDelta 15 16 = 0 := by norm_num [cfgDelta, term]

/-- wrapper: 15/15 -> 15/16, exactly 1/160 (published −0.006250 = 0.135313 − 0.129063). -/
theorem cfg_wrapper : cfgDelta 15 15 = 1 / 160 := by norm_num [cfgDelta, term]

/-- no_register: 12/15 -> 12/16, exactly 1/200 (published −0.005000 = 0.115313 − 0.110313). -/
theorem cfg_no_register : cfgDelta 12 12 = 1 / 200 := by norm_num [cfgDelta, term]

/-- Published compatibility statement: fully passed or fully failed Phase 3 gives the same
term in both versions. -/
theorem cfg_full_or_none (w : ℚ) :
    term w 15 15 = term w 16 16 ∧ term w 0 15 = term w 0 16 := by
  norm_num [term]

/-- Counter-check: a partly passed Phase 3 with the same passes is NOT comparable. -/
theorem cfg_partial_differs : term 1 12 15 ≠ term 1 12 16 := by norm_num [term]

/-! ## Reporting: Phase 2 weight 2/10 (14 tests), Phase 5 weight 1/10 (10 -> 12 tests) -/

def repDelta (p2o p2f p5o p5f : ℚ) : ℚ :=
  (term 2 p2f 14 + term 1 p5f 12 - term 2 p2o 14 - term 1 p5o 10) / 10

theorem rep_fullref : repDelta 14 14 10 12 = 0 := by norm_num [repDelta, term]
/-- fullref_junit_drops_error: −1/70 (published −0.014286). -/
theorem rep_drops_error : repDelta 14 13 10 12 = -1 / 70 := by norm_num [repDelta, term]
/-- fullref_no_body_fix: −1/120 (published −0.008333). -/
theorem rep_no_body_fix : repDelta 14 14 10 11 = -1 / 120 := by norm_num [repDelta, term]
/-- fullref_always_suppress: −1/60 (published −0.016667). -/
theorem rep_always_suppress : repDelta 14 14 10 10 = -1 / 60 := by norm_num [repDelta, term]
/-- starter and stub_junit_correct: Phase 5 2/10 -> 3/12, +1/200 (published +0.005000). -/
theorem rep_starter : repDelta 0 0 2 3 = 1 / 200 ∧ repDelta 5 5 2 3 = 1 / 200 := by
  norm_num [repDelta, term]
/-- stub_junit_drops_error: 5/14 -> 4/14 and 2/10 -> 3/12: −13/1400, which prints as −0.009286. -/
theorem rep_stub_drops : repDelta 5 4 2 3 = -13 / 1400 ∧
    |(-13 / 1400 : ℚ) - (-9286 / 1000000)| < 1 / 2000000 := by
  norm_num [repDelta, term, abs_lt]

/-- The headline bounds: the JUnit test is worth at most 1/70 of the total, a Phase 5 test at
most 1/100 (original, 10 tests). -/
theorem rep_bounds : term 2 1 14 / 10 = 1 / 70 ∧ term 1 1 10 / 10 = 1 / 100 := by
  norm_num [term]

/-! ## Datagen (score side of `DatagenHttpDate.lean`)

`/tests/test.sh` sha256 `82939a75d3ce1f9a7ef4f74420975e673cef8e4d8ed57085b9f468c6e0cfbf84`
(unchanged by the fix), l.255 `weights = [2, 1, 2, 2, 2, 1, 1, 2]` (sum 13), Phase 1 weight 2.
A full pass is reported as 8/8 (l.48 `PHASE1_EXPECTED=8`); one failing date test as 14/15
(paired/results.md). Published: −2/195 of the total, 0.477350 -> 0.467094. -/

theorem datagen_delta : (term 2 8 8 - term 2 14 15) / 13 = 2 / 195 ∧
    |(2 / 195 : ℚ) - (477350 - 467094) / 1000000| < 1 / 1000000 := by
  norm_num [term, abs_lt]

/-! ## Reporting: the original body test can never fail -/

/-- The two classes named `GeneratedValue`. -/
inductive Cls | coverage | negative deriving DecidableEq

inductive Scenario | unexpectedProps | other deriving DecidableEq

structure Val where
  cls : Cls
  scen : Scenario
deriving DecidableEq

/-- Original l.117-118 (deny case): filter on `negative.GeneratedValue`, then assert the
scenario is absent. -/
def origBodyTest (vals : List Val) : Bool :=
  !((vals.filter (fun v => v.cls == Cls.negative)).map (·.scen)).contains Scenario.unexpectedProps

/-- Fixed l.117-121: non-empty, all of `coverage.GeneratedValue`, and the scenario present
iff extra parameters are allowed. -/
def fixedBodyTest (allow : Bool) (vals : List Val) : Bool :=
  !vals.isEmpty && vals.all (fun v => v.cls == Cls.coverage) &&
    ((vals.map (·.scen)).contains Scenario.unexpectedProps == allow)

/-- `cover_schema_iter` yields only `coverage.GeneratedValue` (observed: 12 of 12 on the
starter). Under that premise the original test passes on every output whatsoever, including
one that contains the forbidden scenario and the empty output: it cannot fail. -/
theorem orig_vacuous (vals : List Val) (h : ∀ v ∈ vals, v.cls = Cls.coverage) :
    origBodyTest vals = true := by
  have : vals.filter (fun v => v.cls == Cls.negative) = [] := by
    rw [List.filter_eq_nil_iff]; intro v hv; simp [h v hv]
  simp [origBodyTest, this]

/-- Counter-check: the fixed deny test rejects the starter's behaviour (the forbidden
scenario present), the empty stream, and an always-suppress implementation in the allow case. -/
theorem fixed_rejects :
    fixedBodyTest false [⟨.coverage, .unexpectedProps⟩, ⟨.coverage, .other⟩] = false ∧
    fixedBodyTest false [] = false ∧
    fixedBodyTest true [⟨.coverage, .other⟩] = false := by decide

/-- ... and accepts correct behaviour in both cases. -/
theorem fixed_accepts :
    fixedBodyTest false [⟨.coverage, .other⟩] = true ∧
    fixedBodyTest true [⟨.coverage, .unexpectedProps⟩, ⟨.coverage, .other⟩] = true := by decide

end Ebv.Schemathesis

#print axioms Ebv.Schemathesis.cfg_identity
#print axioms Ebv.Schemathesis.cfg_wrapper
#print axioms Ebv.Schemathesis.cfg_no_register
#print axioms Ebv.Schemathesis.cfg_full_or_none
#print axioms Ebv.Schemathesis.cfg_partial_differs
#print axioms Ebv.Schemathesis.rep_fullref
#print axioms Ebv.Schemathesis.rep_drops_error
#print axioms Ebv.Schemathesis.rep_no_body_fix
#print axioms Ebv.Schemathesis.rep_always_suppress
#print axioms Ebv.Schemathesis.rep_starter
#print axioms Ebv.Schemathesis.rep_stub_drops
#print axioms Ebv.Schemathesis.rep_bounds
#print axioms Ebv.Schemathesis.datagen_delta
#print axioms Ebv.Schemathesis.orig_vacuous
#print axioms Ebv.Schemathesis.fixed_rejects
#print axioms Ebv.Schemathesis.fixed_accepts
