# Schemathesis config modernization (`schemathesis_config_modernization`)

**结论：** 已修复。<mark>Phase 3 的测试只检查 `@schemathesis.metric` 返回的东西能否调用，没有检查它是否原样返回该函数。换成修复版测试，包装器会少过一项测试，即分数的 1/160（100 分制下 0.625 分）。</mark>

![Phase 3 测试结果：原始测试让正确的装饰器和包装器都以 15/15 通过；修复版测试使包装器为 15/16。](../figures/schemathesis_config_modernization.svg)

*原始测试无法区分包装器和正确的装饰器；修复版测试增加了一项测试，价值为分数的 1/160。*

## 任务要求

解题者要把 schemathesis 3.39.16（一个用于测试 Web API 的工具）的配置层改造成现代写法。评分靠按阶段分组的隐藏测试。任务说明要求解题者 "Treat `/app/TODO.md` as the authoritative task specification."（把该文件视为权威的任务规格。）`TODO.md` 的 Target 3 写道 "**`@schemathesis.metric` decorator**: Registers a metric function into a registry. Returns the function unchanged."（该装饰器把一个指标函数注册到注册表中，并原样返回该函数。）装饰器是一种函数，它接收另一个函数，返回一个函数顶替原来的那个。`TODO.md` 对 `@schemathesis.check` 也用了同样的说法。类别：系统与软件工程。

## 问题出在哪里

按规格，装饰器必须原样返回该函数。原始测试 `test_metric_decorator_returns_function` 只断言 `callable(another_metric)`。所以一个把调用转给原函数的包装器，和正确的装饰器得分一样。

我们在 Target 3 的一个最小实现上测了 `metric` 的三个变体。

- `identity` 注册函数并把它返回，这是正确的。
- `wrapper` 返回一个用 `functools.wraps` 做的转发包装器，很可能不对。
- `no_register` 根本不注册函数，显然不对。

下面是它们在原始测试（`orig`）和修复版测试（`repaired`）下的 Phase 3 结果。

```
variant=identity    tests=orig     :: 15 passed
variant=identity    tests=repaired :: 16 passed
variant=wrapper     tests=orig     :: 15 passed
variant=wrapper     tests=repaired :: 1 failed, 15 passed
variant=no_register tests=orig     :: 3 failed, 12 passed
variant=no_register tests=repaired :: 4 failed, 12 passed
```

按规格，包装器应该在检查同一性的那项测试上失分。在原始评分器上，包装器却 15/15 全过，和正确的装饰器一样。

这个问题的影响很小。从行为上看，包装器和正确的装饰器几乎没有差别。它保留 `__name__`，用正确的名字注册，返回值相同，也能和收集器、`hypothesis.target` 一起工作。区别只有 `decorated is original` 这一项，以及多了一个 `__wrapped__`。错误的实现比正确的实现得不到任何好处，只是少丢一项测试。作者原意很可能就是要求同一性，因为 Phase 6 的测试对 `@check` 断言了 `result is my_func`；Phase 3 没有这样的检查。

## 影响有多大

最多是总分的 1/160，即 100 分制下 0.625 分。分数是六个阶段的 Σ(weight × passed/total)/10，Phase 3 的权重为 1。修复版的 Phase 3 有 16 项测试。一个通过原有 15 项中 k 项的包装器，所得从 Phase 3 权重的 k/15 降到 k/16，损失 k/2400。k = 15 时损失为 1/160，即实测的 −0.006250。（原来 15 项测试时，这个阶段每项测试值 1/15 × 1/10 = 1/150。）

计分变化也不全是扣分。如果提交的装饰器原样返回函数，但原有 Phase 3 测试只过了 k < 15 项，所得会从 k/15 升到 (k+1)/16，增加 (15 − k)/2400。两种变化每次运行都不超过 1/160。只有用包装器做装饰器的提交，或 Phase 3 只过了一部分的提交，分数才会变。

## 修复

- `/tests/test_03_metric_system.py` 新增 `test_metric_decorator_preserves_exact_function_identity`。这项测试断言 `metric(f) is f`，然后注销该函数。
- `/tests/test.sh` 把 `PHASE3_TOTAL` 和 `PHASE3_EXPECTED` 从 15 改成 16。

权重、解析器、分数刻度和原有的 126 项测试都不变。`task.json.in` 只改了 `judge.image_tag`。

| 变体 | 角色 | 原始评分器（原始结果） | 修复版评分器（原始结果） | 变化 | Phase 3，原始 → 修复 |
|---|---|---|---|---|---|
| starter | 未改动的初始 `/app` | 0.031466 | 0.031466 | 0 | 0/15 → 0/16 |
| identity | 审查者编写的正确 Target 3 叠加实现（`metric` 返回 `func`） | 0.135313 | 0.135313 | **0** | 15/15 → 16/16 |
| wrapper | 很可能错误，返回一个 `functools.wraps` 转发包装器 | 0.135313 | 0.129063 | **−0.006250 (−1/160)** | 15/15 → 15/16 |
| no_register | 无效的测试提交，从不注册 | 0.115313 | 0.110313 | −0.005000 | 12/15 → 12/16 |

每个变体里，结果有变化的测试项只有新增的同一性测试，以及（包装器才有的）Phase 3 "全部通过"项（`test_phase_3`），它由通过变为失败。其余 131 个原有测试项的结果与原始评分器相同。分数是 0–1 刻度上的原始值。按任务的 `linear` 0..1 刻度，100 分制得分 = 100 × 原始值（0.135313 即 13.53）。这些都只是部分得分，因为叠加实现只做了 Target 3，没有完成整个任务。

提交在修复版 Phase 3 的 16 项测试上全过或全不过时，原始版和修复版评分器分数相同。Phase 3 只过了一部分时，两者不可比，因为这个阶段原来有 15 项测试，现在有 16 项，没全过的阶段得到的比例不一样。

## 我们如何检查

- 我们在按摘要固定的原始公开镜像中运行原始评分器。评分器镜像的 `/app` 里是未改动的 schemathesis 3.39.16 初始代码，没有参考解法。每个变体和未改动的初始代码，都在全新的 `--network none` 容器里，用完整的原始 `judge.eval_cmd`（`bash /tests/test.sh` 加结构化解析器）分别跑原始测试和修复版测试。
- 独立检查的参照就是 `TODO.md` 规格里的那句话（"Returns the function unchanged"，即原样返回该函数），新增的测试直接检查这一点。这里用不上形式化模型。
- 我们把原始版和修复版评分器的并排对照运行重复了三次，结果没有变化（`data/paired-repeatability.md`）。

## 局限

- 没有运行任何 AI 模型或求解器。影响只在我们写的测试提交上演示过。
- 叠加实现只是 Target 3 的最小实现，不是该任务的完整解法，所以绝对分数只是部分得分。
- 我们没有检查历史提交，不清楚真实解题者有多常写出包装器式的装饰器。
- 我们没有从固定的工作镜像里重新提取 `TODO.md`。
- 新增的测试检查的是 `schemathesis.generation.metrics.metric`。`TODO.md` 点名的顶层 `schemathesis.metric` 仍只检查能否调用，所以在顶层重新导出的包装器（例如用 `functools.wraps`）依然能通过全部三项 metric 测试，尽管 `schemathesis.metric(f) is f` 为假（本地探测）。要堵上这一点，得再加一条断言，并重新做一次并排对照运行。
- 我们在一台干净的机器上从零重建过修复包（`evidence/runs/materialize-check-g2`，`status: exit=0`）。`materialize.sh` 原样运行，两个输出都与锁定值一致，构建出的镜像里是锁定的测试文件。
- 隐藏测试没有存进本仓库。重新运行检查时，脚本从固定的评分器镜像里提取它们。

## 复现

- 评分器镜像摘要：`sha256:ff71a766…`。

1. 运行 `evidence/scripts/schemathesis_config_modernization/fetch_tests.sh`。它从固定的评分器镜像中提取隐藏测试并应用补丁。
2. 用 `metrics_base.py` 运行 `evidence/scripts/schemathesis_config_modernization/run_in_judge.sh`。保存的输出为 `observed_output.txt`。

原始版和修复版评分器的并排对照运行是 `repairs/schemathesis_config_modernization-v2/paired/run.sh`，结果在 `paired/results.md` 和 `paired/raw-summary.md` 中。修复本身在 `repairs/schemathesis_config_modernization-v2/repair.patch`、`Dockerfile` 和 `source-lock.json` 中。

支撑记录：`repairs/schemathesis_config_modernization-v2/`（存放修复版的文件夹）和 `evidence/reviews/schemathesis_config_modernization.md`。
