# Trinity (`trinity_text_adventure`)

**结论：** 保留（附说明）。<mark>分数就是游戏自己给出的分数，可以重复，没有发现评分缺陷。说明有两点：计分取最终分数，不取峰值；会话有一些限制，任务文本没有写。</mark>

## 任务要求

任务文本写道："Play the interactive fiction game *Trinity* by sending commands via an HTTP API and maximize your score."（通过 HTTP API 发送命令来玩互动小说游戏 *Trinity*，并使你的分数最大化。）*Trinity* 是一款文字冒险游戏。任务文本没有规定时间、步数上限或游戏局数。类别：交互式游戏与模拟器。

## 我们检查了什么

没有发现会改变分数的缺陷。检查了以下部分：

- **分数怎么来。** 每一步都从 Z-machine（运行该游戏的虚拟机）的内存里读 `env.get_score()`。会话有四种结束方式：游戏结束、显式关闭、空闲后关闭（回收），或被更新的会话挤掉（驱逐）。不论哪种，保存的都是该会话的**最终**分数。一次运行的分数取所有会话最终分数里最高的那个。分数刻度是线性的，从 0（起始分数）到 100，上限就是 Jericho 游戏库给这款游戏设的 `max_score`（`trinity.c:71-73`）。任务没有随附初始解法。例子：在主机上回放 610 条命令的通关流程，得 100/100，即 100 分制下的 100 分。
- **可重复性。** 不带种子的 `FrotzEnv(rom)` 会用库的默认种子 0，所以游戏的随机数与时间无关。我们跑了两个 Trinity 会话：一个 25 条命令的部分会话，一个 610 条命令的完整通关（三款 Jericho 游戏共六个会话）。两者在共同的 25 条命令前缀上分数相同（`prefix_numeric_equal: true`）。命令序列一定，游戏结果就完全确定。

说明（仅涉及文档，不改变分数）：

- **取最终分数，不取峰值。** 保存的是最终分数，但 API 还会返回 `peak_score`，可能让智能体误会。只有游戏中会丢分时，这一点才有影响。三条随附的轨迹（Anchorhead、Trinity、Tryst）里，最终分数都等于峰值。
- **没写出来的会话限制。** 测试框架有几条任务文本没提的限制：每一步 HTTP 超时 10 s；每次运行最多同时开 3 个会话（最旧的会被驱逐）；空闲 600 到 660 s 后关闭（空闲检查每 60 s 一次，`judge_server.py:156,159`）。关闭和驱逐都会保存当前分数，所以分不会丢。但智能体如果在游戏中途停下超过 10 分钟，进行中的游戏就没了，得重新回放。回放花不了多少时间：610 条命令的 Trinity 通关流程，HTTP 回放记录耗时 29.3 s（`elapsed_seconds: 29.325236`）。

**随任务发布的说明。**

- 分数是最佳的已完成或已关闭会话的最终游戏内分数，以游戏的 max_score（100）为满分。
- 会话在空闲 600 到 660 s 后关闭；同时至多运行 3 个会话。

## 影响有多大

两条说明观察到的最大分数影响都是 0。只有依赖 `peak_score` 的智能体，或在游戏中途停下超过 10 分钟的智能体，才可能受影响。

任务不改，上述说明随任务一起发布。

## 我们如何检查

- **测试框架源码。** 在固定的测试框架里读了这几部分：每一步读分数（`game_server_app.py`）、保存会话和执行限制（`judge_server.py`）、在 N 个会话里保留最好的那个（`selection.py`）、有效性检查（`grading.py`）以及分数刻度（`score_rescale.py`）。这些副本与按哈希固定的副本逐字节一致。
- **游戏引擎源码。** 分数的来源、`max_score` 和默认种子，都可以在公开的 Jericho 3.3.1 源码包（sdist）里查到。
- **在主机上运行。** 两个 Trinity 会话（一个 25 条命令的部分会话，一个 610 条命令的完整通关），属于在 Anchorhead、Trinity 和 Tryst 上跑的六个会话。它们跑在一个本地构建的镜像上（`built_image_id sha256:a197e54f…`）；没有记下公开评分器镜像的摘要。
- 这里用不上形式化模型。

## 局限

- 没有运行任何 AI 模型或解题者。影响只在通关流程会话上演示过。
- 没有在固定的评分器镜像里跑过游戏。
- Jericho 的行为依据的是已发布的 3.3.1 源码，没有对已安装的文件取哈希核对。
- 最终分数与峰值分数的差别，没有在会丢分的轨迹上测试。
- 可重复性只在 25 条命令的共同前缀上做了比较。

## 复现

- 审查和固定哈希：`evidence/reviews/_game-tasks-correctness.md`，第 1-3 节。
- 会话记录（保存在 Git 标签 `earlier-audit-final` 下）：`git show earlier-audit-final:evidence/selected/three-adventure-native-release-acceptance.json`（六个会话，Trinity 部分会话 25 条命令得 7 分，完整的 610 条命令得 100 分，前缀一致）和 `git show earlier-audit-final:evidence/selected/trinity-tryst-terminal-acceptance.json`（Trinity HTTP 回放，29.3 s）。
- 固定的测试框架源码：`sforge/harness/judge_server.py`、`sforge/harness/game_server_app.py`、`sforge/harness/selection.py`、`sforge/harness/score_rescale.py`。
- 固定标识：任务 JSON 的 sha256 为 `7364a012…c0ee`；`judge_server.py` 的 sha256 为 `77410d7e…`，`game_server_app.py` 的 sha256 为 `379572e9…`，`score_rescale.py` 的 sha256 为 `98feb630…`；Jericho 3.3.1 的 `jericho.py` 的 sha256 为 `94f2e745…`。
