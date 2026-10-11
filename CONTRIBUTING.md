# Contributing to EdgeBench Verified

Start with [README](README.md), select one task in [TASKS](TASKS.md), and use
[HANDOFF](HANDOFF.md) for its current evidence and execution owner. This repository
includes the upstream SForge harness, but the work here is an audit and versioned
repair of EdgeBench. A clone contains selected evidence, not the full runtime.

## Make one useful change

1. State the question and the result that would settle it. Reuse the task’s saved
   evidence before starting another run.
2. Work on a focused branch; use a separate worktree when concurrent edits would
   conflict. All worktrees share one canonical cloud queue and ownership ledger.
3. Preserve original task files and failed experiments. Identify a changed judge,
   data split or score rule as a new version. Put a repair beside its reproduction
   and matched valid/invalid controls.
4. Update the existing task row and findings when a conclusion changes. Add a
   document only when it has a distinct reader or reproduction purpose. Do not
   duplicate the overview, handoff or skills.
5. Stage an explicit file list. Include selected evidence only after checking
   disclosure rights and removing credentials/private raw payloads. Open a PR
   explaining the changed behavior, evidence and remaining limits.

A supported finding, a withheld original and an approved replacement are separate
outcomes. Follow [VERIFICATION](VERIFICATION.md) for their evidence requirements.
Do not turn missing evidence or our setup failures into benchmark defects.

## Check the change

For documentation changes, check facts, links and consistency with the current
51-task table. For code changes, run relevant tests; the lightweight CI suite uses
Python 3.12:

```sh
python -m pip install -e . pytest
PYTHONPATH=tools python -m pytest tests/test_grading_contract.py tests/test_release_gates.py tests/test_cloud_dispatch_resources.py tests/test_cloud_policy.py tests/test_cloud_queue.py -q
```

These are harness and policy contract tests. Passing them does not reproduce the
benchmark or certify a task. Native/cloud work needs the current coordinator,
resource bounds and exact ownership checks described in HANDOFF and AGENTS.
Do not run broad benchmark jobs merely to validate a documentation change.

Keep upstream license notices. A bug report should include a minimal reproduction,
exact task/version and relevant redacted output; do not upload raw private logs or
credentials. Release or third-party contact requires the applicable authorization.
