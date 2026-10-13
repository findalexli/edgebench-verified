# DCSS Dungeon Crawl Stone Soup AI (`dcss_dungeon_ai`)

**结论：** 保留（附说明）。<mark>在正常运行中，分数与任务承诺的一致；没有游戏结束记录的一局计为 0 分，与任务暗示的一致；说明涉及对墙钟速度的依赖，以及一个未经核实的最高参考点。</mark>

## 任务要求

解题者要用 Lua（一种脚本语言）为 DCSS 0.28，即地牢游戏 Dungeon Crawl Stone Soup，编写一个机器人程序。机器人的评分方式为 "5 hidden seeds, **900s game budget per game**, mean score across all 5 games"（使用隐藏种子，每局有固定的游戏时间预算，取全部各局的平均分）。各局并行运行，评分器在截止时间强制退出。任务说明写道 `Pass rate` "is a validity check, not the quality metric"（是有效性检查，而不是质量指标），并承认 "Wall-clock/PTTY scheduling can still create small score noise"（墙钟/PTTY 调度仍可能造成小的分数噪声）。类别：交互式游戏与模拟器。

## 我们检查了什么

正常运行中不存在问题。经检查是正确的：每局的分数是其 morgue 文件（游戏的结束记录）第 5 行上的整数。如果 morgue 中出现 wizard 或 explore 模式，该局按没有 morgue 的一局处理（`eval_dcss.py:84-85`、`:164-166`）：得 0 分，评分器把提交标为 `valid: false`，而 EdgeBench 的选取规则不读取这一标志（见第一条说明）。总分是 5 局的平均值，四舍五入到 0.1。它按 `100*log1p(raw/400)/log1p(125)` 换算为 0–100 分。代码与任务说明一致：5 个种子、`TIMEOUT=900`、5 局并行，以及退出序列。

| 原始平均分（换算到 0–100 之前） | 100 分制得分 |
|---|---|
| 0（闲置的机器人） | 0 |
| 12.4（五局：2、21、18、7、14） | 0.63 |
| 400 | 14.3 |
| 5,000 | 53.8 |
| 20,000 | 81.3 |
| 50,000 | 100 |

正常路径每局最多约 948 s。带硬超时的路径最多约 1008 s。两者都在评分器的时限 `eval_timeout` 1100 之内。

说明事项：

- **没有 morgue 的一局计为 0 分，与任务说明的暗示一致（不是缺陷）。** 任务说明把分数描述为全部 5 局的平均值。如果一局没有写出 morgue（例如强制退出序列两次失败），得 0 分，评分器把全部 5 局的平均值作为分数输出，同时输出 `"valid": ok == total`（`eval_dcss.py:210-221`）。EdgeBench 的评测框架保留这个分数：`_grade_structured` 照抄它，任务的 `score_first` 选取规则不读取 `valid`（`sforge/harness/grading.py:200-217`、`sforge/harness/selection.py:83-103`，EdgeBench 版本 `6e4e5f4`）。处于 wizard 或 explore 模式的一局也按同样方式处理。这一结论来自源码，并把评分器的输出格式离线送入评测框架做过验证；这条路径没有在真实运行中观察到。
- **对墙钟和主机速度的依赖。** 种子是固定的，但分数大致等于回合速度 × 900 s。回合速度取决于同时运行的五个游戏进程分到的 CPU。任务 JSON 没有设置 CPU 上限；发布方的排行榜设置（`examples/all-tasks-k8s/experiment.yaml`（引用见 [`evidence/impact/edgebench-leaderboard-config.md`](../evidence/impact/edgebench-leaderboard-config.md)），sha256 `d9d29979…43be`）给评分器 4 个 CPU 来运行这五局。评分器在游戏过程中还每隔 1.5 s 墙钟时间发送一次空格、CR 和 Esc，这是一个依赖于计时的输入流。任务说明承认存在 "small score noise"（小的分数噪声），但其大小没有测量。
- **最高参考点没有核实。** 原始平均分 50,000（100 分的参考点）能否在 900 s 内达到，没有核实。没有任何强机器人的运行记录。随任务提供的基线机器人得分基本为 0。

说明的内容是：
- 分数取决于墙钟速度和 CPU 分配；运行间波动没有测量。
- 100 分对应的参考点 50,000 尚未证明可以达到。

任务没有修改；上述说明随任务一起发布。

## 影响有多大

- 缺少 morgue：没有影响；该局在平均值中计为 0，与任务说明的暗示一致。
- 对墙钟速度的依赖：影响每个解题者；其大小没有测量。已发布的 12 小时结果为 8.3、13.4、6.1、7.6 和 5.7 分（满分 100）（`tasks/README.md`，dcss 行）；分别相差 0.4 分和 0.7 分的两对结果，其先后次序可能被这种量级的噪声颠倒。在局限中所述的重复运行完成之前，这一结论是暂定的。

## 我们如何检查

- **原始评分器的源码。** 我们阅读了固定版本的评分器 `eval_dcss.py`（sha256 `101e8858…2218`）以及 EdgeBench 的评分和选取代码（`grading.py`、`selection.py`，版本 `6e4e5f4`）。评分器镜像的摘要 没有记录，所阅读的 `eval_dcss.py` 副本也没有在本仓库中发布，因此所引用的行只能对照评分器镜像核对。
- **精确算术**：评分器的休眠时间表与 `eval_timeout` 1100 的对照，以及 `log1p_max` 分数换算。
- **在评分器上的运行。** 一个闲置的机器人在总计 962 s 内得 0 分。一个有进展的机器人的一次五局运行得到 2、21、18、7、14（平均 12.4）。

## 局限

- 没有运行任何 AI 模型或解题者。影响只在闲置运行和有进展的运行上展示。
- 缺少 morgue 的路径是根据源码推理的，没有实际触发。
- 只有一次得分为正的五局运行，没有重复。能解决噪声问题的检查没有进行：在固定分配的至少 5 个核上把同一机器人运行两次，再在一半核数上运行一次。如果波动与不同机器人之间的差距相当，结论将改为修复或撤下该任务。

## 复现

- 审查记录：`evidence/reviews/_game-tasks-correctness.md`，第 4 节。
- 固定版本的评分器副本：评分器镜像中的文件 `eval_dcss.py`（sha256 见[审查记录](../evidence/reviews/_game-tasks-correctness.md)）。
- 评测框架的评分和选取（EdgeBench `6e4e5f4`）：`sforge/harness/grading.py`、`sforge/harness/selection.py`、`sforge/harness/score_rescale.py`。
