# Continuing the EdgeBench audit

**Handoff snapshot: October 11, 2026, documentation cleanup from Git commit `8f55f7e115cd68d7e61da94db5c8b4e5486e42aa`.** The coordinator reports **zero owned workers running**. Two reviewed reporting jobs are prepared but unlaunched. Verify current ownership before acting; this document is a dated handoff, not a live queue.

## Goal and what counts as finished

The goal is a defensible decision for every acquired public task, with useful native-format corrections where possible. Three products have different finish conditions: an interim findings report can include pending work; a completed public-set audit needs decisions for all 51 acquired tasks; a verified replacement benchmark additionally needs every included version to satisfy [VERIFICATION.md](VERIFICATION.md). Another 83 advertised tasks were unavailable.

[README](README.md) gives the overview, [FINDINGS](docs/FINDINGS.md) explains confirmed problems, and [TASKS](TASKS.md) owns the current 51 dispositions. The Git `audit/task-registry.json` is a historical snapshot with three exclusions; it is not the current ten-exclusion tracker. Do not silently update historical evidence counts. A confirmed finding, an excluded original, a repair candidate and a certified replacement are separate outcomes. Current totals remain 16 scoped findings, ten excluded originals, 41 pending decisions and zero certifications.

## Authority, files and execution

The shared workspace is:

`/mnt/c/users/lisz1/documents/codex/2026-10-07/shopify-plugin-shopify-openai-curated-remote-2`

Paths below are relative to that workspace unless stated otherwise:

| Purpose | Location |
| --- | --- |
| Canonical audit and execution coordinator | `edgebenchverified/` |
| Current authority and protocol | `edgebenchverified/AGENTS.md`, `edgebenchverified/VERIFICATION.md`, direct user steering |
| Compact coordinator handoff | `edgebenchverified/audit/evidence/sol-cloud-authorization-v1/current-root-handoff.json` |
| Model policy | `edgebenchverified/audit/model-policy.json` |
| Single queue, attempts, exports and settlements | `work/cloud-queue/` |
| This Git review checkout | `work/edgebench-worktrees/consolidation/` |
| Local source/evidence packets and reviews | `work/packets/`, `work/reviews/`, `work/task-sources/` |

Execute only through the canonical coordinator and its maintained admission/ownership path. A Git clone, copied launcher or prepared grant is not launch authority. Resolve exact accepted leaves and later steering: the compact handoff retains older subfields that can lag terminal reviews. Recover a live attempt's handle instead of duplicating it; accept or explain an already completed result before rerunning it.

The Git [evidence index](docs/EVIDENCE-INDEX.md) and selected manifest identify included records and local provenance. Large images, private source/test bodies, raw logs, credentials and live accounting are not all present here. Missing archive material is an availability limitation, not permission to fabricate a result or weaken a check.

## Ready work: reviewed, not launched

Both jobs use the reporting implementation V2 already measured in the original judge. Their packet handoffs retain `NOT_GRANTED`; different source reviews do not replace root admission.

**1. Actual pytest lifecycle and xdist controls.** Job `deterministic-reporting-integration-d1f5ed62d6fbfcbe` is in `work/packets/reporting-runtime-integration-native-astra-high-v3/job.json` (SHA-256 `ebaeaa327f9007b8d4c2b97f0f97bf33643ef3c6ea8050c4b3b15e937642b208`). Review: `work/reviews/reporting-runtime-integration-native-astra-high-v3/review.json` (`ec4de45cd4bd0d388269a509e0a92e604ab9f275161c24d0450d9994d58b0d09`). The change corrects the child configuration filename; candidate, driver and resource caps are unchanged. Five controls target real writer lifecycle, repeated-schema hooks, separate schemas, worker transport and injected writer-failure cleanup.

The preceding attempt failed all five outer controls before their intended assertions. `Pytester.makeini()` creates `tox.ini`, while those controls requested `pytest.ini`. This source mistake does not establish a candidate defect; the exact historical missing filename was not exported. Preserve the [accepted failed attempt](evidence/selected/reporting-integration-v2-failure-acceptance.json). Corrected-control behavior remains unmeasured.

**2. Nonvacuous body-property coverage.** Job `deterministic-reporting-coverage-bdad4143009235c5` is in `work/packets/reporting-coverage-filter-native-astra-high-v2/job.json` (`4bed1ae624853a65b14462adb91a510d510d8d63cdfbf2552eb29160fa31208e`). Review: `work/reviews/reporting-coverage-filter-native-astra-high-v2/review.json` (`176843a50dcb7a73c2eeab1017c5e5c6e1c2b047ec9d9b9a843dd387d4ed7c5b`). This corrects output collection only, preserving the scientific control and 30-second/16-KiB aggregate limit. It should determine effective type identity and whether deny/allow assertions actually examine generated values. The previous helper exited zero, but result parsing failed; no scientific conclusion was accepted. Its root record is `edgebenchverified/audit/evidence/reporting-coverage-filter-native-astra-high-v1/root-result-review.json`.

## Evidence to reuse and next priorities

The reporting candidate passed **55 actual printed tests**, although its original scorer reports **53/53**, with score **1.0**. A separately selected repaired JUnit test also passed against the real writer. Reuse those results; they do not establish a persisted replacement, the full patched scorer or all 22 promises. The [coverage matrix](docs/REPORTING-COVERAGE.md) distinguishes ten finite named conclusions, ten partial checks and two source-only behaviors. Stateful integration remains outside the two ready jobs' complete coverage.

The HTTP-date V2 repair has 16 classified reviewer controls matching and one future leap occurrence unclassified. Its native generator/property and full patched-scorer checks remain unfinished. Rust's repair is finite component evidence, with Cargo/native behavior still separate. Earlier Schemathesis function-identity native comparisons remain accepted; do not rediscover them.

Prioritize decision-changing work: finish the two ready reporting questions, close remaining implementation/specification gaps, then assess integrated repairs with matched original/candidate controls. Keep another source-ready task moving when setup stalls. For excluded originals, preserve the finished exclusion and evaluate a separately identified replacement rather than repeatedly reopening the original finding. Use formal tools only where they resolve a specific mathematical uncertainty.

Routine source/accounting work on Sol with targeted Astra review is a **proposed efficiency strategy**, not an adopted model switch. The latest actual policy requests Astra/high for new reviewers; follow current policy and direct user steering. Do not introduce repeated reviews of unchanged evidence or a new controller merely to organize work.

## Boundaries that remain in force

The authorized window ends **October 12, 2026 at 05:52:16 UTC**. Stop new work then, collect terminal evidence and close only owned workers. The obsolete hourly automation was deleted; do not recreate it by default.

Up to 50 useful owned cloud workers and justified resource increases are authorized without the removed dollar ceiling. Keep finite reservations/settlements, four shared staging slots and 64 MiB staged bytes. Native task containers receive no credentials. Local heavy work requires the existing host guard, at least 4 GiB free physical/commit headroom and 50 GiB free on affected filesystems, at most one heavy local job, two CPUs and the default 1 GiB bound unless specifically admitted. Prefer cloud execution for heavy tasks; ordinary bounded source work stays small. Sampled memory or disk observations do not prove an aggregate peak.

Seven task IDs retain automatic-review holds, covering ad-overlap, Coq output/tactic, native codec, CVC5 parser/observer/fanout, grid reflected-score and warehouse implementation work. The Sol V8 model-runner implementation has a separate hold. Use the exact held scope in canonical AGENTS and TASKS; do not retry, rename or route held work through another agent. Unrelated work can continue. Paid fallback, usage resets, third-party messages and benchmark publication require applicable authorization; repository maintenance does not supply it.

After one supported setup correction or roughly 15 minutes without reaching the intended task, record the stop and move to ready work. Preserve failed authored expectations, exact versions, counterevidence and unknown causes. Finish with a clear claim and its limits, update TASKS and the handoff, and deliver a focused Git change. Historical narrative and removed documentation remain recoverable in the [parent Git snapshot](https://github.com/findalexli/edgebench-verified/tree/8f55f7e115cd68d7e61da94db5c8b4e5486e42aa); no duplicate archive documents were created.

## Checks available in a clone

GitHub uses Python 3.12 for lightweight contract checks. These do not create cloud
workers or task containers, and passing them does not certify benchmark tasks:

```sh
python -m pip install -e . pytest
PYTHONPATH=tools python -m pytest tests/test_grading_contract.py tests/test_release_gates.py tests/test_cloud_dispatch_resources.py tests/test_cloud_policy.py tests/test_cloud_queue.py -q
```

The partial historical release registry lacks its full evidence bundle. Use the
canonical coordinator's current registry for release assessment; do not interpret
fixture-test success as successful validation of this repository's selected data.
