# borden_source_inversion-v2: paired results

E2B worker, 8 CPU (job `borden_source_inversion-v2-paired-r2`, exit 0, worker killed; see
`evidence/worker-r2.json`). Every arm ran the task's **original eval_cmd** inside the **unchanged
pinned judge image** (`b1a08348…`), with `--network none`.
- **v1**: the submission/case dir is the v1 work dir plus `answer.json`.
- **v2**: the submission/case dir is the v2 work dir (extracted from the image built from
  `../Dockerfile`, which adds `README.md` and `forward_model.py`) plus the same `answer.json`.

Normalisation uses `sforge/harness/score_rescale.py`. In v1 the task has no `rescale`, so
`score_0_100` is `None`. In v2 it is `linear 0..109`.

| Arm | Kind | v1 raw | v2 raw | v1 normalised | v2 normalised | Cap (both) | hidden / future rRMSE |
|---|---|---|---|---|---|---|---|
| textbook ADE fit (review regression case) | honest, wrong convention | 7.031 | 7.031 | None | 6.45 | cap15 | 2.583 / 1.852 |
| judge-convention fit (review, own re-implementation) | honest | 31.200 | 31.200 | None | 28.62 | cap45 | 0.552 / 0.200 |
| **v2 fit using only the shipped `forward_model.py`** (fitted in the worker) | honest | 31.199 | 31.199 | None | 28.62 | cap45 | 0.552 / 0.200 |
| bound-midpoint baseline | shipped baseline | 7.012 | 7.012 | None | 6.43 | cap15 | 2.622 / 1.925 |
| hidden true source | ceiling anchor (not an honest submission) | 109.000 | 109.000 | None | 100.00 | none | 0 / 0 |
| out-of-bounds answer (C0=5000, half_length_x=500) | invalid | 4.000 | 4.000 | None | 3.67 | cap15 | 9.265 / 2.671 |
| no `answer.json` | invalid | 0 | 0 | None | 0.00 | — | — |

All 14 evaluations exited 0. Raw scores are identical v1 → v2 for every arm, as expected: the
judge image and its logic are unchanged.

## Other checks

- **The shipped model equals the judge model** (`evidence/label_check.txt`, run in the judge image):
  - shipped `forward_model.simulate_from_answer(truth)` against the judge's
    `hidden_forward_model.simulate_from_answer(truth)`: max |diff| = **0.0** over all 656 label rows;
  - against the stored clean labels: max relative diff 8.9e-13.
- **The v2 solver uses only v2 solver-visible files** (`tools/v2_solver.py`, `evidence/v2_solver.log`):
  - it ran in the v2 work image with no network;
  - its row-vectorised wrapper over the shipped functions equals the shipped `simulate_from_answer`
    (max relative diff 0.0 at 3 random parameter sets);
  - it ran 80-start bounded least squares on public noisy/censored data and converged to the
    same point as the review's judge-convention fit (public RMS 0.00792; C0 492.07, z_center
    221.638, half_length_z 2.294);
  - wall time 208 s.
- **Work-dir diff v1 → v2** (`evidence/workdir_diff.txt`): only `README.md` changed, and
  `forward_model.py` was added.
- **Evaluator keyword scan**: the shipped `forward_model.py` contains none of the evaluator's
  forbidden-keyword strings, and no arm produced warnings.

## Run history

- Attempt r1 (`evidence/worker-r1.json`): every judge arm completed with the same numbers.
  The v2 solver finished its fit but could not write `answer.json`: the work image runs as a
  non-root user and the bind mount was root-owned (`evidence/v2_solver-r1-write-failed.log`).
- r2 makes the directory writable (`chmod`) and is otherwise identical.

## Verdict

**Accepted** (documentation and rescale; judge unchanged). Every arm's raw score is identical in v1
and v2 (14 evaluations, all exit 0). The regression case (textbook ADE fit) stays at 7.031 raw. The
honest fit built only from the shipped v2 `forward_model.py` reaches 31.199 raw (28.62 normalized),
which shows the convention can now be reproduced. The out-of-bounds and missing-answer controls stay
at 4.000 and 0.

## Revision (2026-10-12): the prompt says `forward_model.py` may be used

**Why.** The fixed prompt kept the original scoring step "Use a hidden Borden-ADE region-source
forward model" and the rule "Do not read or reference hidden scoring files", without saying that the
shipped `forward_model.py` may be used. A careful solver could read the two together as forbidding it.

**Change.** Three lines, identical in the work-image `README.md` and in `task.json.in` →
`work.agent_query`:
- the `forward_model.py` entry under "Provided files" adds "You may read, run and import it freely.";
- scoring step 3 becomes "Use the Borden-ADE region-source forward model shipped as `forward_model.py` to
  predict concentrations at hidden monitoring wells and hidden future times.";
- the rule becomes "Do not read or reference hidden scoring files. `forward_model.py` is not one of them:
  it is an exact copy of the judge's model and may be used freely."

Nothing else changes: `forward_model.py`, the grader, the grader image, the answer key and the
`rescale` block are as before. Revised `README.md`: `bcd35189…` (was `70c905d7…`); `task.json.in`:
`5ec716d4…` (was `0a48dc9f…`; an earlier revision of this note gave `65928330…`, which is the same file
before the later `work.image_tag` bump to `f389fcf94240-ebv-v2.1`). `repair.patch`, `materialize.sh`, `source-lock.json` and `task-json.diff`
were regenerated (`tools/make_materialize.py`; `task-json.diff` with the same re-serialised `diff -u` as
before), and a clean-copy `./materialize.sh` reproduced every output byte for byte.

**Job.** `evidence/runs/borden_source_inversion-v2-paired-r3`: one E2B worker
(`ic41z0ndpo77solwxjefe`), `status: exit=0` in 61 s, killed. It built the first fixed work image
(v2prev) and the revised one (v2) from the same `Dockerfile`, and graded the seven submissions of r2
(r2's `answer_v2_fit.json` as `v2_fit`; no solver was rerun) in the original, v2prev and v2 work
directories with the unchanged judge image and the original command (21 evaluations, all exit 0).

| Arm | v1 raw | v2prev raw | v2 raw |
|---|---|---|---|
| textbook_fit | 7.031 | 7.031 | 7.031 |
| judgeconv_fit | 31.200 | 31.200 | 31.200 |
| baseline_mid | 7.012 | 7.012 | 7.012 |
| truth | 109.000 | 109.000 | 109.000 |
| v2_fit | 31.199 | 31.199 | 31.199 |
| invalid_oob | 4.000 | 4.000 | 4.000 |
| invalid_missing | 0 | 0 | 0 |

Every `score.json` is byte-identical across the three working directories, `warnings` is empty in
all of them, and the only work-directory difference between v2prev and v2 is the three README lines
(`result/out/workdir_diff_v2prev_v2.txt`). The scores equal those of r2.

**Verdict:** **accepted** (prompt text only; scores unchanged).

## Repeatability (2026-10-13)

The revision's job was run three times on fresh E2B workers (`evidence/runs/borden_source_inversion-v2-paired-r3`, `-rep2`, `-rep3`) with the same `run.sh` and `inputs/`. Every run has `status: exit=0`, and its worker was killed. All seven submissions under the original, earlier fixed and current fixed work image (21 results) give the same exit status and TOTAL_SCORE in all three runs (`result/out/summary.txt`). The staged `pkg/files/` and `pkgprev/files/` (README sha256 `bcd35189…` and `70c905d7…`, `forward_model.py` `2b3efafb…`, as in run 1's `workdir_*.txt`) were removed after collection. The earlier `-paired-r2` job was already run three times.
