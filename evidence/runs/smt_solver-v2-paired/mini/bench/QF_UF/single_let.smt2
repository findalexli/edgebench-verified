; CASE:single_let
(set-logic QF_UF)
(declare-sort U 0)
(declare-fun a () U)
(declare-fun b () U)
(declare-fun f (U) U)
(assert (distinct a b))
(assert (let ((x a)) (= (f x) b)))
(check-sat)
