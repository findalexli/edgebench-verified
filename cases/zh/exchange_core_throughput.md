# Exchange Core Throughput (`exchange_core_throughput`)

**结论：** 已修复。<mark>原始的正确性检查发现不了错误的手续费或丢失的消息，因此不正确的引擎也能拿到全部分数；修复版要求项目自带的集成测试通过，并在无网络的情况下评分。</mark>

![通过/不通过标记组成的表格。各行分别是：正确的引擎；按错误费率向卖方收费的引擎（收取挂单等待成交的费率，而不是立即成交的费率）；从不发送成交消息的引擎。在原始评分器下，三者都通过并按速度计分；修复版评分器另外运行项目自带的 33 个测试，正确引擎通过，两个有错误的引擎被拒绝，记 0 分。注释说明速度分的含义（每秒 209 万笔或更慢记 0 分，每秒 600 万笔记 100 分），列出相互重叠的速度分（满分 100：正确引擎 0–24.19，收错手续费 7.77–24.40，丢失消息 4.71–15.62），并指出在 4 个 CPU 下连正确引擎的速度分也是 0。](../figures/zh/exchange_core_throughput.svg)

*两个带有现实错误的引擎通过了原始评分器，并按速度得分；修复版评分器拒绝了它们。智能体要在不改变功能的前提下让一个证券交易撮合引擎运行得更快，但原始评分器只核对资金总额是否平衡、订单簿是否一致，因此一个向卖方收错手续费的引擎和一个从不发送成交消息的引擎都能通过，并得到速度分（满分 100）：各四次运行分别为 7.77–24.40 和 4.71–15.62，正确引擎七次运行为 0–24.19，这些差异属于运行间波动。修复版评分器先运行项目自带的 33 个测试：在三次并排对照测试中，两个有错误的引擎都记 0 分，正确引擎仍然通过；在排行榜设置的 4 个 CPU 下的三次运行中它也通过，只是速度太慢，速度分为 0。*

## 任务要求

智能体的任务是为 exchange-core 提速。exchange-core 是证券交易所的撮合引擎（把买单和卖单配对的软件）。目标是 "maximize the throughput (MT/s — millions of transactions per second) of `PerfThroughput#testThroughputPeak`"（使该测试的吞吐量最大化，单位为每秒百万笔交易）。

规则写道 "Do NOT change behavior: `mvn test` must still pass functional assertions"（不得改变行为：测试仍必须通过功能断言）。规则还写道 "`CASES_OK = 1` only when `mvn test` exits 0 AND an MT/s line was parsed"（只有当测试正常退出且解析到吞吐量行时才计为通过）。原始结果（换算到 0–100 之前）为 `int(round(Average_MT_s * 1000))`。它按对数刻度（`log_max`）换算为满分 100 的分数。0 分的参考点是 2090.634594076933，100 分的参考点是 6000。类别：系统与软件工程。

## 问题出在哪里

**不正确的引擎通过了正确性检查并获得分数。** 吞吐量测试的正确性检查只比较两件事：全局余额必须为零，L2 订单簿（挂单的价格档位）必须一致。测试源码用 `// TODO compare events, balances, positions` 标出了缺失的比较。对随附引擎做两处看似合理的改动（每处只改一个地方），即可看出其影响：

- **feeswap。** 一个复制粘贴造成的手续费缺陷：作为 taker（订单立即成交的交易者）的卖方被收取 maker 手续费，而不是 taker 手续费。交易所的手续费账簿记下同样错误的金额，因此全局余额仍然恰好为零。卖方入账金额偏多，而在每笔卖方为 taker 的交易中，交易所的手续费收入都少记了。
- **dropevents。** 结果处理阶段不再把命令结果、成交事件、订单缩减事件或拒绝事件转发给用户的结果消费者。API future（调用的返回值）仍然正常完成。

在原始评分器下，两个引擎在全部 50 个检查轮次中都通过了 `testThroughputPeak`。Maven 以 0 退出，评分器打印 `CASE 0000 OK` 和 `CASES_OK 1`。单次运行结果：

| 引擎 | TOTAL_SCORE（原始结果） | 100 分制得分（log_max） |
|---|---|---|
| 正确的测试提交（随附引擎） | 2254 | **7.14** |
| feeswap（余额错误） | 2704 | **24.40** |
| dropevents（丢失事件） | 2465 | **15.62** |

项目自带的集成测试拒绝这两个引擎，并让正确的引擎通过。对 feeswap，5 个 `ITFeesExchangeBasic` 测试中有 2 个失败。例如，`shouldProcessFees_BidGtcMaker_AskIocTakerPartial` 期望 `<199061711100L>`，得到的是 `<199063788300L>`。对 dropevents，全部 28 个 `ITExchangeCoreIntegrationRejectionBasic` 测试都失败，因为处理程序收不到任何命令结果。

feeswap 做的工作与正确的引擎相同。所以这三者之间的排名是吞吐量噪声，而不是缺陷带来的速度效应。结论是：不正确的引擎获得了全部分数。

**原始评分器无法离线评分。** 固定版本镜像中的 `~/.m2`（本地 Maven 缓存）缺少 `surefire-junit-platform:3.0.0-M3`。在 `--network none` 下，每份提交都会失败，包括未修改的引擎（`CASE 0000 RE score=0 / TOTAL_SCORE 0`）。评测框架给评分器容器开放了网络，`internet: false` 只作用于智能体容器。因此原始评分依赖于评分时能访问 Maven Central。

**说明：评分器的 CPU 预算没有写明，而在 4 个 CPU 下随附引擎得 0 分。** 任务说明描述了引擎的线程拓扑（"builder defaults (4ME+2RE, msgsInGroupLimit=4096, BUSY_SPIN wait, DirectImpl orderbook, AffinityThreadFactory)"），并说 "thread topology changes (e.g. 4ME+2RE → 2ME+1RE) can have dramatic impact"（线程拓扑的改变可能有巨大影响），但没有写明 CPU 数。在 EdgeBench 的排行榜配置 `examples/all-tasks-k8s/experiment.yaml` 中（引用见 [`evidence/impact/edgebench-leaderboard-config.md`](../evidence/impact/edgebench-leaderboard-config.md)）（sha256 `d9d299794ba946cae8d2b7f68a7879a35bb8565d95e78107edf79802993643be`），评分器继承 `judge_cpu_limit: 4`。这一限制是 CPU 配额：在 `--cpus 4` 的评分器容器内，`nproc` 仍报告 8，而 `/sys/fs/cgroup/cpu.max` 读数为 `400000 100000`（由 `evidence/runs/exchange_core_throughput-cpu4v8-a/run.sh` 第 17 行记录；输出文件连同镜像摘录一起不放入仓库）。所以按 `nproc` 决定自身规模的引擎会看到 8 个 CPU。

在原始评分器上用原始 eval_cmd 测量（`--network none`，挂载与 `exchange_core_throughput-v2-paired-b` 中相同的 `~/.m2` 文件）。4 个 CPU 一列合并了两组运行：随附引擎 4 次、建议 1 次，使用 `--memory 4g`（`evidence/runs/exchange_core_throughput-cpu4v8-a/result/out/summary.txt`、`-b`）；以及各 3 次，使用排行榜的 `--memory 8g`（`evidence/runs/exchange_core_throughput-v2-cpu4m8g-rep{1,2,3}`）。8 个 CPU 一列只来自第一组。

| 引擎 | 4 个 CPU，原始结果（MT/s × 1000） | 4 个 CPU，满分 100 | 8 个 CPU，原始结果 | 8 个 CPU，满分 100 |
|---|---|---|---|---|
| 随附引擎（4 个 CPU 下 7 次运行，8 个 CPU 下 4 次） | 939、965、972、983、1,006、1,033、1,059 | 0 | 3,418、3,617、4,155、4,638 | 46.63–75.58 |
| 任务说明的建议，2ME+1RE（4 个 CPU 下 4 次运行，8 个 CPU 下 1 次） | 1,644、1,894、1,994、2,091 | 0–0.02 | 4,122 | 64.39 |

在 4 个 CPU 下，随附引擎的速度低于 0 分参考点（2,090.63），因此得 0 分。任务说明自己的建议在 4 个 CPU 下让吞吐量大约翻倍（原始结果 1,644–2,091），但四次运行中有三次仍低于 0 分点，第四次只比它高 0.4，因此得满分 100 中的 0–0.02 分；在 8 个 CPU 下，它的单次运行结果（4,122）落在随附引擎的范围内（3,418–4,638）。所以诚实策略之间的排名取决于 CPU 数，而在排行榜设置下，每个低于约 2.09 MT/s 的引擎都得 0 分。0 分参考点的来源（在什么硬件上测得）不明。它保持不变，因为不存在可精确计算的替代值；根据这些运行设定新的参考点将是另一项决定。修复版没有改变这一点。在同样的设置下（`--cpus 4 --memory 8g`，即排行榜的 `judge_cpu_limit` 和 `judge_mem_limit`），修复版的三次运行每次都通过了集成测试步骤（`GATE OK … tests=33`），随附引擎的原始结果为 811、1,073 和 1,194，2ME+1RE 建议为 1,684、1,687 和 1,832；同一批工作节点上的原始评分器结果为 965–1,059 和 1,644–1,994；全部都是满分 100 中的 0 分。修复版的分数在原始评分器的吞吐量噪声范围之内（随附引擎为 811–1,194，原始评分器全部七次运行为 939–1,059）（`evidence/runs/exchange_core_throughput-v2-cpu4m8g-rep{1,2,3}`）。

## 影响有多大

一个有缺陷的引擎拿到全部吞吐量分数，而不是 0 分。在每个有缺陷引擎的四次原始评分器运行中（上面的单次运行和三次并排对照运行），feeswap 得 7.77–24.40 分，dropevents 得 4.71–15.62 分（满分 100）（原始结果 2,269–2,704 和 2,197–2,465）；未修改的引擎在与它们同批的七次原始评分器运行中（上面的正确测试提交和三次并排对照运行的原始评分器一侧）得 0–24.19 分（原始结果 2,008–2,698），因此这些分数都在吞吐量噪声范围内。任何在优化中破坏了手续费或事件投递、但保持全局余额为零的解题者，都会拿到全部分数而不是 0 分。

## 修复

在未修改的计时测试之前，修复版评分器在一次单独的 Maven 运行中执行项目自带的集成测试 `ITFeesExchangeBasic` 和 `ITExchangeCoreIntegrationRejectionBasic`（33 个测试）。只要其中任何一个失败，提交就得 0 分（`WA`，答案错误）。计时的 Maven 运行没有改变。

修复版还改变了计时运行的计分方式。原始评分器在 Maven 以非零退出时把运行标为 `WA`，但仍把吞吐量打印为分数（`CASE 0000 WA score=<MT/s × 1000>` 和 `TOTAL_SCORE <MT/s × 1000>`），而评测框架不论用例状态如何都按 `TOTAL_SCORE` 排序（`sforge/harness/grading.py` 的 `extract_score`；`selection.py` 的 `_score_first`）。修复版在状态不是 `OK` 时把分数设为 0（`repair.patch` 中的 `if status != "OK": score = 0`）。吞吐量从 `Average: … MT/s` 行解析得到，而测试只有在所有轮次都通过检查后才记录这一行（`ThroughputTestsModule.java:42-69`）；逐轮的行带有日志前缀，不匹配评分器的行首模式。所以只有当 Maven 在记录平均值之后以非零退出时，才会走到这条路径，例如引擎在关闭时出错。规则写道 "`mvn test` must still pass functional assertions"（测试仍必须通过功能断言）。并排对照中有一组走到了这条路径（`shutdownbusy`）：全部 50 轮通过、平均值被记录，然后引擎在关闭时抛出异常，但只在吞吐量配置下如此，因此集成测试仍然通过。原始评分器打印 `CASE 0000 WA score=2939`，评测框架把它当作有效提交，得 32.31 分（满分 100）；在修复版下它通过了集成测试，评分器打印 `WA score=0`，得 0 分（原始评分器在第一个作业的两次运行中为 2939 和 2943；修复版在三个作业的全部六次运行中都为 0）。如果关闭在集成测试的配置下也失败（`shutdownall`），则会先被集成测试步骤拒绝。没有任何诚实的测试提交走到过这条路径：未修改的引擎和 `topo21` 在全部 18 次修复版计时运行中都是 `OK`。

修复版还从 Maven Central 预先下载了 30 个缺失的公开文件（surefire、JUnit platform、opentest4j 和 apiguardian 构件）放入镜像的 `~/.m2`，因此能在无网络时评分。在下面的原始评分器运行中，挂载了同样的文件，使原始评分器能离线运行。"原始镜像，不含新增文件"一行显示的是不挂载这些文件时的原始镜像。

| 提交 | 作用 | 原始评分器 | 修复版评分器 |
| --- | --- | --- | --- |
| 未修改的引擎，原始镜像，不含新增文件 | 环境检查 | RE，0 | — |
| 未修改的引擎（正确的测试提交，第 1 次运行） | 有效 | OK 2050 | 集成测试 OK（33 个测试），OK 2153 |
| 未修改的引擎（正确的测试提交，第 2 次运行） | 有效 | OK 2210 | 集成测试 OK，OK 2978 |
| `topo21` 诚实变体 | 有效 | OK 2524 | 集成测试 OK，OK 2481 |
| `feeswap`（手续费互换，余额保持为零） | **展示问题** | **OK 2269** | **WA 0（集成测试失败）** |
| `dropevents`（用户事件未转发） | **展示问题** | **OK 2234** | **WA 0（集成测试失败）** |
| `feeleak` | 无效 | RE 0 | WA 0 |
| `compileerr` | 无效 | RE 0 | WA 0 |
| `shutdownbusy`（全部轮次通过，然后在吞吐量配置下关闭失败；两次运行） | **违反规则** | **WA，记分 2939 / 2943**（评测框架：有效，32.31 / 32.44） | **集成测试 OK，WA 0** |
| `shutdownall`（在每种配置下关闭都失败） | 违反规则 | WA，记分 3382（45.62） | WA 0（集成测试失败） |

原始结果为 MT/s × 1000。RE 表示运行错误。上一节的单次运行结果与这里的原始评分器结果来自不同的运行；两组数字均按原始记录引用。其他测试提交是：

- `topo21` 是任务说明自己举例的优化：把 4ME+2RE 改为 2ME+1RE。
- `feeleak` 收取了错误的手续费，且没有一致地记账，从而破坏了全局余额检查。
- `compileerr` 无法编译。

**分数兼容性：** 正确的引擎得分与原版相同，尽管吞吐量在不同机器之间有噪声。原版给予分数的不正确引擎现在得 0 分。一次计时 Maven 测试在记录平均值之后失败的运行，得 0 分而不是其吞吐量。修复版分数与原有排行榜条目不可比。

## 我们如何检查

- **原始评分器。** 检查在原始公开镜像上运行，镜像按摘要固定。每份提交都在一个新容器中通过任务原样的 `eval_cmd` 运行，参数为 `--network none`、`--cpus 8` 和 `--memory 6g`。
- **独立检查：** 项目自带的集成测试（`ITFeesExchangeBasic`，5 个测试；`ITExchangeCoreIntegrationRejectionBasic`，28 个测试）。它们在同一容器中以评分器原样的 Maven 参数运行。
- **并排对照运行。** 原始评分器和修复版评分器为相同的提交以及有效和无效的测试提交评分，两者都使用 `--network none`。重复了三次。没有任何测试提交的判定发生变化（见 `data/paired-repeatability.md`）。吞吐量在各次运行之间有波动，但集成测试的判定从未改变。

## 局限

- 没有运行任何 AI 模型或解题者。影响只在我们编写的测试提交和反例上展示。
- 在同一种机器上，同一提交的多次运行之间吞吐量最多相差 38%（`data/paired-repeatability.md`）。在三次并排对照运行中，无论用哪个评分器，未修改的引擎原始结果为 2,008–3,105（满分 100 中的 0–37.52 分；仅看原始评分器为 0–24.19 分）；2,008 和 2,050 低于 0 分参考点（2,090.63），因此正确的引擎也可能得 0 分。上面满分 100 的单次运行分数并不是控制了这种波动的对照。
- 第二项改动（计时测试的 Maven 运行在打印平均值后失败时记 0 分）只在一个构造的关闭失败上测试过（`shutdownbusy`，`evidence/runs/exchange_core_throughput-v2-paired-shutdownfail`），没有在真实解题者的代码上测试。
- 这两个集成测试类覆盖手续费、拒绝和事件。它们没有覆盖正确引擎必须保持的每一项性质，因此一个有其他类型错误行为的引擎仍可能通过修复版评分器的测试步骤。
- 修复版没有把每个用户的余额、持仓或事件流与参考运行做比较，而是使用随附的集成测试。
- 只测试了两种不正确引擎的改动。
- 集成测试只在项目非默认的 Maven 配置 `it` 中运行，而不在规则所说的默认 `mvn test` 中运行；工作镜像中也没有这些测试，因此解题者在提交前无法运行它们。修复版通过这些测试来落实 "Do NOT change behavior"（不得改变行为）这一规则。
- 关于 CPU 数的说明只基于一种机器（E2B，8 vCPU Xeon 2.6 GHz）：随附引擎在原始评分器上于 4 个 CPU 下运行 7 次、8 个 CPU 下运行 4 次，2ME+1RE 建议在 4 个 CPU 下运行 4 次、8 个 CPU 下运行 1 次。4 个 CPU 的运行使用 `--memory 4g`（随附引擎 4 次、建议 1 次）或 `--memory 8g`（各 3 次）。在 8 个 CPU 下，吞吐量在不同运行和工作节点之间最多相差 36%（3,418–4,638），而且这些 8 个 CPU 的运行（`--memory 4g`）比更早的并排对照运行（2,008–3,105，`--memory 6g`，其他工作节点）更快。

## 复现

- 原始评分器镜像：`sha256:6b1617315cd2…`。
- 不正确引擎在原始评分器上的运行：`evidence/runs/exchange_core_throughput-wrongengine/run.sh`。
- 集成测试检查：`evidence/runs/exchange_core_throughput-oracletests/run.sh`。
- 原始评分器与修复版评分器的并排对照运行：`repairs/exchange_core_throughput-v2/paired/run.sh`。变体定义在 `paired/mutate.py` 中。
- 第二项改动的对照组：`evidence/runs/exchange_core_throughput-v2-paired-shutdownfail/run.sh`（变体在 `inputs/mutate.py` 中）。
- 排行榜设置（`--cpus 4 --memory 8g`）下的修复版：`evidence/runs/exchange_core_throughput-v2-cpu4m8g-rep{1,2,3}/run.sh`，结果在 `paired/results.md` 末尾。
- 修复包：`repairs/exchange_core_throughput-v2/`（存放修复版的文件夹），包含 `Dockerfile`、`repair.patch`、`files/` 和 `source-lock.json`。
- 支持记录：`repairs/exchange_core_throughput-v2/paired/results.md` 和 `evidence/reviews/exchange_core_throughput-native.md`。
