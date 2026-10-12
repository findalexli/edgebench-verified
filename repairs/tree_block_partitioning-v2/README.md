# tree_block_partitioning v2: alias-safe T2 grading library

**Defect** ([review](../../evidence/reviews/tree_block_partitioning.md)). In T2 (5 of 100 points), the
grading library's `Data::operator*=` writes `c` and then computes `d` from `x.c`. When a submission
calls `v *= v`, `x.c` has already been overwritten, so `d` comes out as `d·(c+1)²+d` instead of
`d·(c+1)+d`. The statement defines `x*=y` as "set x to x*y" with no rule that the operands must be
distinct objects. The solver-visible library (`down/lib.cpp`) uses a different monoid and does not
show the bug. The reference never self-multiplies.

**Change.** One file, `/opt/p1_judge/prob/P1/T2_P7881/data/interactive_lib.cpp`. The two
assignments are swapped so that `d=d*(x.c+1)+x.d;` runs before `c=(c+1)*(x.c+1)-1;` (`repair.patch`).
The file stays 1225 bytes with CRLF line endings, and the ABI is unchanged. The task JSON changes
only `judge.image_tag` (`task.json.in`). The work image and the solver-visible files are unchanged.

**Why minimal.** The `d` statement reads `d`, `x.c` and `x.d`, and none of them has been written
yet. The `c` statement reads only `c` and `x.c`, which the `d` statement does not change. So every
call on distinct objects gives the same result as before, and the self-product becomes correct.
The review checked this with the TLA+ model (exhaustive at M=4) and a direct harness (0/1e6
differences on distinct objects).

**Score compatibility.** v2 scores are comparable with v1 for any submission that never calls
`x *= x` on a non-identity T2 value. They are not comparable when a submission makes that call:
v2 grades it correctly, while v1 marks those T2 cases WA. Only T2 (5 points) can differ.

**Paired evaluation:** [paired/results.md](paired/results.md). The repair is accepted.

**Limits.**
- The trigger submission is an audit construction derived from `std.cpp`, so how often real
  solvers self-multiply is unknown.
- The latent signed-`int` overflow in the c/d products is present in both v1 and v2 and is not
  addressed.
- Each arm ran once on one E2B worker.

## Build

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
