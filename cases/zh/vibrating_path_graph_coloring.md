# Vibrating Path Graph Coloring (`vibrating_path_graph_coloring`)

**结论：** 已修复。<mark>在发布方 4 个 CPU 的评分器上，每个用例使用超过约 14 s CPU 的有效解法会超时，尽管 README 承诺每个用例 30 s，而只要有一个用例超时，整份提交就没有分数。修复版让同时运行的用例数不超过评分器的 CPU 数，并把整次运行的时限从 600 s 提高到 900 s。测试程序拒绝 README 规定的三行零命中格式，这一问题作为说明保留；它对分数的影响在 37 个有证书的用例上已被排除，在 13 个用例上仍未解决。</mark>

## 任务要求

智能体求解图着色谜题：给一个网络中的点（顶点）着色，使相连的点颜色不同，并且在过程中可以"命中"（hit）顶点。任务说明写道："Your solution is scored on **50 fixed test cases**. Final score = sum of individual case scores. **Lower is better.**"（大意：解法在上述**固定测试用例**上计分，最终分数为各用例分数之和，**越低越好**。）它让解题者参阅 "`README.md` and `tools/README.md` for full problem details"（这两份文件中的完整题目细节）。README 规定的输出格式有三行：

- "Line 1: number of hits $Q$"（第一行：命中次数 $Q$）
- "Line 2: the vertices hit in order (1-indexed)"（第二行：按顺序列出被命中的顶点，从一开始编号）
- "Line 3: coloring of each vertex ($1 \leq x_i \leq K$)"（第三行：每个顶点的颜色）

README 没有为零命中的情形给出任何例外。`tools/README.md` 不含任何输出格式说明，也没有例外。类别：组合优化。

## 我们检查了什么

**规则。** 对零命中，README 的格式是三行，其中命中一行为空。测试程序只接受两行格式的零命中。随附的基线 `solution.py` 打印的是两行格式，`tools/src/verifier.py` 也以同样方式读取。

**原始测试程序下的例子。**

| 输入 | 输出 | 原始测试程序 |
|---|---|---|
| 我们编写的二部 4 点路径，K=2 | `0\n1 2 1 2`（两行） | `Score = 0`，退出码 0 |
| 同上 | `0\n\n1 2 1 2`（三行，README 格式） | `wrong answer: expected 4 colors, got 0`，退出码 1 |
| 同上 | 两行，颜色无效 | WA，同色边，退出码 1（已知错误） |
| 我们编写的单条边，K=1 | `1\n1\n1 1`（Q>0，三行） | `Score = 9`，退出码 0（已知正确、带命中的答案） |
| 官方用例 0001,0002,0003,0004,0007,0008 | Q=0，基线着色，**两行** | 每个用例都是 WA "edge (...) has same color" |
| 同样的用例 | Q=0，同样的着色，**三行** | 每个用例都是 WA "expected N colors, got 0" |

**证据能说明什么。** 在 50 个官方用例中的 37 个上，可以证明输入图不经命中就无法用 K 种颜色着色。在这些用例上，零命中的答案无论用哪种格式都是错的。其余 13 个固定的图在这里没有证书；在假定的生成器下得到的概率上界，并不能确定它们实际的可着色性。解题者可以在有证书的用例上使用命中、在其他用例上使用零命中，所以这 37 个证书并不能说明对一份完整提交的影响为零。

- **37/50 个用例有精确证书**（证明该图无法用 K 种颜色着色的简短证明）：
  - K=1 的 13 个用例：任意一条边；
  - K=2 的 12 个用例：一个奇环；
  - N=1000、K=3 的 6 个用例：一个显式的 K4 团（四个两两相连的顶点；用例 0043 中的 K4 还单独检查过）；
  - N=1000、K=4 的 6 个用例：一个显式的 K5 团。
- **其余 13 个用例** 的 N=10000、K∈{3,4}、平均度为 20，没有小规模的证书。联合界（把每一种可能的有效着色的概率加起来）在 K=4 时给出 ln P ≤ −14895，在 K=3 时给出 ≤ −29550。这假定用例来自已发布的均匀生成器。

**只要一个用例失败，就会使整份提交作废。** 评测程序把每个错误答案、超时或运行时错误的用例分数记为 `float('inf')`，并把它加到总分中（`/tmp/eval_vibrating_path.py`，第 20、35、37、39 和 54 行）。因此一个失败的用例就会使 `TOTAL_SCORE inf`。EdgeBench 的评测框架把它当作原始结果（无穷大）接受，而 `rescale_score` 对无穷大不给出 100 分制的分数（`sforge/harness/score_rescale.py:75-76`）。所以那份提交没有分数；在 `score_first` 下，更早的、没有失败用例的提交仍会被保留。任务说明只说 "Final score = sum of individual case scores"（最终分数为各用例分数之和），没有说明失败的用例记多少分。

**在 4 个 CPU 的评分器上，每个用例的 30 s 缩水为约 14 s 的 CPU 时间（已修复）。** README 承诺 "Time limit | 30 seconds / test case"（第 54 行）。时限按墙钟时间计（`TIME_LIMIT = 30`，第 9 行），且同时运行 8 个用例（`ProcessPoolExecutor(max_workers=min(8, len(case_files)))`，第 45 行）。任务没有设定 CPU 数。在 EdgeBench 的排行榜配置 `examples/all-tasks-k8s/experiment.yaml`（引文见 [`evidence/impact/edgebench-leaderboard-config.md`](../evidence/impact/edgebench-leaderboard-config.md)）（sha256 `d9d299794ba946cae8d2b7f68a7879a35bb8565d95e78107edf79802993643be`）中，评分器继承 `judge_cpu_limit: 4`。八个用例在 4 个 CPU 上各得约半个 CPU，而且还要与任务的 Python 测试程序共享，后者每个用例需要 5.6–19.0 s 的 CPU 时间（全部 50 个用例共 579.6 s，在 1 个 CPU 上逐个用例对诚实对照解法的输出测得：`repairs/vibrating_path_graph_coloring-v2/paired/tester_time.out`）。

在原始评分器上以 `--cpus 4` 测得（`evidence/runs/vibrating_path_graph_coloring-cpu4v8-a/result/out/summary.txt`、`-b`；在 `vibrating_path_graph_coloring-v2-paired-a` 中重复）：

| 有效解法（诚实对照解法的输出，之前附加固定计算量） | 4 个 CPU | 8 个 CPU |
|---|---|---|
| 每个用例 12 或 14 s CPU | 50 OK，TOTAL 24,650,014（最慢的 14 s 用例：29.9 s） | 50 OK，TOTAL 24,650,014 |
| 每个用例 20 s CPU（在两台机器上测得） | **2 OK，48 TLE，TOTAL `inf`（无分数）** | 50 OK，TOTAL 24,650,014（100 分制下 2.06 分） |
| 计算到 25 s 墙钟截止时间 | 50 OK，TOTAL 24,650,014；每个用例 CPU 中位数 12.7 s | 50 OK，TOTAL 24,650,014；中位数 24.9 s |

在另一次 4 个 CPU 的原始评分器运行中（`evidence/runs/vibrating_path_graph_coloring-v2-paired-b`），25 s 截止时间的解法失去了 14 个用例（36 OK，14 TLE，TOTAL `inf`）。那次运行中，每个解法进程都在开始后至多 27.14 s 内结束，而全部 14 个超时用例都在测试程序最慢的 25 个用例之中。评测程序对测试程序的超时（它自己的 `timeout=60`）与解法的超时报告同样的 `TLE` 标签。因此可能的原因是测试程序在只有约半个 CPU 时达到了其 60 s 的超时。这一原因是推断的，而不是观察到的：那次运行没有记录测试程序的启动时间，而在另一个工作节点上记录了这些时间的重复运行（`vibrating_path_graph_coloring-v2-paired-c`）两次都以 50/50 通过。在原始评分器对该解法的全部九次评分中（`-b` 和 `-c` 各运行三次，后者每次运行评分两次），它只失败了这一次；在修复版下，它的全部六次评分都通过了（[可重复性](../repairs/vibrating_path_graph_coloring-v2/paired/results.md)）。

**随任务发布的说明。** 对零命中，测试程序接受两行输出，而拒绝 README 所写的、命中一行为空的三行格式。零命中的答案在 37 个官方用例上已被证明无效；其余 13 个仍未解决。同时接受两种格式可以消除格式不匹配，但这样的解析器修复不属于本修复包，也没有证明它在官方用例上给出相同的分数。

## 影响有多大

- **CPU 数。** 在发布方的 4 个 CPU 下，原始评分器会让任何每个用例使用约 14–30 s CPU 的有效解法失去全部分数（用每个用例 20 和 28 s 测得）；在修复版下，这些解法能得到分数。按截止时间停止的解法，在修复版下每个用例得到约两倍的 CPU（对 25 s 截止时间的解法，平均为 12.84 s → 24.98 s，`vibrating_path_graph_coloring-v2-paired-b`）；这会使其分数改变多少，没有测量。解题者在每次提交后能看到各用例的 TLE 结果，而一次运行会保留其最佳的有效提交，因此只有当一次运行从未提交过更快的有效解法时，它才会失去分数。
- **一个用例失败。** 全有或全无的规则不变，而且仍未披露。
- **零命中格式。** 在 37 个有证书的用例上，分数影响为零。在其余 13 个上仍未解决：一个因格式而被拒绝的有效零命中答案，会使整份提交的结果变为非有限值。目前既没有这样的官方用例见证，也没有普遍的零影响证明。

## 修复

修复版（`repairs/vibrating_path_graph_coloring-v2/`）改变了 `/tmp/eval_vibrating_path.py` 同时运行的用例数。新函数 `cpu_quota_workers()`（与 `repairs/grid_turing_robot-v2/` 中的相同）从 cgroup 读取评分器的 CPU 配额（`cpu.max`，或 cgroup v1 的配额和周期），向下取整为整数个 CPU，在没有配额时退回到 `os.cpu_count()`，并把结果限制在 1 到 8 之间。进程池变为 `ProcessPoolExecutor(max_workers=min(cpu_quota_workers(), len(case_files)))`。`docker run --cpus N` 和发布方的 k8s 后端都会设置这一配额。在 8 个或更多 CPU 下，修复版评分器同时运行 8 个用例，与原始版完全相同。

任务 JSON 改动 `judge.image_tag`，并把 `judge.eval_timeout` 从 600 提高到 900 s。每个用例独占整个 CPU 时，评分耗时更长，而本任务的测试程序很慢：对于接近 30 s 时限的有效解法，在 4 个 CPU 下最坏情况为 (50 × 30 s + 579.6 s) / 4 + 3/4 × 49 s ≈ 557 s，仅比 600 s 低 7%。修复版下测得的最长评分耗时为 558.0 s（25 s 截止时间的解法，`vibrating_path_graph_coloring-v2-paired-b`），因此 600 s 的余量太小。30 s 的时限、README、测试程序、用例、解析器和分数刻度都不变，一个用例失败即使整份提交作废的规则也不变。

在 `--cpus 4` 下（另有一组在 `--cpus 8` 下）的并排对照运行，两个评分器上使用相同的解法（`evidence/runs/vibrating_path_graph_coloring-v2-paired-a`、`-b`、`-c`，`result/out/summary.txt`；`repairs/vibrating_path_graph_coloring-v2/paired/results.md`）：

| 解法 | CPU 数 | 原始评分器 | 修复版 |
| --- | ---: | --- | --- |
| 诚实对照解法，没有额外计算 | 4 | 50 OK，TOTAL 24,650,014 (2.06) | 50 OK，TOTAL 24,650,014 (2.06) |
| **每个用例 20 s CPU** | 4 | **2 OK，48 TLE，TOTAL `inf`（无分数）** | **50 OK，TOTAL 24,650,014 (2.06)** |
| **每个用例 28 s CPU** | 4 | **2 OK，48 TLE，TOTAL `inf`（无分数）** | **50 OK，TOTAL 24,650,014 (2.06)** |
| 计算到 25 s 墙钟截止时间（作业 `-b`） | 4 | **36 OK，14 TLE，TOTAL `inf`**；每个用例平均 12.84 s CPU | 50 OK，TOTAL 24,650,014；每个用例平均 24.98 s CPU |
| 同上，另外两次原始版运行和一次修复版运行（作业 `-c`） | 4 | 50 OK，TOTAL 24,650,014（两次）；12.77 / 12.81 s CPU | 50 OK，TOTAL 24,650,014；24.92 s CPU |
| 每个用例 40 s CPU（错误对照） | 4 | 50 TLE，TOTAL `inf` | 50 TLE，TOTAL `inf` |
| 每个用例 20 s CPU | 8 | 50 OK，TOTAL 24,650,014 | 50 OK，TOTAL 24,650,014 |

在修复版下，最慢的 28 s 用例从开始到结束耗时 28.12 s。4 个 CPU 下的评分耗时为 438.4 s（每个用例 20 s）、508.6 s（每个用例 28 s），以及至多 558.0 s（25 s 截止时间），都在新的 900 s `eval_timeout` 之内。在 `--cpus 1/2/3/4/8` 下，修复版评分器分别同时运行 1/2/3/4/8 个用例（`result/out/v2_workers.txt`）。

**分数是否可比？** 在 8 个或更多评分器 CPU 下，两个版本的评分方式相同。在 4 个 CPU 下，一个在原始版下每个用例都按时完成的确定性解法，在修复版下得到相同的输出和分数；而一个每个用例需要约 14 到 30 s CPU 的解法，会得到分数而不是没有分数。一个搜索到墙钟截止时间的解法每个用例得到约两倍的 CPU，因此它在 4 个 CPU 下两个评分器的分数不可比。在修复版下，每个用例的 CPU 从不减少。

以下说明仍随修复版一起发布：

1. 对零命中，测试程序只接受两行格式，不接受 README 的三行格式。零命中的答案在 37 个官方用例上已被证明是错的；在其余 13 个上，分数影响仍未解决。
2. 一个崩溃、超时或格式错误的用例会使总分为 `inf`，因此整份提交没有分数。

## 我们如何检查

- **在 E2B 上的 CPU 运行和并排对照运行。** 每个用例做 12 到 28 s CPU 计算的有效解法、一个 25 s 墙钟截止时间的解法和一个 40 s 的错误对照，在原始评分器上以 `--cpus 4` 和 `--cpus 8` 运行（`evidence/runs/vibrating_path_graph_coloring-cpu4v8-a`、`-b`），并在原始版和修复版评分器上并排对照运行（`vibrating_path_graph_coloring-v2-paired-a`、`-b`、`-c`），每个作业都是 `status: exit=0`，在按摘要固定的评分器镜像中以 `--network none --memory 4g` 运行。每个解法先运行我们的诚实对照解法（贪心 K 着色，按随附测试程序的规则模拟命中），再做额外的计算，然后打印对照解法的答案，并记录自己在每个用例上的开始、结束时间和 CPU 时间（`result/out/timing/`）。每个用例的测试程序时间在 `--cpus 1` 下单独测量（`paired/tester_time.out`）。

- **原始评分器。** 原始测试程序和辅助程序在按摘要固定的原始公开镜像中以 `--network none` 运行。输入包括我们编写的、带两行和三行零命中输出的图，一个已知错误的着色，一个已知正确、带命中的输出，以及六个官方用例。`tools/bin/tester` 在评分器镜像和智能体工作镜像中完全相同。`tools/README.md` 是从工作镜像中读取的。
- **精确证书。** 对每个官方用例给出图无法用 K 种颜色着色的证明：K=1 时为一条边，K=2 时为一个奇环，以及逐对检查过的显式 K4 或 K5 团。
- **概率上界。** 对其余大而稀疏的用例，在已发布生成器的模型下给出闭式的联合界。

## 局限

- 修复版评分器从 cgroup（`cpu.max`）读取其 CPU 配额。这只用 `docker run --cpus` 测试过，没有在 Kubernetes pod（EdgeBench 排行榜设置所用的后端）中测试。
- 没有 cgroup 配额时，修复版评分器回退到 `os.cpu_count()`，它统计的是主机的全部 CPU，而不是评分器可以使用的 CPU（`os.sched_getaffinity`）。在只有 CPU 集合限制、没有配额的情况下（例如 `docker run --cpuset-cpus`），或者 pod 看不到自己的 `cpu.max` 时，它仍可能同时运行多于 CPU 数的用例，与原版一样。改用亲和性计数需要一次新的并排对照运行，因此这里没有改。
- 没有运行任何 AI 模型或解题者。影响只在我们编写的测试提交和反例上展示。
- 13/50 个用例依赖概率上界，并假定用例来自已发布的均匀生成器。没有找到确切的种子，也没有运行 SAT 反驳（由可满足性求解器给出的机器证明）。
- 振动路径图规则本身没有审查。
- 没有检查过去的提交。
- CPU 依赖性是在 4 和 8 个 CPU 下、在有 8 个 vCPU 的 E2B 工作节点上、用单线程的固定计算量和截止时间测试解法测量的。多线程的解题者没有测试。3、5、6 和 7 个 CPU 没有测试。
- 在 4 个 CPU 下，采用按截止时间停止策略的解题者在修复版中每个用例得到约两倍的 CPU，因此其在两个评分器下的分数不可比。其分数改变多少没有测量。
- 在一次原始评分器运行中，25 s 截止时间解法的 14 次超时的原因是推断的（测试程序在半个 CPU 下达到自己 60 s 的超时），而不是观察到的。
- 测试程序的耗时，以及据此得出的、作为 900 s `eval_timeout` 依据的 557 s 上界，针对的是诚实对照解法的输出；其他输出的检查可能耗时更长。评分器 CPU 少于 3 个时，900 s 的 `eval_timeout` 可能先于每个用例 30 s 的时限起作用（在 2 个 CPU 下约 1,065 s 的工作量）。配额是向下取整的：2.5 个 CPU 时同时运行 2 个用例。

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
