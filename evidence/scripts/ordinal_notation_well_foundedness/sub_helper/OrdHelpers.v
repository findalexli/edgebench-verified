From Coq Require Import List Arith.PeanoNat.
Import ListNotations.

Require Import ChildOf.

(* Shared helper library (support file): childOf [0;1] N = repeat 0 (S N), and every all-zero
   list only steps to its removelast. *)

Lemma removelast_repeat0 : forall k, removelast (repeat 0 (S k)) = repeat 0 k.
Proof.
  induction k as [|k IH]; [reflexivity|].
  change (repeat 0 (S (S k))) with (0 :: repeat 0 (S k)).
  change (repeat 0 (S k)) with (0 :: repeat 0 k) at 1.
  simpl removelast. simpl in IH. destruct k; [reflexivity|].
  simpl. simpl in IH. rewrite IH. reflexivity.
Qed.

Lemma childOf_repeat0 : forall k N, childOf (repeat 0 (S k)) N = repeat 0 k.
Proof.
  intros k N. unfold childOf. cbv zeta. rewrite repeat_length.
  replace (S k - 1) with k by (simpl; rewrite Nat.sub_0_r; reflexivity).
  unfold nth0. rewrite nth_repeat. simpl Nat.eqb. cbv iota.
  apply removelast_repeat0.
Qed.

Lemma acc_repeat0 : forall k,
  Acc (fun child parent : list nat => child_step parent child) (repeat 0 k).
Proof.
  induction k as [|k IH]; constructor; intros y [Hp [N Hy]].
  - exfalso. apply Hp. reflexivity.
  - assert (E : childOf_nonempty (exist _ (repeat 0 (S k)) Hp) N = repeat 0 k)
      by exact (childOf_repeat0 k N).
    rewrite E in Hy. subst y. exact IH.
Qed.

Lemma blocks01 : forall l : list nat,
  concat (map (child_block [0; 1] 1 2) l) = repeat 0 (length l).
Proof.
  induction l as [|x l IH]; [reflexivity|]. simpl. rewrite IH. reflexivity.
Qed.

