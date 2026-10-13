# OpenRCT2 Theme Park AI (`openrct2_theme_park_ai`)

**结论：** 已修复。<mark>任务说明承诺每个场景运行约 4 个游戏年，但 120 s 的时间预算只够约 68 个游戏日，因此分数只是游戏早期的一张快照；修复版更正了任务说明。</mark>

![两根条形图：每个场景 120 s 预算内达到 68 到 69 个游戏日，而承诺的是 992 天（约 4 年）；以及 120 s 的预算，对比每个场景跑完 992 天所需的 1,667 s。](figures/openrct2_theme_park_ai.svg)

*任务说明承诺每个场景约 4 个游戏年，但每个场景 120 s 的预算只够 68 到 69 个游戏日，因此分数只是游戏早期的一张快照。*

## 任务要求

解题者为主题公园模拟游戏 OpenRCT2 编写一个插件，使其 "maximizes **normalized company value** across 3 scenarios"（在各场景中使**归一化公司价值**最大化）。原始任务说明的 Rules 一节写道："The engine runs each scenario for ~4 game years at speed 4 (host --headless)"（大意：引擎以无界面主机模式、按其中所写的速度，把每个场景运行约其中所写的游戏年数），评分 "reads the real in-game `park.companyValue`"（读取游戏内真实的公司价值）。Key APIs 一节把 `gamesetspeed {speed: 4}` 描述为 "max speed (host mode cap is 4)"（最高速度，主机模式的上限即为此值），但任务说明并未要求解题者使用速度 4。类别：交互式游戏与模拟器。

## 问题出在哪里

**承诺的游戏时长无法达到。** 包装脚本为每个场景设置 `OPENRCT2_TIMEOUT=120`，并把整次运行限制在 1,800 s 内。任务清单中的 `eval_timeout` 为 2,400 s。评分器的监视程序设有 `targetDays = 992`，只有到达该日期才输出 `DONE`。评分代码使用监视程序的最后一个采样，从不检查是否到达了 `DONE`。

- 在 2 个 CPU、速度 4 下，引擎每秒墙钟时间推进 0.593 到 0.597 个游戏日（请求速度 8 时为 0.602，实际仍以速度 4 运行）。速率受真实时间限制，而不受主机 CPU 限制：在 0.25 个 CPU 下为 0.582，约低 2%。不过启动阶段受 CPU 限制：在 0.25 个 CPU 下，第一个采样在 11.5 s 才到达，而不是 4.6 s，因此一次 60 s 的运行只达到 27 个游戏日，而不是 33 个（`paired/check_horizon.out`）。
- 每个 120 s 的场景覆盖 68 到 69 个游戏日，约为 992 天目标的 7%，且从未出现 `DONE`。
- 要达到 992 天，每个场景需要约 1,667 s，远超 120 s 的场景预算。三个场景合计（约 83 分钟）也会超过 1,800 s 的包装脚本上限和 2,400 s 的清单超时。

原始评分器上的例子（120 s，速度 4，中等场景）：

- 按任务说明预期：约 4 个游戏年。
- 实际：游戏从日期 8,4,25 运行到 8,7,2，共 69 个游戏日。公司价值从 198,010 变为 133,260，归一化公司价值（该任务的单场景结果）为 0.915。
- 三个场景的平均值为 1.038，包装脚本会将其打印为 `TOTAL_SCORE 10384`（这是计算所得；包装脚本本身没有运行）。

**解题者能控制游戏速度。** `gamesetspeed` 在允许调用的列表中，提交中较晚的调用会覆盖监视程序设置的速度 4。速度 1 的速率为 0.077 天/秒（25.8 s 内 2 个采样、2 个游戏日；与模型的 0.075 一致），速度 3 为 0.291 天/秒。速度 8 会被拒绝。较慢的游戏可以让公司价值保持在初始值附近。在这些运行中，1.10 的上限掩盖了这一点。

为什么重要：该任务衡量的是约 2 个月后的公司价值，而不是约 4 年后的。按所述游戏时长做规划的解题者，优化的是错误的目标。

## 影响有多大

我们没有把它作为分数变化来测量。这个问题改变的是衡量的**内容**：衡量的是约 2 个月后的价值，而不是约 4 年后的。没有证据表明它抬高或压低了某个具体解题者的分数。所有按所述游戏时长做规划的解题者都受到影响。

只为到达 `DONE` 的运行计分并不是修复办法：在随附的 120 s 预算下，这会让每份提交都得 0 分。

## 修复

修复版把 `work.agent_query`（任务说明）中 Rules 的一条要点替换为两条。新文本写明：

- 每个场景运行 "**120 wall-clock seconds**, not to a fixed game date"（按**墙钟秒数**计时，而不是运行到某个固定的游戏日期）。在速度 4 下，这 "only about **70 game days**"（只能覆盖约这么多个**游戏日**）。
- 分数使用监视程序在截止前的最后一个采样。
- 插件可以用速度 1-4 调用 `gamesetspeed`，最近一次调用生效，较低的速度会按比例模拟较少的天数。

镜像、`eval_cmd`、超时、解析器以及分数刻度的参考点（线性，0 到 40000）都不变。解题者能看到的其他文件都没有说明游戏时长。

并排对照检查（仅任务说明；摘自 `paired/results.md`）：

| 检查 | 状态 |
|---|---|
| 展示问题的测试提交：原始任务说明给出错误的游戏时长，修复版给出实测的时长 | 已检查：见下表 |
| 正确的测试提交：从原始版到修复版分数不变 | 按构造成立。评分器的文件逐字节不变。没有新的评分运行 |
| 无效的测试提交：两版都拒绝 | 按构造成立。没有重新运行 |
| 在 E2B（云端机器）上的并排对照作业 | 没有运行。不需要，因为没有任何可执行内容改变 |

```
model speed 1: 0.075 game days / wall-s; 120 s -> 9.0 days
model speed 3: 0.299 game days / wall-s; 120 s -> 35.9 days
model speed 4: 0.598 game days / wall-s; 120 s -> 71.8 days
model: 992 target days at speed 4 need 1658 s

log                          scenario             budget spd t_first t_last  days(samples) d/s   model
run_120s_cpus2.log           scenario_large.park    120   4    4.6  117.8   68(41)   0.595  0.598  DONE=False
run_120s_cpus2.log           scenario_medium.park   120   4    4.5  117.3   69(42)   0.595  0.598  DONE=False
run_120s_cpus2.log           scenario_small.park    120   4    4.7  117.6   68(41)   0.593  0.598  DONE=False
run_60s_speed4_cpus2.log     scenario_small.park     60   4    4.6   59.8   33(20)   0.597  0.598  DONE=False
run_60s_speed4_cpus0.25.log  scenario_small.park     60   4   11.5   57.9   27(17)   0.582  0.598  DONE=False
run_60s_speed1_cpus2.log     scenario_small.park     60   1   27.2   53.0    2(2)    0.077  0.075  DONE=False
run_60s_speed3.log (new)     scenario_small.park     60   3    7.5   59.1   15(10)   0.291  0.299  DONE=False
run_60s_speed8.log (new)     scenario_small.park     60   8    5.0   59.9   33(20)   0.602  0.598  DONE=False
```

**分数是否可比？**

- **评分器相同，分数相同。** 同一个 `my_plugin.js` 在原始版和修复版下得到相同的分数，只存在实时游戏通常的运行间波动。原始版的运行本来就是同样真实的 120 s 时长。
- **在解题者的策略依赖任务说明的情况下，作为解题者能力的度量则不可比。**原始版的解题者可能按 4 年做了规划；修复版的解题者则可以把策略前置，或者故意降低速度。

## 我们如何检查

- **原始评分器，来自按摘要固定的公开镜像。** 在评分器镜像中运行原始辅助程序自身的 `validate_plugin`、`run_scenario` 和 `score_scenario` 函数。唯一的改动是用 tee 额外记录引擎的标准输出。运行参数为 `--network none --memory 2g --cpus 2`，其中一次运行使用 `--cpus 0.25`。运行覆盖三个场景各 120 s，以及速度 1、3、4 和 8 下各 60 s，使用一个简单的测试插件。
- **独立的速率模型。** 一个从基本原理出发、使用 `openrct2.d.ts` 中记载的 tick 和月份常量构建的模型，能预测实测速率（上表中的 "model" 列）。
- 修复版没有改变任何可执行内容，因此没有需要重复的并排评分运行。

## 局限

- 没有运行任何 AI 模型或解题者。所示影响只针对我们编写的测试插件，也没有估计对排行榜的影响。
- **降低速度的动机仍然存在。** 修复版如实说明了速度规则，但并不阻止插件降低速度。要消除这一动机，需要修改评分器：每个 tick 重新设定速度 4，或者在预算足够长的前提下按固定游戏日期计分。
- **约 70 天的前提是引擎跟得上真实时间。** 主机没有固定。更慢的主机、过载的主机或很重的插件可能会落后更多。
- **运行数量少。** 每种配置只运行一次，使用的是一个简单的测试插件，它雇佣员工的操作失败了。没有运行任何有竞争力的插件。
- **没有通过包装脚本运行。** 完整的三场景序列是通过辅助程序的函数运行的，而不是通过 `eval_openrct2.py`。分数刻度上 40000 这一参考点没有检查。

## 复现

- 评分器镜像：`sha256:a5263578…`。
- 驱动程序和测试插件：`evidence/scripts/openrct2_theme_park_ai/driver.py`、`plugin.js` 和 `plugin_speed1.js`。保存的日志为同一文件夹中的 `run_*.log`。
- 游戏时长检查，在 `repairs/openrct2_theme_park_ai-v2/paired/` 中运行：`python3 -I check_horizon.py ../../../evidence/scripts/openrct2_theme_park_ai/run_*.log logs/run_*.log`
- 任务说明的差异：`repairs/openrct2_theme_park_ai-v2/repair.patch`，从 `orig/agent_query.md` 改为 `files/agent_query.md`。
- 支撑记录：`repairs/openrct2_theme_park_ai-v2/`（存放修复版的文件夹：README、`source-lock.json`、`paired/results.md`）。
