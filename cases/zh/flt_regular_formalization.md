# FLT Regular Formalization (`flt_regular_formalization`)

**结论：** 保留（附说明）。<mark>加权计分的陈述列表与任务自己的列表完全一致，也不含任何编译器生成的名字，所以没有发现正确、完整的解法拿不到的陈述。</mark>

## 任务要求

解题者要在一个费马大定理项目中工作，项目用 Lean 4（一种让机器检验数学证明的语言）编写。任务说明要求解题者 "finish **all** sorries in this folder"（完成此文件夹中的所有 sorry；`sorry` 是表示证明缺失的占位符），并说 "we value minor progress"（我们重视小的进展）。它提醒："Do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation."（不要修改现有 lemma/theorem/def 的签名，否则无法通过评测。）它还说 "finishing `fermatLastTheoremSeven` without completeing `isRegularPrime_seven` and `flt_regular` will not count."（两个前置结果没有完成，只完成这个定理不计分。）与其他 Lean 任务不同，本任务按权重计分：一个权重文件列出了 25 个声明，总权重为 87。类别：形式化数学与定理证明。

## 我们检查了什么

没有会改变分数的问题。检查的内容如下：

- **编译器生成的目标。** 几个任务共用的 Lean 评分器，只有在生成的名字和打印出的类型都完全一致时，才给编译器生成的目标（名字形如 `X._proof_N`、`X._simp_N`……）计分。在 `lean_analysis_proofs` 中，这一规则让至少 44 个辅助目标是任何正确、完整的解法都拿不到的（加上 3 个占位陈述和 2 个错误陈述，共占 2901 个目标中的 49 个，即 1.69%）。本任务没有这个问题，因为没有一个目标是编译器生成的：

| 目标（权重） | 编译器生成的目标 | 它们占分数的比例 | 脆弱的生成目标 | 类型中含 `sorry` | P/¬P 对 | 无法达到的目标数下界 |
|---|---|---|---|---|---|---|
| 25（权重 87） | **0** | 0% | 0 | 0 | 0 | **0** |

- **权重文件。** 它有 25 个条目，权重从 1 到 6，共 87。这些条目正好是初始列表中标为 BAD、含有 `sorry` 的 25 个声明，25 个类型文本都与列表中的一致。

说明：README 按 100 分分配分数，但评分器用的权重合计为 87。这只是文档上的不一致。

说明的内容是："清点：25 个加权目标（总权重 87）与列表完全一致；没有辅助目标；0 个无法达到"。

任务没有改动；上述说明随任务一起发布。

## 影响有多大

对正确、完整的解法，没有拿不到的目标（下界 0）。README 按 100 分分配的写法不改变任何分数。

## 我们如何检查

- **原始评分器，来自按摘要固定的公开镜像**（工具链 v4.28.0）。每次只跑一个容器，参数为 `--network none --memory 4g --cpus 2`。任务的 `judge.eval_cmd` 原样运行在评分器镜像中未修改的基线源码上。这条命令把 `/home/workspace/baseline/.lake` 和 `/home/workspace/baseline/lake-manifest.json` 复制到提交中，再重新构建整个项目。两个 manifest 并不相同：在评分器镜像中，`baseline/lake-manifest.json` 的 sha256 为 `7758d921…`，评分器仓库中的 `FltRegular/lake-manifest.json` 为 `880c7aa4…`（`out/flt_regular_formalization/census.log`）。其中的 Mathlib（Lean 的数学库）版本没有记录。做了这一替换后，未修改的初始项目得 0/25（权重 0/87），没有 `type_changed`，也没有 `disappeared`。包括构建在内，一次完整评分在 2 个 CPU 下约用 2.5 分钟（`native.log`，06:43:30–06:46:03），时限为 2,400 s。
- **镜像内的清点。** 我们记录了实际用到的评分器文件，并生成了基线 `ListDeclAxiom` 列表。列表为 `flt_regular` 打印了一行 HASH，这一项在基线上为真。我们把权重文件的条目与列表中含 `sorry` 的 BAD 声明及其打印出的类型逐一对照。
- **公理。** 计分要求声明不用额外的公理，由 `ListDeclAxiom` 检查。

## 局限

- 我们没有运行任何 AI 模型或解题者。影响只在我们写的测试提交上展示。
- 只有未修改的初始项目在评分器上评过分。本任务中没有给任何含正确证明的变体评过分。
- 提交是根据评分器镜像中的基线源码构建的。工作镜像中的初始项目是否与之相同，没有检查。
- 没有检查工作镜像构建时用的 Mathlib 是否与 `/home/workspace/baseline` 相同。如果不同，在工作镜像中能编译的证明，评分时可能构建失败，而构建失败得 0 分。只有证明全是 `sorry` 的初始项目在替换后构建过。本任务已记录的智能体运行最高得 75.1 分（满分 100）（`tasks/README.md`），可见它们的证明在替换后确实能构建。
- 没有测量证明完整时的构建时间；超过 2,400 s 时限的运行得 0 分。
- 没有检查每个目标是否为真。
- 没有检查工作镜像是否暴露了上游证明。上游项目已经完成并公开，其中一部分已并入 Mathlib。
- 评分器隔离不在本次发布的范围内（EdgeBench 的设计选择）。

## 复现

- 评分器镜像：`sha256:c8b50a05…`。
- 目标清点：`evidence/scripts/lean_family_census/pipeline.sh <task_id> <image@digest> <project dir> <root module> FltRegular_weight.json`。
- 原样的 `eval_cmd` 运行：`evidence/scripts/lean_family_census/run_native.sh`。用法见脚本头部。
- 输出：`evidence/scripts/lean_family_census/out/flt_regular_formalization/`。权重文件的条目及其权重列在 `classify.txt` 中；权重文件本身没有放进来。
- 支持记录：`evidence/reviews/lean_family_aux_census.md`。
