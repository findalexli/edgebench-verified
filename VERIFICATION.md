# Verification protocol

This repository is an independent, unreleased audit and repair of the public EdgeBench release. A task is not verified because its metadata loads, a unit test passes, or multiple agents agree. Certification requires task-specific evidence about what the evaluator measures and actual execution of the candidate environment.

## Scope and source identity

The acquisition lock in `audit/upstream-lock.json` records the exact upstream harness and dataset revisions and SHA-256 of all copied files. All 51 public tasks require a documented disposition. The full benchmark advertises 134 tasks; the other 83 have not been acquired and are not covered by a verification claim. Access to them is needed before any full-benchmark certification.

Keep the original task IDs and the SForge JSON/BENCHMARK.yaml format. Preserve originals in the acquisition record. Place fixes in task definitions, source overlays, or the forked harness, with patches and before/after evidence. A different evaluator, changed data split, or changed scoring rule creates a different benchmark version. Do not silently combine its scores with the upstream leaderboard.

## Deliverables and proportional work

A **finding report** can publish supported, scoped conclusions while other tasks
remain pending. A **completed public-set audit** needs a reviewed decision for all
51 acquired originals. A **verified replacement benchmark** additionally needs
tested, versioned retained/repaired tasks and a runnable release manifest. These
are distinct milestones; finishing one does not imply the next.

Use the original task promise to choose the checks. A complete new solver is not
a prerequisite for demonstrating a narrow verifier defect. Build a reference only
when it resolves a named question that smaller controls cannot answer. Domain,
rights and generalization gaps limit the applicable release claim; they do not
reopen a separately established finite finding. Formal tools should reduce a
specific uncertainty, not create a mandatory proof project for every task.

The three checks below must provide different evidence: interpretation, execution
and an attempt to refute/generalize. Three agents agreeing on the same source is
not three independent reproductions. Follow the actual frozen-run and release
gates; do not add a fresh approval chain for routine reversible diagnostics.

## Three independent checks

1. **Specification and data:** identify the intended skill, permitted tools, exact inputs, target outputs and failure conditions; reconcile task prose with every scoring rule. Trace data to its source and recorded license, identify split membership, inspect duplicates, and distinguish provided feedback from untouched evaluation. Verify labels or reference answers independently where feasible. Specialized scientific, educational and formal tasks require competent domain review or an explicit unresolved gate.
2. **Execution and counterexamples:** run the pinned environment; demonstrate a known-good control, known-bad controls, empty input, partial solutions, invalid output and relevant timeout behavior. Test plausible incorrect solutions that ordinary tests miss. Use independent oracles and metamorphic properties rather than copying the implementation into a test. Record randomness, hardware, dependencies and exact commands. A toy harness fixture proves its narrow behavior; it does not establish a task's defect rate.
3. **Independent reproduction and generalization:** have a separate review pass attempt to refute the findings and rerun the evidence. Freeze the candidate artifact before evaluating fresh cases or seeds. Quantify repeatability and selection effects for stochastic or timing-based tasks. Where a learned grader is used, record the grader version, rubric, repeated-score variation and agreement with adjudicated examples.

These are evidence modes, not a claim that three independent humans have reviewed the work. Record who or what performed each pass, its scope, and whether it reused another pass's source analysis or fixtures. Automated corroboration does not substitute for required expert adjudication.

## Disposition rules

- **Retain:** all gates pass without a material change to the task; record the tested release identity.
- **Repair:** identify the failing contract, preserve a regression case, implement a justified correction and rerun both valid and invalid controls in the actual task environment. Record score incompatibilities and rescore affected artifacts.
- **Exclude (withhold this original unchanged):** give a specific, evidenced reason and an independent review; preserve the original and the audit record. Do not exclude merely because a task is difficult to inspect or lowers model performance. An unavailable or unresolved task remains explicitly unresolved unless a justified release exclusion is adjudicated.
- **Review pending:** evidence is incomplete. This is the initial state of every task and is not a release decision.

An exclusion is a version-specific release decision, not a statement that every
score is invalid, a repair is finished, or a future version is unusable. State
whether it follows an impossible requirement, observed verifier/data defect, or
conservative policy choice, and disclose the affected subtask or capability.
Missing evidence and our own environment failures do not by themselves justify
exclusion. Keep the replacement's status separate.

No unresolved task should disappear from the denominator. Publish the list of retained, repaired, excluded and pending tasks alongside family coverage, and disclose how removing tasks changes the evaluated capabilities.

## Claim discipline

Each claim must identify its source revision, task/config/image identity, exact observed behavior, reproduction, counter-evidence and limits. Separate observed source facts, controlled counterexamples, actual corpus occurrences and measured score effects. Do not infer leaderboard impact from a parser fixture. Do not call intentionally exposed development feedback a contamination violation without establishing the promised holdout contract. Retract hypotheses that fail source or runtime checking.

For a change to count as a repair, the old artifact must reproduce the failure, the proposed artifact must resolve it, and independent valid/invalid cases must continue to behave correctly. A test that asserts the implementation's own internal structure does not prove correctness.

## Release gates

`tools/check_release.py` is the mechanical gate for the review registry. It must reject missing, stale or mismatched evidence and unsupported inclusion. It is necessary but not sufficient: human or agent authors can write an incorrect evidence report, so its truth must still be assessed against recorded execution and source.

Before publication, require all 51 public task dispositions to be reviewed; every retained/repaired task to pass specification, verifier, data, execution and independent-reproduction gates; immutable work/judge identities; source and data checksums; a runnable release manifest; reference controls; repeatability measurements; versioned repair notes; and an explicit scope statement for the 83 unavailable tasks.

The benchmark should report original versus repaired score effects where comparable artifacts are available. If historical artifacts or raw trajectories cannot be obtained, state that limitation and produce fresh results rather than estimating an unobserved historical effect.

## Artifact handling

Store compact evidence and hashes in `audit/`. Keep large image blobs, temporary registry tokens and raw hidden answer archives outside the publishable repository. Pin all acquired images by OCI digest. Dataset and image contents can have different provenance from the harness; preserve notices and resolve redistribution rights before publishing those contents.

The work/judge split prevents direct visibility during ordinary agent work, but does not itself prove evaluator integrity. Review trust boundaries with local controlled tests. Do not test attacks against the authors' hosted systems or contact them without user authorization.

## Reader-verifiable case and publication package

Use the [reference publication](https://parsewave.ai/benchmark-research/automation-bench#overview)
as a presentation target: overview, browsable cases, concrete evidence, method
and usable downloads. Presentation quality does not replace scientific evidence.
The dated comparison and worked template remain in the
[pre-cleanup Git snapshot](https://github.com/findalexli/edgebench-verified/tree/8f55f7e115cd68d7e61da94db5c8b4e5486e42aa/docs).

Each case should contain:

1. The task's promised behavior and the exact original version.
2. A small counterexample: expected versus observed result, provenance and limits.
3. A conclusion: confirmed, rejected or unresolved; original disposition separate.
4. A versioned correction, if present, and matched before/after results for the
   trigger plus independently justified valid and invalid controls. Say “not run”
   where evidence is absent; never estimate an unobserved leaderboard effect.
5. Who authored, reviewed and actually reproduced the result, with reused evidence
   and any failed hypotheses or regressions visible.
6. Commands, manifests, resource needs and accessible evidence sufficient to
   reproduce the claimed scope. Explicitly identify restricted or missing inputs.

Keep all 51 task decisions visible in `TASKS.md`, including withheld originals and
pending tasks. Link repaired versions separately and explain capability coverage
lost through exclusion. Before claiming a reproducible benchmark release, verify
a clean rerun of the release package and resolve its distribution permissions.
An interim report must clearly retain its unfinished scope and applicable
publication authorization; it must not imply that release gates passed.
