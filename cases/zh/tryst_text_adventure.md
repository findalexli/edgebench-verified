# Tryst of Fate (`tryst_text_adventure`)

**结论：** 保留（附说明）。<mark>分数是游戏自身可重复的分数，没有发现评分问题；说明指出，计入的是一个会话的最终分数而不是峰值分数，并列出了任务说明没有写明的会话限制。</mark>

## 任务要求

"Play the interactive fiction game *Tryst of Fate* by sending commands via an HTTP API and maximize your score."（通过 HTTP API 发送命令来玩互动小说游戏 *Tryst of Fate*，并使你的分数最大化。）任务说明没有规定游戏时长、步数上限或游戏局数。类别：交互式游戏与模拟器。

## 我们检查了什么

没有发现会改变分数的问题。检查了以下内容：

- **分数如何定义。** 每一步都从 Z-machine（运行该游戏的虚拟机）的内存中读取 `env.get_score()`。会话可能因以下原因结束：游戏结束、被显式关闭、空闲后被关闭，或被更新的会话挤掉。在每种情况下，保存的分数都是该会话的**最终**分数。一次运行的分数是所有会话最终分数中的最高者。分数刻度是从 0（起始分数）到 350 的线性刻度，该上限等于 Jericho 为该游戏设定的 `max_score`（`tryst.c:97`）。Jericho 是运行该游戏的库。任务没有随附基线解法。例子：在主机上回放一次完整的通关流程，得到 350/350，换算为 100 分制下的 100 分。
- **可重复性。** 不带种子的 `FrotzEnv(rom)` 会退回到库的默认种子，即 0，因此游戏的随机数来源不依赖于时间。一次 25 条命令的部分回放与一次完整通关回放的前 25 步一致，而两次独立的完整通关回放（518 条命令）都得到 350/350。给定命令序列，游戏是确定性的。

说明（仅涉及文档，不改变分数）：

- **最终分数，而非峰值分数。** 保存的是最终分数，而 API 还会返回 `peak_score`，这可能误导智能体。只有当游戏过程中可能失分时，这一点才有影响。在全部三份随附的游戏记录（Anchorhead、Trinity、Tryst）中，最终分数都等于峰值。
- **任务说明没有写明的会话限制。** 测试框架强制执行一些任务说明没有提到的限制：每一步 10 s 的 HTTP 超时，每次运行同时至多 3 个会话（最旧的会被挤掉），以及空闲 600 到 660 s 后关闭会话（空闲检查每 60 s 运行一次，`judge_server.py:156,159`）。无论因哪种原因关闭会话，都会在该会话的游戏容器被移除后保存其当前分数，因此不会丢分。如果移除失败，该会话会被保留，并在下一次空闲检查时重试，只有在移除成功后才保存其分数（`judge_server.py:226-239`）。在游戏中途暂停超过 10 分钟的智能体会失去正在进行的游戏，必须重新回放。回放代价很小：完整通关流程（518 条命令）的 HTTP 回放记录耗时 32 s。

**随任务发布的说明。**

- 分数是最佳的已完成或已关闭会话的最终游戏内分数，以游戏的 max_score（350）为满分。
- 会话在空闲 600 到 660 s 后被回收；同时至多运行 3 个会话。

任务本身不作改动；上述说明随任务一起发布。

## 影响有多大

对两条说明而言，观察到的最大分数变化都是 0。只有依赖 `peak_score` 的智能体，或在游戏中途暂停超过 10 分钟的智能体，才可能受影响。

一次第三方的 Claude Opus 5.5 运行（4 小时，以 `adafadaq/edgebench-opus-5-5-xhigh-rollouts` 发布在 Hugging Face 上）在本仓库中有 480 份会话日志。全部 477 个已保存的会话结果中，最终分数都等于峰值分数；最好的是 215/350（game-81）。有三个会话（game-95、game-465、game-479）根据其步骤日志达到了 215，但没有保存的结果；这次运行的最佳分数 215 不受影响。

## 我们如何检查

- **测试框架源码。** 我们在固定的测试框架中阅读了每一步的分数读取（`game_server_app.py`）、会话保存和限制（`judge_server.py`）、保留最佳提交的规则（`selection.py`）、有效性检查（`grading.py`）以及分数换算（`score_rescale.py`）。这些副本与按哈希固定的副本逐字节一致。
- **游戏引擎源码。** 公开的 Jericho 3.3.1 源码包给出了分数的来源、`max_score` 和默认种子。
- **在主机上运行。** 六个会话在主机上通过本仓库所带的 EdgeBench 测试框架副本运行（使用 Docker 后端的 `JudgeState`；其评分和选取文件当时是早先审计修改过的版本；这里报告的会话分数来自游戏服务器，与它们无关），游戏容器由原始游戏文件构建（构建的镜像 id 为 `sha256:a197e54f…`）；没有记录公开评分器镜像的摘要。对 Anchorhead、Trinity 和 Tryst，各有一次完整通关回放和一次 25 条命令的部分回放，每次部分回放的分数都与完整回放的前 25 步一致。另外，一次通过游戏容器 HTTP 端点进行的完整通关回放在 32 s 内得到 350/350。
- 这里不适用形式化模型。

## 局限

- 我们没有运行任何 AI 模型或解题者。影响在通关流程会话上展示；上文的第三方运行只读取了其记录，没有回放。
- 没有在按摘要固定的公开评分器镜像中运行任何游戏。游戏容器由原始游戏文件构建（镜像 id `sha256:a197e54f…`）。
- Jericho 的行为依据的是上游 3.3.1 源码，而不是对已安装的字节取哈希。
- 最终分数与峰值分数的对比没有在会失分的游戏中测试。

## 复现

- 审查和固定哈希：`evidence/reviews/_game-tasks-correctness.md`，第 1-3 节。
- 会话记录：`git show earlier-audit-final:evidence/selected/three-adventure-native-release-acceptance.json` 和 `git show earlier-audit-final:evidence/selected/trinity-tryst-terminal-acceptance.json`。
- 第三方运行：`evidence/runs/opus55-rollouts-meta/result/meta/opus-16x4h-1009-0036-w3/tryst_text_adventure/`（`final_result.json`、`submissions/game-*/game_result.json` 和 `steps.jsonl`）。
- 固定的测试框架源码：`sforge/harness/judge_server.py`、`sforge/harness/game_server_app.py`、`sforge/harness/selection.py`、`sforge/harness/score_rescale.py`。
- 固定标识：任务 JSON 的 sha256 为 `a6e4815a…1b5f`；`judge_server.py` 的 sha256 为 `77410d7e…`，`game_server_app.py` 的 sha256 为 `379572e9…`，`score_rescale.py` 的 sha256 为 `98feb630…`；Jericho 3.3.1 的 `jericho.py` 的 sha256 为 `94f2e745…`。
