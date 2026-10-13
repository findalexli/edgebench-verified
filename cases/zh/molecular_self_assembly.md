# Molecular Self Assembly (`molecular_self_assembly`)

**结论：** 已修复。<mark>在发布方的 4-CPU 评分器上，每个用例使用超过约 15 s CPU 的有效解法会超时，尽管 README 承诺每个用例 30 s，而每个超时用例得 0 分。修复版同时运行的用例数不超过评分器的 CPU 数。README 中写明的 1 GB 内存上限仍未执行；没有发现额外内存能提高分数的途径。</mark>

## 任务要求

解题者要写一个 `solution.py`，从标准输入读取、向标准输出写入，并且 "scored on **50 fixed test cases**"（在一组固定测试用例上评分）。README 的 "Runtime Limits"（运行限制）表写明 `| Time limit | 30 seconds / test case |` 和 `| Memory limit | 1 GB |`。它没有说明所指的是哪种内存度量（常驻内存 RSS 还是地址空间）、哪种单位（10^9 字节还是 GiB），也没有说明超出上限会怎样。类别：组合优化。

## 问题出在哪里

**每个解法 1 GB 的上限没有执行（说明）。** 辅助函数 `run_case` 以 30 s 超时启动 `python3 solution.py`，没有设置任何内存上限。默认情况下，最多 8 个用例同时运行。任务 JSON 没有设置内存上限。已发布的排行榜配置为整个评分器容器设置了 `judge_mem_limit: "8g"` 和 `judge_cpu_limit: 4`。这一上限由最多 8 个同时运行的解法进程及其测试程序共享。

在原始评分器下、全部 50 个官方用例上的结果。测试解法分配 N MiB 内存并实际访问它，然后输出基线结果。OK 表示用例正常评分；RE 表示运行时错误。

| 运行 | 分配的内存 | 同时运行的用例数 | 每个用例的峰值 RSS | 结果 |
|---|---|---|---|---|
| R1（正确的测试提交） | 0 | 1 | 12.6 MB | 50/50 OK，TOTAL 69,280,072 |
| R2（展示问题） | 1300 MiB | 1 | 1,370,013,696 到 1,370,697,728 B（> 10^9 且 > 2^30） | **50/50 OK，TOTAL 69,280,072**（完全相同） |
| R4（低于上限，按比例缩小） | 700 MiB | 2 | 0.74 GB | 50/50 OK，69,280,072 |
| R3（容器上限按比例缩小，2 GiB / 2 个用例 ≈ 官方的 8 GiB / 8） | 1300 MiB | 2 | 1.37 GB | **46/50 OK，4 RE（因内存不足被终止），TOTAL 63,747,304** |

- **预期与实际（R2）。** 一个在每个用例上都使用约 1.37 GB RSS 的解法，在 1 GB 上限下应被拒绝或扣分。实际上它在全部 50 个用例上都拿到了全部分数，总分与正确的测试提交相同。
- **容器上限的作用（R3）。** 它对一个在每个用例上都超限的解法做了部分惩罚：在这一次运行中失去了 50 个用例中的 4 个。预计失去哪些用例取决于计时。这不是每个解法的上限。

**在 4-CPU 评分器上，每个用例 30 s 缩水为约 15 s CPU（已修复）。** 30 s 时限是墙钟时间，最多 8 个用例同时运行（`eval_molecules.py`：`TIME_LIMIT = 30`，`SEBENCH_MOLECULES_WORKERS` 默认为 8）。任务没有设置 `cpu_limit`。在 EdgeBench 的排行榜配置 `examples/all-tasks-k8s/experiment.yaml` 中（引用见 [`evidence/impact/edgebench-leaderboard-config.md`](../evidence/impact/edgebench-leaderboard-config.md)）（sha256 `d9d299794ba946cae8d2b7f68a7879a35bb8565d95e78107edf79802993643be`，标题为 "OFFICIAL EDGEBENCH LEADERBOARD SETTING"），评分器得到 `judge_cpu_limit: 4`，因此 8 个运行中的用例每个约分到半个 CPU。这样一来，每个用例需要超过约 15 s CPU 的单线程解法就会超时，而超时的用例得 0 分，提交仍然有效（与 R3 中 RE 用例的路径相同）。

在原始评分器上、全部 50 个官方用例上测量（`evidence/runs/molecular_self_assembly-cpu4v8/result/out/summary.txt`，在 `molecular_self_assembly-v2-paired` 中重复）。每个测试解法都是随附基线，之前先做固定量的工作：

| 随附基线之前的工作 | 4 个 CPU | 8 个 CPU |
|---|---|---|
| 每个用例 12 s CPU | 50 OK，TOTAL 69,280,072 | 50 OK，TOTAL 69,280,072 |
| 每个用例 16、20 或 28 s CPU | **2 OK，48 TLE，TOTAL 2,849,909（得 0 分）** | 50 OK，TOTAL 69,280,072 |
| 工作到 25 s 墙钟截止时间 | 50 OK，TOTAL 69,280,072；每个用例平均 13.01 s CPU | 未运行 |

一个搜索到墙钟截止时间为止的解法，得到的计算量约为每个用例独占一个 CPU 时的一半（每个用例的 CPU：`molecular_self_assembly-v2-paired/result/out/timing/c4-wall25-v1/`）。

随修复版发布的说明：README 中 1 GB 的内存数字只应视为建议。内存只受评分器容器的限制：在已发布的设置中，是 8 个同时运行的用例共享 8 GiB。这一上限会以无法预测的方式惩罚每个用例都占用大量内存的解法。没有发现额外内存能提高分数的证据。

## 影响有多大

内存：没有发现能借此提高分数的途径。该任务是纯 Python 的（评分器镜像中没有 numpy），每个用例时限 30 s。一张随时间变化的完整两两距离表大约只占 180 MB，远在内存耗尽之前就会碰到时限。隐藏用例对解法不可见。这一结论是推理得出的，没有测量。问题在于缺少拒绝，因此它永远不会拒绝有效的提交。只有使用超过所述上限的解法才受影响，而容器上限可能以无法预测的方式惩罚它们。

CPU 数：在原始评分器下、4 个 CPU 时，每个用例使用超过约 15 s CPU 的解法会失去每一个这样的用例（每个 0 分；在下文的真实运行中，每个用例约值 650 万分，而总分约为 3.26 亿分）；失去 50 个用例中的 48 个几乎等于失去全部分数。在修复版下，这些用例会被正常评分。对于在墙钟截止时间停止的解法，分数取决于用半个 CPU 能达到的搜索质量；在修复版下，这样的解题者每个用例得到的 CPU 约为原来的两倍（25 s 对照解法的平均值从 13.01 s → 24.91 s）；这对其分数的影响没有测量。一次第三方 Claude Opus 5.5 运行（4 小时，以 `adafadaq/edgebench-opus-5-5-xhigh-rollouts` 发布在 Hugging Face 上）在这个评分器上、评分器有 4 个 CPU 时（`run_config.json`：`"judge_cpu_limit": 4`），全部 13 份提交都有效，50/50 用例 OK。其最佳提交（agent-6）总分为 326,392,210，高于 100 分的参考点（322,991,707.7），因此得 100 分。它的评分用了 178.7 s（`report.json` 的 `runtime_seconds`），约为 7 轮、每轮 8 个用例、每轮 25.5 s，这与一个每个用例在约 25 s 截止时间停止的解法应有的表现相符；其源码没有检查。它的最佳提交已经得 100 分，因此对这次运行而言，修复版只会改变采用按截止时间停止策略的解题者每个用例可用的 CPU。

## 修复

修复版（`repairs/molecular_self_assembly-v2/`）改变了评分器 `/tmp/eval_molecules.py` 同时运行的用例数。新函数 `cpu_quota_workers()` 从 cgroup 读取评分器的 CPU 配额（`cpu.max`，或 cgroup v1 的 quota 和 period），向下取整为整数个 CPU，没有配额时退回到 `os.cpu_count()`，并把结果限制在 1 到 8 之间。进程池大小变为 `min(SEBENCH_MOLECULES_WORKERS or 8, cpu_quota_workers(), len(case_files))`。在 `--cpus 1/2/4/8` 下，修复版评分器分别同时运行 1/2/4/8 个用例（`molecular_self_assembly-v2-paired/result/out/v2_workers.txt`）。任务 JSON 只改动 `judge.image_tag`。30 s 时限、README、测试程序、用例和分数刻度都没有改变。在 8 个或更多 CPU 下，修复版评分器同时运行 8 个用例，与原版完全相同。上述内存说明仍随修复版发布。

在 `--cpus 4` 下的并排对照测试（另有一组在 `--cpus 8` 下），两个评分器使用相同的解法（`evidence/runs/molecular_self_assembly-v2-paired/result/out/summary.txt`；`repairs/molecular_self_assembly-v2/paired/results.md`）：

| 解法 | CPU 数 | 原始评分器 | 修复版 |
| --- | ---: | --- | --- |
| 随附基线，无额外工作 | 4 | 50 OK，TOTAL 69,280,072 | 50 OK，TOTAL 69,280,072 |
| 每个用例 12 s CPU | 4 | 50 OK，TOTAL 69,280,072 | 50 OK，TOTAL 69,280,072 |
| **每个用例 16 s CPU** | 4 | **2 OK，48 TLE，TOTAL 2,849,909（得 0 分）** | **50 OK，TOTAL 69,280,072** |
| **每个用例 28 s CPU** | 4 | **2 OK，48 TLE，TOTAL 2,849,909（得 0 分）** | **50 OK，TOTAL 69,280,072** |
| 工作到 25 s 墙钟截止时间 | 4 | 50 OK，TOTAL 69,280,072；每个用例平均 13.01 s CPU | 50 OK，TOTAL 69,280,072；每个用例平均 24.91 s CPU |
| 每个用例 40 s CPU（坏对照） | 4 | 50 TLE，TOTAL 0 | 50 TLE，TOTAL 0 |
| 每个用例 20 s CPU | 8 | 50 OK，TOTAL 69,280,072 | 50 OK，TOTAL 69,280,072 |

这些对照解法建立在随附基线之上，因此它们自身的 100 分制得分接近 0（69,280,072 → 0.0133；2,849,909 → 0；`sforge/harness/score_rescale.py`）。对一个强解法而言，失去 50 个用例中的 48 个几乎等于失去全部分数。在修复版下，最慢的 28 s 用例从开始到结束用了 29.08 s（`result/out/timing/c4-cpu28-v2/`），距时限不到 1 s。在 4 个 CPU 下评分最多需要 ⌈50/4⌉ = 13 轮、每轮 30 s；坏对照用了 390.9 s（原版：210.8 s），在任务 600 s 的 `eval_timeout` 之内。

**分数是否可比？** 在评分器有 8 个或更多 CPU 时，两个版本就是同一个评分器。在 4 个 CPU 下，一个确定性解法如果在原版下每个用例都按时完成，在修复版下得到相同的输出和分数；而需要约 15 到 30 s CPU 的用例会被正常评分，而不是得 0 分。搜索到墙钟截止时间为止的解法，每个用例得到的 CPU 约为原来的两倍，因此它在两个评分器下的分数不可比。在修复版下，每个用例的 CPU 从不减少。

可以在另一个单独的、带新版本号的变体中加入每个解法的内存上限，使用 `RLIMIT_AS`（地址空间上限）或在运行后检查峰值 RSS。其分数不得与原版的分数合并。一个多线程的纯 Python 程序（1 到 64 个线程）在 `RLIMIT_AS=1e9` 下成功运行，RSS 约为 11 MB，因此地址空间上限不会错误地拒绝这类程序。

## 我们如何检查

- **原始镜像中的原始评分器，按摘要固定。** 原始辅助函数在评分器镜像中、在全部 50 个官方用例上运行，参数为 `--network none --memory 2g --memory-swap 2g --cpus 2`，得到上表。
- **源码和配置。** 阅读了辅助函数、任务 JSON 和已发布的排行榜配置，以确定内存在哪里受限、在哪里不受限。
- **在 E2B 上的 CPU 运行和并排对照测试。** 随附基线之前先做每个用例 12 到 28 s 的 CPU 工作、工作到 25 s 墙钟截止时间，或做 40 s 的工作（坏对照），在原始评分器上以 `--cpus 4` 和 `--cpus 8` 运行（`evidence/runs/molecular_self_assembly-cpu4v8`），并在原始评分器和修复版评分器上做了并排对照运行（`evidence/runs/molecular_self_assembly-v2-paired`），每个作业都是 `status: exit=0`。每个解法记录每个用例自己的开始时间、结束时间和 CPU 时间（`result/out/timing/`），这不影响评分。解法文件包含随附基线，没有存放在仓库中；它们的制作方式见每个作业的 `sol/README.md`。

## 局限

- 修复版评分器从 cgroup（`cpu.max`）读取 CPU 配额。这只用 `docker run --cpus` 测试过，没有在 Kubernetes pod 中测试，而 EdgeBench 的排行榜设置使用的正是这个后端。
- 我们没有运行任何 AI 模型或解题者。影响在我们编写的测试提交和反例上展示，上述第三方运行也在 4 个 CPU 下重新评分：其 13 个提交中的 8 个，在修复版下原始结果各高 3–4%，而这次运行的得分仍为 100，因为它原本就已超过分数刻度的顶端（`evidence/runs/opus55-regrade2-summary/summary.json`）。没有估计对排行榜的影响。
- 对 CPU 的依赖是在 4 个和 8 个 CPU 下、用单线程测试解法测量的；没有测试多线程的解题者，也没有测试 3、5、6 和 7 个 CPU。
- 在 4 个 CPU 下，修复版给每个用例使用 28 s CPU 的解法留下的余量不到 1 s（最慢的用例 29.08 s），因此算上解释器启动时间，可用的预算略低于 30 s CPU。
- 采用按截止时间停止策略的解题者在 4 个 CPU 下、在修复版中每个用例得到的 CPU 约为原来的两倍，因此它们在两个评分器下的分数不可比。其分数变化多少没有测量。
- 当评分器 CPU 少于 3 个时，600 s 的 `eval_timeout` 会先于每个用例 30 s 的时限起约束作用：在 2 个 CPU 下为 25 轮 × 30 s = 750 s，因此每个用例实际只能用约 24 s（原版在这种情况下每个用例约给 7.5 s CPU）。配额向下取整：2.5 个 CPU 时同时运行 2 个用例。
- 内存运行使用的是 2 GiB 容器、同时运行 1 到 2 个用例，而不是官方的 8 GiB、同时 8 个用例、4 个 CPU 的设置。R3 通过按比例缩放来模拟官方设置，而它因内存失去多少用例取决于计时。
- 每种内存配置只运行了一次。R3 没有可重复性统计。原始评分器的 CPU 行运行了四次（`molecular_self_assembly-cpu4v8` 一次，`-v2-paired` 及 `-rep2` 和 `-rep3`），计数和总分都相同。
- 过去部署时的覆盖设置不得而知，因此不能排除过去使用过不同的内存策略。
- "额外内存没有好处"这一结论是推理，而不是测量的实验。没有构建任何强解题者。

## 复现

- 原始评分器镜像：`sha256:8afd932de7e5…`。
- 修复版：`repairs/molecular_self_assembly-v2/`（`materialize.sh`、`repair.patch`、`source-lock.json`；修复版评分器 sha256 `1cf8f71d…9ef0`）。并排对照测试：`repairs/molecular_self_assembly-v2/paired/run.sh`（实际运行的版本：`evidence/runs/molecular_self_assembly-v2-paired/run.sh`）；原始评分器上的 CPU 运行：`evidence/runs/molecular_self_assembly-cpu4v8/run.sh`。
- 在全部 50 个官方用例上的内存探测：`evidence/scripts/molecular_self_assembly/run_memory_probe.sh <MiB> <workers>`，配合 `hog_solution.py`。输出为 `r1_base_w1.out`、`r2_hog1300_w1.out`、`r3_hog1300_w2.out` 和 `r4_hog700_w2.out`。
- RLIMIT_AS 线程探测：`evidence/scripts/molecular_self_assembly/as_limit_threads_probe.py`，输出在 `as_limit_threads_probe.out`。
- 第三方运行：`evidence/runs/opus55-rollouts-meta/result/meta/opus-16x4h-1009-0036-w4/molecular_self_assembly/`（`final_result.json`、`run_config.json`、`submissions/*/report.json`）。
- 支撑记录：`evidence/reviews/molecular_self_assembly.md`。
