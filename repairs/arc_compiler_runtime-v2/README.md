# Arc Compiler Runtime, fixed version: document the hidden `analyze()` interface

Status: **adopted**. This is the published fixed version (outcome "Fixed", `cases/arc_compiler_runtime.md`); it was accepted on the side-by-side run in `paired/results.md`.

## What this fixes

The hidden type-checking tests expect `analyze()` to return a list of `{level, message}` items with specific message wording, but no file the solver can see says so. An honest analyzer that keeps the starter's return shape silently loses up to 33.67 points. The fixed version documents the interface and corrects the stated starter score in the solver's instructions; the grader and every submission's score stay the same.

## What changes

### The problem in detail

The hidden type-system suites call `analyze(parse(lex(src)))` from `compiler/src/semantic.js`. They
`.filter` the result by `d.level` and match `d.message` against fixed substrings: `Undefined`,
`Cannot reassign immutable` and `expects 2` (`evaluator-hidden/tests/strengthened/round2-type-system.test.ts:16-46`;
`extra/hidden-type-system-adversarial-{1,2,3}.test.ts:19`). The starter that ships with the task returns
`{ ok, errors, warnings, program }` (`compiler/src/semantic.js:2`). No solver-visible file (TASK.md, problem.md,
CHEATSHEET, spec/, docs/, public smoke tests) names the interface or the message texts. So an honest, correct
analyzer that keeps the starter's shape scores 0/128 on suites worth 1000/2970 of the weight (33.67 points),
with no warning. The side-by-side run shows this: the same analysis scores 69.26 in array form and 35.59 in starter form.

Separately, TASK.md states "Starter expectation `SCORE=0.00`" for the public smoke-test score, and problem.md states
"Expected stripped starter score: 0.00". The starter actually scores `SCORE=100.00` on the public tests (48/48),
measured in the original work image (the container the solver works in): `evidence/runs/arc_compiler_runtime-v2-paired/result/out/public_v1_a_starter.log` ends `SCORE=100.00`. On the hidden tests it scores 35.59.

### Exact change

Two solver-visible Markdown files in the **work image** change. The grader image, grader, tests, starter code and
task prompt do not change.

- `agent-start/TASK.md`:
  - replace the false starter row with the measured `SCORE=100.00` (48/48);
  - add a "Semantic analysis interface" section with the return shape (array of `{level, message}`), the
    three required substrings and the conditions that produce them, and the rule categories the hidden
    type-system suites check (stated as rules, not as test programs).
- `agent-start/problem.md`: replace the false "Expected stripped starter score: 0.00" with the measured value,
  and add a one-line pointer to the interface section in TASK.md.

`Dockerfile` = `FROM` the pinned work-image digest plus two `COPY --chown=1000:1000` lines (build context `files/`).
`repair.patch` was generated with `diff -u` from `orig/` (extracted from the pinned work image) to `files/`.
`task.json.in` changes only `work.image_tag` (`v2-analyze-contract-docs`, a local build tag; see Build and use). `judge.image_tag` stays `200e176a8e30`. `agent_query` already directs solvers to
TASK.md ("Use CHEATSHEET.md, TASK.md, and the public smoke tests as the language contract"), so it does not change.

### Why documentation rather than a matching starter

- **Documentation leaves every submission's score unchanged.** The side-by-side run confirms it: all five test
  submissions score byte-identically per suite under the original and fixed versions. Only what the solver is told changes.
- **A starter whose `analyze()` returns `[]` would change the starter's score** from 35.59 to 47.21 (+11.62). That
  gain comes from passing the "no error expected" cases without doing any analysis. It would also still leave
  the message substrings undocumented.
- **The substrings must be documented either way.** No starter can convey them without, in effect, writing
  the diagnostics. So documentation is necessary, and with it, a starter change is unnecessary.

The `agent-start` folders of the work image and the grader image were compared. They are identical except for `.git`. The
grader's copy of TASK.md is not read by the grader, and `submit_paths` is `compiler/src/` only. So the grader image
does not need rebuilding.

### Score scale and comparability

The task's score scale is `linear`, `lower=0`, `upper=100`. There are no rank30, rank1 or expert reference points. No
reference point is invented or moved: **the score scale is kept**, and `task.json.in` leaves `rescale` untouched.

- **Scores of single submissions are comparable across the original and fixed versions.** For an identical `compiler/src/`, the hidden
  score is the same under both (measured for 5 test submissions).
- **Results of agent runs are not comparable across the two versions.** Solvers of the fixed version receive information that solvers
  of the original lacked (the interface and message texts), so expected agent scores on the fixed version are higher. Do not pool or rank
  agent runs on the original and fixed versions together.

## How it was checked

See `paired/results.md` (job script `paired/run.sh`, raw per-suite counts in `paired/suites/`). Each test submission ran through the original grader once with the original work files and once with the fixed ones. Summary:

| Test submission | Original, hidden score | Fixed, hidden score | Public score (same in both) |
| --- | ---: | ---: | ---: |
| (a) shipped starter | 35.59 | 35.59 | 100.00 |
| (b) `analyze()` returns `[]`, nothing else changed | 47.21 | 47.21 | 100.00 |
| (c) invalid: broken JS code generation | 25.79 | 25.79 | 83.33 |
| (d) honest analyzer, documented array shape | 69.26 | 69.26 | 100.00 |
| (e) same analyzer, starter object shape (the test submission that shows the problem) | 35.59 | 35.59 | 100.00 |

The score out of 100 equals the raw result (the scale is the identity). All runs: `valid=true`, exit 0.

How the acceptance criteria (a test submission that shows the problem, a correct test submission and an invalid test submission) are met for a documentation fix:

1. **The test submission that shows the problem.** Under the original version, the choice between (d) and (e) is invisible to the solver, and the wrong guess costs 33.67 points.
   Under the fixed version the documentation names the right shape.
2. **Correct test submission (a).** Unchanged.
3. **Invalid test submission (c).** Caught by the public and hidden tests in both versions.

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t ebv/arc_compiler_runtime-work:v2 -f Dockerfile files
```

`materialize.sh` takes the following steps:

1. Pull the pinned image(s) by digest, unless already present.
2. Extract the original files with `docker create` and `docker cp`. No container runs in this step.
3. Check each original against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of every file under `files/` (and `orig/`) against `source-lock.json` → `materialize.outputs`. Any mismatch fails loudly.

After that, the `Dockerfile` builds without changes. Regenerated files keep the file mode they have in the image.
See `../MATERIALIZE-CHECK.md` for how each package was verified.

This Dockerfile builds the fixed **work** (solver) image; its build context is `files/` (as stated in the Dockerfile and in the header of `materialize.sh`). `orig/` (the in-image originals referenced above) is also regenerated by `materialize.sh`.

**Image tag.** `task.json.in` names the work image tag `v2-analyze-contract-docs`. That is a local build tag, not a published image: no v2 image is pushed to a registry, and users build it themselves. To use `task.json.in` unchanged, tag the image you build `edgebench.work.arc_compiler_runtime:v2-analyze-contract-docs` (the clean-machine rebuild check, `evidence/runs/materialize-check-g3`, built it under `seededge/edgebench.work.arc_compiler_runtime:v2-analyze-contract-docs`). The `ebv/…:v2` tag above is only a local example.

## Limits

- The fix does not change how the grader counts cases, the `fail_infra` result on a submission that hangs or crashes
  the test process, or the 9-template adversarial suites. Measured on the original grader: the starter with an
  infinite loop on a construct used by one suite (1.35 points) is reported invalid with score 0 instead of about 34.75
  (`../../evidence/runs/arc_compiler_runtime-hang-suite`). The task's `score_first` selection does not read `valid`, so
  such a submission is ranked at 0; it never displaces a submission that scored above 0.
- Credit for format alone remains. `[]` earns +11.62, and a constant analyzer that always returns one diagnostic scored 57.81 (with bun as a
  stand-in runtime, not in the image; the same figure is in `cases/arc_compiler_runtime.md`, Limits), because the "ok" and "error" cases only check whether the result is empty. The fixed version makes the shape known, which makes this slightly
  easier. Fixing it needs grader changes (for example, requiring both the passing and failing forms of a template to pass
  together), and those would change what scores mean.
- The fixed TASK.md describes the checked rule categories at the level of the interface. That is more than the original disclosed about
  the hidden suites, but it does not include test programs or expected values.
- In the fixed work image, `git status` shows `M TASK.md` and `M problem.md` against the image's `init` commit.
  This is harmless, since those files are outside `submit_paths`.
- Test submission (d) was written by an auditor who had read the hidden tests. It shows that the documented interface
  is enough, not how a solver without that knowledge would perform.
- The fixed image was built inside the cloud worker (`sha256:82eb673f…`). A rebuild is not claimed to be bit-identical.
