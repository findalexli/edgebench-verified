# EdgeBench Verified working instructions

## Latest user preferences, October 11, 2026

Use `gpt-6-astra` with `high` reasoning for new parallel reviewers and E2B model
requests. The current coordinator's `audit/model-policy.json` and later direct
steering supersede historical Sol/xhigh settings. Frozen attempts retain their
recorded regime, and all automatic-review holds remain.

The obsolete hourly continuation automation was removed at the user's request.
Continue the active audit goal within its existing authorized window; do not
recreate a recurring schedule without a useful purpose and user authorization.
The publication target is a reproducible audit with evaluated native-format
repairs and clear case evidence; see `docs/PUBLICATION-STANDARD.md`.


## User priorities: finish reviews and make reports readable

The user has repeatedly asked for faster task conclusions and plain-language
updates. Finish decisions from accepted evidence before adding setup for the
same question. Run independent ready task checks alongside result review. After
one bounded setup correction or roughly 15 minutes of setup, record the blocker
and advance another task; do not create another controller framework by default.
Preserve the actual execution gates, review requirements and holds.

Lead reports with what changed since a dated checkpoint, what was concluded and
what it means. Count final task decisions, actual task checks and specific findings
separately. Partial observations are not finished task reviews. Use ordinary task
names; keep job IDs, hashes and internal workflow terminology in supporting links.
`AUDIT-STATUS.md` owns the dated current summary; evidence snapshots retain their
original dates. Apply the two existing skills rather than adding more skills for
these same needs.

## Consolidated workflow, October 11, 2026

Read `docs/AUDIT-WORKFLOW.md` and the two relevant skills under `.agents/skills/`
before preparing another experiment. Recover the named accepted evidence and exact
saved job terminal before assigning source preparation or review. Worktrees isolate
code; the designated coordinator owns the single live queue and ownership ledger.
The Git snapshot contains selected evidence and is not independent launch authority.
The October 11 consolidation does not change existing execution authorization,
holds or release gates. Resume authorized audit work after consolidation without
inventing another user-approval requirement.

## Resumed 48-hour window, October 10, 2026

The user explicitly said to keep going for another two days and requested a
proper GitHub repository and useful isolated worktrees. The new window runs
from 2026-10-10T05:52:16+00:00 to 2026-10-12T05:52:16+00:00 and supersedes the
expired October 10 cutoff below. Bind the new direct instruction in
`audit/evidence/sol-cloud-authorization-v1/resume-user-steering-20261010.json`.
The previous window and its closed-worker receipts remain immutable.

Create the working GitHub repository privately. Preserve the local evidence
archive; commit only reviewed source, public task definitions and explicitly
selected evidence. Worktrees isolate code changes, not cloud accounting: keep
one canonical ownership registry, queue and coordinator. Prioritize integrated
Order repairs, complete Equivalence evaluator checks and the original ANN
evaluator; reuse accepted evidence and avoid new controller/review frameworks.
All previous model preferences, resource bounds, automatic-review holds and
release gates remain in force. No benchmark publication is authorized by this
repository setup. Stop new work at the new deadline, collect evidence, close
only this audit's owned workers and pause the continuation.

## Resumed work and model preference, October 8–9, 2026

The user explicitly resumed the audit after the original execution window and
Codex usage interruption. Continue within the further 24-hour execution window,
explicitly authorized by the user, ending 2026-10-10T05:18:55+00:00. The later
October 9 user instruction removes the agent-imposed $15 ceiling and $5 external
reserve; it supplies no replacement dollar ceiling. Bind the exact instruction
in `audit/evidence/sol-cloud-authorization-v1/budget-user-steering-20261009.json`.
Keep recording finite per-job cost estimates, reservations and settlements.
Preserve earlier policies, attempts, the previous window and unsuccessful reviews.
For every new review subagent and any new model run inside E2B, use
`gpt-6.1-sol` with `xhigh` reasoning. The user intends a later stronger-model
review; it remains pending. Native E2B tests have no model reasoning setting.
Keep using E2B for useful parallel heavy work and the local memory guard for
any heavy local launch. The prior automatic-review holds remain in effect.
The structured preference is recorded in `audit/model-policy.json`.

## User preference recorded October 7, 2026

The user explicitly permits up to 24 hours of careful work and prefers a
responsive, stable local computer over throughput. Respect CPU, memory and disk
limits when delegating or parallelizing. E2B and the relevant configured keys in
`/home/alex/agentsmd-rl` may be used for this audit when needed. This preference
must survive handoffs and context compaction. On October 8 the user explicitly
authorized larger E2B CPU/memory allocations and 10 to 50 simultaneous cloud
workers to accelerate the audit. This expands cloud concurrency, not local load.
On October 8 the user also confirmed an E2B Pro plan and asked to request
two-hour worker lifetimes. The 30-minute initial lifetime below is the audit's
conservative default, not a provider maximum. A separately recorded owned-worker
request may verify the two-hour capability; close that worker immediately after
reading its actual expiry. Longer useful jobs may use the confirmed allowance
with matching time/cost accounting, while frozen earlier attempts retain their
original limits. Do not leave finished workers running to fill their lifetime.
Later on October 8 the user explicitly requested local Docker checks as well,
with independent review agents working in parallel, to improve throughput.
Local native work is now authorized when the host guard below admits it; keep
one bounded local heavy job and use E2B for additional native jobs. This changes
the execution location preference, not the user's requirement that the computer
remain responsive. A live check at 18:42 UTC found about 2.5 GiB Windows physical
memory free and 3.6 GiB commit headroom, so that particular local launch was
refused before any child or container started. Recheck before a later launch.

## Execution policy for this audit

- Prefer E2B for heavy parallel execution; guarded local Docker work is also
  authorized by the later user request above. Use the shared cloud policy in
  `audit/cloud/resource-policy.json`: at most 50 task-owned workers,
  including existing solver workers and unresolved creation reservations. The
  user confirmed account capacity for 50. Exact account maxima were not readable
  with the available API key. Scale only
  useful, reviewed independent work; do not create idle machines to fill slots.
  Use the default 2 vCPU / 4 GiB profile when it fits the work. The user
  explicitly permits the highest useful E2B CPU/memory allocation, including
  new work where it will help. The already measured 8 vCPU / 8 GiB profile
  and any larger profile require a reviewed task-specific resource and cost
  envelope before launch; do not silently change a frozen job or override
  existing controller compatibility guards. Preserve earlier outcomes and
  report different resource regimes. All controllers share ownership
  accounting, a creation rate limit and exact versioned cost policy.
- Give each cloud worker an ownership label and a 30-minute initial lifetime.
  Extend only while useful work progresses. Export checkpoints and terminate
  this audit's idle or finished workers. Never run account-wide cleanup or touch
  another project's sandboxes.
- Respect the actual expiry returned by E2B. The first worker's lifetime was
  capped at one hour despite a renewal request. Export checkpoints before that
  deadline; do not assume repeated renewals extend it. Rotate only after the
  current job is terminal and its needed results are exported, then terminate
  the owned old worker before creating a replacement. Count live workers and
  unresolved reservations against the shared cloud limit.
- Track estimated cloud usage. The initial self-imposed $15 compute ceiling
  was superseded by the later October 9 user instruction, together with the $5
  external reserve. The renewed policy uses JSON null for the agent-imposed
  ceiling and zero external reserve. Keep finite per-job cost estimates,
  lifetime reservations, settlement proofs and useful-work/resource/deadline
  limits. Do not start large model sweeps without a concrete cost estimate.
- Keep credentials in the local client. Read only the needed variable from the
  referenced configuration; do not print values, copy the whole configuration,
  forward unrelated keys, or include secrets in evidence or archives.
- Keep local work to editing, source review, compact reports and small tests.
  Do not launch additional large image downloads or full corpus solving locally
  while Windows has low available physical or committed memory.
- Limit coordinator staging to four simultaneous payloads and 64 MiB of
  admitted payload bytes, releasing bytes after verified upload. Keep the
  independent coordinator address-space limit; payload admission alone does
  not bound total process memory. Cloud jobs may continue after staging slots
  are released.
- Before any future heavy local job, use `tools/run_bounded.py`. Require at least
  4 GiB available physical memory and commit headroom on Windows, and 4 GiB
  available memory in Linux. WSL's memory report alone is insufficient.
- Allow at most one heavy local job, at most two logical CPUs, one numerical
  library thread and 1 GiB worker memory by default. Use a wall timeout and
  checkpoints. Aggregate usage needs monitoring; per-process limits alone do
  not establish an aggregate guarantee. If the guard is not available, do not
  launch the job.
- Preserve at least 50 GiB free on each affected local filesystem. Download
  large source layers in the cloud and return compact, verified source/evidence
  where possible. Do not remove unrelated data to make space.
- Do not change global WSL, Docker, swap, power or Windows settings, restart the
  computer, or terminate unrelated processes to free resources.

Observed reason for caution: Windows reported approximately 2 GiB free physical
memory and 2.4 GiB commit headroom while WSL reported approximately 11 GiB
available. All heavy audit jobs were stopped after that check. These are a
historical observation, not live measurements or a diagnosis of other software.

## Evidence and release discipline

Follow `VERIFICATION.md`. All 51 public tasks require explicit dispositions;
the other 83 advertised tasks are unavailable and cannot be certified. Keep
native task formats. Passing tool tests is not task certification. Distinguish
observed source behavior, synthetic controls, real environment runs and measured
benchmark impact. Do not claim three human reviewers when using AI agents.
Preserve unsuccessful checks and corrected or rejected hypotheses.

## Active automatic-review holds

Grid reflected-score-marker follow-up review/diagnostic is held after automatic
review rejected the reviewing agent for possible cybersecurity risk. The exact
triggering operation was not identified. Preserve existing source facts and
retractions; do not retry, rephrase or reroute the flagged work. See
`audit/evidence/grid-native-proposal/root-hold.json`. Earlier ad-overlap,
Coq-output/tactic, native-codec and CVC5 follow-up holds also remain in effect.

The judge_artifact agent later also errored with the same generic automatic-review
message after a warehouse source/mock assignment; the triggering operation and
causal link to its earlier grid context are unknown. Warehouse implementation is
paused without retry/rerouting; existing reviewed source/math facts are retained.
See `audit/evidence/warehouse-source-review/implementation-hold.json`.


The new Sol V8 cloud model-pilot implementation was also stopped after automatic
review rejected its agent turn for possible cybersecurity risk on October 10.
The triggering operation was not identified. Do not retry, rephrase or reroute
that model-pilot implementation. Preserve V2–V7 failures and the closed no-auth
host diagnostic; adjudicating its already saved result does not authorize a new
model run or diagnostic retry. Ordinary unrelated deterministic, data and formal
audit work remains in scope. This is a separate runner hold, not an eighth held
EdgeBench task or a newly established benchmark defect. See
`audit/evidence/sol-v8-model-pilot-implementation-hold-v1/hold.json`.
