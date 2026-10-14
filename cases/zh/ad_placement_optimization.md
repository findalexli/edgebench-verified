# Ad Placement Optimization (`ad_placement_optimization`)

**结论：** 保留（附说明）。<mark>原始评分器正确执行了 AtCoder 比赛 AHC001 的规则。我们发现的问题都不会让按规则解题的人得到错误的分数。</mark>

## 任务要求

解题者要在 10000x10000 的网格上为每家公司放一个矩形。题面写道："Each company i wants an ad space containing point (x_i+0.5, y_i+0.5) with area as close to r_i as possible. Maximize the total satisfaction."（每家公司 i 想要一块包含其指定点、面积尽量接近 r_i 的广告位；目标是让总满意度最大。）README 写明 "Different rectangles may share edges but must not overlap (common area must be zero)"（不同矩形可以共边，但不能重叠，公共面积必须为零），并写明 "Final score = sum of scores across all 50 public test cases"（最终得分为全部公开测试用例得分之和）。类别：组合优化。

## 我们检查了什么

没有会改变分数的问题。我们检查了判定输出是否合法的各条规则：

- 评分器接受共边和共角。例如，测试输出 `edge_touch` 和 `corner_touch` 各得 `Score = 1000000000`，与独立参考实现（"oracle"，即独立判定程序）给出的结果相同。
- 一对矩形中，只要编号较后的那个包含自己的点，任何正面积的重叠都会遭到拒绝。单个单位格的重叠、一个矩形套在另一个里面、两个矩形完全相同，这几种情况评分器都判为 `wrong answer`，理由是重叠。
- 边界、正面积和是否包含指定点，评分器都做精确检查。
- 超时、运行时错误或错误答案时，该用例得 0 分。该用例仍会列出，不会悄悄丢掉。这与 AHC001 系统测试的规则一致。

评分代码从比赛代码继承了一个顺序上的小问题，但按规则解题的人不会因此得到任何好处。在 23 个手写输出中，评分器与参考实现只有 1 个结果不同。这个输出里有一个矩形没有包含它自己的点，本来就得 p_i = 0。评分器是否检查它的重叠，取决于输出中矩形的顺序。AHC001 官方代码也是这样。重叠本身不得分。解题者最多只能占到本应让出的空间；合法输出也能拿回这部分空间，代价是每个受影响的公司在每个用例中最多约 0.004 分（满分 100）（`evidence/reviews/ad_placement_optimization.md`，"Does it accept real overlaps?"）。

说明写了三点：

1. 参与评分的 50 个输入是公开生成器的种子 0–49。它们也是 AHC001 官方的示例输入，没有作为隐藏数据保留。
2. 0–100 分数刻度有两个参考点（"rank30" 和 "rank1"），取自 AtCoder 在另一批输入上的成绩。我们没有核实其来源。
3. 评分器同时运行 `min(nproc,2)` 个用例。`nproc` 不考虑 Docker 的 CPU 配额，任务也没有设置 `cpu_limit`。所以，有时限的解题者能用多少算力，取决于评分器所在机器给它几个 CPU。我们没有测量这一影响有多大。

随任务发布的说明没有提到下面两点：

- 5 s 时限按墙钟时间计（`eval_ahc.sh` 中的 `timeout 5`）。如果解题者按约 4.9 s 的 CPU 时间安排预算（例如用 `clock()`），两个用例共用一个 CPU 时，它需要约 9.8 s 墙钟时间，于是超时，该用例得 0 分。按墙钟时间安排预算的解题者在 `--cpus 1` 下按时完成（见下文的计时检查）。
- 任务文本写明 "Memory limit: 1 GB"（内存上限），但评分器并不执行这一限制：`eval_ahc.sh` 没有设内存上限，任务也没有设 `mem_limit`。

## 影响有多大

对于按规则解题的人，评分规则造成的最大分数变化为 0（利用这个顺序问题的输出，每个受影响的公司在每个用例中最多多得约 0.004 分）。CPU 分配的影响没有测量：如果评分器的 CPU 配额少于 2 个，按 CPU 时间而不是墙钟时间安排预算的解题者可能每个用例都超时。说明中的其他几点（输入公开、分数刻度的来源、内存上限没有执行）关系到分数该怎么解读，不影响任何输出的评分。

## 我们如何检查

- **原始评分器，来自按摘要固定的公开镜像。** 运行参数为 `--network none --memory 2g --cpus 2|1`，每次只跑一个容器。我们写了七个测试提交，每个检验一条规则，都在全部 50 个评分用例上运行，共得到 350 个逐用例结果。我们根据 README 写了一个用精确分数运算的参考实现，每个用例的状态和分数都与它的结果相同：

| 测试提交 | 检验的内容 | `TOTAL_SCORE`（评分器 = 参考实现） | `CASES_OK` | 100 分制得分 |
|---|---|---|---|---|
| unit | 单位格，互不接触 | 826577 | 50 | 0.00035 |
| tile_full | 对整个正方形做一刀切（guillotine）划分：每块都与其他块共边、共角，用到坐标 0 和 10000 | 27114970588 | 50 | 11.50 |
| tile_fit | 在各块内放置包含对应点、尺寸向 r_i 靠拢的子矩形 | 38525222727 | 50 | 16.33 |
| overlap1 | 在 tile_full 基础上，每个用例加一处面积为 1 的重叠 | 0 | 0（50 WA） | 0 |
| nocontain | 单位格，公司 0 移离其点 | 824412 | 50 | 0.00035 |
| oob | 公司 0 的 x2 = 10001 | 0 | 0（50 WA） | 0 |
| mixed | 每个用例分别为：2 TLE、7 RE、7 WA、4 CRLF/异常空白、30 正常 | 26265417491 | 34 | 11.14 |

（WA = 错误答案，TLE = 超出时限，RE = 运行时错误。）

- **小型手写输出。** 我们用原始评分器程序运行了 23 个手写输出，并与参考实现对照。它们覆盖共边、共角、重叠、越界坐标、零面积、格式错误的记号和各种空白写法。
- **源码对照。** 任务的评分源码与 AHC001 官方可视化工具的评分代码逐条语句一致，只在输入解析和无效输出的报告方式上有差别。
- **计时检查。** 一个忙等到 4.9 s 墙钟时间的解题者，分别在 `--cpus 2` 和 `--cpus 1` 下运行。
- **数据。** 用镜像自带的生成器跑种子 0–49，逐字节重现了全部 50 个评分输入，它们与 AHC001 官方示例输入相同。另外扫描了输入约束，没有发现违规，也没有逐字节相同的重复输入。

## 局限

- 我们没有运行任何 AI 模型或解题者。分数影响只在我们自己写的测试提交和反例上展示。
- 我们没有从源码重新构建评分器程序。源码与程序行为一致，这一点是从所有检验过的分支上行为都相同推断出来的。
- 我们没有运行真正做优化的解题者，所以 CPU 分配对分数的影响没有测量。计时检查用的是按墙钟时间空转，看不出对按 CPU 时间安排预算的解题者有什么影响。
- rank30 和 rank1 两个参考点的来源，以及它们能否与种子 0–49 相比，我们没有核实。

## 复现

- 评分器镜像：`sha256:997d10b59ba0…`（完整摘要和关键文件哈希见 `evidence/reviews/ad_placement_optimization.md`）。
- 小型手写输出：`evidence/scripts/ad_placement_optimization/micro/run_micro.sh`（测试数据在 `micro/fixtures.tsv`；结果在 `micro/tester_results.tsv` 和 `micro/oracle_results.tsv`）
- 原始评分器上的测试提交：`evidence/scripts/ad_placement_optimization/native/run_native.sh`，然后运行 `native/compare.py`（输出在 `native/compare_output.txt`）
- 用精确分数运算的参考实现：`evidence/scripts/ad_placement_optimization/oracle.py`
- 数据：`evidence/scripts/ad_placement_optimization/data/regen_in_image.sh` 和 `data/check_constraints.py`
- 完整评分器镜像摘要和关键文件哈希：`evidence/reviews/ad_placement_optimization.md`
