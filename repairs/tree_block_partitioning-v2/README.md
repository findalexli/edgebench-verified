# Fixed version of `tree_block_partitioning`: alias-safe T2 grading library

## What this fixes

In sub-problem T2, the library the grader supplies computes `x *= y` wrongly when a value is multiplied by itself (`v *= v`). A submission that does this, which the rules allow, loses up to 5 of 100 points. The fixed version swaps two lines so both old values are read first; every other call gives the same result as before.

In detail ([review](../../evidence/reviews/tree_block_partitioning.md)): in T2 (5 of 100 points), the
grader library's `Data::operator*=` writes `c` and then computes `d` from `x.c`. When a submission
calls `v *= v`, `x.c` has already been overwritten, so `d` comes out as `d·(c+1)²+d` instead of
`d·(c+1)+d`. The statement defines `x*=y` as "set x to x*y" with no rule that the operands must be
distinct objects. The library solvers can see (`down/lib.cpp`) uses a different monoid (the value type with its multiplication) and does not
show the bug. The reference solution never multiplies a value by itself.

## What changes

One file, `/opt/p1_judge/prob/P1/T2_P7881/data/interactive_lib.cpp`. The two
assignments are swapped so that `d=d*(x.c+1)+x.d;` runs before `c=(c+1)*(x.c+1)-1;` (`repair.patch`).
The file stays 1225 bytes with CRLF line endings, and the binary interface (ABI) is unchanged. The task JSON changes
only `judge.image_tag` (`task.json.in`). The work image and the files solvers can see are unchanged.

**Why this is the smallest fix.** The `d` statement reads `d`, `x.c` and `x.d`, and none of them has been written
yet. The `c` statement reads only `c` and `x.c`, which the `d` statement does not change. So every
call on distinct objects gives the same result as before, and the product of a value with itself becomes correct.
The review checked this with the TLA+ model (exhaustive at M=4) and a direct harness (0/1e6
differences on distinct objects).

**Score compatibility.** Scores under the fixed version are comparable with the original for any submission that never calls
`x *= x` on a non-identity T2 value. They are not comparable when a submission makes that call:
the fixed version grades it correctly, while the original marks those T2 cases WA (wrong answer). Only T2 (5 points) can differ.

## How it was checked

A side-by-side run of the original and fixed graders on the same submissions is in [paired/results.md](paired/results.md). The fix is accepted on that run.

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t ebv/tree_block_partitioning-judge:v2 .
```

`materialize.sh` takes the following steps:

1. Pull the pinned image(s) by digest, unless already present.
2. Extract the original files with `docker create` and `docker cp`. No container runs in this step.
3. Check each original against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of every file under `files/` (and `orig/`) against `source-lock.json` → `materialize.outputs`. Any mismatch fails loudly.

After that, the `Dockerfile` builds without changes. Regenerated files keep the file mode they have in the image.
See `../MATERIALIZE-CHECK.md` for how each package was verified.

## Limits

- The test submission that shows the problem is an audit construction derived from `std.cpp`, so how often real
  solvers multiply a value by itself is unknown.
- The hidden signed-`int` overflow in the c/d products is present in both the original and fixed versions and is not
  addressed.
- Each test submission ran once on one E2B worker.
