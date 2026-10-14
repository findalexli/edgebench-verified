# Molecular Self Assembly (`molecular_self_assembly`)

**结论：** 已修复。<mark>README 承诺每个用例 30 s，但在发布方的 4-CPU 评分器上，每个用例用掉超过约 15 s CPU 的有效解法会超时，超时的用例得 0 分。修复版同时运行的用例数不超过评分器的 CPU 数。README 写明的 1 GB 内存上限仍然没有执行；我们没有发现多用内存能提高分数的办法。</mark>

## 任务要求

解题者要写一个 `solution.py`，从标准输入读取、向标准输出写入，并且 "scored on **50 fixed test cases**"（在一组固定测试用例上评分）。README 的 "Runtime Limits"（运行限制）表写明 `| Time limit | 30 seconds / test case |` 和 `| Memory limit | 1 GB |`。它没有说明指的是哪种内存度量（常驻内存 RSS 还是地址空间）、用哪种单位（10^9 字节还是 GiB），也没有说超出上限会怎样。类别：组合优化。

## 问题出在哪里

评分器没有执行每个解法 1 GB 的上限，我们把这一点作为说明。辅助函数 `run_case` 以 30 s 超时启动 `python3 solution.py`，没有设任何内存上限。默认最多同时运行 8 个用例。任务 JSON 没有设内存上限。已发布的排行榜配置给整个评分器容器设了 `judge_mem_limit: "8g"` 和 `judge_cpu_limit: 4`，最多 8 个同时运行的解法进程及其测试程序共用这一上限。

下面是原始评分器在全部 50 个官方用例上的结果。测试解法分配 N MiB 内存并实际访问，然后输出基线结果。OK 表示用例正常评分；RE 表示运行时错误。

| 运行 | 分配的内存 | 同时运行的用例数 | 每个用例的峰值 RSS | 结果 |
|---|---|---|---|---|
| R1（正确的测试提交） | 0 | 1 | 12.6 MB | 50/50 OK，TOTAL 69,280,072 |
| R2（展示问题） | 1300 MiB | 1 | 1,370,013,696 到 1,370,697,728 B（> 10^9 且 > 2^30） | **50/50 OK，TOTAL 69,280,072**（完全相同） |
| R4（低于上限，按比例缩小） | 700 MiB | 2 | 0.74 GB | 50/50 OK，69,280,072 |
| R3（容器上限按比例缩小，2 GiB / 2 个用例 ≈ 官方的 8 GiB / 8） | 1300 MiB | 2 | 1.37 GB | **46/50 OK，4 RE（因内存不足被终止），TOTAL 63,747,304** |

- 在 R2 中，一个每个用例都用约 1.37 GB RSS 的解法，在 1 GB 上限下本应遭到拒绝或扣分，它却在全部 50 个用例上都拿了满分，总分与正确的测试提交相同。
- R3 表明，容器上限对一个每个用例都超限的解法做了部分惩罚，这次运行丢了 50 个用例中的 4 个。丢哪几个，预计取决于计时。这不是针对每个解法的上限。

在 4-CPU 评分器上，每个用例的 30 s 缩水为约 15 s CPU，修复版去掉了这个问题。30 s 时限按墙钟时间计，最多同时运行 8 个用例（`eval_molecules.py`：`TIME_LIMIT = 30`，`SEBENCH_MOLECULES_WORKERS` 默认为 8）。任务没有设 `cpu_limit`。在 EdgeBench 的排行榜配置 `examples/all-tasks-k8s/experiment.yaml` 中（引用见 [`evidence/impact/edgebench-leaderboard-config.md`](../evidence/impact/edgebench-leaderboard-config.md)）（sha256 `d9d299794ba946cae8d2b7f68a7879a35bb8565d95e78107edf79802993643be`，标题为 "OFFICIAL EDGEBENCH LEADERBOARD SETTING"），评分器得到 `judge_cpu_limit: 4`，所以 8 个同时运行的用例每个大约分到半个 CPU。这样一来，单线程解法只要每个用例需要超过约 15 s CPU 就会超时；超时的用例得 0 分，提交仍算有效（与 R3 中 RE 用例走的路径相同）。

我们在原始评分器上、用全部 50 个官方用例测量（`evidence/runs/molecular_self_assembly-cpu4v8/result/out/summary.txt`，在 `molecular_self_assembly-v2-paired` 中重复）。每个测试解法都是先做固定量的工作，再运行随附基线：

| 随附基线之前的工作 | 4 个 CPU | 8 个 CPU |
|---|---|---|
| 每个用例 12 s CPU | 50 OK，TOTAL 69,280,072 | 50 OK，TOTAL 69,280,072 |
| 每个用例 16、20 或 28 s CPU | **2 OK，48 TLE，TOTAL 2,849,909（得 0 分）** | 50 OK，TOTAL 69,280,072 |
| 工作到 25 s 墙钟截止时间 | 50 OK，TOTAL 69,280,072；每个用例平均 13.01 s CPU | 未运行 |

一直搜索到墙钟截止时间的解法，得到的计算量约为每个用例独占一个 CPU 时的一半（每个用例的 CPU：`molecular_self_assembly-v2-paired/result/out/timing/c4-wall25-v1/`）。

修复版附带一条说明，即 README 中 1 GB 的内存数字只能当作建议。内存只受评分器容器的限制，在已发布的设置中是 8 个同时运行的用例共用 8 GiB。每个用例都占大量内存的解法，会受到这一上限无法预测的惩罚。没有证据表明多用内存能提高分数。

## 影响有多大

内存方面，我们没有发现能借此提高分数的办法。这个任务是纯 Python 的（评分器镜像中没有 numpy），每个用例时限 30 s。一张随时间变化的完整两两距离表也只占约 180 MB，内存远没用完，时限就先到了。解法看不到隐藏用例。这一结论是推理得出的，没有测量。问题在于评分器不拒绝超限的解法，所以它永远不会错误地拒绝有效提交。只有用量超过所述上限的解法受影响，而容器上限可能以无法预测的方式惩罚它们。

CPU 数方面，在原始评分器下、4 个 CPU 时，解法在每个用掉超过约 15 s CPU 的用例上都会丢分（每个 0 分；在下文的真实运行中，每个用例约值 650 万分，总分约 3.26 亿分）；丢掉 50 个用例中的 48 个，几乎就是丢掉全部分数。修复版会正常给这些用例评分。在墙钟截止时间停止的解法，分数取决于用半个 CPU 能搜到多好；在修复版下，这样的解题者每个用例分到的 CPU 约为原来的两倍（25 s 对照解法的平均值从 13.01 s → 24.91 s），我们没有测量这对分数的影响。一次第三方 Claude Opus 5.5 运行（4 小时，以 `adafadaq/edgebench-opus-5-5-xhigh-rollouts` 发布在 Hugging Face 上）在这个评分器上、评分器有 4 个 CPU 时（`run_config.json`：`"judge_cpu_limit": 4`），13 份提交全部有效，50/50 用例 OK。最佳提交（agent-6）总分为 326,392,210，高于 100 分的参考点（322,991,707.7），所以得 100 分。它评分用了 178.7 s（`report.json` 的 `runtime_seconds`），约合 7 轮、每轮 8 个用例、每轮 25.5 s，与每个用例在约 25 s 截止时间停止的解法相符；它的源码我们没有检查。它的最佳提交已经是 100 分，所以对这次运行来说，修复版只会改变截止时间策略的解题者每个用例能用的 CPU。

## 修复

修复版（`repairs/molecular_self_assembly-v2/`）改变了评分器 `/tmp/eval_molecules.py` 同时运行的用例数。新函数 `cpu_quota_workers()` 从 cgroup 读取评分器的 CPU 配额（`cpu.max`，或 cgroup v1 的 quota 和 period），向下取整为整数个 CPU，没有配额时退回到 `os.cpu_count()`，并把结果限制在 1 到 8 之间。进程池大小改为 `min(SEBENCH_MOLECULES_WORKERS or 8, cpu_quota_workers(), len(case_files))`。在 `--cpus 1/2/4/8` 下，修复版评分器分别同时运行 1/2/4/8 个用例（`molecular_self_assembly-v2-paired/result/out/v2_workers.txt`）。任务 JSON 只改了 `judge.image_tag`。30 s 时限、README、测试程序、用例和分数刻度都没有变。在 8 个或更多 CPU 下，修复版评分器同时运行 8 个用例，与原版完全相同。修复版仍附带上述内存说明。

我们在 `--cpus 4` 下做了并排对照测试（另有一组在 `--cpus 8` 下），两个评分器用相同的解法（`evidence/runs/molecular_self_assembly-v2-paired/result/out/summary.txt`；`repairs/molecular_self_assembly-v2/paired/results.md`）。

| 解法 | CPU 数 | 原始评分器 | 修复版 |
| --- | ---: | --- | --- |
| 随附基线，无额外工作 | 4 | 50 OK，TOTAL 69,280,072 | 50 OK，TOTAL 69,280,072 |
| 每个用例 12 s CPU | 4 | 50 OK，TOTAL 69,280,072 | 50 OK，TOTAL 69,280,072 |
| **每个用例 16 s CPU** | 4 | **2 OK，48 TLE，TOTAL 2,849,909（得 0 分）** | **50 OK，TOTAL 69,280,072** |
| **每个用例 28 s CPU** | 4 | **2 OK，48 TLE，TOTAL 2,849,909（得 0 分）** | **50 OK，TOTAL 69,280,072** |
| 工作到 25 s 墙钟截止时间 | 4 | 50 OK，TOTAL 69,280,072；每个用例平均 13.01 s CPU | 50 OK，TOTAL 69,280,072；每个用例平均 24.91 s CPU |
| 每个用例 40 s CPU（坏对照） | 4 | 50 TLE，TOTAL 0 | 50 TLE，TOTAL 0 |
| 每个用例 20 s CPU | 8 | 50 OK，TOTAL 69,280,072 | 50 OK，TOTAL 69,280,072 |

这些对照解法以随附基线为基础，所以它们本身的 100 分制得分接近 0（69,280,072 → 0.0133；2,849,909 → 0；`sforge/harness/score_rescale.py`）。对强解法来说，丢掉 50 个用例中的 48 个，几乎就是丢掉全部分数。在修复版下，最慢的 28 s 用例从开始到结束用了 29.08 s（`result/out/timing/c4-cpu28-v2/`），离时限不到 1 s。4 个 CPU 时，评分最多需要 ⌈50/4⌉ = 13 轮，每轮 30 s；坏对照用了 390.9 s（原版：210.8 s），没有超过任务 600 s 的 `eval_timeout`。

评分器有 8 个或更多 CPU 时，两个版本就是同一个评分器，分数可以比较。在 4 个 CPU 下，一个确定性的解法如果在原版下每个用例都按时完成，在修复版下输出和分数都不变；需要约 15 到 30 s CPU 的用例，在修复版下会正常评分，不再是 0 分。一直搜索到墙钟截止时间的解法，每个用例得到的 CPU 约为原来的两倍，所以它在两个评分器下的分数不能比较。修复版不会减少任何用例的 CPU。

每个解法的内存上限可以放进另一个带新版本号的变体，用 `RLIMIT_AS`（地址空间上限）或在运行后检查峰值 RSS 来实现，其分数不能与原版合并。一个多线程的纯 Python 程序（1 到 64 个线程）在 `RLIMIT_AS=1e9` 下运行成功，RSS 约 11 MB，可见地址空间上限不会错误地拒绝这类程序。

## 我们如何检查

- 原始评分器来自按摘要固定的原始镜像。我们在评分器镜像中用全部 50 个官方用例运行原始辅助函数，参数为 `--network none --memory 2g --memory-swap 2g --cpus 2`，得到上表。
- 我们读了辅助函数、任务 JSON 和已发布的排行榜配置，弄清内存在哪里受限、在哪里不受限。
- 我们在 E2B 上做了 CPU 运行和并排对照测试。测试解法在运行随附基线之前，先做每个用例 12 到 28 s 的 CPU 工作、工作到 25 s 墙钟截止时间，或做 40 s 的工作（坏对照）。它们先在原始评分器上用 `--cpus 4` 和 `--cpus 8` 运行（`evidence/runs/molecular_self_assembly-cpu4v8`），再在原始评分器和修复版评分器上并排对照运行（`evidence/runs/molecular_self_assembly-v2-paired`），每个作业都是 `status: exit=0`。每个解法记录每个用例自己的开始时间、结束时间和 CPU 时间（`result/out/timing/`），不影响评分。解法文件包含随附基线，没有放进仓库；制作方法见每个作业的 `sol/README.md`。

## 局限

- 修复版评分器从 cgroup（`cpu.max`）读取 CPU 配额。我们只用 `docker run --cpus` 测试过，没有在 Kubernetes pod 中测试，而 EdgeBench 的排行榜设置用的正是这个后端。
- 没有 cgroup 配额时，修复版评分器回退到 `os.cpu_count()`。它统计的是主机的全部 CPU，而不是评分器能用的 CPU（`os.sched_getaffinity`）。如果只限制了 CPU 集合、没有配额（例如 `docker run --cpuset-cpus`），或者 pod 看不到自己的 `cpu.max`，它仍可能同时运行比 CPU 数更多的用例，与原版一样。改用亲和性计数需要重新做一次并排对照运行，所以这里没有改。
- 我们没有运行任何 AI 模型或解题者。影响在我们写的测试提交和反例上展示；上述第三方运行也在 4 个 CPU 下重新评了分：13 个提交中有 8 个在修复版下原始结果各高 3–4%，这次运行的得分仍是 100，因为它本来就已超过分数刻度的顶端（`evidence/runs/opus55-regrade2-summary/summary.json`）。我们没有估计对排行榜的影响。
- 对 CPU 的依赖是在 4 个和 8 个 CPU 下、用单线程测试解法测的；没有测试多线程的解题者，也没有测试 3、5、6 和 7 个 CPU。
- 在 4 个 CPU 下，每个用例用 28 s CPU 的解法在修复版下只剩不到 1 s 余量（最慢的用例 29.08 s），所以算上解释器启动时间，可用的预算略低于 30 s CPU。
- 采用截止时间策略的解题者，在 4 个 CPU 下、在修复版中每个用例得到的 CPU 约为原来的两倍，所以它们在两个评分器下的分数不能比较。我们没有测量分数会变化多少。
- 评分器 CPU 少于 3 个时，600 s 的 `eval_timeout` 会比每个用例 30 s 的时限先起作用：在 2 个 CPU 下为 25 轮 × 30 s = 750 s，因此每个用例实际只能用约 24 s（原版在这种情况下每个用例约给 7.5 s CPU）。配额向下取整：2.5 个 CPU 时同时运行 2 个用例。
- 内存运行用的是 2 GiB 容器、同时运行 1 到 2 个用例，不是官方的 8 GiB、同时 8 个用例、4 个 CPU 的设置。R3 按比例缩小来模拟官方设置，它因内存丢掉多少用例取决于计时。
- 我们每种内存配置只跑了一次，R3 没有可重复性统计。原始评分器的 CPU 行跑了四次（`molecular_self_assembly-cpu4v8` 一次，`-v2-paired` 及 `-rep2` 和 `-rep3`），计数和总分都相同。
- 我们不知道过去部署时有没有另行设置，所以不能排除过去用过不同的内存策略。
- "多用内存没有好处"这一结论来自推理，不是实验测量。我们没有构建强解题者。

## 复现

- 原始评分器镜像：`sha256:8afd932de7e5…`。
- 修复版：`repairs/molecular_self_assembly-v2/`（`materialize.sh`、`repair.patch`、`source-lock.json`；修复版评分器 sha256 `1cf8f71d…9ef0`）。并排对照测试：`repairs/molecular_self_assembly-v2/paired/run.sh`（实际运行的版本：`evidence/runs/molecular_self_assembly-v2-paired/run.sh`）；原始评分器上的 CPU 运行：`evidence/runs/molecular_self_assembly-cpu4v8/run.sh`。
- 在全部 50 个官方用例上的内存探测：`evidence/scripts/molecular_self_assembly/run_memory_probe.sh <MiB> <workers>`，配合 `hog_solution.py`。输出为 `r1_base_w1.out`、`r2_hog1300_w1.out`、`r3_hog1300_w2.out` 和 `r4_hog700_w2.out`。
- RLIMIT_AS 线程探测：`evidence/scripts/molecular_self_assembly/as_limit_threads_probe.py`，输出在 `as_limit_threads_probe.out`。
- 第三方运行：`evidence/runs/opus55-rollouts-meta/result/meta/opus-16x4h-1009-0036-w4/molecular_self_assembly/`（`final_result.json`、`run_config.json`、`submissions/*/report.json`）。
- 支撑记录：`evidence/reviews/molecular_self_assembly.md`。
