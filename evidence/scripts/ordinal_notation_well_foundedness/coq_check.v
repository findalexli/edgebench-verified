From Coq Require Import List.
Import ListNotations.
Require Import ChildOf.
Compute (childOf [0;1;0;2;0;3] 2).
Compute (childOf [0;1;0;0;3;3] 2).
Compute (childOf [0;1;0;1] 2).
Compute (childOf [0;1;0;2;0;0;2] 2).
Compute (childOf [0;1;0;2;0;0;2;0;0;2] 2).
Compute (childOf [0;1;0;0;4] 2).
