# Continuing the EdgeBench audit

**Handoff snapshot: October 11, 2026, after the corrected writer-error assessment and original-suite regression.** Five corrected integration controls passed. The same shared-hook plugin also passed a fresh 55-item original-suite regression and selected repaired JUnit test. Both workers are closed; no owned workers are running. These results remain finite evidence; verify current ownership before acting.

## Goal and what counts as finished

The goal is a defensible decision for every acquired public task, with useful native-format corrections where possible. Three products have different finish conditions: an interim findings report can include pending work; a completed public-set audit needs decisions for all 51 acquired tasks; a verified replacement benchmark additionally needs every included version to satisfy [VERIFICATION.md](VERIFICATION.md). Another 83 advertised tasks were unavailable.

[README](README.md) gives the overview, [FINDINGS](docs/FINDINGS.md) explains confirmed problems, and [TASKS](TASKS.md) owns the current 51 dispositions. The Git `audit/task-registry.json` is a historical snapshot with three exclusions; it is not the current ten-exclusion tracker. Do not silently update historical evidence counts. A confirmed finding, an excluded original, a repair candidate and a certified replacement are separate outcomes. Current totals remain findings across 16 tasks, ten excluded originals, 41 pending decisions and zero certifications.

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

## Latest results and next work

**Coverage filtering:** all four native helper calls passed their authored checks on the reporting candidate V2 overlay. The original test's class filter discarded all 36 generated values; complementary allow cases contained unexpected properties while the filtered assertion still examined nothing. This confirms a finite test gap in that measured environment, not bare-original behavior or historical score impact. The original test function and full scorer were not run in this attempt. [Accepted result](evidence/selected/reporting-coverage-filter-acceptance.json). The frozen correction matched all 20 paired complete test-function expectations: 12 normal returns and eight expected assertion failures, using actual generation in 12 calls and explicit empty/wrong-type doubles in eight. Valid generation passed; forced wrong behavior was rejected by the repaired tests. [Patch and finite acceptance](proposedrepairs/reporting-coverage-filter/README.md). Full phase-five pytest/scorer execution and fresh independent native reproduction remain separate.

**Actual plugin integration:** the shared-hook correction improved four of five unchanged controls over the base plugin's zero of five. A later control-only change replaced the stdout-specific error check with an actual injected-error event and nonzero exit; all five corrected controls passed, including completed closing of observed writers. The exceptional parallel case does not check complete final reports or receipt of both schemas. This is not an unchanged-control zero-to-five comparison and does not explain the prior stdout failure. [Matched comparison](evidence/selected/reporting-shared-hook-acceptance.json) · [corrected-control acceptance](evidence/selected/reporting-writer-error-acceptance.json).

**Treant:** the adapted README counts turns, so seven iterations with six position changes do not establish a separate arithmetic defect. Differences from the primary game's movement remain measured, but whether the adaptation intended them is unresolved. Seek authoritative adaptation wording rather than replaying the same controls. [Accepted conclusion](evidence/selected/treant-contract-conclusion.json).

## Evidence to reuse and next priorities

A **fresh regression on the changed shared-hook plugin** passed the same **55 original test identities**, all five phases and score **1.0**; the unchanged script still reports **53/53**. Its actual writer also passed the separately mounted repaired JUnit test. This is newly measured evidence, not an inherited base-V2 pass. [Accepted regression](evidence/selected/reporting-shared-regression-acceptance.json). The original scorer was unpatched; the 20 coverage-repair expectations remain evidence on base V2. The [current matrix](docs/REPORTING-COVERAGE.md) has 13 finite-check rows and nine partial rows, not 13 completed requirements. Historical category snapshots and failed controls remain linked there.

The HTTP-date V2 repair has 16 classified reviewer controls matching and one future leap occurrence unclassified. Native preparation still lacks a pinned generator and selected-overlay runner; generator/property and full patched-scorer checks are not ready. Rust's repair is finite component evidence, with Cargo/native behavior still separate. Earlier Schemathesis function-identity native comparisons remain accepted; do not rediscover them.

Prioritize decision-changing work: run the integrated corrected judge through the full scorer, address named stateful and dispatcher gaps, and obtain a fresh independent reproduction with matched controls. Keep another source-ready task moving when setup stalls. For excluded originals, preserve the finished exclusion and evaluate a separately identified replacement rather than repeatedly reopening the original finding. Use formal tools only where they resolve a specific mathematical uncertainty.

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
