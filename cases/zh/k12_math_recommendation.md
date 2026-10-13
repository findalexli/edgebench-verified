# K-12 Math Recommendation (`k12_math_recommendation`)

**结论：** 保留（附说明）。<mark>原始评分器给两个随附参考解都打出了有效的正分，但随附的示例报告已经过时，而且评分器在严格的内存限制下会失败。</mark>

## 任务要求

解题者要构建一个为中小学生（K-12 年级）推荐数学学习内容的系统。任务文本指向工作区中的一份说明文件："Read the complete task instructions in `/home/workspace/task_instruction.md`, and complete the task according to those requirements."（阅读完整的任务说明，并按其中的要求完成任务。）分数来自 `cd /home/workspace && python3 scoring/score.py`。它报告一个 `TOTAL_SCORE`，由 100 个场景上的五项加权指标（M1-M5）构成。类别：专业知识工作。

## 我们检查了什么

没有发现评分缺陷。评分器在两个随附参考解上都能正常工作：

| 测试提交 | 资源限制 | 结果 | total_score（报告的分数；任务没有 0–100 分数刻度） | M1 / M2 / M3 / M4 / M5 | 容器的峰值内存（cgroup memory.peak） | 内存不足事件 |
|---|---|---|---|---|---|---|
| stage2_advanced | 6 GiB、4 CPU、900 s | 有效，`TOTAL_SCORE 24.699` | **24.699** | 9.81 / 39.75 / 14.93 / 96.6 / 100 | 544,985,088 B（≈520 MiB） | 0 |
| stage1_baseline | 6 GiB、4 CPU、900 s | 有效，`TOTAL_SCORE 17.598` | **17.598** | 10.86 / 25.79 / 3.69 / 98.8 / 100 | 561,098,752 B（≈535 MiB） | 0 |
| stage2_advanced | 1 GiB、1 CPU、`prlimit --as=536870912 --cpu=120:120`、178 s | `OpenBLAS blas_thread_init: pthread_create failed for thread 7 of 8`，随后在导入 scipy/sklearn 时出现 `KeyboardInterrupt`。evaluate.py rc=-2；score.py 打印 `SCORER_INFRA_ERROR missing parseable score; rc=-2`、`TOTAL_SCORE 0` | 0（基础设施错误） | 无 | 108,732,416 B | 0 |

- 100 个场景中的 100 个全部匹配。权重为 M1 .35、M2 .30、M3 .30、M4 .04、M5 .01。顺序（stage2 24.7 > stage1 17.6）与作者对两个阶段的描述一致。每次运行从开始到结束约需 8 s。

随任务发布两项说明。

**随附报告已过时。** 随附的 `evaluation_report.json` 文件报告的是 45.292（stage1）和 50.4（stage2）。当前评分器对同样的参考解给出 17.6 和 24.7。差距的大部分在 M1：随附报告中为 44.3/43.6，现在为 10.9/9.8。随附报告看起来来自一个更早、更宽松的评分器。拿这些数字做对比的读者会被误导。

**内存限制。** 在 512 MiB 的地址空间限制下、可见 8 个核时，OpenBLAS 数学库无法创建其线程（每个核一个）。评分器随后在导入 numpy/scipy 时崩溃，此时尚未进行任何推理或评分（上表第三行）。在合理的限制下，整个容器（包括页缓存）的峰值内存约为 520 到 535 MiB。评分器所需的地址空间没有测量。

## 影响有多大

- 过时的报告：只涉及文档；不改变任何分数。
- 内存限制：只影响在严格地址空间限制下运行的评分器。在那种情况下，评分器对每份提交都报告 `TOTAL_SCORE 0` 并附带基础设施错误。

不做任何修改；上述说明随任务一起发布。

## 我们如何检查

- **原始公开镜像中的原始评分器，按摘要固定**（按摘要拉取，镜像 ID 已核实）。原样的 `eval_cmd` 在一台 8 vCPU、7.9 GB 的主机上运行。每个测试提交都在一个新的 `docker run --rm --network none` 容器中运行。
- **正确的测试提交。** 两个随附参考解（`scoring/reference_implementation/<stage>/`，即 `train.py`、`infer.py`、`requirements.txt`、`README.md` 和 `models/`）复制到 `/home/workspace` 后评分。
- **内存。** 从 cgroup v2 的 `memory.peak` 和 `memory.events` 读取，并每隔 1 s 采样一次 `memory.current`。

## 局限

- 没有运行任何 AI 模型或解题者。影响只在随附参考解和一次严格限制下的运行上展示。
- 每个测试提交只运行了一次。给定 `infer` 的输出，评分是确定性的。
- 内存数字是包含页缓存的 cgroup 总量，而不是每个进程的内存（RSS）。
- 没有测试其他严格限制的设置（其他核数或包装方式）下的行为。没有测试接近 512 MiB 的容器内存（cgroup）限制；失败的那次运行用的是地址空间限制。
- 本任务已发布的排行榜平均分（Opus 4.8 为 44.3，GPT-5.5 为 44.0，`evidence/impact/leaderboard_12h.json`）远高于作者的高级参考解在该评分器下的 24.7 分。这一差距从何而来，没有考察。

## 复现

- 评分器镜像摘要：`sha256:6489d4ea0e48…`。
- `evidence/runs/k12_math_recommendation-positive/run.sh`。它需要一台能拉取固定镜像的 Docker 主机。输出在 `result/out/<arm>/`。
- 严格限制的那一组（`stage2_audit_envelope`，`prlimit --as=536870912 --cpu=120:120`）在同一个 `run.sh` 中。
- `evidence/scripts/k12_math_recommendation/measure_evaluate.sh` 是一个更早的测量脚本。它需要没有发布的桩库，并使用旧的目录名，因此按已发布的形式无法运行。
- 审查记录：`evidence/reviews/k12_math_recommendation-native.md`。
