# Vibrating Path Graph Coloring (`vibrating_path_graph_coloring`)

**结论：** 已修复。<mark>README 承诺每个用例 30 s，可在发布方 4 个 CPU 的评分器上，有效解法每个用例只要用了超过约 14 s CPU 就会超时，而只要一个用例超时，整份提交就没有分数。修复版限制同时运行的用例数不超过评分器的 CPU 数，并把整次运行的时限从 600 s 提高到 900 s。测试程序不接受 README 规定的三行零命中格式，这一点作为说明保留。在 37 个有证书的用例上，它对分数没有影响，另外 13 个用例还没有定论。</mark>

## 任务要求

智能体要解一个图着色谜题，即给网络里的点（顶点）着色，相连的点颜色不能相同，过程中还可以"命中"（hit）顶点。任务说明写道 "Your solution is scored on **50 fixed test cases**. Final score = sum of individual case scores. **Lower is better.**"（大意：解法在上述**固定测试用例**上计分，最终分数为各用例分数之和，**越低越好**。）它让解题者参阅 "`README.md` and `tools/README.md` for full problem details"（这两份文件中的完整题目细节）。README 规定的输出格式有三行。

- "Line 1: number of hits $Q$"（第一行：命中次数 $Q$）
- "Line 2: the vertices hit in order (1-indexed)"（第二行：按顺序列出被命中的顶点，从一开始编号）
- "Line 3: coloring of each vertex ($1 \leq x_i \leq K$)"（第三行：每个顶点的颜色）

README 没有给零命中的情形留任何例外。`tools/README.md` 里没有输出格式说明，也没有例外。类别：组合优化。

## 我们检查了什么

按 README，零命中时输出三行，命中那一行为空。测试程序只接受两行格式的零命中。随附的基线 `solution.py` 打印的是两行格式，`tools/src/verifier.py` 也按两行读取。

下表是原始测试程序下的例子。

| 输入 | 输出 | 原始测试程序 |
|---|---|---|
| 我们编写的二部 4 点路径，K=2 | `0\n1 2 1 2`（两行） | `Score = 0`，退出码 0 |
| 同上 | `0\n\n1 2 1 2`（三行，README 格式） | `wrong answer: expected 4 colors, got 0`，退出码 1 |
| 同上 | 两行，颜色无效 | WA，同色边，退出码 1（已知错误） |
| 我们编写的单条边，K=1 | `1\n1\n1 1`（Q>0，三行） | `Score = 9`，退出码 0（已知正确、带命中的答案） |
| 官方用例 0001,0002,0003,0004,0007,0008 | Q=0，基线着色，**两行** | 每个用例都是 WA "edge (...) has same color" |
| 同样的用例 | Q=0，同样的着色，**三行** | 每个用例都是 WA "expected N colors, got 0" |

**证据能说明什么。** 50 个官方用例中有 37 个可以证明，不命中的话输入图无法用 K 种颜色着色。在这些用例上，零命中的答案不管用哪种格式都是错的。其余 13 个固定的图我们没有证书。在假定生成器下得出的概率上界，定不了它们实际能否着色。解题者可以在有证书的用例上用命中、在其他用例上用零命中，所以这 37 个证书说明不了对一份完整提交的影响为零。

- **37/50 个用例有精确证书**（证明该图无法用 K 种颜色着色的简短证明）：
  - K=1 的 13 个用例，证书是任意一条边；
  - K=2 的 12 个用例，证书是一个奇环；
  - N=1000、K=3 的 6 个用例，证书是一个显式的 K4 团（四个两两相连的顶点；用例 0043 中的 K4 还单独检查过）；
  - N=1000、K=4 的 6 个用例，证书是一个显式的 K5 团。
- **其余 13 个用例** 的 N=10000、K∈{3,4}、平均度为 20，没有小规模的证书。联合界（把每一种可能的有效着色的概率加起来）在 K=4 时给出 ln P ≤ −14895，在 K=3 时给出 ≤ −29550。这假定用例来自已发布的均匀生成器。

**一个用例失败，整份提交作废。** 评测程序把答案错误、超时或运行出错的用例都记为 `float('inf')`，再加进总分（`/tmp/eval_vibrating_path.py`，第 20、35、37、39 和 54 行）。所以只要一个用例失败，就是 `TOTAL_SCORE inf`。EdgeBench 的评测框架把它当作原始结果（无穷大）收下，而 `rescale_score` 遇到无穷大不给 100 分制的分数（`sforge/harness/score_rescale.py:75-76`）。于是那份提交没有分数。在 `score_first` 下，更早的、没有失败用例的提交仍会保留。任务说明只说 "Final score = sum of individual case scores"（最终分数为各用例分数之和），没说失败的用例记多少分。

**在 4 个 CPU 的评分器上，每个用例的 30 s 缩水成约 14 s CPU 时间（已修复）。** README 承诺 "Time limit | 30 seconds / test case"（第 54 行）。时限按墙钟时间算（`TIME_LIMIT = 30`，第 9 行），同时跑 8 个用例（`ProcessPoolExecutor(max_workers=min(8, len(case_files)))`，第 45 行）。任务没有规定 CPU 数。EdgeBench 的排行榜配置 `examples/all-tasks-k8s/experiment.yaml`（引文见 [`evidence/impact/edgebench-leaderboard-config.md`](../evidence/impact/edgebench-leaderboard-config.md)）（sha256 `d9d299794ba946cae8d2b7f68a7879a35bb8565d95e78107edf79802993643be`）里，评分器沿用 `judge_cpu_limit: 4`。八个用例在 4 个 CPU 上每个约分到半个 CPU，还要和任务的 Python 测试程序抢 CPU。测试程序每个用例要 5.6–19.0 s CPU 时间（50 个用例共 579.6 s，在 1 个 CPU 上对正常对照解法的输出逐个用例测得，见 `repairs/vibrating_path_graph_coloring-v2/paired/tester_time.out`）。

下表是在原始评分器上用 `--cpus 4` 测得的结果（`evidence/runs/vibrating_path_graph_coloring-cpu4v8-a/result/out/summary.txt`、`-b`；在 `vibrating_path_graph_coloring-v2-paired-a` 中重复）。

| 有效解法（正常对照解法的输出，之前附加固定计算量） | 4 个 CPU | 8 个 CPU |
|---|---|---|
| 每个用例 12 或 14 s CPU | 50 OK，TOTAL 24,650,014（最慢的 14 s 用例：29.9 s） | 50 OK，TOTAL 24,650,014 |
| 每个用例 20 s CPU（在两台机器上测得） | **2 OK，48 TLE，TOTAL `inf`（无分数）** | 50 OK，TOTAL 24,650,014（100 分制下 2.06 分） |
| 计算到 25 s 墙钟截止时间 | 50 OK，TOTAL 24,650,014；每个用例 CPU 中位数 12.7 s | 50 OK，TOTAL 24,650,014；中位数 24.9 s |

另一次 4 个 CPU 的原始评分器运行（`evidence/runs/vibrating_path_graph_coloring-v2-paired-b`）里，25 s 截止时间的解法丢了 14 个用例（36 OK，14 TLE，TOTAL `inf`）。那次运行中，每个解法进程都在开始后 27.14 s 以内结束，而 14 个超时用例全在测试程序最慢的 25 个用例之列。测试程序超时（它自己的 `timeout=60`）和解法超时，评测程序报的都是 `TLE`。所以可能是测试程序只分到约半个 CPU，撞上了自己的 60 s 超时。这个原因是推断的，没有直接观察到。那次运行没记下测试程序的启动时间，而在另一个工作节点上记了这些时间的重复运行（`vibrating_path_graph_coloring-v2-paired-c`）两次都是 50/50 通过。原始评分器给这个解法一共评了九次（`-b` 和 `-c` 各运行三次，后者每次运行评两次分），只有这一次失败。修复版下六次评分全部通过（[可重复性](../repairs/vibrating_path_graph_coloring-v2/paired/results.md)）。

**随任务发布的说明。** 零命中时，测试程序接受两行输出，却不接受 README 写的三行格式（命中那一行为空）。在 37 个官方用例上，零命中的答案已证明无效，其余 13 个还没有定论。让解析器两种格式都接受，可以消除格式不一致，但这样的修复不在本修复包里，也没有证明它在官方用例上给出相同的分数。

## 影响有多大

- **CPU 数。** 在发布方的 4 个 CPU 下，有效解法如果每个用例用约 14–30 s CPU，在原始评分器下会丢掉全部分数（用每个用例 20 和 28 s 测得），在修复版下能得分。按截止时间停下的解法，在修复版下每个用例分到约两倍的 CPU（25 s 截止时间的解法，平均 12.84 s → 24.98 s，`vibrating_path_graph_coloring-v2-paired-b`）。我们没有测量分数会因此变多少。解题者每次提交后都能看到各用例的 TLE 结果，一次运行又会保留最好的有效提交，所以只有一次运行从没交过更快的有效解法时，才会丢分。
- **一个用例失败。** 全有或全无的规则没变，也仍然没有写明。
- **零命中格式。** 在 37 个有证书的用例上，分数影响为零，其余 13 个还没有定论。一个有效的零命中答案如果因为格式遭拒，整份提交的结果就变成非有限值。目前既找不到这样的官方用例实例，也没有一般性的零影响证明。

## 修复

修复版（`repairs/vibrating_path_graph_coloring-v2/`）改了 `/tmp/eval_vibrating_path.py` 同时运行的用例数。新函数 `cpu_quota_workers()`（与 `repairs/grid_turing_robot-v2/` 中的相同）从 cgroup 读取评分器的 CPU 配额（`cpu.max`，或 cgroup v1 的配额和周期），向下取整成整数个 CPU，没有配额时退回 `os.cpu_count()`，结果限制在 1 到 8 之间。进程池改为 `ProcessPoolExecutor(max_workers=min(cpu_quota_workers(), len(case_files)))`。`docker run --cpus N` 和发布方的 k8s 后端都会设置这个配额。有 8 个或更多 CPU 时，修复版评分器同时跑 8 个用例，和原始版完全一样。

任务 JSON 改了 `judge.image_tag`，并把 `judge.eval_timeout` 从 600 s 提高到 900 s。每个用例独占整个 CPU 时，评分时间更长，而本任务的测试程序又慢。有效解法接近 30 s 时限时，4 个 CPU 下最坏情况是 (50 × 30 s + 579.6 s) / 4 + 3/4 × 49 s ≈ 557 s，只比 600 s 低 7%。修复版下测到的最长评分耗时为 558.0 s（25 s 截止时间的解法，`vibrating_path_graph_coloring-v2-paired-b`），所以 600 s 的余量不够。30 s 的时限、README、测试程序、用例、解析器和分数刻度都不变，一个用例失败整份提交作废的规则也不变。

我们在 `--cpus 4` 下（另有一组是 `--cpus 8`）做了并排对照，两个评分器用相同的解法（`evidence/runs/vibrating_path_graph_coloring-v2-paired-a`、`-b`、`-c`，`result/out/summary.txt`；`repairs/vibrating_path_graph_coloring-v2/paired/results.md`）。

| 解法 | CPU 数 | 原始评分器 | 修复版 |
| --- | ---: | --- | --- |
| 正常对照解法，没有额外计算 | 4 | 50 OK，TOTAL 24,650,014 (2.06) | 50 OK，TOTAL 24,650,014 (2.06) |
| **每个用例 20 s CPU** | 4 | **2 OK，48 TLE，TOTAL `inf`（无分数）** | **50 OK，TOTAL 24,650,014 (2.06)** |
| **每个用例 28 s CPU** | 4 | **2 OK，48 TLE，TOTAL `inf`（无分数）** | **50 OK，TOTAL 24,650,014 (2.06)** |
| 计算到 25 s 墙钟截止时间（作业 `-b`） | 4 | **36 OK，14 TLE，TOTAL `inf`**；每个用例平均 12.84 s CPU | 50 OK，TOTAL 24,650,014；每个用例平均 24.98 s CPU |
| 同上，另外两次原始版运行和一次修复版运行（作业 `-c`） | 4 | 50 OK，TOTAL 24,650,014（两次）；12.77 / 12.81 s CPU | 50 OK，TOTAL 24,650,014；24.92 s CPU |
| 每个用例 40 s CPU（错误对照） | 4 | 50 TLE，TOTAL `inf` | 50 TLE，TOTAL `inf` |
| 每个用例 20 s CPU | 8 | 50 OK，TOTAL 24,650,014 | 50 OK，TOTAL 24,650,014 |

修复版下，最慢的 28 s 用例从开始到结束耗时 28.12 s。4 个 CPU 下的评分耗时分别为 438.4 s（每个用例 20 s）、508.6 s（每个用例 28 s）和最多 558.0 s（25 s 截止时间），都在新的 900 s `eval_timeout` 以内。在 `--cpus 1/2/3/4/8` 下，修复版评分器分别同时跑 1/2/3/4/8 个用例（`result/out/v2_workers.txt`）。

**分数是否可比？** 评分器有 8 个或更多 CPU 时，两个版本评分方式相同。4 个 CPU 时，在原始版下每个用例都按时完成的确定性解法，在修复版下输出和分数都不变。每个用例需要约 14 到 30 s CPU 的解法，则从没有分数变成有分数。一直搜到墙钟截止时间的解法，每个用例分到约两倍的 CPU，所以它在 4 个 CPU 下的两个评分器分数不可比。在修复版下，每个用例分到的 CPU 不会减少。

以下说明仍随修复版一起发布。

1. 零命中时，测试程序只接受两行格式，不接受 README 的三行格式。在 37 个官方用例上，零命中的答案已证明是错的，其余 13 个上的分数影响还没有定论。
2. 一个用例崩溃、超时或格式错误，总分就是 `inf`，整份提交没有分数。

## 我们如何检查

- **在 E2B 上的 CPU 运行和并排对照运行。** 每个用例做 12 到 28 s CPU 计算的有效解法、一个 25 s 墙钟截止时间的解法和一个 40 s 的错误对照，先在原始评分器上用 `--cpus 4` 和 `--cpus 8` 运行（`evidence/runs/vibrating_path_graph_coloring-cpu4v8-a`、`-b`），再在原始版和修复版评分器上并排对照（`vibrating_path_graph_coloring-v2-paired-a`、`-b`、`-c`）。每个作业都是 `status: exit=0`，在按摘要固定的评分器镜像里以 `--network none --memory 4g` 运行。每个解法先跑我们的正常对照解法（贪心 K 着色，按随附测试程序的规则模拟命中），再做额外计算，然后打印对照解法的答案，并记下自己在每个用例上的开始时间、结束时间和 CPU 时间（`result/out/timing/`）。每个用例的测试程序耗时另在 `--cpus 1` 下单独测量（`paired/tester_time.out`）。

- **原始评分器。** 我们在按摘要固定的原始公开镜像里以 `--network none` 运行原始测试程序和辅助程序。输入包括我们写的图（配两行和三行的零命中输出）、一个已知错误的着色、一个已知正确且带命中的输出，以及六个官方用例。`tools/bin/tester` 在评分器镜像和智能体工作镜像里完全相同。`tools/README.md` 是从工作镜像里读的。
- **精确证书。** 我们为每个官方用例给出"该图无法用 K 种颜色着色"的证明。K=1 时是一条边，K=2 时是一个奇环，此外还有逐对检查过的显式 K4 或 K5 团。
- **概率上界。** 对其余又大又稀疏的用例，我们在已发布生成器的模型下给出闭式的联合界。

## 局限

- 修复版评分器从 cgroup（`cpu.max`）读取 CPU 配额。这一点只用 `docker run --cpus` 测过，没有在 Kubernetes pod（EdgeBench 排行榜设置用的后端）里测。
- 没有 cgroup 配额时，修复版评分器退回 `os.cpu_count()`，它数的是主机的全部 CPU，不是评分器实际能用的 CPU（`os.sched_getaffinity`）。如果只限制了 CPU 集合、没有配额（例如 `docker run --cpuset-cpus`），或者 pod 看不到自己的 `cpu.max`，它仍可能和原版一样，同时跑的用例比 CPU 多。改用亲和性计数需要再做一次并排对照运行，所以我们没有改。
- 没有运行任何 AI 模型或解题者。影响只在我们写的测试提交和反例上演示过。
- 13/50 个用例靠的是概率上界，并假定用例来自已发布的均匀生成器。没有找到确切的种子，也没有做 SAT 反驳（由可满足性求解器给出的机器证明）。
- 我们没有审查振动路径图的规则本身。
- 我们没有检查过去的提交。
- CPU 的影响是在有 8 个 vCPU 的 E2B 工作节点上，用 4 和 8 个 CPU、单线程的固定计算量和截止时间测试解法测的。多线程的解题者和 3、5、6、7 个 CPU 的情形都没有测试。
- 4 个 CPU 时，按截止时间停的解题者在修复版下每个用例分到约两倍的 CPU，所以它在两个评分器下的分数不可比，我们没有测量变化多少。
- 一次原始评分器运行中，25 s 截止时间解法出现 14 次超时，原因是推断的（测试程序只有半个 CPU，撞上了自己 60 s 的超时），没有直接观察到。
- 测试程序的耗时，以及由此得出、用来定 900 s `eval_timeout` 的 557 s 上界，针对的都是正常对照解法的输出；检查别的输出可能更慢。评分器 CPU 少于 3 个时，900 s 的 `eval_timeout` 可能比每个用例 30 s 的时限先起作用（2 个 CPU 时约 1,065 s 的工作量）。配额向下取整，2.5 个 CPU 时同时跑 2 个用例。

## 复现

- 修复版：`repairs/vibrating_path_graph_coloring-v2/`（`materialize.sh`、`repair.patch`、`source-lock.json`；修复版评分器的 sha256 为 `3b72b9ed…bd23`）。并排对照运行：`repairs/vibrating_path_graph_coloring-v2/paired/run.sh` 和 `run-tester-log.sh`（实际运行版本：`evidence/runs/vibrating_path_graph_coloring-v2-paired-a/run.sh`、`-b`、`-c`）；在原始评分器上的 CPU 运行：`evidence/runs/vibrating_path_graph_coloring-cpu4v8-a/run.sh`、`-b`；测试程序耗时：`paired/tester_time.sh`。

- 测试程序的格式：`evidence/scripts/vibrating_path_graph_coloring/run_tester_forms.sh`（输入在 `inputs/`；输出 `run_tester_forms.out`）
- 零命中证书和上界：`evidence/scripts/vibrating_path_graph_coloring/zero_hit_reachability.py`（输出 `zero_hit_reachability.out`）
- 工作镜像中的文档：`evidence/scripts/vibrating_path_graph_coloring/work_image_docs.out`
- 固定标识：
  - 评分器镜像：`seededge/edgebench.judge.vibrating_path_graph_coloring@sha256:db8a9741831762040afb7e9819f997eb5f5293641fd5cd97d27fce3880ce084e`。
  - 工作镜像：`seededge/edgebench.work.vibrating_path_graph_coloring@sha256:ea4a4f4a959a5b0fcd4c884979f5a379b7ef73e3793719c4f80146a599e91c9e`。
  - 任务 JSON：sha256 `d3bba054…a9c5`。
  - `tools/bin/tester`：`b1c7694b8de3444c0459393b967851ad7d61e38a9a320222ce01ba7a1b446463`。
  - `README.md`：`d7a4af29cb6af5158aebaebadc3b7b991c505d3528bf523e715c6e340e719218`。
  - `/tmp/eval_vibrating_path.py`：`934a2b9de14bc1e155adab2a114d3dcf4d6fdbf48bedc860b78ca602ba3e9350`。
