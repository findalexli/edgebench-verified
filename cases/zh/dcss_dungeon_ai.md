# DCSS Dungeon Crawl Stone Soup AI (`dcss_dungeon_ai`)

**结论：** 保留（附说明）。<mark>正常运行时，分数与任务的承诺一致；没有游戏结束记录的一局计 0 分，这也符合任务说明的暗示；说明涉及分数依赖墙钟速度，以及最高参考点没有核实。</mark>

## 任务要求

解题者要用 Lua（一种脚本语言）为地牢游戏 Dungeon Crawl Stone Soup（DCSS 0.28）写一个机器人程序。评分方式为 "5 hidden seeds, **900s game budget per game**, mean score across all 5 games"（用隐藏种子，每局有固定的游戏时间预算，取各局平均分）。各局并行运行，到截止时间评分器强制退出。任务说明写道 `Pass rate` "is a validity check, not the quality metric"（是有效性检查，不是质量指标），也承认 "Wall-clock/PTTY scheduling can still create small score noise"（墙钟/PTTY 调度仍可能造成小的分数噪声）。类别：交互式游戏与模拟器。

## 我们检查了什么

正常运行时，我们没有发现问题，并确认了以下几点。每局的分数是它的 morgue 文件（游戏的结束记录）第 5 行上的整数。如果 morgue 中出现 wizard 或 explore 模式，这一局按没有 morgue 处理（`eval_dcss.py:84-85`、`:164-166`），得 0 分；评分器把提交标为 `valid: false`，而 EdgeBench 的选取规则不读这个标志（见第一条说明）。总分是 5 局的平均值，四舍五入到 0.1，再按 `100*log1p(raw/400)/log1p(125)` 换算为 0–100 分。代码与任务说明一致：5 个种子、`TIMEOUT=900`、5 局并行，以及退出序列。

| 原始平均分（换算到 0–100 之前） | 100 分制得分 |
|---|---|
| 0（闲置的机器人） | 0 |
| 12.4（五局：2、21、18、7、14） | 0.63 |
| 400 | 14.3 |
| 5,000 | 53.8 |
| 20,000 | 81.3 |
| 50,000 | 100 |

正常情况下每局最多约 948 s，触发硬超时的情况下最多约 1008 s，都在评分器的时限 `eval_timeout` 1100 之内。

下面几点需要说明。

- 没有 morgue 的一局计 0 分。这符合任务说明的暗示，不是缺陷。任务说明把分数说成全部 5 局的平均值。如果一局没有写出 morgue（例如强制退出序列两次都失败），这一局得 0 分，评分器照样输出全部 5 局的平均值作为分数，同时输出 `"valid": ok == total`（`eval_dcss.py:210-221`）。EdgeBench 的评测框架保留这个分数。`_grade_structured` 原样照抄，任务的 `score_first` 选取规则不读 `valid`（`sforge/harness/grading.py:200-217`、`sforge/harness/selection.py:83-103`，EdgeBench 版本 `6e4e5f4`）。处于 wizard 或 explore 模式的一局也这样处理。这一结论来自源码，我们还把评分器的输出格式离线送进评测框架验证过；我们在真实运行中没有观察到这条路径。
- 分数依赖墙钟和主机速度。种子是固定的，但分数大致等于回合速度 × 900 s，而回合速度取决于同时运行的五个游戏进程分到多少 CPU。任务 JSON 没有设 CPU 上限；发布方的排行榜设置（`examples/all-tasks-k8s/experiment.yaml`（引用见 [`evidence/impact/edgebench-leaderboard-config.md`](../evidence/impact/edgebench-leaderboard-config.md)），sha256 `d9d29979…43be`）给评分器 4 个 CPU 跑这五局。游戏过程中，评分器还每隔 1.5 s 墙钟时间发送一次空格、CR 和 Esc，这串输入依赖计时。任务说明承认有 "small score noise"（小的分数噪声），但我们没有测量噪声有多大。
- 原始平均分 50,000（100 分的参考点）能否在 900 s 内达到，我们没有核实，也没有任何强机器人的运行记录。随任务提供的基线机器人得分基本为 0。

随任务发布的说明写了两条。

- 分数取决于墙钟速度和 CPU 分配；运行间波动没有测量。
- 100 分对应的参考点 50,000 尚未证明可以达到。

任务没有改动；上述说明随任务一起发布。

## 影响有多大

- 缺少 morgue：没有影响；这一局在平均值中计 0，符合任务说明的暗示。
- 依赖墙钟速度：影响每个解题者，我们没有测量影响有多大。已发布的 12 小时结果为 8.3、13.4、6.1、7.6 和 5.7 分（满分 100）（`tasks/README.md`，dcss 行）。其中有两对结果分别只差 0.4 分和 0.7 分，这种量级的噪声就可能让它们的先后颠倒。局限中所说的重复运行完成之前，这一结论只是暂定的。

## 我们如何检查

- 我们阅读了固定版本的原始评分器源码 `eval_dcss.py`（sha256 `101e8858…2218`）以及 EdgeBench 的评分和选取代码（`grading.py`、`selection.py`，版本 `6e4e5f4`）。我们没有记录评分器镜像的摘要，读过的 `eval_dcss.py` 副本也没有在本仓库中发布，所以引用的行号只能对照评分器镜像核对。
- 我们用精确算术把评分器的休眠时间表与 `eval_timeout` 1100 对照，并核算 `log1p_max` 分数换算。
- 在评分器上，一个闲置的机器人共用 962 s，得 0 分。一个能推进游戏的机器人跑了一次五局，得 2、21、18、7、14（平均 12.4）。

## 局限

- 我们没有运行任何 AI 模型或解题者。影响只在闲置运行和能推进游戏的运行上展示。
- 缺少 morgue 的情况是我们从源码推理的，没有实际触发过。
- 得分为正的五局运行只有一次，没有重复。能回答噪声问题的检查我们还没有做，做法是在固定分配的至少 5 个核上把同一个机器人跑两次，再用一半核数跑一次。如果波动与不同机器人之间的差距相当，结论将改为修复或撤下这个任务。

## 复现

- 审查记录：`evidence/reviews/_game-tasks-correctness.md`，第 4 节。
- 固定版本的评分器副本：评分器镜像中的文件 `eval_dcss.py`（sha256 见[审查记录](../evidence/reviews/_game-tasks-correctness.md)）。
- 评测框架的评分和选取（EdgeBench `6e4e5f4`）：`sforge/harness/grading.py`、`sforge/harness/selection.py`、`sforge/harness/score_rescale.py`。
