# Fixed version of `equivalence_class_divide_and_conquer`: T3 checker counts the last state's size

## What this fixes

In sub-problem T3, the checker that grades each output leaves the size of the last neighbourhood reached (the target of the last move) out of its cost total. An output can therefore go over the cost budget by up to that size (at most 10⁶) and still be accepted. The fixed version counts that size too and changes nothing else.

Details ([review](../../evidence/reviews/equivalence_class_divide_and_conquer.md)): T3 is P8204, worth 10 of
100 points. At the end, the checker sums costs over states `0..tt-1` and leaves out the last
created state `t[tt]`, whose net coefficient is +1. The counted cost is therefore the true cost
minus |N_last|, where N_last is the target of the last operation. As a result, outputs whose true cost lies in (2.5·10⁹, 2.5·10⁹ + |N_last|] are
accepted, although the statement says "总代价不超过 2.5×10^9" (the total cost must not exceed 2.5×10^9). The excess is at most n ≤ 10⁶.

## What changes

One file, `/opt/p2_judge/prob/P2/T3_P8204/data/checker.cpp` (`repair.patch`):

- `std::iota(oq, oq+tt, 0), std::sort(oq, oq+tt, …)` becomes `oq+tt+1` in both places;
- `i<tt` becomes `i<=tt`.

CRLF line endings are kept. The arrays are sized `Q = 5N+1` and `tt ≤ 5m ≤ 5·10⁶`, so index `tt`
is in bounds. The task JSON changes only `judge.image_tag`. No time, memory, output or other
limits are changed.

**Why this is the smallest fix.** These are the only three tokens that set the range of the sum. Changing only the
`iota`/`sort` pair, or only the loop bound, would be wrong. The fix is byte-identical to the
review's instrumented checker (`checker_true_cost.cpp`) once its diagnostic print is removed. That
checker matched a brute-force calculation of the true cost on 329 random cases.

**Score compatibility.** Scores under the fixed version equal scores under the original for every output whose true cost is
≤ 2.5·10⁹ or > 2.5·10⁹ + |N_last|. They differ only for outputs inside the window.
The fixed version rejects those, and the original wrongly accepted them. Only T3 can differ.

**About the 64 MiB output allowance.** The earlier note that the "corrected checker needed a
64 MiB output allowance" comes from the earlier audit's own sandbox, which had a 16 MiB file cap.
It is not a property of the task. Inside the original grader image, `ulimit -f` is unlimited and
`eval_common.py` sets no output-size limit. The reference's largest T3 output is about 40.6 MB, and
it passes all 30 cases under both the original and the fixed version with no change to any limit (`paired/results.md`).

## How it was checked

A side-by-side run of the original and fixed graders on the same submissions is in [paired/results.md](paired/results.md). The fix is accepted on that run.

## Build and use

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

## Limits

- The test submission that shows the problem uses a crafted input (n = 10⁶ star), added as an extra T3 case. No official input
  places any known solution in the window.
- Each test submission ran three times, each time on a separate worker (runs 2 and 3 in `evidence/runs/equivalence_class_divide_and_conquer-v2-paired-rep2` and `-rep3`, both `status: exit=0`); verdicts and scores were identical in all three (`data/paired-repeatability.md`).
- The strictness quirks from comparing pairs, noted in the review, are unchanged.
