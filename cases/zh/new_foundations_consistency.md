# New Foundations Consistency (`new_foundations_consistency`)

**结论：** 保留（附说明）。<mark>联网时，原始评分器能构建项目，并对未修改的初始项目返回有效结果。它无法离线评分；另有 15 个编译器生成的计分项存在风险，我们没有测试，影响至多 0.67%。</mark>

## 任务要求

这是一个 Lean 项目，内容是 New Foundations（一种集合论）的一致性。Lean 是一种用于机器检验数学证明的语言，`sorry` 是 Lean 中表示缺失证明的占位符。任务说明要求解题者 "finish **all** sorries in this folder"（补完该文件夹中的**所有** sorry），并说 "we value minor progress"（我们重视微小的进展）。它还警告 "do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation"（不要修改已有 lemma/theorem/def 的签名，否则无法通过评测），以及 "we check the axioms transitively, finishing a theorem without completeing precedent lemma will not count."（我们传递地检查公理，若未完成前置引理就完成一个定理，不计分）。

初始项目里有一批依赖 `sorry` 的声明。分数是提交把其中多大比例改成了不含未经认可的公理、打印出的类型也不变的声明。每个计分项（目标）权重相同。任务卡写着 `internet: false`。测试框架（`sforge/harness/run_evaluation.py`）只对智能体的容器执行这项设置，创建评分器容器时不限网络。类别：形式化数学与定理证明。

## 我们检查了什么

联网时，评分器能构建项目，并对未修改的初始项目返回有效结果。 我们没有这样给任何正常写出的证明评过分。

- Lean 的构建工具 Lake 打印出 `doc-gen4: URL has changed; deleting … and cloning again`，接着打印 `checking out revision '86d735ecf420e0dbaaf84e2fc2221969f9fca097'`。这是项目清单（manifest）里固定的提交，而不是一直在变的 `main` 分支。它的 `lean-toolchain` 是 `v4.21.0-rc3`。
- 构建成功，`eval_cmd` rc=0，没有错误。
- 未修改的初始项目得到 `valid: true` 和 `score: 0.0`，同时输出 `mode=unweighted, repaired=0/2246, remaining_bad=2246, new_bad=301`，`type_changed` 0 个，`disappeared` 0 个，也没有 HASH 检查。
- 这 301 个 `new_bad` 条目是编译器内部的常量（`_cstage2` 239 个、`_spec_N` 38 个、`_elambda_N` 24 个）。它们不是 `sorry` 目标，权重为 0。初始项目里也有它们（2547 行 BAD，对应 2246 个目标）。

无法离线评分。 在随附的评分器镜像里，`lake build` 在 `--network none` 下会失败。评分器的初始仓库和严格按 `eval_cmd` 准备的提交都会失败。

- 失败的原因是 Lake 打印 `doc-gen4: URL has changed; deleting '…/.lake/packages/doc-gen4' and cloning again`（`build_orig.err`）。另有记录显示，打包的检出副本没有 `origin` 远程仓库，HEAD 是 `0ee5b43…`，而清单里是 `86d735ec…`。这一状态没有留下原始日志，只记在 `lean_family_aux_census.md` 和 `nf_direct.sh` 里的一条注释。
- 离线时，Lake 删掉检出副本并尝试重新克隆，`git` 随即失败（退出码 128）。`eval_cmd` 返回 1，不写任何 JSON。
- 我们预期离线也能得到有效结果，实际没有任何结果。

编译器生成的目标中没有不可达的，只有一小部分风险未经测试。 Lean 编译器会自动生成辅助声明（`X._proof_N`、`X._simp_N` 等）。在任务 `lean_analysis_proofs` 里，同一个评分器要求生成的名称和打印出的类型都完全一致，才给这些辅助目标计分，所以那里有些目标拿不到。在本任务中，我们逐个统计了目标，没有发现能证明完整、正确的解法也拿不到的目标（下界为 0）。

| 目标数 | 辅助目标数 | 辅助目标占分比例 | 脆弱的辅助目标 | 类型中含 `sorry` 的目标 | P 与 ¬P 成对出现 | 不可达目标的下界 |
|---|---|---|---|---|---|---|
| 2246 | 370 | 16.5% | **15 (0.67%)** | 0 | 0 | **0**（至多 0.67% 存在风险） |

- 辅助目标包括 337 个 `_proof`、15 个 `_sizeOf`、10 个 `match`，以及其他种类。
- 这 15 个脆弱的辅助目标是 `BasePerm.instMulActionNearLitter._proof_1/2`、`instGroupNewPerm._proof_1…10`、`instInvNewPerm._proof_1` 和 `instMulActionNewPermCode._proof_1/2`。它们是直接含有占位符的实例字段，以及同一实例里按默认方式填充的同级字段。正常写出的证明可能让它们重新编号。
- 有 96 个 `_proof_N` 辅助目标的父声明是定理，我们预计它们不会变。我们在核心 Lean 中用本镜像的编译器（4.21.0-rc3）做了检查，取四个只差一个常量的 `@[simp]` iff 定理，分别用 `sorry`、项、`omega` 和 `simp` 四种方式证明。每种写法生成的辅助声明都叫 `_proof_1`，类型都是把定理本身的陈述写成等式（`auxstyle/nf_v4.21.out`）。`omega` 证明还会多生成 `_proof_1_1` 和 `_proof_1_2`，它们不是目标。我们没有用评分器实际给这 96 个目标中的任何一个计过分。

随任务发布的说明：“在评分器可以联网时能构建并返回有效结果，仅在未修改的初始项目上展示过（Lake 会在清单固定的提交 86d735ec 重新克隆 doc-gen4）；无法离线评分；370 个辅助目标中有 15 个可能因重新编号而受影响（≤0.67%），未经测试”。

## 影响有多大

- 离线评分只影响不能联网的评分器，这时它根本给不出分数。EdgeBench 的测试框架允许评分器联网，所以实际使用中这不算缺陷。但评分仍要求能访问 GitHub，而且 GitHub 上要一直能取到提交 `86d735ec`。
- 辅助目标重新编号最多影响 0.67% 的分数，而且只影响填了相关实例字段的解题者。这个数是风险上界，不是测得的损失。

任务不改，上述说明随任务一起发布。

## 我们如何检查

- 我们在按摘要固定的原始公开镜像中运行原始评分器（工具链 v4.21.0-rc3）。在评分器未改动的初始源码上，一字不改地运行任务的 `judge.eval_cmd`。同一时间只跑一个容器，参数为 `--memory 4g --cpus 2`。一次用 `--network none`，一次用默认的 bridge 网络并加 `timeout 3600`。
- 统计目标时，我们得绕开 Lake，因为这个镜像里的 Lake 不能离线构建。我们用普通的 `lean` 运行镜像里同一个 `ListDeclAxiom` 辅助程序来生成目标列表，`LEAN_PATH` 指向镜像中已有的编译文件（olean）。然后用其他 Lean 任务用过的同一个分类器套用评分器的目标规则。
- 检查证明写法不会改变名称，用的就是上文那项核心 Lean 检查，由镜像里的编译器运行。

## 局限

- 没有运行任何 AI 模型或求解器。影响只在未修改的初始项目上演示过。
- 没有给任何正常写出的证明评过分，所以这 15 个有风险的目标仍未经测试。
- 目标列表用普通的 `lean` 生成，没有用 `lake build ListDeclAxiom`，但辅助文件和 olean 是同一批。
- 联网时的结果取决于运行当时的 GitHub，只观察过一次。
- 测试提交用评分器的初始源码构建。我们没有核对智能体工作镜像里的初始项目是否与它完全相同。
- 没有逐一检查每个目标是否为真。
- 没有检查工作镜像是否暴露了源项目中的证明，包括 README 中提到的 `Old/` 目录。

## 复现

- 评分器镜像摘要：`sha256:c17cd565…cc4`。
- 联网运行 `eval_cmd`：`evidence/scripts/lean_family_census/nf_networked.sh`。输出位于 `evidence/scripts/lean_family_census/out/new_foundations_consistency/networked/`，包括 `report.json`。
- 离线运行 `eval_cmd`：`evidence/scripts/lean_family_census/run_native.sh`。失败日志为 `out/new_foundations_consistency/native/build_orig.err`。
- 目标统计：`evidence/scripts/lean_family_census/nf_direct.sh`。
- 证明写法检查：`evidence/scripts/lean_family_census/auxstyle/run.sh`。输出位于 `auxstyle/nf_v4.21.out`。
- 支撑记录：`evidence/reviews/lean_family_aux_census.md` 中的 "Separate finding" 和 "Networked judge run" 两节。
