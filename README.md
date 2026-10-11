# EdgeBench Verified

We are checking whether EdgeBench's tasks, tests and data measure what they promise. The goal is a reviewed decision for every publicly available task: keep it, repair it, or exclude the original version for an evidenced reason.

**This is an unfinished, private audit. No task is certified for benchmark release.** The project is independent of the upstream authors.

- [Where we are now](AUDIT-STATUS.md): finished decisions, changes since the previous snapshot, and remaining work.
- [What we found](docs/FINDINGS.md): each confirmed problem, how we checked it, and what the result means.
- [Supporting evidence](docs/EVIDENCE-INDEX.md): recorded results and their sources.

We acquired 51 public tasks. Another 83 advertised tasks were unavailable. A partial test is useful evidence, but it does not finish a task review. The dated status page owns the current progress numbers; older evidence snapshots retain their original dates.

## How we work

Finish conclusions from evidence already collected. Run ready, independent task checks in parallel. If setup repeatedly fails, explain the blocker and move another task forward. Report new results and completed decisions first; keep internal run names and hashes in the supporting records.

The [working instructions](docs/AUDIT-WORKFLOW.md) explain Git branches, shared cloud accounting, local resource limits and how to avoid duplicate work. [Verification requirements](VERIFICATION.md) define what must be established before a task can be included in a release.

## What's in this repository

The original-format task definitions and harness are in `tasks/` and `sforge/`. Reviewed tools, selected evidence and audit skills are versioned here. Large images, private data, credentials and live cloud accounting stay outside Git. The [source manifest](docs/CONSOLIDATED-SOURCE-MANIFEST.json) identifies the copied execution-source snapshot; it is not a second live coordinator.

GitHub runs small checks with Python 3.12. They start no cloud workers or task containers:

```sh
python -m pip install -e . pytest
PYTHONPATH=tools python -m pytest tests/test_grading_contract.py tests/test_release_gates.py tests/test_cloud_dispatch_resources.py tests/test_cloud_policy.py tests/test_cloud_queue.py -q
```

The [shareable progress site](https://edgebench-audit-progress.alex-shengzhi.chatgpt.site) has its own update date and may lag this repository.

## Sources

The harness derives from [ByteDance Seed EdgeBench](https://github.com/ByteDance-Seed/EdgeBench) at `6e4e5f4aa087a9121aa09a6059e5484e5102c6ff`; its Apache-2.0 license is retained in `LICENSE`. Public definitions derive from the [Hugging Face release](https://huggingface.co/datasets/ByteDance-Seed/EdgeBench) at `6cc5a7f1b3288ce52484ad828177b8cc86b05b75`, with a separate license in `tasks/LICENSE`. These notices do not establish rights to redistribute every dataset or dependency inside the images.

[Rethlas, Lean and TLA+](docs/FORMAL-TOOLS.md) can help check suitable mathematical claims. A generated proof needs an actual tool check and a clear connection to the task being audited.
