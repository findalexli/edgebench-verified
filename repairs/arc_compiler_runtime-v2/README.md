# arc_compiler_runtime v2: document the hidden `analyze()` interface

Status: **candidate, paired evaluation run (accepted under REPAIR-SPEC 1–3)**. Not adopted, not published.

## Defect

The hidden type-system suites call `analyze(parse(lex(src)))` from `compiler/src/semantic.js`. They
`.filter` the result by `d.level` and match `d.message` against fixed substrings: `Undefined`,
`Cannot reassign immutable` and `expects 2` (`evaluator-hidden/tests/strengthened/round2-type-system.test.ts:16-46`;
`extra/hidden-type-system-adversarial-{1,2,3}.test.ts:19`). The shipped starter returns
`{ ok, errors, warnings, program }` (`compiler/src/semantic.js:2`). No solver-visible file (TASK.md, problem.md,
CHEATSHEET, spec/, docs/, public smoke tests) names the interface or the message texts. An honest, correct
analyzer that keeps the starter's shape therefore scores 0/128 on suites worth 1000/2970 weight (33.67 points),
silently. The paired run shows this: the same analysis scores 69.26 in array form and 35.59 in starter form.
Separately, TASK.md states "Starter expectation `SCORE=0.00`" for the public smoke score, and problem.md states
"Expected stripped starter score: 0.00". The shipped starter actually scores public `SCORE=100.00` (48/48),
measured in the original work image. Analysis: `evidence/reviews/_science-systems-triage.md` §1.

## Exact change

Two solver-visible Markdown files in the **work image** change. Judge image, evaluator, tests, starter code and
task prompt do not change.

- `agent-start/TASK.md`:
  - replace the false starter row with the measured `SCORE=100.00` (48/48);
  - add a "Semantic analysis interface" section with the return shape (array of `{level, message}`), the
    three required substrings and the conditions that produce them, and the rule categories the hidden
    type-system suites check (as rules, not test programs).
- `agent-start/problem.md`: replace the false "Expected stripped starter score: 0.00" with the measured value,
  and add a one-line pointer to the TASK.md interface section.

`Dockerfile` = `FROM` the pinned work-image digest plus two `COPY --chown=1000:1000` lines (build context `files/`).
`repair.patch` was generated with `diff -u` from `orig/` (extracted from the pinned work image) to `files/`.
`task.json.in` changes only `work.image_tag` (placeholder `v2-analyze-contract-docs`, to be replaced by the
real tag of the built image). `judge.image_tag` stays `200e176a8e30`. `agent_query` already directs solvers to
TASK.md ("Use CHEATSHEET.md, TASK.md, and the public smoke tests as the language contract"), so it does not change.

## Why documentation rather than a matching starter

- **Documentation leaves every submission's score unchanged.** The paired run confirms it: all five controls
  score byte-identically per suite under v1 and v2. Only what the solver is told changes.
- **A starter with `analyze()` returning `[]` would change the baseline** from 35.59 to 47.21 (+11.62). That
  gain comes from passing the "no error expected" cases without doing any analysis. It would also still leave
  the message substrings undocumented.
- **The substrings must be documented either way.** No starter can convey them without effectively writing
  the diagnostics. So documentation is necessary, and with it, a starter change is unnecessary.

The work image and the judge image `agent-start` were compared: they are identical except for `.git`. The
judge copy of TASK.md is not read by the evaluator, and `submit_paths` is `compiler/src/` only. So the judge
does not need rebuilding.

## Anchors and score compatibility

The task rescale is `linear`, `lower=0`, `upper=100`. There are no rank30/rank1/expert anchors, and no
anchor is invented or moved: **anchors are kept**, and `task.json.in` leaves `rescale` untouched.

- **Per-submission scores are comparable across v1 and v2.** For an identical `compiler/src/`, the hidden
  score is the same under both (measured for 5 controls).
- **Agent-run results are not comparable across v1 and v2.** v2 solvers receive information that v1 solvers
  lacked (the interface and message texts), so expected agent scores on v2 are higher. Do not pool or rank
  v1 and v2 agent runs together.

## Paired evaluation

See `paired/results.md` (job script `paired/run.sh`, raw per-suite counts in `paired/suites/`). Summary:

| Control | v1 hidden | v2 hidden | public (v1 = v2) |
| --- | ---: | ---: | ---: |
| (a) shipped starter | 35.59 | 35.59 | 100.00 |
| (b) `analyze()` returns `[]`, nothing else changed | 47.21 | 47.21 | 100.00 |
| (c) invalid: broken JS codegen | 25.79 | 25.79 | 83.33 |
| (d) honest analyzer, documented array shape | 69.26 | 69.26 | 100.00 |
| (e) same analyzer, starter object shape (trigger) | 35.59 | 35.59 | 100.00 |

Normalized = raw (identity linear rescale). All runs: `valid=true`, exit 0.

How the REPAIR-SPEC criteria are met for a documentation repair:

1. **Trigger.** Under v1, the (d)/(e) choice is invisible to the solver, and the wrong guess costs 33.67 points.
   Under v2 the docs name the right shape.
2. **Valid control (a).** Unchanged.
3. **Invalid control (c).** Caught by public and hidden tests in both versions.

## Limits

- The repair does not address the other triage items: in-process counting and the exit-hook forgery (out of
  good-faith scope here), the `EXPECTED_CASES` environment exposure, `fail_infra` on crashes, and the
  9-template adversarial suites.
- Format-only gaming remains. `[]` earns +11.62, and the triage's constant-error analyzer earns 57.81 (bun
  stand-in), because the "ok" and "error" cases only check emptiness. v2 makes the shape known, which slightly
  eases this. Fixing it needs judge changes (for example, requiring both polarities of a template to pass
  together), and those would change what scores mean.
- The v2 TASK.md describes the checked rule categories at contract level. That is more than v1 disclosed about
  the hidden suites, but it does not include test programs or expected values.
- In the v2 work image, `git status` shows `M TASK.md` and `M problem.md` against the image's `init` commit.
  This is harmless, since those files are outside `submit_paths`.
- Control (d) was written by an auditor who had read the hidden tests. It shows that the documented contract
  is sufficient, not how a blind solver would perform.
- The v2 image was built inside the worker (`sha256:82eb673f…`). A rebuild is not claimed bit-identical.

## Build

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

This Dockerfile builds the v2 **work** (solver) image; its build context is `files/` (as stated in the Dockerfile). `orig/` (the in-image originals referenced above) is also regenerated by `materialize.sh`.
