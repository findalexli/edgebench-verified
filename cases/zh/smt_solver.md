# SMT Solver (`smt_solver`)

**结论：** 已修复。<mark>答案检查器按字面文本查找函数的取值，因此有 27 个可满足的隐藏问题是任何求解器都无法拿分的。</mark>

![两条断言分别把 x 绑定到 a 和 b，但在原始检查器中都读取同一个键 (f x)，因此任何答案都无法通过；修复版检查器按实际参数查找 (f a) 和 (f b)，接受正确答案。](figures/smt_solver.svg)

*原始检查器按文本查找函数的取值，因此有 27 个可满足的隐藏问题无法拿分；修复版检查器使用实际参数。*

## 任务要求

智能体要构建一个 SMT 求解器。这个程序判定一组逻辑约束能否被满足（"sat"），若能满足，则打印出一组满足这些约束的取值（即一个模型）。求解器必须打印 "sat followed by a JSON model witness that validates the assertions"（sat，后接一个能使各断言成立的 JSON 模型见证）。

随附的 `smtlib_spec.md` 写道 "Keys are SMT-LIB symbols or canonical ground terms that appear in the assertions"（键是断言中出现的 SMT-LIB 符号或规范的基项）。它说，未解释函数（UF，即由求解器自行选择含义的函数）的取值 "for ground applications needed to evaluate the assertions, such as `"(f a)"`"（针对求值断言所需的基应用给出）。它说 "The evaluator checks every assertion under the witness and enforces congruence"（评测器在见证下检查每条断言，并强制同余）。同余是指函数对相同输入给出相同输出。它还说 "an invalid or missing model receives 0 for that case"（无效或缺失的模型在该用例上不得分）。预期为 sat 的问题，只有在模型有效时才得分。类别：组合优化。

## 问题出在哪里

**规则。** 隐藏评分器的检查代码只按源文本读取 UF 应用的取值，例如 `(f x)`。它不代入 `let` 绑定（局部名称，例如"让 x 代表 a"）。当同一段文本出现在不同的 `let` 绑定之下时，所有出现都必须共用同一个值。

**例子。** 断言为 `(distinct a b)`、`(let ((x a)) (= (f x) a))` 和 `(let ((x b)) (= (f x) b))`。取 f = 恒等函数时它们可满足。在原始评分器下：

- 按规格的描述使用基项键 `(f a)` 和 `(f b)` 时，判定为 `invalid_model: missing model value for (f x)`。
- 加上文本键 `(f x)` 后，判定为 `invalid_model: assertion is false`。

任何答案都无法通过，因为两处应用读取的是同一个键 `(f x)`。

**在隐藏问题集中**（774 个文件：546 个 sat / 228 个 unsat）：

- **27 个 sat 的 QF_UF 文件（15 个 medium、12 个 hard）无法拿分。** 这些是拟群（quasigroup）文件，在每条断言中重新绑定 `?v_0 … ?v_n`。在全部 27 个文件中，按检查器的读法，公式是 unsat 的，而真实公式是 sat 的。在原始镜像上，`QF_UF/79f4ca54c7f5a5f0.smt2` 在两种键写法下都拒绝了一个真实的 z3 模型。
- **另有 42 个隐藏 sat 文件拒绝规格中给出的那种形式的键。** 在这些文件上，一个严格按规格输出基项键的求解器会被拒绝。在那里只有没有文档说明的文本键约定才行得通。

**方向。** 已展示的键值缺陷会导致正确答案被拒绝。Lean `orig_sound` 和 `fixed_sound` 证明：在建模的单一 sort、一元函数的 QF_UF 片段中，检查器接受即意味着公式可满足。它们并没有对整个 Python 评分程序或所有受支持的 SMT-LIB 特性证明这一点；模型与实现的对应关系是论证并经过差分测试的，不是机器证明的。不过，原始检查器可能接受一个本身并不构成函数的见证：下文的 `unused_conflict` 让 f 在同一个参数值上取两个值，而原始评分器接受了它。

**说明：评分器 CPU 数（不属于修复内容）。** eval_cmd 运行 `evaluate.py --timeout 60 --parallel 16`，超时按墙钟时间计（`proc.communicate(timeout=timeout)`，第 690 行）；超时得 0 分。全部四个官方排行榜配置（EdgeBench 提交 6e4e5f4 中的 `examples/all-tasks-k8s/experiment*.yaml`）都为 `smt_solver` 设置了 `judge_cpu_limit: 16`，因此 16 个求解器进程各得一个 CPU。在 CPU 较少的评分器上，例如配置的默认值 4，每个问题在其 60 s 内得到的 CPU 会按比例减少。我们在原始评分器上、用评分器的原样参数、在隐藏集的一个 32 题子集（QF_LIA、hard、预期 unsat）上用一个替身求解器测量了这一点：在 4 个 CPU 下，每题需要 20 s CPU 时间的求解器在全部 32 题上超时，而在 8 个 CPU 下通过（`evidence/runs/smt_solver-cpu4v8-a`、`-b`；`evidence/runs/smt_solver-v2-paired-cpu`、`smt_solver-v2-paired-b-cpu`、`-c-cpu`）。任务文本本身也自相矛盾：任务说明写的是 "16 evaluator workers"，而工作镜像中的 `smtlib_spec.md:118` 写的是 "4 evaluator workers"。在官方的 16 个 CPU 下，这两点都不影响评分，因此作为说明保留。

## 影响有多大

- 完美求解器的最高分从 78.61 降到 72.40，损失 6.21 分。15 个无法拿分的 medium 问题占 medium 档的 15/61。
- 所有求解器都会失去那 27 个同一文本有多种含义的文件。按规格描述输出基项键的求解器，还会失去那 42 个同一文本只有一种含义的文件。

## 修复

修复版改动一个文件 `evaluate.py`。构建检查器时，对每个属于基应用的答案键求值，并把其取值登记在该函数及其参数的**求值后**取值之下。检查时，检查器在当前作用域中对 UF 应用的参数求值，并首先查找该表项；若没有表项，则退回原来的文本查找。同余检查覆盖全部表项和每个求值后的应用。解析、扰动、超时和计分都不变。任务 JSON 唯一的改动是 `judge.image_tag`。

原始版与修复版评分器的并排对照结果。两个镜像都以官方参数和 `--network none` 运行；两者中的隐藏 zip 完全相同。问题集：69 个受影响的隐藏 sat 文件。"多上下文"文件在不同绑定下复用同一文本；"单上下文"文件则不然。

| 测试提交 | 文件 | 原始评分器 | 修复版评分器 | 预期 | 是否符合预期 |
| --- | --- | --- | --- | --- | --- |
| ground（正确，规格中的键） | 27 个多上下文 | invalid_model 27 | **correct 27** | 原始版出错，修复版接受 | 是 |
| ground（正确，规格中的键） | 42 个单上下文 | invalid_model 42 | **correct 42** | 修复版接受 | 是 |
| textual（正确的测试提交） | 42 个单上下文 | correct 42 | correct 42 | 不变 | 是 |
| textual（正确的测试提交） | 27 个多上下文 | unknown 27（无见证） | unknown 27 | 不变 | 是 |
| textual_true（正确的模型） | 27 个多上下文 | invalid_model 27 | **correct 27** | 修复版可以接受（真实模型） | 是 |
| textual_true（正确的模型） | 42 个单上下文 | correct 42 | correct 42 | 不变 | 是 |
| ground_wrong（无效，`-c`） | 27 个多上下文 | invalid_model 27 | invalid_model 27 | 两者都拒绝 | 是 |
| ground_wrong（无效，`-c`） | 42 个单上下文 | invalid_model 42 | invalid_model 42 | 两者都拒绝 | 是 |

用 ground 测试提交运行完整的原始 `eval_cmd`（全部 774 个隐藏文件，`--parallel 16`）。替身求解器在 705 个没有预备答案的文件上回答 `unknown`。

| 评分器 | 原始分数（0–1） | 100 分制得分 | 通过 | 退出码 |
| --- | --- | --- | --- | --- |
| 原始版 | 0.0000 | 0.00 | 0/774 | 0 |
| 修复版 | 0.1249 | 12.49 | 69/774 | 0 |

任务的换算是从 0 到 1 的线性刻度（`tasks/smt_solver.json`），因此 100 分制得分为 100 × 原始分数；评分器自己的汇总行为 `score=0.124948 (12.49/100)`（`repairs/smt_solver-v2/paired/evidence/b/fulleval_lines.txt`）。

问题集上没有任何测试提交从正确变为被拒绝。在 13 个小型构造用例中，只有 `unused_conflict` 如此，这符合预期：该答案通过一个未使用的键让 f 在同一个参数值上取两个值，因此它不定义一个函数。小型用例上的原始分数（0–1 刻度）：原始评分器 0.1615，修复版评分器 0.3231（100 分制下为 16.15 和 32.31）。

**分数兼容性。**

- **可比：** 对于答案只使用文本键的求解器，修复版分数与原始分数可比，只有一个已在 Lean 中证明的例外：在复用了某个已声明常量名称的 `let` 之下的文本键，可能被修复版检查器拒绝（同一模型用基项键写出则能通过）。774 个隐藏文件中没有一个包含这样的 `let`（`evidence/formal/notes/smt_solver.md`）。
- **不可比：**
  - 对于输出基项键的求解器；
  - 在那 27 个多上下文文件上，原始评分器根本无法给分。
- **新增拒绝：** 让函数在相同参数值上取两个值的答案。规格中的 "enforces congruence"（强制同余）本来就排除了这种情况。

## 我们如何检查

- **原始评分器。** 构造的问题和真实的隐藏问题都交给原始评分器运行：使用按摘要固定的原始公开镜像和官方参数（`--perturb --perturb-salt hidden-sebench`）。一个打印固定答案的替身求解器代替了正确的求解器。嵌套最深的 sat 文件（括号深度 2621）被接受。
- **独立检查（z3）。** z3 是一个广泛使用的 SMT 求解器。我们把检查器的接受条件精确编码，并在评分器之外用 z3 求解。为验证这一编码，在编码为 sat 的全部 42 个隐藏文件上，把 z3 模型转换为答案；原始检查器接受了全部 42 个。对全部 774 个隐藏文件的扫描使用了原始的分词规则。z3 确认全部 69 个 ground 答案都是真实模型，并证明全部 69 个错误模型答案都不是模型。
- **算术。** 分数影响根据任务的分档权重重新计算。
- **可重复性。** 并排对照运行重复了三次，结论没有变化（`data/paired-repeatability.md`）。

## 局限

- 没有运行任何 AI 模型或求解器。这里所示的影响只针对我们编写的测试提交和反例，也没有估计对排行榜的影响。
- 答案是由替身求解器回放的 z3 模型，而不是为该任务构建的完整求解器的输出。
- "检查器编码恰好拒绝检查器所拒绝的内容"这一论断，依据的是一个精确性论证和在原始镜像上的运行，没有经过机器证明。
- 错误模型测试提交之所以"不是模型"，依赖于 z3 4.13.0.0。每个错误答案只改动一个 UF 取值，因此这些测试提交并不覆盖所有可能的错误模型。
- 据报告，公开的开发集中含有 2 个无法拿分的 sat 问题；这里没有包含对它的扫描输出。
- 规格文本没有改写；其中 "canonical ground terms"（规范的基项）的措辞现在与检查器一致。
- 只深入检查了 UF 的取键方式。扰动和预检扫描只做了抽查；超时对评分器 CPU 数的依赖，是用替身求解器在一个 32 题子集上测量的（见上文说明）。

## 复现

- 原始评分器镜像：`sha256:2bf3482a…`。
- 构造用例（原始镜像）：`evidence/scripts/smt_solver/run_mini_native.sh`；输出在 `evidence/scripts/smt_solver/mini_native_output.txt`
- 真实隐藏问题（原始镜像）：`evidence/scripts/smt_solver/run_corpus_native.sh` 和 `run_deep_native.sh`
- 问题集扫描和检查器编码：`evidence/scripts/smt_solver/scan_corpus.py --z3`；编码验证：`witness_roundtrip.py`；输出在 `evidence/scripts/smt_solver/results/`
- 分数影响：`evidence/scripts/smt_solver/score_impact.py`
- 原始版与修复版评分器的并排对照运行：`repairs/smt_solver-v2/paired/run.sh`（错误模型测试提交：`run_wrongarm_c.sh`）；补丁：`repairs/smt_solver-v2/repair.patch`；修复版 `evaluate.py` 的 sha256 为 `bbc730f8…2998`
- CPU 数说明：`evidence/runs/smt_solver-cpu4v8-a/run.sh`、`-b`（原始评分器在 4 和 8 个 CPU 下）

支撑记录：`repairs/smt_solver-v2/`（存放修复版的文件夹：README、`source-lock.json`、`paired/results.md`、`paired/evidence/`）。
