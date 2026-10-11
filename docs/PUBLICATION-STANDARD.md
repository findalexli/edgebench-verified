# A publishable EdgeBench audit

**The target is a reproducible audit with evaluated repairs and clear reporting.** Our current record supports 13 scoped finding decisions and ten decisions to omit exact originals. It does not yet support a completed public-task audit or a verified replacement benchmark: 41 of 51 public task decisions remain pending and no task is certified.

## What to take from the reference

The reference reports screening 600 public tasks, flagging 323, rejecting 117 suspected issues and confirming/fixing 206. It publishes 100 detailed cases and reports 1,236 fresh trials plus 344 changed verdicts among 1,235 opposite-verifier replays. Its method says 84 tasks kept the same instructions, starting records and tool names; other comparisons may include setup or requirement changes. These are the site's claims, not independently verified results from this review. [Reference overview and method](https://parsewave.ai/benchmark-research/automation-bench#overview).

Its useful structure is **overview → browsable findings → concrete case evidence → method and downloads**. A reader can compare a correct submission with a faulty one, inspect the checker change, and see recorded before/after scores. Case 813 links original submissions, patches, a replay package and reproduction instructions, while distinguishing finite replay from final integration review. [Reference case 813](https://parsewave.ai/benchmark-research/automation-bench#case/task-813).

Case 4026 makes a remaining false rejection visible: a shared-email alternative described as valid still receives 0.667 after repair. We should match that candor; a polished page and passing selected controls are not proof of a complete fix. [Reference case 4026](https://parsewave.ai/benchmark-research/automation-bench#case/task-4026).

## Concrete comparison

| Publication requirement | EdgeBench's current position | Deliverable that closes the gap |
| --- | --- | --- |
| Complete account of the acquired public set | 51 acquired; 10 original exclusions; 41 pending; 0 certified | One reviewed final disposition for every acquired original, with separate identities and decisions for proposed replacements. All 51 remain visible, including exclusions. |
| Reader-verifiable findings | 13 scoped decisions and selected evidence exist; much supporting execution evidence remains in the local archive | A complete case card for every published claim, with a public-safe, usable reproduction bundle or an explicit access limit. |
| Repairs that actually run | Schemathesis has a complete native scorer comparison for the exact two-file repair; English has fixed-response local controls. Persisted replacement packaging and whole-task approval remain incomplete | Exact task definition, source changes, work/judge environment identities and run instructions, followed by original/candidate tests in the actual candidate environment. A patch file alone is insufficient. |
| Evidence that a repair preserves valid work | Selected controls exist; their coverage differs by task | Matched original/candidate results for the triggering failure and independently justified valid alternatives, with meaningful negative and boundary controls. Keep every observed regression visible. |
| Independent reproduction | Separate reviews exist, but source review, review of saved results and fresh reruns are distinct | Identify the author, reviewer and reproducer for each case, reused evidence, actual rerun commands and outcomes. Say when no independent execution occurred. |
| Measured impact | Local/component outcomes are available; many claims explicitly do not establish score inflation | Publish only measured score/verdict changes, distinguish same-submission replay from fresh solving, and isolate changed task requirements or scoring rules. No inferred leaderboard effect. |
| Transparent audit selection | Rejected hypotheses and setup failures are preserved in scattered records | A screening/review log showing confirmed, rejected and unresolved claims with reasons. Do not turn setup failure or intentional partial credit into a benchmark defect. |
| Reusable evidence | Exact identities exist, but selected Git evidence is not the full reproducible archive | A downloadable manifest, sufficient licensed inputs, exact versions, expected outputs and a verified clean rerun. Describe anything readers cannot access. |

The historical “37 partial tasks” tracking group is not yet a reconciled union of every task ever checked. Do not use it as the audit coverage headline. Source reading, component execution, full-task execution and final dispositions need separate labels.

## Strongest recovered repair example

The exact Schemathesis correction already passed a native comparison on October 8. The metrics reference kept score **0.135313**; the forwarding wrapper changed from **0.135313 to 0.129063**, an exact **−1/160**. All 126 original outcomes were preserved in each pair. These are partial task implementations, so the result validates that correction at its tested scope; it does not provide a complete known-good task solution or a certified replacement image. Reuse this accepted result rather than run the same experiment again. [Native repair comparison](../evidence/selected/schemathesis-native-repair-comparison.json).

## Publication structure

1. **Overview:** what EdgeBench measures, the public scope, the principal conclusions, the 51-task disposition table and measured results. State that 83 advertised tasks were unavailable. Explain exclusions as finished decisions about exact originals, not completed repairs.
2. **Findings:** concise, searchable case cards with outcome-based titles and task names. Show the same evidence sequence on every card; use evidence images only when they explain the failure better than text.
3. **Repairs and evaluation:** list each original/replacement pair, exact change, native-format download, matched results, remaining regressions and certification decision. Keep unrepaired exclusions visible.
4. **Method and reproducibility:** acquisition identities, task-specific controls, reviewer/reproducer roles, failed attempts and rejected claims, selection limitations, data provenance and permissions, and rerun instructions.
5. **Complete task ledger:** all 51 acquired originals, final decisions, replacement links and capability coverage lost through exclusion. The unavailable 83 are explicitly out of scope.

A publishable interim finding report may honestly contain pending tasks and uncertified repairs. A finished public-set audit requires reviewed dispositions for all 51. A releasable verified benchmark additionally requires every included original/replacement to meet VERIFICATION.md and have a runnable release manifest. These are distinct products; do not silently lower one standard to finish another.

No proposed number of model trials, reviewers or random seeds here replaces task-specific evidence requirements. Statistical uncertainty, model identity, resource conditions and denominators must match whatever impact experiment is actually performed. No original and repaired scores should be silently pooled.
