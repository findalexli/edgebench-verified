# Ordinal Notation Well-Foundedness (`ordinal_notation_well_foundedness`)

**结论：** 保留（附说明）。<mark>Coq 评分器给正确、完整的证明计分，拒绝 `Admitted` 和依赖公理的证明，但有两条限制没写进文档（辅助文件名过滤和 300 s 的编译时限）。从发布方的结果看，目标 1–6 已有封闭的证明；目标 7–9（85 分中的 64 分）能否证明还不清楚。</mark>

## 任务要求

解题者用 Coq（一种用于机器检验数学证明的语言）证明若干命题。每个命题说的都是：从给定的初始列表出发，一个逐步改写列表的过程一定会终止。任务说明写道："Read `README.md` in the workspace, then complete as many Coq proof targets as possible."（阅读工作区中的说明文件，然后尽可能多地完成 Coq 证明目标。）README 写道："A target receives credit only if the hidden checker's `Print Assumptions` output is closed under the global context. Proofs that rely on `Admitted`, new axioms, parameters, or other open assumptions … will not receive credit."（只有当隐藏检查器打印的假设在全局上下文下封闭时，目标才得分；依赖未完成证明、新公理、参数或其他开放假设的证明不得分。）解题者可以另加 `.v` 辅助库，而且 "Shared helper libraries are submitted."（共享的辅助库会被提交。）

一共九个目标，权重依次为 1、2、2、4、4、8、16、16 和 32（满分 85）。每个目标的形式都是 `Acc (fun child parent => child_step parent child) L`，L 是一个固定列表。`Acc` 是 Coq 的可达性谓词：从 L 出发的每条步骤链都有限，它就成立。task9 的列表等于 `ChildOf.v` 中的 `start`。类别：形式化数学与定理证明。

## 我们检查了什么

**评分器没有缺陷。** 它先删掉已编译的文件，再编译所有非目标的 `.v` 文件，支撑库先编译，反复重试，直到没有文件还能编译为止。对每个目标，它运行 `coqc taskN.v` 和 `coqc eval_taskN.v`。两个都编译通过，且 eval 文件的输出含有 "Closed under the global context"，才算得分。每个 `eval_taskN.v` 都把目标原样重述一遍，所以改过的命题拿不到分。解题者能看到 eval 文件，但这没有关系，它们只是原样重述各个目标。

| 提交 | task1 | task2、task4–task9（`Admitted` 占位） | task3 | 总分 |
|---|---|---|---|---|
| `sub_controls/`（task1 的正常证明；task3 由一条新 `Axiom` 证明） | **PASSED (1)** | FAILED："assumptions were not closed"，列出 `taskN.WF` | **FAILED**，列出 `task3.all_acc` | 1/85 |
| `sub_helper/`（同一个 task1 证明，其引理移到辅助库 `OrdHelpers.v` 中） | **PASSED (1)** | FAILED | FAILED | 1/85 |

应当失败的测试提交，列出的正是预期的那些假设。

**目标是否为真：任务 1–6 为真；任务 7–9 尚无定论。**

- 这些目标连成一条链：每个目标的列表都能由下一个目标的列表走到（对每个 k，task k+1 都能走到 task k；用 N ≤ 3、列表长度 ≤ 30 的广度优先搜索验证，见 `chain_check.py`）。例如 `childOf [0;1;0;0;4] 2 = [0;1;0;0;3;3]`（从 task4 到 task3）。`Acc` 会传给后代，所以证出 task k 就证出了任务 1 到 k，证出 task9 就证出了全部目标。
- 本文证明了 task1（见下文）。按发布方的逐任务结果（`tasks/README.md` 中 ordinal 一行），Opus 4.8 和 GPT-5.5 从 4–6 小时起得分 24.7（满分 100），即 21/85。证明沿链向下传递，所以解题者拿到分的目标实际上是链的一个前缀，各前缀的权重依次为 1、3、5、9、13、21、37、53、85。21 正好是任务 1–6 的权重之和。评分器只给 `Print Assumptions` 封闭的证明计分（下文已检查），由此可知任务 1–6 的封闭证明确实存在。
- 有界的环搜索**没有找到环**。只要有环，`Acc` 就不成立。task1 和 task2 的搜索空间在界限内已经穷尽，其余目标碰到了节点数上限。
- `ChildOf.v` 没有给出到序数的解释，也没有参考证明。这个系统在 task7、task8 和 `start`（task9）处是否良基，还没有定论；这三项占 85 分中的 16 + 16 + 32 = 64 分。没有发现哪个目标为假的证据。在 task7–task9 的证明出现之前，85 分的满分没有经过验证。

**没有写进文档的限制。** 这两条是从任务 JSON 和评分器里读出来的，都没有端到端复现。

- (a) `submit_exclude` 会悄悄丢掉名为 `test*.v`、`check*.v`、`debug*.v`、`explore*.v`、`tmp*.v` 或 `scratch*.v` 的辅助文件，而 README 说辅助库会被提交。证明如果 `Require` 了这类文件，在评分器里会编译失败。
- (b) 每次 `coqc` 调用有 300 s 时限，文档没说。依赖大量计算的正常证明可能会撞上它。

随任务发布的说明：

- 评分器只给 `Print Assumptions` 封闭的证明计分，不多也不少。经内核检验的 task1 正常证明得分，`Admitted` 和依赖公理的证明被拒绝。
- 九个目标连成一条链，每个目标都蕴含比它低的所有目标。已发布的结果显示任务 1–6 已有封闭证明（85 分中的 21 分）；任务 7–9（64 分）还没有已知的证明。即使某个目标为假，也只会压低分数上限，不会让错误的工作得分。
- 名称匹配 `test*`、`check*`、`debug*`、`explore*`、`tmp*` 或 `scratch*`（`.v`）的辅助文件不会被纳入提交。
- 每个 Coq 文件有 300 s 的编译时限。

## 影响有多大

没有发现正常证明的分数受到影响。文件名过滤只影响一种解题者：必需的辅助文件恰好用了被排除的前缀命名，依赖它的证明就会编译失败。时限只影响依赖大量计算的证明。如果 task7、task8 或 task9 为假，所有解题者的最高分都要扣掉这个目标及其以上目标的权重。目前没有发现这样的目标。

任务不改，上述说明随任务一起发布。

## 我们如何检查

- **在按摘要固定的原始公开镜像中运行原始评分器**（Coq 8.20.1、OCaml 4.13.1），用 `--network none --memory 2g --cpus 2` 评上述两份提交。提交里有一个经内核检验的 task1 正常证明、把引理挪到 `OrdHelpers.v` 里的同一证明、用一条新 `Axiom` 证明的 task3（作为应当失败的测试提交），其余目标用 `Admitted` 占位。
- **形式化检查（Coq）。** task1 的证明先说明 `childOf [0;1] N` 归约为 `repeat 0 (S N)`，且全零列表的下一步只能是它的 `removelast`，再用归纳法得出结论。它的 `Print Assumptions` 输出 "Closed under the global context"，即没有用任何公理。
- **独立转写。** `explore.py` 是 `ChildOf.v` 的 Python 转写，在六个非平凡展开上与 Coq 自己的 `Compute` 输出一致。我们用它做了目标之间后代关系的广度优先搜索（BFS；N ≤ 3，长度 ≤ 30），以及有界的环搜索（N ≤ 2，长度 ≤ 24，每个目标 200k 个节点）。

## 局限

- 没有运行任何 AI 模型或求解器。影响只在我们写的测试提交上演示过。
- 这里只证明了 task1。说任务 2–6 可以证明，依据的是发布方的结果（21/85）和评分器的封闭假设检查；随附材料和本仓库里都没有这些证明。排行榜上有些数值不是 1/85 的整数倍（例如 18.4），看起来是多次运行的平均值，发布方对此没有说明。
- `submit_exclude` 的复制步骤是从任务 JSON 中读出的，没有实际执行。
- 有界搜索不是证明。

## 复现

- 评分器镜像摘要：`sha256:272b80aa6554…`。
- `evidence/scripts/ordinal_notation_well_foundedness/run_native.sh <submission_dir> <out_file>`，`sub_controls/` 和 `sub_helper/` 在同一文件夹中。预期输出：`native_controls_output.txt` 和 `native_helper_output.txt`。
- `evidence/scripts/ordinal_notation_well_foundedness/explore.py`（输出 `explore_output.txt`）、`chain_check.py`（输出 `chain_check_output.txt`）和 `coq_check.v`（输出 `coq_check_output.txt`）。
- 审查：`evidence/reviews/ordinal_notation_well_foundedness.md`。
