---- MODULE DataMul_TTrace_1791793828 ----
EXTENDS Sequences, TLCExt, Toolbox, DataMul, Naturals, TLC

_expression ==
    LET DataMul_TEExpression == INSTANCE DataMul_TEExpression
    IN DataMul_TEExpression!expression
----

_trace ==
    LET DataMul_TETrace == INSTANCE DataMul_TETrace
    IN DataMul_TETrace!trace
----

_inv ==
    ~(
        TLCGet("level") = Len(_TETrace)
        /\
        init = (<<[a |-> 0, b |-> 0, c |-> 1, d |-> 1], [a |-> 0, b |-> 0, c |-> 0, d |-> 0]>>)
        /\
        pc = ("done")
        /\
        mem = (<<[a |-> 0, b |-> 0, c |-> 3, d |-> 1], [a |-> 0, b |-> 0, c |-> 0, d |-> 0]>>)
    )
----

_init ==
    /\ init = _TETrace[1].init
    /\ mem = _TETrace[1].mem
    /\ pc = _TETrace[1].pc
----

_next ==
    /\ \E i,j \in DOMAIN _TETrace:
        /\ \/ /\ j = i + 1
              /\ i = TLCGet("level")
        /\ init  = _TETrace[i].init
        /\ init' = _TETrace[j].init
        /\ mem  = _TETrace[i].mem
        /\ mem' = _TETrace[j].mem
        /\ pc  = _TETrace[i].pc
        /\ pc' = _TETrace[j].pc

\* Uncomment the ASSUME below to write the states of the error trace
\* to the given file in Json format. Note that you can pass any tuple
\* to `JsonSerialize`. For example, a sub-sequence of _TETrace.
    \* ASSUME
    \*     LET J == INSTANCE Json
    \*         IN J!JsonSerialize("DataMul_TTrace_1791793828.json", _TETrace)

=============================================================================

 Note that you can extract this module `DataMul_TEExpression`
  to a dedicated file to reuse `expression` (the module in the 
  dedicated `DataMul_TEExpression.tla` file takes precedence 
  over the module `DataMul_TEExpression` below).

---- MODULE DataMul_TEExpression ----
EXTENDS Sequences, TLCExt, Toolbox, DataMul, Naturals, TLC

expression == 
    [
        \* To hide variables of the `DataMul` spec from the error trace,
        \* remove the variables below.  The trace will be written in the order
        \* of the fields of this record.
        init |-> init
        ,mem |-> mem
        ,pc |-> pc
        
        \* Put additional constant-, state-, and action-level expressions here:
        \* ,_stateNumber |-> _TEPosition
        \* ,_initUnchanged |-> init = init'
        
        \* Format the `init` variable as Json value.
        \* ,_initJson |->
        \*     LET J == INSTANCE Json
        \*     IN J!ToJson(init)
        
        \* Lastly, you may build expressions over arbitrary sets of states by
        \* leveraging the _TETrace operator.  For example, this is how to
        \* count the number of times a spec variable changed up to the current
        \* state in the trace.
        \* ,_initModCount |->
        \*     LET F[s \in DOMAIN _TETrace] ==
        \*         IF s = 1 THEN 0
        \*         ELSE IF _TETrace[s].init # _TETrace[s-1].init
        \*             THEN 1 + F[s-1] ELSE F[s-1]
        \*     IN F[_TEPosition - 1]
    ]

=============================================================================



Parsing and semantic processing can take forever if the trace below is long.
 In this case, it is advised to uncomment the module below to deserialize the
 trace from a generated binary file.

\*
\*---- MODULE DataMul_TETrace ----
\*EXTENDS IOUtils, DataMul, TLC
\*
\*trace == IODeserialize("DataMul_TTrace_1791793828.bin", TRUE)
\*
\*=============================================================================
\*

---- MODULE DataMul_TETrace ----
EXTENDS DataMul, TLC

trace == 
    <<
    ([init |-> <<[a |-> 0, b |-> 0, c |-> 1, d |-> 1], [a |-> 0, b |-> 0, c |-> 0, d |-> 0]>>,pc |-> "chk_x",mem |-> <<[a |-> 0, b |-> 0, c |-> 1, d |-> 1], [a |-> 0, b |-> 0, c |-> 0, d |-> 0]>>]),
    ([init |-> <<[a |-> 0, b |-> 0, c |-> 1, d |-> 1], [a |-> 0, b |-> 0, c |-> 0, d |-> 0]>>,pc |-> "chk_this",mem |-> <<[a |-> 0, b |-> 0, c |-> 1, d |-> 1], [a |-> 0, b |-> 0, c |-> 0, d |-> 0]>>]),
    ([init |-> <<[a |-> 0, b |-> 0, c |-> 1, d |-> 1], [a |-> 0, b |-> 0, c |-> 0, d |-> 0]>>,pc |-> "a",mem |-> <<[a |-> 0, b |-> 0, c |-> 1, d |-> 1], [a |-> 0, b |-> 0, c |-> 0, d |-> 0]>>]),
    ([init |-> <<[a |-> 0, b |-> 0, c |-> 1, d |-> 1], [a |-> 0, b |-> 0, c |-> 0, d |-> 0]>>,pc |-> "b",mem |-> <<[a |-> 0, b |-> 0, c |-> 1, d |-> 1], [a |-> 0, b |-> 0, c |-> 0, d |-> 0]>>]),
    ([init |-> <<[a |-> 0, b |-> 0, c |-> 1, d |-> 1], [a |-> 0, b |-> 0, c |-> 0, d |-> 0]>>,pc |-> "c",mem |-> <<[a |-> 0, b |-> 0, c |-> 1, d |-> 1], [a |-> 0, b |-> 0, c |-> 0, d |-> 0]>>]),
    ([init |-> <<[a |-> 0, b |-> 0, c |-> 1, d |-> 1], [a |-> 0, b |-> 0, c |-> 0, d |-> 0]>>,pc |-> "d",mem |-> <<[a |-> 0, b |-> 0, c |-> 3, d |-> 1], [a |-> 0, b |-> 0, c |-> 0, d |-> 0]>>]),
    ([init |-> <<[a |-> 0, b |-> 0, c |-> 1, d |-> 1], [a |-> 0, b |-> 0, c |-> 0, d |-> 0]>>,pc |-> "done",mem |-> <<[a |-> 0, b |-> 0, c |-> 3, d |-> 1], [a |-> 0, b |-> 0, c |-> 0, d |-> 0]>>])
    >>
----


=============================================================================

---- CONFIG DataMul_TTrace_1791793828 ----
CONSTANTS
    M = 4
    T = 1
    X = 1
    Patched = FALSE

INVARIANT
    _inv

CHECK_DEADLOCK
    \* CHECK_DEADLOCK off because of PROPERTY or INVARIANT above.
    FALSE

INIT
    _init

NEXT
    _next

CONSTANT
    _TETrace <- _trace

ALIAS
    _expression
=============================================================================
\* Generated on Mon Oct 12 01:30:30 PDT 2026