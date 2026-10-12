# Publication red team, batch 2: claim audit of 17 case pages

Scope: every quantitative or causal claim on `cases/<id>.md` for flt_regular_formalization,
git_rewrite_in_zig, graph_node_classification, grid_turing_robot, integer_compression_codec,
jagua_nesting_optimization, juliet_vulnerability_analyzer, k12_math_recommendation,
lean_analysis_proofs, molecular_self_assembly, nethack_dungeon_agent, new_foundations_consistency,
openrct2_theme_park_ai, openttd_transport_ai, order_addition_permutation_optimization,
ordinal_notation_well_foundedness and pfr_formalization. Good-faith correctness only. No decision
was changed. `.internal/` was not read. Nothing was run except reading saved outputs and
`tools/check_consistency.py` (0 problems after the edits).

Claims were checked against `evidence/reviews/`, `repairs/<id>-v2/`, `evidence/runs/<job>/result/`,
`evidence/scripts/**/out*`, `paired-results.csv` and `decisions.json`. Only claims that were not
SUPPORTED are listed below. All other checked claims were SUPPORTED by the cited review or the raw
output. Spot checks against raw output included the git reward.json (29,075/0/1,177, per-category
counts), the grid grade_out (19.80/19.56/2.84, 48 TLE), the integer summary.txt, the k12 cgroup
peaks and TOTAL_SCORE lines, the NF networked report (0/2246, new_bad 301, valid), the PFR
repaired.txt and reports (2/423 for A and B), the FLT classify.txt (25 entries, weight 87, weights
1 to 6), the ordinal outputs (1/85; cycle search exhausted for task1 and task2 only) and the task
JSON hashes and prompt quotes.

## Non-supported claims

| page | original text | class | evidence | edit made |
|---|---|---|---|---|
| flt_regular_formalization | "no target is out of reach for an honest, complete solution" | OVERSTATED | `lean_family_aux_census.md` L183 gives a heuristic *lower bound* of 0 (classes A+B). The page's own Limits say target truth was not audited | Now reads "the census lower bound on targets out of reach … is 0 (the truth of individual targets was not audited)" |
| flt_regular_formalization | "Export tar: sha256 `c04d3085…8e1b`" | UNSUPPORTED | No saved record outside the page | Added "(not recorded in the saved evidence)" |
| flt_regular_formalization | earlier setup failure "was a signal 11 during `lean --version`" | UNSUPPORTED | No saved log or review of that earlier record | Added "No log of that earlier record is saved in this repository." |
| flt_regular_formalization | "The census copy of the weights file is included." | CONTRADICTED | `out/flt_regular_formalization/` has no weights JSON. The entries and weights are in `classify.txt` | Now reads "The weights-file entries and their weights are listed in `classify.txt`; the weights file itself is not included." |
| git_rewrite_in_zig | "An earlier result, not re-run here, recorded that the shipped stub baseline scores 0." (also `decisions.json` "stub 0") | UNSUPPORTED | No saved run or review records the stub score | Added "that record is not among the saved evidence here" |
| graph_node_classification | "submissions that give an integer-convertible prediction for every test node score identically in v1 and v2" | CONTRADICTED | `repair.patch` `_strict_class_id` rejects bools and non-integral floats. v1 converts these with `int()` (`int(True)=1`, `int(3.5)=3`), so such submissions are valid in v1 and invalid in v2. Identity was measured on only 3 valid controls (`paired/results.md` L41-45) | Restated as int, integral finite float or decimal-integer string (not a bool). Added "measured on three valid controls" and the bool/non-integral exception. (`repairs/…/README.md` L58 has the same wording and was not edited.) |
| grid_turing_robot | "up to the full score for fixed-work solutions on a judge with fewer than about 8 CPUs" | OVERSTATED | Invalidation was measured only at `--cpus 2` (48 TLE, `native_cpus2/cpu12.log`). The cpu12 solution was not run at 3-7 CPUs | Added "Invalidation was measured only at 2 CPUs with one 12 s-per-case solution; 3 to 7 CPUs were not tested." |
| integer_compression_codec | "The starter's own throughput moved by up to 15% between runs" | CONTRADICTED | `paired/evidence/logs/r1-s0_starter-v2.stdout` vs `r4-…`: grid decode_gbps 0.7893 vs 0.6462 (about 18%). Docids 0.954 vs 0.826 is about 13% | Now reads "up to about 18% between runs (grid 0.789 vs 0.646 GB/s)". (`repairs/…/README.md` L54 still says 15% and was not edited.) |
| jagua_nesting_optimization | "Each accepted overlap is at least 25% of an item's area, about 10^6 times the validator's tolerance." | CONTRADICTED | The witness `tiny_overlap_1e-6` (area 1e-5) is also accepted by v1 (`jagua_nesting_optimization.md` L41). The 25% witness (`diag_shift`) is rejected. The large accepted overlaps are 50-100% (review L47) | Now reads "Each accepted overlap listed above is 50–100% … (`EPS = 1e-5`). The only other accepted overlap witness is at tolerance scale … benign." |
| juliet_vulnerability_analyzer | 723/723 CWE, anchor and trace checks; 16 unlabelled cases; 38/38 public vs 120/120 hidden CWE-78; 234/489 trace lengths; 120 CWE-416 sources; 18-case sample; starter 10.00 | UNSUPPORTED | No review file and no script outputs for this task under `evidence/`. The page cites only the internal triage record §6 | Added a bullet saying the outputs are not saved here and the counts come from the internal triage record §6 |
| juliet_vulnerability_analyzer | "Censuses: … `source_choice_census.py`, `unlabelled_cases.py`" | CONTRADICTED | `evidence/scripts/juliet_vulnerability_analyzer/` contains only `cwe78_public_vs_hidden.py`, `label_convention_check.py` and `sink_shape_census.py` | Now says those two scripts are not included |
| k12_math_recommendation | "A whole-container peak of about 520 to 535 MiB exceeds a 512 MiB address-space limit." and the note "The scorer needs more than a 512 MiB address-space limit: about 520 to 535 MiB whole-container peak" | OVERSTATED | The peaks are cgroup `memory.peak` values that include page cache (review L48, L60), not address space. The failure is OpenBLAS thread creation under RLIMIT_AS. The address-space need was not measured | Separated the two facts: cgroup peak 520-535 MiB under sound limits, and failure under 512 MiB RLIMIT_AS with 8 cores. Added "The address space it needs was not measured." |
| molecular_self_assembly | "A container cap partially and nondeterministically penalizes … It lost an unpredictable subset of cases, 4 of 50 in this run." | OVERSTATED | Single R3 run with no repeats (review L92). Nondeterminism was not observed | Now reads "lost 4 of 50 cases in this single run. Which cases are lost is expected to depend on timing, but repeats were not run." |
| new_foundations_consistency | Decision: "With the judge's network access, the original evaluator grades correctly." Heading: "Grading with the judge's network: works." | OVERSTATED | Only the unmodified starter was scored, once (`networked/report.json`: valid, 0/2246). No positive control | Scoped to "builds and returns a valid result for the unmodified starter (one run …)" and "works for the unmodified starter" |
| new_foundations_consistency | "In the maintained harness this applies only to the agent container. The judge container has network access." | OVERSTATED | Second-hand: `lean_family_aux_census.md` L209 says "The coordinator reports…". `sforge/harness/run_evaluation.py` is not in this repository | Attributed to the coordinator's reading and noted the file is not included |
| new_foundations_consistency | "Export tar: sha256 `076b5c9f…196`" | UNSUPPORTED | No saved record | Added "(not recorded in the saved evidence)" |
| new_foundations_consistency | "The census found no target that an honest, complete solution cannot reach." | OVERSTATED | Lower bound 0 with 15 targets exposed and untested (census L80, L105-107). Target truth not audited | Now reads "no target that is provably out of reach … (lower bound 0). The 15 exposed targets were not tested …" |
| new_foundations_consistency | "The 96 theorem-parent `_proof_N` auxiliaries are stable." | OVERSTATED | Inferred from the core-Lean `auxstyle` check (census L150, `auxstyle/nf_v4.21.out`). None was scored | Now reads "expected to be stable … inferred …; none was scored natively" |
| new_foundations_consistency | "The 20th remount command returned exit 32 inside the audit worker" | UNSUPPORTED | No saved log | Added "No log of that earlier record is saved in this repository." |
| openrct2_theme_park_ai | "The three-scenario average was 1.038, printed as `TOTAL_SCORE 10384`." | UNSUPPORTED (as observed output) | No saved log contains 10384. The wrapper `eval_openrct2.py` was not run (page Limits; review L85). The value is computed from 1.10/0.915/1.10 | Now reads "which the wrapper would print as … This value was computed; the wrapper itself was not run." |
| openrct2_theme_park_ai | Footnote: "`decisions.json` ("accepted (prompt correction)", provisional)" | CONTRADICTED | `decisions.json` status is "final (release candidate 2026-10-12)". Nothing in it says provisional | Footnote now quotes the actual status and notes the source lock is not updated |
| openttd_transport_ai | Decision: "The scorer itself works." | OVERSTATED | Only the crashing do-nothing baseline was run. No positive-score control (page Limits; review L83) | Now reads "On the do-nothing baseline, the scorer behaved as read from source; no positive-score control was run." |
| pfr_formalization | Decision: "honest proofs in two styles score identically. No target is out of reach for an honest, complete solution." | OVERSTATED | The native test covered one theorem (`mem_symmGroup`). The census gives a lower bound of 0. Target truth not audited | Scoped to "honest proofs of one theorem" and "census lower bound … is 0 (…not audited)" |
| pfr_formalization | "The auxiliary targets are 7 `_simp` lemmas, and they are stable." | OVERSTATED | `probe_summary.txt`: 7 transitive, 0 fragile. Only `mem_symmGroup._simp_1` was scored (`native/repaired.txt`) | Now says the probe found no own hole, one was credited natively and six were not scored |
| pfr_formalization | "Export tar: sha256 `61f3cc08…584`" | UNSUPPORTED | No saved record | Added "(not recorded in the saved evidence)" |
| pfr_formalization | Earlier setup failure: "A fixed-version step returned -11" | UNSUPPORTED | No saved log | Added "No log of that earlier record is saved in this repository." |

## Counts

Each row is one claim. The Juliet counts row groups one set of related numbers from one source.

| class | rows |
|---|---|
| OVERSTATED | 11 |
| UNSUPPORTED | 9 |
| CONTRADICTED | 6 |
| **total non-supported** | **26** |

Pages edited: 14 of 17. Pages with no non-supported claims: lean_analysis_proofs, nethack_dungeon_agent,
order_addition_permutation_optimization and ordinal_notation_well_foundedness.

## Not edited (outside the batch pages)

- `repairs/graph_node_classification-v2/README.md` L58 has the same "integer-convertible" compatibility wording.
- `repairs/integer_compression_codec-v2/README.md` L54 says "up to 15% (docids)". The grid dataset moved about 18%.
- `decisions.json` / `DECISIONS.md` "stub 0" for git_rewrite_in_zig has no saved evidence.

## Decisions worth a second look (reported, not changed)

- **git_rewrite_in_zig (retain, no note).** The native review recommended repair-v2 (withhold). Some of its reasons are scorer isolation, which is out of scope. Two are good-faith concerns: the scoring method is undisclosed, and the 120 s per-script timeouts depend on the host and were untested below 8 cores. The page lists both only as "observations for readers", and the decision carries no formal note. A retain-with-note decision would match the evidence better.
- **openttd_transport_ai (retain with note).** The recorded maximum effect is "whole score for prompt-following solvers", and no positive-score control exists. Retain with note is defensible because local testing exposes the crash. Still, "scorer itself works" was the main support for the decision, and it rests only on a zero-score baseline.
