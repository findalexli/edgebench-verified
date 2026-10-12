# Vibrating Path Graph Coloring (`vibrating_path_graph_coloring`)

Status: reviewed by the coordinator, 2026-10-12

- **Domain:** Combinatorial Optimization
- **Decision:** Retain with note. The tester rejects the README's three-line form for zero-hit output, but a zero-hit answer is not valid on any official case (proved for 37 of 50; overwhelmingly likely for the other 13 under the published-generator assumption), so no score can change.

## What the task promises

The prompt says: "Your solution is scored on **50 fixed test cases**. Final score = sum of individual case scores. **Lower is better.**" It defers to "`README.md` and `tools/README.md` for full problem details".

The README's output format has three lines:

- "Line 1: number of hits $Q$"
- "Line 2: the vertices hit in order (1-indexed)"
- "Line 3: coloring of each vertex ($1 \leq x_i \leq K$)"

The README gives no exception for the case with no hits.

## What we checked and how

- **Native tester runs.** We ran the original tester and helper in the pinned judge image with `--network none --memory 2g --cpus 2`. Inputs were:
  - authored graphs with two-line and three-line zero-hit outputs;
  - a known-bad coloring;
  - a known-good output with hits;
  - six official cases.
- **Documentation recovered.** We pulled the work image and recovered `tools/README.md`, which the earlier audit had not recovered.
- **Exact certificates.** For each official case we searched for proof that the graph cannot be K-colored, which would mean zero hits is never valid. The proofs are an edge for K=1, an odd cycle for K=2, and explicit K4 or K5 cliques checked pairwise.
- **Probabilistic bound.** For the remaining large, sparse cases we used a closed-form union bound under the published generator's model.
- **Original identity.**
  - Judge image: `seededge/edgebench.judge.vibrating_path_graph_coloring@sha256:db8a9741831762040afb7e9819f997eb5f5293641fd5cd97d27fce3880ce084e`.
  - Work image: `seededge/edgebench.work.vibrating_path_graph_coloring@sha256:ea4a4f4a959a5b0fcd4c884979f5a379b7ef73e3793719c4f80146a599e91c9e`.
  - Task JSON: sha256 `d3bba054…a9c5`.
  - `tools/bin/tester`: `b1c7694b8de3444c0459393b967851ad7d61e38a9a320222ce01ba7a1b446463`. It is identical in both images.
  - `README.md`: `d7a4af29cb6af5158aebaebadc3b7b991c505d3528bf523e715c6e340e719218`.
  - `/tmp/eval_vibrating_path.py`: `934a2b9de14bc1e155adab2a114d3dcf4d6fdbf48bedc860b78ca602ba3e9350`.

## What we found

**Confirmed, narrower and not material: the zero-hit format mismatch.** The tester accepts zero hits in a two-line form but rejects the README's three-line form, which has an empty hit line. Results under the original tester:

| Input | Output | Original tester |
|---|---|---|
| authored bipartite 4-path, K=2 | `0\n1 2 1 2` (two-line) | `Score = 0`, exit 0 |
| same | `0\n\n1 2 1 2` (three-line, README form) | `wrong answer: expected 4 colors, got 0`, exit 1 |
| same | two-line with invalid colors | WA same-color edge, exit 1 (known-bad) |
| authored K=1 single edge | `1\n1\n1 1` (Q>0, three-line) | `Score = 9`, exit 0 (known-good positive) |
| official cases 0001,0002,0003,0004,0007,0008 | Q=0, baseline coloring, **two-line** | WA "edge (...) has same color" in every case |
| same cases | Q=0, same coloring, **three-line** | WA "expected N colors, got 0" in every case |

**Zero hits is never valid on an official case.** On 37 of the 50 official cases the input graph provably cannot be K-colored without hits; on the other 13 this holds with overwhelming probability, assuming the published generator. A zero-hit answer is therefore wrong in either format, and the mismatch changes only the reason given for the wrong answer.

- **37/50 cases have exact certificates:**
  - 13 cases with K=1: any edge;
  - 12 cases with K=2: an odd cycle;
  - 6 cases with N=1000, K=3: an explicit K4 clique (the coordinator separately re-verified the K4 in case 0043);
  - 6 cases with N=1000, K=4: an explicit K5 clique.
- **The other 13 cases** have N=10000, K∈{3,4} and average degree 20, and admit no small certificate. A union bound gives ln P ≤ −14895 for K=4 and ≤ −29550 for K=3. This assumes the cases came from the published uniform generator.

Maximum score effect: 0 on the official cases.

**Earlier withholding.** An earlier audit withheld the original task under a conservative interface-consistency policy. It left open whether the unrecovered detailed README might allow an exception. Re-checking showed:

- The recovered `tools/README.md` contains no output-format text and no exception.
- The shipped baseline `solution.py` prints the two-line form for zero hits, and `tools/src/verifier.py` reads it the same way.
- The mismatch cannot change any official score, so withholding is not justified.

## Note for users

No repair. The note says: for zero hits, the tester accepts a two-line output and rejects the README's three-line form with an empty hit line. On every official case a zero-hit answer is wrong anyway (proved for 37 of 50, overwhelmingly likely for the other 13), so the mismatch cannot change any score.

A proposed parser patch would accept both forms. It is score-identical on the official corpus and could be adopted as optional hygiene.

## Limits and what was not run

- No model or solver re-runs were done. Effects are shown only on authored controls and counterexamples.
- 13/50 cases rely on a probabilistic bound and assume the cases came from the published uniform generator. The exact seeds were not found, and no SAT refutation was run.
- The separate question about the vibrating-path graph rules, raised by the earlier audit, was not reviewed here.
- Historical submissions were not examined.

## Reproduce

- Tester forms: `evidence/scripts/vibrating_path_graph_coloring/run_tester_forms.sh` (inputs in `inputs/`; output `run_tester_forms.out`)
- Zero-hit certificates and bound: `evidence/scripts/vibrating_path_graph_coloring/zero_hit_reachability.py` (output `zero_hit_reachability.out`)
- Recovered work-image documentation: `evidence/scripts/vibrating_path_graph_coloring/work_image_docs.out`
