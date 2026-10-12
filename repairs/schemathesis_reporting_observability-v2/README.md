# schemathesis_reporting_observability v2: JUnit XML and coverage body suppression checks

**Defects** ([review](../../evidence/reviews/schemathesis_reporting_observability.md)):
1. `test_junitxml_writer_context_manager` searches for two substrings, so plain text, malformed XML, or XML that drops the `<error>` all pass. This is 1/70 of the total.
2. `test_body_unexpected_parameters_control_deny`, and its query sibling, filter on the wrong `GeneratedValue` class (`specs.openapi.negative` instead of `generation.coverage`). The assertion is therefore vacuous, and it passes on the untouched starter that lacks the required BODY fix. This is 1/100 of the total.

**Change:** three judge files, taken byte-for-byte from the earlier accepted patches `proposedrepairs/reporting-junit/` and `proposedrepairs/reporting-coverage-filter/`. This is the same combined judge as `evidence/selected/reporting-integrated-acceptance.json`.
- `/tests/test_02_reporting.py`: parses the XML and requires one `test_label` testcase with an `<error>` carrying the message. Test names and count are unchanged.
- `/tests/test_05_email_coverage.py`: uses the correct class, requires a nonempty, correctly typed stream, and parametrizes allow/deny for body and query.
- `/tests/test.sh`: Phase 5 count goes from 10 to 12. Weights are unchanged.

`task.json.in` changes only `judge.image_tag` (`21a26db29432` → `junit-coverage-v2`).

**Deliberately excluded:** `proposedrepairs/reporting-shared-hooks/` patches `src/schemathesis/pytest/plugin.py` of a candidate *implementation*. It is not a judge or scorer file, so it is not part of v2. It appears only as an input to the paired run (inside `fullref`).

**Score compatibility:** v2 scores are not comparable with v1 when Phase 2 or Phase 5 is partially passed. Phase 5 has 12 tests instead of 10. The untouched starter rises from 0.020 to 0.025 because the new allow/deny cases check generator behavior it already has. Fully correct submissions score 1.0 in both versions.

**Paired evaluation:** [paired/results.md](paired/results.md). The complete accepted implementation stays at 1.0. Three single-line plausibly-wrong mutants each keep 1.0 under v1 and lose points under v2:

| Mutant | v2 delta |
|---|---|
| dropped JUnit error | −1/70 |
| missing BODY fix | −1/120 |
| over-suppression | −1/60 |

**Limits:** the inherited phase-4 count floor quirk (9 expected, 11 collected) is unchanged. Only one complete implementation was available. The original task and images are untouched.

## Build

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t ebv/schemathesis_reporting_observability-judge:v2 .
```

`materialize.sh` takes the following steps:

1. Pull the pinned image(s) by digest, unless already present.
2. Extract the original files with `docker create` and `docker cp`. No container runs in this step.
3. Check each original against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of every file under `files/` (and `orig/`) against `source-lock.json` → `materialize.outputs`. Any mismatch fails loudly.

After that, the `Dockerfile` builds without changes. Regenerated files keep the file mode they have in the image.
See `../MATERIALIZE-CHECK.md` for how each package was verified.
