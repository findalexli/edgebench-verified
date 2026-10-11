# EdgeBench Verified — private working audit

An independent audit of the public EdgeBench release, with versioned repairs and evidence-backed conclusions. **No task is certified.** This project is not affiliated with or endorsed by the upstream authors.

The acquired scope contains **51 public tasks**. There are accepted partial component or data observations for **37 tasks**, **12 closed scoped finding decisions**, **two reviewed exact-version exclusions**, and **49 pending final dispositions**. The other **83 advertised tasks are unavailable**. Finding closure, tested repairs and task certification are separate measures. See [current status](AUDIT-STATUS.md), [the evidence index](docs/EVIDENCE-INDEX.md) and [verification requirements](VERIFICATION.md).

## Repository and evidence

This private repository consolidates the harness, public task definitions, Order/ANN/Equivalence branches, selected source and evidence, contract checks, and reusable audit skills. The complete local audit archive, acquired private data, cloud ownership ledger, credentials and image caches remain outside Git. Selected evidence has an explicit provenance manifest; copying a record does not constitute another independent reproduction.

- `sforge/` and `tasks/`: harness and public definitions in the original format.
- `evidence/selected/`: scoped conclusions and task coverage, with source hashes.
- `tools/` and `tests/`: selected execution, accounting and contract checks.
- `.agents/skills/`: E2B execution and EdgeBench evidence-audit guidance.
- [Audit workflow](docs/AUDIT-WORKFLOW.md): canonical coordination, worktrees and useful experiments.
- [Consolidated source manifest](docs/CONSOLIDATED-SOURCE-MANIFEST.json): exact source-copy identities.

## Lightweight checks

```sh
python -m pip install -e . pytest
PYTHONPATH=tools python -m pytest tests/test_grading_contract.py tests/test_release_gates.py tests/test_cloud_dispatch_resources.py tests/test_cloud_policy.py tests/test_cloud_queue.py -q
```

CI uses Python 3.12 and runs these provider-free contract checks. It starts no native containers, cloud workers or model runs. The optional E2B dependency is pinned to the reviewed coordinator SDK; task interpreters remain separate. The incomplete release registry is expected to reject benchmark release.

## Current execution

Use isolated worktrees for concurrent source edits and **one canonical cloud queue, ownership registry and coordinator**. Read current accepted evidence and exact job terminals before preparing another run. Preserve failed hypotheses and run only unresolved work. The resumed window ends **October 12, 2026 at 05:52:16 UTC**. The user removed the compute ceiling and reserve; useful cloud concurrency up to 50 remains subject to local responsiveness, staging limits and existing holds.

The [public progress report](https://edgebench-audit-progress.alex-shengzhi.chatgpt.site) is separately authorized and can lag this repository's snapshot. This private consolidation does not publish or certify the benchmark.

## Sources and attribution

The harness derives from [ByteDance Seed EdgeBench](https://github.com/ByteDance-Seed/EdgeBench) at `6e4e5f4aa087a9121aa09a6059e5484e5102c6ff`; its Apache-2.0 license is retained in `LICENSE`. Public definitions derive from the [Hugging Face release](https://huggingface.co/datasets/ByteDance-Seed/EdgeBench) at `6cc5a7f1b3288ce52484ad828177b8cc86b05b75`; the separate license is retained in `tasks/LICENSE`. These notices do not clear every in-image dataset or dependency for redistribution.

[Rethlas and the formal-checking workflow](docs/FORMAL-TOOLS.md) can support selected mathematical claims. Generated proofs require actual independent Lean or TLA+ checks and correspondence with the audited implementation.
