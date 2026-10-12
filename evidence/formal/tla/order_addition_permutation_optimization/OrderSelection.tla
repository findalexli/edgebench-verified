----------------------- MODULE OrderSelection -----------------------
(* Run-level model of best-submission selection for the EdgeBench task
   order_addition_permutation_optimization, original (v1) and fixed (v2)
   graders side by side on the same submission sequence.

   Code modelled
   -------------
   (1) Grader: /home/workspace/complex_job_scheduling/tests/test_final_result.py
       in judge image seededge/edgebench.judge.order_addition_permutation_optimization
       @sha256:6d1a1506...7fbd8.  Original sha256 4f1d5fad...01cc (6265 B);
       fixed sha256 37e7bae6...77bd3 (6265 B).  The only difference is line 18,
       EXPECTED_SCORE_HELPER_SHA256 (3023b9a4... -> 337837af..., the installed
       helper's real hash).  Five tests, independent under pytest:
         T1 test_no_private_cost_module_access    l.74-91  (on failure prints TOTAL_SCORE 0)
         FP test_private_judge_files_are_available l.94-98  (v1: always fails, l.98;
                                                             v2: always passes)
         T3 test_baseline_file_was_not_modified    l.101-110
         T4 test_final_result_exists_and_has_required_fields l.113-123
         T5 test_final_result_is_valid_permutation_and_cost  l.126-144
            (prints TOTAL_SCORE <score> only if every assert passes, l.143-144)
       A submission is abstracted to the set p of non-FP tests it passes plus
       the score value sc it would print in T5.  Its pass count is |p| (v1) or
       |p|+1 (v2): FP is the only test whose outcome the patch changes, and FP
       does not read the submission (it hashes files under tests/, which is
       excluded from submissions).
   (2) Report: sforge/harness/grading.py _grade_legacy (parser pytest_v):
       pass_rate = passed/total; score = the single TOTAL_SCORE line or None;
       two TOTAL_SCORE lines (T1 fails AND T5 passes) raise in extract_score
       (l.91-92), so that submission yields no rankable entry -> "Excluded".
   (3) Selection: sforge/harness/selection.py (sha256 3338ed24...2fba),
       _pass_rate_first l.86-103 -> PRF below, _score_first l.106-117 -> SF.
       PRF: better = not best_valid or rate > best_rate            (l.96)
            if rate == best_rate == 1.0 and score is not None:
                better = score > best_score                           (l.97-98)
            best_score := score if score is not None else rate        (l.100)
       Rates k/5 are compared through k (float k/5 is strictly monotone in k
       and k/5 == 1.0 iff k = 5).  best_score is kept as a tagged value
       [rate |-> TRUE/FALSE, v |-> ...] so the "rate used as score" fallback of
       l.100 is visible.  Scores are abstract integers 1..MaxScore (higher is
       better, task direction "maximize"); 0 is the T1-violation score.
   The task's policy is judge.selection = "pass_rate_first" (task.json.in).
   SF models the "best so far by score" consumer (policy score_first).    *)
EXTENDS Integers, FiniteSets, Sequences

CONSTANTS N,         \* maximum number of submissions in a run
          MaxScore   \* abstract score values 1..MaxScore

Tests  == {"T1", "T3", "T4", "T5"}       \* the non-fingerprint tests
Scores == 1..MaxScore
NONE   == -1                             \* Python None (scores are >= 0)

\* A submission: tests passed (other than FP) and the score T5 would print.
Subs == {[p |-> q, sc |-> s] : q \in SUBSET Tests, s \in Scores}

Excluded(x)   == "T1" \notin x.p /\ "T5" \in x.p        \* two TOTAL_SCORE lines
Valid(x)      == x.p = Tests                            \* meets the task contract
PassCount(x, fixed) == Cardinality(x.p) + (IF fixed THEN 1 ELSE 0)
ScoreOf(x)    == IF "T5" \in x.p THEN x.sc
                 ELSE IF "T1" \notin x.p THEN 0 ELSE NONE

NoBest == [valid |-> FALSE, k |-> 0, bs |-> [rate |-> FALSE, v |-> NONE], round |-> 0]

\* One step of _pass_rate_first (selection.py l.89-102) for entry i.
PRFStep(b, x, i, fixed) ==
  IF Excluded(x) THEN b ELSE
  LET k  == PassCount(x, fixed)
      s  == ScoreOf(x)
      better0 == ~b.valid \/ k > b.k
      better  == IF k = b.k /\ b.k = 5 /\ s # NONE
                 THEN (b.bs.v = NONE \/ s > b.bs.v)   \* _is_better_score
                 ELSE better0
  IN IF better
     THEN [valid |-> TRUE, k |-> k, round |-> i,
           bs |-> IF s # NONE THEN [rate |-> FALSE, v |-> s]
                              ELSE [rate |-> TRUE, v |-> k]]   \* v = rate*5
     ELSE b

\* One step of _score_first (selection.py l.109-116).
SFStep(b, x, i) ==
  IF Excluded(x) \/ ScoreOf(x) = NONE THEN b
  ELSE IF b.bs.v = NONE \/ ScoreOf(x) > b.bs.v
       THEN [valid |-> TRUE, k |-> Cardinality(x.p), round |-> i,
             bs |-> [rate |-> FALSE, v |-> ScoreOf(x)]]
       ELSE b

VARIABLES hist, prf1, prf2, sf1, sf2, mixed
vars == <<hist, prf1, prf2, sf1, sf2, mixed>>

Init == hist = <<>> /\ prf1 = NoBest /\ prf2 = NoBest
        /\ sf1 = NoBest /\ sf2 = NoBest /\ mixed = FALSE

Submit == /\ Len(hist) < N
          /\ \E x \in Subs :
               LET i == Len(hist) + 1 IN
               /\ hist' = Append(hist, x)
               /\ prf1' = PRFStep(prf1, x, i, FALSE)
               /\ prf2' = PRFStep(prf2, x, i, TRUE)
               /\ sf1'  = SFStep(sf1, x, i)
               /\ sf2'  = SFStep(sf2, x, i)
               \* would l.98 compare a score against a rate-valued best_score?
               /\ mixed' = (mixed \/ (~Excluded(x) /\ ScoreOf(x) # NONE
                                       /\ PassCount(x, TRUE) = 5 /\ prf2.k = 5
                                       /\ prf2.bs.rate))
Next == Submit
Spec == Init /\ [][Next]_vars

\* ---- derived sets over the history ----
Idx       == 1..Len(hist)
ValidIdx  == {i \in Idx : Valid(hist[i])}
ScoredIdx == {i \in Idx : ~Excluded(hist[i]) /\ ScoreOf(hist[i]) # NONE}
Max(S)    == CHOOSE m \in S : \A y \in S : y <= m
Min(S)    == CHOOSE m \in S : \A y \in S : m <= y
BestValidScore == Max({hist[i].sc : i \in ValidIdx})
BestScored     == Max({ScoreOf(hist[i]) : i \in ScoredIdx})

\* ---- claims (must hold) ----
TypeOK == hist \in Seq(Subs) /\ Len(hist) <= N

\* C1 original: with any valid submission, the run's best is the FIRST valid one.
OrigFreezesAtFirstValid ==
  ValidIdx # {} => prf1.round = Min(ValidIdx)

\* C2 fixed: the run's best is the highest-scoring valid submission
\*    (earliest among equal scores), and best_score is that score, not a rate.
FixedPicksBestValid ==
  ValidIdx # {} =>
    /\ prf2.bs = [rate |-> FALSE, v |-> BestValidScore]
    /\ prf2.round = Min({i \in ValidIdx : hist[i].sc = BestValidScore})
    /\ prf2.k = 5

\* C3 the fix never makes l.98 compare a score with a rate-valued best_score.
NoMixedComparison == ~mixed

\* C4 score_first ("best so far by score") is the same under v1 and v2
\*    (by construction: SFStep never reads the pass count, the only thing the
\*    patch changes),
\*    and is the maximum score over all rankable scored submissions.
ScoreFirstUnchanged ==
  /\ sf1 = sf2
  /\ (ScoredIdx # {} => sf2.bs.v = BestScored)

\* C5 when every scored submission is valid, fixed pass_rate_first and
\*    score_first report the same best score.
FixedMatchesScoreFirstOnValidRuns ==
  (ValidIdx # {} /\ ScoredIdx = ValidIdx) => prf2.bs.v = sf2.bs.v

Claims == OrigFreezesAtFirstValid /\ FixedPicksBestValid /\ NoMixedComparison
          /\ ScoreFirstUnchanged /\ FixedMatchesScoreFirstOnValidRuns

\* ---- counter-checks (must be VIOLATED) ----
\* K1 too strong for v1: the original also picks the best valid score.
OrigPicksBestValid == ValidIdx # {} => prf1.bs.v = BestValidScore
\* K2 too strong for v2: whenever pass_rate_first reports a real score, it
\*    equals score_first's.  Fails because score_first also ranks scored but
\*    contract-violating submissions (e.g. baseline file modified: T3 fails,
\*    T5 still prints TOTAL_SCORE).
FixedEqualsScoreFirst == ~prf2.bs.rate => prf2.bs.v = sf2.bs.v
\* K3 best_score is never a pass rate standing in for a score (fails in both
\*    versions: a run with only score-less submissions reports its pass rate).
NeverRateAsScore == prf2.bs.rate = FALSE
=============================================================================
