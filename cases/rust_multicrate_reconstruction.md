# Rust Multicrate Reconstruction (`rust_multicrate_reconstruction`)

**Outcome:** Kept, with a note. <mark>When an excused test passes, one unrelated failure can be credited as a pass, which raises the score by at most 0.1 points out of 100.</mark>

## What the task asks

The task says: "Complete the missing Rust implementations in the unpacked CAS workspace." It adds that "the hidden evaluator runs additional tests for the same public crate and CLI contracts". A crate is a Rust package; the workspace has 14 of them.

The score is a weighted sum over 10 layers, where each layer contributes `passed / total` of its tests. The cas-pty and cas-recording crates make up layer L3, weighted 4 across 40 tests. The cas-cli crate makes up layer L9, weighted 10 across 1344 tests. Category: Systems & Software Engineering.

## What we checked

**Rule.** The grader excuses one known-failing test per crate. When a crate has at least one failure, the grader converts one failure into a pass if the excused test's name appears anywhere in the test output. It does not check whether that test actually failed.

**Example.** The excused test passes and one unrelated cas-pty test (`test_pty_config_default`) fails. The expected result is TEST_FAIL with 10 passed and 1 failed. The original grader reports PASS with 11 passed and 0 failed.

**Why it matters.** An honest, partly finished solution can trigger this. The excused test only checks how arguments are built, so a genuine implementation can pass it while another cas-pty test still fails. The crate-level PASS label can be wrong, but that label does not enter the score.

A separate property is not counted as a finding: an extra passing test can hide a missing expected test. It exists in both the original and the corrected grader, and a solver could reach it only by editing tests, which the task forbids.

## How much it matters

- One wrong credit in cas-pty adds 4 / (11 + 29) = **+0.100 points** out of 100. That is the cap per grading.
- The cas-cli exemption could add at most +0.0074 points if it ever forgave an unrelated failure.
- Only solvers whose cas-pty crate passes the excused test while failing another cas-pty test are affected. Rankings separated by more than 0.1 points are unaffected.

**Note shipped with the task.** The original grader excuses a known-failing cas-pty test by checking only whether its name appears in the output. When that test actually passes, one unrelated cas-pty failure is credited as a pass instead. Task scores may therefore be overstated by at most 0.1 points out of 100. A one-condition fix exists: credit the exemption only if the excused test itself failed. It is checked on the test crate and in the model below, and shifts a score by at most −0.1 per run.

The task does not change; the note above ships with it.

## How we checked it

- **Original grader.** Real Cargo (cargo/rustc 1.88.0) ran in the original public image, pinned by digest. It called the unmodified `run_crate_test` from both the original grader and the corrected grader (with the one-condition fix). The test crate is a real crate named `cas-pty` with 11 tests: the 10 real cas-pty test names plus one placeholder. Six failure scenarios:

| Scenario (true failures) | Original grader | Corrected grader (patch) |
| --- | --- | --- |
| S1 all pass (0) | PASS 11/0 | PASS 11/0 |
| S2 only excused test fails (1) — intended exemption | PASS 11/0 | PASS 11/0 |
| **S3 excused test passes, `test_pty_config_default` fails (1)** | **PASS 11/0 (false)** | TEST_FAIL 10/1 |
| S4 excused test passes, two others fail (2) | TEST_FAIL 10/1 (one forgiven) | TEST_FAIL 9/2 |
| S5 excused test + one other fail (2) | TEST_FAIL 10/1 | TEST_FAIL 10/1 |
| S6 excused test passes, `…_with_teams_lead` fails (1) | **PASS 11/0 (false)** | TEST_FAIL 10/1 |

- **Formal check (TLA+).** TLA+ is a language for describing a system's behaviour, and its checker TLC explores every reachable state. A bounded model, `KnownFailureCredit.tla`, was checked with TLC. It covers 4 tests, each ok, FAILED, ignored or absent, with up to 2 excused tests. It checks the invariants `PassSound` and `CreditSound` (properties that must hold in every state). On the original grader both invariants fail. The counterexample is `outcome=<<ok,ok,ok,FAILED>>, Ex={1}`: the excused test passes, another fails, and the crate status is PASS. On the corrected grader both hold: 2,304 distinct states with up to 1 excused test and 4,608 with up to 2.
- **Arithmetic.** The score effect follows from the layer weights above.

## Limits

- No AI model or solver was run. The effects shown are only on test submissions and counterexamples we wrote, and no leaderboard impact is estimated.
- The test crate uses the real cas-pty test names but not the real crate.
- The full `score.sh` and `eval_cmd` were not run. Building the 14-crate workspace with the hidden tests added would need a reference implementation, and none exists.
- How often real submissions hit S3 or S4 was not measured.
- The cas-cli exemption was not run on the real image.
- Why `test_pty_config_claude_with_teams` is listed as known-failing was not established.
- The TLA+ model is bounded (4 tests, at most 2 excused). It leaves out compile-fail, timeout and crash branches, multiple test binaries and the layer weighting.

## Reproduce

- Real-Cargo test crate, original against corrected grader: `evidence/scripts/rust_multicrate_reconstruction/run_native_fixture.sh` (outputs in `out/run.log` and `out/results.json`)
- TLA+ model: `evidence/formal/tla/rust_multicrate_reconstruction/run_tlc.sh` (outputs in `tlc_*.out`)
- Pinned identity: grader image `seededge/edgebench.judge.rust_multicrate_reconstruction@sha256:d1d18aed02e81e5f09938de0272a76a72fab174a784613aefa3eb51443f6e408`; `judge/tools/score.py` sha256 `d725dd934a01e40948267131d8ae91a075b4217d8012b41468cc9b38bb782b35`.

Supporting records: `evidence/reviews/rust_multicrate_reconstruction.md`.
