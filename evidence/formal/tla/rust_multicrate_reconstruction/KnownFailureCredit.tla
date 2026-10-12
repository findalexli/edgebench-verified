---------------------------- MODULE KnownFailureCredit ----------------------------
(* Model of judge/tools/score.py run_crate_test() per-crate counting, lines 282-336
   (sha256 d725dd93...b35), for ONE crate after a successful compile.

   Source -> model mapping
     outcome[t]          libtest line "test <t> ... ok|FAILED|ignored", or "absent"
                         (test not compiled into the binary; no line printed).
     passed0 / failed0   sums of "N passed;" / "N failed;" from "test result:" lines
                         (= #ok / #FAILED; ignored tests count in neither).
     discovered          max(#listed tests, EXPECTED_TOTALS[crate]); here
                         Expected = N means absent tests become failures via
                         the gap; Expected < N models a workspace with extra tests.
     Ex                  KNOWN_FAILURES[crate] (cas-pty: one name, cas-cli: one name).
     Collide             TRUE models cas-pty, where the exempt name
                         "pty::tests::test_pty_config_claude_with_teams" is a
                         substring of the always-printed public test line
                         "pty::tests::test_pty_config_claude_with_teams_lead"
                         (test 2 here when Collide).
     Original credit     `if known and failed > 0: for name in known:
                            if name in stdout: failed -= 1; passed += 1`
                         "name in stdout" = e printed (any result) or collision.
     Corrected credit    proposedrepairs/rust-known-failure-credit/repair.patch
                         (cas-pty branch): credit only if e's exact path had
                         result FAILED and failed > 0 (rechecked per name).
     status              "PASS" iff failed = 0 and total > 0; executed = 0 is the
                         TEST_CRASH branch (never PASS).
   Omitted: compile failure / timeout / crash branches (they never report PASS),
   public/hidden bucket bookkeeping (not used by the score), multi-binary output,
   the scalar layer weighting (see review). *)
EXTENDS Integers, FiniteSets

CONSTANTS N, MaxEx, Mode, Expected   \* Expected = EXPECTED_TOTALS[crate]   \* Mode \in {"original", "corrected"}

Tests    == 1..N
Outcomes == {"ok", "FAILED", "ignored", "absent"}

VARIABLES outcome, Ex, Collide
vars == <<outcome, Ex, Collide>>

Printed(t) == outcome[t] # "absent"
Count(r)   == Cardinality({t \in Tests : outcome[t] = r})

passed0    == Count("ok")
failed0    == Count("FAILED")
Listed     == Cardinality({t \in Tests : Printed(t)})
discovered == IF Listed > Expected THEN Listed ELSE Expected

InStdout(e) == Printed(e) \/ (Collide /\ e # 2 /\ Printed(2))

\* Apply the credit loop over the exempt names in a fixed order.
RECURSIVE Credit(_, _, _)
Credit(S, p, f) ==
  IF S = {} THEN <<p, f>>
  ELSE LET e == CHOOSE x \in S : \A y \in S : x <= y
           fire == IF Mode = "original"
                     THEN InStdout(e)                       \* guard `failed>0` checked once, before loop
                     ELSE f > 0 /\ outcome[e] = "FAILED"
       IN IF fire THEN Credit(S \ {e}, p + 1, f - 1) ELSE Credit(S \ {e}, p, f)

AfterCredit == IF Ex # {} /\ failed0 > 0 THEN Credit(Ex, passed0, failed0)
                                         ELSE <<passed0, failed0>>
passed1   == AfterCredit[1]
failed1   == AfterCredit[2]
executed  == passed1 + failed1
total     == IF discovered > executed THEN discovered ELSE executed
failedRep == IF total > executed THEN failed1 + (total - executed) ELSE failed1
\* executed = passed0 + failed0 (credit conserves the sum), so executed = 0 implies
\* no FAILED line, returncode 0, and the TEST_CRASH branch is not taken.
status    == IF failedRep = 0 /\ total > 0 THEN "PASS" ELSE "TEST_FAIL"

Init == /\ outcome \in [Tests -> Outcomes]
        /\ Ex \in {S \in SUBSET Tests : Cardinality(S) <= MaxEx}
        /\ Collide \in BOOLEAN
        /\ Collide => (N >= 2 /\ 2 \notin Ex)
Next == UNCHANGED vars
Spec == Init /\ [][Next]_vars

\* Reported PASS => every non-exempt test passed.
PassSound == status = "PASS" => \A t \in Tests \ Ex : outcome[t] = "ok"
\* Credited passes never exceed true passes plus exempt tests that really FAILED.
CreditSound == passed1 <= passed0 + Cardinality({e \in Ex : outcome[e] = "FAILED"})
\* Same, restricted to runs where the exempt test printed no line of its own: any
\* violation here comes only from the substring collision.
PassSoundExemptSilent == (\A e \in Ex : ~Printed(e)) => PassSound
=============================================================================
