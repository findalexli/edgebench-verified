# PFR Formalization (`pfr_formalization`)

**结论：** 类型污染的修复得到验证；目标得分的恢复和解题镜像的集成尚待完成。<mark>有五个计分命题的类型中带有一个真正的 `sorry`，它是 Lean 的模块系统在处理一个用 `variable` 声明的自动参数时静默加入的。因此任何提交都无法拿到这五项（100 分制下 1.18 分），而之后用到其中任何一项的证明也会被标记为依赖 `sorry`。修复版把这个参数直接写进这五个命题；其他一切不变。同一个带有辅助目标的定理用两种写法给出的诚实证明，得分相同。</mark>

## 任务要求

解题者在一个关于 PFR 猜想（加性组合学中的一个结果）的项目中工作，该项目用 Lean 4（一种用于机器检验数学证明的语言）写成。任务说明要求解题者 "finish **all** sorries in this folder"（补完该文件夹中的**所有** sorry；`sorry` 是缺失证明的占位符），并说 "we value minor progress"（我们重视微小的进展）。它还警告："do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation"（不要修改已有 lemma/theorem/def 的签名，否则无法通过评测），以及 "we check the axioms transitively, finishing a theorem without completeing precedent lemma will not count."（我们传递地检查公理，若未完成前置引理就完成一个定理，不计分）。分数是基线中依赖 `sorry` 的声明里，被提交变成不使用额外公理、且打印出的类型不变的声明所占的不加权比例。这样的目标共有 423 个。类别：形式化数学与定理证明。

## 问题出在哪里

我们检查了两个可能的问题。第一个，关于编译器生成的目标，在所测试的一个辅助目标和两种证明写法上没有出现。第二个是真实存在的：有五个目标无法得分。

**一个生成的辅助目标在两种测试过的证明写法下得分相同。** 这并不能说明全部七个生成目标、或任何一种证明写法都得到公平计分。同一个评分器在 `lean_analysis_proofs` 中只有在生成的名称和打印出的类型都完全一致时，才为编译器生成的辅助目标（`X._proof_N`、`X._simp_N` 等）计分。在那里，至少有 44 个辅助目标（连同 3 个占位命题和 2 个假命题，共占全部 2901 个目标中的 49 个，即 1.69%）是任何诚实、完整的解法都无法拿到的，而且分数取决于证明写法。在本任务中（`evidence/reviews/lean_family_aux_census.md`；类型中带有真正 `sorry` 的数量来自下文所述的类型探测）：

| 目标数 | 编译器生成的目标 | 它们占分数的比例 | 观察到的脆弱生成目标 | 类型中含 `sorry` | P/¬P 成对 | 无法拿到的目标的下界 |
|---|---|---|---|---|---|---|
| 423 | 7 | 1.65% | **0** | **5** | 0 | **5** |

这些辅助目标是 7 个 `_simp` 引理，其中没有一个自身含有 `sorry`。在原始评分器上，用同一定理的诚实证明做的测试：

| 提交 | 在原始评分器上的结果 |
|---|---|
| 未修改的初始项目（正确的测试提交） | 0/423，没有 `type_changed`，没有 `disappeared` |
| 写法 A（`Iff.rfl`） | 2/423：`mem_symmGroup` 和 `mem_symmGroup._simp_1` |
| 写法 B（策略证明） | 2/423：`mem_symmGroup` 和 `mem_symmGroup._simp_1` |

所测试的 `_simp` 辅助目标在这两种证明写法下得分相同。其他六个 `_simp` 辅助目标没有评分。

**有五个目标无法得分。** 五个目标（`PFR_projection`、`PFR_projection'`、`torsion_free_doubling`、`torsion_dist_shrinking`、`app_ent_PFR`）打印为 `μ : autoParam (Measure Ω) sorry`。这个绑定来自 `PFR/WeakPFR.lean` 中的 `variable (μ : Measure Ω := by volume_tac)`，而该文件是一个 Lean `module` 文件。其中的公开命题不能引用保存该策略的私有辅助声明，于是 Lean 在那里放入一个表示错误的 `sorry`，却不报告任何错误。

我们在评分器镜像内部做了检查。这五个目标的类型中都含有常量 `sorryAx`（`evidence/runs/pfr_formalization-autoparam-probe/result/out/probe_baseline.out`）。评分器既从声明的证明中、也从其类型中收集公理（`ListDeclAxiom.lean` 中的 `collectAxiomDeps`），并要求类型文本保持不变。因此任何证明都无法拿到它们。

我们用任务自己的评分器确认了这一点。在同一绑定下用 `rfl` 证明的一个引理被标记为依赖 `sorry`（`evidence/runs/pfr_formalization-autoparam-eval/`；`repairs/pfr_formalization-v2/paired/results.md` 中的变体 T）。一个参数普通、证明只是应用了那个引理的引理（变体 D）也是如此：评分器还会收集证明中用到的每个引理的类型中的公理。

在上游的 PFR 证明（teorth/pfr `master`）中，`weak_PFR_asymm_prelim`、`weak_PFR_asymm`、`weak_PFR` 和 `weak_PFR_int` 是通过这五个目标证明的，因此照着上游证明做的解题者也会失去这四项。这是由实测的规则和上游的证明结构推出的，没有用真实证明运行过。

## 影响有多大

任何提交都无法拿到 423 个目标中的这 5 个（5/423 = 100 分制下 1.18 分，实测）；因此分数至多为 418/423 = 98.82。这是一个上限，并不是已证明可以达到的分数；其余 418 个目标并没有全部被证明。一个通过这些引理证明 `weak_PFR_asymm_prelim`、`weak_PFR_asymm`、`weak_PFR` 和 `weak_PFR_int` 的解题者，也会失去这些项：至多 9 个目标，即 9/423 = 2.13 分（如上所述，是推断）。这五项只让本来会证明它们的解题者丢分（其他人无论如何在这几项上都得 0 分），因此排名可能改变；是否有提交证明了它们，尚不清楚。用修复版评分器对已有提交重新评分会得到相同的分数，因为每份提交都带着旧文件的副本。只有从修复后的文件出发的新运行才能拿到这些分。

## 修复

在 `PFR/WeakPFR.lean` 中，两个自动测度参数及其概率测度假设从 `variable` 移入这五个引理的签名。这一改动同时作用于评分器的基线和解题者的初始项目，评分器的构建文件用任务自己的工具重新生成。计分的仍是同样的 423 个目标。五个打印出的类型只在自动参数上改变：`sorry` 变成一个具名的辅助声明，例如 `PFR_projection._auto_1`（`repairs/pfr_formalization-v2/paired/out/listing_compare.txt`）。评分器、`eval_cmd` 和分数刻度（`rescale`：线性，0.0 到 1.0）不变。修复包：`repairs/pfr_formalization-v2/`。

| 提交 | 原始评分器 | 修复版 |
|---|---|---|
| 未改动的初始项目 | 0/423 | 0/423 |
| 两个按这五个目标的方式陈述、用 `rfl` 证明的引理 | 两者都被标记为依赖 `sorry` | 两者都得分 |
| 一个参数普通、应用了其中之一的引理 | 被标记为依赖 `sorry` | 得分 |
| 一个通过仍使用 `sorry` 的引理证明的目标，外加一个用 `sorry` 证明的引理 | 被拒绝 | 被拒绝 |

表中每个分数都是 0.0，因为没有提交证明这五个真实目标中的任何一个；不同的是新增引理的状态。在每次运行中，其余 418 个目标的状态保持不变，`type_changed` 和 `disappeared` 都为 0，`weak_PFR` 和 `entropic_PFR_conjecture` 的 HASH 检查通过，`eval_cmd` 退出码为 0（`repairs/pfr_formalization-v2/paired/results.md`，来自 `evidence/runs/pfr_formalization-v2-paired-v1/` 和 `-v2/` 中的报告）。在修复版基线中做的类型探测显示，这五个目标的类型中都没有 `sorryAx`；它们唯一的 `sorryAx` 现在来自它们自身的 `sorry` 证明（`repairs/pfr_formalization-v2/paired/out/probe_v2_baseline.out`）。

**分数与原始版可比。** 分母仍为 423；一份提交如果没有证明这五个目标中的任何一个，也没有证明用到它们的引理，得分就与以前完全相同。

## 我们如何检查

- **原始评分器，来自按摘要固定的公开镜像**（工具链 v4.29.0）。任务的 `judge.eval_cmd` 在评分器镜像中运行，同一时间一个容器，使用 `--network none`。它对未修改的基线源码，以及 `PFR/HundredPercent.lean` 的两个诚实变体评分，这两个变体分别用 `Iff.rfl`（A）和 `constructor <;> intro h <;> exact h`（B）证明 `@[simp] mem_symmGroup`。实际使用的 `ListDeclAxiom.lean` 还检查 `weak_PFR` 和 `entropic_PFR_conjecture` 的 HASH 行，它们在基线上为真。
- **在镜像内部统计。** 构建了基线的 `ListDeclAxiom` 列表。每个目标都用与 `lean_analysis_proofs` 相同的目标规则和辅助名称模式分类。镜像内部的一个探测检查每个辅助目标是否自身含有 `sorry`。
- **类型探测。** 评分器镜像中的一个 Lean 探测（`EbvProbe.lean`）读取这五个目标类型中的公理，与它们的证明分开：在原始版中五个都含 `sorryAx`，在修复版中一个也没有。
- **并排对照测试。** 原始评分器和修复版评分器在 E2B 工作节点上对同样的四份提交运行（`evidence/runs/pfr_formalization-v2-paired-v1/` 和 `-v2/`，均为 `status: exit=0`）。修复版作业用 `materialize.sh` 从公开镜像重建修复包，包括重新构建 Lean，检查重新生成的列表与预期列表逐字节一致，运行 `docker build`，并在它构建的镜像中评分。

## 局限

- 没有运行任何 AI 模型或解题者。影响只在初始项目和我们编写的测试提交上展示。
- 没有运行这五个目标的真实证明。它们在修复版中可以拿到，是通过以同样方式陈述的引理和对其类型的检查来展示的。
- 四个 `weak_PFR*` 目标会丢失，是由实测规则和上游证明结构推出的，没有用真实证明运行过。
- 确认缺陷和测试修复的评分器运行中，由于磁盘空间不足，把 eval_cmd 对 7.0 GB `.lake` 的复制替换为复制 `.lake/build` 并加一个指向 `.lake/packages` 的符号链接。其他每一步都原样执行，初始项目的得分与原样运行一致（0/423）。
- 修复版工作镜像（`Dockerfile.work`）在干净机器重建检查中构建过一次（`evidence/runs/materialize-check-pfr`，`status: exit=0`），其中修复后的 `PFR/WeakPFR.lean` 的 sha256 与锁定值一致；没有解题者在其中运行过。在固定的工作镜像中，每个 `PFR/*.lean` 文件都与评分器中的逐字节相同（作业 `pfr_formalization-v2-extract`）。这项检查需要为节省磁盘而把工作镜像那一步移到评分器步骤之后；现在 `materialize.sh` 自己就这样做。
- **未经验证的部分及其原因：五个实际目标的得分。** 要说明对五个修复后目标的真实证明现在能够得分，需要这些定理的真实证明，而这需要 PFR 项目的数学内容；我们没有这样的证明，于是用以同样方式陈述的引理代替它们。这一点作为已记录的局限保留。
- 用同一定理的诚实证明做的测试只覆盖一个模块。
- 一个修改定义或实例主体（签名不变）的解题者，仍可能使依赖它们的辅助声明重新编号。这一点没有测量。
- 没有检查 `AddCombi` 依赖与 PFR 内容的重叠程度。
- 没有逐一检查每个目标是否为真。
- 没有检查工作镜像是否暴露了上游的证明。

## 复现

- 评分器镜像：`sha256:07b51e8e…09cc4`。工作镜像：`sha256:3be95d28…7c86`。
- 目标统计：`evidence/scripts/lean_family_census/pipeline.sh <task_id> <image@digest> <project dir> <root module>`。
- 用诚实变体原样运行 `eval_cmd`：`evidence/scripts/lean_family_census/run_native.sh <task_id> <image@digest> evidence/scripts/lean_family_census/pfr_native PFR/HundredPercent.lean`。输出：`evidence/scripts/lean_family_census/out/pfr_formalization/`；得分目标的集合在 `native/repaired.txt` 中。
- 在原始评分器上的类型探测和触发测试：`evidence/runs/pfr_formalization-autoparam-probe/` 和 `evidence/runs/pfr_formalization-autoparam-eval/`。
- 原始评分器与修复版评分器的并排对照测试：`evidence/runs/pfr_formalization-v2-paired-v1/` 和 `-v2/`（`run.sh`、`grade_variants.sh`、`make_variant.py`）；摘要见 `repairs/pfr_formalization-v2/paired/results.md`。
- 修复版：`repairs/pfr_formalization-v2/`（`README.md`、`repair.patch`、`materialize.sh`、`source-lock.json`）。
- 支撑记录：`evidence/reviews/lean_family_aux_census.md`。
