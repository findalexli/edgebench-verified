From Coq Require Import List.
Import ListNotations.
Require Import ChildOf.
Require Import OrdHelpers.

Lemma WF : Acc (fun child parent : list nat => child_step parent child) [0; 1].
Proof.
  constructor. intros y [Hp [N Hy]].
  unfold childOf_nonempty, childOf in Hy. simpl in Hy.
  rewrite blocks01, length_seq in Hy. subst y.
  exact (acc_repeat0 (S N)).
Qed.
