# Verification protocol

This repository is an independent, unreleased audit and repair of the public EdgeBench release. A task is not verified because its metadata loads, a unit test passes, or multiple agents agree. Certification requires task-specific evidence about what the evaluator measures and actual execution of the candidate environment.

## Scope and source identity

The acquisition lock in `audit/upstream-lock.json` records the exact upstream harness and dataset revisions and SHA-256 of all copied files. All 51 public tasks require a documented disposition. The full benchmark advertises 134 tasks; the other 83 have not been acquired and are not covered by a verification claim. Access to them is needed before any full-benchmark certification.

Keep the original task IDs and the SForge JSON/BENCHMARK.yaml format. Preserve originals in the acquisition record. Place fixes in task definitions, source overlays, or the forked harness, with patches and before/after evidence. A different evaluator, changed data split, or changed scoring rule creates a different benchmark version. Do not silently combine its scores with the upstream leaderboard.

## Three independent checks

1. **Specification and data:** identify the intended skill, permitted tools, exact inputs, target outputs and failure conditions; reconcile task prose with every scoring rule. Trace data to its source and recorded license, identify split membership, inspect duplicates, and distinguish provided feedback from untouched evaluation. Verify labels or reference answers independently where feasible. Specialized scientific, educational and formal tasks require competent domain review or an explicit unresolved gate.
2. **Execution and counterexamples:** run the pinned environment; demonstrate a known-good control, known-bad controls, empty input, partial solutions, invalid output and relevant timeout behavior. Test plausible incorrect solutions that ordinary tests miss. Use independent oracles and metamorphic properties rather than copying the implementation into a test. Record randomness, hardware, dependencies and exact commands. A toy harness fixture proves its narrow behavior; it does not establish a task's defect rate.
3. **Independent reproduction and generalization:** have a separate review pass attempt to refute the findings and rerun the evidence. Freeze the candidate artifact before evaluating fresh cases or seeds. Quantify repeatability and selection effects for stochastic or timing-based tasks. Where a learned grader is used, record the grader version, rubric, repeated-score variation and agreement with adjudicated examples.

These are evidence modes, not a claim that three independent humans have reviewed the work. Record who or what performed each pass, its scope, and whether it reused another pass's source analysis or fixtures. Automated corroboration does not substitute for required expert adjudication.

## Disposition rules

- **Retain:** all gates pass without a material change to the task; record the tested release identity.
- **Repair:** identify the failing contract, preserve a regression case, implement a justified correction and rerun both valid and invalid controls in the actual task environment. Record score incompatibilities and rescore affected artifacts.
- **Exclude:** give a specific, evidenced reason and an independent review; preserve the original and the audit record. Do not exclude merely because a task is difficult to inspect or lowers model performance. An unavailable or unresolved task remains explicitly unresolved unless a justified release exclusion is adjudicated.
- **Review pending:** evidence is incomplete. This is the initial state of every task and is not a release decision.

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
