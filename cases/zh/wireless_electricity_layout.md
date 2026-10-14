# Wireless Electricity Layout (`wireless_electricity_layout`)

**结论：** 保留（附说明）。<mark>按原始结果算，上游测试框架可能把一个编译失败的程序报为最佳提交，但 100 分制得分永远不会因此改变。</mark>

## 任务要求

智能体要改进一个现成的 C++ 程序，它用来求解一个布局谜题。任务说明写道 "Your solution is scored on **50 fixed hidden test cases**. Final score = sum of (P+Q) across all hidden cases. **Lower is better.**"（大意：解法在一组**固定的隐藏测试用例**上计分，最终分数为所有隐藏用例上 (P+Q) 之和，**越低越好**。）它还写道 "A valid baseline `solution.cpp` already exists. Improve it."（已有一个有效的基线程序，请改进它。）

评分器把各用例分数相加（`score_sum` 解析器），越低越好（`minimize`）。一次运行保留分数最好的提交（`score_first` 选取规则）。原始结果（换算为 0–100 分之前）按分段对数刻度（`piecewise_log_min`）换算成 100 分制得分，参考点依次为 baseline 2.606e16、rank30 2.445e15、rank1 3.624e14 和 super_anchor 1.812e14。任务说明没有提到失败怎么罚。类别：组合优化。

## 我们检查了什么

原始评分器对两类失败罚得不一样。

- 文件缺失或编译失败只得到**一行**惩罚，`CASE 0000 CE score=1e17`，并且 `TOTAL_SCORE 1e17`。
- 每个用例的超时、运行时错误或答案错误，**每个用例**都加上 `1e17`。

只要一个用例失败，整份提交在 100 分制下就是 0 分。 一个用例失败，原始总分就会达到或超过 1e17，高于 baseline 参考点（2.606e16），所以该提交得 0 分（`eval_wirel.sh`，`BAD_SCORE=100000000000000000`；`piecewise_log_min` 在 baseline 参考点及以上返回 0）。任务说明只说 "Final score = sum of (P+Q) across all hidden cases"（最终分数为所有隐藏用例上 (P+Q) 之和），没说失败的用例记多少分。时限是每个用例 5 s 墙钟时间（`TIME_LIMIT=5`，`timeout`），同时跑 2 个用例（`MAX_JOBS=2`），评分器没有设 CPU 限制（`tasks/wireless_electricity_layout.json` 里没有 `cpu_limit`）。所以运行时间接近 5 s 的解题者会不会超时，要看评分器在哪台机器上。在 `score_first` 下，更早的、没有失败用例的提交仍会保留。我们没有测量这一影响。

随附的基线得 0 分。它的原始总分 6.631e17（`observed/baseline.log`）是 baseline 参考点 2.606e16 的 25.4 倍，所以任务说明给的这个"有效基线"在 100 分制下是 0 分。参考点的来历，任务里没有交代，我们也没有查。

随附的基线能正常运行，总分却超过 1e17，按原始单位排名还在一个编译不过的程序后面。能运行的解法本该排在编译失败之前。下表是原始评分器下的实际结果。

| 提交 | 原始评分器输出 |
|---|---|
| `baseline`：**随附的**基线，未作改动 | 50/50 OK，`TOTAL_SCORE 663100735542396309`（6.63e17） |
| `ce`：无法编译 | `CASE 0000 CE`，`TOTAL_SCORE 100000000000000000`（1e17），`CASES_TOTAL 50` |
| `re_some`：在 8 个用例上中止的基线 | 42/50 OK，`TOTAL_SCORE 1356919142089112260`（1.36e18） |

- 在上游测试框架下，编译失败的报告算有效，原始结果为 1e17，100 分制得分为 0.0。测过的每一种顺序里，测试框架都会选中它，排在随附基线和 `re_some` 前面。这些提交在 100 分制下全是 0.0 分。

这不会改变换算后的分数。 原始结果越大，刻度给的分只会更低或不变。原始总分只要达到或超过 baseline 参考点（2.606e16），分数就是 0。编译失败的总分 1e17 在这个点之上。只有其他每份提交的原始总分都不低于 1e17 时，编译失败才可能入选，而那些提交在 100 分制下同样是 0 分。这个问题只影响按原始单位报告的结果，以及哪份提交称作"最佳"。

任务随附了这条说明。在原始评分器里，编译失败总共只罚一次 1e17，而每个失败的用例都要各罚 1e17。所以按原始结果，上游测试框架可能把一份编译不过的提交选为最佳，排在能运行但很差的提交（包括随附基线）前面。100 分制得分永远不会因此改变，因为这样的原始总分都换算成零。

## 影响有多大

编译失败规则对分数的最大影响是 100 分制下 0 分。只有当解题者最好的能运行的提交原始总分也不低于 1e17 时，他才可能看到编译失败按原始结果称作最佳，而这样的解题者在 100 分制下反正都是 0 分。

一个用例失败，整份提交的分就全没了。这种全有或全无的影响来自另一条没有写明的规则，比如在较慢的评分器上有一个用例超时就会这样。我们没有测量影响有多大。

任务本身不改，上述说明随任务一起发布。

## 我们如何检查

- 我们在按摘要固定的原始公开镜像里以 `--network none` 运行原始的 `eval_wirel.sh`，评上述三份提交。
- 我们用真实的测试框架函数给保存的日志评分（`grade_output` → `rescale_score` → `select_best`），用的是 EdgeBench 测试框架 `6e4e5f4` 版本（`sforge/`，哈希见 `sforge/UPSTREAM.lock`）。
- 从分数刻度和选取规则的源码出发，一个简短的论证就能说明 100 分制得分不会变。我们又用上游代码在 200,000 个随机提交历史上验证了这一点。在每个位置插入一份编译失败的提交后，选中提交的 100 分制得分变了 **0** 次，最高 100 分制得分变了 0 次，原始的 `best_score` 变了 43,336 次。
- 形式化证明用的是 Lean 4：`evidence/formal/lean/ebv/Ebv/WirelessCeInvariance.lean`（输出 `WirelessCeInvariance.out`，`lean exit=0`，只用标准公理）证明了 `selected_norm_invariant`、`bestMax_invariant` 和 `task_ce_invariant`，即在非空的提交历史里任意位置插入编译失败的条目，选中提交的 100 分制得分和最高的 100 分制得分都不变。证明的适用范围是原始分数为有理数而非浮点数，没有 NaN 或无穷大，不包括空历史（只有编译失败时得 0 分，见 `task_ce_only`）。参见 `evidence/formal/notes/wireless_electricity_layout.md`。

## 局限

- 没有运行任何 AI 模型或解题者。影响只在我们写的测试提交上演示过。
- 一共跑了三份提交。能运行的测试提交只有随附的基线，没有运行有竞争力的解法。
- `sforge/` 中的测试框架文件与 EdgeBench 的 GitHub 提交 `6e4e5f4` 逐字节一致（`sforge/UPSTREAM.lock`，由 `tools/check_upstream.py` 检查），包括 `selection.py` abb55b7b…、`grading.py` ba15c46d… 和 `score_rescale.py` 98feb630…。
- 最佳提交的选择是用真实的测试框架函数离线测试的，没有在实际的评分器或智能体运行中测试。
- 200,000 个历史的检查输出没有保存在本仓库中。
- 我们没有测量这种情况在过去的运行中出现的频率。
- 在 CPU 更少或更慢的评分器上，5 s 墙钟时限对接近时限的解题者有多大影响，也没有测量。

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
