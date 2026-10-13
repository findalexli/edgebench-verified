# Carleson Formalization (`carleson_formalization`)

**结论：** 保留（附说明）。<mark>在评分器镜像内对每个计分项的清点发现，没有任何一项因评分器对编译器生成项的命名方式而变得无法达到；是否每一项都为真且可证明没有检查；说明涉及一个占位的数据定义和尚未完成的源项目。</mark>

## 任务要求

该任务是一个关于傅里叶级数 Carleson 定理的大型 Lean 项目。Lean 是一种用于机器检验数学证明的语言，`sorry` 是 Lean 中表示缺失证明的占位符。任务文本要求解题者 "finish **all** sorries in this folder"（完成此文件夹中的所有 sorry），并说 "we value minor progress"（我们重视小的进展）。它警告："do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation."（不要修改现有 lemma/theorem/def 的签名，否则无法通过评测。）它还说 "we check the axioms transitively, finishing a theorem without completeing precedent lemma will not count."（我们会传递地检查公理；在没有完成前置引理的情况下完成一个定理不计分。）

分数是初始项目中依赖 `sorry` 的声明里，被提交变为不含未经认可的公理、且打印出的类型不变的声明所占的比例。每个计分项（目标）权重相同。类别：形式化数学与定理证明。

## 我们检查了什么

没有发现会改变分数的缺陷。检查了以下部分：

- **辅助目标。** Lean 编译器会自动生成辅助声明（`X._proof_N`、`X._simp_N`……）。几个任务共用的 Lean 评分器只有在生成的名字和打印出的类型都完全一致时，才为这些辅助目标计分。在任务 `lean_analysis_proofs` 中，这使至少 44 个辅助目标（连同 3 个占位陈述和 2 个错误陈述，共 2901 个目标中的 49 个，占 1.69%）对任何诚实、完整的解法都无法达到，而且分数取决于证明风格。在本任务中，没有任何辅助目标受到这一问题的影响：

| 目标数 | 辅助目标数 | 辅助目标占分数的比例 | 脆弱的辅助目标 | 类型中含 `sorry` 的目标 | P 与 ¬P 成对 | 无法达到的目标数下界 |
|---|---|---|---|---|---|---|
| 3004 | 151 | 5.0% | **0** | 0 | 0 | **0** |

  - 辅助目标的种类：90 个 `_proof`、19 个 `_simp`、11 个 `congr_simp`、10 个 `eq_def`，以及其他。
  - 基于文本的计数发现 8 个辅助目标的类型重复，分类器把它们列为 "likely unattainable"（很可能无法达到）。镜像内的探测把它们全部归为仅传递型：它们本身不含 `sorry`，只是继承了它。按照清点的推理，它们因此没有风险。这一点没有通过评分来检验。
- **证明风格。** 使用该镜像的编译器（4.30.0-rc2），对四个形状相同的 `@[simp]` 等价（iff）定理 `a + b = b + a ↔ k ≤ a + k`（k = 0, 1, 2, 3）分别用四种方式证明：用 `sorry`、用项、用 `omega` 和用 `simp`。在每种情况下，辅助声明都得到相同的名字后缀（`_simp_1`），类型也与其所属定理的陈述一致（`auxstyle/carleson_v4.30.out`）。`omega` 证明还会再生成两个辅助声明 `_proof_1_1` 和 `_proof_1_2`；它们是新名字，不是初始目标。这项测试并没有用多种风格重新证明同一个定理。

说明事项：

- **占位的数据定义。** `ToMathlib/RealInterpolation/LorentzInterpolation.lean` 中有一个**数据**定义 `C_LorentzInterpolation := sorry`，也就是一个被定义的值，而不是一个证明。任何值都能拿到该目标的分数，之后用到它的界也可能变得更容易。这看起来是源项目中尚未完成的工作。这一点来自阅读源码，没有通过运行评分器来检验。
- **源项目的完成度。** 据报道源项目已完成其主定理（此处未核实），但项目本身尚未完成。有些目标在源项目中可能没有证明。

说明的内容是："清点：0 个目标无法达到，辅助目标占 5.0% 且稳定；一个以 sorry 给出的数据定义（C_LorentzInterpolation）可以取任意值；上游项目尚未完成，因此有些目标可能没有上游证明"。

## 影响有多大

没有发现任何目标因评分器对编译器生成项的命名方式而无法达到：由此原因导致的无法达到目标数下界为 0。这并不表明每个目标都可达到。每个目标是否为真没有检查，而且源项目尚未完成，所以有些目标可能没有已知证明。一个例子是 `exists_hasLorentzType_real_interpolation`，它的陈述用到了占位的 `C_LorentzInterpolation`（`out/carleson_formalization/baseline-ListDeclAxiom.out`）。占位的数据定义影响一个目标，并可能影响之后一些界的难度。它对分数的影响没有测量。

## 我们如何检查

- **原始公开镜像中的原始评分器，按摘要固定**（工具链 v4.30.0-rc2）。每次只运行一个容器，参数为 `--network none --memory 4g --cpus 2`。任务的 `judge.eval_cmd` 原样在评分器未修改的初始源码上运行。未修改的初始项目得分为 0/3004，没有 `type_changed`，也没有 `disappeared`。
- **镜像内的清点。** 我们记录了实际使用的评分器文件，并生成了初始的 `ListDeclAxiom` 列表。它为 `classical_carleson_check` 打印了一行 HASH，该项在初始项目上为真。然后我们用与 `lean_analysis_proofs` 研究相同的目标规则和辅助名字模式为每个目标分类。镜像内的一个探测检查每个辅助目标本身是否含有 `sorry`（"脆弱"）。
- **证明风格不改变名字的形式化检查。** 即上文所述、用镜像中的编译器在核心 Lean 中做的检查。
- **公理。** 计分要求声明不含未经认可的公理。评分器用 `ListDeclAxiom` 传递地检查公理，覆盖声明所依赖的一切。

## 局限

- 没有运行任何 AI 模型或解题者。影响只在我们编写的测试提交上展示。
- 只有未修改的初始项目在评分器上实际评过分。本任务没有为任何诚实的证明评分。稳定/脆弱的分类来自镜像内的探测。
- 测试提交是根据评分器的初始源码构建的。智能体工作镜像中的初始项目是否与之相同，没有检查。
- 编辑定义或实例主体（签名不变）的解题者仍可能导致传递型辅助声明重新编号。这一点没有测量。
- 没有审计每个目标是否为真。
- 没有检查工作镜像是否暴露了源项目或其蓝图（blueprint）中的证明。
- 评分器隔离不在本次发布的范围内（EdgeBench 的设计选择）。

## 复现

- 评分器镜像摘要：`sha256:dd9aab33…`。
- 清点：`evidence/scripts/lean_family_census/pipeline.sh <task_id> <image@digest> <project dir> <root module>`。
- 在测试提交上运行原样的 `eval_cmd`：`evidence/scripts/lean_family_census/run_native.sh`。用法见脚本头部。
- 证明风格检查：`evidence/scripts/lean_family_census/auxstyle/run.sh`。输出在 `auxstyle/carleson_v4.30.out`。
- 输出：`evidence/scripts/lean_family_census/out/carleson_formalization/`。
- 支持记录：`evidence/reviews/lean_family_aux_census.md`。
