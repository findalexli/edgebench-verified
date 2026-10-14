# Apple Incremental Game (`apple_incremental_game`)

**结论：** 已修复。<mark>README 承诺每个用例 30 s，但在发布方的 4-CPU 评分器上，每个用例用掉超过约 15 s CPU 的有效解法会超时，超时的用例得 0 分。修复版同时运行的用例数不超过评分器的 CPU 数。分数刻度的低端与一个独立模拟的结果一致；高端参考点没有核实；1 GB 内存上限没有对每个解法执行。</mark>

## 任务要求

这个任务改编自 AtCoder Heuristic Contest 的一道题（AHC058），是一个机器生产类的放置型（incremental）游戏。任务文本写道："Your solution is scored on **50 fixed test cases**. Final score = sum of individual case scores. **Higher is better.**"（解法在一组固定测试用例上评分；最终得分为各用例得分之和；越高越好。）单个用例的得分为 `round(1e5·log2 S)`（README:34-36）。类别：组合优化。

## 我们检查了什么

我们发现一个评分缺陷，即时限依赖 CPU 数（已修复）。下面是我们检查的各项。

- 评分器用 `piecewise_max` 方法换算原始结果（换算到 0–100 之前的数值）。0 分的参考点是 45,000,000（每个用例 900,000，即 S = 2⁹）。排名第 1 的参考点 282,791,094 对应 80 分，100 分对应 289,952,856.4（`tasks/apple_incremental_game.json`，`judge.rescale`；`sforge/harness/score_rescale.py`，`piecewise_max`）。随任务提供的初始解法什么也不做，S = K = 1，所以原始结果为 0，对应 0 分。我们另写了一个简单的贪心模拟器，它的原始结果为 **237,518,875**（每个用例 4.75M），对应 **17.7** 分（满分 100）。这低于排名第 30 水平的参考点（每个用例 5.25M），先后顺序符合预期。这一项只检查了刻度的低端。
- 我们没有核实高端参考点。rank30、rank1 和 100 分这三个点（262,328,915.67、282,791,094 和 289,952,856.42）不是整数；乘以 3 和乘以 12 后才得到整数（786,986,747 和 3,479,434,277），看起来可能是从另一个用例数换算来的。它们的来源，以及在这 50 个用例上能否拿到 100 分，我们没有核实。姊妹任务 Treant 用的是同一套评估器代码，它排名第 1 的参考点是可达最大值的 3.58 倍（`evidence/reviews/_game-tasks-correctness.md`，第 8 节）。
- 在 4-CPU 评分器上，每个用例的 30 s 缩水为约 15 s CPU（已修复）。README 承诺 "Time limit | 30 seconds / test case"（第 71 行）。这个时限按墙钟时间计（`TIME_LIMIT = 30`，`/tmp/eval_apple_incremental_game.py` 第 9 行），评分器同时运行 8 个用例（`max_workers=min(8, len(case_files))`，第 45 行），超时的用例得 0 分（第 37 行）。任务没有规定 CPU 数。EdgeBench 的排行榜配置是 `examples/all-tasks-k8s/experiment.yaml`（引用见 [`evidence/impact/edgebench-leaderboard-config.md`](../evidence/impact/edgebench-leaderboard-config.md)）（sha256 `d9d299794ba946cae8d2b7f68a7879a35bb8565d95e78107edf79802993643be`），其中评分器继承 `judge_cpu_limit: 4`，于是 8 个用例每个大约分到半个 CPU。我们在原始评分器上用 `--cpus 4` 测量（`evidence/runs/apple_incremental_game-cpu4v8-a/result/out/summary.txt`，`-b`；在 `apple_incremental_game-v2-paired` 中重复），用的是我们自己写的正常贪心对照解法（TOTAL 99,714,418，5.04 分，满分 100）。随任务提供的基线每个用例都得 0 分，看不出 OK 与 TLE 的差别，所以我们没有用它。每个用例额外做 12 或 14 s CPU 工作时，50/50 通过；额外做 20 s 时，两个工作节点上都有 50 个用例中的 48 个超时，总分降到 3,955,266，即 0 分（满分 100）。在 `--cpus 8` 下全部通过，得 99,714,418。一个在 25 s 墙钟截止时间停止的解法，在 4 个 CPU 下每个用例平均只得到 13.00 s CPU，在 8 个 CPU 下为 24.94 s。
- 评分可以重复，评估器代码不引入随机性。逐用例分数来自测试程序 `tools/bin/tester`。我们没有检查它的代码，但在各次 CPU 运行中，它给我们贪心对照解法的输出打分，每次都是 99,714,418。

任务文本（README）写明内存上限为 1 GB，但评分器没有对每个解法执行这一上限。

随任务发布的说明写明，宣称的 1 GB 内存规定没有对每个解法执行。

说明没有交代高端参考点（rank30、rank1 和 100 分）的来源，我们也没有核实。

## 影响有多大

先看 CPU 数。在发布方的 4 个 CPU 下，如果解法每个用例用掉超过约 15 s CPU，原始评分器会让它丢掉这些用例（每个 0 分）。丢掉 50 个用例中的 48 个，几乎就是丢掉全部分数（实测中，我们的对照解法从 5.04 → 0；对更强的解题者，这一点是从用例数推出的，没有测量）。修复版会正常给这些用例评分。按截止时间停止的解法在修复版下，每个用例分到的 CPU 约为原来的两倍（25 s 截止时间的解法平均从 13.00 s → 24.99 s）；它的分数会因此变化多少，我们没有测量。

再看说明事项。刻度低端没有带来分数影响。高端参考点没有核实，所以不能排除它们带来的影响。内存说明不影响正常解法的分数，只对依赖所述上限的用户有意义。

## 修复

修复版（`repairs/apple_incremental_game-v2/`）改变了 `/tmp/eval_apple_incremental_game.py` 同时运行的用例数。新函数 `cpu_quota_workers()` 与 `repairs/grid_turing_robot-v2/` 中的相同。它从 cgroup 读取评分器的 CPU 配额（`cpu.max`，或 cgroup v1 的 quota 和 period），向下取整为整数个 CPU，没有配额时退回到 `os.cpu_count()`，并把结果限制在 1 到 8 之间。进程池改为 `ProcessPoolExecutor(max_workers=min(cpu_quota_workers(), len(case_files)))`。`docker run --cpus N` 和发布方的 k8s 后端都会设置这一配额；在 `--cpus 1/2/3/4/8` 下，修复版评分器分别同时运行 1/2/3/4/8 个用例（`apple_incremental_game-v2-paired/result/out/v2_workers.txt`）。任务 JSON 只改了 `judge.image_tag`。30 s 时限、600 s 的 `eval_timeout`、README、测试程序、用例和分数刻度都没有变。在 8 个或更多 CPU 下，修复版评分器同时运行 8 个用例，与原版完全相同。

我们在 `--cpus 4` 下做了并排对照测试（另有一组在 `--cpus 8` 下），两个评分器用相同的解法（`evidence/runs/apple_incremental_game-v2-paired/result/out/summary.txt`；`repairs/apple_incremental_game-v2/paired/results.md`）。

| 解法 | CPU 数 | 原始评分器 | 修复版 |
| --- | ---: | --- | --- |
| 正常对照解法，无额外工作 | 4 | 50 OK，TOTAL 99,714,418（5.04） | 50 OK，TOTAL 99,714,418（5.04） |
| **每个用例 20 s CPU** | 4 | **2 OK，48 TLE，TOTAL 3,955,266（0.00）** | **50 OK，TOTAL 99,714,418（5.04）** |
| **每个用例 28 s CPU** | 4 | **2 OK，48 TLE，TOTAL 3,955,266（0.00）** | **50 OK，TOTAL 99,714,418（5.04）** |
| 工作到 25 s 墙钟截止时间 | 4 | 50 OK，TOTAL 99,714,418；每个用例平均 13.00 s CPU | 50 OK，TOTAL 99,714,418；每个用例平均 24.99 s CPU |
| 每个用例 40 s CPU（坏对照） | 4 | 50 TLE，TOTAL 0 | 50 TLE，TOTAL 0 |
| 每个用例 20 s CPU | 8 | 50 OK，TOTAL 99,714,418 | 50 OK，TOTAL 99,714,418 |

在修复版下，最慢的 28 s 用例从开始到结束用了 28.02 s（`result/out/timing_summary.txt`）。4 个 CPU 时，评分最多需要 ⌈50/4⌉ = 13 轮，每轮 30 s。坏对照每个用例都超时，用了 390.8 s（原版：210.7 s），没有超过任务 600 s 的 `eval_timeout`。390.8 s 是这次实测的运行时间，不是算出来的上限。

评分器有 8 个或更多 CPU 时，两个版本的评分方式相同。在 4 个 CPU 下，一个确定性的解法如果在原版下每个用例都按时完成，在修复版下输出和分数都不变；每个用例需要约 15 到 30 s CPU 的解法，在修复版下这些用例会正常得分，不再是 0 分。一直搜索到墙钟截止时间的解法，每个用例得到的 CPU 约为原来的两倍，所以它在 4 个 CPU 下两个评分器给出的分数不能比较。修复版不会减少任何用例的 CPU。

修复版仍附带两条说明。一是 1 GB 内存上限没有对每个解法执行，二是我们没有核实高端参考点的来源和可达性。

## 我们如何检查

- 我们读了原始公开镜像中的评分器源码文件 `eval_apple_incremental_game.py`。它与 Treant 任务的代码相同，`TIME_LIMIT=30`，分数刻度为 `piecewise_max`。
- 我们在 E2B 上做了 CPU 运行和并排对照测试。测试解法包括：每个用例做 12 到 28 s CPU 工作的有效解法、一个 25 s 墙钟截止时间解法和一个 40 s 的坏对照。它们先在原始评分器上用 `--cpus 4` 和 `--cpus 8` 运行（`evidence/runs/apple_incremental_game-cpu4v8-a`、`-b`；台账作业名 `cpu4v8-games-a`、`-b`），再在原始评分器和修复版评分器上并排对照运行（`evidence/runs/apple_incremental_game-v2-paired`）。每个作业都是 `status: exit=0`，都在按摘要固定的评分器镜像中以 `--network none --memory 4g` 运行。每个解法先运行我们的正常对照解法（一个 level-0 的投资回报率贪心），再做额外工作，然后输出对照解法的答案，并记录每个用例自己的开始时间、结束时间和 CPU 时间（`result/out/timing/`）。
- 我们运行了一个独立的贪心模拟器，它向前看一步，按任务文本的规则运行，覆盖随任务提供的全部 50 个用例。它不是原始的测试程序。
- 我们检查了时间预算和分数刻度的算术（`evidence/scripts/_game-tasks-correctness/check_arith.py`）。脚本里写的贪心总分 237,518,875 是观测值；模拟器本身的输出没有保存在本仓库中。

## 局限

- 修复版评分器从 cgroup（`cpu.max`）读取 CPU 配额。我们只用 `docker run --cpus` 测试过，没有在 Kubernetes pod 中测试，而 EdgeBench 的排行榜设置用的正是这个后端。
- 我们没有运行任何 AI 模型或解题者。影响只在我们写的测试提交和反例上展示。
- 贪心检查用的是独立模拟器，不是原始的 `tools/bin/tester`。用原始测试程序给一份贪心输出打分，就能补上这个缺口。
- 原始评分器和修复版评分器只在 CPU 测量和并排对照测试中运行过，都在按摘要固定的评分器镜像内，CPU 数为 4 和 8，工作节点是有 8 个 vCPU 的 E2B 机器。我们没有测试 3、5、6 和 7 个 CPU。
- CPU 测试解法都是单线程的，要么做固定量的 CPU 工作，要么工作到 25 s 墙钟截止时间。我们没有测试多线程的解题者。
- 采用截止时间策略的解题者，在 4 个 CPU 下、在修复版中每个用例得到的 CPU 约为原来的两倍，所以它们在两个评分器下的分数不能比较。我们没有测量分数会变化多少。
- 评分器 CPU 少于 3 个时，起约束作用的是 600 s 的 `eval_timeout`，不是每个用例 30 s（2 个 CPU 时为 25 轮 × 30 s = 750 s）。评分器要等所有用例结束才输出结果，所以一份提交如果撞上 `eval_timeout`，全部输出都会丢失，得 0 分。因此在少于 3 个 CPU 时，如果一个解法的大多数用例都超时，它在修复版下的得分可能比原版低（由代码推出，没有运行）。配额向下取整：2.5 个 CPU 时同时运行 2 个用例。
- 没有 cgroup 配额时，修复版评分器回退到 `os.cpu_count()`。它统计的是主机的全部 CPU，而不是评分器能用的 CPU（`os.sched_getaffinity`）；如果只限制了 CPU 集合、没有配额，它仍可能同时运行比 CPU 数更多的用例。
- 我们在一台干净的机器上从零重建过修复包（`evidence/runs/materialize-check-g1`，`status: exit=0`）。`materialize.sh` 原样运行，输出与锁定值一致，构建出的镜像中是锁定的文件。
- 我们没有核实高端参考点的来源和可达性。

## 复现

- 评分器镜像：`seededge/edgebench.judge.apple_incremental_game@sha256:d3af7b43331078bb3ef29fab70c502cbb72d0e08d52e59cf9bdb044105d63f39`；`/tmp/eval_apple_incremental_game.py` sha256 `c33f5257…d70c`。
- 修复版：`repairs/apple_incremental_game-v2/`（`materialize.sh`、`repair.patch`、`source-lock.json`；修复版评分器 sha256 `ba31e840…1931`）。并排对照测试：`repairs/apple_incremental_game-v2/paired/run.sh`（实际运行的版本：`evidence/runs/apple_incremental_game-v2-paired/run.sh`）；原始评分器上的 CPU 运行：`evidence/runs/apple_incremental_game-cpu4v8-a/run.sh`、`-b`。

- 审查记录：`evidence/reviews/_game-tasks-correctness.md`，第 9 节。
- 贪心模拟器：`evidence/scripts/_game-tasks-triage/apple/greedy_lookahead.py`。
- 原始评分器：评分器镜像中的文件 `eval_apple_incremental_game.py`（sha256 见[审查记录](../evidence/reviews/_game-tasks-correctness.md)）。本仓库没有发布它的副本。
