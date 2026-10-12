import Mathlib.Tactic.Ring
import Mathlib.Tactic.Linarith

/-!
# exchange_core_throughput: the original correctness gate is blind to fee swaps and dropped events

Source modelled (judge image
`seededge/edgebench.judge.exchange_core_throughput@sha256:6b1617315cd2bdc7248ed057b449042c215b90c7571e302378d3c8b3202bbb8d`,
paths under `/home/workspace/exchange-core/src/`):

* `test/java/exchange/core2/tests/util/ThroughputTestsModule.java`
  sha256 `dd5a5873a7c468218ae6775d5a87cd1984936a9a1fcdecf31a15fd08f486be29`.
  The gate of every one of the 50 rounds is lines 50-56:
    l.50  `assertTrue(container.totalBalanceReport().isGlobalBalancesAllZero());`
    l.53-56 `assertEquals(<generated final L2 book>, container.requestCurrentOrderBook(symbolId))` per symbol
    l.58  `// TODO compare events, balances, positions`
  -> `gateRound` below.  Called by `test/.../perf/PerfThroughput.java` l.61-79
  (sha256 `e0e45d8244fb382f624d558f65fef4ac65a53acc175e94d566f80d6f44f6ccc1`), iterations = 50 -> `gate`.
* `main/java/exchange/core2/core/common/api/reports/TotalCurrencyBalanceReportResult.java`
  sha256 `9a47ab7c80c4c66babf2b9c2c2aa2a7eb7edd9b378304362a256ea5a431afdc3`,
  l.80-90: global sum = mergeSum(accountBalances, ordersBalances, fees, adjustments, suspends),
  all-zero per currency -> `Ledger`, `globalSum`.
* `main/java/exchange/core2/core/processors/RiskEngine.java`
  sha256 `8e7f955e5079a013bd360bebc90fd354d2b2a0e71d34fc2391e1c6e5fe303c3a`.
  `handleMatcherEventsExchangeSell` l.687-736: taker quote credit l.729
  `takerSizePrice*quoteScaleK - takerFee*takerSize`; fee ledger l.734
  `takerFee*takerSize + makerFee*makerSize`; maker quote release l.717 -> `sellDelta`.
  `handleMatcherEventsExchangeBuy` l.738-791: maker credit l.769 `gained - makerFee*size`,
  fee ledger l.789 -> `buyDelta`.
* `main/java/exchange/core2/core/ExchangeCore.java`
  sha256 `f38670ff0b11c64b998ac063ac65d6e47962b6535369284f63f294d639f637ef`,
  l.205-208: results stage `resultsHandler.onEvent(cmd, seq, eob); api.processResult(seq, cmd);`
  The `dropevents` mutation removes the first call -> `Final.events`.
* `test/java/exchange/core2/tests/integration/ITFeesExchange.java`
  sha256 `8f6de92d09c0cf5730050568a7c5537a4c11ea4d02a95801a5d37d15423b9271`,
  `shouldProcessFees_BidGtcMaker_AskIocTakerPartial` l.127-200; seller-taker assertion l.188,
  fee assertion l.197. Fee spec `TestConstants.SYMBOLSPECFEE_XBT_LTC`: quoteScaleK 10000,
  takerFee 1900, makerFee 700.
* Evaluator `/tmp/eval_exchange_core.py` sha256
  `65bfba1129ef022ab3c3712769c335d8d1c42638a18a0e814a660e7647d8140a`: l.44-52 runs only
  `PerfThroughput#testThroughputPeak`; l.85-86 status OK iff Maven rc 0 and score > 0.

Mutations (`evidence/runs/exchange_core_throughput-wrongengine/inputs/mutate.py`):
feeswap = rate `makerFee` at both l.729 and l.734 (taker side); feeleak = changes only one of them.

Abstraction: amounts are unbounded integers (Java `long` overflow is not modelled); the
order-book / hold-release quantities that the mutations do not touch are free parameters.
-/

namespace Ebv.Exchange

/-! ## The gate (ThroughputTestsModule.java l.50-58) -/

/-- One currency's ledger in `TotalCurrencyBalanceReportResult` (l.37-41). -/
structure Ledger where
  accounts : List Int
  ordersBalances : Int
  fees : Int
  adjustments : Int
  suspends : Int

/-- `getGlobalBalancesSum` for one currency (l.80-82). -/
def globalSum (l : Ledger) : Int :=
  l.accounts.sum + l.ordersBalances + l.fees + l.adjustments + l.suspends

/-- Final state of one round: one ledger per currency, one L2 book per symbol, and the event
stream delivered to the user's results consumer. -/
structure Final (Book Ev : Type) where
  ledgers : List Ledger
  books : List Book
  events : List Ev

variable {Book Ev : Type} [DecidableEq Book]

/-- One round of the gate: l.50 (global balance all zero) and l.53-56 (books equal). -/
def gateRound (expected : List Book) (s : Final Book Ev) : Bool :=
  s.ledgers.all (fun l => globalSum l == 0) && s.books == expected

/-- The whole test: all 50 rounds pass (PerfThroughput l.61-79). -/
def gate (rounds : List (List Book × Final Book Ev)) : Bool :=
  rounds.all (fun r => gateRound r.1 r.2)

/-- The gate depends on the final state only through the per-currency global sums and the
books: any two final states that agree on those get the same verdict. -/
theorem gateRound_factors (e : List Book) (s t : Final Book Ev)
    (hs : s.ledgers.map globalSum = t.ledgers.map globalSum) (hb : s.books = t.books) :
    gateRound e s = gateRound e t := by
  unfold gateRound
  rw [hb]
  congr 1
  have key : ∀ (xs ys : List Ledger), xs.map globalSum = ys.map globalSum →
      xs.all (fun l => globalSum l == 0) = ys.all (fun l => globalSum l == 0) := by
    intro xs
    induction xs with
    | nil => intro ys h; cases ys with
      | nil => rfl
      | cons _ _ => simp at h
    | cons x xs ih => intro ys h; cases ys with
      | nil => simp at h
      | cons y ys =>
        simp only [List.map_cons, List.cons.injEq] at h
        simp only [List.all_cons, h.1, ih ys h.2]
  exact key _ _ hs

/-- The gate never reads the event stream: replacing it by anything (for `dropevents`, the
empty stream) leaves every round's verdict unchanged. -/
theorem gateRound_ignores_events (e : List Book) (s : Final Book Ev) (evs : List Ev) :
    gateRound e { s with events := evs } = gateRound e s := rfl

theorem gate_ignores_events (rs : List (List Book × Final Book Ev)) (f : List Ev → List Ev) :
    gate (rs.map (fun r => (r.1, { r.2 with events := f r.2.events }))) = gate rs := by
  unfold gate
  induction rs with
  | nil => rfl
  | cons r rs ih => simp only [List.map_cons, List.all_cons]; rw [← ih]; rfl

/-- Counter-check (the gate can fail): a round whose global sum in some currency is nonzero
is rejected, whatever the books. -/
theorem gateRound_rejects_imbalance (e : List Book) (s : Final Book Ev) (l : Ledger)
    (hl : l ∈ s.ledgers) (h : globalSum l ≠ 0) : gateRound e s = false := by
  unfold gateRound
  have : s.ledgers.all (fun l => globalSum l == 0) = false := by
    rw [List.all_eq_false]; exact ⟨l, hl, by simpa using h⟩
  rw [this]; rfl

/-! ## The fee handlers (RiskEngine.java l.687-791), quote currency -/

/-- One trade event of a taker command (fields read in l.700-723). -/
structure Trade where
  size : Int
  price : Int
  release : Int   -- calculateAmountBidReleaseCorrMaker(size, priceDiff, spec), l.716 (untouched)
  mine : Bool     -- uidForThisHandler(matchedOrderUid), l.710

/-- Change of the quote-currency global sum caused by one `handleMatcherEventsExchangeSell`
call. `rT` is the rate charged to the selling taker (l.729), `rF` the rate booked for the taker
side in the fee ledger (l.734); `makerFee` is the maker-side booking (l.734); `hold` is the
change in `ordersBalances` (held amounts of filled maker orders, computed by the report from the
order state, untouched by the mutations). Taker present (l.704). -/
def sellDelta (qk makerFee rT rF hold : Int) (ts : List Trade) : Int :=
  let T := (ts.map (·.size)).sum
  let PT := (ts.map (fun t => t.size * t.price)).sum
  let M := ((ts.filter (·.mine)).map (·.size)).sum
  let R := ((ts.filter (·.mine)).map (·.release)).sum
  (PT * qk - rT * T)          -- taker account, l.729
  + R                         -- maker accounts, l.717
  + (rF * T + makerFee * M)   -- fees ledger, l.734
  + hold                      -- ordersBalances

/-- The only way the taker rates enter the global sum is through `(rF - rT) * T`. -/
theorem sellDelta_rates (qk mf rT rF hold : Int) (ts : List Trade) :
    sellDelta qk mf rT rF hold ts
      = sellDelta qk mf 0 0 hold ts + (rF - rT) * (ts.map (·.size)).sum := by
  unfold sellDelta; ring

/-- Any consistent taker rate (same rate charged and booked: shipped engine `takerFee`,
`feeswap` `makerFee`, or any other) gives exactly the shipped engine's global-sum change. -/
theorem sellDelta_consistent (qk mf tf r hold : Int) (ts : List Trade) :
    sellDelta qk mf r r hold ts = sellDelta qk mf tf tf hold ts := by
  rw [sellDelta_rates, sellDelta_rates qk mf tf tf]; ring

/-- Same for the buy handler's maker side (l.769 charged, l.789 booked): `rM` charged to
the maker, `rFM` booked. Taker side of the buy handler carries no fee term (l.784-785). -/
def buyDelta (tf rM rFM other : Int) (ts : List Trade) : Int :=
  let T := (ts.map (·.size)).sum
  let M := ((ts.filter (·.mine)).map (·.size)).sum
  (- rM * M) + (tf * T + rFM * M) + other

theorem buyDelta_consistent (tf r tfM other : Int) (ts : List Trade) :
    buyDelta tf r r other ts = buyDelta tf tfM tfM other ts := by
  unfold buyDelta; ring

/-- Counter-check: an inconsistent edit (`feeleak`: charge `takerFee`, book `makerFee`)
shifts the global sum by `(makerFee - takerFee) * T`, nonzero whenever the fees differ and
the taker traded. -/
theorem sellDelta_leak_shifts (qk mf tf hold : Int) (ts : List Trade)
    (hf : tf ≠ mf) (hT : (ts.map (·.size)).sum ≠ 0) :
    sellDelta qk mf tf mf hold ts ≠ sellDelta qk mf tf tf hold ts := by
  rw [sellDelta_rates, sellDelta_rates qk mf tf tf]
  intro h
  have : (mf - tf) * (ts.map (·.size)).sum = 0 := by linarith
  rcases mul_eq_zero.mp this with h1 | h1
  · exact hf (by linarith)
  · exact hT h1

/-- What `feeswap` does change: the selling taker's own balance, by `(takerFee - makerFee)*T`. -/
theorem feeswap_taker_balance (PT T qk tf mf : Int) :
    (PT * qk - mf * T) - (PT * qk - tf * T) = (tf - mf) * T := by ring

/-! ## A whole run: global sum after a sequence of taker commands -/

/-- Global sum of the quote ledger after applying the sell-handler effects of a run with a
given pair of taker rates, starting from `g0`. -/
def runSum (qk mf rT rF g0 : Int) : List (Int × List Trade) → Int
  | [] => g0
  | (hold, ts) :: rest => runSum qk mf rT rF (g0 + sellDelta qk mf rT rF hold ts) rest

theorem runSum_consistent (qk mf tf r g0 : Int) (cmds : List (Int × List Trade)) :
    runSum qk mf r r g0 cmds = runSum qk mf tf tf g0 cmds := by
  induction cmds generalizing g0 with
  | nil => rfl
  | cons c rest ih =>
    obtain ⟨hold, ts⟩ := c
    simp only [runSum]; rw [sellDelta_consistent qk mf tf r hold ts]; exact ih _

/-- Main theorem (feeswap). If the shipped engine's run passes the gate, then any engine that
differs only by a consistent change of the sell-side taker rate passes it too, provided its
final books equal the shipped engine's. The book hypothesis is *not* proved here: the matcher
does not read the risk engine's fee rates, but risk checks (NSF rejections) read balances; it
was observed to hold in all 50 rounds of the recorded run. -/
theorem feeswap_passes (e : List Book) (qk mf tf r g0 : Int) (cmds : List (Int × List Trade))
    (others : List Ledger) (q : Ledger) (books : List Book) (evs : List Ev)
    (hq : globalSum q = runSum qk mf tf tf g0 cmds)
    (q' : Ledger) (hq' : globalSum q' = runSum qk mf r r g0 cmds)
    (hpass : gateRound e ⟨q :: others, books, evs⟩ = true) :
    gateRound e (⟨q' :: others, books, evs⟩ : Final Book Ev) = true := by
  rw [gateRound_factors e (⟨q' :: others, books, evs⟩ : Final Book Ev) ⟨q :: others, books, evs⟩
    (by simp [hq, hq', runSum_consistent qk mf tf r g0 cmds]) rfl]
  exact hpass

/-- Counter-check (feeleak): with a single trading command, an inconsistent rate makes the
final global sum differ from the shipped engine's; if the shipped engine's is 0 (the gate
passes), the feeleak engine's is not, so the gate rejects it. -/
theorem feeleak_rejected (e : List Book) (qk mf tf hold g0 : Int) (ts : List Trade)
    (others : List Ledger) (books : List Book) (evs : List Ev) (q' : Ledger)
    (hf : tf ≠ mf) (hT : (ts.map (·.size)).sum ≠ 0)
    (h0 : runSum qk mf tf tf g0 [(hold, ts)] = 0)
    (hq' : globalSum q' = runSum qk mf tf mf g0 [(hold, ts)]) :
    gateRound e (⟨q' :: others, books, evs⟩ : Final Book Ev) = false := by
  apply gateRound_rejects_imbalance e _ q' (by simp)
  rw [hq']
  simp only [runSum] at h0 ⊢
  intro h
  exact sellDelta_leak_shifts qk mf tf hold ts hf hT (by linarith)

/-! ## The fixed gate: integration tests AND the unchanged gate -/

/-- v2 `eval_exchange_core.py`: score 0 unless the 33 integration tests pass, then the
unchanged timed test. `it` is the (opaque) verdict of the Maven run of the 33 tests. -/
def fixedGate (it : Bool) (rs : List (List Book × Final Book Ev)) : Bool := it && gate rs

/-- The fix only removes acceptances; it never accepts what the original rejects. -/
theorem fixed_le_orig (it : Bool) (rs : List (List Book × Final Book Ev)) :
    fixedGate it rs = true → gate rs = true := by
  unfold fixedGate; intro h; simp at h; exact h.2

/-- And an engine that passes the integration tests is judged exactly as before. -/
theorem fixed_eq_orig_of_it (rs : List (List Book × Final Book Ev)) :
    fixedGate true rs = gate rs := by simp [fixedGate]

/-! ## ITFeesExchange l.188 and l.197 on the scenario's inputs (differential check)

Scenario `shouldProcessFees_BidGtcMaker_AskIocTakerPartial`: maker bid 1731 lots at 11500,
taker IOC ask 2000 lots, so T = M = 1731, price 11500, quoteScaleK 10000, takerFee 1900,
makerFee 700. The seller-taker starts with 0 LTC, so its LTC balance after the trade is the
l.729 credit. -/

/-- Seller-taker LTC balance with taker rate `rT` (RiskEngine l.729). -/
def itTakerLtc (rT : Int) : Int := 1731 * 11500 * 10000 - rT * 1731

/-- Fee ledger with taker-side booking `rF` (RiskEngine l.734). -/
def itFees (rF : Int) : Int := rF * 1731 + 700 * 1731

/-- Shipped engine: the model reproduces the expected value printed by surefire
(`Expected: is <199061711100L>`, it_fees_feeswap TEST-...ITFeesExchangeBasic.xml l.66). -/
theorem it_expected : itTakerLtc 1900 = 199061711100 := by norm_num [itTakerLtc]

/-- feeswap: the model reproduces the observed wrong value (`but: was <199063788300L>`, l.67). -/
theorem it_feeswap_observed : itTakerLtc 700 = 199063788300 := by norm_num [itTakerLtc]

/-- l.188 rejects every wrong sell-side taker charge on this scenario ... -/
theorem it_l188_exact (rT : Int) : itTakerLtc rT = (11500 * 10000 - 1900) * 1731 ↔ rT = 1900 := by
  unfold itTakerLtc; constructor <;> intro h <;> omega

/-- ... and l.197 rejects every wrong taker-side fee booking (so feeleak's other half too). -/
theorem it_l197_exact (rF : Int) : itFees rF = (700 + 1900) * 1731 ↔ rF = 1900 := by
  unfold itFees; constructor <;> intro h <;> omega

/-- Counter-check for the event model: a gate that did compare events (the l.58 TODO) would
reject `dropevents` whenever the reference run emits any event. -/
def gateRoundWithEvents [DecidableEq Ev] (e : List Book) (eEv : List Ev) (s : Final Book Ev) : Bool :=
  gateRound e s && s.events == eEv

theorem dropevents_caught_by_event_gate [DecidableEq Ev] (e : List Book) (eEv : List Ev)
    (s : Final Book Ev) (hne : eEv ≠ []) :
    gateRoundWithEvents e eEv { s with events := [] } = false := by
  unfold gateRoundWithEvents
  have : (([] : List Ev) == eEv) = false := by
    cases eEv with
    | nil => exact absurd rfl hne
    | cons _ _ => rfl
  simp [this]

end Ebv.Exchange

#print axioms Ebv.Exchange.gateRound_factors
#print axioms Ebv.Exchange.gate_ignores_events
#print axioms Ebv.Exchange.gateRound_rejects_imbalance
#print axioms Ebv.Exchange.sellDelta_consistent
#print axioms Ebv.Exchange.buyDelta_consistent
#print axioms Ebv.Exchange.sellDelta_leak_shifts
#print axioms Ebv.Exchange.runSum_consistent
#print axioms Ebv.Exchange.feeswap_passes
#print axioms Ebv.Exchange.feeleak_rejected
#print axioms Ebv.Exchange.fixed_le_orig
#print axioms Ebv.Exchange.fixed_eq_orig_of_it
#print axioms Ebv.Exchange.it_expected
#print axioms Ebv.Exchange.it_feeswap_observed
#print axioms Ebv.Exchange.it_l188_exact
#print axioms Ebv.Exchange.it_l197_exact
#print axioms Ebv.Exchange.dropevents_caught_by_event_gate
