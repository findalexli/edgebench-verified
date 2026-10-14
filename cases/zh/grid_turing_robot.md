# Grid Turing Robot (`grid_turing_robot`)

**结论：** 已修复。<mark>README 承诺每个用例 30 s，但在发布方的 4-CPU 评分器上，每个用例用掉超过约 15 s CPU 的有效解法会超时，而只要一个用例超时，整份提交就作废。修复版同时运行的用例数不超过评分器的 CPU 数。还有两项说明：分数刻度起点有偏移（2.84 分）；"一个用例失败，整份提交作废"的规则没有写明（约 20 分）。</mark>

![折线图：每个测试用例的时钟时间与计算时间的关系。8 个 CPU 时，从 12 到 28 秒，时钟时间等于计算时间。4 个 CPU 时，12 秒计算耗时 24 秒，14 秒耗时 28 秒；16、20、24 和 28 秒在 30 秒时限处标为超时，50 个用例中 48 个超时，没有分数。注释说明修复版评分器让 16 秒和 28 秒的解法通过全部 50 个用例，得 19.80 分（满分 100）。](../figures/zh/grid_turing_robot.svg)

*在 EdgeBench 官方的 4 CPU 设置下，Grid Turing Robot 的有效解法只要每个测试用例需要超过约 15 秒的计算，就得不到分数，尽管任务说明承诺每个用例有 30 秒。智能体要编写一张规则表，驱动机器人在网格上移动。评分器同时运行 8 个用例，所以在 4 个 CPU 上每个用例只分到半个 CPU，时钟时间是计算时间的两倍；只要有一个用例超时，整份提交就作废。每用例需要 16 秒和 28 秒的测试解法，在原始评分器上 50 个用例中有 48 个超时。修复版评分器同时运行的用例数不超过 CPU 数，这两个解法在它上面得 19.80 分（满分 100）。*

## 任务要求

解题者要写一张规则表（类似图灵机的转移表），驱动一个机器人在网格上移动。任务文本写道："Your solution is scored on **50 fixed test cases**. Final score = sum of individual case scores. **Lower is better.**"（解法在一组固定测试用例上评分；最终得分为各用例得分之和；越低越好。）README 给出单个用例的得分为 "If V = K: Score = C + Q"，惩罚为 "If V < K: Score = 2N^4 + (K − V) × N^2"，并写明 "Time limit | 30 seconds / test case"（每个测试用例的时限）。类别：组合优化。

## 问题出在哪里

评分规则本身实现得没错，问题出在边界条件上。(c) 在新版本中修复，(a) 和 (b) 作为说明发布。

**(a) 一个用例失败，整份提交作废。** 任务文本没有说明这一点。只要有一个用例崩溃、超时或输出格式错误，这个用例的分数就是无穷大，`TOTAL_SCORE` 也就成了 `inf`。EdgeBench 的评测框架保留这样的结果（`valid: true`），原始分数为 `inf`，没有 100 分制分数（总分不是有限值时 `rescale_score` 返回 None，`sforge/harness/score_rescale.py:75-76`）；在 `minimize` 下，任何完成的提交都排在它前面。

| 解法（都是正常解法） | 评分器逐用例结果 | TOTAL_SCORE | 评测框架是否计分 | 100 分制得分 |
|---|---|---|---|---|
| `good_stepstate`（已知是好解法） | 50 OK | 94,092 | 是 | 19.80 |
| `fail_partial`（格式正确；用例 0000 上路线被截掉一半） | 50 OK | 202,310 | 是 | 19.56 |
| `fail_crash`（只在用例 0000 上抛出错误） | 0000 RE score=inf | inf | **否**（原始分 `inf`） | None |
| `fail_tle`（在用例 0000 上休眠 40 s） | 0000 TLE score=inf | inf | 否（原始分 `inf`） | None |

分数越低越好，所以失败永远不会让解题者占便宜。评分器不会丢掉失败的用例，也不会把它记为 0。

**(b) 分数刻度起点有偏移。** 配置的 0 分参考点（基线）是 9,025,986。随任务提供的初始解法什么也不做，它在 50 个评分用例上的实际总分是 7,744,909，所以得 **2.84** 分（满分 100），而不是 0 分。

**(c) 在 4-CPU 评分器上，每个用例 30 s 缩水为约 15 s CPU（已修复）。** 评分器每次同时运行八个用例（`ProcessPoolExecutor(max_workers=min(8, len(case_files)))`），墙钟时限为 30 s，任务没有设 `cpu_limit`。在 EdgeBench 的排行榜配置 `examples/all-tasks-k8s/experiment.yaml` 中（引用见 [`evidence/impact/edgebench-leaderboard-config.md`](../evidence/impact/edgebench-leaderboard-config.md)）（sha256 `d9d299794ba946cae8d2b7f68a7879a35bb8565d95e78107edf79802993643be`，标题为 "OFFICIAL EDGEBENCH LEADERBOARD SETTING"），`grid_turing_robot: {}` 继承 `judge_cpu_limit: 4`。k8s 后端把它设为评分器 pod 的 CPU request 和 limit（`sforge/harness/backend/k8s_backend.py:214-224`）。八个用例在 4 个 CPU 上，每个大约分到半个 CPU。所以单线程解法只要每个用例需要超过约 15 s CPU，就会超过 30 s 的墙钟时限，尽管 README 承诺 "30 seconds / test case"；而按 (a)，有一个这样的用例，整份提交就作废。

我们在原始评分器上用 `--cpus 4` 测量（`evidence/runs/grid_turing_robot-cpu4v8-a/result/out/summary.txt`，在 `grid_turing_robot-v2-paired` 中重复）：

| 有效解法（已知正确的输出，之前先做固定量的工作） | 4 个 CPU | 8 个 CPU |
|---|---|---|
| 每个用例 12 或 14 s CPU | 50 OK，TOTAL 94,092 | 50 OK，TOTAL 94,092 |
| 每个用例 16、20、24 或 28 s CPU | **2 OK，48 TLE，TOTAL `inf`（无分数）** | 50 OK，TOTAL 94,092 |
| 工作到 25 s 墙钟截止时间 | 50 OK，TOTAL 94,092；每个用例平均 13.03 s CPU | 50 OK，TOTAL 94,092 |

（8 个 CPU 一列：`evidence/runs/grid_turing_robot-cpu4v8-b/result/out/summary.txt`。每个用例的 CPU：`grid_turing_robot-v2-paired/result/out/timing/c4-wall25-v1/`。）更早一次在本地用 `--cpus 2` 运行时，每个用例 12 s 就已经出现 48 TLE（`evidence/scripts/grid_turing_robot/native_cpus2/`）。

## 影响有多大

- (a) 受影响的提交，与给这个用例记最小惩罚相比，最多差约 20 分（满分 100）。如果这次运行更早有一份有效提交，影响为 0，因为每次运行保留最佳的有效提交。
- (b) 最多 2.84005 分（≈ 2.84；这是精确的最大值，已在 Lean 中证明），而且只出现在 0 分参考点与排名第 30 水平的参考点（rank30）之间，即 0–20 分段。
- (c) 在发布方的 4-CPU 评分器上，每个用例用约 15 到 30 s CPU 的有效解法，最多会丢掉全部分数。每个用例 16 s 和 28 s 的解法在原始评分器下作废，在修复版下通过（`evidence/runs/grid_turing_robot-v2-paired/result/out/summary.txt`）。按截止时间停止的解法在修复版下，每个用例分到的 CPU 约为原来的两倍（25 s 对照解法的平均值从 13.03 s → 24.91 s）；我们没有测量它的分数会因此变化多少。解题者每次提交后都能看到逐用例的 TLE 结果，而每次运行保留最佳的有效提交，所以只有一次运行从头到尾都没提交过更快的有效解法时，才会丢分。

## 修复

修复版（`repairs/grid_turing_robot-v2/`）改变了评分器 `/tmp/eval_grid_turing_robot.py` 同时运行的用例数。新函数 `cpu_quota_workers()` 从 cgroup 读取评分器的 CPU 配额（`cpu.max`，或 cgroup v1 的 quota 和 period），向下取整为整数个 CPU，没有配额时退回到 `os.cpu_count()`，并把结果限制在 1 到 8 之间。进程池改为 `ProcessPoolExecutor(max_workers=min(cpu_quota_workers(), len(case_files)))`。`docker run --cpus N` 和发布方的 k8s 后端都会设置这一配额；在 `--cpus 1/2/4/8` 下，修复版评分器分别同时运行 1/2/4/8 个用例（`grid_turing_robot-v2-paired/result/out/v2_workers.txt`）。任务 JSON 只改了 `judge.image_tag`。30 s 时限、README、测试程序、用例、解析器和分数刻度都没有变，(a) 中的规则也没有变。在 8 个或更多 CPU 下，修复版评分器同时运行 8 个用例，与原版完全相同。

修复版仍附带两条说明。

1. 配置的基线（9,025,986）高于随附基线的实际值 7,744,909，因此随附基线得 2.84 分而不是 0 分。
2. 只要有一个用例崩溃、超时或格式错误，总分就是 `inf`，整份提交没有分数。

我们在 `--cpus 4` 下做了并排对照测试（另有一组在 `--cpus 8` 下），两个评分器用相同的解法（`evidence/runs/grid_turing_robot-v2-paired/result/out/summary.txt`；`repairs/grid_turing_robot-v2/paired/results.md`）。

| 解法 | CPU 数 | 原始评分器 | 修复版 |
| --- | ---: | --- | --- |
| 已知正确，无额外工作 | 4 | 50 OK，TOTAL 94,092（19.80） | 50 OK，TOTAL 94,092（19.80） |
| 每个用例 12 s CPU | 4 | 50 OK，TOTAL 94,092 | 50 OK，TOTAL 94,092 |
| **每个用例 16 s CPU** | 4 | **2 OK，48 TLE，TOTAL `inf`（无分数）** | **50 OK，TOTAL 94,092（19.80）** |
| **每个用例 28 s CPU** | 4 | **2 OK，48 TLE，TOTAL `inf`（无分数）** | **50 OK，TOTAL 94,092（19.80）** |
| 工作到 25 s 墙钟截止时间 | 4 | 50 OK，TOTAL 94,092；每个用例平均 13.03 s CPU | 50 OK，TOTAL 94,092；每个用例平均 24.91 s CPU |
| 每个用例 40 s CPU（坏对照） | 4 | 50 TLE，TOTAL `inf` | 50 TLE，TOTAL `inf` |
| 每个用例 20 s CPU | 8 | 50 OK，TOTAL 94,092 | 50 OK，TOTAL 94,092 |

在修复版下，最慢的 28 s 用例从开始到结束用了 28.34 s（`result/out/timing/c4-cpu28-v2/`）。4 个 CPU 时，评分最多需要 ⌈50/4⌉ = 13 轮，每轮 30 s；坏对照用了 390.9 s（原版：210.8 s），没有超过任务 600 s 的 `eval_timeout`。

评分器有 8 个或更多 CPU 时，两个版本就是同一个评分器，分数可以比较。在 4 个 CPU 下，一个确定性的解法如果在原版下每个用例都按时完成，在修复版下输出和分数都不变；每个用例需要约 15 到 30 s CPU 的解法，在修复版下会正常评分，不再作废。一直搜索到墙钟截止时间的解法，每个用例得到的 CPU 约为原来的两倍，所以它在两个评分器下的分数不能比较。修复版不会减少任何用例的 CPU。

## 我们如何检查

- 原始评分器来自按摘要固定的原始公开镜像。我们在评分器镜像中以 `docker run --network none --memory 2g --cpus 4` 运行未修改的评分器，再用仓库中的评测框架给日志评分。做固定量 CPU 工作的解法还在 `--cpus 2` 和 `--cpus 8` 下跑过。
- 我们在 E2B 上做了 CPU 运行和并排对照测试。测试解法包括：每个用例做 12 到 28 s CPU 工作的有效解法、一个 25 s 墙钟截止时间解法和一个 40 s 的坏对照。它们先在原始评分器上用 `--cpus 4` 和 `--cpus 8` 运行（`evidence/runs/grid_turing_robot-cpu4v8-a`、`-b`），再在原始评分器和修复版评分器上并排对照运行（`evidence/runs/grid_turing_robot-v2-paired`），每个作业都是 `status: exit=0`。每个解法记录每个用例自己的开始时间、结束时间和 CPU 时间（`result/out/timing/`），不影响评分。
- 我们只根据 README 文本另写了一套独立实现，包括解析器、模拟器和计分器，没有导入任务的验证器。在 50 个评分用例上用 3,000 张随机规则表对照，0 处不一致。对已知正确的解法，两个实现在全部 50 个用例上的总和都是 94,092。
- 我们在极小的棋盘上穷举搜索了所有 C+Q ≤ 5 的规则表，确认最小代价的界。
- 数据检查表明，全部 50 个用例都有效：N 和 K 在范围内，墙壁格式正确，网格完全连通，目标互不相同，并且用独立的广度优先搜索（BFS）验证了 X ≤ T ≤ 2X。
- 种子搜索表明，没有一个评分用例与种子 0..60,000 的生成器输出相同，所以这些用例不在解题者能在本地用的 0..10000 范围内。
- 在 Lean 4 形式化检查中，`GridTuringBaseline.lean` 证明，在配置的刻度下，什么也不做的解法恰好得 6405385/2255374 ≈ 2.84005 分，并且对每一个原始总分，参考点错位多给的分数都在 0 和 2.84005 之间，在 rank30 以下为 0。50 个逐用例分数取自保存的评分器日志。形式化说明见 `evidence/formal/notes/grid_turing_robot.md`。

## 局限

- 修复版评分器从 cgroup（`cpu.max`）读取 CPU 配额。我们只用 `docker run --cpus` 测试过，没有在 Kubernetes pod 中测试，而 EdgeBench 的排行榜设置用的正是这个后端。
- 没有 cgroup 配额时，修复版评分器回退到 `os.cpu_count()`。它统计的是主机的全部 CPU，而不是评分器能用的 CPU（`os.sched_getaffinity`）。如果只限制了 CPU 集合、没有配额（例如 `docker run --cpuset-cpus`），或者 pod 看不到自己的 `cpu.max`，它仍可能同时运行比 CPU 数更多的用例，与原版一样。改用亲和性计数需要重新做一次并排对照运行，所以这里没有改。
- 我们没有运行任何 AI 模型或解题者。分数影响只在我们写的测试提交和反例上展示。
- 原始评分器的运行使用本地 Docker，参数为 `--cpus 4`、`--cpus 2` 和 `--cpus 8`，以及 `--memory 2g`；CPU 运行和并排对照测试使用有 8 个 vCPU 的 E2B 工作节点，参数为 `--memory 4g` 以及 `--cpus 4` 或 `--cpus 8`。我们没有测试 3、5、6 和 7 个 CPU。
- CPU 测试解法都是单线程的，要么做固定量的 CPU 工作，要么工作到 25 s 墙钟截止时间。我们没有测试多线程的解题者。
- 采用截止时间策略的解题者，在 4 个 CPU 下、在修复版中每个用例得到的 CPU 约为原来的两倍，所以它们在两个评分器下的分数不能比较。我们没有测量分数会变化多少。
- 评分器 CPU 少于 3 个时，600 s 的 `eval_timeout` 会比每个用例 30 s 的时限先起作用：在 2 个 CPU 下为 25 轮 × 30 s = 750 s，因此每个用例实际只能用约 24 s（原版在这种情况下每个用例约给 7.5 s CPU）。配额向下取整：2.5 个 CPU 时同时运行 2 个用例。
- 我们只测试了简单的正常解法，没有检查 100 分的参考点（rank1 = 1,575）能否达到，也没有追查 rank1 和 rank30 参考点的来源。
- 对照用的随机规则表只走出了部分路线。完整路线上的一致性，依据的是已知正确的解法和一个半程路线用例。
- 种子搜索只覆盖了 gen.py 的种子 0..60,000。

## 复现

- 评分器镜像摘要：`sha256:f67864ad75a3…`。
- 修复版：`repairs/grid_turing_robot-v2/`（`materialize.sh`、`repair.patch`、`source-lock.json`；修复版评分器 sha256 `285229ee…3a22`）。并排对照测试：`repairs/grid_turing_robot-v2/paired/run.sh`（实际运行的版本：`evidence/runs/grid_turing_robot-v2-paired/run.sh`）；原始评分器上的 CPU 运行：`evidence/runs/grid_turing_robot-cpu4v8-a/run.sh`、`-b`。
- 原始评分器的运行：`evidence/scripts/grid_turing_robot/run_native.sh`，然后运行 `grade.py`（输出在 `native/grade_out.txt`；CPU 运行在 `native_cpus2/` 和 `native_cpus8/`）。`native_cpus8/grade_out.txt` 中有两行 `cpu12.log`：第一行（`valid=True`，原始分 `inf`，没有归一化分数）是对 2-CPU 日志的评分，第二行（`valid=True`，19.8014）是对 8-CPU 日志的评分。
- 独立实现、数据检查和极小棋盘搜索：`evidence/scripts/grid_turing_robot/oracle.py`（输出 `data_out.txt` 和 `brute_out.txt`）。
- 随机规则表对照：`evidence/scripts/grid_turing_robot/fuzz_agree.py`（输出 `fuzz_out.txt`）。
- 种子搜索：`evidence/scripts/grid_turing_robot/seeds_header.py`（输出 `seeds_header_out.txt`）。
