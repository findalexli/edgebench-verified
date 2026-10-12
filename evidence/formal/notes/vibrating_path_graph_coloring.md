# vibrating_path_graph_coloring: formal note

## Claim
On 37 of the 50 official cases, the tester rejects every zero-hit (Q = 0) output, whatever the
colouring and whichever line form is used. So the two-line/three-line mismatch cannot change
those cases' scores.

## Model and link to the code
Lean 4: `evidence/formal/lean/ebv/Ebv/VibratingZeroHit.lean` (output `VibratingZeroHit.out`).
- `Q0Accepts` models `tools/bin/tester` (sha256 b1c7694b…6463), Q = 0 path: lines 61-73
  (N colours in [1, K]) and lines 151-157 (no edge may have equal colours). With no hits,
  `removed_edges` stays empty (lines 75-149).
- `testerQ0` is an executable model of lines 41-73 and 151-157 including line splitting. Its
  `#eval` on the authored inputs gives `[true, false, false, false]`, which matches
  `run_tester_forms.out` (two-line accepted; three-line, bad colouring and K=1 no-hit rejected).
- Certificates come from `evidence/formal/scripts/vibrating_certs.py`, run over the work-image
  `cases/*.txt`. The aggregate `sha256sum cases/*.txt | sha256sum` is d2e7d742…2545, the value in
  the review. The certificates are a K2 (K=1), a triangle (K=2), a K4 (K=3, N=1000) or a K5
  (K=4, N=1000). `vibrating_certs.out` records each case's sha256 and the edge-list index of every
  certificate pair, re-read from the raw tokens.

## Result
**Proved for 37 cases; the other 13 are not formalizable here.** `clique_blocks_q0` is general: a
(K+1)-clique leaves no accepted Q = 0 output (pigeonhole). `certs_wf` (kernel `decide`) checks
that all 37 certificates are cliques. `no_zero_hit_answer` combines the two. The 13 remaining cases
(N=10000, K∈{3,4}) have no K4/K5: a scan of 4 of them found no K4 and no odd wheel. Proving
non-3/4-colourability there needs a SAT-scale refutation. The published 13-case claim rests on a
union bound under an assumed generator model, which is a statement about the generator, not the
grader.

## Counter-check
- `counter_bip4_accepted`: the model is not vacuous (the bipartite 4-path is accepted).
- `counter_triangle_k3`: a K-clique does not block.
- `counter_mutated_cert` and `counter_small_cert`: a certificate with a pair dropped, or one vertex
  short, fails `WF`.

## Limits
- Edge membership of the certificate pairs is checked by script against sha-pinned files and
  enters Lean as hypothesis `hsub`. The case data is not embedded in Lean.
- The published K=2 certificates are odd cycles; we used triangles, a special case.
- The 13 large cases are not covered.
