# EdgeBench Verified

We are checking whether EdgeBench's tasks, tests and data measure what they promise, and whether proposed corrections work in the original task format. This is an independent, unfinished private audit. No replacement benchmark is released.

**October 11, 2026:** 51 public tasks acquired; another 83 advertised tasks unavailable. The current record has **16 confirmed findings at their stated scopes, ten excluded original versions, 41 pending task decisions and zero certified tasks**. A finding can be settled before its repair or whole-task decision is ready. Exclusion means withholding that exact original unchanged for its recorded reason; it does not approve a replacement.

- [Findings](docs/FINDINGS.md): confirmed problems, evidence, exclusions and separate repair progress.
- [Task tracker](TASKS.md): one current disposition for each of the 51 acquired tasks.
- [Handoff](HANDOFF.md): what a successor needs to continue, including ready work, limits and execution ownership.

The reporting candidate passed 55 printed original tests with score 1.0, and its actual writer passed a separate repaired JUnit test. That does not establish all 22 reporting requirements. Later integration controls failed before their intended lifecycle checks; the authored configuration mismatch is documented, and corrected controls remain unlaunched at this handoff. The date-checker repair has accepted finite predicate evidence, with native generator and full-scorer assessment still pending.

This repository contains original-format task definitions, the harness, reviewed source, selected evidence and bounded repair/reproduction packages. It is not the complete private evidence archive or a live execution coordinator. The task tracker owns current dispositions; older registry and evidence tables retain historical counts. Earlier narrative checkpoints remain available in Git history at commit `8f55f7e115cd68d7e61da94db5c8b4e5486e42aa`.

The harness derives from ByteDance Seed EdgeBench at `6e4e5f4aa087a9121aa09a6059e5484e5102c6ff`; its Apache-2.0 license remains in `LICENSE`. Public task definitions derive from the Hugging Face release at `6cc5a7f1b3288ce52484ad828177b8cc86b05b75`, with a separate license in `tasks/LICENSE`. Those notices do not establish redistribution rights for every dataset or dependency inside task images.
