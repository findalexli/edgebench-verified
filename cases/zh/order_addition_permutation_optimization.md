# Order Addition Permutation Optimization (`order_addition_permutation_optimization`)

**结论：** 已修复。<mark>一项文件完整性测试期望的是某个辅助文件过时的指纹，因此每份提交都会在五项测试中失败一项；按照本任务挑选一次运行最佳提交的规则，这次运行会一直停留在第一份有效提交上，而忽略之后更好的提交。</mark>

![两行展示同样的两份有效提交：原始评分器把得分较低的第一份当作最佳，而修复版保留更好的第二份。](figures/order_addition_permutation_optimization.svg)

*一个过时的文件指纹使每份提交最多只能通过 4/5 项测试，因此原始评分器保留一次运行的第一份有效提交，而忽略之后更好的提交。*

## 任务要求

任务说明要求给出 1..1000 的一个排列（一种排序），使一个黑箱响应最小。它列出了 "the evaluator will check"（评测器将检查）的内容：不访问私有内容；基线文件未被修改；`final_result.txt` 存在；`final_pai` 是一个有效排列；`final_cost` 与重新计算的成本一致。

随后，连续分数 "calculated using `score_cost_num(cost, num)` from the evaluator-side private `tests/score_vcpom_result.py`"（使用评测器一侧私有文件中的计分函数计算）。约定中没有任何地方提到辅助文件的指纹。解题者也无法影响它，因为 `tests/` 不包含在提交中。类别：组合优化。

## 问题出在哪里

**有一项测试总是失败。** `test_private_judge_files_are_available` 断言已安装辅助文件的 sha256 指纹等于 `3023b9a4…`。这是早先一个带中文注释的辅助文件的指纹。后来的一个镜像层把辅助文件替换成了英文注释的译本 `337837af…`，而期望值没有更新。两个版本的辅助文件只在注释、一个文档字符串和示例标签上不同；`parse_result_file` 和 `score_cost_num` 的行为完全相同。这项检查是无条件的，对每份提交都会失败。

- **每份提交的分数是正确的。** 只有这一项测试失败。其余四项照常运行，`TOTAL_SCORE` 用已安装的辅助文件计算。
- **通过率被封顶。** 一份完全正确的提交得到的通过率是 0.8，而不是 1.0。
- **一次运行的最佳提交选择被冻结。** 本任务的规则（`pass_rate_first`）保留通过测试最多的提交。只有当两份提交的通过率都是 1.0 时，它才比较分数；否则，较晚的提交只有在通过率严格更高时才胜出。每份有效提交都被封顶在 0.8，因此这次运行的 `best_score` / `best_round` 停留在**第一份**有效提交上。

原始评分器下的例子：两份有效提交，先是恒等排列，然后是搜索结果。恒等排列得分 3.3e-09，搜索结果得分更高。预期：选中搜索结果。实际：选中恒等排列，之后更好的提交被忽略。

## 影响有多大

对于任何有不止一份有效提交、且较晚的提交得分更高的运行，这会改变其记录的分数：之后的改进在这次运行的最佳分数中被忽略。有些使用方改为取所有提交的最大值，这与顺序无关。因此，一个已发布的数字是否有误，取决于是哪个使用方得出的。每份提交自身的分数不受影响。

## 修复

修复版只改动 `tests/test_final_result.py` 中的一个值：`EXPECTED_SCORE_HELPER_SHA256` 改为已安装辅助文件的指纹 `337837af…`。以下内容不变：辅助文件、`.so`、基线文件、任务说明、智能体的工作镜像、解析器、挑选最佳提交的规则和分数刻度。任务 JSON 只改动 `judge.image_tag`。

| 提交 | 角色 | 评分器 | 通过的测试 | pass_rate | 原始 TOTAL_SCORE | 100 分制得分 | 失败的测试 |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| identity | 有效 | 原始版 | 4/5 | 0.80 | 3.3e-09 | 3.3e-09 | 指纹 |
| identity | 有效 | 修复版 | **5/5** | **1.00** | 3.3e-09 | 3.3e-09 | – |
| search | 有效，更好 | 原始版 | 4/5 | 0.80 | 0.0093733018 | 0.0093733018 | 指纹 |
| search | 有效，更好 | 修复版 | **5/5** | **1.00** | 0.0093733018 | 0.0093733018 | – |
| badcost（谎报成本） | 无效的测试提交 | 原始版 | 3/5 | 0.60 | 无 | 无 | 指纹、成本不符 |
| badcost | 无效的测试提交 | 修复版 | 4/5 | 0.80 | 无 | 无 | 成本不符 |
| dup（不是排列） | 无效的测试提交 | 原始版 | 3/5 | 0.60 | 无 | 无 | 指纹、排列 |
| dup | 无效的测试提交 | 修复版 | 4/5 | 0.80 | 无 | 无 | 排列 |

一次运行的最佳提交选择（任务规则 `pass_rate_first`，用 EdgeBench 的 `select_best` 计算）：

| 提交顺序 | 原始评分器选中 | 修复版评分器选中 |
| --- | --- | --- |
| identity, search | **identity**（3.3e-09），卡在第一份 | **search**（0.00937） |
| search, identity | search（0.00937） | search（0.00937） |
| dup, identity, search | **identity**（3.3e-09） | **search**（0.00937） |
| badcost, identity, search | **identity**（3.3e-09） | **search**（0.00937） |

**分数兼容性：** 每份提交的原始结果和 100 分制得分逐位不变。通过率会改变：合法提交现在得到 5/5，而不是 4/5。只要一次运行有不止一份有效提交、且较晚的一份得分更高，`pass_rate_first` 下这次运行的 `best_score` / `best_round` 就与原始版不可比：原始版保留第一份，修复版保留最佳的一份。

## 我们如何检查

- **原始评分器。** 在按摘要固定的原始公开镜像中对已安装的辅助文件计算哈希，并与测试期望的值比较。原始 `eval_cmd`（`python -m pytest tests/test_final_result.py -s -v`）在 `--network none --memory 2g --cpus 2` 下对有效和无效的测试提交运行。
- **最佳提交选择。** 保存的日志依次送入测试框架自己的 `grade_output`、`rescale_score` 和 `select_best`，它们来自 EdgeBench 的测试框架（`sforge`，版本 `6e4e5f4`）。
- **形式化检查（TLA+）。** 选取规则的一个有界模型逐行对应 `selection.py` 和 `grading.py`，已模型检验：5,421,361 个状态，没有违例；另有三个配置（`k1`–`k3`）如说明所述出现违例（`evidence/formal/tla/order_addition_permutation_optimization/`、`evidence/formal/notes/order_addition_permutation_optimization.md`）。
- **原始版与修复版评分器的并排对照运行。** 每份提交都在一个全新的 `--network none` 容器中通过 TaskSpec 的 `eval.sh` 运行。事先检查确认每个镜像都收集到 5 项测试。共重复三次，结论没有变化（[`data/paired-repeatability.md`](../data/paired-repeatability.md)）。

## 局限

- 没有运行任何 AI 模型或求解器。影响只在我们编写的测试提交和反例上展示。
- 这些提交很简单：恒等排列，以及短时间的随机交换搜索（30 s 和 60 s）。它们离参考成本很远。对最佳提交选择的影响与分数大小无关。
- 最佳提交选择是用 EdgeBench 的 `select_best` 在保存的报告上计算的，而不是在实际运行的 `judge_server` 上得出的。智能体的工作镜像没有运行。
- 没有测量过去排行榜上的运行中有多少次出现了之后更好的提交。
- 修复还改变了测试框架的一个回退行为。当被选中的提交没有分数时，`pass_rate_first` 报告 `best_score = pass_rate`（`sforge/harness/selection.py`，`_pass_rate_first`）。因此，只有无效提交的运行（例如 badcost）在原始版下报告 0.6，在修复版下报告 0.8。在两个版本中，这个值都高于这里测得的每份有效提交的分数（100 分制下 3.3e-09 到 0.0094，见上表），所以一次全部无效的运行报告的 `best_score` 比这些有效运行更高。

## 复现

- 原始评分器镜像：`sha256:6d1a1506…`。
- 脚本：`evidence/scripts/order_addition_permutation_optimization/run_judge.sh`、`make_result.py`、`grade_and_select.py`；保存的日志位于 `observed/`。
- 并排对照运行：`repairs/order_addition_permutation_optimization-v2/paired/run.sh`（结果位于 `paired/results.md`）。
- 补丁：`repairs/order_addition_permutation_optimization-v2/repair.patch`。
- 支撑记录：`repairs/order_addition_permutation_optimization-v2/`（存放修复版的文件夹：source-lock.json、并排对照运行的输出记录）。
