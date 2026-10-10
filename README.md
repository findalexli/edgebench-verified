# EdgeBench Verified — private working audit

An independent audit and repair of the public EdgeBench release. **No task is certified.** This project is not affiliated with or endorsed by the upstream authors.

The aim is to retain, repair or exclude tasks using reproducible evidence while preserving the original SForge task format. The acquired scope contains 51 public tasks; 83 other advertised tasks remain unavailable. Current decisions are two exact-version exclusions and 49 pending. See [audit status](AUDIT-STATUS.md) and [verification requirements](VERIFICATION.md).

## Repository and evidence

This initial private repository contains the harness, public task definitions, selected contract tests and the fail-closed release checker. The complete local audit archive, private acquired judge/data contents, cloud ownership ledger, credentials and image caches are deliberately outside the initial commit. Selected compact evidence and versioned repairs will be added through focused review branches.

- `sforge/`: acquired harness and existing audited changes.
- `tasks/`: public definitions in upstream format; presence does not imply inclusion.
- `tests/`: selected grading and synthetic evidence-integrity regressions.
- `tools/check_release.py`: release-evidence integrity checker; passing would still require scientific review.
- `AGENTS.md`: current execution authority, resource limits and preserved holds.

## Lightweight checks

```sh
python -m pip install -e . pytest
python -m pytest tests/test_grading_contract.py tests/test_release_gates.py -q
```

CI runs only these small contract checks on Python 3.12. It does not start native task containers, E2B workers or model runs. A real release check against this incomplete archive is expected to reject release; it is not a CI success criterion.

## Parallel work

Use focused branches and worktrees for Order, Equivalence and ANN. Keep one canonical local cloud queue and ownership registry; worktree copies must never create competing accounting state. Freeze candidate code before fresh independent controls. Record original/candidate results and remaining gates before a task decision.

The resumed execution window ends October 12, 2026 at 05:52:16 UTC. Existing automatic-review holds remain in effect. Creating this private repository does not authorize benchmark publication.

## Sources and attribution

The harness derives from [ByteDance Seed EdgeBench](https://github.com/ByteDance-Seed/EdgeBench) at `6e4e5f4aa087a9121aa09a6059e5484e5102c6ff`; its Apache-2.0 license is retained in `LICENSE`. Public task definitions derive from the [Hugging Face release](https://huggingface.co/datasets/ByteDance-Seed/EdgeBench) at `6cc5a7f1b3288ce52484ad828177b8cc86b05b75`; the separate license is retained in `tasks/LICENSE`. These notices do not clear every in-image dataset or dependency for redistribution.

The authorized [public progress report](https://edgebench-audit-progress.alex-shengzhi.chatgpt.site) explains the current findings and their limits.
