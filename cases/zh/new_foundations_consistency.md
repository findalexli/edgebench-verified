# New Foundations Consistency (`new_foundations_consistency`)

**结论：** 保留（附说明）。<mark>在可以联网时，原始评分器能构建项目，并对未修改的初始项目返回有效结果；但它无法离线评分，另有 15 个由编译器生成的计分项存在未经测试的风险，影响至多 0.67%。</mark>

## 任务要求

该任务是一个关于 New Foundations（一种集合论）一致性的 Lean 项目。Lean 是一种用于机器检验数学证明的语言，`sorry` 是 Lean 中表示缺失证明的占位符。任务说明要求解题者 "finish **all** sorries in this folder"（补完该文件夹中的**所有** sorry），并说 "we value minor progress"（我们重视微小的进展）。它还警告："do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation"（不要修改已有 lemma/theorem/def 的签名，否则无法通过评测），以及 "we check the axioms transitively, finishing a theorem without completeing precedent lemma will not count."（我们传递地检查公理，若未完成前置引理就完成一个定理，不计分）。

分数是这样计算的：在初始项目中依赖 `sorry` 的声明里，提交把多大比例变成了不含未经认可公理、且打印出的类型不变的声明。每个计分项（目标）权重相同。任务卡写着 `internet: false`。在测试框架（`sforge/harness/run_evaluation.py`）中，这一设置只作用于智能体的容器；评分器的容器在创建时没有网络限制。类别：形式化数学与定理证明。

## 我们检查了什么

**在可以联网时，评分器能构建项目，并对未修改的初始项目返回有效结果。** 没有用这种方式为任何诚实的证明评分。

- Lean 的构建工具 Lake 打印出 `doc-gen4: URL has changed; deleting … and cloning again`，接着打印 `checking out revision '86d735ecf420e0dbaaf84e2fc2221969f9fca097'`。这是项目清单（manifest）中固定的提交，而不是不断变化的 `main` 分支，其 `lean-toolchain` 为 `v4.21.0-rc3`。
- 构建成功：`eval_cmd` rc=0，没有错误。
- 未修改的初始项目得到 `valid: true` 和 `score: 0.0`，伴随 `mode=unweighted, repaired=0/2246, remaining_bad=2246, new_bad=301`、0 个 `type_changed`、0 个 `disappeared`，且没有 HASH 检查。
- 这 301 个 `new_bad` 条目是编译器内部的常量（`_cstage2` 239 个、`_spec_N` 38 个、`_elambda_N` 24 个）。它们不是 `sorry` 目标，权重为 0。它们在初始项目中同样存在（2547 行 BAD，对应 2246 个目标）。

**无法离线评分。** 在随附的评分器镜像中，`lake build` 在 `--network none` 下失败。无论在评分器的初始仓库中，还是在严格按 `eval_cmd` 准备的提交中，都会失败。

- 原因：Lake 打印 `doc-gen4: URL has changed; deleting '…/.lake/packages/doc-gen4' and cloning again`（`build_orig.err`）。另有记录显示，打包的检出副本没有 `origin` 远程仓库，HEAD 为 `0ee5b43…`，而不是清单中的 `86d735ec…`；这一状态没有保存原始日志（只见于 `lean_family_aux_census.md` 和 `nf_direct.sh` 中的一条注释）。
- 离线时，Lake 删除检出副本并尝试重新克隆，结果在 `git` 中失败（退出码 128）。`eval_cmd` 返回 1，不写出任何 JSON。
- 预期：离线也能得到有效结果。实际：没有结果。

**编译器生成的目标：没有不可达的，只有很小的未经测试的风险。** Lean 编译器会自动生成辅助声明（`X._proof_N`、`X._simp_N` 等）。在任务 `lean_analysis_proofs` 中，同一个评分器只有在生成的名称和打印出的类型都完全一致时才为这些辅助目标计分，这使那里的一些目标不可达。在本任务中，对每个目标逐一统计，没有发现任何一个目标可以证明是诚实、完整的解法无法达到的（下界为 0）。

| 目标数 | 辅助目标数 | 辅助目标占分比例 | 脆弱的辅助目标 | 类型中含 `sorry` 的目标 | P 与 ¬P 成对出现 | 不可达目标的下界 |
|---|---|---|---|---|---|---|
| 2246 | 370 | 16.5% | **15 (0.67%)** | 0 | 0 | **0**（至多 0.67% 存在风险） |

- 辅助目标的种类：337 个 `_proof`、15 个 `_sizeOf`、10 个 `match`，以及其他。
- 这 15 个脆弱的辅助目标是 `BasePerm.instMulActionNearLitter._proof_1/2`、`instGroupNewPerm._proof_1…10`、`instInvNewPerm._proof_1` 和 `instMulActionNewPermCode._proof_1/2`。它们是直接包含占位符的实例字段，以及这些实例中以默认方式填充的同级字段。一个诚实的证明可能会让它们重新编号。
- 父声明为定理的 96 个 `_proof_N` 辅助目标预计是稳定的。我们在核心 Lean 中用本镜像的编译器（4.21.0-rc3）做了检查：四个只相差一个常量的 `@[simp]` iff 定理，分别用四种方式证明：`sorry`、项、`omega` 和 `simp`。在每种写法下，辅助声明都名为 `_proof_1`，其类型都是把定理本身的陈述写成等式（`auxstyle/nf_v4.21.out`）。`omega` 证明还额外生成 `_proof_1_1` 和 `_proof_1_2`，它们不是目标。这 96 个目标都没有经过实际运行评分器的计分。

随任务发布的说明：“在评分器可以联网时能构建并返回有效结果，仅在未修改的初始项目上展示过（Lake 会在清单固定的提交 86d735ec 重新克隆 doc-gen4）；无法离线评分；370 个辅助目标中有 15 个可能因重新编号而受影响（≤0.67%），未经测试”。

## 影响有多大

- 离线评分：只影响无法联网的评分器，它们此时根本给不出分数。在 EdgeBench 的测试框架下，评分器可以联网，因此这在实际使用中不是缺陷。评分仍然需要能够访问 GitHub，且 GitHub 持续提供提交 `86d735ec`。
- 重新编号的辅助目标：至多影响 0.67% 的分数，且只影响填写了相关实例字段的解题者。这是风险的上界，不是测得的损失。

不作改动；上述说明随任务一起发布。

## 我们如何检查

- **在按摘要固定的原始公开镜像中运行原始评分器**（工具链 v4.21.0-rc3）。任务的 `judge.eval_cmd` 完全按原文在评分器未修改的初始源码上运行。同一时间只运行一个容器，参数为 `--memory 4g --cpus 2`。一次以 `--network none` 运行，一次在默认的 bridge 网络上以 `timeout 3600` 运行。
- **目标统计。** 在这个镜像中 Lake 无法离线构建。因此目标列表是用镜像中同一个 `ListDeclAxiom` 辅助程序、通过普通的 `lean` 运行生成的，`LEAN_PATH` 由镜像中已有的编译文件（olean）构成。随后用其他 Lean 任务所用的同一分类器应用评分器的目标规则。
- **检查证明写法不会改变名称。** 即上文所述在核心 Lean 中、用镜像编译器运行的检查。

## 局限

- 没有运行任何 AI 模型或求解器。影响只在未修改的初始项目上展示。
- 没有为任何诚实的证明评分，因此这 15 个存在风险的目标仍未经测试。
- 目标列表是用普通的 `lean` 而非 `lake build ListDeclAxiom` 生成的，使用的是同一辅助文件和同一批 olean。
- 联网时的结果依赖运行时的 GitHub，只观察过一次。
- 测试提交基于评分器的初始源码构建。没有检查智能体工作镜像中的初始项目是否与之完全相同。
- 没有逐一检查每个目标是否为真。
- 没有检查工作镜像是否暴露了源项目中的证明，包括 README 中提到的 `Old/` 目录。

## 复现

- 评分器镜像摘要：`sha256:c17cd565…cc4`。
- 联网运行 `eval_cmd`：`evidence/scripts/lean_family_census/nf_networked.sh`。输出位于 `evidence/scripts/lean_family_census/out/new_foundations_consistency/networked/`，包括 `report.json`。
- 离线运行 `eval_cmd`：`evidence/scripts/lean_family_census/run_native.sh`。失败日志为 `out/new_foundations_consistency/native/build_orig.err`。
- 目标统计：`evidence/scripts/lean_family_census/nf_direct.sh`。
- 证明写法检查：`evidence/scripts/lean_family_census/auxstyle/run.sh`。输出位于 `auxstyle/nf_v4.21.out`。
- 支撑记录：`evidence/reviews/lean_family_aux_census.md` 中的 "Separate finding" 和 "Networked judge run" 两节。
