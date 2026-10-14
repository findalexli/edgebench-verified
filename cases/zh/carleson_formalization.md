# Carleson Formalization (`carleson_formalization`)

**结论：** 保留（附说明）。<mark>我们在评分器镜像内清点了每个计分项，没有一项因为评分器对编译器生成项的命名方式而变得无法达到；每一项是否为真、能否证明，没有检查；说明涉及一个占位的数据定义，以及源项目尚未完成。</mark>

## 任务要求

这个任务是一个关于傅里叶级数 Carleson 定理的大型 Lean 项目。Lean 是一种让机器检验数学证明的语言，`sorry` 是 Lean 中表示证明缺失的占位符。任务文本要求解题者 "finish **all** sorries in this folder"（完成此文件夹中的所有 sorry），并说 "we value minor progress"（我们重视小的进展）。它提醒："do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation."（不要修改现有 lemma/theorem/def 的签名，否则无法通过评测。）它还说 "we check the axioms transitively, finishing a theorem without completeing precedent lemma will not count."（我们会传递地检查公理；前置引理没有完成，只完成定理不计分。）

初始项目中有一批依赖 `sorry` 的声明。提交让其中一部分不再依赖未经认可的公理，并且打印出的类型不变；分数就是这部分所占的比例。每个计分项（目标）权重相同。类别：形式化数学与定理证明。

## 我们检查了什么

我们没有发现会改变分数的缺陷。下面是检查过的各项。

- Lean 编译器会自动生成辅助声明（`X._proof_N`、`X._simp_N`……）。几个任务共用的 Lean 评分器，只有在生成的名字和打印出的类型都完全一致时，才给这些辅助目标计分。在任务 `lean_analysis_proofs` 中，这一规则让至少 44 个辅助目标对任何正确、完整的解法都无法达到（加上 3 个占位陈述和 2 个错误陈述，共占 2901 个目标中的 49 个，即 1.69%），而且分数取决于证明风格。本任务中没有任何辅助目标受这个问题影响：

| 目标数 | 辅助目标数 | 辅助目标占分数的比例 | 脆弱的辅助目标 | 类型中含 `sorry` 的目标 | P 与 ¬P 成对 | 无法达到的目标数下界 |
|---|---|---|---|---|---|---|
| 3004 | 151 | 5.0% | **0** | 0 | 0 | **0** |

  - 辅助目标的种类：90 个 `_proof`、19 个 `_simp`、11 个 `congr_simp`、10 个 `eq_def`，以及其他。
  - 按文本计数，有 8 个辅助目标的类型重复，分类器把它们列为 "likely unattainable"（很可能无法达到）。镜像内的探测把它们全部归为仅传递型，即本身不含 `sorry`，只是继承了它。按清点的推理，这样的目标没有风险，但我们没有用实际评分检验过。
- 为了检查证明风格，我们用镜像中的编译器（4.30.0-rc2），对四个形状相同的 `@[simp]` 等价（iff）定理 `a + b = b + a ↔ k ≤ a + k`（k = 0, 1, 2, 3），分别用四种方式证明：`sorry`、项、`omega` 和 `simp`。每种情况下，辅助声明的名字后缀都相同（`_simp_1`），类型也都与所属定理的陈述一致（`auxstyle/carleson_v4.30.out`）。`omega` 证明还会多生成两个辅助声明 `_proof_1_1` 和 `_proof_1_2`；它们是新名字，不是初始目标。这项测试没有用多种风格重新证明同一个定理。

下面几点需要说明。

- `ToMathlib/RealInterpolation/LorentzInterpolation.lean` 中有一个占位的数据定义 `C_LorentzInterpolation := sorry`。它定义的是一个值，不是一个证明。给它任何值都能拿到这个目标的分，后面用到它的界也可能变得更容易证。这看起来是源项目里还没做完的工作。这一点来自我们阅读源码，没有运行评分器检验。
- 关于源项目的完成度，据报道，源项目已经完成了主定理（这里没有核实），但项目本身还没有完成。有些目标在源项目中可能没有证明。

随任务发布的说明写道："清点：0 个目标无法达到，辅助目标占 5.0% 且稳定；一个以 sorry 给出的数据定义（C_LorentzInterpolation）可以取任意值；上游项目尚未完成，因此有些目标可能没有上游证明"。

## 影响有多大

我们没有发现哪个目标因为评分器对编译器生成项的命名方式而无法达到，由这个原因造成的无法达到目标数下界为 0。这并不说明每个目标都能达到。我们没有检查每个目标是否为真；源项目也还没完成，所以有些目标可能没有已知的证明。例如 `exists_hasLorentzType_real_interpolation` 的陈述就用到了占位的 `C_LorentzInterpolation`（`out/carleson_formalization/baseline-ListDeclAxiom.out`）。占位的数据定义影响一个目标，也可能影响后面一些界的难度。我们没有测量它对分数的影响。

## 我们如何检查

- 原始评分器来自按摘要固定的原始公开镜像（工具链 v4.30.0-rc2）。每次只跑一个容器，参数为 `--network none --memory 4g --cpus 2`。我们在评分器未改动的初始源码上原样运行任务的 `judge.eval_cmd`。未修改的初始项目得 0/3004，没有 `type_changed`，也没有 `disappeared`。
- 我们在镜像内做了清点，记录了实际用到的评分器文件，并生成了初始的 `ListDeclAxiom` 列表。它为 `classical_carleson_check` 打印了一行 HASH，这一项在初始项目上为真。然后我们沿用 `lean_analysis_proofs` 研究中的目标规则和辅助名字模式，给每个目标分类。镜像内的一个探测逐个检查辅助目标本身是否含有 `sorry`（"脆弱"）。
- 形式化检查就是上文所述、用镜像中的编译器在核心 Lean 中做的检查，结果是证明风格不改变名字。
- 计分要求声明不含未经认可的公理。评分器用 `ListDeclAxiom` 传递地检查公理，声明依赖的一切都在检查范围内。

## 局限

- 我们没有运行任何 AI 模型或解题者。影响只在我们写的测试提交上展示。
- 我们只在评分器上实际评过未修改的初始项目，没有给本任务的任何正确证明评过分。稳定/脆弱的分类来自镜像内的探测。
- 我们根据评分器的初始源码构建测试提交，没有检查智能体工作镜像中的初始项目是否与之相同。
- 如果解题者修改定义或实例的主体（签名不变），传递型辅助声明仍可能重新编号。我们没有测量这一点。
- 我们没有逐一审查每个目标是否为真。
- 我们没有检查工作镜像是否暴露了源项目或其蓝图（blueprint）中的证明。
- 评分器隔离不在本次发布的范围内（EdgeBench 的设计选择）。

## 复现

- 评分器镜像摘要：`sha256:dd9aab33…`。
- 清点：`evidence/scripts/lean_family_census/pipeline.sh <task_id> <image@digest> <project dir> <root module>`。
- 在测试提交上运行原样的 `eval_cmd`：`evidence/scripts/lean_family_census/run_native.sh`。用法见脚本头部。
- 证明风格检查：`evidence/scripts/lean_family_census/auxstyle/run.sh`。输出在 `auxstyle/carleson_v4.30.out`。
- 输出：`evidence/scripts/lean_family_census/out/carleson_formalization/`。
- 支持记录：`evidence/reviews/lean_family_aux_census.md`。
