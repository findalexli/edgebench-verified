# tree_block_partitioning

## Claim

- (C1) The original `Data::operator*=` of the T2 judge library computes the stated product for
  every call on two distinct objects, and computes it wrongly for some self-aliased calls `v *= v`.
- (C2) The fixed library, which assigns `d` before `c`, computes the stated product for every call,
  aliased or not, and gives the same result as the original on every call with distinct objects.

## Model and link to the code

`evidence/formal/tla/tree_block_partitioning/DataMul.tla`, configs `alias_orig.cfg`,
`alias_patched.cfg`, `noalias_orig.cfg` and `noalias_patched.cfg`, runner `run_tlc.sh`, outputs
`tlc-*.out`. The module header maps each C++ statement of `operator*=` in
`opt/p1_judge/prob/P1/T2_P7881/data/interactive_lib.cpp` (sha256 `0c57271b…c982`) to one atomic
step: `chk_x`, `chk_this`, `a`, `b`, `c`, `d`. `this` and `x` are object identities T and X in a
two-object memory; T = X is the aliased call. `Patched = TRUE` runs the fixed order.

Invariants: `ResultCorrect` (on return, `mem[T] = Spec(init[T], init[X])`, the stated product on the
old values) and `FrameOK` (a distinct right-hand operand is never written).

## Result

**Model-checked (bounded)**, with fields modulo M = 4. Every config explores all 65,536 initial
memories (`Finished computing initial states: 65536` in each `tlc-*.out`).

| Config | Result (`tlc-*.out`) |
|---|---|
| `alias_orig` | `Invariant ResultCorrect is violated` |
| `alias_patched` | no error, 457,472 distinct states |
| `noalias_orig` | no error, 456,452 distinct states |
| `noalias_patched` | no error, 456,452 distinct states |

## Counter-check

`alias_orig` gives the counterexample (a,b,c,d) = (0,0,1,1): `c` becomes 3 first, so
`d = 1·(3+1)+1 ≡ 1 (mod 4)`, while the stated product gives `1·2+1 = 3`.

## Limits

- Bounded: arithmetic modulo 4 instead of 2^16. This is exhaustive finite-state checking, not a
  proof for the real field width.
- The call counter and its 2e7 guard, I/O, and the signed overflow of `(c+1)*(x.c+1)` after
  promotion to `int` are not modelled. The overflow exists in both versions
  (`evidence/reviews/tree_block_partitioning.md`).
- The model covers `operator*=` only, not how often a solver writes `v *= v`. Score effects are on
  the case page (`cases/tree_block_partitioning.md`).
