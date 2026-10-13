# Ordinal Notation Well-Foundedness (`ordinal_notation_well_foundedness`)

**结论：** 保留（附说明）。<mark>Coq 评分器为诚实的完整证明计分，并拒绝 `Admitted` 和依赖公理的证明，但有两个限制没有写入文档（对辅助文件名的过滤和 300 s 的编译时限）。发布方的结果显示目标 1–6 已有封闭的证明；目标 7–9（85 分中的 64 分）能否证明尚不清楚。</mark>

## 任务要求

解题者用 Coq（一种用于机器检验数学证明的语言）证明若干命题。每个命题都断言：从一个给定的初始列表出发，一个逐步改写列表的过程总会终止。任务说明写道："Read `README.md` in the workspace, then complete as many Coq proof targets as possible."（阅读工作区中的说明文件，然后尽可能多地完成 Coq 证明目标。）README 写道："A target receives credit only if the hidden checker's `Print Assumptions` output is closed under the global context. Proofs that rely on `Admitted`, new axioms, parameters, or other open assumptions … will not receive credit."（只有当隐藏检查器打印的假设在全局上下文下封闭时，目标才得分；依赖未完成证明、新公理、参数或其他开放假设的证明不得分。）解题者可以添加额外的 `.v` 辅助库，并且 "Shared helper libraries are submitted."（共享的辅助库会被提交。）

共有九个目标，权重分别为 1、2、2、4、4、8、16、16 和 32（满分 85）。每个目标都是 `Acc (fun child parent => child_step parent child) L`，其中 L 是一个固定列表。`Acc` 是 Coq 的可达性谓词：当从 L 出发的每条步骤链都有限时，它成立。task9 的列表等于 `ChildOf.v` 中的 `start`。类别：形式化数学与定理证明。

## 我们检查了什么

**评分器没有缺陷。** 评分器先删除已编译的文件，然后编译每个非目标文件的 `.v` 文件，先编译支撑库，反复重试直到再没有文件能编译。对每个目标，它运行 `coqc taskN.v` 和 `coqc eval_taskN.v`。得分要求两者都编译通过，且 eval 文件的输出包含 "Closed under the global context"。每个 `eval_taskN.v` 都原样重述目标，因此改动过的命题无法得分。eval 文件对解题者可见；这无关紧要，因为它们只是原样重述每个目标。

| 提交 | task1 | task2、task4–task9（`Admitted` 占位） | task3 | 总分 |
|---|---|---|---|---|
| `sub_controls/`（task1 的诚实证明；task3 由一条新 `Axiom` 证明） | **PASSED (1)** | FAILED："assumptions were not closed"，列出 `taskN.WF` | **FAILED**，列出 `task3.all_acc` | 1/85 |
| `sub_helper/`（同一个 task1 证明，其引理移到辅助库 `OrdHelpers.v` 中） | **PASSED (1)** | FAILED | FAILED | 1/85 |

那些应当失败的测试提交，列出的恰好是预期的假设。

**目标是否为真：任务 1–6 为真；任务 7–9 尚无定论。**

- 这些目标构成一条链：每个目标的列表都能从下一个目标的列表到达（对每个 k，task k+1 都能到达 task k；用 N ≤ 3、列表长度 ≤ 30 的广度优先搜索验证，见 `chain_check.py`）。例如 `childOf [0;1;0;0;4] 2 = [0;1;0;0;3;3]`（从 task4 到 task3）。`Acc` 会传递给后代，因此 task k 的证明蕴含任务 1 到 k，而 task9 蕴含所有目标。
- 本文证明了 task1（见下文）。发布方的逐任务结果（`tasks/README.md` 中 ordinal 一行）显示，Opus 4.8 和 GPT-5.5 从 4–6 小时起得分为 24.7（满分 100），即 21/85。由于证明沿链向下传递，解题者得分的目标实际上是这条链的一个前缀，各前缀的权重为 1、3、5、9、13、21、37、53、85。21 恰好是任务 1–6 的权重。评分器只为 `Print Assumptions` 封闭的证明计分（下文已检查），因此任务 1–6 的封闭证明是存在的。
- 有界的环搜索**没有找到环**。环的存在会否定 `Acc`。task1 和 task2 的搜索空间在界限内已穷尽；其余目标触及了节点数上限。
- `ChildOf.v` 没有提供到序数的解释，也没有参考证明。该系统在 task7、task8 和 `start`（task9）处是否良基尚无定论；这三项占 85 分中的 16 + 16 + 32 = 64 分。没有发现任何目标为假的证据。在 task7–task9 的证明出现之前，85 的满分未经验证。

**没有写入文档的限制。** 这些是从任务 JSON 和评分器中读出的，都没有端到端复现。

- (a) `submit_exclude` 会静默丢弃名为 `test*.v`、`check*.v`、`debug*.v`、`explore*.v`、`tmp*.v` 或 `scratch*.v` 的辅助文件。README 说辅助库会被提交。一个 `Require` 了此类文件的证明在评分器中会编译失败。
- (b) 每次 `coqc` 调用 300 s 的时限没有说明。一个依赖大量计算的诚实证明可能会触及它。

随任务发布的说明：

- 评分器恰好为 `Print Assumptions` 封闭的证明计分。经内核检验的 task1 诚实证明得分，`Admitted` 和依赖公理的证明被拒绝。
- 九个目标构成一条链，因此每个目标蕴含所有更低的目标。已发布的结果显示任务 1–6 已有封闭证明（85 分中的 21 分）；任务 7–9（64 分）没有已知的证明。一个为假的目标只会压低分数上限，而绝不会奖励错误的工作。
- 名称匹配 `test*`、`check*`、`debug*`、`explore*`、`tmp*` 或 `scratch*`（`.v`）的辅助文件不会被纳入提交。
- 每个 Coq 文件有 300 s 的编译时限。

## 影响有多大

没有发现对诚实证明分数的影响。文件名过滤只影响那些给必需的辅助文件取了被排除前缀名称的解题者：依赖该文件的证明会编译失败。时限只影响依赖大量计算的证明。如果 task7、task8 或 task9 为假，每个解题者的最高分都会减少该目标及其以上目标的权重。目前不知道有这样的目标。

不作改动；上述说明随任务一起发布。

## 我们如何检查

- **在按摘要固定的原始公开镜像中运行原始评分器**（Coq 8.20.1、OCaml 4.13.1），以 `--network none --memory 2g --cpus 2` 对上述两份提交运行。它们包含一个经内核检验的 task1 诚实证明、把引理放到 `OrdHelpers.v` 中的同一证明、由一条新 `Axiom` 证明的 task3（作为应当失败的测试提交），以及其他目标的 `Admitted` 占位。
- **形式化检查（Coq）。** task1 的证明说明 `childOf [0;1] N` 归约为 `repeat 0 (S N)`，且每个全零列表的下一步只能是其 `removelast`，然后用归纳法得出结论。它的 `Print Assumptions` 为 "Closed under the global context"：不使用任何公理。
- **独立转写。** `explore.py` 是 `ChildOf.v` 的 Python 转写。它在六个非平凡展开上与 Coq 自身的 `Compute` 输出一致。用它驱动了目标之间后代关系的广度优先搜索（BFS；N ≤ 3，长度 ≤ 30），以及有界的环搜索（N ≤ 2，长度 ≤ 24，每个目标 200k 个节点）。

## 局限

- 没有运行任何 AI 模型或求解器。影响只在我们编写的测试提交上展示。
- 这里只证明了 task1。任务 2–6 可以证明，这一点依据的是发布方的结果（21/85）和评分器的封闭假设检查；随附材料和本仓库中都没有它们的证明。排行榜上不是 1/85 整数倍的数值（例如 18.4）暗示这是多次运行的平均值，发布方对此没有说明。
- `submit_exclude` 的复制步骤是从任务 JSON 中读出的，没有实际执行。
- 有界搜索不是证明。

## 复现

- 评分器镜像摘要：`sha256:272b80aa6554…`。
- `evidence/scripts/ordinal_notation_well_foundedness/run_native.sh <submission_dir> <out_file>`，`sub_controls/` 和 `sub_helper/` 在同一文件夹中。预期输出：`native_controls_output.txt` 和 `native_helper_output.txt`。
- `evidence/scripts/ordinal_notation_well_foundedness/explore.py`（输出 `explore_output.txt`）、`chain_check.py`（输出 `chain_check_output.txt`）和 `coq_check.v`（输出 `coq_check_output.txt`）。
- 审查：`evidence/reviews/ordinal_notation_well_foundedness.md`。
