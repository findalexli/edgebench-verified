# Warehouse Forklift Routing (`warehouse_forklift_routing`)

**结论：** 评分器修复已经测试；EdgeBench 等待最后结果的方式也需要相应修改，这一部分只做了分部测试，还没有在完整运行中检验。<mark>任务说明承诺每个测试用例 30 s，评分器却只给每个输入（含五个用例）60 s。在发布方 4 个 CPU 的评分器上，它还同时跑 8 个输入，每个输入只分到约半个 CPU。修复版把时限提高到承诺的每个输入 150 s，让同时运行的输入数不超过评分器的 CPU 数，分数刻度不变，并在文档里写明约 30.6 分（满分 100；显示舍入前为 30.3）的上限。这个上限由原始总分的一个下界推出，该下界已在 Lean 中检验。</mark>

![每组输入的时间条，从 0 到 150 秒。原始评分器：约 30 秒计算，随后是 60 秒时限，承诺的 60 到 150 秒范围标为超时。修复版评分器：完整的 150 秒，最多同时运行 4 组输入，每组一个 CPU。表格列出三个测试提交（每个用例 13 秒，每组输入计算 80 秒和 140 秒）：在原始评分器上 50 组全部超时、没有分数，在修复版上 50 组全部计分。方框说明已记录、未修复的上限：约 30.6 分（满分 100；取整前为 30.3）。](../figures/zh/warehouse_forklift_routing.svg)

*在 Warehouse Forklift Routing 中，解法只要用足任务说明承诺的时间，就得不到分数。任务说明承诺每个测试用例 30 秒，每组五个用例共 150 秒，但原始评分器在每组输入运行到 60 秒时就把它终止。在 EdgeBench 的 4 CPU 设置下，它还同时运行 8 组输入，所以每组只得到约 30 秒的计算时间；只要有一次超时，整份提交就没有分数。每个用例等待 13 秒、或每组输入计算 80 秒或 140 秒的测试提交，在原始评分器上没有分数。修复版允许 150 秒，同时运行的输入组数不超过 CPU 数，在它上面 50 组输入全部计分（修复还需要在 EdgeBench 的运行器中延长最终等待时间，这一部分只做了局部测试）。另一个上限已记录、未修复：任何有效答案都不可能超过约 30.6 分（满分 100）。*

## 任务要求

本任务改编自 CodeChef 题目 WAREHOUS。解题者要输出叉车指令串，把陆续到达的 R·C−1 件货物存进一个 R x C 的网格，再按顺序发出去。目标是 "Minimize the total instruction string length"（使指令串总长度最小）。任务说明写明 "T=5 test cases per input"（每个输入的测试用例数）和 "Time limit: 30 seconds per test case"（每个测试用例的时限）。README 写道 "Final score = sum of per-input average scores."（最终分数为各输入平均分之和。）原始结果越低越好。类别：组合优化。

## 问题出在哪里

### 1. 时限比承诺的更严

任务说明承诺每个测试用例 30 s，每个输入 5 个测试用例，也就是每个输入 150 s。评分器却给整个输入设了 `TIME_LIMIT = 60`，并行跑 8 个输入。超时记为 `inf`，所以一次超时就让 `TOTAL_SCORE` 变成 `inf`。EdgeBench 的测试框架会保留这样的结果（`valid: true`），原始分数为 `inf`，不给 100 分制得分（总分非有限时 `rescale_score` 返回 None，`sforge/harness/score_rescale.py:75-76`）。在 `minimize` 下，任何跑完了的提交都排在它前面。所以一次超时，整份提交的分就全没了。

在原始评分器上，一份带时间预算的测试提交（会 sleep）在每个测试用例上花 13 s，不到承诺时限的一半，结果是 50 个 TLE（超时）、总分 `inf`，没有分数。按任务说明，50 个输入都应该计分。

本地工具不会给出任何警告，因为 `tools/bin/tester` 只给输出文件打分。按承诺的时间预算来做的解题者，会丢掉全部分数。

在发布方 4 个 CPU 的评分器上，原始版每个输入的 60 s 约合 30 s CPU 时间，同一个修复版纠正了这一点。 时限按墙钟时间算，而评分器不管有几个 CPU，都运行 `ProcessPoolExecutor(max_workers=min(8, len(case_files)))`。EdgeBench 的排行榜设置给这个评分器 4 个 CPU（默认值，本任务没有另行设置；引文见 [`evidence/impact/edgebench-leaderboard-config.md`](../evidence/impact/edgebench-leaderboard-config.md)），所以同时跑的 8 个输入每个约分到半个 CPU。在原始评分器下，单线程解题者只要每个输入用了超过约 30 s CPU，就会丢掉全部分数（半个 CPU 跑 60 s 墙钟时间；这是算出来的，实测的几组都超过了这个数）。只把时限提到 150 s，这样的解题者仍会在约 75 s CPU 处超时。我们在 `--cpus 4` 下测了这个只改时限的版本（150 s，同时 8 个）。每个输入做固定 80 s 或 140 s CPU 计算的有效解法，都是 2 OK + 48 TLE，没有分数（`evidence/runs/warehouse_forklift_routing-v2-cpu4-b/result/out/summary.txt`、`-cpu4-a`）。原始评分器对两者都是 50 TLE（`-cpu4-b`、`-cpu4-c`）。

### 2. 分数刻度的参考点无法达到

测试程序接受的每个指令串都满足 S ≥ 2RC(R+C−1) − 6(R+C−2) − 2，所以每个有效的单用例分数都 ≥ 20 − 6(R+C−2)/(R+C−1)。在 50 个评分输入上，每个有效的 TOTAL 都 ≥ 198283458104808536/278277680055375 ≈ 712.538。即使算上显示时的舍入，它也高于 "rank1" 参考点。

TOTAL ≥ 712.538 > rank1 395.80，"super_anchor" 参考点（293.51）更低。按任务自己的分数刻度，任何有效提交都得不到约 30.3 分以上（满分 100；精确下界处为 30.308；显示舍入后可能的最低总分 710.2 处为 30.586）。

所以 0–100 的刻度实际上限远低于 100。提交之间的先后顺序没有变。

### 已检查、且发现不会改变分数的部分

- 测试程序允许空载叉车开进被占用的格子。这比原始 CodeChef 规则宽松，但任务说明写清楚了。按哪种规则做的解题者，测试程序都接受。
- 对角线构造恰好得 20.0 分，加一次 E,W 绕行得 20.2 分。
- 测试程序把每个输入的分数打印到小数点后 1 位，TOTAL 因此最多偏 2.5 个原始分（能达到的最低显示 TOTAL 为 710.2），在上限处约合 100 分制的 0.3 分（30.308 → 30.586，`evidence/scripts/warehouse_forklift_routing/lean_bound/recompute_total.out.txt`）。
- 失败累加成 `inf`，该提交没有分数，这和 README 里的"求和"一致。
- 计分是确定性的。
- 数据格式正确。我们回放了生成器种子 0..300,000，没有复现出 50 个评分文件中的任何一个，可见评分输入不在公开的种子范围内。

## 影响有多大

- 由于时限，解题者只要在某个输入上用了 60–150 s（仍在承诺预算之内），就会丢掉全部分数。在发布方 4 个 CPU 的评分器上，单线程解题者只要在某个输入上用了超过约 30 s CPU，也是一样，因为同时跑的 8 个输入每个只分到约半个 CPU。更快的解题者不受影响。一直搜到墙钟截止时间（低于 60 s）才停的解题者，在 4 个 CPU 下每个输入只分到约半个 CPU。如果有一整个 CPU，它能多得多少分，我们没有测量。
- 由于分数上限，每个解题者的 100 分制得分都封顶在约 30.6（显示舍入前为 30.3）。这是一个上界，实际能达到的最高分不知道，可能更低（见局限）。

## 修复

修复版在 `/tmp/eval_warehouse_manager.py` 里改了两处。第一，`TIME_LIMIT = 60` 改为 `TIME_LIMIT = 150`，即任务说明承诺的每个测试用例 30 s × T=5。第二，新函数 `cpu_quota_workers()` 从 cgroup 读取评分器的 CPU 配额（`cpu.max`，或 cgroup v1 的配额和周期），向下取整成整数个 CPU，没有配额时退回 `os.cpu_count()`，结果限制在 1 到 8 之间。进程池改为 `ProcessPoolExecutor(max_workers=min(cpu_quota_workers(), len(case_files)))`。在 `--cpus 1/2/4/8` 下，修复版评分器分别同时跑 1/2/4/8 个输入（`evidence/runs/warehouse_forklift_routing-v2-cpu4-a/result/out/v2_workers.txt`）。有 8 个或更多 CPU 时，和原始版一样同时跑 8 个。`eval_timeout` 仍是 3600。这个修复的早先版本只改了时限（sha256 `eff6a69b…7b95`），当前修复版评分器的 sha256 为 `afccb3bb…5a76`。任务 JSON 只改了 `judge.image_tag`。工作镜像、任务说明、README、测试程序、用例、解析器、选取规则和分数刻度都不变。

`piecewise_log_min` 的参考点保留，没有替换。已证明的下限只是一个下界，不是已知的最优值，把 100 分定在那里等于凭空重新校准。保留参考点，分数就能和原始版继续比较。发布说明写明了上限（精确下界处 ≈30.3，显示舍入后 ≈30.6）。

| 提交 | 角色 | 原始评分器 | 修复版评分器 |
| --- | --- | --- | --- |
| 通用的有效测试提交 | 正确 | OK 50/50，TOTAL 46676.8 | OK 50/50，TOTAL 46676.8 |
| 一个无意的错误 | 无效 | 49 OK + 1 WA → inf | 49 OK + 1 WA → inf |
| 随附的初始文件 | 无效 | 50 WA → inf | 50 WA → inf |
| **每个测试用例 13 s（使用承诺的预算）** | **展示问题** | **50 TLE → inf** | **50 OK，TOTAL 46676.8** |
| 接近每个输入 150 s 的时限 | 展示问题 | 50 TLE → inf | 50 OK，TOTAL 46676.8 |

（WA = 答案错误，TLE = 超时。来源是 `repairs/warehouse_forklift_routing-v2/paired/results.md` 的 "Paired run" 一节，在 `--cpus 2` 下用早先只改时限的修复版跑了三次。五行全部在 `--cpus 4` 下用当前修复版重跑过，结果相同，见 `evidence/runs/warehouse_forklift_routing-v2-cpu4-c`、`-cpu4-d`。）

下表是发布方 4 个 CPU 下的 CPU 份额（`evidence/runs/warehouse_forklift_routing-v2-cpu4-a` 到 `-d`，`result/out/summary.txt`）。

| 提交 | CPU 数 | 原始评分器 | 只改时限的修复（150 s，同时 8 个） | 修复版 |
| --- | ---: | --- | --- | --- |
| **每个输入 80 s CPU** | 4 | 50 TLE → inf | **2 OK + 48 TLE → inf** | **50 OK，TOTAL 46676.8** |
| **每个输入 140 s CPU** | 4 | 50 TLE → inf | **2 OK + 48 TLE → inf** | **50 OK，TOTAL 46676.8** |
| 每个输入 80 s CPU | 8 | 未运行 | 50 OK，TOTAL 46676.8 | 50 OK，TOTAL 46676.8 |

修复版下，最慢的 140 s 输入从开始到结束耗时 140.58 s。4 个 CPU 下的评分最多耗时 1825.2 s，在 3600 s 的 `eval_timeout` 以内。最坏情况是 ⌈50/4⌉ = 13 轮 × (150 s + 30 s 测试程序超时) = 2340 s。

确定性的提交，只要解题者在所用评分器上每个输入都在 60 s 内跑完，修复版给的分数就和原始版一样。在某个输入上用了 60–150 s 的提交，两版不可比，因为原始版让整份提交作废，修复版照常计分。在 CPU 少于 8 个的评分器上，一直搜到墙钟截止时间才停的解题者，在修复版下每个输入分到更多 CPU（4 个 CPU 时是 1 个 CPU，原来约 0.5 个），所以它在两个评分器下的分数不可比。和所有计时任务一样，接近时限的运行也可能因机器快慢而结果不同。参考点不变，所以 0–100 刻度（包括 ≈30.3、显示舍入后 ≈30.6 的上限）在两个版本中相同。

## 我们如何检查

- 我们在按摘要固定的原始评分器镜像里以 `--network none` 原样运行 `eval_cmd`，解法以只读方式挂载，由本仓库的测试框架评分。测试提交包括一份通用的有效提交、它的一次重复、随附的初始文件、一份带无意错误的提交，以及带时间预算的解题者。我们另在评分器镜像里用测试程序跑了 16 份手写输出，与参照程序的预测 0 处不一致。
- 作为独立参照，我们照题面文字写了一个模拟器，用精确的 `Fraction` 计分，支持两种规则模式（任务说明的规则和更严格的 CodeChef 规则）。与原始测试程序做差分测试，用了 20,000 个随机指令串和 2,000 份测试提交的输出（其中一半改了一个字符），结果全部一致。极小网格的精确最优值，来自 2x2、2x3 和 3x2 网格上两种规则下的 Dijkstra 最短路搜索。数据检查覆盖了全部 50 个评分输入（250 个子用例）和生成器种子 0..300,000。
- 在 Lean 4 形式化检查中，单用例下界是 `formal/lean/ebv/Ebv/WarehouseBound.lean` 里的定理 `EbvWarehouse.lower_bound`。Lean 内核在 Lean v4.34.1 和 Mathlib `d13f23b7` 下检验了它，没有 `sorry`，也没有 `native_decide`，还独立重新编译过。它只依赖 Lean 的标准公理 `[propext, Classical.choice, Quot.sound]`。`EbvWarehouse.score_bound` 给出单用例的分数下界。在 `Ebv/WarehouseData.lean` 中，`totalLB_eq` 和 `totalLB_gt` 给出 TOTAL 的下界，`displayed_gt_rank1` 处理显示舍入。这个定理并不空洞。模型接受一个 42 个字符的最优解（`opt23_accepted`），而去掉 −6(R+C−2) 项的更强下界已证明为假（`too_strong_bound_false`），暴力搜索找到的 248 个最优解中有 239 个违反那个更强的下界。证明没有用到"能否进入被占用格子"这一条件，所以在任务说明的规则和 CodeChef 规则下都成立。
- 我们把原始版与只改时限的修复版在 `--cpus 2` 下并排对照跑了三次，结果没有变化（`data/paired-repeatability.md`）。`--cpus 4` 和 `--cpus 8` 下的 CPU 份额运行（`evidence/runs/warehouse_forklift_routing-v2-cpu4-a` 到 `-d`，都是 `status: exit=0`）各跑了三次（`-rep2`、`-rep3`），OK/TLE/WA/RE 计数和总分都相同（`repairs/warehouse_forklift_routing-v2/paired/results.md` 的 Repeatability 一节）。

## 局限

- 修复版评分器从 cgroup（`cpu.max`）读取 CPU 配额。这一点只用 `docker run --cpus` 测过，没有在 Kubernetes pod（EdgeBench 排行榜设置用的后端）里测。
- 没有 cgroup 配额时，修复版评分器退回 `os.cpu_count()`，它数的是主机的全部 CPU，不是评分器实际能用的 CPU（`os.sched_getaffinity`）。如果只限制了 CPU 集合、没有配额（例如 `docker run --cpuset-cpus`），或者 pod 看不到自己的 `cpu.max`，它仍可能和原版一样，同时跑的用例比 CPU 多。改用亲和性计数需要再做一次并排对照运行，所以我们没有改。
- 上游评测框架为最终评分只等 900 s，可能收不到修复后的一次评分（实测 1,825.2 s）。请把单独的[最终等待评测框架叠加层](../repairs/harness-final-drain-v1/README.md)和本评分器修复包一起使用。它会等到历史记录进入终态，截止时间把排队考虑在内，收集不完整时明确报错。确定性的补丁源码测试已通过，经该叠加层的完整 Docker/Kubernetes 运行还没有验证。在经该叠加层物化的评测框架运行中，每个任务的最终收集都会改变，不只是 Warehouse。等待时间最长可达 `300 + n·(eval_timeout + 300)` s（一份未完成的 Warehouse 提交为 4,200 s），这段时间工作沙箱一直占着，详见其 README。只改镜像的修复解决不了这个主机端的边界问题。我们此前说"原本能计分的提交都能在 900 s 等待内完成"，这一说法没有得到证实，现予撤回。
- 没有运行任何 AI 模型或解题者。影响只在我们写的测试提交上演示过。
- 有效的测试提交是通用的，也比较弱（100 分制下 0.0 分）。我们没有写出有竞争力的解题者，所以没有测量在下限（原始分 712.5）和约 1000 原始分（对角线构造）之间实际能达到的最好分数。
- 带时间预算的测试提交用的是 `sleep`，说明时限确实按承诺对每个输入执行。CPU 争用是用每个输入做固定 80 s 或 140 s CPU 计算的单线程提交演示的。多线程的解题者和 3、5、6、7 个 CPU 的情形都没有测试。
- 4 个 CPU 时，修复版给每个输入 140 s 的 CPU 计算只留了约 9 s 余量（最慢的输入为 140.58 s）。
- 评分器 CPU 少于 3 个时，3600 s 的 `eval_timeout` 会比每个输入 150 s 的时限先起作用。2 个 CPU 时，25 轮 × 150 s = 3750 s，每个输入只能用约 144 s。配额向下取整，2.5 个 CPU 时同时跑 2 个输入。
- Lean 模型与测试程序的对应是人工逐行对照的，另有一个运行时差分测试支撑（294 个指令串上 0 处不一致），但这不是经内核检验的证明。用例的假设（排列、最后到达的不为 1）和 (R,C) 的提取是用 Python 检查的。0–100 刻度上的上限来自测试框架的浮点换算代码，不是来自 Lean。
- 参考点的来历不清楚。
- 评分器隔离不在本次发布的范围内（这是 EdgeBench 的设计选择）。影响按规则作答的解题者的发现已在上文报告。

## 复现

- 评分器镜像：`sha256:ac7fdf03…`。
- 主机上的检查：`evidence/scripts/warehouse_forklift_routing/`（`oracle_sim.py`、`diff_fuzz.py`、`authored_cases.py`、`data_and_bound.py`、`tiny_optimum.py`、`native/run_native.sh`、`harness_grade.py`；校验和见 `SHA256SUMS`）。
- Lean 下界：`evidence/formal/lean/ebv/Ebv/Warehouse{Bound,Check,Data}.lean`，用 `evidence/scripts/warehouse_forklift_routing/lean_bound/compile_capped.sh` 编译。精确总分：`lean_bound/recompute_total.py`。暴力搜索：`lean_bound/brute_force.py`。
- 并排对照运行：`repairs/warehouse_forklift_routing-v2/paired/run.sh`（实际运行版本：`evidence/runs/warehouse_forklift_routing-v2-paired-b/run.sh`）。CPU 份额运行：`repairs/warehouse_forklift_routing-v2/paired/run-cpu4.sh`（实际运行版本：`evidence/runs/warehouse_forklift_routing-v2-cpu4-a/run.sh` 到 `-d`）。
- 固定标识：评分器镜像 `seededge/edgebench.judge.warehouse_forklift_routing@sha256:ac7fdf03…`；`/tmp/eval_warehouse_manager.py` 的 sha256 为 `c5ff0c26…`；`tools/bin/tester` 的 sha256 为 `277f4841…`；50 个评分输入（拼接后）的 sha256 为 `04b8cd29…`；任务 JSON 的 sha256 为 `78002570…`。
- 支撑记录：`repairs/warehouse_forklift_routing-v2/`（存放修复版的文件夹：README、`repair.patch`、`source-lock.json`）、`evidence/reviews/warehouse_forklift_routing.md`、`evidence/reviews/warehouse_lower_bound_lean.md`。
