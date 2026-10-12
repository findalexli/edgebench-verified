# equivalence_class_divide_and_conquer v2: T3 checker counts the final move's cost

**Defect** ([review](../../evidence/reviews/equivalence_class_divide_and_conquer.md)). In T3 (P8204, 10 of
100 points), the checker's final cost sweep covers states `0..tt-1` and leaves out the last
created state `t[tt]`, whose net coefficient is +1. The counted cost is therefore the true cost
minus |N_last|. As a result, outputs whose true cost lies in (2.5·10⁹, 2.5·10⁹ + |N_last|] are
accepted, although the statement says "总代价不超过 2.5×10^9". The leak is at most n ≤ 10⁶.

**Change.** One file, `/opt/p2_judge/prob/P2/T3_P8204/data/checker.cpp` (`repair.patch`):
- `std::iota(oq, oq+tt, 0), std::sort(oq, oq+tt, …)` becomes `oq+tt+1` in both places;
- `i<tt` becomes `i<=tt`.

CRLF line endings are kept. The arrays are sized `Q = 5N+1` and `tt ≤ 5m ≤ 5·10⁶`, so index `tt`
is in bounds. The task JSON changes only `judge.image_tag`. No time, memory, output or other
limits are changed.

**Why minimal.** These are the only three tokens that bound the sweep. Changing only the
`iota`/`sort` pair, or only the loop bound, would be wrong. The fix is byte-identical to the
review's instrumented checker (`checker_true_cost.cpp`) once its diagnostic print is removed. That
checker matched a brute-force oracle on 329 random cases.

**Score compatibility.** v2 scores equal v1 scores for every output whose true cost is
≤ 2.5·10⁹ − |N_last| or > 2.5·10⁹ + |N_last|. They differ only for outputs inside the leak window.
v2 rejects those, and v1 wrongly accepted them. Only T3 can differ.

**About the 64 MiB output allowance.** The earlier note that the "corrected checker needed a
64 MiB output allowance" comes from the earlier audit's own sandbox, which had a 16 MiB file cap.
It is not a property of the task. Inside the native judge image, `ulimit -f` is unlimited and
`eval_common.py` sets no output-size limit. The reference's largest T3 output is about 40.6 MB, and
it passes all 30 cases under both v1 and v2 with no change to any limit (`paired/results.md`).

**Paired evaluation:** [paired/results.md](paired/results.md). The repair is accepted.

**Limits.**
- The trigger uses a crafted input (n = 10⁶ star), mounted as an extra T3 case. No official input
  places any known solution in the leak window.
- Each arm ran once on one worker.
- The pair-equality strictness quirks noted in the review are unchanged.

## Build

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t ebv/equivalence_class_divide_and_conquer-judge:v2 .
```

`materialize.sh` takes the following steps:

1. Pull the pinned image(s) by digest, unless already present.
2. Extract the original files with `docker create` and `docker cp`. No container runs in this step.
3. Check each original against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of every file under `files/` (and `orig/`) against `source-lock.json` → `materialize.outputs`. Any mismatch fails loudly.

After that, the `Dockerfile` builds without changes. Regenerated files keep the file mode they have in the image.
See `../MATERIALIZE-CHECK.md` for how each package was verified.
