# Schemathesis reporting and observability (`schemathesis_reporting_observability`)

**结论：** 已修复。<mark>针对 JUnit 报告写入器的隐藏测试会接受损坏的输出，而针对在某些生成场景中省略请求体的测试永远不会失败；这两个漏洞合计给出约占分数 2.4% 的错误得分。</mark>

![两个面板：原始的 JUnit 测试和原始的请求体抑制测试都让有缺陷的实现通过，而修复版测试让它们失败。](figures/schemathesis_reporting_observability.svg)

*两项隐藏测试为有缺陷的实现给了分，合计约占分数的 2.4%；修复版测试让这些有缺陷的版本失败。*

## 任务要求

Schemathesis 是一个自动测试 Web API 的工具。解题者扩展 schemathesis 4.13.0 中的报告和可观测性功能，并被要求 "Treat `/app/TODO.md` as the authoritative task specification."（把该文件视为权威的任务规格。）评分器用隐藏测试为工作评分。这里涉及两个目标：

- Target 2：一个 "**`JunitXmlWriter`**: A context-manager class that writes JUnit XML reports"（写出 JUnit XML 报告的上下文管理器类），带有一个 "records a test error"（记录测试错误）的 `record_error` 方法。JUnit XML 是 CI（持续集成）系统读取的一种常见测试报告格式。
- Target 5 的第 2 项修复："The `allow-extra-parameters = false` configuration suppresses unexpected-properties coverage scenarios for query, header, and cookie parameters, but not for request bodies. Bodies should be included in this suppression."（该配置会为 query、header 和 cookie 参数抑制"意外属性"覆盖场景，但不会为请求体抑制；请求体也应纳入这一抑制。）

类别：系统与软件工程。

## 问题出在哪里

### 1. JUnit 测试接受损坏或不完整的报告

**规则。** `record_error` 必须在 JUnit XML 报告中记录一个错误。原始测试只检查字符串 `"schemathesis"` 和 `"test_label"` 是否出现在输出中的某处。

**例子。** 四个测试用写入器：`correct`（基于初始文件的命令行工具已在使用的 `junit_xml` 库）、`drops_error`（格式良好的 XML，但没有 `<error>`）、`unterminated`（格式错误的 XML）和 `plaintext`（根本不是 XML）。预期：只有 `correct` 通过。在原始测试（"orig"）和修复版测试（"repaired"）下的实际结果：

```
correct      orig: 1 passed   repaired: 1 passed
drops_error  orig: 1 passed   repaired: 1 failed
unterminated orig: 1 passed   repaired: 1 failed
plaintext    orig: 1 passed   repaired: 1 failed
```

**为什么重要。** 一个丢掉 `<error>` 的写入器会让一次失败的操作在 CI 中看起来像是通过了，而它仍然拿到这项测试的分数。反方向上，一个正确的写入器如果把测试套件命名为 `schemathesis` 以外的名称，就会在原始测试中失败，因为此时字符串 `schemathesis` 在其输出中根本不出现（见下文在 E2B 上的修订运行）；而 `TODO.md` 并没有规定套件的名称。

### 2. 省略请求体的测试永远不会失败

**规则。** 在 `allow-extra-parameters = false` 下，请求体不得产生"意外属性"场景（带有额外的、未声明字段的生成测试输入）。

**例子。** 未改动的初始文件缺少请求体修复。在它上面，若要求抑制请求体，`cover_schema_iter` 会产生 12 个值，而且其中出现了不应有的 `OBJECT_UNEXPECTED_PROPERTIES` 场景。这 12 个值全部属于覆盖模块中的 `GeneratedValue` 类。测试却按另一个同名的类过滤，因此它得到的场景集合总是空的，其检查永远不会失败。预期：如测试自己的头部注释所说，该测试在初始文件上失败。实际：它在初始文件上通过。它在一个忽略该标志、总是省略请求体的实现上也通过。

**为什么重要。** 该测试为缺失或错误的行为给分。针对查询参数的对应测试同样永远不会失败，但它守护的只是初始文件已有的行为。

## 影响有多大

分数为五个阶段上的 Σ wᵢ·passedᵢ/totalᵢ / 10，权重为 2、2、3、2、1（`/tests/test.sh`）。Phase 2 中一项测试价值总分的 2/(14·10) = 1/70；Phase 5 中一项测试在原始版中价值 1/100，在修复版中价值 1/120。

- 原始版中的错误得分：JUnit 测试至多给出 1/70（100 分制下约 1.4 分），请求体测试至多给出 1/100（1.0 分）。
- 原始版中的错误扣分：对于输出不含字符串 `schemathesis` 的正确写入器，JUnit 测试扣去 1/70（约 1.4 分）。
- 修复版下的最大降幅：4.76 分。一份在原始版下全部通过、但在修复版 JUnit 测试和全部四项新覆盖测试中失败的提交，在 Phase 2 失去 1/70，在 Phase 5 失去 10·(1 − 8/12)/100 = 1/30，合计 1/70 + 1/30 = 4.76 分。所测的改动版本分别失去 1.43、0.83 和 1.67 分。
- 修复版下的最大升幅：2.76 分。修订后的 JUnit 测试可能在原始测试失败的地方通过：一个输出中从不含字符串 `schemathesis` 的正确写入器（例如套件用了别的名称），在原始测试中失败、在修订后的测试中通过，即 1/70 或 1.43 分。在 Phase 5 中，只要覆盖生成器能运行，两项原有的覆盖测试在任何提交上都会通过，因此在没有通过其他 Phase 5 测试的情况下，所占份额从 2/10 变为至多 4/12，即 1.33 分；合计 2.76 分。初始文件和桩实现增加 0.5 分。只有当一份提交从 `schemathesis.specs.openapi.negative` 中删除了 `GeneratedValue` 类（原有覆盖测试导入了这个类）时，升幅才可能达到 4.76 分。
- 所测的错误实现中，没有一个得分高于正确实现；所测的唯一一个正确实现保持 1.0。

## 修复

修复版改动三个评分器文件：

- `/tests/test_02_reporting.py` 会解析 XML。它接受 `testsuite` 或 `testsuites` 作为根元素，并要求有一个名为 `test_label`（即传给 `record_error` 的标签）的测试用例，其中包含一个以文本或属性形式携带消息的 `<error>`。这些正是 `TODO.md` 所述的要点：一份 JUnit XML 报告，以及 `record_error` "records a test error"（记录测试错误）。测试名称和测试数量都不变。
- `/tests/test_05_email_coverage.py` 使用正确的 `GeneratedValue` 类，并要求得到正确类型的非空值流。它还为请求体和查询参数分别添加了允许额外参数和拒绝额外参数的用例。
- `/tests/test.sh` 把 Phase 5 的测试数从 10 提高到 12。权重不变。

在 `task.json.in` 中，只有 `judge.image_tag` 改变。

下表中，`fullref` 是一个完整的参考实现，用作正确的测试提交。`fullref_*` 各行分别改动它的一行，`stub_*` 各行使用一个最小的桩实现。分数为 0–1 刻度上的原始结果（换算为 0–100 分之前）。

| 测试提交 | 角色 | 原始评分器 | 修复版评分器 | 变化 | 通过的测试，P2 = Phase 2，P5 = Phase 5（原始 → 修复） |
|---|---|---|---|---|---|
| fullref | 正确的完整实现 | 1.000000 | 1.000000 | **0** | P2 14/14 → 14/14；P5 10/10 → 12/12 |
| fullref_junit_drops_error | 看似合理的错误：`record_error` 创建了测试用例但丢掉 `<error>` | 1.000000 | 0.985714 | **−0.014286 (−1/70)** | P2 14/14 → 13/14 |
| fullref_no_body_fix | 看似合理的错误：省略了 Target 5 的第 2 项修复（BODY 未被抑制） | 1.000000 | 0.991667 | **−0.008333** | P5 10/10 → 11/12 |
| fullref_always_suppress | 看似合理的错误：抑制时忽略 `allow_extra_parameters` | 1.000000 | 0.983333 | **−0.016667** | P5 10/10 → 10/12 |
| stub_junit_correct | 审查者编写的桩，基于 `junit_xml` 的写入器 | 0.091429 | 0.096429 | +0.005000 | P2 5/14 → 5/14；P5 2/10 → 3/12 |
| stub_junit_drops_error | 审查者编写的桩，丢掉错误 | 0.091429 | 0.082143 | −0.009286 | P2 5/14 → 4/14；P5 2/10 → 3/12 |
| starter | 未改动的初始文件 | 0.020000 | 0.025000 | +0.005000 | P2 0/14 → 0/14；P5 2/10 → 3/12 |

对每份测试提交，Phase 1、3 和 4 的结果都相同。只有以下各项改变：

- JUnit 测试；
- 原先两项只测拒绝情形的覆盖测试，它们被替换为四项允许/拒绝测试；
- 那些现在在 Phase 2 和 Phase 5 中失败的改动版本的阶段汇总项（`test_phase_2`、`test_phase_5`）。

三个看似合理的错误版本在原始评分器下都得 1.0，但在修复版评分器下失分。正确的测试提交保持 1.0。

**修复的修订（2026-10-12）。** 第一次发布的修复版还要求套件名称恰为 `schemathesis`、恰好一个测试用例和一个 `<error>`，并且没有 `<failure>` 或 `<skipped>` 元素。`TODO.md` 对这些都没有规定；`schemathesis` 只是初始文件的命令行 JUnit 处理程序所用的套件名称。修订后的测试去掉了这些要求。原始评分器、第一版修复和修订版修复的并排对照运行在全新的工作节点上做了三次，对之前的每份提交都得到与上表相同的结果。另外新增了三份提交：

| 测试提交 | 角色 | 原始评分器 | 第一版修复 | 修订版修复 |
|---|---|---|---|---|
| fullref_junit_other_suite | 正确：套件名为 `api-report` | 0.985714 | 0.985714 | 1.000000 |
| stub_junit_other_suite | 正确的桩写入器，套件名为 `api-report` | 0.077143 | 0.082143 | 0.096429 |
| stub_junit_unterminated | 错误：格式错误的 XML | 0.091429 | 0.082143 | 0.082143 |

原始测试也会让套件名称不同的正确写入器失败，因为其输出中不含字符串 `schemathesis`；第一版修复也是如此。修订版让它通过。丢掉 `<error>` 或写出格式错误 XML 的写入器，在两个修复版本下都失败。

**分数兼容性。** 完全正确的提交在两个版本中都得 1.0。当 Phase 2 或 Phase 5 只部分通过时，原始分数与修复版分数不可比，因为 Phase 5 有 12 项测试而不是 10 项。在修复版下，未改动的初始文件和桩提交增加 +0.005。新增的允许用例和查询参数的拒绝用例检查的是初始文件的生成器已有的行为。因此，初始文件在 Phase 5 的得分，从那项永远不会失败的请求体测试，转移到了真实有效的检查上。一个更小的替代方案是只改动 `GeneratedValue` 的导入、保留 10 项测试，但它无法发现一个总是省略请求体的实现。

## 我们如何检查

- **在按摘要固定的原始镜像中运行原始评分器。** 评分器镜像中保存了未经修改的 schemathesis 4.13.0 初始文件。每份测试提交都在全新的 `--network none` 容器中，分别通过完整的原始 `judge.eval_cmd` 和修复版评分器运行。
- **直接检查。** 检查了 `cover_schema_iter` 在初始文件上产生的每个值的类，这说明了原始覆盖过滤为何总是为空。修复版覆盖测试在初始文件、一个正确的修复和一个总是省略请求体的修复上运行。
- **可重复性。** 原始版和修复版评分器的并排对照运行做了三次，结论没有变化（`data/paired-repeatability.md`）。这些重复使用的是第一版修复。使用修订版修复的运行也做了三次（`evidence/runs/schemathesis_reporting_observability-v2-paired-rev2`、`-rev2-rep2`、`-rev2-rep3`），分数和每项测试的结果都相同。

## 局限

- 没有运行任何 AI 模型或求解器。影响只在我们编写的测试提交和改动版本上展示。
- 作为正确的测试提交，只有一个完整实现可用，而且尝试过的每个正确 JUnit 写入器都基于 `junit_xml`。修订后的 JUnit 测试仍然假定通常的 JUnit 形式：错误是 `<testcase>` 中的一个 `<error>` 元素，且该测试用例的 `name` 就是标签。一个把错误记录为 `<failure>`、或只把标签放在 `classname` 中的写入器会失败，根元素带有 XML 命名空间（`<testsuites xmlns=…>`）的报告也会失败（本地探测；XML 声明、字节顺序标记、CDATA 或嵌套的 `testsuites` 都能通过）；`TODO.md` 对这些细节都没有明确说明。
- Phase 4 的测试计数有一处反常（预期 9 项，收集到 11 项）未作改动，不在范围之内。
- 修复包在一台干净的机器上从零重建过（`evidence/runs/materialize-check-g2`，`status: exit=0`）：全部 3 个输出与锁定值一致，构建出的镜像中是锁定的测试文件。
- 更广泛的集成行为（xdist、有状态运行、一处 55/53 的测试计数反常）没有检查。
- `TODO.md` 取自工作目录树的云端导出（sha256 `097166d3…`），而不是从工作镜像中重新提取。
- 隐藏测试没有保存在本仓库中。重新运行检查时，会从固定的评分器镜像中提取它们。

## 复现

- 原始评分器镜像：`sha256:b1e16633…`。
- **原始测试与修复版测试的对照。** 先运行 `evidence/scripts/schemathesis_reporting_observability/fetch_tests.sh`。然后运行 `run_junit_in_judge.sh`（配合 `reporting_overlay/`）、`run_coverage_in_judge.sh` 和 `run_coverage_variants.sh`。保存的输出在 `observed_junit.txt`、`observed_coverage.txt` 和 `observed_coverage_variants.txt` 中。
- **原始版和修复版评分器的并排对照运行。** `repairs/schemathesis_reporting_observability-v2/paired/run.sh`。结果在 `paired/results.md` 和 `paired/raw-summary.md` 中。
- **修复。** `repairs/schemathesis_reporting_observability-v2/repair.patch`、`Dockerfile` 和 `source-lock.json`。

支撑记录：`repairs/schemathesis_reporting_observability-v2/`（存放修复版的文件夹）和 `evidence/reviews/schemathesis_reporting_observability.md`。
