# exchange_core_throughput, fixed version

## What this fixes

The original grader's correctness check does not compare fees, balances or messages, so matching engines with simple bugs pass and get full credit. The fixed grader first runs 33 of the project's own integration tests and scores the submission 0 if any fails. It also ships the build files the original image lacks, so grading works without network access.

### The problem in detail

See the [review](../../evidence/reviews/exchange_core_throughput-native.md). The original correctness
check runs only `testThroughputPeak`, which does not compare fees, balances, positions or emitted
events. Two plausible one-edit engine bugs passed all 50 checked rounds and scored higher than the correct
engine (24.40 and 15.62 against 7.14 out of 100). The first is a maker/taker fee swap that keeps the global balance at
zero. The second stops forwarding user events. The project's own integration tests reject both.

## What changes

- **`files/eval_exchange_core.py`** (generated `repair.patch`): before the unchanged timed
  test, the grader runs the project's shipped integration tests `ITFeesExchangeBasic` and
  `ITExchangeCoreIntegrationRejectionBasic` (33 tests) in a separate Maven run. If they do not
  all pass, the submission scores 0 (`WA`, wrong answer). The timed run itself is unchanged.
- **`files/m2/`** pre-loads the public Maven artifacts the original image lacks (7 jars with their POMs, 30 files; listed in `source-lock.json`). So the fixed grader grades offline; the original grader needs network access.

**Score compatibility:** correct engines score as under the original version (throughput is noisy from machine to machine). Incorrect
engines that the original version rewarded now score 0. Fixed-version scores are not comparable with original leaderboard entries.

## How it was checked

A side-by-side run of the original and fixed graders on the same submissions: [paired/results.md](paired/results.md). Correct engines pass the integration tests and are timed. The two buggy engines pass the original grader and score 0 under the fixed grader.

## Limits

- The two integration test classes cover fees, rejections and events, not every property a correct engine must keep.
- Throughput varies ±~20% from run to run on the same cloud machine (correct engine 2,050–2,978 raw).

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t ebv/exchange_core_throughput-judge:v2 .
```

`materialize.sh` takes the following steps:

1. Pull the pinned image(s) by digest, unless already present.
2. Extract the original files with `docker create` and `docker cp`. No container runs in this step.
3. Check each original against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of every file under `files/` (and `orig/`) against `source-lock.json` → `materialize.outputs`. Any mismatch fails loudly.

After that, the `Dockerfile` builds without changes. Regenerated files keep the file mode they have in the image.
See `../MATERIALIZE-CHECK.md` for how each package was verified.

`files/m2/repository/**` are public Maven Central artifacts, not image files: `materialize.sh` downloads the 30 files by exact URL and checks each sha256 (needs network access).
