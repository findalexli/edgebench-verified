# Tie-aware ranking: proof and counterexample contract

This is an author-owned mathematical problem for optional Rethlas review and
subsequent independent Lean checking. It contains no benchmark input records,
answers, actual task verdict or claim about the installed ANN implementation.
No proof or model execution has occurred.

Let U be a finite set with n elements, d: U -> real numbers, and 1 <= k <= n.
Let tau be the kth smallest distance, with repeated distance values counted.
Let S be a subset of U with exactly k distinct elements.

First attempt to refute this intentionally questionable claim:

> If every selected element has distance at most tau, S is a valid selection of
> the k nearest elements, allowing arbitrary choice at distance ties.

An independent negative control is U={a,b,c}, d(a)=0, d(b)=d(c)=1, k=2,
S={b,c}. Determine whether the claim holds and state the missing premise.

Then assess the proposed corrected contract:

> S is a valid tie-aware k-nearest selection precisely when S contains every
> element whose distance is strictly below tau and every selected element has
> distance at most tau.

Make "valid" precise as the pairwise condition that d(x) <= d(y) for every
selected x and unselected y. Prove both directions, retaining |S|=k and the
finite order-statistic definition. Cover k=1, k=n, repeated distances and the
all-equal case. Do not introduce an arbitrary unique tie ordering or assume
distances are distinct.

Expected deliverables: counterexample verdict, explicit hypotheses, informal
proof blueprint, and a precise statement suitable for Lean formalization.
Rethlas's own positive verdict is not the formal acceptance criterion. Lean
must check the encoded theorem with declared axioms and reject the false claim.

This abstract contract cannot establish floating-point distances, installed
oracle correspondence, dataset validity, runtime or complete task certification.
