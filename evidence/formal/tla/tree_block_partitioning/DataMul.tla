---------------------------- MODULE DataMul ----------------------------
(* Statement-level model of Data::operator*=(const Data &x) from the T2 judge
   library  opt/p1_judge/prob/P1/T2_P7881/data/interactive_lib.cpp
   (sha256 0c57271b...c982).  Source-to-model mapping:
     if(is_id(x))return;              -> pc "chk_x"
     if(is_id( *this )){*this=x;return;}-> pc "chk_this"
     a+=x.a;                          -> pc "a"
     b^=x.b;                          -> pc "b"
     c=(c+1)*(x.c+1)-1;               -> pc "c"
     d=d*(x.c+1)+x.d;                 -> pc "d"
   Each C++ statement is one atomic step: its right-hand side is evaluated from
   the current memory and then stored, exactly as sequenced C++ does.  `this`
   and `x` are object identities T and X into a two-object memory, so T = X is
   the aliased call  v *= v  and T # X is the ordinary call.  Patched = TRUE
   executes the proposed repair (d assignment before c assignment).
   Omitted: the call counter t1 / 2e7 guard (does not touch fields), I/O, and
   unsigned short width: arithmetic is modulo M (M = 2^16 in the source; small
   power of two here).  Int promotion/signed overflow is not modelled.        *)
EXTENDS Naturals
CONSTANTS M, T, X, Patched
Objs   == {1, 2}
Fields == {"a", "b", "c", "d"}
Val    == 0..(M-1)
RECURSIVE Xor(_, _)
Xor(p, q) == IF p = 0 /\ q = 0 THEN 0
             ELSE (((p % 2) + (q % 2)) % 2) + 2 * Xor(p \div 2, q \div 2)
IsId(o) == o.a = 0 /\ o.b = 0 /\ o.c = 0 /\ o.d = 0
(* Abstract product stated by the library's formulas, on OLD values only:
   the value-semantics contract "x*=y sets x to x*y". *)
Spec(p, q) == IF IsId(q) THEN p ELSE IF IsId(p) THEN q ELSE
   [a |-> (p.a + q.a) % M, b |-> Xor(p.b, q.b),
    c |-> ((p.c + 1) * (q.c + 1) + M - 1) % M,
    d |-> (p.d * (q.c + 1) + q.d) % M]
Order == IF Patched THEN <<"a", "b", "d", "c", "done">>
                    ELSE <<"a", "b", "c", "d", "done">>
Next1(s) == CHOOSE i \in 1..4 : Order[i] = s
VARIABLES mem, init, pc
vars == <<mem, init, pc>>
Init == /\ mem \in [Objs -> [Fields -> Val]]
        /\ init = mem
        /\ pc = "chk_x"
Set(f, v) == mem' = [mem EXCEPT ![T][f] = v]
Step ==
  \/ /\ pc = "chk_x"
     /\ IF IsId(mem[X]) THEN pc' = "done" ELSE pc' = "chk_this"
     /\ UNCHANGED <<mem, init>>
  \/ /\ pc = "chk_this"
     /\ IF IsId(mem[T]) THEN /\ mem' = [mem EXCEPT ![T] = mem[X]] /\ pc' = "done"
                        ELSE /\ pc' = Order[1] /\ UNCHANGED mem
     /\ UNCHANGED init
  \/ /\ pc \in Fields
     /\ LET t == mem[T]  x == mem[X] IN
          CASE pc = "a" -> Set("a", (t.a + x.a) % M)
            [] pc = "b" -> Set("b", Xor(t.b, x.b))
            [] pc = "c" -> Set("c", ((t.c + 1) * (x.c + 1) + M - 1) % M)
            [] pc = "d" -> Set("d", (t.d * (x.c + 1) + x.d) % M)
     /\ pc' = Order[Next1(pc) + 1]
     /\ UNCHANGED init
Done == pc = "done" /\ UNCHANGED vars
Next == Step \/ Done
SpecF == Init /\ [][Next]_vars
(* Correctness: on return, *this holds the monoid product of the OLD values. *)
ResultCorrect == pc = "done" => mem[T] = Spec(init[T], init[X])
(* Frame: a distinct right operand is never written. *)
FrameOK == (pc = "done" /\ T # X) => mem[X] = init[X]
TypeOK == mem \in [Objs -> [Fields -> Val]]
=============================================================================
