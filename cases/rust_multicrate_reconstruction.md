# Rust Multicrate Reconstruction (`rust_multicrate_reconstruction`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Systems & Software Engineering
- **Decision:** Retain with note. A passing exempt test can cause one unrelated failure to be credited as a pass, which raises the score by at most 0.1 of 100 points[^2].

## What the task promises

The task says: "Complete the missing Rust implementations in the unpacked CAS workspace." It adds that "the hidden evaluator runs additional tests for the same public crate and CLI contracts". The score is a weighted sum over 10 layers, where each layer contributes `passed / total` of its tests. The cas-pty and cas-recording crates make up layer L3, weighted 4 across 40 tests. The cas-cli crate makes up layer L9, weighted 10 across 1344 tests.

## What we checked and how

- **Source reading.** We read the scorer's known-failure exemption. When a crate has at least one failure, the scorer converts one failure into a pass if the exempt test's name appears anywhere in the test output. It does not check whether that test actually failed.
- **Native run with real Cargo.** We ran this in the pinned judge image (cargo/rustc 1.88.0, `--network none --memory 4g --cpus 2`), calling the unmodified `run_crate_test` from both the original scorer and the corrected scorer.
  - The fixture was a real crate named `cas-pty` with 11 tests: the 10 real cas-pty test names plus one placeholder.
  - We ran six failure scenarios. The reviewer reports that host cargo 1.95.0 gave the same outcomes; that host run's output is not saved.
- **Exhaustive bounded model.** We built a TLA+ model (`KnownFailureCredit.tla`) and checked it with TLC 2026.10.06. It covers 4 tests, each of which can be ok, FAILED, ignored or absent, with up to 2 exempt tests. It checks the invariants `PassSound` and `CreditSound`.
- **Arithmetic.** We worked out the score effect from the layer weights.
- **Original identity.**
  - Judge image: `seededge/edgebench.judge.rust_multicrate_reconstruction@sha256:d1d18aed02e81e5f09938de0272a76a72fab174a784613aefa3eb51443f6e408`.
  - `judge/tools/score.py` sha256 `d725dd934a01e40948267131d8ae91a075b4217d8012b41468cc9b38bb782b35`.
  - `judge/hidden-tests/split-manifest.json` sha256 `68a4fcef6d196813d3f6fd46a23076398822562aaba3053af2ebaeb4e992cbcb`.
  - Task JSON sha256 `9c6823f5874adf3b0a8d810b6801eda901f799cd0f5c964616010e61d8505173`.

## What we found

**Confirmed, narrower.** The mechanism works exactly as the earlier claim described, but its effect is small. Results with real Cargo in the judge image:

| Scenario (true failures) | Original | Corrected (patch) |
| --- | --- | --- |
| S1 all pass (0) | PASS 11/0 | PASS 11/0 |
| S2 only exempt fails (1) — intended exemption | PASS 11/0 | PASS 11/0 |
| **S3 exempt passes, `test_pty_config_default` fails (1)** | **PASS 11/0 (false)** | TEST_FAIL 10/1 |
| S4 exempt passes, two others fail (2) | TEST_FAIL 10/1 (one forgiven) | TEST_FAIL 9/2 |
| S5 exempt + one other fail (2) | TEST_FAIL 10/1 | TEST_FAIL 10/1 |
| S6 exempt passes, `…_with_teams_lead` fails (1) | **PASS 11/0 (false)** | TEST_FAIL 10/1 |

**Example (S3).** The exempt test passes and one unrelated cas-pty test fails. The expected result is TEST_FAIL with 10 passed and 1 failed. The original scorer reports PASS with 11 passed and 0 failed.

**Who can hit this.** An honest partial solution can trigger it, with no adversarial action. The exempt test only checks argument construction, so a genuine implementation can pass it while another cas-pty test still fails.

**What the TLA+ model found.**
- On the original scorer, both invariants fail. The counterexample is `outcome=<<ok,ok,ok,FAILED>>, Ex={1}`: the exempt test passes, another test fails, and the crate status is PASS.
- On the corrected scorer, both invariants hold: 2,304 distinct states with up to 1 exempt test and 4,608 with up to 2.

**Maximum score effect.** One spurious credit in cas-pty adds 4 / (11 + 29) = **+0.100 points** of 100, and that is the cap per evaluation. The cas-cli exemption could add at most +0.0074 points if it ever forgave an unrelated failure. The crate-level PASS label can be wrong, but that label does not enter the score.

**Earlier withholding.** An earlier audit withheld this task because of this defect. Re-checking confirmed the mechanism. Its maximum effect, however, is a 0.1-point overstatement, which does not invalidate the task, the hidden suite or any ranking separated by more than 0.1 points.

**Not counted as a finding.** The model also found a separate property. An extra passing test can hide a missing expected test. That property exists in both versions, and a solver could reach it only by editing tests, which the task forbids.

## Note for users

No repair. The original scorer exempts a known-failing cas-pty test by checking only whether its name appears in the output. When that test actually passes, one unrelated cas-pty failure is credited as a pass instead. Task scores may therefore be overstated by at most 0.1 of 100 points. A one-guard fix exists: credit the exemption only if the exempt test itself failed. It is validated on the fixture and in the model above, and shifts a score by at most −0.1 per run.

## Limits and what was not run

- No model or solver was re-run. The effects shown are on authored controls and counterexamples only, and no leaderboard impact is estimated.
- The fixture uses the real cas-pty test names but not the real crate.
- The full `score.sh` and `eval_cmd` were not run. Building the 14-crate workspace with hidden-test injection would need a reference implementation, and none exists.
- How often real submissions hit S3 or S4 was not measured.
- The cas-cli exemption was not executed natively.
- Why `test_pty_config_claude_with_teams` is listed as known-failing was not established.
- The TLA+ model is bounded (4 tests, at most 2 exempt). It omits compile-fail, timeout and crash branches, multiple test binaries and the layer weighting.

## Reproduce

- Real-Cargo fixture, original vs corrected: `evidence/scripts/rust_multicrate_reconstruction/run_native_fixture.sh` (outputs in `out/run.log` and `out/results.json`)
- TLA+ model: `evidence/formal/tla/rust_multicrate_reconstruction/run_tlc.sh` (outputs in `tlc_*.out`)

Supporting records: `evidence/reviews/rust_multicrate_reconstruction.md`.

[^2]: The review's arithmetic section says "about 0.11 points on a 0–100 scale". That figure adds the cas-pty and cas-cli maxima. The review's verdict and `decisions.json` give "≤0.1/100", which is the cas-pty cap per evaluation. This page uses ≤0.1 as the coordinator's value and lists the cas-cli +0.0074 separately.
