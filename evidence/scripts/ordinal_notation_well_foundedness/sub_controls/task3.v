From Coq Require Import List.
Import ListNotations.

Require Import ChildOf.

(* Negative control: relies on a new axiom; must NOT receive credit. *)
Axiom all_acc : forall a, Acc (fun child parent : list nat => child_step parent child) a.

Lemma WF : Acc (fun child parent : list nat => child_step parent child) [0; 1; 0; 0; 3; 3].
Proof. apply all_acc. Qed.
