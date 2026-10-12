# Tree Block Partitioning (`tree_block_partitioning`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Combinatorial Optimization
- **Decision:** Repair v2. The supplied in-place multiply in the T2 grading library gives a wrong result when both operands are the same object (`v *= v`). The effect is at most 5/100 points (T2), and only for solvers that alias. A two-line swap fixes it.

## What the task promises

The task has six progressive problems worth 5, 5, 10, 15, 25 and 40 points. T2 (P7881) defines `Data` as a monoid and states: "使用 `x*=y` 可以将 $x$ 修改为 $x*y$", which means "using `x*=y` changes x to x*y". The statement places no rule that the two operands must be distinct objects. It also says the downloadable library differs from the one used for grading: "下发的交互库和实际测试的交互库不同".

## What we checked and how

- **Direct harness.** We compiled the original judge library with the evaluator's flags and compared it with an independent 64-bit oracle that evaluates the stated product on the old values. The oracle was checked on 1,000,000 random distinct-object products, 1,000,000 random self-products, and all scalar values 0–1000.
- **Native runs.** We ran the original evaluator (`eval.py --task T2`) in the pinned judge image, with `--network none --memory 4g --cpus 2`, using both the original and the patched library.
- **TLA+ model** of `operator*=`. It explores all 65,536 initial memories (fields modulo 4) and covers aliased and non-aliased calls under both the original and the patched statement order.
- **Paired v1/v2 evaluation.** This ran on one E2B worker. Every arm used the original `eval_cmd`, which grades all six subtasks.
- **Original identity:** judge image `seededge/edgebench.judge.tree_block_partitioning@sha256:6ebbb44a…69d2`. The key file is `P1/T2_P7881/data/interactive_lib.cpp`, sha256 `0c57271b…c982`.

## What we found

**Confirmed, narrower than the earlier wording.** The library computes `c=(c+1)*(x.c+1)-1;` and then `d=d*(x.c+1)+x.d;`. When `this == &x`, the second line reads `x.c` after the first line has already overwritten it. As a result, `d` becomes `d·(c+1)²+d` instead of `d·(c+1)+d`.

- **Example under the original library.** The input is `read_Data()` from scalar 1, which gives (1,1,1,1238).
  - Copy product `y*=copy`: (2,0,3,3714). This matches the oracle.
  - Self-product `x*=x`: (2,0,3,6190). This is wrong.
- **Rates:**
  - Random distinct-object products that disagree with the oracle: 0/1000000.
  - Random self-products that disagree: 999566/1000000.
- **Through the real evaluator.** We built an alias variant of the official `std.cpp`. It makes one local change: it computes the self-product when the two factors are equal, which the contract treats as the same computation.
  - On the original library the variant scores 1/10 OK, 9 WA, 0.25 points.
  - On the patched library it scores 10/10 AC, 5.00.
  - The one case it passes is the only case with zero self-products.
- **TLA+.** `ResultCorrect` is violated only for the aliased call under the original order. The non-aliased original and both patched configurations show no error.
- **Maximum effect:** at most 5 of 100 points (T2), and only for submissions that self-multiply a non-identity value. The official reference never aliases and scores 5/5 on both libraries.

**Narrowing:**

- That aliasing is "permitted by its operation contract" holds only by implication. The statement never mentions aliasing, although ordinary C++ value-type conventions support it.
- No natural solution pattern was found that needs `v *= v`.
- The solver-visible library uses a different monoid, so the bug cannot be found by local testing.

An earlier audit withheld this task because of the aliasing bug. Re-checking showed that the defect is confined to 5 points and never affects the reference. The fix is provably neutral for non-aliased calls, so withholding the other 95 points is not justified.

## Repair

v2 swaps the two assignments in `P1/T2_P7881/data/interactive_lib.cpp`, so that `d=d*(x.c+1)+x.d;` runs before `c=(c+1)*(x.c+1)-1;`. The file stays 1225 bytes with CRLF line endings, and the ABI is unchanged. The task JSON changes only `judge.image_tag`. The work image and the solver-visible files are unchanged.

| Arm | Submission | v1 raw / norm | v2 raw / norm | v1 → v2 per subtask (T1..T6 cases passed) | Exit v1/v2 | Pass rate v1 → v2 |
|---|---|---|---|---|---|---|
| Valid control | Official `std.cpp` for all six subtasks | **100 / 100** | **100 / 100** | 45/45, 10/10, 20/20, 10/10, 40/40, 10/10 in both | 0/0 | 1.000 → 1.000 |
| Trigger | T2 = alias variant of `std.cpp` (`make_alias_variant.py`); T1, T3–T6 empty | **0.25 / 0.25** (T2 1/10) | **5 / 5** (T2 10/10) | T2 1/10 → 10/10; all others 0 (empty) | 1/1 | 0.005 → 0.050 |
| Invalid control | T2 = `std.cpp` with the second merge factor dropped (`make_invalid_variant.py`); others empty | **0.25 / 0.25** (T2 1/10, 9 WA) | **0.25 / 0.25** (T2 1/10, 9 WA) | unchanged | 1/1 | 0.005 → 0.005 |

The invalid control is a logic error that actually exercises the merge path. It replaces an earlier missing-answer control, which never reached the alias path.

**Score compatibility:** v2 scores are comparable with v1 for any submission that never calls `x *= x` on a non-identity T2 value. For a submission that does make that call, v2 grades it correctly, while v1 marks those T2 cases WA. Only T2 (5 points) can differ.

## Limits and what was not run

- No model or solver re-runs. Effects are shown only on authored controls and counterexamples.
- The trigger submission is an audit construction derived from `std.cpp`. How often real solvers self-multiply is unknown, and probably low.
- A latent signed-`int` overflow in the c/d products is present in both v1 and v2 and is not addressed. No effect on scores was seen.
- The TLA+ model is bounded: fields are modulo 4 rather than 2^16. It omits the call counter and the overflow behaviour.
- Whether the upstream Luogu P7881 judge library has the same code was not checked.
- Each paired arm ran once, on one E2B worker.

## Reproduce

- Direct harness: `evidence/scripts/tree_block_partitioning/run_direct.sh` (output `direct-results.txt`)
- Native run: `evidence/scripts/tree_block_partitioning/run_native.sh` (output `native-results.txt`)
- TLA+ model: `evidence/formal/tla/tree_block_partitioning/DataMul.tla`, run with `run_tlc.sh`
- Paired evaluation: `repairs/tree_block_partitioning-v2/paired/run.sh` (results in `paired/results.md`)
- Patch: `repairs/tree_block_partitioning-v2/repair.patch`

Supporting records: `repairs/tree_block_partitioning-v2/` (source-lock.json, `paired/evidence/`).
