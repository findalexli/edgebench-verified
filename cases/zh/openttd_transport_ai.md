# OpenTTD Transport AI (`openttd_transport_ai`)

**结论：** 已修复。<mark>任务说明要求解题者最大化一个游戏函数 `AICompany.GetCompanyValue`，但它在固定的游戏版本中并不存在，因此调用它的脚本会崩溃，随附的初始程序也在第一次调用它时崩溃；修复改的是任务说明和初始程序，而不是评分器。</mark>

![流程图：原始任务说明指定的 GetCompanyValue 在 OpenTTD 13.4 中不存在，因此调用它的脚本在该调用处终止，其公司停止行动；修复版的任务说明和初始程序改用确实存在的 GetQuarterlyCompanyValue，脚本得以继续运行。一条注释说明评分器不变，初始程序在两个版本中都得 0 分。](figures/openttd_transport_ai.svg)

*任务要求解题者调用一个不存在的游戏函数，因此初始程序在第一次调用它时就崩溃了；修复改动了任务说明和初始程序。*

## 任务要求

OpenTTD 是一款开源的运输公司模拟游戏。解题者编写 "a **Squirrel** AI in `my_ai/` that maximizes **company value** over 20 game-years, averaged across multiple random seed maps."（大意：在指定目录中编写一个 **Squirrel** AI，在多张随机种子地图上平均，使一段游戏年限内的**公司价值**最大化。）Squirrel 是 OpenTTD 为电脑玩家使用的脚本语言。任务说明的目标一行写道："Maximize **`AICompany.GetCompanyValue(AICompany.COMPANY_SELF)`**"。它还说 "A baseline AI that just logs company value is already in `my_ai/`; improve it"（大意：目录中已有一个只记录公司价值的基线 AI，请改进它）。类别：交互式游戏与模拟器。

## 问题出在哪里

**任务说明指定了一个不存在的函数。** `AICompany.GetCompanyValue` 不在 OpenTTD 13.4 的 NoAI API 中，而该 API 是游戏提供给电脑玩家的接口。随附的初始程序记录一行日志后，就在主循环中（`main.nut` 第 5 行）调用它，随即崩溃：

```
dbg: [script] [0] [S] Your script made an error: the index 'GetCompanyValue' does not exist
dbg: [script] [0] [S] *FUNCTION [Start()] myai/main.nut line [5]
dbg: [script] The script died unexpectedly.
```

原始评分器在初始程序上的完整运行：墙钟时间 **63 s**，退出码 0，请求的 5/5 个种子全部返回。

| 种子 | 公司价值 | 公司价值对应日期 | 资金 | 贷款 | 净资产 | 错误 |
|---|---|---|---|---|---|---|
| 0 | 0 | N/A | 54,191 | 100,000 | -45,809 | YES |
| 1 | 0 | N/A | 54,191 | 100,000 | -45,809 | YES |
| 2 | 0 | N/A | 54,191 | 100,000 | -45,809 | YES |
| 3 | 0 | N/A | 54,191 | 100,000 | -45,809 | YES |
| 4 | 0 | N/A | 54,191 | 100,000 | -45,809 | YES |

包装脚本打印出 `CASE 0000 WA score=0` 和 `TOTAL_SCORE 0`。

- **预期与实际：** 遵循任务说明、调用指定函数的解题者，预期能读到自己的公司价值。实际上，脚本在这次调用处被终止，公司停止行动。分数是其最后一个为正的季度价值，或者 0。
- 这个问题可以通过任务提供的本地测试发现。它是误导性的任务说明，而不是评分器错误。

**任务说明还错误描述了计分内容。** 目标一行把目标定义为 "vehicle value at 1.5× purchase + infrastructure value + cash − loans"（即车辆价值按购买价的一定倍数计，加上基础设施价值和现金，再减去贷款）。评分器读取的是游戏自身的公司价值。在 OpenTTD 13.4 源码中，这个值把车辆按其价值的 1.5× 计入，并计入车站，再加上现金减去贷款，下限为 1；道路、铁轨和其他基础设施不计入。下表中的探测提交与此一致：它有 8 个站点、没有车辆、现金减贷款为负，得分为 4,975。按 [`METHOD.md`](../METHOD.md) 中的判据，这属于告诉智能体的规则与实际应用的规则不同的情形。一个修建铁轨或道路、期待它们增加价值的解题者，计分时不会算上它们。其影响大小没有测量，而关于铁轨的部分依据的是阅读源码，而不是一次运行。

**评分器本身行为正确。** 它从游戏每月的存档文件中读取公司价值。在一次种子 0 的运行中，共有 239 个月度存档，从 1950-02-01 到 1969-12-01，因此游戏完整运行了 7,300 天。`old_economy[0].company_value` 在每个存档中都是 1，评分器的 `> 1` 过滤把它变成 0，所以什么都不做的公司得 0 分。有 239 个存档、最终日期为 1969-12-01 时，"最后的季度价值"对应 1969-10 这一季度。OpenTTDLab（运行游戏的库）给出的 `error` 标志会被打印出来，但不影响分数。

**这次运行不存在运行时间问题。** 单个种子耗时 55.4 s，约 **9,750 ticks/s**，远高于所需的约 150 ticks/s。5 个种子的运行耗时 63 s，而 `eval_timeout` 为 3600 s。

## 影响有多大

对于遵循任务说明、调用指定函数的解题者，影响可达全部分数。在本地测试并改用其他函数的解题者不受影响。

## 修复

修复版位于 `repairs/openttd_transport_ai-v2/`（存放修复版的文件夹）。

- **任务说明。** `work.agent_query` 的目标段落现在写明：OpenTTD 13.4 没有 `AICompany.GetCompanyValue`，调用它会使脚本停止。它指定用 `AICompany.GetQuarterlyCompanyValue(AICompany.COMPANY_SELF, AICompany.CURRENT_QUARTER)` 获取当前值，用季度 `1` 获取当前季度开始时记录的值。它更正了公式：车站计入，其他基础设施不计入，下限为 1。它说明了分数的读取方式：对每个种子，取游戏结束前最近一个季度边界处的值（否则退回到更早的一个大于 1 的季度，或取 0），再对 5 个种子取平均。
- **初始程序。** `my_ai/main.nut` 第 5 行改为调用 `GetQuarterlyCompanyValue(AICompany.COMPANY_SELF, AICompany.CURRENT_QUARTER)`。`Dockerfile.work` 以原始工作镜像的摘要为基础构建修复版工作镜像（压缩后约 0.46 GB）；`work.image_tag` 变为 `f2e9a9fb0fff-ebv-v2`。
- **在游戏代码中的依据。** OpenTTD 13.4 源码中，`GetQuarterlyCompanyValue` 在 `CURRENT_QUARTER` 时定义为 `CalculateCompanyValue(c)`，否则为 `old_economy[quarter - 1].company_value`。缓存的 13.4 程序中包含名称 `GetQuarterlyCompanyValue`，不包含 `GetCompanyValue`。一个探测脚本报告 `has_GetCompanyValue=false has_GetQuarterlyCompanyValue=true`。
- 评分器镜像、`eval_cmd`、解析器和分数刻度（`log_max`，参考点为 1e5 到 1e9）都不变，因此每份提交在原始版和修复版下得分相同。

并排对照运行（完全按原始 `eval_cmd`，5 个种子，20 个游戏年；摘自 `paired/results.md`）。`TOTAL_SCORE` 是原始结果（换算为 0–100 分之前）。

| 测试提交 | 随附于哪个任务版本 | 脚本是否崩溃？ | `TOTAL_SCORE`，原始版 | `TOTAL_SCORE`，修复版 | 每个种子的公司价值（评分器读到的） | 错误标志（5 个种子） |
|---|---|---|---|---|---|---|
| baseline_v1（随附的初始程序） | 原始版 | 是，在 `main.nut` 第 5 行 | 0 | 0 | 5 个种子均为 0 | 5/5 YES |
| probe_min（每月调用正确的函数） | 遵循修复版任务说明 | 否 | 0 | 0 | 5 个种子均为 0 | 0/5 |
| baseline_v2（修复版初始程序） | 修复版 | 否 | 0 | 0 | 5 个种子均为 0 | 0/5 |
| probe_value（价值为正的测试提交） | 遵循修复版任务说明 | 否 | 4975 | 4975 | 5 个种子均为 4,975 | 0/5 |

展示问题的测试提交，即随附的初始程序，在同一评分器上的结果：

| 初始程序 | 脚本是否崩溃？（原始版） | 脚本是否崩溃？（修复版） | `TOTAL_SCORE`，原始版 | `TOTAL_SCORE`，修复版 |
|---|---|---|---|---|
| 随附的初始程序（原始工作镜像 vs 修复版工作镜像） | 是，在 `main.nut` 第 5 行 | 否 | 0 | 0 |

- 空闲的探测提交得 0 分，因为空闲公司的价值停留在下限 1（现金减去 100,000 的贷款为负），而评分器把它计为 0。它们表明脚本得以存活，并不代表得到正分。
- 对两个探测提交，在每个种子上，最后记录的 `GetQuarterlyCompanyValue(SELF, 1)` 都等于评分器所用的 `old_economy[0].company_value`。对 `probe_value` 而言该值为 4,975，而结束时 `CURRENT_QUARTER` 的当前值为 4,858。

**分数兼容性：** 作为同一测试框架的测量结果，分数可比。但如果原始版的解题者遵循了任务说明并调用了那个不存在的函数，那么作为解题者能力的度量，分数不可比。

## 我们如何检查

- **在按摘要固定的原始镜像中运行原始评分器。** 完全按原样的 eval_cmd，即 `cd /home/workspace/openttd_ai && OPENTTD_N_SEEDS=5 python3 /tmp/eval_openttd.py`，在评分器镜像中、`timeout 2600` 的限制下离线运行（`--network none --memory 6g`）；主机有 8 个 vCPU，因此 5 个种子并行运行。提交是工作镜像中随附的初始程序 `my_ai/`。OpenTTD 13.4 和 OpenGFX 7.1（游戏的图形素材集）已预先缓存在镜像中。
- **存档文件检查。** 一个种子 0 的诊断脚本（`diag1.py`）以评分器自己的参数调用 `run_experiments`，并打印每一行存档记录。
- **原始版与修复版的并排对照运行。** 即上面的表格。共重复三次，结论没有变化（[`data/paired-repeatability.md`](../data/paired-repeatability.md)）。

## 局限

- 没有运行任何 AI 模型或解题者。影响只在随附的初始程序和我们编写的探测提交上展示。
- 在并排对照运行中，每份测试提交只评分一次，因为两个版本的评分器镜像相同；原始版和修复版的 `TOTAL_SCORE` 两列重复的是同一个分数。两个版本只在解题者收到的初始程序和任务说明上不同。
- 唯一原始结果为正的测试提交是一个探测提交（4,975，远低于分数刻度的下参考点 1e5，因此在 100 分制下为 0 分）。所有不超过 1e5 的公司价值在 100 分制下都是 0 分，因此 0 分无法区分崩溃的脚本和较弱的脚本。上参考点 1e9 能否达到，没有测试。
- 任务说明中的文档路径（`docs/noai_api_docs/`）与实际路径（`docs/openttd_reference_docs/noai_api_docs/`）不同，随附的 HTML 文档似乎来自比 13.4 更新的 OpenTTD 版本。这两点都已在修复包的 README 中注明，未作改动。
- ticks/s 数值是一台主机上空闲脚本的结果。运营大量车辆的 AI 会更慢；这一点没有测量。

## 复现

- 原始评分器镜像：`sha256:27167956fd00…`。
- `evidence/runs/openttd_transport_ai-native-baseline/run.sh`（完整运行）和 `evidence/runs/openttd_transport_ai-native-saves-diag/run.sh`（配合 `diag1.py`）。需要一台能拉取固定镜像的 Docker 主机。
- 审查：`evidence/reviews/openttd_transport_ai-native.md`。
- 修复与并排对照运行：`repairs/openttd_transport_ai-v2/`（先运行 `paired/stage.sh`，再运行 `tools/e2b_run.py`）。
