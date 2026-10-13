# Rust Multicrate Reconstruction (`rust_multicrate_reconstruction`)

**结论：** 已修复。<mark>原始评分器把隐藏测试插入到无法编译的位置，因此对每个按任务要求不改动测试的解题者，有两个 crate 整体得 0 分：cas-search（12 分）和 cas-cli（10 分）。此外，Cargo 会在第一个失败的测试文件处停止，而评分器把没有运行的测试算作失败。在发布方的评分环境中，一份完整的解法得 73.99 分（满分 100）；在修复版下得 94.70 分。另外，已发布的镜像缺少四个随附依赖（vendored）文件，因此直接使用随附镜像时，同一解法只得 27.61 分；这不影响发布方自己的评分。</mark>

## 任务要求

任务写道："Complete the missing Rust implementations in the unpacked CAS workspace."（在解压后的 CAS 工作区中补全缺失的 Rust 实现。）并补充说 "the hidden evaluator runs additional tests for the same public crate and CLI contracts"（隐藏评测器会针对同样的公开 crate 和 CLI 约定运行额外的测试）。crate 是 Rust 的包；工作区中共有 14 个。

分数是 10 个层级的加权和，每个层级按其测试贡献 `weight × passed / total`（`score.py` 第 29-38 行和第 390 行）。cas-search 单独构成层级 L5（权重 12，136 项测试），cas-cli 单独构成层级 L9（权重 10，1344 项测试）。cas-pty 和 cas-recording 两个 crate 构成层级 L3（权重 4，40 项测试）。任务禁止修改测试（"Do not edit … tests"，`TASK.md`；"Do not delete, weaken, or bypass tests"，`SPEC.md`；即不得修改、删除、削弱或绕过测试）。类别：系统与软件工程。

## 问题出在哪里

共有四个缺陷。前三个会改变发布方自己评分环境中的分数，因而也改变已发布的排行榜。第四个只影响使用已发布镜像评分的人。

**1. 无法编译的隐藏测试（cas-cli 和 cas-search）。** 评分器把每段隐藏测试代码追加到测试文件末尾；如果是源文件，则追加到其最后一个 `#[cfg(test)]` 模块的末尾（`score.py` 中的 `inject_hidden_tests`）。在两个 crate 中，这个位置是错的：

- **cas-cli。** 在 `cas-cli/tests/proptest/search_properties.rs` 中，四项隐藏测试是用 `proptest!` 语法写的（`fn search_never_crashes(query in search_query_strategy())`）。初始文件保留了该文件的 `proptest! { … }` 块但不含这些测试，评分器把它们追加在这个块之后，而那里这种语法并不合法。该文件无法编译（`expected one of ':', '@', or '|', found keyword 'in'`；`functions used as tests can not have any arguments`），cas-cli 在 1344 项中得 0。
- **cas-search。** 有三项隐藏测试是 `#[tokio::test]` 异步测试，在上游代码中位于 `#[cfg(feature = "parallel")]` 模块内：`src/hybrid.rs` 和 `tests/hybrid_integration.rs` 中的 `test_async_hybrid_search`，以及 `src/bm25_tests/tests.rs` 中的 `test_async_remove`。评分器把它们放在这些模块之外。在那里，它们需要可选依赖 `tokio`，以及只有启用该 feature 时才存在的 `search_async` 和 `AsyncBm25Index`。cas-search 无法编译，在 136 项中得 0。

编译器信息见 `evidence/runs/rust_multicrate_reconstruction-v2-paired-r2-starter/result/out/origcc/diag.txt`。只有当每个隐藏函数名都已出现在文件中时，评分器才会跳过该文件。对 cas-cli，唯一的出路是写出隐藏测试的确切名称，而解题者不可能知道这些名称。对 cas-search，解题者还可以把该 crate 的 `parallel` feature 设为默认开启（`crates/cas-search/Cargo.toml` 声明了 `parallel = ["tokio"]`，且 `default = []`），这不需要修改任何测试；这条路没有尝试过，任务中也没有任何内容指向它。因此，一个不改动测试和 crate feature 的善意解题者，在 L5 和 L9 上得 0 分。

**2. Cargo 在第一个失败的测试文件处停止。** `run_crate_test` 运行 `cargo test --frozen -p <crate> -- --test-threads=4`，不带 `--no-fail-fast`（`score.py:266-268`）。一个 crate 的某个测试二进制失败后，Cargo 不再运行其后的任何二进制（集成测试文件、文档测试），而评分器把没有运行的测试加到失败数中（`:329-331`）。损失取决于失败出现在哪里，而不是有多少测试通过。例如，cas-pty 库测试中预期的已知失败，会使 cas-pty 唯一的文档测试无法运行，因此一份完整的解法得 11 项中的 10 项，而不是 11 项中的 11 项。

**3. 豁免测试的计分（早先的发现）。** 评分器对每个 crate 豁免一项已知会失败的测试。当一个 crate 至少有一项失败时，只要被豁免测试的名称出现在测试输出中的任何位置，评分器就把一项失败转为通过；它并不检查那项测试是否真的失败了。因此，当被豁免的 cas-pty 测试通过、而另一项 cas-pty 测试（例如 `test_pty_config_default`）失败时，原始评分器报告 PASS，通过 11、失败 0，而不是 TEST_FAIL，通过 10、失败 1。一份诚实但只完成了一部分的解法就可能触发这一点：被豁免的测试只检查参数是如何构造的。

**4. 缺失的随附依赖文件（仅限已发布的镜像）。** 评分器解压的归档 `cas_rust_benchmark.tar.gz`（44,858 个条目）中，没有任何位于名为 `target` 的目录下的路径。因此随附依赖中的 `cc` 1.2.55 crate 缺少 `src/target/{apple,generated,llvm,parser}.rs`，而它的 `.cargo-checksum.json` 列出了这些文件；在 741 个随附依赖 crate 中，`cc` 是唯一缺少文件的。Cargo 拒绝这个 crate，于是用 `cc` 构建的 9 个 crate 得到 `TEST_CRASH`：cas-code、cas-recording、cas-store、cas-search、cas-core、cas-mux、cas-factory、cas-mcp 和 cas-cli。`eval_cmd` 会替换提交中的 `vendor-deps/`，因此解题者无法补上这些文件，而工作镜像中同样缺少它们（`cargo build --frozen -p zstd-sys` 失败，报 `failed to open file …/cc/src/target/apple.rs`）。

这不影响发布方的评分。只恢复这四个文件后，原始评分器给未改动的初始项目打出 3.8189 分，与发布方记录的结果（归档中的 `judge/skeleton-score.json`）在总分、公开分（3.3913）、通过测试数（66）以及每个 crate 的状态和计数上都完全一致。而使用随附归档时得分为 1.4711。所以发布方是用完整的 vendor 目录评分的；归档很可能是之后打包的，打包时排除了 `target` 目录，从而也删掉了 `cc/src/target/`（推断）。已发布的分数与此相符：它们最高达到 57.8（`tasks/README.md:131`），高于使用随附镜像时完整解法所能得到的 27.61。

**解题者自己添加的测试会被计分（不算作一项发现）。** 评分器按原样复制解题者的工作区，追加隐藏测试，并统计 `cargo test` 输出中每个 `N passed;` 和 `N failed;`（`score.py:286-291`）。crate 的总数为 `max(listed tests, EXPECTED_TOTALS)`（`:263-264`、`:329`）。因此，解题者自己编写的单元测试或文档测试会同时计入通过数和总数，尽管任务 README 称分母是固定的（"The current fixed scoring denominator is `RAW_TOTAL=2611`"；`RAW_TOTAL` 确实固定，但各层级分数使用的是每个 crate 的总数）。这一点在原始评分器和修复版中相同，其对真实提交的影响没有测量。另一个性质在两者中也相同：多出的一项通过测试可能掩盖一项缺失的预期测试，但这只会在删除或重命名公开测试时发生，而任务禁止这样做。

## 影响有多大

**对已发布的排行榜。** 发布方评分时这四个随附依赖文件是存在的（上文缺陷 4），因此真正要比较的是“原始评分器加上这些文件”与修复版。在相同的提交字节上、用任务的 `eval_cmd` 测得（`repairs/rust_multicrate_reconstruction-v2/paired/results.md`）：

| 提交 | 原始评分器 + cc 文件 | 修复版 | 变化 |
|---|---|---|---|
| 未改动的初始项目 | 3.8189 | 5.7236 | +1.9047 |
| 完整解法（上游代码） | 73.9926 | 94.7022 | +20.7096 |
| 同上，但有一个 cas-search 模块未完成 | 73.9926 | 93.9963 | +20.0037 |
| 错误对照：默认终端尺寸错误 | 73.8926 | 94.6022 | +20.7096 |

- 对完整解法，增益为 cas-search 12 × 128/136 = 11.2941，加上 cas-cli 10 × 1252/1344 = 9.3155，再加上 Cargo 不再跳过的 cas-pty 文档测试 4 × 1/40 = 0.1000：合计 20.7096（`paired/results.md`，参考一节）。
- **单独的 fail-fast 影响**，通过用去掉 `--no-fail-fast` 的修复版对相同提交评分来测量：完整解法损失 0.4348（94.7022 对 94.2674：cas-pty 的文档测试，以及属性测试二进制因其桩策略失败后才会运行的 45 项 cas-cli 测试），部分解法损失 3.2583（93.9963 对 90.7380：另外还有其库测试失败后的 32 项 cas-search 测试），初始项目损失 0.9884（5.7236 对 4.7352）。
- **任何提交的最大可能增益：29.22 分。** 在原始评分器中，对每次不改动测试的运行，cas-search 和 cas-cli 都得 0 分，因此修复版至多能增加它们的全部权重，即 12 + 10 = 22。在其他每个 crate 中，fail-fast 只会让位于该 crate 第一个测试二进制（总会运行的库测试）之外、且能够通过的测试失分。这些测试的数量来自一次执行了所有二进制的运行（`evidence/runs/rust_multicrate_reconstruction-failfast-paired-r3/result/out/raw/v2-*`），cas-mux 除外；被忽略的测试不计入，因为它们从不通过：
  - cas-factory-protocol：45 项集成测试和 5 项文档测试，10 × 50/196 = 2.5510（层级 L2，196 项测试）；
  - cas-factory：38 项集成测试，8 × 38/171 = 1.7778（L7，171 项测试）；
  - cas-store：21 项集成测试，15 × 21/216 = 1.4583（L4）；
  - cas-tui-test：10 项集成测试和 3 项文档测试，5 × 13/121 = 0.5372（L8，121 项测试）；
  - cas-pty：1 项文档测试，4 × 1/40 = 0.1000（L3）；
  - cas-mux：`--list` 列出的 17 项集成测试（`raw/v2-cas-mux-19.stdout`；一项都没有运行，因为该 crate 在终端桩中崩溃，见 `raw/v2-cas-mux-20.stderr`），8 × 17/171 = 0.7953（L7）。

  其余 crate 没有其他含可通过测试的二进制。合计为 22 + 7.2196 = 29.2196。在所测的每份完整解法中，cas-mux 都在终端桩中崩溃，这是评分器预期的，在两个版本中都得 0 分；去掉它的份额，最大值为 28.4243。这些计数针对随附的测试，不包括解题者自己添加的测试。
- 反方向上，豁免修复每次评分至多使分数降低 4/40 = 0.1000：即一项被错误宽恕的 cas-pty 失败。cas-cli 的豁免不变；它至多能增加 10/1344 = 0.0074。
- 增益随一次运行在 cas-search 和 cas-cli 上的进展而增大，因此可能改变排名。

**直接使用随附的已发布镜像时**，完整解法得 27.6091 分，初始项目得 1.4711 分，因为有 9 个 crate 无法构建。这只对使用这些镜像评分的人有影响；修复版也恢复了这些文件。

## 修复

所有改动都在评分器镜像的 `cas_rust_benchmark.tar.gz` 中，由修复包的 `Dockerfile` 重写；`eval_cmd` 不变。修复包：`repairs/rust_multicrate_reconstruction-v2/`。

- **`judge/tools/score.py`**：测试运行改用 `cargo test --frozen --no-fail-fast -p <crate> -- --test-threads=4`，使每个测试二进制都会运行。对 cas-pty，只有当被豁免的测试确实在失败测试之中时，才计入豁免（即本页前文所述的单条件修复）；cas-cli 的规则不变。测试发现（`--list`）不变。
- **cas-cli 的隐藏测试**：四项隐藏属性测试被包进它们自己的 `proptest! { #![proptest_config(ProptestConfig::with_cases(20))] … }` 块中，使用与初始文件中的块相同的配置。
- **cas-search 的隐藏测试**：三项异步测试各自加上 `#[cfg(feature = "parallel")]`，即它们在上游模块中所带的条件。在评分器使用的默认 feature 下，它们不会被编译，与上游一致。
- **随附依赖文件**：四个 `vendor-deps/cc/src/target/*.rs` 文件，与 crates.io 上的 `cc-1.2.55.crate` 完全相同，其 sha256 等于随附 `.cargo-checksum.json` 中的包 sha256。`Dockerfile.work` 也把它们加入工作镜像，使解题者能离线构建每个 crate。
- **`task.json.in`**：只改动两个镜像标签，改为 `…-ebv-v2`。

**分数与原始排行榜不可比**：在发布方的环境中，完整解法从 73.99 变为 94.70。在两个版本中，完整解法都仍然无法达到 100：被忽略的测试算作失败，而 cas-mux 按评分器的预期在终端桩中崩溃。

## 我们如何检查

- **并排对照运行。** 每份提交都用任务的 `eval_cmd` 原样评分，使用相同的提交字节，每份提交一个 E2B 工作节点（`--network none`，cargo/rustc 1.88.0），在三个镜像中运行：按摘要固定的原始评分器镜像；只添加了四个随附依赖文件的同一镜像（发布方的环境）；以及在工作节点上由 `materialize.sh` 和 `Dockerfile` 构建的修复版。提交如下：
  - 初始项目；
  - 参考解法：把初始项目中 507 个含 `todo!()` 的文件替换为上游 CAS v1.0.0（`github.com/codingagentsystem/cas`，版本 `a0a4b5ad`）。在其中带有隐藏测试的 182 个文件里，再把隐藏测试函数删掉，使评分器像对任何解题者一样注入它们；
  - 部分解法：参考解法，但 `cas-search/src/metrics.rs` 保持初始文件的样子；
  - 错误对照：参考解法，但 `PtyConfig::default()` 返回 25 行（`test_pty_config_default` 期望 24）。

  | 提交 | 原始评分器 | 原始评分器 + cc 文件 | 修复版 |
  |---|---|---|---|
  | 初始项目 | 1.4711 | 3.8189 | 5.7236 |
  | 参考解法 | 27.6091 | 73.9926 | 94.7022 |
  | 部分解法 | 27.6091 | 73.9926 | 93.9963（cas-search 120/136，对比 128） |
  | 错误对照 | 27.5091 | 73.8926 | 94.6022（cas-pty 10/11，失败 = 1） |

  作业 `evidence/runs/rust_multicrate_reconstruction-v2-paired-r2-{starter,reference,partial,bad}`，每个都是 `status: exit=0`，且收集到了每一组的 `score-results.json`。在修复版中，部分解法和错误对照仍然失去它们出错的测试（8 项 cas-search 测试、1 项 cas-pty 测试）。第 1 轮作业（`…-v2-paired-{starter,reference,partial}`）给出了相同的原始分数和“+ cc 文件”分数；它们使用的是第一版修复包，其中没有 cas-search 的改动，cas-search 的缺陷正是这样被发现的。
- **单独隔离 fail-fast。** 用去掉 `--no-fail-fast` 的修复版对相同的提交字节评分（作业 `…-v2-failfast-isolation-r2-{reference,partial,bad}`，初始项目来自 `…-v2-failfast-isolation-b`；作业 `…-isolation-a` 磁盘耗尽，未使用）。
- **随附依赖文件。** 在固定的评分器镜像中列出归档内容，对全部 741 个随附依赖 crate 逐一核对校验和（只有 `cc` 缺少文件），并对照 `.cargo-checksum.json` 检查恢复的文件。列表没有保存在本仓库中；可从 `cas_rust_benchmark.tar.gz`（sha256 `5e2fb3e3…`，与 `repairs/rust_multicrate_reconstruction-v2/source-lock.json` 中一致）复现：`tar tzf` 给出 44,858 个条目，没有任何一个的路径组成部分名为 `target`；有 741 个条目匹配 `vendor-deps/*/.cargo-checksum.json`；把每个 crate 校验和文件中的文件列表与归档比较，只在 `vendor-deps/cc` 中发现缺失文件（`src/target/apple.rs`、`generated.rs`、`llvm.rs`、`parser.rs`）。
- **豁免，真实 Cargo。** 在原始公开镜像中，原始评分器和修正后评分器中未经修改的 `run_crate_test`，在一个名为 `cas-pty` 的真实 11 项测试 crate 上运行（10 个真实的 cas-pty 测试名加一个占位测试）：

| 场景（真实失败数） | 原始评分器 | 修正后的评分器 |
| --- | --- | --- |
| S1 全部通过 (0) | PASS 11/0 | PASS 11/0 |
| S2 只有被豁免的测试失败 (1) — 预期的豁免 | PASS 11/0 | PASS 11/0 |
| **S3 被豁免的测试通过，`test_pty_config_default` 失败 (1)** | **PASS 11/0（错误）** | TEST_FAIL 10/1 |
| S4 被豁免的测试通过，另两项失败 (2) | TEST_FAIL 10/1（宽恕了一项） | TEST_FAIL 9/2 |
| S5 被豁免的测试和另一项都失败 (2) | TEST_FAIL 10/1 | TEST_FAIL 10/1 |
| S6 被豁免的测试通过，`…_with_teams_lead` 失败 (1) | **PASS 11/0（错误）** | TEST_FAIL 10/1 |

- **豁免，形式化检查（TLA+）。** TLA+ 是一种描述系统行为的语言，其检验器 TLC 会探索每个可达状态。有界模型 `KnownFailureCredit.tla` 覆盖一个含 4 项测试的 crate，每项测试为 ok、FAILED、ignored 或 absent，最多 2 项被豁免的测试。它检查不变式 `PassSound` 和 `CreditSound`。在原始评分器上两者都不成立；反例为 `outcome=<<ok,ok,ok,FAILED>>, Ex={1}`：被豁免的测试通过，另一项失败，而 crate 状态为 PASS。在修正后的规则（即修复版对 cas-pty 的豁免规则）上，两者都成立：最多 1 项被豁免测试时有 2,304 个不同状态，最多 2 项时有 4,608 个。该模型不涵盖其他三个缺陷：隐藏测试的放置位置、Cargo 在失败的二进制处停止，以及随附依赖文件。
- **算术。** 上文的每项分数影响都由 `score.py` 中的层级权重和所引运行中的测试计数推出。

## 局限

- 没有运行任何 AI 模型或解题者。参考解法是上游代码，而不是某个解题者写的；它替换的 507 个文件还带有上游的测试辅助代码，而任务允许解题者实现这些代码。
- 两处编译失败会影响每份不改动测试的提交。fail-fast 和豁免对真实提交造成多少损失，取决于其失败出现在哪里，没有测量。
- 发布方的评分环境是根据对其初始项目结果的精确复现推断出来的，没有文档记载。
- 29.22 的上界针对随附的测试。解题者添加的测试在两个版本中都可能改变 crate 的总数。
- 使用 `--no-fail-fast` 后，排在后面、会崩溃的测试二进制现在也会运行，此时即使其库测试先失败，该 crate 也会被记为崩溃；而在原始评分器中，Cargo 会在此之前停止。在 cas-mux 之外，没有运行出现这样的崩溃。
- 初始文件中的属性测试策略是桩（`Just("test")`）。不改动该辅助文件的解题者在修复版中会有几项属性测试失败：这里 cas-cli 得 1252/1344，而使用上游文件时得 1258/1344（`evidence/runs/rust_multicrate_reconstruction-failfast-paired-r3`），相差 0.045 分。
- 这些运行使用了一个监视程序，在评分器构建好合并后的工作区后删除公开阶段的 `target/`；没有它，两次构建会撑满 20.7 GB 的工作节点磁盘。此时公开阶段的结果已经确定。
- 豁免测试用的 crate 使用真实的 cas-pty 测试名，但不是真实的 crate。TLA+ 模型是有界的（4 项测试，最多 2 项被豁免），且不包括编译失败、超时和崩溃分支、多个测试二进制以及层级加权。
- 没有查明 `test_pty_config_claude_with_teams` 为何被列为已知失败。

## 复现

- 修复版和并排对照运行：`repairs/rust_multicrate_reconstruction-v2/`（`README.md`、`repair.patch`、`materialize.sh`、`source-lock.json`、`Dockerfile`、`Dockerfile.work`）；结果见 `paired/results.md`，相关脚本为 `run-paired.sh.in`、`run-failfast.sh.in`、`build_sub.py`、`strip.py` 和 `diag.py`。
- 运行：`evidence/runs/rust_multicrate_reconstruction-v2-paired-*`、`…-v2-paired-r2-*` 和 `…-v2-failfast-*`；各二进制的测试计数见 `evidence/runs/rust_multicrate_reconstruction-failfast-paired-r3/result/out/raw/`。
- 用真实 Cargo 测试豁免：`evidence/scripts/rust_multicrate_reconstruction/run_native_fixture.sh`（输出在 `out/run.log` 和 `out/results.json`）。它需要源码导出文件 `rust_multicrate_reconstruction_nested-000.tar.gz`（`SRC_TGZ`），该文件不在本仓库中；原始的 `score.py` 也可以从评分器镜像中取得（sha256 见下）。
- TLA+ 模型：`evidence/formal/tla/rust_multicrate_reconstruction/run_tlc.sh`（输出在 `tlc_*.out`）。
- 固定标识：评分器镜像 `seededge/edgebench.judge.rust_multicrate_reconstruction@sha256:d1d18aed02e81e5f09938de0272a76a72fab174a784613aefa3eb51443f6e408`，原始 `judge/tools/score.py` 的 sha256 为 `d725dd934a01e40948267131d8ae91a075b4217d8012b41468cc9b38bb782b35`；修复版 `score.py` 的 sha256 为 `50707cd4d7e7256777fa806ba450d7185cd2d872806c4c915bd4bc119d09b545`。

支撑记录：`evidence/reviews/rust_multicrate_reconstruction.md`。
