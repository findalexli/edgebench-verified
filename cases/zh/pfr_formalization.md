# PFR Formalization (`pfr_formalization`)

**结论：** 类型污染的修复得到验证；目标得分的恢复和解题镜像的集成尚待完成。<mark>有五个计分命题的类型里藏着一个真正的 `sorry`：Lean 的模块系统处理一个用 `variable` 声明的自动参数时，悄悄把它加了进去。所以任何提交都拿不到这五项（100 分制下 1.18 分），之后用到其中任何一项的证明也会被判为依赖 `sorry`。修复版把这个参数直接写进这五个命题，其余一概不变。对同一个带辅助目标的定理，两种写法的正常证明得分相同。</mark>

## 任务要求

解题者面对的是一个 Lean 4（一种用于机器检验数学证明的语言）项目，内容是 PFR 猜想（加性组合学中的一个结果）。任务说明要求解题者 "finish **all** sorries in this folder"（补完该文件夹中的**所有** sorry；`sorry` 是缺失证明的占位符），并说 "we value minor progress"（我们重视微小的进展）。它还警告："do not modify the signature of existing lemma/theorem/def as these changes will not pass the judge evaluation"（不要修改已有 lemma/theorem/def 的签名，否则无法通过评测），以及 "we check the axioms transitively, finishing a theorem without completeing precedent lemma will not count."（我们传递地检查公理，若未完成前置引理就完成一个定理，不计分）。计分方法：基线里有一批依赖 `sorry` 的声明，看提交把其中多大比例改成了不用额外公理、打印出的类型也不变的声明，不加权。这样的目标一共 423 个。类别：形式化数学与定理证明。

## 问题出在哪里

我们查了两个可能的问题。第一个与编译器生成的目标有关，在测过的一个辅助目标和两种证明写法上没有出现。第二个确实存在：有五个目标拿不到分。

**一个生成的辅助目标在两种测过的证明写法下得分相同。** 这不能说明七个生成目标全都、或任何证明写法都能公平计分。在 `lean_analysis_proofs` 中，同一个评分器要求生成的名称和打印出的类型都完全一致，才给编译器生成的辅助目标（`X._proof_N`、`X._simp_N` 等）计分。那里至少有 44 个辅助目标是任何正确、完整的解法都拿不到的（加上 3 个占位命题和 2 个假命题，共 49 个，占全部 2901 个目标的 1.69%），而且分数随证明写法而变。本任务的情况如下（`evidence/reviews/lean_family_aux_census.md`；类型中带真正 `sorry` 的数目来自下文的类型探测）：

| 目标数 | 编译器生成的目标 | 它们占分数的比例 | 观察到的脆弱生成目标 | 类型中含 `sorry` | P/¬P 成对 | 无法拿到的目标的下界 |
|---|---|---|---|---|---|---|
| 423 | 7 | 1.65% | **0** | **5** | 0 | **5** |

这些辅助目标是 7 个 `_simp` 引理，没有一个自身含 `sorry`。我们在原始评分器上用同一定理的两种正常证明做了测试：

| 提交 | 在原始评分器上的结果 |
|---|---|
| 未修改的初始项目（正确的测试提交） | 0/423，没有 `type_changed`，没有 `disappeared` |
| 写法 A（`Iff.rfl`） | 2/423：`mem_symmGroup` 和 `mem_symmGroup._simp_1` |
| 写法 B（策略证明） | 2/423：`mem_symmGroup` 和 `mem_symmGroup._simp_1` |

测过的那个 `_simp` 辅助目标在两种写法下得分相同。另外六个 `_simp` 辅助目标没有评分。

**有五个目标拿不到分。** 五个目标（`PFR_projection`、`PFR_projection'`、`torsion_free_doubling`、`torsion_dist_shrinking`、`app_ent_PFR`）打印出来是 `μ : autoParam (Measure Ω) sorry`。这个绑定来自 `PFR/WeakPFR.lean` 里的 `variable (μ : Measure Ω := by volume_tac)`，而这个文件是 Lean 的 `module` 文件。文件里的公开命题不能引用保存该策略的私有辅助声明，于是 Lean 在那里塞了一个表示错误的 `sorry`，却一个错误也不报。

我们在评分器镜像里检查过：这五个目标的类型中都有常量 `sorryAx`（`evidence/runs/pfr_formalization-autoparam-probe/result/out/probe_baseline.out`）。评分器既从声明的证明里收集公理，也从它的类型里收集（`ListDeclAxiom.lean` 中的 `collectAxiomDeps`），还要求类型文本不变。所以无论怎么证，都拿不到这五项。

我们用任务自己的评分器确认了这一点。在同一绑定下用 `rfl` 证明的一个引理，被判为依赖 `sorry`（`evidence/runs/pfr_formalization-autoparam-eval/`；`repairs/pfr_formalization-v2/paired/results.md` 中的变体 T）。另一个引理参数是普通的，证明只是套用了前面那个引理（变体 D），结果也一样：评分器还会收集证明中用到的每个引理的类型里的公理。

在上游的 PFR 证明（teorth/pfr `master`）里，`weak_PFR_asymm_prelim`、`weak_PFR_asymm`、`weak_PFR` 和 `weak_PFR_int` 都是借这五个目标证出来的，所以照上游证明做的解题者也会丢掉这四项。这是从实测规则和上游证明结构推出来的，没有拿真实证明跑过。

## 影响有多大

423 个目标里的这 5 个，任何提交都拿不到（5/423 = 100 分制下 1.18 分，实测），所以分数最多是 418/423 = 98.82。这是上限，并非已证明能达到的分数；其余 418 个目标并没有全部证出来。解题者如果借这些引理证明 `weak_PFR_asymm_prelim`、`weak_PFR_asymm`、`weak_PFR` 和 `weak_PFR_int`，这几项也会丢：最多 9 个目标，即 9/423 = 2.13 分（如上所述，属于推断）。只有本来能证出这五项的解题者才会因此丢分（其他人在这几项上反正都是 0 分），所以排名可能变化；有没有提交证出过它们，目前不清楚。用修复版评分器重评已有提交，分数不会变，因为每份提交都带着旧文件的副本。只有从修复后的文件开始的新运行，才拿得到这些分。

## 修复

在 `PFR/WeakPFR.lean` 中，把两个自动测度参数及其概率测度假设从 `variable` 挪进这五个引理的签名。评分器的基线和解题者的初始项目都做了这一改动，评分器的构建文件用任务自己的工具重新生成。计分的仍是同样的 423 个目标。五个打印出的类型只有自动参数变了：`sorry` 换成了一个具名的辅助声明，例如 `PFR_projection._auto_1`（`repairs/pfr_formalization-v2/paired/out/listing_compare.txt`）。评分器、`eval_cmd` 和分数刻度（`rescale`：线性，0.0 到 1.0）不变。修复包：`repairs/pfr_formalization-v2/`。

| 提交 | 原始评分器 | 修复版 |
|---|---|---|
| 未改动的初始项目 | 0/423 | 0/423 |
| 两个按这五个目标的方式陈述、用 `rfl` 证明的引理 | 两者都被判为依赖 `sorry` | 两者都得分 |
| 一个参数普通、套用了其中之一的引理 | 被判为依赖 `sorry` | 得分 |
| 一个通过仍使用 `sorry` 的引理证明的目标，外加一个用 `sorry` 证明的引理 | 被拒绝 | 被拒绝 |

表中分数全是 0.0，因为没有提交证出这五个真实目标中的任何一个；变化在于新增引理的状态。每次运行里，其余 418 个目标的状态都没变，`type_changed` 和 `disappeared` 都为 0，`weak_PFR` 和 `entropic_PFR_conjecture` 的 HASH 检查通过，`eval_cmd` 退出码为 0（`repairs/pfr_formalization-v2/paired/results.md`，取自 `evidence/runs/pfr_formalization-v2-paired-v1/` 和 `-v2/` 中的报告）。在修复版基线上做的类型探测显示，这五个目标的类型里都已没有 `sorryAx`；它们仅剩的 `sorryAx` 来自各自的 `sorry` 证明（`repairs/pfr_formalization-v2/paired/out/probe_v2_baseline.out`）。

**分数与原始版可比。** 分母仍是 423。一份提交只要既没证这五个目标中的任何一个，也没证用到它们的引理，得分就和以前完全一样。

## 我们如何检查

- **原始评分器，来自按摘要固定的公开镜像**（工具链 v4.29.0）。在评分器镜像里运行任务的 `judge.eval_cmd`，同一时间只开一个容器，使用 `--network none`。评分对象是未改动的基线源码，以及 `PFR/HundredPercent.lean` 的两个正常变体：分别用 `Iff.rfl`（A）和 `constructor <;> intro h <;> exact h`（B）证明 `@[simp] mem_symmGroup`。实际使用的 `ListDeclAxiom.lean` 还检查 `weak_PFR` 和 `entropic_PFR_conjecture` 的 HASH 行，这两行在基线上为真。
- **在镜像内统计。** 构建了基线的 `ListDeclAxiom` 列表，每个目标都按与 `lean_analysis_proofs` 相同的目标规则和辅助名称模式分类。镜像内的一个探测检查每个辅助目标自身是否含 `sorry`。
- **类型探测。** 评分器镜像里的一个 Lean 探测（`EbvProbe.lean`）撇开证明，单独读这五个目标类型中的公理：原始版五个都含 `sorryAx`，修复版一个也没有。
- **并排对照测试。** 在 E2B 工作节点上，用原始评分器和修复版评分器评同样的四份提交（`evidence/runs/pfr_formalization-v2-paired-v1/` 和 `-v2/`，均为 `status: exit=0`）。修复版作业用 `materialize.sh` 从公开镜像重建修复包，其中包括重新构建 Lean、核对重新生成的列表与预期列表逐字节一致、运行 `docker build`，然后在构建出的镜像里评分。

## 局限

- 没有运行任何 AI 模型或解题者。影响只在初始项目和我们写的测试提交上演示过。
- 没有运行这五个目标的真实证明。说它们在修复版里拿得到，依据的是按同样方式陈述的引理，以及对其类型的检查。
- 四个 `weak_PFR*` 目标会丢分，是从实测规则和上游证明结构推出来的，没有拿真实证明跑过。
- 在确认缺陷和测试修复的评分器运行中，因为磁盘空间不够，eval_cmd 复制 7.0 GB `.lake` 这一步改成了只复制 `.lake/build`，再加一个指向 `.lake/packages` 的符号链接。其余每一步都原样执行，初始项目的得分与原样运行一致（0/423）。
- 修复版工作镜像（`Dockerfile.work`）在干净机器的重建检查中构建过一次（`evidence/runs/materialize-check-pfr`，`status: exit=0`），镜像里修复后的 `PFR/WeakPFR.lean` 的 sha256 与锁定值一致；还没有解题者在里面跑过。在固定的工作镜像里，每个 `PFR/*.lean` 文件都与评分器中的逐字节相同（作业 `pfr_formalization-v2-extract`）。为了省磁盘，这项检查得把工作镜像那一步挪到评分器步骤之后；现在 `materialize.sh` 本身就是这样做的。
- **未经验证的部分及原因：五个实际目标的得分。** 要说明五个修复后目标的真实证明现在能得分，就需要这些定理的真实证明，而那要用到 PFR 项目的数学内容。我们没有这样的证明，只好用按同样方式陈述的引理代替。这一点作为已记录的局限保留。
- 用同一定理的正常证明做的测试只覆盖了一个模块。
- 解题者如果改了定义或实例的主体（签名不变），依赖它们的辅助声明仍可能重新编号。这一点没有测量。
- 没有检查 `AddCombi` 依赖与 PFR 内容的重叠程度。
- 没有逐一检查每个目标是否为真。
- 没有检查工作镜像是否暴露了上游的证明。

## 复现

- 评分器镜像：`sha256:07b51e8e…09cc4`。工作镜像：`sha256:3be95d28…7c86`。
- 目标统计：`evidence/scripts/lean_family_census/pipeline.sh <task_id> <image@digest> <project dir> <root module>`。
- 用正常变体原样运行 `eval_cmd`：`evidence/scripts/lean_family_census/run_native.sh <task_id> <image@digest> evidence/scripts/lean_family_census/pfr_native PFR/HundredPercent.lean`。输出：`evidence/scripts/lean_family_census/out/pfr_formalization/`；得分目标的集合在 `native/repaired.txt` 中。
- 在原始评分器上的类型探测和触发测试：`evidence/runs/pfr_formalization-autoparam-probe/` 和 `evidence/runs/pfr_formalization-autoparam-eval/`。
- 原始评分器与修复版评分器的并排对照测试：`evidence/runs/pfr_formalization-v2-paired-v1/` 和 `-v2/`（`run.sh`、`grade_variants.sh`、`make_variant.py`）；摘要见 `repairs/pfr_formalization-v2/paired/results.md`。
- 修复版：`repairs/pfr_formalization-v2/`（`README.md`、`repair.patch`、`materialize.sh`、`source-lock.json`）。
- 支撑记录：`evidence/reviews/lean_family_aux_census.md`。
