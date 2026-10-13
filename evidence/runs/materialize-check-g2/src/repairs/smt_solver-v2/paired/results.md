# smt_solver v2: paired results

**Verdict: ACCEPTED.**
- **Trigger:** correct models, which v1 rejects, are accepted by v2.
- **Valid controls:** unchanged.
- **Wrong models:** every wrong-model control is rejected by both versions, and no wrong model became
  acceptable.

## Setup

**Runs.** Two E2B jobs ran on 2026-10-12. Both exited 0, and both workers were killed. Each was run
three times on fresh workers (`-rep2`, `-rep3`); see Repeatability below.
- **`evidence/runs/smt_solver-v2-paired-b/`** ran every arm, the mini cases and the full `eval_cmd`.
- **`evidence/runs/smt_solver-v2-paired-c/`** reran only the wrong-model arm, after a fix to the
  witness-building oracle described below.
- **First attempt** (`smt_solver-v2-paired/`). Its corpus arms never reached scoring. The submission
  preflight rejected the replay stub, because a comment contained the word "z3", and rejected the
  witness files, because they contained benchmark paths. This was a setup error, so that attempt has
  no corpus results. Its mini results match `-b`.

**Images.**
- v1 is `seededge/edgebench.judge.smt_solver@sha256:2bf3482a…`, with `evaluate.py` sha256 `f4be8e8d…`.
- v2 was built from `../Dockerfile`. Its `evaluate.py` sha256 is `bbc730f8…`, and the image ID is
  `sha256:a1942c2f…`.
- The hidden zip is identical in both images (`d51f1ee9…`).

**Judge arms.** Every arm runs `--network none` with the image's own `evaluate.py` and the official
flags (`--timeout 60 --perturb --perturb-salt hidden-sebench`).

**Witness preparation.** It ran before any judge arm, in a separate `python:3.11-slim` container with
z3 4.13.0.0, using `witness_roundtrip.py` and `make_witness_sets.py`. The scoped set is the 69
expected-sat hidden files, 53 in QF_UF and 16 in QF_UFLRA: 27 are multi-context (unwinnable in v1) and
42 are single-context. A replay stub (`stub_solve`) prints the precomputed witness for the exact file,
selected by a content hash that ignores the perturbation lines.

**Witness arms.**
- **ground** (C): the z3 true model with keys rendered as let-expanded ground terms, which is the form
  the spec describes.
- **textual** (A): the reviewer's checker-model witness with textual keys. It exists only for the 42
  single-context files; the stub answers `unknown` on the other 27.
- **textual_true** (B): the z3 true model keyed by textual key, taking the value at the first
  occurrence.
- **ground_wrong** (Cw): C with one UF value changed. For each file, z3 proved on the real formula that
  the changed witness is **not** a model, giving 69 of 69 wrong witnesses in `-c`. In `-b`, an oracle
  bug with Real-sorted values had dropped the 16 QF_UFLRA files; `-c` fixed it.
- **Oracle check:** every C witness is a genuine model according to z3, 69 of 69 `sat`
  (`evidence/c/oracle.jsonl`).

## Corpus: 69 scoped hidden files (verdict counts)

| arm | class | v1 | v2 | expected | ok |
| --- | --- | --- | --- | --- | --- |
| ground (correct, spec keys) | 27 multi-context | invalid_model 27 | **correct 27** | v1 wrong, v2 accepted | yes |
| ground (correct, spec keys) | 42 single-context | invalid_model 42 | **correct 42** | v2 accepted | yes |
| textual (valid control) | 42 single-context | correct 42 | correct 42 | unchanged | yes |
| textual (valid control) | 27 multi-context | unknown 27 (no witness) | unknown 27 | unchanged | yes |
| textual_true (correct model) | 27 multi-context | invalid_model 27 | **correct 27** | v2 may accept (genuine model) | yes |
| textual_true (correct model) | 42 single-context | correct 42 | correct 42 | unchanged | yes |
| ground_wrong (invalid, `-c`) | 27 multi-context | invalid_model 27 | invalid_model 27 | rejected in both | yes |
| ground_wrong (invalid, `-c`) | 42 single-context | invalid_model 42 | invalid_model 42 | rejected in both | yes |

**Other observations.**
- **No arm went from correct to rejected.** Verdict changes between v1 and v2 run only from
  invalid_model to correct: ground 69, textual_true 27.
- **Subset scores**, raw on the 0–1 scale (the rescale is linear 0..1, so the score out of 100 is
  100 × raw; there are no easy files in the subset, so the raw maximum is 0.9):

  | arm | v1 | v2 |
  | --- | --- | --- |
  | ground | 0.0 | 0.9 |
  | textual | 0.587 | 0.587 |
  | textual_true | 0.587 | 0.9 |
  | ground_wrong | 0.0 | 0.0 |

- **Rejection reasons for the wrong models in v2.** 53 were rejected for a congruence violation, and 15
  QF_UFLRA files plus 1 more were rejected for a false assertion or a congruence violation. In v1, all
  69 were rejected for a missing key or a false assertion.

## Full original `eval_cmd` (all 774 hidden files, `--parallel 16`), ground arm

The stub answers `unknown` on the 705 files that have no witness.

| version | raw score (0–1) | out of 100 | pass | exit |
| --- | --- | --- | --- | --- |
| v1 | 0.0000 | 0.00 | 0/774 | 0 |
| v2 | 0.1249 | 12.49 | 69/774 | 0 |

The grader's own summary lines (`evidence/b/fulleval_lines.txt`) read `score=0.000000 (0.00/100)` and
`score=0.124948 (12.49/100), correct=69/774`.

## Mini cases (reviewer's fixed-witness stub, 13 cases)

| case | v1 | v2 | expected | ok |
| --- | --- | --- | --- | --- |
| scope_conflict (trigger, correct ground keys) | invalid_model (missing `(f x)`) | **correct** | v2 accepted | yes |
| define_conflict (trigger) | invalid_model (missing `(f y)`) | **correct** | v2 accepted | yes |
| single_let (ground key) | invalid_model (missing `(f x)`) | **correct** | v2 accepted | yes |
| scope_conflict_textkeys (correct ground keys plus a textual key) | invalid_model | **correct** | v2 accepted (ground keys determine f) | yes |
| ground_control | correct | correct | unchanged | yes |
| single_let_textkey | correct | correct | unchanged | yes |
| ground_control_wrong | invalid_model | invalid_model | rejected | yes |
| scope_conflict_wrong | invalid_model | invalid_model (false assertion) | rejected | yes |
| define_conflict_wrong | invalid_model | invalid_model (false assertion) | rejected | yes |
| single_let_wrong | invalid_model | invalid_model (false assertion) | rejected | yes |
| alias_conflict (unsat, "sat" answer) | wrong | wrong | rejected | yes |
| alias_conflict_let (unsat, "sat" answer) | wrong | wrong (congruence) | rejected | yes |
| unused_conflict (f gets 2 values at one argument, through an unused key) | **correct** | invalid_model (congruence) | v2 rejects a witness that is not a function | yes (intended change) |

Mini final score, raw on the 0–1 scale: v1 0.1615, v2 0.3231 (16.15 and 32.31 out of 100).

## Limits

- **Witness source.** The witnesses are z3 models replayed by a stub, not output from an end-to-end
  solver built for the task.
- **Repeatability.** Both jobs were run three times on fresh workers
  (`evidence/runs/smt_solver-v2-paired-{b,c}{,-rep2,-rep3}/`). Each run's `result/out/summary_parsed.txt`
  is identical to its first run's, so every verdict and score above is the same in all three runs. The
  first attempt of `-b-rep2` failed on the image pull (`result-attempt1/`, exit 2) and was retried.
- **Wrong-model controls.** Each wrong witness changes one UF value. The controls do not cover every
  possible wrong-model shape.

## Repeatability (2026-10-13)

The corpus, mini and full-`eval_cmd` arms were run three times (`-b`, `-c`, each with `-rep2` and `-rep3`; see Limits), with identical results. The CPU-quota arms (`smt_solver-v2-paired-cpu`) and the re-runs of `-b`/`-c` against the CPU-capped version (`-b-cpu`, `-c-cpu`) were **not** repeated. That part of the SMT fix was withdrawn, because the official configs give SMT 16 grader CPUs. Those three jobs remain single-run measurements and are not counted as repeats of the fix.
