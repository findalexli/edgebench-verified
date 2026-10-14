# Combinatorial Games Formalization (`combinatorial_games_formalization`)

**结论：** 保留（附说明）。<mark>在原始评分器上测试时，两种风格的正确证明得分相同；在评分器镜像内做的完整清点没有发现哪个计分项是正确、完整的解法拿不到的（下界为 0；统计了两类失败）。</mark>

## 任务要求

这个任务用 Lean 编写。Lean 是一种让机器检验数学证明的语言，`sorry` 是 Lean 中表示证明缺失的占位符。任务说明要求解题者 "finish **all** sorries in this folder"（完成此文件夹中的所有 sorry），说 "we value minor progress"（我们重视小的进展），并提醒："do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation."（不要修改现有 lemma/theorem/def 的签名，否则无法通过评测。）

评分器先列出初始项目中依赖 `sorry` 的声明。提交让其中一部分只用允许的公理（"axiom-clean"，即公理干净），并且打印出的类型不变；分数就是这部分所占的比例。每个声明权重相同。类别：形式化数学与定理证明。

## 我们检查了什么

我们没有发现会改变分数的问题。下面是检查过的各项。

- Lean 编译一个定义时，可能会自己生成辅助声明（`X._proof_N`、`X._simp_N`……）。EdgeBench 各 Lean 任务共用的评分器，只有在生成的名字和打印出的类型都完全一致时，才给这些辅助项计分。在任务 `lean_analysis_proofs` 中，至少有 44 个辅助项是任何正确、完整的解法都拿不到的（加上 3 个占位陈述和 2 个错误陈述，共占 2901 项中的 49 项，即 1.69%；`cases/lean_analysis_proofs.md`），而且分数取决于证明风格。本任务没有这种情况：

| 计分项 | 辅助项 | 辅助项占分数的比例 | 脆弱的辅助项 | 类型中含 `sorry` | 陈述/否定（P/¬P）对 | 无法达到的项数下界 |
|---|---|---|---|---|---|---|
| 3732 | 937 | 25.1% | **0** | 0 | 0 | **0** |

  - 辅助项的种类：450 个 `_simp`、432 个 `_proof`、25 个 `_unsafe_rec`、13 个 `eq_def`、8 个 `eq_N`，以及其他。
  - 按文本计数，有 33 个辅助项的类型重复，分类器把它们列为 "likely unattainable"（很可能无法达到）。镜像内的探测把每一个都归为仅传递型，即本身不含 `sorry`，所以正确的证明永远不会重新构建它。除了下文的单模块测试，我们没有用实际评分检验过这一点。
- 原因在于，这个初始项目是把*定理*的证明体换成 `sorry` 得到的。辅助项失败，只是因为它们的证明项取自上游库，调用了一个现在含 `sorry` 的定理。这些定理一旦证出，辅助项就自动得分。

辅助项占分数的 25.1%，这一点列入说明。它们依赖的项一旦证出，它们就自动得分，所以权重分布会有些偏斜，但不会造成不公。

随任务发布的说明写道："共用的 Lean 评分器：原生清点表明，正确的项风格证明和策略风格证明得到相同的分数（16/3732）；发现 0 个目标无法达到（下界）；辅助目标占权重的 25.1%，但稳定"。

## 影响有多大

我们没有发现哪个计分项是正确、完整的解法拿不到的。下界 0 只统计了两类失败：记录的类型中含有 `sorry`；同一父声明下有一对辅助项，类型分别为 P 和 ¬P（`classify.txt`）。我们没有检查每个陈述是否为真，也没有检查修改定义主体会不会让辅助项重新编号（见局限）。在原始评分器上测试时，证明风格没有改变得分。

代码没有改动。上述说明随任务一起发布。

## 我们如何检查

- 原始评分器来自固定的评分器镜像（`sha256:3e1062c6…`，Lean 工具链 v4.28.0）。每次只跑一个容器，参数为 `--network none --memory 4g --cpus 2`。我们逐字原样运行任务的 `judge.eval_cmd`，包括 `.lake`/manifest 的替换和完整的 `lake build`。我们正确证明了 `SignExpansion/Basic.lean` 中六个含 `sorry` 的定理，签名都没改：`isUpperSet_preimage_singleton_zero`、`copy_eq`、`coe_mk`、`sign_eq_coe`、`le_iff_toLex`、`lt_iff_toLex`。证明用了两种风格：项模式（A），把证明写成一个表达式；策略模式（B），把证明写成一步步的证明步骤。

| 测试提交 | 原始评分器结果 |
|---|---|
| 未修改的初始项目（正确的基线） | 0/3732，没有 `type_changed`，没有 `disappeared` |
| 风格 A（项模式） | 16/3732 |
| 风格 B（策略模式） | 16/3732，得分的项集合相同 |

  - 这 16 项是 6 个定理、`copy`、`instBoundedOrder` 和 8 个辅助项（`copy._proof_1`、`instBoundedOrder._proof_1/_2`、`instCompleteLinearOrder._proof_1…5`）。没有任何项改变类型或消失。
  - `eval_cmd` 换入共用的基线 `.lake` 并重新构建整个项目后，初始项目仍是 0 分。那个 `.lake` 中的 Mathlib（Lean 的主要数学库）与评分器仓库中的不同。
- 我们在镜像内做了清点，记录了实际用到的评分器文件，并生成了基线 `ListDeclAxiom` 列表（它不打印任何 HASH 行）。然后我们沿用 `lean_analysis_proofs` 研究中的计分项规则和辅助名字模式，给每个计分项分类。镜像内的一个探测逐个检查辅助项，看它本身含有 `sorry`（"脆弱"），还是只通过其他常量间接用到 `sorry`。
- 计分要求声明公理干净，由 `ListDeclAxiom` 检查。

## 局限

- 我们没有运行任何 AI 模型或解题者。影响只在我们写的测试提交和正确证明的变体上展示。
- 原始评分器上的正确证明测试只覆盖一个叶子模块。
- 我们根据评分器的基线源码构建测试提交，没有检查工作镜像中的初始项目是否与之相同。
- 如果解题者修改定义或实例的主体（签名不变），传递型辅助项仍可能重新编号。我们没有测量这一点。
- 上游库还在开发中，所以不清楚每个含 `sorry` 的项是否都有上游证明。我们没有逐一审查每个陈述是否为真。
- 我们没有检查工作镜像是否暴露了上游证明。
- 评分器是否与提交隔离，不在本次发布的范围内（这是 EdgeBench 的设计选择）。

## 复现

- 清点：`evidence/scripts/lean_family_census/pipeline.sh <task_id> <image@digest> <project dir> <root module>`。
- 用正确证明的变体运行原样的 `eval_cmd`：`evidence/scripts/lean_family_census/run_native.sh <task_id> <image@digest> evidence/scripts/lean_family_census/cg_native SignExpansion/Basic.lean`。
- 输出：`evidence/scripts/lean_family_census/out/combinatorial_games_formalization/`。得分项的集合在 `native/repaired.txt` 中。
- 支持记录：`evidence/reviews/lean_family_aux_census.md`。
