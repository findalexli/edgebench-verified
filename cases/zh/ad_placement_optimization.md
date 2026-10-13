# Ad Placement Optimization (`ad_placement_optimization`)

**结论：** 保留（附说明）。<mark>原始评分器正确地执行了 AtCoder 比赛 AHC001 的规则，没有发现任何会让诚实解题者得分错误的问题。</mark>

## 任务要求

解题者要在 10000x10000 的网格上为每家公司放置一个矩形。题面写道："Each company i wants an ad space containing point (x_i+0.5, y_i+0.5) with area as close to r_i as possible. Maximize the total satisfaction."（每家公司 i 希望得到一块包含其指定点、面积尽量接近 r_i 的广告位；目标是使总满意度最大。）README 写明 "Different rectangles may share edges but must not overlap (common area must be zero)"（不同矩形可以共边，但不得重叠，公共面积必须为零），并且 "Final score = sum of scores across all 50 public test cases"（最终得分为全部公开测试用例得分之和）。类别：组合优化。

## 我们检查了什么

不存在会改变分数的问题。我们检查了决定输出是否合法的各项规则：

- 共边和共角都被接受。例如，测试输出 `edge_touch` 和 `corner_touch` 各得 `Score = 1000000000`，与独立参考实现（"oracle"，即独立判定程序）的结果相同。
- 只要一对矩形中编号较后的那个包含其自身的点，任何正面积的重叠都会被拒绝。这包括单个单位格、被包含的矩形和完全相同的矩形。每一种都被判为 `wrong answer`，理由是重叠。
- 边界、正面积和点包含都被精确检查。
- 超时、运行时错误或错误答案使该用例得 0 分。该用例仍会列出，绝不会被悄悄丢弃。这与 AHC001 系统测试的规则一致。

有一个从比赛代码继承来的顺序问题，但它不会给诚实解题者带来任何好处。在 23 个手写输出中，评分器与参考实现有 1 个不一致。该输出中有一个矩形没有包含它自己的点，因此本来就得 p_i = 0。它的重叠是否被检查，取决于输出中的顺序。AHC001 官方代码的行为相同。重叠本身不得分；解题者最多只能获得原本需要让出的空间，而合法输出可以把这部分空间找回来，代价是每个受影响的公司在每个用例中最多约 0.004 分（满分 100）（`evidence/reviews/ad_placement_optimization.md`，"Does it accept real overlaps?"）。

说明的内容是：

1. 参与评分的 50 个输入是公开生成器的种子 0–49。它们也是 AHC001 官方的示例输入，并没有被保留为隐藏数据。
2. 0–100 分数刻度的两个参考点（"rank30" 和 "rank1"）来自 AtCoder 在其他输入上的成绩。其来源没有核实。
3. 评分器并行运行 `min(nproc,2)` 个用例。`nproc` 不考虑 Docker 的 CPU 配额，而任务也没有设置 `cpu_limit`。因此，有时限的解题者能用到多少算力，取决于评分器所在机器给它多少 CPU。这一影响的大小没有测量。

随任务发布的说明中没有的内容：

- 5 s 的时限是墙钟时间（`eval_ahc.sh` 中的 `timeout 5`）。按约 4.9 s CPU 时间安排预算的解题者（例如使用 `clock()`），在两个用例共用一个 CPU 时需要约 9.8 s 墙钟时间，于是超时，该用例得 0 分。按墙钟时间安排预算的解题者在 `--cpus 1` 下按时完成（见下文的计时检查）。
- 任务文本写明 "Memory limit: 1 GB"（内存上限）。评分器并不执行这一限制：`eval_ahc.sh` 没有设置内存上限，任务也没有设置 `mem_limit`。

## 影响有多大

评分规则对诚实解题者造成的最大分数变化为 0（利用该顺序问题的输出，每个受影响的公司在每个用例中最多多得约 0.004 分）。CPU 分配的影响没有测量：在 CPU 配额少于 2 个的评分器上，按 CPU 时间而非墙钟时间安排预算的解题者可能在每个用例上都超时。说明中的其他事项（输入公开、分数刻度的来源、未执行的内存上限）影响的是应当如何解读分数，而不是任何输出如何被评分。

## 我们如何检查

- **原始评分器，来自按摘要固定的公开镜像。** 运行参数为 `--network none --memory 2g --cpus 2|1`，每次只运行一个容器。七个测试提交，每个用来检验一条规则，在全部 50 个评分用例上运行，得到 350 个逐用例结果。每个逐用例的状态和分数，都与根据 README 编写、用精确分数运算的参考实现的结果相同：

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

- **小型手写输出。** 23 个手写输出经原始评分器程序运行，并与参考实现对照。它们覆盖共边、共角、重叠、越界坐标、零面积、格式错误的记号和各种空白变体。
- **源码对照。** 任务的评分源码与 AHC001 官方可视化工具的评分代码逐条语句一致。唯一的差别在于输入解析和对无效输出的报告方式。
- **计时检查。** 忙等到 4.9 s 墙钟时间的解题者分别在 `--cpus 2` 和 `--cpus 1` 下运行。
- **数据。** 用镜像自带的生成器在种子 0–49 上运行，逐字节重现了全部 50 个评分输入。它们与 AHC001 官方示例输入相同。另一项对输入约束的扫描没有发现违规，也没有逐字节相同的重复。

## 局限

- 没有运行任何 AI 模型或解题者。分数影响只在我们编写的测试提交和反例上展示。
- 评分器程序没有从源码重新构建。源码与程序行为一致，是根据所有被检验分支上的行为一致推断出来的。
- 没有运行真正做优化的解题者，因此 CPU 分配对分数的影响没有测量。计时检查用的是按墙钟时间空转，无法显示对按 CPU 时间安排预算的解题者的影响。
- rank30 和 rank1 参考点的来源，以及它们与种子 0–49 是否可比，没有核实。

## 复现

- 评分器镜像：`sha256:997d10b59ba0…`（完整摘要和关键文件哈希见 `evidence/reviews/ad_placement_optimization.md`）。
- 小型手写输出：`evidence/scripts/ad_placement_optimization/micro/run_micro.sh`（测试数据在 `micro/fixtures.tsv`；结果在 `micro/tester_results.tsv` 和 `micro/oracle_results.tsv`）
- 原始评分器上的测试提交：`evidence/scripts/ad_placement_optimization/native/run_native.sh`，然后运行 `native/compare.py`（输出在 `native/compare_output.txt`）
- 用精确分数运算的参考实现：`evidence/scripts/ad_placement_optimization/oracle.py`
- 数据：`evidence/scripts/ad_placement_optimization/data/regen_in_image.sh` 和 `data/check_constraints.py`
- 完整评分器镜像摘要 和关键文件哈希：`evidence/reviews/ad_placement_optimization.md`
