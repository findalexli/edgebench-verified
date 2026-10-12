---
name: e2b-efficient-audits
description: Plan, run, recover, and account for useful E2B audit or test workers with bounded local coordination and exact owned cleanup. Use for E2B execution and failure diagnosis; task validity and scientific acceptance remain task-specific.
---

# E2B: useful tests, accountable workers

## Spend coordination on useful tests

Prepare a worker only for a named unanswered task question. Prefer collecting and concluding a completed run to recreating its setup. Use an existing runner and bounded local checks when they answer the question; add infrastructure only for an identified missing capability in the next useful test.

Enforce the evidence-audit skill's setup stop when dispatching: preserve the typed failure, leave the lane stopped, and advance its named ready fallback. Another preparation assignment requires new evidence about the failure. A source-ready packet goes to its required review and admission. Reuse unchanged accepted checks and completed slices; admit the unresolved complement. Useful concurrency follows demonstrated original task execution and observed staging/settlement capacity.

Report how many original task checks actually ran and what they established. If none ran, say so in plain language. Put worker handles, estimates and failure codes in linked operational records. The evidence-audit skill owns scientific conclusions; README is the overview and TASKS is the current decision tracker.

## Start from one current state

Resolve current state from `AGENTS.md` and the E2B ledger `evidence/runs/ledger.jsonl` (the earlier coordinator and `HANDOFF.md` are preserved at Git tag `earlier-audit-final`); workspace paths and historical receipt links below are locally available provenance, not required archive contents in Git. Obtain the current handoff/authority from that coordinator rather than substitute an old packet when a link is absent.

Read the coordinator's dated `audit/AUDIT-BRIEF.md`, compact current handoff and later steering. Follow only the historical archive keys needed for the current question; preserve the full archive without repeatedly loading it. Bind authorization, user deadline, local guards, ownership and task/runner holds; historical packets are not current authority. Never retry or reroute automatic-review holds. A separate model-runner hold does not block unrelated unheld native/data lanes.

Before dispatching preparation or review, recover the named task's accepted leaf and exact saved job/attempt terminal, exports, closure and settlement. Keep one current task row pointing to these receipts:

- **Accepted/completed:** reuse matching evidence; recover only missing collection, acceptance or bookkeeping. Never change a job ID to manufacture freshness.
- **Running/unsettled:** preserve its handle; recover or close exact owned resources before another attempt.
- **Stopped:** retain the failed phase/configuration; distinguish local precredential stops, provider attempts and original task tests.
- **Unattempted:** name the unresolved question and smallest experiment that could answer it.

Reuse unchanged sources, reviews, controls, collectors and resource/lifecycle evidence when bytes and assumptions match. Check changes and unresolved concerns using complete saved identities and actual schemas/reference bases.

## Make useful work runnable

Choose a supported bounded local diagnostic, admitted native container or E2B heavy job. Ordinary reversible diagnostics need no invented approval chain; fragile frozen workers retain their actual root/grant, intake and ownership gates. Source GO is not launch authority.

A missing cached interpreter or previously built environment is a provisioning need, not proof the task is blocked. When owned cloud setup is authorized, try a bounded standard image/bootstrap with the required versions before declaring them unavailable. Record the actual runtime and any compatibility differences; never silently substitute a different interpreter or retry a held path.

Pilot the **original task path** on useful actual inputs before repeating it at scale. Fixtures, dependency censuses and launcher success do not establish evaluator behavior. Freeze the finite hypothesis, exact inputs/sources, bounds, observables, typed failures and owned cleanup. Prefer the maintained runner and small inputs over copied controller ancestry. After one evidence-based setup correction, reassess at roughly 15 minutes: report the concrete blocker and choose a supported environment or another runnable lane.

Run independent task/data/review lanes together. Reuse collectors/reviewers across waves. Read-only adjudication of a closed batch can use its saved history while a separately admitted batch runs; preserve that run's handle instead of restoring a stale current-batch pointer. Whole-drain requirements for new launch/runtime replacement do not automatically block adjudication. Use `followup_task` to start an idle agent's new assignment.

A shared-runner failure blocks only its actual consumers. Keep one repair owner while unrelated admitted runs, saved-result review and completed Git delivery proceed. On owner failure, preserve any exact live worker handle and recover ownership; an old handoff entry does not establish a live agent.

When direct user steering changes a deadline, budget, model or schedule, reconcile the saved automation with current authority. Inspect its actual cadence; do not carry it forward merely because it already exists. An active goal does not by itself require a recurring wake-up. Remove an obsolete automation when authorized, and preserve notification preferences on retained schedules.

## Preserve execution boundaries

This audit permits up to **50 useful owned workers**, including unresolved reservations, and useful CPU/memory increases under reviewed resource/cost envelopes. Capacity is not a target. Bound CPU, memory, wall time, disk, expansion, output and cleanup. Honor host/headroom guards and **four staging slots totaling 64 MiB**, releasing bytes after verified upload; keep the independent coordinator address-space cap. Scale with runnable work, observed throughput and cost, not submitted threads.

For long native runs, compare CPU-seconds with allowed parallelism and wall time. A per-process CPU cap can end a multi-threaded program before its wall budget; size it for the intended observation or explicitly limit the claim. Keep wall, memory, ownership and cleanup bounds intact.

Bind final serialized job, controls digest, grant, worker identity and actual runtime consumers before credentials. Use the supported coordinator interpreter/SDK; scientific interpreter/ABI is separate. Check policy loaders/imported constants when renewing deadlines. Keep credentials in the authorized coordinator or isolated account service, outside native actors and evidence. Secure staging of the authorized Codex-plan cache does not authorize unrelated keys; native actors retain their network/filesystem restrictions.

The user removed the $15 ceiling/$5 reserve: record actual/committed usage and forecasts without a replacement ceiling. Resolve new reviewer and E2B model settings from the current model policy and latest direct user steering. Frozen attempts retain their regime; a preference change does not authorize retrying a hold. Resets, paid fallback, publication and unrelated work need applicable authorization.

## Lessons from the Claude re-verification (2026-10-12)

- **Closed is not completed.** A ledger "closed"/killed event only proves cleanup. Treat a job as
  finished only if its record shows `status: exit=0` **and** the collected `result/out/` exists;
  a host restart left three paired jobs killed with `ReadTimeout`/`ConnectError` and no results.
- **Keep heavy local work off the host.** Three concurrent Lean builds (two 33 GB-image containers
  plus an uncapped host Mathlib compile) exhausted a 15 GB host and forced a restart. Use a
  machine-wide `flock` for heavy local jobs, cap host compiles, and send everything that fits
  (≤ ~18 GB disk, ≤ 8 GB RAM per worker on this account) to E2B.
- The minimal runner `tools/e2b_run.py` (one job per worker, exact kill in
  `finally`, append-only ledger) replaced the earlier multi-file coordinator for routine jobs.

## Collect and conclude

Retain bounded first-failure observations, partials and typed stops; parse nested connector JSON before safe projection. Missing, malformed, over-cap or failed output is incomplete; exit zero alone is not coverage. Private stderr, hidden IDs/labels/features/answers and credentials stay out of public exports.

Verify declared artifact identities/completeness and that receipts come from the backend that actually performed the work. Keep scientific identities distinct from resource telemetry while checking both against their pinned contracts. Terminate and confirm **exact owned** workers/coordinators/children only; local exit is not closure proof. Preserve unresolved closure and prioritize recovery. Settle usage, retain conservative unknown-cost evidence and join settlement, batch and native hashes in their separate domains. Never clean the whole account.

Separate proposals/source checks/model requests, actual task starts/completions and accepted results. Lead updates with results, failures, closure and spend. Source GO, private auditor access and finite controls do not establish holdout independence, broader science or certification; scientific acceptance remains task-specific.

## Read only the applicable lesson

Use [observed failure lessons](references/observed-failure-lessons.md) by trigger; reuse unchanged loaded guidance:

- Capture caps/nested writers/phase snapshots → **Receipt budgets and phase snapshots**.
- Accepted-leaf recovery, SDK/imports/argv/deadline/intake/reference bases → **Runtime and intake compatibility**.
- Upload congestion/fanout → **Pilot and staging congestion**.
- Diagnostics, inherited readers, child limits/restoration/version probes → **Failure observations and bounded readers**.
- Coordinator errno 12/mappings/cache/IPC → **Coordinator memory and network boundaries**.
