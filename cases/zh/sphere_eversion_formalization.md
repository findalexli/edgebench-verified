# Sphere Eversion Formalization (`sphere_eversion_formalization`)

**结论：** 保留（附说明）。<mark>评分器对编译器生成项的命名方式没有让任何计分项变得拿不到，这些生成项也是稳定的。这个结论只基于测试提交和检查：没有给任何正常写出的证明评过分，也没有逐个核实计分项是否为真。</mark>

## 任务要求

这是一个 Lean 项目，内容是球面外翻（sphere eversion，即球面可以光滑地里外翻转这一结果）。Lean 是一种用于机器检验数学证明的语言，`sorry` 是 Lean 中表示缺失证明的占位符。任务说明要求解题者 "finish **all** sorries in this folder"（补完该文件夹中的**所有** sorry），并说 "we value minor progress"（我们重视微小的进展）。它还警告："do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation."（不要修改已有 lemma/theorem/def 的签名，否则无法通过评测。）

计分方法：初始项目里有一批依赖 `sorry` 的声明，看提交把其中多大比例改成了不含未经认可的公理、打印出的类型也没变的声明。每个计分项（目标）权重相同。类别：形式化数学与定理证明。

## 我们检查了什么

没有发现会改变分数的缺陷。

**检查了什么。** Lean 编译器会自动生成辅助声明（`X._proof_N`、`X._simp_N` 等）。多个任务共用的 Lean 评分器要求生成的名称和打印出的类型都完全一致，才给这些辅助目标计分。在任务 `lean_analysis_proofs` 里，这导致至少 44 个辅助目标是任何正确、完整的解法都拿不到的（加上 3 个占位命题和 2 个假命题，共 49 个，占全部 2901 个目标的 1.69%），分数也随证明写法而变。本任务没有这个问题：

| 目标数 | 辅助目标数 | 辅助目标占分比例 | 脆弱的辅助目标 | 类型中含 `sorry` 的目标 | P 与 ¬P 成对出现 | 不可达目标的下界 |
|---|---|---|---|---|---|---|
| 661 | 119 | 18.0% | **0** | 0 | 0 | **0** |

- **辅助目标的种类：** 94 个 `_proof`、23 个 `_simp`，以及其他。
- 没有哪个辅助目标自身含占位符（即"脆弱的"）。辅助目标被标为 BAD，只是因为它依赖的父声明用了 `sorry`。所以正常地证明这些父声明，应该不会改变辅助目标本身。这是从评分器镜像内的一个探测推断出来的，没有给任何正常写出的证明评过分。
- **权重。** 辅助目标占分数的 18.0%。按探测结果，它们依赖的声明一旦证出，它们应该会自动得分。这一点没有用评分验证过。
- **评分器隔离** 不在本次发布的范围内（这是 EdgeBench 的设计选择）。没有发现会影响按规则解题者的评分缺陷。

**随任务发布的说明。** "Census: 0 targets unattainable; aux targets 18.0% and stable (controls only, no honest-proof test)"（统计：没有拿不到的目标；辅助目标占比如上且稳定；仅基于对照提交，没有用正常证明测试）。

## 影响有多大

没有测到任何影响。因编译器生成的名称而拿不到的目标，下界是 661 个中的 0 个。这不说明每个目标都为真或都能证明。

任务不改，上述说明随任务一起发布。

## 我们如何检查

- **在按摘要固定的原始公开镜像中运行原始评分器**（工具链 v4.28.0）。同一时间只跑一个容器，使用 `--network none`。以评分器未改动的初始源码为测试提交，一字不改地运行任务的 `judge.eval_cmd`。它把 `/home/workspace/baseline/.lake` 和 `/home/workspace/baseline/lake-manifest.json` 复制进提交，再重新构建整个项目。这两份清单并不相同：评分器镜像里 `baseline/lake-manifest.json` 的 sha256 是 `af7adc71…`，评分器仓库里 `sphere-eversion/lake-manifest.json` 的是 `c2b475de…`（`out/sphere_eversion_formalization/census.log`）。其中的 Mathlib 版本没有记录。做了这种替换后，初始项目得 0/661，没有 `type_changed`，也没有 `disappeared`。所有证明都是 `sorry` 时，连构建在内的完整评分运行约需 5.8 分钟（`native.log`，07:07:18–07:13:06），时限为 2,400 s。
- **在镜像内统计。** 构建了初始项目的 `ListDeclAxiom` 列表，然后按与 `lean_analysis_proofs` 相同的目标规则和辅助名称模式给每个目标分类。镜像内的一个探测检查每个辅助目标自身是否含 `sorry`。实际使用的 `ListDeclAxiom.lean` 会为 `Gromov` 打印一行 HASH，这一行在初始项目上为真。
- 这里用不上单独的形式化模型，统计本身就是一次 Lean 运行。

## 局限

- 没有运行任何 AI 模型或求解器。影响只在我们写的测试提交上演示过。
- 实际在评分器上评过分的只有未改动的初始项目，没有给任何正常写出的证明评过分。稳定/脆弱的分类来自镜像内的探测，不是评分运行。
- 测试提交用评分器的初始源码构建。我们没有核对智能体工作镜像里的初始项目是否与它完全相同。
- 没有核对工作镜像所用的 Mathlib 是否与 `/home/workspace/baseline` 相同。如果不同，在工作镜像里能编译的证明，评分时可能构建失败，而构建失败得 0 分。做了这种替换后只构建过初始项目，里面的证明全是 `sorry`。本任务有记录的智能体运行最高得 58.5 分（满分 100，见 `tasks/README.md`），说明它们的证明在替换后确实构建成功了。
- 没有测量完整证明下的构建时间。初始项目完整重建一次已要约 5.8 分钟，而超过 2,400 s 时限的运行得 0 分。
- 解题者如果改了定义或实例的主体（签名不变），间接依赖它们的辅助声明仍可能重新编号。这一点没有测量。
- 没有逐个审查目标是否为真。
- 没有检查工作镜像是否暴露了源项目中的证明。

## 复现

- 评分器镜像摘要：`sha256:1f6eae1d…486`。
- 统计：`evidence/scripts/lean_family_census/pipeline.sh <task_id> <image@digest> <project dir> <root module>`。
- 在测试提交上原样运行 `eval_cmd`：`evidence/scripts/lean_family_census/run_native.sh`。其用法说明在脚本头部。
- 输出：`evidence/scripts/lean_family_census/out/sphere_eversion_formalization/`。
- 固定标识：任务 JSON 的 sha256 为 `089f1248…17c4`；`eval_lean.py` 的 sha256 为 `3319767e…`；实际生效的 `ListDeclAxiom.lean` 为 `4b74bf12…`。
- 支撑记录：`evidence/reviews/lean_family_aux_census.md`。
