# Formal verification tools

[Rethlas](https://github.com/frenzymath/Rethlas) is an optional mathematical
proof-generation and critique tool for this audit. It is an external tool;
EdgeBench code, task decisions and evidence stay in this repository and its
separate local archive.

The inspected source is pinned to
`e7e48a6d30e7f0ddf0ed1909a594a1f0cfe2c2b7`.

## What its result means

Rethlas uses two Codex agents: one writes an informal proof blueprint and another
checks its reasoning and references. The inspected runner, verification API and
MCP writer do not invoke Lean or TLC. A Rethlas verdict is additional AI review,
not a proof checked by a formal kernel or a task certification.

Use it to expose assumptions, find counterexamples and produce a proof plan.
Then encode the exact supported claim in Lean, or the relevant state model in
TLA+, and independently execute the appropriate checker. Keep the source-to-model
mapping, numerical or state bounds, assumptions and negative controls explicit.
Reuse already accepted results when their relevant bytes and assumptions match.

## Audit integration

1. Select a bounded, author-owned statement with no private benchmark answers.
2. Give it a fresh problem ID and pin the statement, permitted references and
   tool source. The initial [tie-aware ranking packet](../formal/problems/tie-aware-ranking.md)
   contains a deliberately false claim and the intended corrected contract.
3. When a separately permitted bounded model run is available, collect both the
   draft and the verifier's verdict. Verify schema and statement/proof bindings;
   the existence of `blueprint_verified.md` alone is insufficient.
4. Independently check the resulting precise claim with Lean or TLC. Retain
   failures and distinguish abstract proof from actual native task behavior.

All new model requests, including Rethlas nested agents, must select
`gpt-6.1-sol` with `xhigh`. Upstream defaults and its named subgoal agent do not
match that preference. An eventual isolated configuration must also bound
iterations, agent fanout, process memory/CPU/wall time and verifier timeout;
the inspected verifier's default timeout is unlimited. No paid API fallback
or use of a usage reset is authorized.

Existing automatic-review holds remain intact. This tool must not be used to
retry or reroute the held Sol V8 model-pilot/auth implementation or held task
work. Linking and source inspection do not admit a model run or service launch.

## Current state

Source inspected and tool linked; problem packet prepared. No Rethlas service,
generation loop, verifier request, dependency installation or proof execution
has run. The optional tool does not block the three active native audit lanes.

Sources: [README](https://github.com/frenzymath/Rethlas/blob/e7e48a6d30e7f0ddf0ed1909a594a1f0cfe2c2b7/README.md),
[verifier instructions](https://github.com/frenzymath/Rethlas/blob/e7e48a6d30e7f0ddf0ed1909a594a1f0cfe2c2b7/agents/verification/AGENTS.md),
[runner](https://github.com/frenzymath/Rethlas/blob/e7e48a6d30e7f0ddf0ed1909a594a1f0cfe2c2b7/agents/generation/tests/run_example.sh).
