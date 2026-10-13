# Schemathesis data-generation pipeline (`schemathesis_datagen_pipeline`)

**结论：** 已修复。<mark>针对 HTTP 日期的隐藏测试只检查字符串的形状，因此生成不可能存在的日期和时刻的生成器也能通过；这一漏洞约占分数的 1%。</mark>

![原始日期测试接受一个毫无意义的日期字符串，也接受一个约 90% 日期不可能存在的生成器给出的全部 50 个日期；修复版测试只接受其中有效的 5 个。](figures/schemathesis_datagen_pipeline.svg)

*原始日期测试只检查字符串形状，因此一个约 90% 日期不可能存在的生成器在 50 个日期中 50 个都通过；修复版测试只接受其中有效的 5 个日期。*

## 任务要求

解题者为 schemathesis 4.14.3（一个测试 Web API 的工具）构建数据生成策略。任务要求解题者 "Treat `/app/TODO.md` as the authoritative task specification."（把该文件视为权威的任务规格。）`TODO.md` 的 Target 1 要求一个 "**HTTP-date strategy**: Generate valid HTTP-date values in IMF-fixdate format"（**HTTP 日期策略**：生成 IMF-fixdate 格式的有效 HTTP 日期值）。它还补充道："In positive generation mode, all generated values should conform to the protocol grammar."（在正向生成模式下，所有生成的值都应符合协议语法。）HTTP 日期的标准 RFC 9110 §5.6.7 把 `time-of-day` 标注为 `00:00:00 - 23:59:60 (leap second)`。它把日期各字段的含义交给 RFC 5322 §3.3，后者要求日期时间 "semantically valid"（语义上有效）：月中的日子真实存在、星期与之相符、时刻在范围之内。类别：系统与软件工程。

## 问题出在哪里

**规则。** 生成的 HTTP 日期必须是 IMF-fixdate 格式的有效日期。原始测试只用 `^\w{3}, \d{2} \w{3} \d{4} \d{2}:\d{2}:\d{2} GMT$` 检查每个字符串，别无其他。这个模式不检查：

- 日期是否在日历中存在（31 Apr 和 29 Feb 2023 都不存在）；
- 星期是否与日期相符；
- 时刻的范围，例如 24:00；
- 星期和月份的名称是否是真实的名称。`\w{3}` 接受任意三个单词字符，因此 `"Abc, 99 Xyz 0000 99:99:99 GMT"` 也能通过。

**例子。** 一个现实中可能写出的生成器独立地抽取星期、日、月、年和时刻（`independent_fields`）。约 90% 的抽样会产生不可能存在的日期和不相符的星期。在随机数固定的 50 次抽样中，原始模式接受了 50/50，修复版检查接受了 5/50。按任务规格的预期：日期测试应当失败。在原始评分器上的实际结果：Phase 1 让这个生成器以 15/15 通过。

**为什么重要。** 错误的生成器相对正确的生成器并无收益，但两者在 Phase 1 得到相同的分数，因此该测试无法区分它们。

## 影响有多大

至多约为总分的 1%。日期测试是 Phase 1 的 15 项测试中的 1 项，而 Phase 1 的权重为 2/13，因此影响为总分的 −2/195。只有 `http_date_values` 会生成无效日期或时刻的解题者受影响。

## 修复

修复版改动一个文件 `/tests/test_01_header_strategies.py`。只检查形状的模式被替换为检查 `is_imf_fixdate`。该检查覆盖 IMF-fixdate 语法、真实的公历日期、星期的一致性和时刻范围，并且只在 23:59 时允许 `:60`。它只要求年份可以表示（≥ 1），因为 `TODO.md` 没有规定最低年份。这项日期测试的 `max_examples` 从 50 提高到 200。用 50 个样例时，罕见的时刻缺陷（小时为 24）只在 15/20 个随机种子中被发现；用 200 个样例时，在 20/20 个种子中都被发现。测试数量、`test.sh`、权重和解析器都不变。在 `task.json.in` 中，只有 `judge.image_tag` 改变。

测试用生成器：`correct`（`st.datetimes(1970..2100)`）；`stdlib_1900` 和 `stdlib_any_year`（基于 `email.utils.format_datetime` 的诚实生成器）；`independent_fields` 和 `off_by_one_clock`（看似合理但错误；后者抽取 0–24 的小时和 0–60 的分钟）；`garbage_shape`（无效的测试提交，`"999, 99 888 0000 99:99:99 GMT"`）；`rfc850`（格式错误的测试提交）；以及未改动的初始文件。

| 生成器 | 原始评分器得分 | 修复版评分器得分 | 20 个种子中的失败次数，原始 / 修复 |
| --- | --- | --- | --- |
| correct | 0.477350 | 0.477350 | — |
| stdlib_1900 | 0.477350 | 0.477350 | 0/20 / 0/20 |
| **stdlib_any_year** | 0.477350 | **0.477350** | 0/20 / 0/20 |
| independent_fields | 0.477350 | 0.467094 | 0/20 / 20/20 |
| off_by_one_clock | 0.477350 | 0.467094 | 0/20 / 20/20 |
| garbage_shape | 0.477350 | 0.467094 | — |
| rfc850（无效） | 0.467094 | 0.467094 | — |
| 初始文件 | 0.323504 | 0.323504 | — |

在所有生成器中，`test_http_date_values_grammar` 是唯一结果改变的测试。对三个被拒绝的生成器，`test_phase_1` 汇总项也从通过变为失败。其余 97 项都不变。这些分数只是部分得分，因为其他目标保持初始状态。没有诚实的生成器失分。每个看似合理但错误的生成器，以及只有形状正确的垃圾输出，都失去 Phase 1 的 1/15。格式错误的测试提交在两个版本中都被拒绝。

**分数是否可比？** 只有当提交的 `http_date_values` 生成的无效日期或时刻被测试抽取的 200 个样例命中时，修复版才与原始版不同。这些提交失去 Phase 1 的 1/15（总分的 −2/195）。其他所有提交得分相同。

## 我们如何检查

- **原始评分器，来自按摘要固定的公开镜像。** 评分器镜像中保存了未经修改的 schemathesis 4.14.3 初始文件和 hypothesis 6.155.2（属性测试库），没有参考解法。每个生成器都在全新的 `--network none` 容器中，分别在完整的原始 `judge.eval_cmd` 和修复版下运行。这项日期测试还单独用 20 个 Hypothesis 种子运行过。
- **独立检查。** 一个纯 Python 检查在固定字符串上运行原始模式和修复版检查：31 Apr、24:00、错误的星期、29 Feb 2023、29 Feb 2024 和 `Sat, 31 Dec 2016 23:59:60`。日历有效性用 Python 的公历 `calendar` 检查。
- **可重复性。** 原始版和修复版评分器的并排对照运行做了三次，结果没有变化（`data/paired-repeatability.md`）。

## 局限

- 没有运行任何 AI 模型或求解器。影响只在我们编写的生成器上展示。
- 这些生成器是 Target 1 的最小叠加实现。没有可用的上游参考生成器，因此分数只是部分得分。
- 没有检查闰秒是否真的发生过。`:60` 只在 23:59 时允许，但没有对照真实的闰秒表检查。
- 属性测试仍然是随机的。所测的错误生成器在 20/20 个种子中都被发现，但更罕见的缺陷在某个给定种子下仍可能通过。
- 这类错误在真实提交中出现的频率未知。

## 复现

- 评分器镜像：`sha256:16b21364…`。
- 原始测试与修复版测试的对照：先运行 `evidence/scripts/schemathesis_datagen_pipeline/fetch_tests.sh`，它从固定的镜像中提取隐藏测试。
- 然后用同一文件夹中的 `headers_overlay.py`、`run_seed_sweep.sh` 和 `check_witnesses.py` 运行 `run_in_judge.sh`。保存的输出：`observed_output.txt`、`observed_seed_sweep.txt` 和 `observed_witnesses.txt`。
- 原始版和修复版评分器的并排对照运行：运行 `repairs/schemathesis_datagen_pipeline-v2/paired/run.sh` 和 `paired/extra.sh`（`repairs/schemathesis_datagen_pipeline-v2/` 是存放修复版的文件夹）。结果在 `paired/results.md` 中。上表来自最终一次运行 `evidence/runs/schemathesis_datagen_pipeline-v2-paired-b/result/out/summary.md`（种子扫描见 `result/out/extra.log`）；`paired/raw-summary.md` 和 `paired/seed-sweep.txt` 记录的是更早的一次运行，当时修复版检查设有年份 ≥ 1900 的下限；这两份记录已被取代。
- 修复：`repairs/schemathesis_datagen_pipeline-v2/repair.patch`、`Dockerfile`、`source-lock.json`。

支撑记录：`repairs/schemathesis_datagen_pipeline-v2/` 和 `evidence/reviews/schemathesis_datagen_pipeline.md`。
