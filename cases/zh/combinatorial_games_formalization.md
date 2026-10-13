# Combinatorial Games Formalization (`combinatorial_games_formalization`)

**结论：** 保留（附说明）。<mark>在原始评分器上的测试中，两种风格的诚实证明得到相同的分数；在评分器镜像内的完整清点没有发现任何对诚实、完整的解法无法达到的计分项（下界为 0；统计了两类失败）。</mark>

## 任务要求

该任务用 Lean 编写，Lean 是一种用于机器检验数学证明的语言。在 Lean 中，`sorry` 是缺失证明的占位符。任务说明要求解题者 "finish **all** sorries in this folder"（完成此文件夹中的所有 sorry），说 "we value minor progress"（我们重视小的进展），并警告："do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation."（不要修改现有 lemma/theorem/def 的签名，否则无法通过评测。）

评分器从初始项目中依赖 `sorry` 的声明列表出发。分数是其中被提交变为只使用允许的公理（"axiom-clean"，即公理干净）、且打印出的类型保持不变的声明所占的比例。每个声明权重相同。类别：形式化数学与定理证明。

## 我们检查了什么

不存在会改变分数的问题。检查内容如下：

- **辅助项。** Lean 编译一个定义时，可能会自行创建辅助声明（`X._proof_N`、`X._simp_N`……）。EdgeBench 各 Lean 任务共用的评分器只有在生成的名字和打印出的类型都完全一致时，才为这些辅助项计分。在任务 `lean_analysis_proofs` 中，至少有 44 个辅助项对任何诚实的完整解法都无法达到（连同 3 个占位陈述和 2 个错误陈述，共 2901 项中的 49 项，占 1.69%；`cases/lean_analysis_proofs.md`），而且分数取决于证明风格。本任务没有这种情况：

| 计分项 | 辅助项 | 辅助项占分数的比例 | 脆弱的辅助项 | 类型中含 `sorry` | 陈述/否定（P/¬P）对 | 无法达到的项数下界 |
|---|---|---|---|---|---|---|
| 3732 | 937 | 25.1% | **0** | 0 | 0 | **0** |

  - 辅助项的种类：450 个 `_simp`、432 个 `_proof`、25 个 `_unsafe_rec`、13 个 `eq_def`、8 个 `eq_N`，以及其他。
  - 基于文本的计数发现 33 个辅助项的类型重复，分类器把它们列为 "likely unattainable"（很可能无法达到）。镜像内的探测把每一个都归为仅传递型：它本身不含 `sorry`，因此诚实的证明永远不会重新构建它。除下文的单模块测试外，这一点没有通过评分来检验。
- **原因。** 这个初始项目是通过把**定理**的证明体替换为 `sorry` 得到的。辅助项之所以失败，只是因为它们的证明项取自上游库，调用了一个现在含有 `sorry` 的定理。一旦这些定理被证明，它们就会自动得分。

说明：辅助项占分数的 25.1%。一旦它们所依赖的项被证明，它们就会自动得分，所以这会使权重分布有所偏斜，但并无不公。

说明的内容是："共用的 Lean 评分器：原生清点表明，诚实的项风格和策略风格证明得到相同的分数（16/3732）；发现 0 个目标无法达到（下界）；辅助目标占权重的 25.1%，但稳定"。

## 影响有多大

没有发现任何计分项对诚实、完整的解法无法达到。下界 0 只统计了两类失败：记录的类型中含有 `sorry`，以及同一父声明下类型分别为 P 和 ¬P 的辅助项对（`classify.txt`）。每个陈述是否为真，以及修改定义主体是否会让辅助项重新编号，没有检查（见局限）。在原始评分器上的测试中，证明风格没有改变得分。

没有代码修改。上述说明随任务一起发布。

## 我们如何检查

- **固定评分器镜像中的原始评分器**（`sha256:3e1062c6…`，Lean 工具链 v4.28.0）。每次只运行一个容器，参数为 `--network none --memory 4g --cpus 2`。任务的 `judge.eval_cmd` 逐字原样运行，包括 `.lake`/manifest 的替换和完整的 `lake build`。`SignExpansion/Basic.lean` 中六个含 `sorry` 的定理被诚实地证明，签名没有改动：`isUpperSet_preimage_singleton_zero`、`copy_eq`、`coe_mk`、`sign_eq_coe`、`le_iff_toLex`、`lt_iff_toLex`。使用了两种证明风格：项模式（A），把证明写成一个表达式；策略模式（B），把证明写成一系列证明步骤。

| 测试提交 | 原始评分器结果 |
|---|---|
| 未修改的初始项目（正确的基线） | 0/3732，没有 `type_changed`，没有 `disappeared` |
| 风格 A（项模式） | 16/3732 |
| 风格 B（策略模式） | 16/3732，得分的项集合相同 |

  - 这 16 项是 6 个定理、`copy`、`instBoundedOrder` 和 8 个辅助项（`copy._proof_1`、`instBoundedOrder._proof_1/_2`、`instCompleteLinearOrder._proof_1…5`）。没有任何项改变类型或消失。
  - 在 `eval_cmd` 换入共用的基线 `.lake` 并重新构建整个项目之后，初始项目的 0 分依然成立。那个 `.lake` 中的 Mathlib（Lean 的主要数学库）与评分器仓库中的不同。
- **镜像内的清点。** 我们记录了实际使用的评分器文件，并生成了基线 `ListDeclAxiom` 列表（它不打印任何 HASH 行）。然后我们用与 `lean_analysis_proofs` 研究相同的计分项规则和辅助名字模式为每个计分项分类。镜像内的一个探测检查每个辅助项本身是否含有 `sorry`（"脆弱"），还是只通过其他常量才到达 `sorry`。
- **公理。** 计分要求声明公理干净，通过 `ListDeclAxiom` 检查。

## 局限

- 没有运行任何 AI 模型或解题者。影响只在我们编写的测试提交和诚实证明变体上展示。
- 原始评分器上的诚实测试只覆盖一个叶子模块。
- 测试提交是根据评分器的基线源码构建的。工作镜像中的初始项目是否与之相同，没有检查。
- 编辑定义或实例主体（签名不变）的解题者仍可能导致传递型辅助项重新编号。这一点没有测量。
- 由于上游库仍在开发中，不清楚每个含 `sorry` 的项是否都有上游证明。没有审计每个陈述是否为真。
- 没有检查工作镜像是否暴露了上游证明。
- 评分器是否与提交隔离，不在本次发布的范围内（这是 EdgeBench 的设计选择）。

## 复现

- 清点：`evidence/scripts/lean_family_census/pipeline.sh <task_id> <image@digest> <project dir> <root module>`。
- 用诚实变体运行原样的 `eval_cmd`：`evidence/scripts/lean_family_census/run_native.sh <task_id> <image@digest> evidence/scripts/lean_family_census/cg_native SignExpansion/Basic.lean`。
- 输出：`evidence/scripts/lean_family_census/out/combinatorial_games_formalization/`。得分项的集合在 `native/repaired.txt` 中。
- 支持记录：`evidence/reviews/lean_family_aux_census.md`。
