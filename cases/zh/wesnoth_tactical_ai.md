# Wesnoth Tactical AI (`wesnoth_tactical_ai`)

**结论：** 保留（附说明）。<mark>在一台 8 vCPU 的主机上，完整的评分运行能在时间预算内跑完（80–172 s，预算 900 s）。但随附初始程序的招募设置在固定的游戏版本上已经失效，所以它得 0 分；对局结果也无法重复。</mark>

## 任务要求

The Battle for Wesnoth（韦诺之战）是一款回合制策略游戏。解题者编写 "a Lua AI for The Battle for Wesnoth 1.18 that wins turn-based multiplayer matches against the default AI"（一个能在回合制多人对局中战胜默认 AI 的 Lua AI）。Lua 是这款游戏里电脑玩家用的脚本语言。分数为 "**total_score = 80 x win_rate + 20 x avg_efficiency**, evaluated over 3 maps x N seeds (default 10) x N repeats (default 2)"（即由胜率和平均效率加权得出，在若干地图、种子和重复次数上评估）。任务说明还写道 "The baseline AI (default C++ CAs) typically scores 0-20."（基线 AI，即默认的 C++ 候选动作，通常得分落在这一区间。）默认的评分运行有 60 局对局，`eval_timeout` 为 900 s。类别：交互式游戏与模拟器。

## 我们检查了什么

对局的计分方式没有问题。有四点要说明：时限、失效的初始程序、无法复现的对局，以及一个可能误拒无害文件的文本扫描。

**1. 时间预算够用，但有一条任务没写的限制。** 用默认 AI 下完一整局约需 3 s。

- 随附的初始程序：完整的默认评分运行在 **80 s** 内完成，退出码 0，`TOTAL_SCORE 0`，`CASES_OK 0/60`，`TIMEOUT_COUNT 0`。
- 使用游戏自带 AI 的正确测试提交：在 **172 s** 内完成，退出码 0，60/60 局，`TIMEOUT_COUNT 0`，`TOTAL_SCORE 41`（18/60 胜）。每局墙钟时间：平均 2.86 s，中位数 2.79 s，最长 5.65 s。
- 余量：提交的 AI 每局大约能用到自带 AI 的 5 倍时间，即平均每局约 15 s，才会碰到 900 s。每局时限是 180 s，但 60 x 15 s = 900 s，所以计算量大的 Lua AI 可能超出总预算。任务没有说明这条限制。
- 一旦超过 900 s，丢掉的是所有对局的分，不只是后面几局：评分器要等 60 局全部下完才打印 `CASE` 行和 `TOTAL_SCORE`；测试框架超时杀掉评分器时，`TOTAL_SCORE` 不会打印，这份提交就没有分数（EdgeBench 的评分本身不看超时标志，`sforge/harness/grading.py:224-241`）。

**2. 随附的初始程序在 Wesnoth 1.18.5 上已失效。** 初始程序的全部三份对局日志（每张地图一份）都包含：

```
error ai/engine/cpp: side 1 : UNKNOWN candidate_action[ai_default_rca::aspect_recruitment_phase]
```

游戏自带的 1.18 宏用的是 `name=default_recruitment::recruitment`。所以初始程序的第 1 方从不招募单位，领袖最后被击溃。每张地图各运行一次原始的 `run_game`：

| 地图 | 墙钟时间 | `run_game` 返回值 | 对局输出中的标记 |
|---|---|---|---|
| Weldyn_Channel | 2.08 s | (False, 8, False) | `WINNER: 2`、`GAME_END_TURN: 8` |
| The_Freelands | 1.40 s | (False, 6, False) | `WINNER: 2`、`GAME_END_TURN: 6` |
| Fallenstar_Lake | 1.42 s | (False, 9, False) | `WINNER: 2`、`GAME_END_TURN: 9` |

任务说明里的 "typically scores 0-20" 从字面上看是满足的，因为分数是 0。问题出在初始程序，与计分无关：一个能正常工作的 AI，评分器给出了正确的分数（41）。

**3. 重复对局的结果无法复现。** 固定 `--rng-seed` 并不能固定两个 AI 对局的结果。在重复对（同一地图、同一种子，重复 0 对重复 1）里，自带 AI 的测试提交 **30 对中只有 1 对** 完全相同，随附的初始程序是 30 对中 6 对。所以第二次重复得到的是新样本，并非重复样本。

另外还看到：自带 AI 在 The_Freelands 上有两局打到了 50 回合上限，没有打印 `WINNER`，评分器把它们算作负局。

每次评分的波动有多大，只能估计，没有测量：假如 60 局互相独立、胜率为 p，胜率部分（80 x 胜率）的标准差就是 80 x √(p(1 − p)/60)。p = 0.3 时（自带 AI 对照赢了 18/60）约为 100 分制下的 4.7 分，p = 0.85 时约为 3.7 分，效率部分的波动还没算在内。

**4. 评分器的文本扫描可能误拒无害的文件。** 对局开始前，`scan_for_hacks()` 会在每个提交的 `.lua` 文件原文里搜 `wml_actions`、`game_events`、`os\.execute`、`io\.open` 和 `debug\.`，在每个 `.cfg` 文件里搜 `[kill]`、`[event]`、`[command]` 和 `wml_actions`。注释和更长名字中的片段也算匹配。只要匹配上一处，整份提交就是 0 分。任务说明把这些 API 列为禁用（"violation = score=0 and hack flag"，即违规则得零分并标记为作弊），但没说注释和子串也算。

- **例子。** 注释 `-- never use wesnoth.wml_actions here`、一个名为 `mydebug`、用法如 `mydebug.log` 的表，或者变量 `n_game_events_seen`，都会匹配上某个模式（用 Python 的 `re.search` 套用评分器的模式核对过）。这样的提交会得 0 分。我们没有实际给这样的提交评过分。

**随任务发布的说明。**

- 随附初始程序的招募候选动作在 Wesnoth 1.18.5 上无效，所以初始程序得 0 分。建议的修复是像自带宏那样用 `name=default_recruitment::recruitment`，这一修复没有测试过。
- 虽然有 `--rng-seed`，对局仍然无法复现。
- 60 局的总耗时必须在 900 s 以内，也就是平均每局约 15 s，虽然每局时限是 180 s。

## 影响有多大

- 失效的招募设置只影响原样提交初始程序、或在它基础上开发的解题者；初始程序得 0 分。
- 总时限只影响平均每局超过约 15 s 的 AI。
- 对局无法复现，每个解题者的分数都多了方差：按上面的二项分布估计，每次评分约为 100 分制下 ±4 到 ±5 分；这是估计值，没有测量。本任务有记录的智能体运行得分为 36.3–88.0 分（满分 100，见 `tasks/README.md`），所以这个波动正落在有实际意义的分数段上。该任务的选取规则（`score_first`）保留最佳提交，每次评分之间的波动因此可能把一次运行记下的最佳成绩抬高。
- 文本扫描只影响文件里（不论代码还是注释）提到了某个禁用名称的解题者，他们会得 0 分。

没有改代码，上述说明随任务一起发布。

## 我们如何检查

- **在按摘要固定的原始镜像中运行原始评分器。** 评分器镜像（Wesnoth 1.18.5）在一台不限 CPU 的 8 vCPU 主机上以 `--network none` 运行。对随附的初始程序，在每张地图上各跑一次未改动评分器的 `scan_for_hacks()`、`install_agent_ai()` 和原始的 `run_game(map, 0, 0)`，只给 `subprocess.run` 套了一层包装，用来记录对局输出和耗时。然后用默认参数、在 `timeout 900` 下运行一模一样的 `eval_cmd`（`python3 /tmp/eval_wesnoth.py`）。
- **正确的测试提交。** 第 1 方用 Wesnoth 自带的 `data/ai/ais/ai_default_rca.cfg`，只把 `id=` 改名为 `my_custom_ai`，它通过了评分器的作弊扫描。在 `timeout 900` 下用未改动的评分器跑完整的默认评分运行，`subprocess.run` 上加了计时包装。
- 这里用不上形式化模型。

## 局限

- 没有运行任何 AI 模型或求解器。影响只在随附的初始程序和自带 AI 的测试提交上演示过。
- 只用了一台不限 CPU 的 8 vCPU 主机。评分主机就算慢上几倍，也可能仍在 900 s 内跑完。
- 自带 AI 的测试提交是 Wesnoth 自己的 AI，不是哪个解题者的提交。每种配置只跑了一次完整的评分运行，所以 `TOTAL_SCORE` 的方差是二项分布估计，不是测量值。
- 文本扫描的误报来自阅读评分器源码、把它的模式套到样例字符串上；没有实际给这样的提交评过分。
- 把 Lua 文件装在子目录里可能出的问题，没有实际测试。

## 复现

- `evidence/runs/wesnoth_tactical_ai-native-timing/run.sh`（随附的初始程序，配合 `game1.py`）。
- `evidence/runs/wesnoth_tactical_ai-native-rca-control/run.sh`（自带 AI 的测试提交，配合 `timed_eval.py`）。
- 两者都需要一台能拉取固定镜像的 Docker 主机。
- 固定标识：评分器镜像 `seededge/edgebench.judge.wesnoth_tactical_ai@sha256:660e126eddcd…`；工作镜像 `seededge/edgebench.work.wesnoth_tactical_ai@sha256:4d9b1e6515b2…`；`eval_wesnoth.py` 的 sha256 为 `b1cbe456fc15…`；初始程序 `my_custom_ai.cfg` 为 `66e11740789a…`（两个镜像中是同一文件；它就是整份提交）。
- 支撑记录：`evidence/reviews/wesnoth_tactical_ai-native.md`。
