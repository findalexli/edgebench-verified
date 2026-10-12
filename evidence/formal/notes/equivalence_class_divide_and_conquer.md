# equivalence_class_divide_and_conquer (T3, P8204 checker)

## Claim

(i) The original checker counts the true operation cost minus |N_last|, the size of the target
of the last operation 1. (ii) The fixed checker counts exactly the true cost, so it accepts if and
only if the true cost is at most W = 2.5·10⁹, as the statement requires. (iii) The original and
fixed verdicts agree for every true cost ≤ W and every true cost > W + |N_last|; they differ
exactly inside (W, W + |N_last|], where the original accepts and the fix rejects. The fix never
accepts an output the original rejected.

## Model and link to the code

`evidence/formal/lean/ebv/Ebv/EquivClassCost.lean` (output in `EquivClassCost.out`). The model
covers `/opt/p2_judge/prob/P2/T3_P8204/data/checker.cpp` in the digest-pinned judge image: the
original has sha256 `f92b52cc…4145`, the fix `14734cf3…299e`. The operation loop (lines 32–38)
is modelled as a state machine with `tt`, the stack `st[0..tp]` and `ct[]`. The true cost is
built up separately from the statement's definition (|new| − |top|). The cost loop (lines
40–43) is a sum over `oq`. Because of the `iota` and `sort`, `oq` is modelled as any permutation
of `0..tt-1` (original) or `0..tt` (fixed). The verdict is line 44, `w <= W`.

## Result

**Proved.** (i), (ii) and (iii) are proved for every operation sequence the checker accepts,
from one invariant: `cost = Σ_{k≤tt} ct[k]·|N_k|`, with `ct[tt] = 1` once `tt ≥ 1`. As a
differential check, the five crafted cases in `run_crafted_output.txt` (A–E: true cost,
|N_last|, original count and both verdicts) are proved as concrete runs. Each one matches the
recorded checker output.

## Counter-check

`not_always_agree`: case B (star with n = 10⁶, m = 2501, true cost 2.501·10⁹) is accepted by
the original and rejected by the fix, so "the verdicts always agree" is false.
`orig_not_true_cost` uses case E, where the true cost is 10⁶ and the original counts 0.
`orig_violates_contract` also fails as expected. The weaker claim, that the verdicts agree for
every cost ≤ W − |N_last|, is proved (`agree_below_weak`).

## Limits

The neighbourhood size of each state (the BIT and two-pointer computation, lines 40–43) is
taken as given. That code is the same in both versions, and only the index range of the sum
changed. The legality checks (lines 33–39) are shared by both versions and are not modelled
beyond the stack-pop check. The model does not cover parsing or 64-bit overflow. Overflow does
not occur here: the sum of |ct[k]| is at most 2·5·10⁶ and each size is at most 10⁶.
