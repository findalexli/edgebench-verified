# Paired v1/v2 results: schemathesis_config_modernization

The E2B job `e2b/jobs/schemathesis_config_modernization-v2-paired` ran on worker `imckpa05ohtptx5g62b3e` for 123 s, finished with exit 0 and was killed after collection. It ran every variant through the full original `judge.eval_cmd` (`bash /tests/test.sh` plus the structured parser) in fresh `--network none` containers (2 CPU, 3 GiB):
- v1 is the pinned original judge `@sha256:ff71a766…`.
- v2 was built inside the worker from `../Dockerfile`.

The rescale is linear 0..1, so the normalized score equals the raw score. Raw table: `raw-summary.md`.

| Variant | Role | v1 score | v2 score | Delta | Phase 3 v1 → v2 |
|---|---|---|---|---|---|
| starter | untouched starter `/app` | 0.031466 | 0.031466 | 0 | 0/15 → 0/16 |
| identity | reviewer's correct Target 3 overlay (`metric` returns `func`) | 0.135313 | 0.135313 | **0** | 15/15 → 16/16 |
| wrapper | plausibly wrong: returns a `functools.wraps` forwarding wrapper | 0.135313 | 0.129063 | **−0.006250 (−1/160)** | 15/15 → 15/16 |
| no_register | invalid control: never registers | 0.115313 | 0.110313 | −0.005000 | 12/15 → 12/16 |

The only test-function difference in every variant is the added `test_metric_decorator_preserves_exact_function_identity` (the phase summary item `test_phase_3` follows it for the failing variants). It passes for identity and fails for wrapper, no_register and starter. All 132 original items keep their v1 outcome. The wrapper also loses the phase-3 "all passed" flag.

- **Trigger:** v1 scores the wrapper the same as the correct overlay. v2 docks exactly 1/160. Holds.
- **Valid control:** the identity score is unchanged. Holds. No shipped reference exists in the image; the earlier native reference run (16/16, 0.135313, `evidence/selected/schemathesis-native-repair-comparison.json`) agrees.
- **Invalid control:** no_register is rejected in both versions (12/15 and 12/16). Holds.

Note: `paired/run.sh` differs from the executed job script in one line only. The `/tests` hash listing was fixed to run through `bash -c`, because the executed version wrote empty hash files. v2 test hashes were verified separately on a local build: `v2-image-tests.sha256`, matching `../source-lock.json`.

## Verdict

**Accepted.** The correct identity-preserving overlay keeps its score (0.135313 in both versions).
The plausibly wrong wrapper loses exactly the new identity test (−1/160). The invalid `no_register`
control fails in both versions. The starter is unchanged.
