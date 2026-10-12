# Vibrating Path Graph Coloring (`vibrating_path_graph_coloring`)

**Outcome:** Kept, with a note. <mark>The tester rejects the README's three-line form for an answer with no hits, but a no-hit answer is wrong on every official case (proved for 37 of 50; overwhelmingly likely for the other 13, assuming the published generator), so no score can change.</mark>

## What the task asks

The agent solves graph-colouring puzzles: it colours the points (vertices) of a network so that linked points differ, and may "hit" vertices along the way. The prompt says: "Your solution is scored on **50 fixed test cases**. Final score = sum of individual case scores. **Lower is better.**" It defers to "`README.md` and `tools/README.md` for full problem details". The README's output format has three lines:

- "Line 1: number of hits $Q$"
- "Line 2: the vertices hit in order (1-indexed)"
- "Line 3: coloring of each vertex ($1 \leq x_i \leq K$)"

The README gives no exception for the case with no hits. `tools/README.md` contains no output-format text and no exception. Category: Combinatorial Optimization.

## What we checked

**Rule.** For zero hits, the README form is three lines with an empty hit line. The tester accepts zero hits only in a two-line form. The shipped baseline `solution.py` prints the two-line form, and `tools/src/verifier.py` reads it the same way.

**Example under the original tester.**

| Input | Output | Original tester |
|---|---|---|
| bipartite 4-path we wrote, K=2 | `0\n1 2 1 2` (two-line) | `Score = 0`, exit 0 |
| same | `0\n\n1 2 1 2` (three-line, README form) | `wrong answer: expected 4 colors, got 0`, exit 1 |
| same | two-line with invalid colors | WA same-color edge, exit 1 (known-bad) |
| single edge we wrote, K=1 | `1\n1\n1 1` (Q>0, three-line) | `Score = 9`, exit 0 (known-good answer with hits) |
| official cases 0001,0002,0003,0004,0007,0008 | Q=0, baseline coloring, **two-line** | WA "edge (...) has same color" in every case |
| same cases | Q=0, same coloring, **three-line** | WA "expected N colors, got 0" in every case |

**Why it does not matter for scores.** On 37 of the 50 official cases, the input graph provably cannot be coloured with K colours without hits. On the other 13 this holds with overwhelming probability, assuming the published generator. A zero-hit answer is therefore wrong in either format. The mismatch changes only the reason given for the wrong answer.

- **37/50 cases have exact certificates** (short proofs that the graph cannot be coloured with K colours):
  - 13 cases with K=1: any edge;
  - 12 cases with K=2: an odd cycle;
  - 6 cases with N=1000, K=3: an explicit K4 clique (four mutually linked vertices; the K4 in case 0043 was also checked separately);
  - 6 cases with N=1000, K=4: an explicit K5 clique.
- **The other 13 cases** have N=10000, K∈{3,4} and average degree 20, and admit no small certificate. A union bound (adding up the probabilities of every possible valid colouring) gives ln P ≤ −14895 for K=4 and ≤ −29550 for K=3. This assumes the cases came from the published uniform generator.

**Note shipped with the task.** For zero hits, the tester accepts a two-line output and rejects the README's three-line form with an empty hit line. On every official case a zero-hit answer is wrong anyway (proved for 37 of 50, overwhelmingly likely for the other 13), so the mismatch cannot change any score. A parser patch that accepts both forms gives identical scores on the official cases and could be adopted as an optional clean-up.

## How much it matters

Largest score effect: 0 on the official cases. Only a solver that outputs zero hits in the README form would see a different error message.

The task does not change; the note above ships with it.

## How we checked it

- **Original grader.** The original tester and helper ran in the original public image, pinned by digest, with `--network none`. The inputs were graphs we wrote with two-line and three-line zero-hit outputs, a known-bad colouring, a known-good output with hits, and six official cases. `tools/bin/tester` is identical in the grader image and the agent's working image. `tools/README.md` was read from the working image.
- **Exact certificates.** For each official case, a proof that the graph cannot be coloured with K colours: an edge for K=1, an odd cycle for K=2, and explicit K4 or K5 cliques checked pair by pair.
- **Probabilistic bound.** For the remaining large, sparse cases, a closed-form union bound under the published generator's model.

## Limits

- No AI model or solver was run. Effects are shown only on test submissions and counterexamples we wrote.
- 13/50 cases rely on a probabilistic bound and assume the cases came from the published uniform generator. The exact seeds were not found, and no SAT refutation (a machine proof by a satisfiability solver) was run.
- The vibrating-path graph rules themselves were not reviewed.
- Past submissions were not examined.

## Reproduce

- Tester forms: `evidence/scripts/vibrating_path_graph_coloring/run_tester_forms.sh` (inputs in `inputs/`; output `run_tester_forms.out`)
- Zero-hit certificates and bound: `evidence/scripts/vibrating_path_graph_coloring/zero_hit_reachability.py` (output `zero_hit_reachability.out`)
- Working-image documentation: `evidence/scripts/vibrating_path_graph_coloring/work_image_docs.out`
- Pinned identity:
  - Grader image: `seededge/edgebench.judge.vibrating_path_graph_coloring@sha256:db8a9741831762040afb7e9819f997eb5f5293641fd5cd97d27fce3880ce084e`.
  - Working image: `seededge/edgebench.work.vibrating_path_graph_coloring@sha256:ea4a4f4a959a5b0fcd4c884979f5a379b7ef73e3793719c4f80146a599e91c9e`.
  - Task JSON: sha256 `d3bba054…a9c5`.
  - `tools/bin/tester`: `b1c7694b8de3444c0459393b967851ad7d61e38a9a320222ce01ba7a1b446463`.
  - `README.md`: `d7a4af29cb6af5158aebaebadc3b7b991c505d3528bf523e715c6e340e719218`.
  - `/tmp/eval_vibrating_path.py`: `934a2b9de14bc1e155adab2a114d3dcf4d6fdbf48bedc860b78ca602ba3e9350`.
