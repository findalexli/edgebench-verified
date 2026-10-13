# Triangulation Coloring Optimization (`triangulation_coloring_optimization`)

**结论：** 已修复。<mark>评分器判定合法边翻转的规则漏掉了 README 中的凸性条件；全部十个隐藏输入都是用同一规则生成的，其中含有重叠或折叠的三角形，而这一规则还决定提交中的哪些操作被接受。另外，在发布方 4 个 CPU 的评分器上，一个每个用例使用超过约 15 s CPU 的有效解法会超时，尽管 README 承诺每个用例 30 s，而只要有一个用例超时，整份提交就没有分数；修复版还让同时运行的用例数不超过评分器的 CPU 数。</mark>

![示意图：一个带凹角的飞镖形四边形，翻转其内部的边会使两个新三角形重叠；原始评分器接受这次翻转并为其计分（在四点测试输入上得 41），修复版则以无效翻转拒绝它。在真实的隐藏用例 0009 上，一次被禁止的翻转使分数从 644,809 降到（即改进到）641,611。](figures/triangulation_coloring_optimization.svg)

*原始评分器接受规则所禁止的翻转，其中一次甚至改进了分数（越低越好：在隐藏用例 0009 上从 644,809 降到 641,611）；修复版拒绝这些翻转。*

## 任务要求

输入是 N = 512 个点的 "a **triangulation**"（一个**三角剖分**）：一张覆盖这些点、彼此不重叠的三角形网格。智能体通过给点重新着色和翻转边来降低分数。README 这样定义翻转操作："if an edge is a diagonal of a **convex quadrilateral** formed by two adjacent triangles, replace it with the other diagonal. The result remains a valid triangulation."（如果一条边是由两个相邻三角形构成的**凸四边形**的对角线，就把它替换为另一条对角线；结果仍是有效的三角剖分。）

任务说明写道 "The local `tester` applies flips exactly like the judge"（本地测试程序应用翻转的方式与评测完全相同）。分数在 "on the **final** triangulation after all flips"（所有翻转之后的**最终**三角剖分上）计算。类别：组合优化。

## 问题出在哪里

**规则。** 只有凸四边形的对角线才能合法翻转。共享库中的 `Triangulation.is_flippable` 只检查两个顶点（两个三角形各自的远端顶点）位于公共边的两侧。它从不检查公共边的两个端点是否位于新对角线的两侧。因此它接受非凸四边形的翻转，而这些翻转会使网格折叠。

**对输入的影响。** `gen.py` 用这一规则施加 K 次随机翻转来构建每个用例。全部十个隐藏输入都含有重叠的三角形，每个用例有 17 到 583 对重叠的三角形。其中六个还含有重复的三角形和非流形边（被超过两个三角形共享的边）。不做翻转（K=0）时，生成器的原始输出没有重叠。

**对计分的影响。** 同一规则也是官方评分器的操作规则：

- 在每个隐藏用例上，有 317–379 条内部边能通过官方规则，但并不是凸四边形的对角线。README 禁止翻转这些边。
- 没有任何凸四边形翻转被拒绝。官方规则允许文档规则允许的一切，而且允许得更多。
- **原始评分器下的例子（用例 0009）：** 随附的什么都不做的输出得 `Score = 644809`（U=803）。加上一次 README 禁止的非凸翻转（边 39–52）后，它被接受，得分为 `Score = 641611`（U=801）。一次被禁止的操作改进了官方分数（越低越好）。
- **最小例子（N=4）：** 输入是一个有效的两三角形网格，其四边形有一个优角（向内凹的）顶点。原始测试程序接受这次被禁止的翻转（`Score = 41`），得到的两个三角形相互重叠。这个问题并不依赖于有缺陷的输入。

**在 4 个 CPU 的评分器上，每个用例的 30 s 缩水为约 15 s 的 CPU 时间。** README 写明 "Time limit: **30 seconds per case**"（第 50 行）。评分器 `/tmp/eval_triangulation_coloring.py` 同时运行 8 个用例（`max_workers=min(8, len(case_files))`，第 44 行），墙钟时限为 30 s（`TIME_LIMIT = 30`，第 9 行）；超时的用例得 `float('inf')`（第 36 行），这使整份提交没有 100 分制得分（`sforge/harness/score_rescale.py:75-76`）。任务没有设定 CPU 数。在 EdgeBench 的排行榜配置 `examples/all-tasks-k8s/experiment.yaml`（引文见 [`evidence/impact/edgebench-leaderboard-config.md`](../evidence/impact/edgebench-leaderboard-config.md)）（sha256 `d9d299794ba946cae8d2b7f68a7879a35bb8565d95e78107edf79802993643be`）中，评分器继承 `judge_cpu_limit: 4`，因此前 8 个用例各约分到半个 CPU。我们在原始评分器上以 `--cpus 4` 测量（`evidence/runs/triangulation_coloring_optimization-cpu4v8-a/result/out/summary.txt`、`-b`），使用诚实的 `greedy.py` 对照解法，并在其后附加固定量的 CPU 计算：每个用例 12 或 14 s 时 10/10 通过；每个用例 20 s 时，两个工作节点上都是 2 个 OK、8 个 TLE，`TOTAL_SCORE inf`。在 `--cpus 8` 下，20 s 的解法以 866,166（100 分制下 48.87 分）10/10 通过。一个在 25 s 墙钟截止时间停止的解法，在 4 个 CPU 下每个用例平均得到 15.00 s CPU（中位数 12.62 s；10 个用例中有 2 个在最后单独运行），在 8 个 CPU 下为 24.97 s。

**限制危害的因素。** 智能体的工作镜像随附了同样的 `verifier.py`、`tester` 和样例。因此智能体的本地测试看到的恰好是评分器的规则，分数是一致且可重复的。危害在于，被计分的问题与文档描述的问题不同。

## 影响有多大

**CPU 数。** 在发布方的 4 个 CPU 下，一个每个用例使用约 15–30 s CPU 的有效解法在原始评分器下会失去全部分数（用每个用例 20 和 28 s 测得）。在修复版下它能得到分数。一个在墙钟截止时间停止的解法，在修复版下每个用例得到约两倍的 CPU（对 25 s 截止时间，平均从 15.00 s 增至 24.91 s）；这会使其分数改变多少，没有测量。

**翻转规则。** 该规则改变了每个解题者能合法进行的翻转，而隐藏输入对每个解题者都是折叠的。唯一测得的分数影响是用例 0009 上的一次被禁止的翻转，它使该用例从 644,809 降到 641,611（对于什么都不做的输出，10 个用例的总分约为 609 万）。诚实的贪心测试提交在不同的输入上从 48.87 变为 48.95 分（满分 100）。对于一个强解题者在完整优化中的影响大小，没有测量。

## 修复

修复版在评分器镜像和智能体工作镜像中都改动了 `tools/src/triangulation.py` 中的 `is_flippable`。它现在还要求 `a != b`、边 ab 尚不存在，并且公共边的两个端点严格位于新对角线的两侧。文件中的其他内容都不变。

随后，用随附的、未经修改的 `gen.py` 和 `delaunay.py` 加上修复后的规则，重新生成了 10 个隐藏用例和 3 个样例：

- 用例 0000 和样例保留原来的种子（9000000 和 1000001–1000003）。
- 用例 0001–0009 使用新种子 9000001–9000009，因为原来的种子未知。K 根据每个用例的缺陷模式推断。

修复版还改动了 `/tmp/eval_triangulation_coloring.py`，使其同时运行的用例数不超过评分器 CPU 配额所允许的数量：新函数 `cpu_quota_workers()`（与 `repairs/grid_turing_robot-v2/` 中的相同）读取 cgroup 配额（`cpu.max`，或 cgroup v1 的配额和周期），向下取整为整数个 CPU，在没有配额时退回到 `os.cpu_count()`，并把结果限制在 1 到 8 之间；进程池变为 `ProcessPoolExecutor(max_workers=min(cpu_quota_workers(), len(case_files)))`。在 8 个或更多 CPU 下，它同时运行 8 个用例，与原始版完全相同。

以下内容不变：`verifier.py`、`tester`、各 README、任务说明、解析器、每个用例 30 s 的时限、1200 s 的 `eval_timeout`，以及分数刻度的参考点。

- 在 13 个修复后的输入上，修复后的规则在每条边上都等价于严格凸四边形检验。它只允许旧规则允许过的翻转，也不禁止任何 README 允许的翻转。Lean 证明覆盖所有有效的三角剖分。
- `v2/rule_check.py` 中的对照检验也包含修复后规则的两个新防护条件（`a != b`，以及边 ab 尚不存在），因此仅凭它本身无法说明这两个防护条件什么也不拒绝。去掉它们后，在每个原始隐藏用例上，`flip_rules.jsonl` 中的凸性计数（`convex_flippable`）都超过 `rule_check.jsonl` 中的计数。在隐藏用例 0000–0009 上，修复后的规则会分别拒绝 2、1、2、2、2、19、17、24、20 和 23 次严格凸的翻转，因为在折叠的网格中其另一条对角线已经存在（例如用例 0009 中，边 79–156，顶点为 15 和 497）。这样的边在有效的三角剖分中不可能出现，而修复版随附的是重新生成的有效输入，因此这不影响修复版。它意味着，如果只把规则修复应用到原始输入上，会禁止少数几次严格凸四边形的翻转，而这些翻转的结果会与一条已有的边重复。
- 在原始输入上，规则修复使每个隐藏用例减少 319–398 条可翻转的边（`rule_check.jsonl` 中原始计数减去修复后计数）。这比上文的 317–379 条非凸边略多，多出的正是刚才所说的被防护条件拦下的凸边。

完整评分器（`eval_cmd`，10 个隐藏用例）。原始结果越低越好。

| 提交 | 角色 | 原始评分器，原始结果 | 原始评分器，OK 的用例 | 原始评分器，100 分制 | 修复版评分器，原始结果 | 修复版评分器，OK 的用例 | 修复版评分器，100 分制 |
|---|---|---:|---|---:|---:|---|---:|
| 随附的 `solution.py`（什么都不做） | 正确的测试提交 | 6,092,430 | 10/10 | 0.055 | 6,092,622 | 10/10 | 0.054 |
| `greedy.py`（贪心重新着色 + 贪心地做 README 允许的凸翻转） | 独立的诚实测试提交 | 866,166 | 10/10 | 48.87 | 863,058 | 10/10 | 48.95 |
| `nonconvex_flip.py`（什么都不做 + 每个用例一次 README 禁止的非凸翻转） | **展示问题** | 6,093,050 | 10/10 被接受 | 0.052 | inf | 0/10（WA "Invalid flip"） | 无（原始结果 inf） |
| `wrong_count.py`（给顶点 1 重新着色，却声称 C=0） | 无效的测试提交 | inf | 0/10 (WA) | 无（原始结果 inf） | inf | 0/10 (WA) | 无（原始结果 inf） |

相同输入，只看规则：

| 输入 | 原始测试程序 | 修复版测试程序 |
|---|---|---|
| N=4 的有效 2 三角形输入，含优角四边形，翻转 1–2（来自审查的测试提交） | 被接受，`Score = 41`（结果重叠） | `wrong answer: Invalid flip (1,2)` |
| 每个修复后的隐藏用例 + 原始规则允许的第一条非凸边（10 个输入） | 10/10 被接受 | 10/10 `Invalid flip` |

智能体的本地测试流程（工作镜像）：

| 提交 | 原始 SAMPLE_TOTAL | 修复版 SAMPLE_TOTAL |
|---|---:|---:|
| 什么都不做 | 1,780,251 | 1,802,171 |
| greedy | 263,500 | 258,183 |
| nonconvex_flip | 1,780,471（被接受） | 3 个全部 `wrong answer: Invalid flip` |

保存下来的用例 0009 输出含有那次能改进分数的被禁止翻转，它在原始验证器下得 `Score: 641611`；换用修复后的 `triangulation.py` 时则给出 `INVALID: Invalid flip (39,52)`。全部 13 个重新生成的输入都有 0 对重叠、0 处交叉、0 处折叠、0 个重复或退化三角形，以及 0 条非流形边。

CPU 份额：在 `--cpus 4` 下（另有一组在 `--cpus 8` 下），对相同的解法并排对照运行原始评分器、上一版修复（只有翻转规则和重新生成的输入）和修复版（`evidence/runs/triangulation-v2-paired-cpu/result/out/summary.txt`；`repairs/triangulation_coloring_optimization-v2/paired/results.md` 的 "CPU-quota parallelism" 一节）。原始评分器对原始用例评分，两个修复版本对重新生成的用例评分，因此有效的总分不同（866,166 对 863,058）。

| 解法（诚实的 `greedy.py` 输出，之前附加固定计算量） | CPU 数 | 原始评分器 | 上一版修复 | 修复版 |
| --- | ---: | --- | --- | --- |
| 没有额外计算 | 4 | 10 OK，866,166 | 10 OK，863,058 | 10 OK，863,058 |
| **每个用例 20 s CPU** | 4 | **2 OK，8 TLE，`inf`（无分数）** | **2 OK，8 TLE，`inf`** | **10 OK，863,058 (48.95)** |
| **每个用例 28 s CPU** | 4 | **2 OK，8 TLE，`inf`** | **2 OK，8 TLE，`inf`** | **10 OK，863,058** |
| 计算到 25 s 墙钟截止时间 | 4 | 10 OK，866,166；每个用例平均 15.00 s CPU | 10 OK，863,058；平均 15.00 s | 10 OK，863,058；平均 24.91 s |
| 每个用例 40 s CPU（错误对照） | 4 | 10 TLE，`inf` | 10 TLE，`inf` | 10 TLE，`inf` |
| 每个用例 20 s CPU | 8 | 10 OK，866,166 | 10 OK，863,058 | 10 OK，863,058 |

上一版修复与原始版一样让 20 s 和 28 s 的解法失败，因此恢复它们的是并行度的改动，而不是翻转规则。在修复版下，最慢的 28 s 用例耗时 28.03 s；错误对照的评分耗时 90.5 s（3 轮 × 30 s），在 1200 s 的 `eval_timeout` 之内。上面各表中所有较早的对照，在修复版上以 `--cpus 8` 和 `--cpus 4` 都完全复现（`evidence/runs/triangulation-v2-paired-cpu-controls`），而修复版镜像与上一版修复的区别只在 `/tmp/eval_triangulation_coloring.py`。

**分数兼容性：** 修复版分数与原始分数**不可比**，原因有四：

- 10 个隐藏输入中有 9 个是新实例。
- 所有输入现在都是有效的三角剖分。
- 合法操作的集合变小了。
- 在评分器 CPU 少于 8 个时，一直搜索到墙钟截止时间才停止的解法，每个用例能得到更多 CPU（在 4 个 CPU 下约为两倍）。

分数刻度的全部四个原始参考点都保持不变，仅作为一个固定的参照刻度。在修复版上，它们不再对应排行榜上的名次。

## 我们如何检查

- **原始评分器。** 原始的 `tools/bin/tester` 和完整的原始 `eval_cmd` 在按摘要固定的原始公开镜像中以 `--network none` 运行，分别针对原始版和修复版。
- **独立检查。** 在全部 10 个隐藏用例和全部 3 个样例上运行精确的整数几何计算，不使用浮点数。它涵盖：对每对三角形的精确分离轴重叠检验；真正的边交叉；位于三角形内部的顶点；重复、退化和非流形的三角形与边；欧拉示性数和顶点链接（检验网格是否为正常曲面的两项标准检查）；相对凸包的面积超出；以及三点共线。在每条内部边上，把官方规则与一个独立的精确凸四边形检验做了比较。
- **重新生成。** 随附的 `gen.py` 用种子 9000000 能逐字节复现隐藏用例 0000。种子 1000001–1000003 能逐字节复现全部三个样例。（O(N³) 的共线检查被替换为一个完全等价的更快检验。）
- **可重复性。** 原始版和修复版评分器的并排对照运行重复了三次，结论没有变化（`data/paired-repeatability.md`）。
- **在 E2B 上的 CPU 运行和并排对照运行。** 固定计算量的解法（每个用例 12 到 28 s）、一个 25 s 墙钟截止时间的解法和一个 40 s 的错误对照，在原始评分器上以 `--cpus 4` 和 `--cpus 8` 运行（`evidence/runs/triangulation_coloring_optimization-cpu4v8-a`、`-b`），并在原始评分器、上一版修复和修复版上并排对照运行（`evidence/runs/triangulation-v2-paired-cpu`、`-cpu-controls`），每个作业都是 `status: exit=0`，参数为 `--network none --memory 4g`。每个解法都记录自己在每个用例上的开始、结束时间和 CPU 时间（`result/out/timing/`）。

## 局限

- 修复版评分器从 cgroup（`cpu.max`）读取其 CPU 配额。这只用 `docker run --cpus` 测试过，没有在 Kubernetes pod（EdgeBench 排行榜设置所用的后端）中测试。
- 没有运行任何 AI 模型或解题者。分数影响只在我们编写的测试提交上展示。
- 隐藏用例 0001–0009 原来的种子未知。它们的 K 是推断的，而不是恢复出来的。
- 随附的 Delaunay 生成器的一个副作用（其“超级三角形”构造）没有处理。13 个修复后的输入中有 12 个缺少 1–3 个凸包三角形。每个输入都是覆盖全部点的有效三角剖分多边形，但没有覆盖整个凸包。README 的措辞 "a triangulation of those points"（这些点的一个三角剖分）比这略强。这一措辞已记录，但没有改动。
- 没有查阅 CodeChef TRICOL 的题面和检查器。
- 没有测量强解题者在完整优化中从非凸翻转获得的收益。
- CPU 依赖性是在 4 和 8 个 CPU 下、用单线程的固定计算量和截止时间测试解法测量的。多线程的解题者没有测试。在 4 个 CPU 下，采用按截止时间停止策略的解题者在修复版中每个用例得到更多 CPU，因此其分数不可比；变化多少没有测量。配额是向下取整的：2.5 个 CPU 时同时运行 2 个用例。
- 修复版镜像是为这次运行在本地构建和测试的，之后已删除。因此没有镜像仓库中的摘要（digest）。

## 复现

- 几何和规则分析：`evidence/scripts/triangulation_coloring_optimization/check_geometry.py`、`flip_rule_analysis.py`、`regen_compare.py`、`run_gen.py`
- 修复版的重新生成和规则检查：`evidence/scripts/triangulation_coloring_optimization/v2/regen_v2.py`、`v2/rule_check.py`
- 并排对照运行：`repairs/triangulation_coloring_optimization-v2/paired/run.sh`（结果在 `paired/results.md`）；CPU 份额：`paired/run-cpu4.sh`（实际运行版本：`evidence/runs/triangulation-v2-paired-cpu/run.sh`）；在原始评分器上的 CPU 运行：`evidence/runs/triangulation_coloring_optimization-cpu4v8-a/run.sh`、`-b`
- 修复版评分器 `/tmp/eval_triangulation_coloring.py`：sha256 `082d72b2…acb1`（原始版 `1c5100f5…c009`）
- 补丁：`repairs/triangulation_coloring_optimization-v2/repair.patch`
- 固定标识：评分器镜像 `seededge/edgebench.judge.triangulation_coloring_optimization@sha256:beeea763…dcf671`；`triangulation.py` 的 sha256 为 `32862fe5…`；`verifier.py` 为 `1f0c714a…`；`gen.py` 为 `67201f1e…`；`tools/bin/tester` 为 `01b6e17b…`；隐藏用例 0000 为 `8e0c5efc…`。

支撑记录：`repairs/triangulation_coloring_optimization-v2/`（存放修复版的文件夹：source-lock.json、并排对照运行的日志）。
