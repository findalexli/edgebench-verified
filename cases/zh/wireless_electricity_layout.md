# Wireless Electricity Layout (`wireless_electricity_layout`)

**结论：** 保留（附说明）。<mark>在上游测试框架下，一个编译失败的程序可能按原始结果被报告为最佳提交，但这永远不会改变 100 分制得分。</mark>

## 任务要求

智能体改进一个现成的、用于求解布局谜题的 C++ 程序。任务说明写道："Your solution is scored on **50 fixed hidden test cases**. Final score = sum of (P+Q) across all hidden cases. **Lower is better.**"（大意：解法在一组**固定的隐藏测试用例**上计分，最终分数为所有隐藏用例上 (P+Q) 之和，**越低越好**。）它还写道："A valid baseline `solution.cpp` already exists. Improve it."（已有一个有效的基线程序，请改进它。）

评分器对各用例分数求和（`score_sum` 解析器），并以低为好（`minimize`）。一次运行保留分数最好的提交（`score_first` 选取规则）。原始结果（换算为 0–100 分之前）通过分段对数刻度（`piecewise_log_min`）换算为 100 分制得分。其参考点依次为 baseline 2.606e16、rank30 2.445e15、rank1 3.624e14 和 super_anchor 1.812e14。任务说明对失败的惩罚只字未提。类别：组合优化。

## 我们检查了什么

**规则。** 原始评分器对两类失败的惩罚不同：

- 文件缺失或编译失败只得到**一行**惩罚，`CASE 0000 CE score=1e17`，并且 `TOTAL_SCORE 1e17`。
- 每个用例的超时、运行时错误或答案错误，**每个用例**都加上 `1e17`。

**只要有一个用例失败，整份提交在 100 分制下就得 0 分。** 一个失败的用例会使原始总分达到或超过 1e17，这高于 baseline 参考点（2.606e16），因此该提交得 0 分（`eval_wirel.sh`，`BAD_SCORE=100000000000000000`；`piecewise_log_min` 在 baseline 参考点及以上返回 0）。任务说明只说 "Final score = sum of (P+Q) across all hidden cases"（最终分数为所有隐藏用例上 (P+Q) 之和），并没有说明失败的用例记多少分。时限是每个用例 5 s 墙钟时间（`TIME_LIMIT=5`，`timeout`），同时运行 2 个用例（`MAX_JOBS=2`），且没有为评分器设置 CPU 限制（`tasks/wireless_electricity_layout.json` 中没有 `cpu_limit`）。因此，一个运行时间接近 5 s 的解题者是否超时，取决于评分器所在的机器。在 `score_first` 下，更早的、没有失败用例的提交仍会被保留。这一影响没有测量。

**随附的基线得 0 分。** 它的原始总分 6.631e17（`observed/baseline.log`）是 baseline 参考点 2.606e16 的 25.4 倍，因此任务说明所提供的"有效基线"在 100 分制下得 0 分。参考点从何而来，任务中没有说明，我们也没有检查。

**例子。** 随附的、能正常工作的基线总分超过 1e17。因此按原始单位，它的排名还低于一个无法编译的程序。预期：一个能工作的解法应排在编译失败之前。原始评分器下的实际结果：

| 提交 | 原始评分器输出 |
|---|---|
| `baseline`：**随附的**基线，未作改动 | 50/50 OK，`TOTAL_SCORE 663100735542396309`（6.63e17） |
| `ce`：无法编译 | `CASE 0000 CE`，`TOTAL_SCORE 100000000000000000`（1e17），`CASES_TOTAL 50` |
| `re_some`：在 8 个用例上中止的基线 | 42/50 OK，`TOTAL_SCORE 1356919142089112260`（1.36e18） |

- **上游测试框架。** 编译失败的报告是有效的，原始结果为 1e17，100 分制得分为 0.0。在测试过的每种顺序中，它都会被选中，排在随附基线和 `re_some` 之前。所有这些提交在 100 分制下都得 0.0 分。

**为什么它不会改变分数。** 分数刻度从不随原始结果的增大而上升，并且对任何达到或超过 baseline 参考点（2.606e16）的原始总分都等于 0。编译失败的总分 1e17 高于该点。只有当其他每份提交的原始总分都至少为 1e17 时，编译失败才可能被选中，而那些提交在 100 分制下同样得 0 分。这个问题只影响以原始单位报告的结果，以及哪份提交被称为"最佳"。

**随任务发布的说明。** 在原始评分器中，编译失败总共只受到一次 1e17 的惩罚，而每个失败的用例都受到 1e17 的惩罚。因此在上游测试框架下，一份无法编译的提交可能按原始结果被选为最佳，排在一份能工作但很差的提交（包括随附基线）之前。这永远不会改变 100 分制得分，因为所有这样的原始总分都换算为零。

## 影响有多大

编译失败规则的最大分数影响：100 分制下 0 分。只有当解题者最好的可工作提交的原始总分也至少为 1e17 时，他才可能看到编译失败按原始结果被称为最佳，而这样的解题者无论如何在 100 分制下都得 0 分。

一个用例失败就让整份提交失去全部分数，这种全有或全无的影响来自另一条未披露的规则。例如，在较慢的评分器上有一个用例超时，就会出现这种情况；其影响大小没有测量。

任务本身不作改动；上述说明随任务一起发布。

## 我们如何检查

- **原始评分器。** 原始的 `eval_wirel.sh` 在按摘要固定的原始公开镜像中以 `--network none` 运行，针对上述三份提交。
- **测试框架评分。** 保存的日志用真实的测试框架函数评分（`grade_output` → `rescale_score` → `select_best`）。使用的是 EdgeBench 测试框架 `6e4e5f4` 版本（`sforge/`，哈希见 `sforge/UPSTREAM.lock`）。
- **论证和随机检查。** 根据分数刻度和选取规则的源码，一个简短的论证说明 100 分制得分不可能改变。我们在 200,000 个随机提交历史上通过上游代码检验了这一点，并在每个位置插入一份编译失败的提交。结果：被选中的 100 分制得分有 **0** 次改变，最高 100 分制得分有 0 次改变，而原始的 `best_score` 有 43,336 次改变。
- **形式化证明（Lean 4）。** `evidence/formal/lean/ebv/Ebv/WirelessCeInvariance.lean`（输出 `WirelessCeInvariance.out`，`lean exit=0`，只使用标准公理）证明了 `selected_norm_invariant`、`bestMax_invariant` 和 `task_ce_invariant`：在一个非空的提交历史中任意位置插入编译失败的条目，既不改变被选中的 100 分制得分，也不改变最高的 100 分制得分。范围：原始分数是有理数而不是浮点数，没有 NaN 或无穷大；不涵盖空历史（只有编译失败时得分为 0，见 `task_ce_only`）。参见 `evidence/formal/notes/wireless_electricity_layout.md`。

## 局限

- 没有运行任何 AI 模型或解题者。影响只在我们编写的测试提交上展示。
- 共运行了三份提交。随附的基线是唯一能工作的测试提交，没有运行有竞争力的解法。
- `sforge/` 中的测试框架文件与 EdgeBench 的 GitHub 提交 `6e4e5f4` 逐字节一致（`sforge/UPSTREAM.lock`，由 `tools/check_upstream.py` 检查），包括 `selection.py` abb55b7b…、`grading.py` ba15c46d… 和 `score_rescale.py` 98feb630…。
- 最佳提交的选择是用真实的测试框架函数离线测试的，而不是在实际的评分器或智能体运行中测试的。
- 200,000 个历史的检查输出没有保存在本仓库中。
- 没有测量这种情况在过去的运行中出现的频率。
- 在 CPU 更少或更慢的评分器上，5 s 墙钟时限对接近时限的解题者的影响没有测量。

## 复现

- 在原始镜像上运行：`evidence/scripts/wireless_electricity_layout/run_judge.sh OUTDIR`（提交在 `subs/`；保存的日志在 `observed/`）
- 测试框架评分和最佳提交选择：`evidence/scripts/wireless_electricity_layout/grade_and_select.py HARNESS_ROOT TASKS_DIR LOGDIR`
- 随机性质检查：`evidence/scripts/wireless_electricity_layout/normalized_invariance.py`
- 固定标识：
  - 评分器镜像：`seededge/edgebench.judge.wireless_electricity_layout@sha256:78c341ca6e52849dfa7644f6664cbdbf87cd144cc72ff156c2508f5d623906d9`。
  - 任务 JSON：sha256 `050ab35f99431e94ee6279fcd23dc06c9a795ee7b9f26b7d9ec4eadb3e060809`。
  - `/tmp/eval_wirel.sh`：`c670ff6d7ac8a0042666c275b8bc947ddc93263f0b898fdab7078e208ce7dd8f`。
  - 随附基线 `solution.cpp`：`811fe1e54452f935563de0480bd03a0b6270752efa7b45e01fba578116cb9256`。
  - `tools/bin/tester`：`a7d59fd3cc9796305d55d280b5ebe1455b80ae7df13425a47bde88433cd9cf87`。
