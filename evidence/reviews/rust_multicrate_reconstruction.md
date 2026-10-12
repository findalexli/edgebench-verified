# Review: `rust_multicrate_reconstruction`

Reviewer: Claude (critical re-verification), 2026-10-11. Scripts are in
`evidence/scripts/rust_multicrate_reconstruction/`. The model is in
`evidence/formal/tla/rust_multicrate_reconstruction/`.

## Claim under review

Earlier claim (verbatim): "A passing exempt test can cancel an unrelated failure, producing false
PASS. Real Cargo fixture evidence supports the decision; original-corpus frequency and the full
public/hidden suite remain unmeasured."

Earlier disposition: **Withhold original** (evidence/selected/rust-original-exclusion.json,
`ADOPT_EXACT_ORIGINAL_WITHHOLDING`). A component repair was accepted separately
(proposedrepairs/rust-known-failure-credit, rust-native-repair-acceptance.json: "five fixtures, ten
original/corrected outcomes"). No full replacement was certified.

## Pinned artifacts

| Item | Identity |
| --- | --- |
| Task JSON `tasks/rust_multicrate_reconstruction.json` | sha256 `9c6823f5874adf3b0a8d810b6801eda901f799cd0f5c964616010e61d8505173` |
| Judge image | `seededge/edgebench.judge.rust_multicrate_reconstruction@sha256:d1d18aed02e81e5f09938de0272a76a72fab174a784613aefa3eb51443f6e408` (pulled; cargo/rustc 1.88.0) |
| Source export `cloud-exports/rust_multicrate_reconstruction_nested-000.tar.gz` | `6d0192e53ef5485d91293a173a8c54613644b57a5873e77efea71188f7889b43` |
| `judge/tools/score.py` (original) | `d725dd934a01e40948267131d8ae91a075b4217d8012b41468cc9b38bb782b35` (equals the "original" identity in the repair manifest) |
| `judge/score.sh` | `4172f802fd37572f8ba2fb131fc151e96d872402ffeabc423618cd60757940af` |
| `judge/hidden-tests/split-manifest.json` | `68a4fcef6d196813d3f6fd46a23076398822562aaba3053af2ebaeb4e992cbcb` |
| `proposedrepairs/rust-known-failure-credit/repair.patch` | `700b66ca…8b82`. Applying it gives score.py `a28b3124…4b69`, which matches the manifest. |
| TLA+ module `KnownFailureCredit.tla` | `9dbc1bb615c9bd6ca0f6ec2c23ef6e6b0edf0a770070e0ad087cfd4ba4960502` |

## Contract

- agent_query: complete the Rust implementations in `agent-start/`. The hidden evaluator runs
  more tests "for the same public crate and CLI contracts".
- `agent-start/TASK.md`: "Do not edit Cargo.lock, vendored dependencies, task metadata, scoring
  scripts, or tests."
- Score (score.py `compute_score`, used directly as `total_score`; the rescale is linear over
  0..100). The score is a sum over 10 layers of `weight × layer_passed / layer_total`, where the
  counts are per-crate `passed`/`total` from the combined run (agent code + injected hidden tests).
  Weights are L0 13, L1 8, L2 10, **L3 4 (cas-pty 11 + cas-recording 29 tests)**, L4 15, L5 12,
  L6 15, L7 8, L8 5, **L9 10 (cas-cli 1344 tests)**.
- The crate `status` (PASS/TEST_FAIL) **does not enter the score**. It only sets the layer
  "worst" label and the `crate_*` detail rows.

## The counting code (score.py lines 282–336)

```python
passed, failed = 0, 0
for line in stdout.splitlines():
    if line.startswith("test result:"):
        ... if part == "passed;": passed += int(parts[i-1])
        ... elif part == "failed;": failed += int(parts[i-1])
    ...
known = KNOWN_FAILURES.get(crate_name, [])        # cas-pty: ["pty::tests::test_pty_config_claude_with_teams"]
if known and failed > 0:                          #  cas-cli: ["factory_mcp_ops_test"]
    for test_name in known:
        if test_name in stdout:                   # <-- substring of the whole stdout, any outcome
            failed -= 1
            passed += 1
            pub_passed += 1
            pub_failed = max(0, pub_failed - 1)
executed = passed + failed
total = max(discovered, executed); if total > executed: failed += total - executed
status = "PASS" if failed == 0 and total > 0 else "TEST_FAIL"
```

The bug in the arithmetic: the guard asks whether the exempt name *appears* in stdout, not
whether that test *FAILED*. libtest prints `test pty::tests::test_pty_config_claude_with_teams ... ok`
for a passing exempt test, so the name is always present. Whenever the crate has at least one
failure, one failure is converted into a pass, whatever the exempt test's own outcome. With the
exempt test passing and exactly one other test failing: `passed = 10, failed = 1` becomes
`passed = 11, failed = 0`, giving status PASS and 11/11 credited.

There is a second effect: the exempt name is also a substring of the *public* test
`pty::tests::test_pty_config_claude_with_teams_lead`, so the name appears even if the exempt
(hidden) test produced no line. The model shows this matters only when the exempt test produced no
output **and** the listed test count reaches `EXPECTED_TOTALS`. Hidden tests are injected, so in
normal runs this collision adds nothing beyond the main bug.

## Independent reproduction

### Real Cargo, original and corrected scorer component, in the pinned judge image

`scripts/rust_multicrate_reconstruction/run_native_fixture.sh` extracts the original `score.py` from
the pinned tarball, applies `repair.patch`, and then, inside the judge image with
`--network none --memory 4g --cpus 2`, calls the unmodified `run_crate_test(ws, "cas-pty", 300)`
of each version. That call runs real `cargo test --frozen -p cas-pty -- --list` and `cargo test`.
The fixture is a real crate named `cas-pty` with 11 tests: the 10 real cas-pty test names from
split-manifest.json, including `test_pty_config_claude_with_teams` and `…_with_teams_lead`, plus
one placeholder standing in for the 11th expected test. `FIXTURE_FAIL` selects which tests panic.
Output: `out/run.log`, `out/results.json`.

| Scenario (true failures) | Original | Corrected (patch) |
| --- | --- | --- |
| S1 all pass (0) | PASS 11/0 | PASS 11/0 |
| S2 only exempt fails (1) — intended exemption | PASS 11/0 | PASS 11/0 |
| **S3 exempt passes, `test_pty_config_default` fails (1)** | **PASS 11/0 (false)** | TEST_FAIL 10/1 |
| S4 exempt passes, two others fail (2) | TEST_FAIL 10/1 (one forgiven) | TEST_FAIL 9/2 |
| S5 exempt + one other fail (2) | TEST_FAIL 10/1 | TEST_FAIL 10/1 |
| S6 exempt passes, `…_with_teams_lead` fails (1) | **PASS 11/0 (false)** | TEST_FAIL 10/1 |

The same outcomes were obtained with the host cargo 1.95.0. The run independently reproduces the
earlier fixture result (original 11/0 PASS versus corrected 10/1 TEST_FAIL).

The shipped skeleton baseline (`judge/skeleton-score.json`) is consistent with the code. All cas-pty
tests panic on `todo!()`, and cas-pty is reported as `passed 1, failed 10`, with that one pass coming
from the exemption (in this case the exempt test really failed, so the credit is intended).

### Score effect (arithmetic)

For one crate result, a single spurious credit changes the task score by `weight / layer_total`:

- cas-pty: 4 / (11 + 29) = **+0.100 points** out of 100. This is the maximum per evaluation, because
  the configured list has one name.
- cas-cli: 10 / 1344 = **+0.0074 points** (if its substring rule ever forgives an unrelated failure).

So the maximum inflation from this defect is about **0.11 points on a 0–100 scale**, about 1 test
in 2,749. The crate-level "PASS" label can be wrong, but that label is not scored.

## Refutation attempts

1. *Is the trigger reachable by a real solver?* Yes, without any contrivance. The exempt test checks
   only `PtyConfig::claude(... Some(&teams))` argument construction, which an honest implementation
   can pass. Any other failing cas-pty test then fires the bug, for example `default()` left as
   `todo!()` or a spawn test that fails in the sandbox. No adversarial action is needed. It is an
   accounting error, not a reward-hacking vector.
2. *Is it material?* No. At most +0.1 points per run (above). It cannot change validity. It changes
   rankings only between runs within about 0.1 points.
3. *Could the substring collision (`…_teams_lead`) widen the effect?* Only for the narrow case where
   the exempt hidden test is missing and the listed count still reaches the expected total
   (model, below). It never adds more than the same single credit.
4. *cas-cli*: the exempt token `factory_mcp_ops_test` is an integration-test **file** name. Under
   libtest it appears in stdout essentially only through panic locations of failing tests in that
   file, so it mostly forgives a failure from that binary, as intended, capped at one. I did not run
   cas-cli natively. The earlier repair leaves it unchanged, which I agree with.

## Formal check (TLA+)

Model `formal/tla/rust_multicrate_reconstruction/KnownFailureCredit.tla`. The header comment gives
the source-to-model mapping. One crate after a successful compile. N = 4 tests, each with outcome
∈ {ok, FAILED, ignored, absent}. Exempt set `Ex` with |Ex| ≤ MaxEx ∈ {1, 2}. A `Collide` flag models
the `_lead` substring. `Expected` = EXPECTED_TOTALS. Original credit: `failed>0` checked once, then
`name in stdout`. Corrected credit: `failed>0 ∧ outcome[e] = FAILED`. All initial states are
enumerated (`Next` = stutter). Invariants:

- `PassSound`: status = PASS ⇒ every non-exempt test is `ok`.
- `CreditSound`: credited passes ≤ true passes + exempt tests that really FAILED.

TLC 2026.10.06 results (`tlc_*.out`, rerun with `run_tlc.sh`):

| Config (N=4, Expected=4) | Original | Corrected |
| --- | --- | --- |
| PassSound, MaxEx=1 | **violated**: `outcome=<<ok,ok,ok,FAILED>>, Ex={1}, Collide=FALSE` | holds (2,304 distinct states) |
| PassSound, MaxEx=2 | violated (same) | holds (4,608 states) |
| CreditSound, MaxEx=1 / 2 | violated (same state) | holds (2,304 / 4,608) |
| PassSoundExemptSilent (exempt test printed nothing) | holds | holds |
| same, Expected=3 (workspace has an extra test) | violated: `<<ok,ok,ok,absent>>, Ex={}` | violated (same) |

The first counterexample is exactly the claim: exempt test 1 passes, test 4 fails, status PASS.
The last row is a **different, out-of-scope property**. `discovered = max(listed, EXPECTED_TOTALS)`
lets an extra passing test hide a missing expected test, independent of exemptions and also
present in the corrected version. A solver can reach it only by editing tests, which TASK.md
forbids. I did not run it natively and do not count it as a finding.

What the model omits: the compile-fail, timeout and crash branches (none of them can report PASS),
public/hidden bucket bookkeeping (not scored), multiple test binaries and cargo stopping after the
first failing binary, and the layer weighting (handled in the arithmetic above). The bounds are
N = 4 and |Ex| ≤ 2. The defect does not depend on N. The violation needs only n = 2 tests.

## Verdict

**CONFIRMED-NARROWER.** The mechanism is exactly as claimed, now reproduced with real Cargo in the
pinned judge image and with an exhaustive bounded model. Its impact is narrow. It affects only the
crate status label and at most one test credit per crate: **≤ 0.1 points of 100** for cas-pty
(≈ 0.0074 for cas-cli). It is reachable by honest partial solutions.

## Disposition assessment

**I disagree with "withhold original".** VERIFICATION.md requires a specific evidenced reason for
exclusion. The reason here is real, but its maximum effect is a +0.1-point overstatement of the
score. It does not invalidate the task, the hidden suite, or any ranking separated by more than
0.1 points. Proportionate options:

- **Retain with a note**, disclosing that scores may be overstated by at most 0.1 points (cas-pty
  exemption). Or
- **Repair** with the one-line guard fix below, and rescore if artifacts exist. The shift is
  bounded and known: at most −0.1 per run.

A full-task native run, original-corpus frequency and reference controls are still missing, but
they are needed to certify a repaired *release*, not to justify withholding.

## Recommended publishable wording

"The original scorer exempts a known-failing cas-pty test by checking only whether its name appears
in the output. When that test passes, one unrelated cas-pty failure is credited as a pass instead.
This can mislabel the crate as PASS and raise the task score by at most 0.1 of 100 points. We correct
the guard to require that the exempt test itself failed."

## Repair note

The earlier patch is correct for cas-pty. In real Cargo and in the model it removes the false
credit (S3, S4 and S6 change) and keeps legitimate exemption credit (S2 and S5 unchanged). Its
re-check of `failed > 0` inside the loop and its routing of credit to the hidden or public bucket
are sound bookkeeping. The smallest correct fix is: collect the exact test paths whose result is
`FAILED`, and credit a known failure only if its exact path is in that set, keeping the `failed > 0`
guard. The patch keeps cas-cli's substring rule. That is acceptable: the token is a file name, the
effect is capped at 0.0074 points, and the rule is still documented as unresolved. Optional
hardening: anchor the cas-cli rule to the panic location of a failing test in that file.

## Limits

- The fixture uses the real cas-pty test names but not the real crate. I did not run the full
  `score.sh` or eval_cmd: this requires building the 14-crate workspace with hidden-test injection,
  and there is no reference implementation.
- Original-corpus frequency (how often real submissions hit S3/S4) remains unmeasured. Whatever it
  is, the impact is bounded by 0.1 points per run.
- cas-cli exemption behavior was not executed.
- Why `test_pty_config_claude_with_teams` is "known failing" (presumably in the reference
  implementation or the environment) was not established. This affects the interpretation of S2,
  not the bug.
