# Review: tree_block_partitioning (T2 aliasing defect in the judge library)

## Claim under review

> "A supplied multiplication routine gives a wrong result when input and output share storage, a case permitted by its operation contract. Six selected examples support a defect in 5/100 points. The official reference avoids it; the other 95 points are not invalidated."

Earlier disposition: **withhold original**. Earlier repair evidence: "T2 regression: reference 10/10, wrong 0/10 before/after correction" (`evidence/selected/tree-t2-repair-regression-acceptance.json`). The proposed repair swaps two lines (`$W/audit/evidence/tree-t2-alias-correction-proposal-v1/apply_overlay.py`).

## Pinned artifacts

| Item | Identity |
|---|---|
| Task JSON `tasks/tree_block_partitioning.json` | `44b08d0d5f7bd4660a3d2a073496a820798762724491d6f0bc1fdc7994b51be4` |
| Judge image | `seededge/edgebench.judge.tree_block_partitioning@sha256:6ebbb44ab188660b15d260143e942ddcf0ba3bceb0bb7d7c78e976b1a36669d2`. I pulled it and ran it. |
| Source export `tree_block_partitioning-000.tar.gz` | `8cc00cc94de41c2cdae3f2eb8ef4f901e387665836a4546856323a8169c9ee9c` |
| Judge T2 library `P1/T2_P7881/data/interactive_lib.cpp` (the file that gets linked for grading) | `0c57271bd1b05d3cfbb44558fcf2e2770bb020858aa4411eaaa725a89409c982`. The tar copy and the copy inside the image are identical. |
| Judge `lib.h` | `0b30e7e58eaeb3476085c2a510521eca8bc9481655d9a8e4602100ededf49844` |
| Downloadable library for solvers `T2_P7881/down/lib.cpp` | `9f8dd083fcbf642b7903941035363f549de5acc83861bea0b1c2f44a669d373b` |
| Reference solution `T2_P7881/std.cpp` | `e5fc6e9ba50eb4019c4ca710720d04569b918909f6796f1fb9e2377bb74dc657` |
| Statement `T2_P7881/题面.md` | `73ceff302e89fb856138293eb22dd126ea567ece69657be8bb8d3d28daa08c5d` |
| Checker `data/checker.cpp` | `5717bfcbff00e42a8fbf84dfdeb4991d6672e2bc8703fce20c83e815ec66b29a` |
| `eval_common.py` inside the image | `0b20c8bfa4cd1f717cabc68aa085abf7a1c5d28df8c70ac18e04b1fb728b7541`. It compiles with `g++ -std=c++17 -Ofast -pipe` using g++ 11.4.0. |
| Patched library made by my `patch_overlay.py` | `26c4edc615b1d5c3426fd592a857090210cbbc4179d6582ee160ce128e3ee2ea`. This matches the earlier patched hash. |

## Contract

From the task prompt (`agent_query`): T2 is worth 5 of the 100 points. When only some test points pass, each passed point earns half credit.

From the T2 statement (`题面.md`), quoted:

> Data 类型是一个含幺半群 $(D,*,e)$ … $\forall x,y,z\in D, x*(y*z)=(x*y)*z$; $\forall x\in D, x*e=e*x=x$
> 使用 `x.clr()` 可以将 $x$ 修改为 $e$；使用 `x=y` 可以将 $x$ 修改为 $y$；
> **使用 `x*=y` 可以将 $x$ 修改为 $x*y$**，这个操作的调用次数有常数上限 $2\times 10^7$，不计 $x=e$ 或 $y=e$ 的情况。
> 下发的交互库和实际测试的交互库不同。

In English: "Using `x*=y` changes x to x*y." The statement also says the downloadable library differs from the one used for grading.

**Is aliasing permitted?** Yes, by implication, but the statement never says so explicitly.

- The operation is defined on monoid *values* for all x, y in D.
- There is no rule that the two operands must be distinct objects.
- The rule that skips the call count when x=e or y=e shows the statement thinks about operand cases, and it still adds no restriction on aliasing.

The analogy with C aliasing does not apply. Aliasing undefined behaviour in C concerns `restrict` and `memcpy` on raw memory. This API is a C++ value-semantic compound operator, `operator*=(const Data&)`. By the ordinary convention of C++ value types, `v *= v` must work, as it does for `std::complex`, `std::valarray` and built-in arithmetic. A solver has no reason to expect that a self-product is forbidden.

**The library a solver can test with hides the bug.** `down/lib.cpp` uses a different monoid: `b+=`, and `d=max(d,x.d)`, which does not read `x.c`. Self-products are correct there. A solver testing locally therefore cannot discover the defect.

**Is the judge's monoid itself valid?** The product is `(a,b,C,d) * (a',b',C',d') = (a+a', b^b', C·C', d·C'+d')`, where `C = c+1`. In the C and d components this is composition of affine maps, which is associative. The element `e` (all zero) is an identity of the formula, so the shortcut branches for `e` in the library are consistent with it. The contract is therefore met for operands in distinct objects.

## Independent reproduction

### 1. Direct harness against the original library bytes

Script: `scripts/tree_block_partitioning/run_direct.sh`. Output: `direct-results.txt`.

- The harness compiles the original `interactive_lib.cpp` with the evaluator's flags, renaming the library's `main` to `lib_main`.
- It compares the library against an independent 64-bit oracle (`spec`), which evaluates the stated formula on the old values only.

Results:

```
=== orig library
input mk(1)                  (1,1,1,1238)      # what read_Data() makes from scalar v=1
copy  y*=copy                (2,0,3,3714)
alias x*=x                   (2,0,3,6190)      # wrong: d used the already-updated c
spec(mk1,mk1)                (2,0,3,3714)
random distinct-object products disagreeing with spec: 0/1000000
random self-products (x*=x) disagreeing with spec:    999566/1000000
scalar v in [0,1000]: self-product wrong for 1000/1001 values   # only v=0 (c=0) is unaffected
=== patched library
... alias x*=x (2,0,3,3714); 0/1000000; 0/1000000; 0/1001
```

**Mechanism.** The source reads:

```
c=(c+1)*(x.c+1)-1;
d=d*(x.c+1)+x.d;
```

When `this == &x`, the second line reads `x.c` after the first line has already overwritten it. The result is `d·(c+1)²+d` instead of `d·(c+1)+d`. For v=1 that gives 1238·4+1238 = 6190 instead of 3714, which matches the earlier "3714/6190" pair. The `a` and `b` fields are alias-safe, because each statement reads and writes only its own field.

### 2. Native run with the original evaluator, inside the pinned judge image

Script: `scripts/tree_block_partitioning/run_native.sh`. Output: `native-results.txt`.

Command: `eval.py --task T2 --time-factor 1 --time-grace 0 --score-sum` inside `docker run --rm --network none --memory 4g --cpus 2`. The patched library was bind-mounted read-only over the original file. Each run's log records the library's sha256 inside the container.

The submissions:

- **std**: the official `std.cpp`.
- **alias**: `make_alias_variant.py` makes one local change to `std.cpp`'s `MergeBlock`. When the two factors have bitwise-equal values, the variant computes `Tmp.info[tc] *= Tmp.info[tc]` instead of `Tmp.info[tc] *= B`. Because B equals A at that point, the contract makes this the same computation.

| Submission | Original library | Patched library |
|---|---|---|
| std (reference) | 10/10 AC, **5.00** | 10/10 AC, **5.00** |
| alias variant | 1/10 OK, 9 WA, **0.25** | 10/10 AC, **5.00** |

Self-products per case for the alias variant on the original library: case 1: 0, case 2: 10, case 3: 81, …, case 8: 850, case 10: 831, case 11: 772.

The one case that passes (case 1, with 10 operations) is the only case with zero self-products. This serves as an internal control: the failure follows the alias path, not anything else in the variant.

This is the first demonstration through the real checker and the real corpus that a submission which is correct under the contract loses T2 points. The earlier "wrong 0/10" regression used a missing-answer control. That control never reached the alias path, so the earlier installed-evaluator regression shows only that the patch preserves the reference's score.

## Refutation attempts

- **Is the contract really unrestricted?** Partly refuted. Aliasing is never explicitly allowed, so "a case permitted by its operation contract" holds only by implication; the statement never mentions it. I still judge it permitted, for the reasons in the Contract section.
- **Does the reference or the corpus trigger it?** No. `std.cpp` multiplies by `GetInfo(...)`, which returns a copy, into `Tmp`, which is a separate object. The reference never aliases and gets the full 5/5 on both libraries.
- **Is the trigger reachable only with a contrived fixture?** The trigger I used is my own construction. A natural T2 solution (block merging, lazy tags, time-ordered products) has no need for `v *= v`, and I found no standard solution pattern that requires it. Real incidence among solvers is therefore unknown and probably low. Still, it is reachable from a legal submission through the real harness, and it cost a correct submission 4.75 of 5 points.
- **Does the patch change any non-aliased result?** No. My direct harness found 0/1e6 random differences, and the TLA+ model is exhaustive at M=4 (below).
- **Other defects found along the way (not in the earlier claim):** `(c+1)*(x.c+1)` and `d*(x.c+1)` are evaluated in `int`, after promotion from `unsigned short`. Their products can reach about 2^32, so this is signed overflow, which is undefined behaviour in C++. It exists in both the original and the patched order. With g++ 11 and `-Ofast` it wraps in practice, and the reference passes, so I saw no effect on scores. It is a latent fragility, not a demonstrated defect.

## Formal check (TLA+)

Model: `formal/tla/tree_block_partitioning/DataMul.tla`. Configs: `*.cfg`. Runner: `run_tlc.sh`. Outputs: `tlc-*.out`.

**Mapping from source to model.**

- Each C++ statement of `operator*=` becomes one atomic step: `chk_x`, `chk_this`, `a`, `b`, `c`, `d`. Each step evaluates its right-hand side from the current memory and then stores the result, which is exactly how C++ sequences these statements.
- `this` and `x` are object identities T and X over a two-object memory. The aliased call is T = X.
- `Patched` reorders the steps to `d` before `c`.
- **Invariants:**
  - `ResultCorrect`: on return, `mem[T] = Spec(init[T], init[X])`, where `Spec` is the stated product on the old values.
  - `FrameOK`: a distinct right-hand operand is never written.
- **Bounds:** fields are modulo M = 4, standing in for 2^16. All 4^8 = 65,536 initial memories are explored, with search depth 7.
- **Omitted:** the call counter and the 2e7 guard (they never touch the fields), I/O, the real field width, and the signed-overflow undefined behaviour.

| Config | Result |
|---|---|
| `alias_orig` (T=X, original order) | **Invariant ResultCorrect is violated.** Counterexample: (a,b,c,d) = (0,0,1,1). Computed d = 1·(3+1)+1 ≡ 1 (mod 4), but the spec gives 1·2+1 = 3. |
| `noalias_orig` (negative control) | No error. 456,452 distinct states. |
| `alias_patched` | No error. 457,472 distinct states. |
| `noalias_patched` | No error. 456,452 distinct states. |

TLC 2 workers, Java 11. Within these bounds the model shows four things: the original loop is correct for distinct objects, it is wrong for self-aliasing, and the two-line swap fixes aliasing without changing any distinct-object result. TLC has no axioms to report; it is exhaustive finite-state checking, not a proof.

## Verdict

**CONFIRMED-NARROWER.**

- The defect is real. It is reproduced from the original bytes, both directly and through the real evaluator, and shown in a model with a negative control.
- Two parts of the earlier wording overstate it:
  1. "Permitted by its operation contract" holds only by implication.
  2. Only submissions that perform an in-place self-product are affected. Neither the reference nor any natural solution pattern I could identify does this.

## Disposition assessment

**I disagree with "withhold original."** The recommended disposition is **repair**, falling back to "retain with a note."

Reasons:

- The defect is confined to 5 of the 100 points.
- It affects only submissions that call `v *= v` on a non-identity value.
- It never affects the reference.
- The fix is a two-line swap that is provably neutral for every non-aliased call. Rescoring with the patched library therefore cannot change the score of any submission that never self-multiplies.

Withholding the whole task discards 95 points that this finding does not touch, and it addresses a scoring bias that is narrow and fully fixable. If the release policy forbids modifying the judge, "retain with a note" is defensible, but repairing is better. The earlier record itself says "T2 is 5/100 points; the other 95 … remain meaningful," which argues against withholding.

## Recommended publishable wording

> In T2 (5 of 100 points), the grading library's in-place product `v *= v` returns a wrong value because it reads a field it has already overwritten. The statement defines `x *= y` for arbitrary values and does not forbid this call. The reference solution never makes this call and scores fully. A contract-valid variant that does make it scored 0.25/5 instead of 5/5. Swapping two lines in the library fixes the self-product case and leaves every other result unchanged.

## Repair note

The earlier patch exchanges `c=(c+1)*(x.c+1)-1;` and `d=d*(x.c+1)+x.d;`. It is **correct and minimal**.

- The `d` statement reads only `d`, `x.c` and `x.d`. None of these has been written yet, and `d` and `x.d` are read before the store in the same full expression.
- The `c` statement reads only `c` and `x.c`, which the `d` statement does not change.
- The edit is byte-neutral (1225 bytes, CRLF preserved) and leaves the ABI unchanged.
- I verified it through the direct harness, the native run (std 5/5 → 5/5; alias variant 0.25 → 5/5) and TLC.

A more defensive alternative is `Data y = x;` followed by operating on `y`. It is equally correct but larger.

Optional hardening, outside this finding: compute the c and d products in `unsigned` to remove the signed-overflow undefined behaviour. This is not required by any observed result. If adopted, it should be a separate, reviewed change.

## Limits

- **Coverage:** I checked only T2. T1 and T3–T6 (95 points) were neither examined nor run.
- **Contrived trigger:** the trigger submission is my construction. I have no data on how often real solvers self-multiply.
- **Upstream unknown:** I did not check whether the upstream Luogu P7881 judge library has the same code.
- **TLA+ bounds:** the model is bounded (M = 4 rather than 2^16), and it omits the signed-overflow undefined behaviour and the call counter.
- **Scale of the native run:** one run per arm on one machine, under Docker `--cpus 2 --memory 4g`, with the evaluator's time factor of 1.
- **Cleanup:** all containers ran with `--rm`. The judge image (about 368 MB) was left pulled locally.
