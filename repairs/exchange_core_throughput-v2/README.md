# exchange_core_throughput v2

**Defect** ([review](../../evidence/reviews/exchange_core_throughput-native.md)): the original correctness
check runs only `testThroughputPeak`, which does not compare fees, balances, positions or emitted
events. Two plausible one-edit engine bugs (a maker/taker fee swap that keeps the global balance at
zero; user events not forwarded) passed all 50 asserted rounds and scored higher than the correct
engine (24.40 and 15.62 vs 7.14 normalized). The project's own integration tests reject both.

**Change** (`files/eval_exchange_core.py`, generated `repair.patch`): before the unchanged timed
test, the evaluator runs the project's shipped integration tests `ITFeesExchangeBasic` and
`ITExchangeCoreIntegrationRejectionBasic` (33 tests) in a separate Maven invocation; if they do not
all pass, the submission scores 0 (`WA`). The timed run itself is unchanged. `files/m2/` pre-seeds
the public Maven artifacts the original image lacks (7 jars with their POMs, 30 files; listed in `source-lock.json`), so v2 grades offline; v1 needs network.

**Score compatibility:** correct engines score as in v1 (throughput is host-noisy); incorrect
engines that v1 rewarded now score 0. v2 scores are not comparable with v1 leaderboard entries.

**Limits:** two integration test classes cover fees, rejections and events, not every engine
invariant; throughput varies ±~20% run to run on the same worker (control 2,050–2,978 raw).
Paired evidence: [paired/results.md](paired/results.md).

## Build

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
