# exchange_core_throughput: formal note

## Claim

1. The original correctness gate cannot see fees or events. A round's verdict depends only on the
   per-currency global sums and the final L2 books. So any engine change that keeps those two, in
   particular a consistent fee swap (maker/taker on the sell side, or on the buy side's maker leg)
   or dropping event delivery, gets the verdict the shipped engine gets.
2. The fix (33 integration tests, then the unchanged gate) never accepts anything the original
   rejects, and it judges engines that pass the tests exactly as before.

## Model and link to the code

`lean/ebv/Ebv/ExchangeGate.lean`. The header cites paths, sha256 and line numbers in the pinned image
`sha256:6b1617315cd2…`. The gate is `ThroughputTestsModule.java` l.50-58 (sha256 `dd5a5873…`), the
global sum `TotalCurrencyBalanceReportResult.java` l.80-90, and the fee handlers `RiskEngine.java`
l.687-791 (taker credit l.729, fee ledger l.734). The event path is `ExchangeCore.java` l.205-208;
the original evaluator is sha256 `65bfba11…`. The sell handler's change to the quote currency's
global sum is modelled with the charged and booked taker rates as parameters.

## Result: proved (blindness); the fix is proved only in its structure

- `gateRound_factors` and `gate_ignores_events`: the gate reads only the sums and the books.
- `sellDelta_rates`: the rates enter the global sum only as `(rF − rT)·T`. `sellDelta_consistent`,
  `buyDelta_consistent` and `runSum_consistent` (a whole run) follow, and so does `feeswap_passes`.
- Differential check: the l.729 formula reproduces the surefire values exactly: 199061711100
  expected, 199063788300 under feeswap (`it_expected`, `it_feeswap_observed`). `it_l188_exact` and
  `it_l197_exact`: on that scenario, the assertions at `ITFeesExchange` l.188 and l.197 reject every
  wrong taker charge and every wrong booking.
- `fixed_le_orig` and `fixed_eq_orig_of_it`: the fix only removes acceptances.

The fix is **not** formally proven correct. That the 33 tests reject feeswap and dropevents is
an observed result (surefire), not a theorem, and nothing shows the tests reject every wrong engine.

## Counter-check

`feeleak_rejected` and `sellDelta_leak_shifts`: charging `takerFee` while booking `makerFee` moves the
global sum by `(makerFee − takerFee)·T ≠ 0`, so the gate fails. This matches the observed RE for feeleak.
`dropevents_caught_by_event_gate`: a gate that compared events would reject dropevents.

## Limits

- `feeswap_passes` takes as a hypothesis that the final books are equal. Fee rates do not reach the
  matcher, but NSF risk checks read balances. Equal books were observed in all 50 rounds, not proved.
- Java `long` overflow is not modelled. Hold-release and order-balance amounts are free parameters.
- Base-currency legs are not modelled (they carry no fee).
- The integration tests themselves are opaque (`it : Bool`).
