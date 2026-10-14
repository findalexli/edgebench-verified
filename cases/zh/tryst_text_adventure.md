# Tryst of Fate (`tryst_text_adventure`)

**结论：** 保留（附说明）。<mark>分数就是游戏自己给出的分数，可以重复，没有发现评分问题。说明指出，计入的是会话的最终分数，不是峰值；另外列出了任务说明没写的会话限制。</mark>

## 任务要求

"Play the interactive fiction game *Tryst of Fate* by sending commands via an HTTP API and maximize your score."（通过 HTTP API 发送命令来玩互动小说游戏 *Tryst of Fate*，并使你的分数最大化。）任务说明没有规定游戏时长、步数上限或游戏局数。类别：交互式游戏与模拟器。

## 我们检查了什么

我们没有发现会改变分数的问题，检查过的内容如下。

- 每一步都从 Z-machine（运行该游戏的虚拟机）的内存里读 `env.get_score()`。会话结束有几种情况，即游戏结束、显式关闭、空闲后关闭，或被更新的会话挤掉。不论哪种，保存的都是该会话的最终分数。一次运行的分数取所有会话最终分数里最高的那个。分数刻度从 0（起始分数）到 350，是线性的，上限就是 Jericho 给这款游戏设的 `max_score`（`tryst.c:97`）。Jericho 是运行该游戏的库。任务没有随附基线解法。在主机上回放一次完整通关，得 350/350，换算成 100 分制是 100 分。
- 不带种子的 `FrotzEnv(rom)` 会用库的默认种子 0，所以游戏的随机数与时间无关。一次 25 条命令的部分回放，与一次完整通关回放的前 25 步一致。两次独立的完整通关回放（518 条命令）都得 350/350。命令序列一定，游戏结果就是确定的。

下面两点说明只涉及文档，不改变分数。

- 保存的是最终分数，不是峰值，而 API 还会返回 `peak_score`，可能让智能体误会。只有游戏中会丢分时，这一点才有影响。三份随附的游戏记录（Anchorhead、Trinity、Tryst）里，最终分数都等于峰值。
- 测试框架有几条任务说明没提的会话限制。每一步 HTTP 超时 10 s，每次运行最多同时开 3 个会话（新会话会挤掉最旧的），空闲 600 到 660 s 后关闭会话（空闲检查每 60 s 一次，`judge_server.py:156,159`）。不论因为什么关闭会话，都要等该会话的游戏容器移除之后再保存当前分数，所以分不会丢。容器移除失败的话，会话会留着，下一次空闲检查时重试，移除成功后才保存分数（`judge_server.py:226-239`）。智能体如果在游戏中途停下超过 10 分钟，进行中的游戏就没了，得重新回放。回放花不了多少时间，完整通关流程（518 条命令）的 HTTP 回放记录耗时 32 s。

任务随附了这条说明。

- 分数是最佳的已完成或已关闭会话的最终游戏内分数，以游戏的 max_score（350）为满分。
- 会话在空闲 600 到 660 s 后回收，同时至多运行 3 个会话。

任务本身不改，上述说明随任务一起发布。

## 影响有多大

两条说明观察到的最大分数变化都是 0。只有依赖 `peak_score` 的智能体，或在游戏中途停下超过 10 分钟的智能体，才可能受影响。

第三方有一次 Claude Opus 5.5 运行（4 小时，以 `adafadaq/edgebench-opus-5-5-xhigh-rollouts` 发布在 Hugging Face 上），本仓库里存有它的 480 份会话日志。477 个已保存的会话结果里，最终分数全都等于峰值分数，最好的是 215/350（game-81）。另有三个会话（game-95、game-465、game-479）按步骤日志也到了 215，但没有保存结果。这次运行的最佳分数 215 不受影响。

## 我们如何检查

- 我们在固定的测试框架里读了每一步的分数读取（`game_server_app.py`）、会话保存和限制（`judge_server.py`）、保留最佳提交的规则（`selection.py`）、有效性检查（`grading.py`）以及分数换算（`score_rescale.py`）。这些副本与按哈希固定的副本逐字节一致。
- 分数的来源、`max_score` 和默认种子，都可以在公开的 Jericho 3.3.1 源码包里查到。
- 六个会话用本仓库自带的 EdgeBench 测试框架副本在主机上运行（Docker 后端的 `JudgeState`；当时其评分和选取文件是早先审计改过的版本，但这里报告的会话分数来自游戏服务器，与这些文件无关）。游戏容器用原始游戏文件构建（构建的镜像 id 为 `sha256:a197e54f…`），我们没有记下公开评分器镜像的摘要。Anchorhead、Trinity 和 Tryst 各做了一次完整通关回放和一次 25 条命令的部分回放，每次部分回放的分数都与完整回放的前 25 步一致。另外，经游戏容器 HTTP 端点做的一次完整通关回放，32 s 内得到 350/350。
- 这里用不上形式化模型。

## 局限

- 我们没有运行任何 AI 模型或解题者。影响只在通关流程会话上演示过。上文的第三方运行我们只读了记录，没有回放。
- 我们没有在按摘要固定的公开评分器镜像里跑过游戏。游戏容器用原始游戏文件构建（镜像 id `sha256:a197e54f…`）。
- Jericho 的行为依据的是上游 3.3.1 源码，我们没有对已安装的字节取哈希核对。
- 最终分数与峰值分数的对比，没有在会丢分的游戏上测试过。

## 复现

- 审查和固定哈希：`evidence/reviews/_game-tasks-correctness.md`，第 1-3 节。
- 会话记录：`git show earlier-audit-final:evidence/selected/three-adventure-native-release-acceptance.json` 和 `git show earlier-audit-final:evidence/selected/trinity-tryst-terminal-acceptance.json`。
- 第三方运行：`evidence/runs/opus55-rollouts-meta/result/meta/opus-16x4h-1009-0036-w3/tryst_text_adventure/`（`final_result.json`、`submissions/game-*/game_result.json` 和 `steps.jsonl`）。
- 固定的测试框架源码：`sforge/harness/judge_server.py`、`sforge/harness/game_server_app.py`、`sforge/harness/selection.py`、`sforge/harness/score_rescale.py`。
- 固定标识：任务 JSON 的 sha256 为 `a6e4815a…1b5f`；`judge_server.py` 的 sha256 为 `77410d7e…`，`game_server_app.py` 的 sha256 为 `379572e9…`，`score_rescale.py` 的 sha256 为 `98feb630…`；Jericho 3.3.1 的 `jericho.py` 的 sha256 为 `94f2e745…`。
