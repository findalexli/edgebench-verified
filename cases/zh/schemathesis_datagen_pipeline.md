# Schemathesis data-generation pipeline (`schemathesis_datagen_pipeline`)


**2026-10-13 修订：** v2.1 恢复了 RFC 规定的年份下限（年份 ≥ 1900）。我们做了一次干净的原生运行（`schemathesis_datagen_pipeline-v2.1-native-20261013b`，台账记录 `exit=0`）：从修复包构建 v2.1 镜像，在六个对照臂上运行原始评测命令。有效的生成器奖励仍是 0.477350，生成 1900 年以前日期的生成器和垃圾生成器降到 0.467094。这几组有限的对照证明不了整个任务没有问题。见[后续说明](../repairs/schemathesis_datagen_pipeline-v2/paired/followup.md)。

**结论：** 原始缺陷已确认；v2.1 修复已在并排的原生对照中验证。<mark>HTTP 日期的隐藏测试只看字符串的形状，生成器即使给出根本不存在的日期和时刻也能通过；这个漏洞约占分数的 1%。</mark>

![原始日期测试接受一个毫无意义的日期字符串，也接受一个约 90% 日期不可能存在的生成器给出的全部 50 个日期；修复版测试只接受其中有效的 5 个。](../figures/schemathesis_datagen_pipeline.svg)

*原始日期测试只检查字符串形状，因此一个约 90% 日期不可能存在的生成器在 50 个日期中 50 个都通过；修复版测试只接受其中有效的 5 个日期。*

## 任务要求

解题者要为 schemathesis 4.14.3（一个测试 Web API 的工具）编写数据生成策略。任务要求解题者 "Treat `/app/TODO.md` as the authoritative task specification."（把该文件视为权威的任务规格。）`TODO.md` 的 Target 1 要求一个 "**HTTP-date strategy**: Generate valid HTTP-date values in IMF-fixdate format"（**HTTP 日期策略**：生成 IMF-fixdate 格式的有效 HTTP 日期值）。它还补充道："In positive generation mode, all generated values should conform to the protocol grammar."（在正向生成模式下，所有生成的值都应符合协议语法。）HTTP 日期的标准 RFC 9110 §5.6.7 把 `time-of-day` 标注为 `00:00:00 - 23:59:60 (leap second)`。日期各字段的含义，它引用 RFC 5322 §3.3 的规定，后者要求日期时间 "semantically valid"（语义上有效）：这一天在该月确实存在，星期与日期相符，时刻不越界。类别：系统与软件工程。

## 问题出在哪里

**规则。** 生成的 HTTP 日期必须是 IMF-fixdate 格式的有效日期。原始测试只拿 `^\w{3}, \d{2} \w{3} \d{4} \d{2}:\d{2}:\d{2} GMT$` 匹配每个字符串，此外什么也不查。这个模式不管：

- 日历上有没有这一天（31 Apr 和 29 Feb 2023 都不存在）；
- 星期与日期是否相符；
- 时刻是否越界，例如 24:00；
- 星期和月份是不是真实的名称。`\w{3}` 接受任意三个单词字符，所以 `"Abc, 99 Xyz 0000 99:99:99 GMT"` 也能通过。

**例子。** 一个现实里很可能有人这样写的生成器，把星期、日、月、年和时刻分开独立抽取（`independent_fields`）。约 90% 的抽样会得到不存在的日期，星期也对不上。固定随机数抽 50 次，原始模式全部接受（50/50），修复版检查只接受 5/50。按任务规格，日期测试应当失败；而原始评分器上的实际结果是 Phase 1 让这个生成器 15/15 全过。

**为什么重要。** 错误的生成器比正确的生成器得不到额外好处，但两者在 Phase 1 分数相同，这项测试分不出它们。

## 影响有多大

最多约为总分的 1%。日期测试是 Phase 1 的 15 项测试中的 1 项，Phase 1 的权重为 2/13，所以影响是总分的 −2/195。只有 `http_date_values` 会生成无效日期或时刻的解题者才受影响。

## 修复

修复版只改了一个文件 `/tests/test_01_header_strategies.py`：把只查形状的模式换成 `is_imf_fixdate` 检查。新检查覆盖 IMF-fixdate 语法、真实的公历日期、星期是否一致、时刻范围，并且只在 23:59 时允许 `:60`。它要求年份不早于 1900：`TODO.md` 要求有效的 HTTP 日期值，而 RFC 9110 §5.6.7 的日期语义取自 RFC 5322 §3.3（"any numeric year 1900 or later"，即任何 1900 年或以后的数字年份）。较早的 v2 去掉了这条下限（年份 ≥ 1），v2.1 又把它加了回来。这项日期测试的 `max_examples` 从 50 提高到 200：用 50 个样例时，罕见的时刻缺陷（小时为 24）只有 15/20 个随机种子能查出来；用 200 个样例，20/20 都能查出。测试数量、`test.sh`、权重和解析器都不变。`task.json.in` 只改了 `judge.image_tag`。

当前 v2.1 的结果（原生运行，原始 `judge.eval_cmd`，`--cpus 2 --memory 4g --network none`）：

| 生成器 | 角色 | 原始评分器得分 | 修复版评分器得分（v2.1） |
| --- | --- | --- | --- |
| stdlib_1900 | 有效 | 0.477350 | 0.477350 |
| stdlib_any_year（1900 年以前的年份） | 无效 | 0.477350 | **0.467094** |
| garbage_shape | 无效 | 0.477350 | **0.467094** |

下面较长的表格来自**历史 v2** 运行（判定条件为年份 ≥ 1）。表里用到的测试生成器有：`correct`（`st.datetimes(1970..2100)`）；`stdlib_1900` 和 `stdlib_any_year`（基于 `email.utils.format_datetime` 的生成器；后者还会生成 1900 年以前的年份，v2.1 拒绝这些年份）；`independent_fields` 和 `off_by_one_clock`（看似合理但错误；后者抽取 0–24 的小时和 0–60 的分钟）；`garbage_shape`（无效的测试提交，`"999, 99 888 0000 99:99:99 GMT"`）；`rfc850`（格式错误的测试提交）；以及未改动的初始文件。

| 生成器 | 原始评分器得分 | 历史 v2 得分 | 20 个种子中的失败次数，原始 / v2 |
| --- | --- | --- | --- |
| correct | 0.477350 | 0.477350 | — |
| stdlib_1900 | 0.477350 | 0.477350 | 0/20 / 0/20 |
| **stdlib_any_year** | 0.477350 | **0.477350** | 0/20 / 0/20 |
| independent_fields | 0.477350 | 0.467094 | 0/20 / 20/20 |
| off_by_one_clock | 0.477350 | 0.467094 | 0/20 / 20/20 |
| garbage_shape | 0.477350 | 0.467094 | — |
| rfc850（无效） | 0.467094 | 0.467094 | — |
| 初始文件 | 0.323504 | 0.323504 | — |

所有生成器里，只有 `test_http_date_values_grammar` 这一项测试的结果变了。三个被拒的生成器，`test_phase_1` 汇总项也由通过变为失败。其余 97 项都不变。其他目标都保持初始状态，所以这些只是部分得分。历史 v2 下，年份在范围内的生成器都没有丢分；v2.1 下，`stdlib_any_year` 会生成 1900 年以前的年份，也丢掉 Phase 1 的 1/15。看似合理但错误的生成器，以及只有形状对的垃圾输出，都丢掉 Phase 1 的 1/15。格式错误的测试提交在两个版本里都被拒绝。

**分数是否可比？** 提交的 `http_date_values` 会生成无效日期、1900 年以前的年份或无效时刻，而且测试抽的 200 个样例碰上了，修复版（v2.1）的分数才和原始版不同。这样的提交丢掉 Phase 1 的 1/15（总分的 −2/195）。其余提交得分相同。

## 我们如何检查

- **原始评分器，来自按摘要固定的公开镜像。** 评分器镜像里是未改动的 schemathesis 4.14.3 初始文件和 hypothesis 6.155.2（属性测试库），没有参考解法。每个生成器都在全新的 `--network none` 容器里，分别用完整的原始 `judge.eval_cmd` 和修复版运行。这项日期测试还另外用 20 个 Hypothesis 种子跑过。
- **独立检查。** 一个纯 Python 脚本拿一组固定字符串，分别过一遍原始模式和修复版检查：31 Apr、24:00、错误的星期、29 Feb 2023、29 Feb 2024 和 `Sat, 31 Dec 2016 23:59:60`。日历有效性用 Python 的公历 `calendar` 判断。
- **可重复性。** 原始版和修复版评分器的并排对照运行做了三次，结果不变（`data/paired-repeatability.md`）。

## 局限

- 没有运行任何 AI 模型或求解器。影响只在我们写的生成器上演示过。
- 这些生成器是 Target 1 的最小叠加实现。手头没有上游的参考生成器，所以分数只是部分得分。
- 没有核实闰秒是否真的发生过。`:60` 只在 23:59 时允许，但没有对照真实的闰秒表。
- 属性测试仍有随机性。测过的错误生成器在 20/20 个种子下都被查出，但更罕见的缺陷在某个种子下仍可能漏过。
- 真实提交里这类错误有多常见，目前不知道。

## 复现

- 评分器镜像：`sha256:16b21364…`。
- 原始测试与修复版测试的对照：先运行 `evidence/scripts/schemathesis_datagen_pipeline/fetch_tests.sh`，它从固定的镜像中提取隐藏测试。
- 然后用同一文件夹中的 `headers_overlay.py`、`run_seed_sweep.sh` 和 `check_witnesses.py` 运行 `run_in_judge.sh`。保存的输出：`observed_output.txt`、`observed_seed_sweep.txt` 和 `observed_witnesses.txt`。
- 原始版和修复版评分器的并排对照运行：运行 `repairs/schemathesis_datagen_pipeline-v2/paired/run.sh` 和 `paired/extra.sh`（`repairs/schemathesis_datagen_pipeline-v2/` 是存放修复版的文件夹）。结果在 `paired/results.md` 中。上表取自最后一次运行 `evidence/runs/schemathesis_datagen_pipeline-v2-paired-b/result/out/summary.md`（种子扫描见 `result/out/extra.log`）。`paired/raw-summary.md` 和 `paired/seed-sweep.txt` 记的是更早的一次运行，当时修复版检查带有年份 ≥ 1900 的下限；这两份记录已被取代。
- v2.1 原生运行（当前修复）：`evidence/runs/schemathesis_datagen_pipeline-v2.1-native-20261013b/run.sh`，结果见 `result/out/summary.txt` 以及 `paired/results.md` 的开头。
- 修复：`repairs/schemathesis_datagen_pipeline-v2/repair.patch`、`Dockerfile`、`source-lock.json`。

支撑记录：`repairs/schemathesis_datagen_pipeline-v2/` 和 `evidence/reviews/schemathesis_datagen_pipeline.md`。
