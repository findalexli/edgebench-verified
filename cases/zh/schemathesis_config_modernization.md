# Schemathesis config modernization (`schemathesis_config_modernization`)

**结论：** 已修复。<mark>Phase 3 的测试只检查 `@schemathesis.metric` 返回的是可调用对象，而不检查它是否原样返回该函数；在修复版测试下，一个包装器会失去一个测试项，即分数的 1/160（100 分制下 0.625 分）。</mark>

![Phase 3 测试结果：原始测试让正确的装饰器和包装器都以 15/15 通过；修复版测试使包装器为 15/16。](figures/schemathesis_config_modernization.svg)

*原始测试无法区分包装器和正确的装饰器；修复版测试增加了一项测试，价值为分数的 1/160。*

## 任务要求

解题者对 schemathesis 3.39.16（一个用于测试 Web API 的工具）的配置层进行现代化改造。按阶段分组的隐藏测试为结果评分。任务说明要求解题者 "Treat `/app/TODO.md` as the authoritative task specification."（把该文件视为权威的任务规格。）`TODO.md` 的 Target 3 写道："**`@schemathesis.metric` decorator**: Registers a metric function into a registry. Returns the function unchanged."（该装饰器把一个指标函数注册到注册表中，并原样返回该函数。）装饰器是这样一种函数：它接受另一个函数，并返回一个函数来代替它。`TODO.md` 对 `@schemathesis.check` 使用了同样的措辞。类别：系统与软件工程。

## 问题出在哪里

**规则。** 装饰器必须原样返回该函数。原始测试 `test_metric_decorator_returns_function` 只断言 `callable(another_metric)`。因此，一个把调用转发给原函数的包装器，与正确的装饰器得分相同。

**例子。** 在 Target 3 的一个最小实现上测试了 `metric` 的三个变体：

- `identity` 注册该函数并将其返回。这是正确的。
- `wrapper` 返回一个用 `functools.wraps` 构建的转发包装器。这很可能是错误的。
- `no_register` 从不注册该函数。这显然是错误的。

在原始测试（`orig`）和修复版测试（`repaired`）下的 Phase 3 结果：

```
variant=identity    tests=orig     :: 15 passed
variant=identity    tests=repaired :: 16 passed
variant=wrapper     tests=orig     :: 15 passed
variant=wrapper     tests=repaired :: 1 failed, 15 passed
variant=no_register tests=orig     :: 3 failed, 12 passed
variant=no_register tests=repaired :: 4 failed, 12 passed
```

按规格的预期：包装器应当失去检查同一性的那个测试项。在原始评分器上的实际结果：包装器以 15/15 通过，与正确的装饰器相同。

**为什么重要，以及为什么只是略微重要。** 在行为上，包装器几乎等价于正确的装饰器。它保留 `__name__`，以正确的名称注册，返回相同的值，并能与收集器和 `hypothesis.target` 配合工作。唯一的区别是 `decorated is original` 以及 `__wrapped__` 的存在。错误的实现相对正确的实现没有任何优势；它只是避免失去一个测试项。作者很可能本意就是要求同一性：Phase 6 的测试对 `@check` 断言了 `result is my_func`，但 Phase 3 没有这样的检查。

## 影响有多大

至多为总分的 1/160，即 100 分制下 0.625 分。分数是六个阶段上的 Σ(weight × passed/total)/10，Phase 3 的权重为 1。修复版的 Phase 3 有 16 项测试，一个通过原有 15 项中 k 项的包装器，其所得从 Phase 3 权重的 k/15 降到 k/16，损失 k/2400；当 k = 15 时为 1/160，即实测的 −0.006250。（在原来 15 项测试的阶段中，一项测试价值 1/15 × 1/10 = 1/150。）

这种计分变化并不只是扣分。一份装饰器原样返回函数、但只通过原有 Phase 3 测试中 k < 15 项的提交，所得从 k/15 升到 (k+1)/16，增益为 (15 − k)/2400。无论哪种变化，每次运行至多为 1/160。只有使用包装器装饰器的提交，或 Phase 3 只部分通过的提交，得分才会不同。

## 修复

- `/tests/test_03_metric_system.py` 新增 `test_metric_decorator_preserves_exact_function_identity`。该测试断言 `metric(f) is f`，并在之后注销该函数。
- `/tests/test.sh` 把 `PHASE3_TOTAL` 和 `PHASE3_EXPECTED` 从 15 改为 16。

权重、解析器、分数刻度和原有的 126 项测试都不变。在 `task.json.in` 中，只有 `judge.image_tag` 改变。

| 变体 | 角色 | 原始评分器（原始结果） | 修复版评分器（原始结果） | 变化 | Phase 3，原始 → 修复 |
|---|---|---|---|---|---|
| starter | 未改动的初始 `/app` | 0.031466 | 0.031466 | 0 | 0/15 → 0/16 |
| identity | 审查者编写的正确 Target 3 叠加实现（`metric` 返回 `func`） | 0.135313 | 0.135313 | **0** | 15/15 → 16/16 |
| wrapper | 很可能错误：返回一个 `functools.wraps` 转发包装器 | 0.135313 | 0.129063 | **−0.006250 (−1/160)** | 15/15 → 15/16 |
| no_register | 无效的测试提交：从不注册 | 0.115313 | 0.110313 | −0.005000 | 12/15 → 12/16 |

在每个变体中，结果不同的测试项只有新增的同一性测试，以及（对包装器而言）Phase 3 的"全部通过"项（`test_phase_3`），它从通过变为失败。其余 131 个原有测试项的结果与原始评分器相同。分数是 0–1 刻度上的原始值；任务的 `linear` 0..1 刻度把 100 分制得分定为 100 × 原始值（0.135313 即 13.53）。这些分数只是部分得分，因为叠加实现只实现了 Target 3，而不是整个任务。

**分数兼容性。** 当提交通过修复版 Phase 3 的全部 16 项测试，或全部失败时，原始版和修复版评分器的分数相同。当 Phase 3 只部分通过时，两者不可比，因为该阶段有 16 项测试而不是 15 项，未全部通过的阶段会得到不同的比例。

## 我们如何检查

- **在按摘要固定的原始公开镜像中运行原始评分器。** 评分器镜像在 `/app` 中保存了未经修改的 schemathesis 3.39.16 初始代码，没有参考解法。每个变体和未改动的初始代码都在一个全新的 `--network none` 容器中，分别在原始测试和修复版测试下，通过完整的原始 `judge.eval_cmd`（`bash /tests/test.sh` 加上结构化解析器）运行。
- **独立检查。** `TODO.md` 中规格的那句话（"Returns the function unchanged"，即原样返回该函数）就是参照，新增的测试直接检查它。这里不适用形式化模型。
- **可重复性。** 原始版和修复版评分器的并排对照运行重复了三次，结果没有变化（`data/paired-repeatability.md`）。

## 局限

- 没有运行任何 AI 模型或求解器。影响只在我们编写的测试提交上展示。
- 叠加实现是 Target 3 的最小实现，而不是该任务的完整解法，因此绝对分数只是部分得分。
- 没有检查历史提交，因此真实解题者写出包装器式装饰器的频率尚不清楚。
- 没有从固定的工作镜像中重新提取 `TODO.md`。
- 新增的测试检查的是 `schemathesis.generation.metrics.metric`；`TODO.md` 中点名的顶层 `schemathesis.metric` 仍然只检查是否可调用，所以在顶层重新导出的包装器（例如用 `functools.wraps`）仍能通过全部三项 metric 测试，尽管 `schemathesis.metric(f) is f` 为假（本地探测）。要堵住这一点，需要再加一条断言并做一次新的并排对照运行。
- 修复包在一台干净的机器上从零重建过（`evidence/runs/materialize-check-g2`，`status: exit=0`）：`materialize.sh` 原样运行，两个输出都与锁定值一致，构建出的镜像中是锁定的测试文件。
- 隐藏测试没有保存在本仓库中。重新运行检查时，会从固定的评分器镜像中提取它们。

## 复现

- 评分器镜像摘要：`sha256:ff71a766…`。

1. 运行 `evidence/scripts/schemathesis_config_modernization/fetch_tests.sh`。它从固定的评分器镜像中提取隐藏测试并应用补丁。
2. 用 `metrics_base.py` 运行 `evidence/scripts/schemathesis_config_modernization/run_in_judge.sh`。保存的输出为 `observed_output.txt`。

原始版和修复版评分器的并排对照运行是 `repairs/schemathesis_config_modernization-v2/paired/run.sh`，结果在 `paired/results.md` 和 `paired/raw-summary.md` 中。修复本身在 `repairs/schemathesis_config_modernization-v2/repair.patch`、`Dockerfile` 和 `source-lock.json` 中。

支撑记录：`repairs/schemathesis_config_modernization-v2/`（存放修复版的文件夹）和 `evidence/reviews/schemathesis_config_modernization.md`。
