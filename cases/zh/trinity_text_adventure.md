# Trinity (`trinity_text_adventure`)

**结论：** 保留（附说明）。<mark>分数是游戏自身可重复的分数，没有发现评分缺陷；说明涉及两点：计分使用最终分数而非峰值分数，以及任务文本没有披露的会话限制。</mark>

## 任务要求

任务文本写道："Play the interactive fiction game *Trinity* by sending commands via an HTTP API and maximize your score."（通过 HTTP API 发送命令来玩互动小说游戏 *Trinity*，并使你的分数最大化。）*Trinity* 是一款文字冒险游戏。任务文本没有规定时间范围、步数上限或游戏局数。类别：交互式游戏与模拟器。

## 我们检查了什么

没有发现会改变分数的缺陷。检查了以下部分：

- **分数如何定义。** 每一步都从 Z-machine（运行该游戏的虚拟机）的内存中读取 `env.get_score()`。会话有四种结束方式：游戏结束、被显式关闭、空闲后被关闭（回收），或被更新的会话挤掉（驱逐）。在每种情况下，保存的分数都是该会话的**最终**分数。一次运行的分数是所有会话最终分数中的最高者。分数刻度是线性的，从 0（起始分数）到 100，后者等于 Jericho 游戏库为该游戏设定的 `max_score`（`trinity.c:71-73`）。没有随附的初始解法。例子：在主机上回放 610 条命令的通关流程，得到 100/100，即 100 分制下的 100 分。
- **可重复性。** 不带种子的 `FrotzEnv(rom)` 会退回到库的默认种子，即 0。因此游戏的随机数来源不依赖于时间。我们运行了两个 Trinity 会话：一个 25 条命令的部分会话，以及 610 条命令的完整通关流程（三款 Jericho 游戏共六个会话）。它们在共同的 25 条命令前缀上分数相同（`prefix_numeric_equal: true`）。给定命令序列，游戏是完全确定性的。

说明（仅涉及文档，不改变分数）：

- **最终分数，而非峰值分数。** 保存的是最终分数，而 API 还会返回 `peak_score`，这可能误导智能体。只有当游戏过程中可能失分时，这一点才有影响。在全部三条随附的轨迹（Anchorhead、Trinity、Tryst）中，最终分数都等于峰值。
- **未披露的会话限制。** 测试框架强制执行一些任务文本没有提到的限制：每一步 10 s 的 HTTP 超时，每次运行同时至多 3 个会话（最旧的会被驱逐），以及空闲 600 到 660 s 后关闭（空闲检查每 60 s 运行一次，`judge_server.py:156,159`）。关闭和驱逐都会保存当前分数，因此不会丢分。但是，在游戏中途暂停超过 10 分钟的智能体会失去正在进行的游戏，必须重新回放。回放代价很小：610 条命令的 Trinity 通关流程的 HTTP 回放记录耗时 29.3 s（`elapsed_seconds: 29.325236`）。

**随任务发布的说明。**

- 分数是最佳的已完成或已关闭会话的最终游戏内分数，以游戏的 max_score（100）为满分。
- 会话在空闲 600 到 660 s 后关闭；同时至多运行 3 个会话。

## 影响有多大

对两条说明而言，观察到的最大分数影响都是 0。只有依赖 `peak_score` 的智能体，或在游戏中途暂停超过 10 分钟的智能体，才可能受影响。

不作改动；上述说明随任务一起发布。

## 我们如何检查

- **测试框架源码。** 从固定的测试框架中阅读了以下部分：每一步读取分数（`game_server_app.py`）、保存会话和强制执行限制（`judge_server.py`）、保留 N 个会话中的最佳者（`selection.py`）、有效性检查（`grading.py`）以及分数刻度（`score_rescale.py`）。这些副本与按哈希固定的副本逐字节一致。
- **游戏引擎源码。** 公开的 Jericho 3.3.1 源码包（sdist）给出了分数的来源、`max_score` 和默认种子。
- **在主机上运行。** 两个 Trinity 会话（一个 25 条命令的部分会话，一个 610 条命令的完整通关流程），属于 Anchorhead、Trinity 和 Tryst 上六个会话的一部分。它们在一个本地构建的镜像上运行（`built_image_id sha256:a197e54f…`）；没有记录公开评分器镜像的摘要。
- 这里不适用形式化模型。

## 局限

- 没有运行任何 AI 模型或解题者。影响只在通关流程会话上展示。
- 没有在固定的评分器镜像中运行任何游戏。
- Jericho 的行为依据的是已发布的 3.3.1 源码，而不是对已安装文件取哈希。
- 最终分数与峰值分数的差异没有在会失分的轨迹中测试。
- 可重复性只在 25 条命令的共同前缀上做了比较。

## 复现

- 审查和固定哈希：`evidence/reviews/_game-tasks-correctness.md`，第 1-3 节。
- 会话记录（保存在 Git 标签 `earlier-audit-final` 下）：`git show earlier-audit-final:evidence/selected/three-adventure-native-release-acceptance.json`（六个会话，Trinity 部分会话 25 条命令得 7 分，完整的 610 条命令得 100 分，前缀一致）和 `git show earlier-audit-final:evidence/selected/trinity-tryst-terminal-acceptance.json`（Trinity HTTP 回放，29.3 s）。
- 固定的测试框架源码：`sforge/harness/judge_server.py`、`sforge/harness/game_server_app.py`、`sforge/harness/selection.py`、`sforge/harness/score_rescale.py`。
- 固定标识：任务 JSON 的 sha256 为 `7364a012…c0ee`；`judge_server.py` 的 sha256 为 `77410d7e…`，`game_server_app.py` 的 sha256 为 `379572e9…`，`score_rescale.py` 的 sha256 为 `98feb630…`；Jericho 3.3.1 的 `jericho.py` 的 sha256 为 `94f2e745…`。
