# VLIW Kernel Optimization (`vliw_kernel_optimization`)

**结论：** 保留（附说明）。<mark>发现的唯一问题涉及评分器隔离，不在本次发布的范围之内；运行过的两份诚实测试提交都得到了正确的评分。</mark>

## 任务要求

解题者为一个模拟的 VLIW 处理器（一种同时发射多条指令的处理器）编写程序生成器。任务文本写道："Implement KernelBuilder.build_kernel so the generated instruction program is correct and faster on the simulator."（实现该方法，使生成的指令程序正确，并在模拟器上运行得更快。）它还写道："Modify only solution.py. Do not change problem.py, runner.py, verifier.py, test cases, or hard-code public or hidden seeds."（只修改 solution.py；不要改动其他给定文件或测试用例，也不要硬编码公开或隐藏的种子。）

只有当每个正确性用例都通过时，生成的程序才计分。此时其原始结果（换算为 0–100 分之前）就是性能用例上的周期数。分数刻度是 `log_min`，一种周期越少得分越高的对数刻度。其 0 分参考点（基线）为 4475.53 个周期，100 分参考点（专家水平）为 1000 个周期。类别：系统与软件工程。

## 我们检查了什么

没有发现会改变分数的缺陷。检查了以下部分：

- **隐藏用例。** 文件中有 8 个正确性用例和 1 个性能用例。全部用例的高度为 10、轮数为 16、批大小为 256。
- **原始评分器上的诚实测试提交：**

| 提交 | 原始评分器结果 | 100 分制得分 |
|---|---|---|
| 初始的 `solution.py`（正确、简单的内核） | 有效，9/9 PASSED，周期数 = 147734 | 0 |
| 空程序（已知错误） | 无效，0/9，无分数 | （无效） |

正确性检查拒绝了空程序，而正确的初始内核得到了有效的周期数。

- **评分器隔离** 不在本次发布的范围之内（这是 EdgeBench 的设计选择）。没有发现影响诚实解题者的评分缺陷。

**随任务发布的说明。** 本次发布不评估评分器隔离（这是 EdgeBench 的设计选择）。运行过的两份诚实对照提交（初始内核和一个空程序）在原始评测器上得到了正确的评分。

## 影响有多大

对诚实的提交，没有测得任何影响。

**刻度在低于 1000 个周期时饱和。** `log_min` 在 100 处截断，即在 1000 个周期的专家参考点处达到上限。一次第三方的 Claude Opus 5.5 运行（4 小时，以 `adafadaq/edgebench-opus-5-5-xhigh-rollouts` 发布在 Hugging Face 上）在这个评分器上的全部 18 份提交都有效，且都以 9/9 通过。其内核分别用了 1122、1027、979、970、966、965、962、957、956、951 和 950 个周期（agent-1 到 agent-11，`report.json` 中的 `score`）。不截断时，这些对应 92.3、98.2、101.4、102.0、…、103.4，因此从 979 个周期起的每个内核都得 100 分，刻度无法区分它们。已发布的最佳结果是 85.6（GPT-5.5，12 小时，`tasks/README.md`），约为 1240 个周期，因此已发布的分数不受影响。950 个周期的内核在 8 个正确性用例和 1 个性能用例之外是否正确，没有检查；其源码没有查看。

不作改动；上述说明随任务一起发布。

## 我们如何检查

- **在按摘要固定的原始公开镜像中运行原始评分器。** 任务 JSON 中的原始 `eval_cmd` 在评分器镜像中以 `--network none` 原样运行。只有 `solution.py` 被替换为各份测试提交。`problem.py` 与 `tests/frozen_problem.py` 逐字节相同。
- **分数刻度。** 100 分制得分用本仓库的 `score_rescale.py` 计算（`log_min`，截断到 0–100）。
- 这里不适用形式化模型。

## 局限

- 我们没有运行任何 AI 模型或求解器。评分器的运行针对的是我们编写的测试提交；上文的第三方运行只读取了其结果，没有重新评分。
- 初始内核是我们运行过的唯一正确的测试提交。第三方运行的内核（最低到 950 个周期）没有重新运行，它们在 9 个隐藏用例之外的输入上是否正确也没有检查。
- 两份测试提交的运行记录不在本仓库中。
- 工作镜像没有运行。关于解题者能看到 `runner.py` 和 `verifier.py` 的说法，依据的是任务的 `submit_exclude` 列表和任务卡。
- 没有检查历史提交。

## 复现

- 第三方运行：`evidence/runs/opus55-rollouts-meta/result/meta/opus-16x4h-1009-0036-w1/vliw_kernel_optimization/`（`final_result.json`、`submissions/*/report.json`）。
- 在固定的评分器镜像中，以 `--network none --memory 4g --cpus 2` 运行 `tasks/vliw_kernel_optimization.json` 中的原始 `eval_cmd`。可使用随附的初始 `solution.py`，或一个空程序的 `solution.py`。
- 固定标识：
  - 评分器镜像：`seededge/edgebench.judge.vliw_kernel_optimization@sha256:e0d5eeaf24e98c8a53bd04e2d268cd662ae41871340944baf445afc0274eef5f`。
  - 任务 JSON：sha256 `b6861e44…57d3`。
  - `runner.py`：`2c49071045bdd796fd5c53abcc70717e700e69b913ccae658eb671dc77ea1172`。
  - `verifier.py`：`4b0bc76cf87dedb68b166ea481c10ebef3eb8a684dc8dc20c283cb3d18ba2fd5`。
  - `problem.py`：`fadb0f0858e2259f5759077a5544b9906dad3ceee80d37b4f0aa77da730c93c9`。
  - 初始 `solution.py`：`778c1dceb6e8731424301faa93d47f253ed15bc4016ac002495c5538cf1b39da`。
  - `test_cases/hidden_cases.json`：`81727bbefd0bfa90d2a9e21eaf518a2571d7d93dacc2068c177c886f06050fea`。
