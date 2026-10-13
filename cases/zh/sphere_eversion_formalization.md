# Sphere Eversion Formalization (`sphere_eversion_formalization`)

**结论：** 保留（附说明）。<mark>没有发现任何计分项因评分器对编译器生成项的命名方式而变得不可达，而且这些生成项是稳定的；这一结论只基于测试提交和检查，没有为任何诚实的证明评分，也没有检查每个计分项是否为真。</mark>

## 任务要求

该任务是一个关于球面外翻（sphere eversion，即球面可以被光滑地里外翻转这一结果）的 Lean 项目。Lean 是一种用于机器检验数学证明的语言，`sorry` 是 Lean 中表示缺失证明的占位符。任务说明要求解题者 "finish **all** sorries in this folder"（补完该文件夹中的**所有** sorry），并说 "we value minor progress"（我们重视微小的进展）。它还警告："do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation."（不要修改已有 lemma/theorem/def 的签名，否则无法通过评测。）

分数是这样计算的：在初始项目中依赖 `sorry` 的声明里，提交把多大比例变成了不含未经认可公理、且打印出的类型不变的声明。每个计分项（目标）权重相同。类别：形式化数学与定理证明。

## 我们检查了什么

没有发现会改变分数的缺陷。

**检查了什么。** Lean 编译器会自动生成辅助声明（`X._proof_N`、`X._simp_N` 等）。多个任务共用的 Lean 评分器只有在生成的名称和打印出的类型都完全一致时，才为这些辅助目标计分。在任务 `lean_analysis_proofs` 中，这使得至少 44 个辅助目标（连同 3 个占位命题和 2 个假命题，共占全部 2901 个目标中的 49 个，即 1.69%）对任何诚实、完整的解法都不可达，并使分数取决于证明写法。本任务没有这个问题：

| 目标数 | 辅助目标数 | 辅助目标占分比例 | 脆弱的辅助目标 | 类型中含 `sorry` 的目标 | P 与 ¬P 成对出现 | 不可达目标的下界 |
|---|---|---|---|---|---|---|
| 661 | 119 | 18.0% | **0** | 0 | 0 | **0** |

- **辅助目标的种类：** 94 个 `_proof`、23 个 `_simp`，以及其他。
- 没有任何辅助目标自身含有占位符（即"脆弱的"）。每个辅助目标被标为 BAD，仅仅是因为它依赖一个使用了 `sorry` 的父声明。因此，对这些父声明的诚实证明应当不会改变它。这是根据评分器镜像内部的一个探测推断的；没有为任何诚实的证明评分。
- **权重。** 辅助目标占分数的 18.0%。根据探测，一旦它们所依赖的声明被证明，它们应当会自动得分。这一点没有通过评分来测试。
- **评分器隔离** 不在本次发布的范围之内（这是 EdgeBench 的设计选择）。没有发现影响诚实解题者的评分缺陷。

**随任务发布的说明。** "Census: 0 targets unattainable; aux targets 18.0% and stable (controls only, no honest-proof test)"（统计：没有不可达的目标；辅助目标占比如上且稳定；仅基于对照提交，未用诚实证明测试）。

## 影响有多大

没有测得任何影响。因编译器生成的名称而不可达的目标，下界为 661 个中的 0 个。这并不说明每个目标都为真或可证明。

不作改动；上述说明随任务一起发布。

## 我们如何检查

- **在按摘要固定的原始公开镜像中运行原始评分器**（工具链 v4.28.0）。同一时间只运行一个容器，使用 `--network none`。任务的 `judge.eval_cmd` 完全按原文在评分器未修改的初始源码上运行，作为测试提交。它把 `/home/workspace/baseline/.lake` 和 `/home/workspace/baseline/lake-manifest.json` 复制到提交中，并重新构建整个项目。这两个清单并不相同：在评分器镜像中，`baseline/lake-manifest.json` 的 sha256 为 `af7adc71…`，而评分器仓库中 `sphere-eversion/lake-manifest.json` 的为 `c2b475de…`（`out/sphere_eversion_formalization/census.log`）。其中的 Mathlib 版本没有记录。在这种替换下，初始项目得 0/661，没有 `type_changed`，也没有 `disappeared`。在每个证明都是 `sorry` 的情况下，包括构建在内的完整评分运行耗时约 5.8 分钟（`native.log`，07:07:18–07:13:06），时限为 2,400 s。
- **在镜像内部统计。** 构建了初始项目的 `ListDeclAxiom` 列表，然后用与 `lean_analysis_proofs` 相同的目标规则和辅助名称模式对每个目标分类。镜像内部的一个探测检查每个辅助目标是否自身含有 `sorry`。实际使用的 `ListDeclAxiom.lean` 会为 `Gromov` 打印一行 HASH，它在初始项目上为真。
- 这里不适用单独的形式化模型；统计本身就是一次 Lean 运行。

## 局限

- 没有运行任何 AI 模型或求解器。影响只在我们编写的测试提交上展示。
- 只有未修改的初始项目在评分器上实际评过分。没有为任何诚实的证明评分。稳定/脆弱的分类来自镜像内部的探测，而不是评分运行。
- 测试提交基于评分器的初始源码构建。没有检查智能体工作镜像中的初始项目是否与之完全相同。
- 没有检查工作镜像是否基于与 `/home/workspace/baseline` 相同的 Mathlib 构建。如果不是，在工作镜像中能编译的证明在评分时可能构建失败，而构建失败得 0 分。在这种替换下只构建过初始项目，其证明全部是 `sorry`。本任务已记录的智能体运行最高得 58.5 分（满分 100，见 `tasks/README.md`），因此它们的证明在替换下确实构建成功了。
- 没有测量完整证明下的构建时间；初始项目的完整重建已需约 5.8 分钟，而超过 2,400 s 时限的运行得 0 分。
- 解题者如果修改定义或实例的主体（签名不变），仍可能使间接依赖的辅助声明重新编号。这一点没有测量。
- 没有逐一审查每个目标是否为真。
- 没有检查工作镜像是否暴露了源项目中的证明。

## 复现

- 评分器镜像摘要：`sha256:1f6eae1d…486`。
- 统计：`evidence/scripts/lean_family_census/pipeline.sh <task_id> <image@digest> <project dir> <root module>`。
- 在测试提交上原样运行 `eval_cmd`：`evidence/scripts/lean_family_census/run_native.sh`。其用法说明在脚本头部。
- 输出：`evidence/scripts/lean_family_census/out/sphere_eversion_formalization/`。
- 固定标识：任务 JSON 的 sha256 为 `089f1248…17c4`；`eval_lean.py` 的 sha256 为 `3319767e…`；实际生效的 `ListDeclAxiom.lean` 为 `4b74bf12…`。
- 支撑记录：`evidence/reviews/lean_family_aux_census.md`。
