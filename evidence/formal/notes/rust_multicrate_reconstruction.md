# rust_multicrate_reconstruction: formal note

## Claim
In the original grader, a passing exempt test can turn one unrelated failure in the same crate into
a pass, so the crate is reported PASS while a test failed. With the one-condition fix (credit the
exemption only if the exempt test itself failed), this cannot happen.

## Model and link to the code
TLA+: `evidence/formal/tla/rust_multicrate_reconstruction/KnownFailureCredit.tla` (sha256
9dbc1bb6…0502), checked with TLC (`run_tlc.sh`, outputs `tlc_*.out`).
- The module header maps the model to `judge/tools/score.py` `run_crate_test`, lines 282-336
  (sha256 d725dd93…2b35): the `N passed;` / `N failed;` sums, `discovered = max(listed,
  EXPECTED_TOTALS)`, the `KNOWN_FAILURES` loop (`if name in stdout`) and the PASS rule.
- One crate after a successful compile; N = 4 tests, each ok, FAILED, ignored or absent; up to 1
  (`ex1`) or 2 (`ex2`) exempt tests; `Collide` models the cas-pty name that is a substring of
  `…_with_teams_lead`.
- The corrected rule follows the earlier patch `proposedrepairs/rust-known-failure-credit/repair.patch`
  (not in this repository). The same rule is now the cas-pty branch of the exemption change in the
  fixed version (`repairs/rust_multicrate_reconstruction-v2/repair.patch`, `score.py` hunk at line
  299: credit only if the excused test's path is among the FAILED results).

## Result
**Model-checked (bounded).**
- Original grader: `PassSound` and `CreditSound` are violated (`tlc_original_ex1_*`,
  `tlc_original_ex2_*`). Counterexample: `outcome = <<ok,ok,ok,FAILED>>, Ex = {1}`: the exempt test
  passes, another fails, and the crate status is PASS.
- Corrected grader: both hold, 2,304 distinct states with `ex1` and 4,608 with `ex2`.
These runs set the expected-test count equal to N = 4.

## Counter-check
- `PassSoundExemptSilent_expected3` (expected count 3, N = 4) is violated on both graders: a crate
  with one test absent and an extra passing test reports PASS. This is the separate "extra test
  hides a missing test" property described on the case page, not the exemption bug.

## What the model covers in the fixed version (2026-10-12)
The fixed version corrects four defects (see the case page). This model covers one of them, the
exemption rule. It does not cover the other three, which were settled by paired runs of the task's
`eval_cmd`, not by a model:
- hidden tests placed where they do not compile (cas-cli, cas-search);
- Cargo stopping at the first failing test binary (`--no-fail-fast` in the fixed version);
- the four vendored `cc` files missing from the published archive.

## Limits
- Bounded: 4 tests, at most 2 exempt tests.
- Left out: compile-fail, timeout and crash branches, multiple test binaries (including Cargo
  stopping at the first failing binary, which the original `score.py` does not prevent and the
  fixed version does), the public/hidden bookkeeping and the layer weighting.
- The exemption's score effect (at most 0.100 points from cas-pty and 0.0074 from cas-cli) is
  arithmetic on the layer weights, not part of the model.
