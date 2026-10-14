# Git Rewrite in Zig (`git_rewrite_in_zig`)

**结论：** 已修复。<mark>如果提交的文件夹里留有构建产物（`main`、`main.o`），或者有一行源码调用系统的 `git`（哪怕只在测试里），原始评分器就把整份提交记 0 分。按规则做题的解题者也可能碰上这两种情况，而任务说明对这两项检查只字未提。修复版在构建前删掉残留文件，并去掉了源码文本检查；正确的 git 仍得 100 分。</mark>

## 任务要求

任务说明写道："Reimplement git in Zig as a drop-in replacement for the `git` binary."（用 Zig 重新实现 git，可以直接替换原程序。）这个二进制程序 "must behave identically to the real `git` — same CLI interface, same output formats, same exit codes."（行为必须与真正的 git 完全相同——相同的命令行接口、相同的输出格式、相同的退出码。）分数是 git v2.47.0 自带的 `t/` 测试套件的通过比例，分母固定为 29,075 个测试。类别：系统与软件工程。

## 问题出在哪里

- 评分之前，`test.sh` 会检查提交的文件夹。只要有一项检查失败，整份提交的奖励值（reward）就记 0（`compute_reward.py:118-123`）。任务说明一项检查也没有描述，只说 "Do not compile or link the C source or wrap around the existing git binary"（不要编译或链接 C 源码，也不要包装现有的 git 程序），还鼓励 "The system `git` is installed — use it to test your implementation as you go"（系统中装有 git，可以边写边用它测试你的实现）。
- 我们在正常模式下用原始评分器、以任务自带的初始代码为基础测量（`evidence/runs/git_rewrite_in_zig-v2-paired-gates-b/`；最初发现于 `evidence/runs/git_rewrite_in_zig-gates/`）：
  - 未修改的初始代码能通过检查（奖励值为 0.000069，即它通过的 2 个测试）；
  - 在项目文件夹中运行 `zig build-exe src/main.zig -lc -lz` 会留下 `main` 和 `main.o`，奖励值为 0（`precompiled_objects`、`stray_elf_binaries`，`test.sh:105-121`）；只留其中一个文件也得 0；
  - `src/` 中有一个调用系统 git 来比对输出的 `test` 块，得 0（`shells_out_to_git`，`test.sh:89-94`）；`src/` 中有一个只供测试用的辅助文件，结果也一样。两者都不会进入发布的二进制程序。
  - 文档所述的 `zig build`，以及 `zig test` 和 `zig run`，都不会留下这类文件（在同一评分器镜像中本地运行，Zig 0.14.0）。
- 评测框架会把除 `.git`、`zig-cache`、`zig-out` 和 `.zig-cache` 之外的整个项目文件夹发过去，并保留可执行权限位（`sforge/harness/run_agent.py:185-215`），所以项目根目录或 `src/` 里留下的任何东西都会被检查。

**说明：CPU 上限（修复没有改动）。** `test.sh` 同时运行 `nproc` 个测试脚本，每个限时 120 s，而 `nproc` 不考虑 CPU 配额（`test.sh:286`、`:301`）。我们在一台 8 核主机上用一个正确的 git（C v2.47.0，oracle 模式）测量（`evidence/runs/git_rewrite_in_zig-nproc-c8c4/`、`-c2/`、`-c1/`）：

| `--cpus` | 每个 CPU 的脚本数 | 最慢的脚本 | 在 120 s 时被终止 | 通过 | 分数 |
|---|---:|---:|---:|---:|---:|
| 8 | 1 | 25 s | 0 | 29,075 | 100 |
| 4 | 2 | 45 s | 0 | 29,075 | 100 |
| 2 | 4 | 109 s | 0 | 29,075 | 100 |
| 1 | 8 | 120 s | 2 | 28,311 | 97.37 |

- 在 `--cpus 1` 下，`t1092` 和 `t0027` 恰好跑满 120 s 后被切断，丢了 42 + 722 = 764 个测试（29,075 − 28,311），奖励值为 0.973723（`reward.json`）。只有这两个脚本的通过数与 8-CPU 运行不同。
- 只有 `t1092` 带有评分器的 `# TIMEOUT after 120s` 标记（`timeouts.txt`）。`t0027` 的输出也在 120 s 时被切断，却没有这个标记，所以这个标记漏计了超时。
- 脚本用时取每个结果文件从创建到最后一次写入的时间（`stat_times.txt`）。起作用的是每个 CPU 分到几个脚本，所以 16 核主机配 `--cpus 2` 的表现与最后一行相同。比 C git 慢的 Zig 移植版会更早撞上时限。
- EdgeBench 的排行榜设置给这个评分器 4 个 CPU（默认值，本任务没有另行设置；引用见 [`evidence/impact/edgebench-leaderboard-config.md`](../evidence/impact/edgebench-leaderboard-config.md)）。在 8 核主机上，这相当于每个 CPU 2 个脚本，即上表 `--cpus 4` 一行：没有脚本被切断，最慢的用了 120 s 中的 45 s，正确的 git 得 100 分。主机核数更多时，`nproc` 和每个 CPU 的脚本数都更高（32 核主机为每个 CPU 8 个，即最后一行）；排行榜用的主机有多少核，我们不知道。不做配置时，评测框架不设 CPU 配额（`judge_cpu_limit` 为 `None`，`sforge/harness/config.py:69`），也就不会出现这种情况。这一点写进文档，但不做改动。

随任务发布的说明：

- 任务说明没有描述评分方法（git 的 `t/` 套件，按单个测试计数）。
- 真正的 Zig 提交还得自己提供 `--exec-path` 和各个辅助程序，任务说明没有写明这一点。

## 影响有多大

一份按规则完成的提交，只要触发三项检查中的一项，在原始评分器下就会丢掉全部分数，最多 100 分；修复版则按它的测试结果评分。其他所有提交在两个版本下分数相同。真实运行中有多少次触发了检查，不得而知；本任务的排行榜平均分为 15-24（`evidence/impact/leaderboard_12h.json`）。

## 修复

只改动一个文件 `/opt/tests/test.sh`（`repairs/git_rewrite_in_zig-v2/`）：

- 干净构建之前，修复版删除残留的 `*.o`、`*.a`、`*.so`、`*.so.*` 和 `*.dylib` 文件，以及 `zig-out` 和 Zig 缓存之外的可执行 ELF 文件，并记入日志。原版遇到这些文件会把分数记 0。
- 去掉了针对 git 调用的源码文本检查。运行测试时已经没有 git 可调用：git 源码、系统 git 和测试构建中的 C git 二进制程序都会事先删除（修复版 `test.sh:147`、`:235-237`、`:261-262`，对应原版第 143、231-233 和 257-258 行；并排对照运行中的 `git_after_nuke.txt` 显示没有剩下任何 `git` 或 `git-*` 程序）。
- 其他都不变，包括其余检查、测试运行、并行度和奖励值。`compute_reward.py` 和 `pytest_shim.sh` 在两个镜像中完全相同（`grader_sha.txt`）。`task.json.in` 中只改了 `judge.image_tag`。

并排对照测试，原始评分器对修复版，相同输入，`--network none --cpus 8 --memory 6g`（`repairs/git_rewrite_in_zig-v2/paired/results.md`，来自 `evidence/runs/git_rewrite_in_zig-v2-paired-gates-b/` 和 `-oracle-b/`）：

| 提交的目录树 | 原始评分器 | 修复版 |
|---|---:|---:|
| 未修改的初始代码 | 0.000069 | 0.000069 |
| 运行 `zig build-exe` 之后（`main`、`main.o`） | 0 | 0.000069 |
| 只有 `main.o` / 只有 `main` | 0 / 0 | 0.000069 / 0.000069 |
| 调用 git 的 `test` 块 / 只供测试的辅助文件 | 0 / 0 | 0.000069 / 0.000069 |
| 真正的 git v2.47.0（oracle 模式） | 1.000000 | 1.000000 |
| 包装 C git 的提交 | 不得分 | 不得分 |

奖励值在 0 到 1 之间；满分 100 的分数为奖励值 × 100。"不得分"表示最多只拿到未修改的初始代码通过的那 2 个测试（0.000069）。

- 修复版给初始代码和五个正常目录树的 `reward.json`，与原始评分器给初始代码的逐字节相同：通过 2 个测试，失败 69 个。
- 使用真正的 git 时，两个版本都运行了 1,007 个脚本中的 1,007 个，0 个测试失败，0 次超时，逐脚本计数完全相同（`oracle/v{1,2}/per_script_ok_notok_timeout.txt`）。

**分数可以与原版比较。** 对每一个提交的目录树，修复版的分数要么与原始评分器相同，要么原版给的是 0：只要目录树里没有修复版会删的东西，也没有会被已去掉的检查匹配到的行，两个版本运行的命令就完全相同。

## 我们如何检查

- **原始评分器，来自按摘要固定的公开镜像。** 每次运行都在一个新容器中原样使用任务的 `eval_cmd`，参数为 `--network none --memory 6g`，用的是随附的 `test.sh`（sha256 `c2e6d446…`）、git `t/` 套件、`compute_reward.py` 和 `pytest_shim.sh`。
- **通过 eval_cmd 的正常模式运行**，原始评分器和修复版用相同的目录树：初始代码、五个会触发检查的正常目录树，以及两种包装方式。见上表。
- **真正的 git。** 我们在评分器镜像中（`--network none`），用评分器自带的测试套件源码树构建了一个真正的 git v2.47.0，make 参数与 `test.sh` 相同，放在 `zig-out/bin/` 中。它在评测框架自带的 `HARBOR_ORACLE_MODE=1` 下运行。这个模式跳过对提交目录树的检查、干净的 `zig build` 和删除系统 git 的步骤；运行测试和计算奖励值的过程与计分路径完全相同。在较早的运行中（`evidence/runs/git_rewrite_in_zig-oraclefull/`），以及并排对照运行的两个版本下，它都得到 29,075 中的 29,075，奖励值为 1.000000。完整运行中，每个类别的通过数都恰好等于评分器固定的 `oracle_attempted` 基线：t0 5379、t1 3191、t2 980、t3 4778、t4 3485、t5 4540、t6 2355、t7 2912、t8 493、t9 962。147 个脚本因为缺少前置条件而自行跳过，例如 "Cannot run httpd tests as root"。
- **CPU 上限。** 同一个真正的 git，在一台 8 核 E2B 工作节点上分别以 `--cpus` 8、4、2 和 1 运行；每次运行中 `nproc` 都是 8，`cpu.max` 显示了配额。
- **修复版。** 用修复包的 `Dockerfile` 从公开镜像构建；其 `test.sh`（sha256 `87bae2a5…`）与 `source-lock.json` 中的 `materialize.outputs` 一致（`materialize.log`）。两个并排对照作业都以 `status: exit=0` 结束，结果都已收集。

## 局限

- 我们没有运行任何 AI 模型或解题者。结果来自我们写的测试提交。
- 并排对照运行中的正常目录树，是在初始代码上加了残留文件或测试，不是真正的 Zig 移植版。并排对照表的每一组跑了三次（`-rep2`、`-rep3`），奖励值完全相同；逐步减少 `--cpus` 的作业只跑了一次。
- 代替真正 git 的是在 oracle 模式下运行的 C git，不是走正常构建路径的 Zig 二进制程序。
- CPU 上限的运行只用了一台 8 核主机，每种设置跑一次。

## 复现

- 评分器镜像：`sha256:645bc84baa85…`。
- 并排对照运行：`evidence/runs/git_rewrite_in_zig-v2-paired-gates-b/` 和 `-oracle-b/`（`run.sh`）；摘要和脚本在 `repairs/git_rewrite_in_zig-v2/paired/`（`results.md`、`run_gates.sh`、`run_oracle.sh`）。
- 对检查的首次测量：`evidence/runs/git_rewrite_in_zig-gates/`。CPU 上限：`evidence/runs/git_rewrite_in_zig-nproc-c8c4/`、`-c2/`、`-c1/`。
- 原始评分器上的真正 git：`evidence/runs/git_rewrite_in_zig-oraclefull/run.sh`（完整套件）和 `evidence/runs/git_rewrite_in_zig-oraclet0001/run.sh`（仅 t0001）。输出在各文件夹的 `result/` 中。
- 修复版：`repairs/git_rewrite_in_zig-v2/`（`README.md`、`repair.patch`、`materialize.sh`、`source-lock.json`）。
- 审查记录：`evidence/reviews/git_rewrite_in_zig-native.md`。
