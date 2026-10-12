# Rust Multicrate Reconstruction (`rust_multicrate_reconstruction`)

**Decision:** Retain with note. A passing exempt test can cause one unrelated failure to be credited as a pass, which raises the score by at most 0.1 of 100 points.

## What the task asks for

The task says: "Complete the missing Rust implementations in the unpacked CAS workspace." It adds that "the hidden evaluator runs additional tests for the same public crate and CLI contracts". The score is a weighted sum over 10 layers, where each layer contributes `passed / total` of its tests. The cas-pty and cas-recording crates make up layer L3, weighted 4 across 40 tests. The cas-cli crate makes up layer L9, weighted 10 across 1344 tests. Category: Systems & Software Engineering.

## What goes wrong

**Rule.** The scorer has a known-failure exemption. When a crate has at least one failure, the scorer converts one failure into a pass if the exempt test's name appears anywhere in the test output. It does not check whether that test actually failed.

**Example.** The exempt test passes and one unrelated cas-pty test (`test_pty_config_default`) fails. The expected result is TEST_FAIL with 10 passed and 1 failed. The original scorer reports PASS with 11 passed and 0 failed.

**Why it matters.** An honest partial solution can trigger this. The exempt test only checks argument construction, so a genuine implementation can pass it while another cas-pty test still fails. The crate-level PASS label can be wrong, but that label does not enter the score.

A separate property is not counted as a finding: an extra passing test can hide a missing expected test. It exists in both the original and the corrected scorer, and a solver could reach it only by editing tests, which the task forbids.

## Impact

- One spurious credit in cas-pty adds 4 / (11 + 29) = **+0.100 points** of 100. That is the cap per evaluation.
- The cas-cli exemption could add at most +0.0074 points if it ever forgave an unrelated failure.
- Only solvers whose cas-pty crate passes the exempt test while failing another cas-pty test are affected. Rankings separated by more than 0.1 points are unaffected.

**Note shipped with the task.** The original scorer exempts a known-failing cas-pty test by checking only whether its name appears in the output. When that test actually passes, one unrelated cas-pty failure is credited as a pass instead. Task scores may therefore be overstated by at most 0.1 of 100 points. A one-guard fix exists: credit the exemption only if the exempt test itself failed. It is validated on the fixture and in the model below, and shifts a score by at most −0.1 per run.

## Fix (v2)

No change; the note above ships with the task.

## How we know

- **Original evaluator in the pinned image.** Real Cargo (cargo/rustc 1.88.0) in the judge image `sha256:d1d18aed02e8`, calling the unmodified `run_crate_test` from both the original scorer and the one-guard corrected scorer. The fixture is a real crate named `cas-pty` with 11 tests: the 10 real cas-pty test names plus one placeholder. Six failure scenarios:

| Scenario (true failures) | Original | Corrected (patch) |
| --- | --- | --- |
| S1 all pass (0) | PASS 11/0 | PASS 11/0 |
| S2 only exempt fails (1) — intended exemption | PASS 11/0 | PASS 11/0 |
| **S3 exempt passes, `test_pty_config_default` fails (1)** | **PASS 11/0 (false)** | TEST_FAIL 10/1 |
| S4 exempt passes, two others fail (2) | TEST_FAIL 10/1 (one forgiven) | TEST_FAIL 9/2 |
| S5 exempt + one other fail (2) | TEST_FAIL 10/1 | TEST_FAIL 10/1 |
| S6 exempt passes, `…_with_teams_lead` fails (1) | **PASS 11/0 (false)** | TEST_FAIL 10/1 |

- **Formal check (TLA+).** A bounded model, `KnownFailureCredit.tla`, checked with TLC. It covers 4 tests, each ok, FAILED, ignored or absent, with up to 2 exempt tests, and checks the invariants `PassSound` and `CreditSound`. On the original scorer both invariants fail; the counterexample is `outcome=<<ok,ok,ok,FAILED>>, Ex={1}` (the exempt test passes, another fails, the crate status is PASS). On the corrected scorer both hold: 2,304 distinct states with up to 1 exempt test and 4,608 with up to 2.
- **Arithmetic.** The score effect follows from the layer weights above.

## Limits

- No model or solver was run. The effects shown are on authored controls and counterexamples only, and no leaderboard impact is estimated.
- The fixture uses the real cas-pty test names but not the real crate.
- The full `score.sh` and `eval_cmd` were not run. Building the 14-crate workspace with hidden-test injection would need a reference implementation, and none exists.
- How often real submissions hit S3 or S4 was not measured.
- The cas-cli exemption was not executed natively.
- Why `test_pty_config_claude_with_teams` is listed as known-failing was not established.
- The TLA+ model is bounded (4 tests, at most 2 exempt). It omits compile-fail, timeout and crash branches, multiple test binaries and the layer weighting.

## Reproduce

- Real-Cargo fixture, original vs corrected: `evidence/scripts/rust_multicrate_reconstruction/run_native_fixture.sh` (outputs in `out/run.log` and `out/results.json`)
- TLA+ model: `evidence/formal/tla/rust_multicrate_reconstruction/run_tlc.sh` (outputs in `tlc_*.out`)
- Pinned identity: judge image `seededge/edgebench.judge.rust_multicrate_reconstruction@sha256:d1d18aed02e81e5f09938de0272a76a72fab174a784613aefa3eb51443f6e408`; `judge/tools/score.py` sha256 `d725dd934a01e40948267131d8ae91a075b4217d8012b41468cc9b38bb782b35`.

Supporting records: `evidence/reviews/rust_multicrate_reconstruction.md`.
