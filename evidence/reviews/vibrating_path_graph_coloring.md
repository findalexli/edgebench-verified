# Review: `vibrating_path_graph_coloring` (zero-hit output format)

Reviewer: Claude (critical re-verification pass), 2026-10-11. Independent rerun in the pulled original judge and work images; no E2B or cloud.

> **Note (2026-10-12).** Superseded below: the recommendation to retain with a note. The grader's dependence on CPU count (8 cases at once under a 30 s wall-clock limit; the publisher's leaderboard setting, `examples/all-tasks-k8s/experiment.yaml` sha256 `d9d29979…43be`, gives it 4 CPUs) is now measured and fixed in a new version (`repairs/vibrating_path_graph_coloring-v2/`), which also raises `eval_timeout` from 600 to 900 s. Measured at 4 and 8 CPUs (`evidence/runs/vibrating_path_graph_coloring-cpu4v8-a`, `-b`, `vibrating_path_graph_coloring-v2-paired-a`, `-b`, `-c`). The zero-hit format findings below are unchanged and still ship as a note. See `cases/vibrating_path_graph_coloring.md`.

## Claim under review

Earlier claim: "Conservative interface-consistency decision: the tester rejects the visible README's three-line zero-hit output while accepting the same coloring in two lines. The unrecovered detailed README could establish an exception and warrant reconsideration. Its absence and unresolved graph-rule differences are not exclusion grounds; historical incidence is unknown."
Earlier disposition: **Withhold original** (`ADOPT_EXACT_ORIGINAL_WITHHOLDING`, evidence/selected/vibrating-original-exclusion.json). The proposed repair is proposedrepairs/vibrating-zero-hit-format/repair.patch.

## Pinned artifacts

| Item | Identity |
|---|---|
| Task JSON | `tasks/vibrating_path_graph_coloring.json` sha256 `d3bba054…a9c5` (repo HEAD `92be4bf`) |
| Judge image | `seededge/edgebench.judge.vibrating_path_graph_coloring@sha256:db8a9741831762040afb7e9819f997eb5f5293641fd5cd97d27fce3880ce084e` |
| Work image | `seededge/edgebench.work.vibrating_path_graph_coloring@sha256:ea4a4f4a959a5b0fcd4c884979f5a379b7ef73e3793719c4f80146a599e91c9e` (pulled; this is where the "unrecovered" tools README lives) |
| `tools/bin/tester` (identical in both images) | `b1c7694b8de3444c0459393b967851ad7d61e38a9a320222ce01ba7a1b446463` |
| `README.md` (identical in both images) | `d7a4af29cb6af5158aebaebadc3b7b991c505d3528bf523e715c6e340e719218` |
| `solution.py` baseline (both images) | `c119500a177f9d8a7f24ab60ea3e266296355774ca670d62b535dae9267a7689` |
| work `tools/README.md` | `8e979ee25af7ceac6eb7d3d8c3bf2723d1396372123406ae995fdba0873fa1a9` |
| work `tools/src/verifier.py` | `3154bdd2d3852861c67db9e8c18a71074befdc67e3ae28ae6d6982631af6d9c2` |
| `tools/bin/gen` | `3e738324…266e` |
| `/tmp/eval_vibrating_path.py` | `934a2b9de14bc1e155adab2a114d3dcf4d6fdbf48bedc860b78ca602ba3e9350` |
| `cases/*` aggregate | `d2e7d742…2545` (image matches the merged copy) |

## Contract (quoted)

README "Output Format":

````
```
Q
v_1 v_2 ... v_Q
x_1 x_2 ... x_N
```

- Line 1: number of hits $Q$
- Line 2: the vertices hit in order (1-indexed)
- Line 3: coloring of each vertex ($1 \leq x_i \leq K$)
````

The README has no zero-hit exception. The task prompt defers to "`README.md` and `tools/README.md` for full problem details".

**The previously unrecovered `tools/README.md` is now recovered from the work image.** It contains no output-format text and no zero-hit exception. It covers only gen and tester usage ("Success: stderr outputs `Score = <integer>`…"). So the open question "could the detailed README establish an exception" is answered: **it does not**.

Two other solver-visible artifacts do encode the two-line Q=0 convention:
- The baseline `solution.py` prints `print(0)` and then the coloring, which is two lines.
- `tools/src/verifier.py` uses `colors = list(map(int, out_lines[1].split()))` when Q≤0.

The tester itself is a readable Python script in the work image.

Tester logic: `out_lines = f.read().strip().split('\n')`. If Q>0 it needs 3 lines. Otherwise `color_line = out_lines[1]`. A blank second line therefore yields "expected N colors, got 0".

## Independent reproduction

`scripts/vibrating_path_graph_coloring/run_tester_forms.sh` runs the original tester and the original helper in the judge image (`--network none --memory 2g --cpus 2`). Output is in `run_tester_forms.out`.

| Input | Output | Original tester |
|---|---|---|
| authored bipartite 4-path, K=2 | `0\n1 2 1 2` (two-line) | `Score = 0`, exit 0 |
| same | `0\n\n1 2 1 2` (three-line, README form) | `wrong answer: expected 4 colors, got 0`, exit 1 |
| same | two-line with invalid colors | WA same-color edge, exit 1 (known-bad) |
| authored K=1 single edge | `1\n1\n1 1` (Q>0, three-line) | `Score = 9`, exit 0 (known-good positive) |
| official cases 0001,0002,0003,0004,0007,0008 | Q=0, baseline coloring, **two-line** | WA "edge (...) has same color" in every case |
| same cases | Q=0, same coloring, **three-line** | WA "expected N colors, got 0" in every case |

The original helper on an authored one-case corpus: two-line gives `OK score=0`, and three-line gives `WA score=inf`. The format inconsistency is real. On official cases it changes only the WA reason, not the result.

### Is a zero-hit answer ever valid on the official corpus?

`scripts/vibrating_path_graph_coloring/zero_hit_reachability.py` gives exact certificates that the input graph is not K-colorable, so Q=0 is *always* WA in either format. Output is in `zero_hit_reachability.out`.

- K=1 (13 cases): any edge.
- K=2 (12 cases): an odd cycle, found as a BFS 2-colouring conflict.
- N=1000, K=3 (6 cases): an explicit K4 clique, checked pairwise.
- N=1000, K=4 (6 cases): an explicit K5 clique, checked pairwise.
- **That is 37/50 cases with exact certificates.**
- The remaining 13 cases (N=10000, K∈{3,4}, average degree 20) have no small certificate, because the graph is locally tree-like.

For those 13 cases I used a union (first-moment) bound over colourings for the published generator (uniform simple graph with M=10^5 distinct edges):
P(K-colorable) ≤ K^N·((1−1/K)·N/(N−1))^M.
This gives ln P ≤ −14895 for K=4 and ≤ −29550 for K=3. It agrees with the known chromatic number of G(n, d=20), which is 6–7. All 50 cases have distinct simple edges, as the script asserts. The case files are not byte-identical to `gen(seed)` for the few seeds I tried. The bound therefore assumes they were drawn from the same uniform process, and the header combinations match gen's 8-way cycle.

**Consequence:** on all 50 official cases, any Q=0 submission scores WA (inf) whether it uses two or three lines. The trap cannot change any official score. For 37 cases this is proven exactly. For 13 it holds with probability at least 1 − e^−14895 under the generator model. Local gen seeds come from the same generator, so the same holds for local development.

## Refutation attempts

- **Does the detailed README carve out an exception?** Recovered: no. It is silent, so the earlier "could establish an exception" is resolved against an exception. But the baseline solution and the verifier source both *show* the two-line Q=0 form, which narrows any claim that the visible materials are inconsistent.
- **Is the three-line Q=0 form reachable by a real submission?** It is reachable as output. A natural `print(Q); print(*hits); print(*colors)` produces it when Q=0. But it is reachable only on cases where Q=0 is already wrong. So the reachable trigger has zero score effect.
- **Could a solver be misled during development?** Local testing is unlimited and uses the same tester. A Q=0 local run gives WA in either form, with a different message. No score-affecting path exists.

## Formal check

No Lean/TLA. The exact combinatorial certificates (cliques and odd cycles) are machine-checked in the script. The 13-case bound is a closed-form union bound evaluated in floating-point logs; its magnitude makes rounding irrelevant.

## Verdict

**CONFIRMED-NARROWER (immaterial).** The tester does reject the README's three-line zero-hit form and accept the two-line form, so the literal claim is true. Two facts limit it:
- The previously unrecovered tools README contains no exception, while solver-visible baseline and verifier code show the two-line convention.
- Zero hits is never a valid answer on any official case: 37/50 by exact certificate, 13/50 by a generator bound below e^−14000. The inconsistency therefore cannot affect any score.

## Disposition assessment

**I disagree with withholding.** The defect is real, but it has a proven zero effect on the official 50-case score (exactly for 37 cases, with overwhelming probability for 13). VERIFICATION.md requires a specific, evidenced reason. Removing the task for a formatting path that only ever converts a WA into a different WA is not proportionate. Recommend **retain with a note**. The proposed parser repair can optionally be adopted as a score-identical hygiene fix. Graph-rule (vibrating-path semantics) questions are separate and are not reviewed here.

## Recommended publishable wording

"For zero hits, the Vibrating Path tester accepts a two-line output but rejects the README's three-line form, which has an empty hit line. On every official case the graph cannot be K-colored without hits (proven exactly for 37 of 50 cases, overwhelmingly likely for the rest), so a zero-hit answer is always wrong anyway. The mismatch cannot change any score. We retain the task with a note."

## Repair note

The proposed patch is correct and minimal. When Q=0 and there are ≥3 lines, it requires line 2 to be blank and reads colors from line 3. Otherwise it keeps the legacy two-line form. It changes no score on the official corpus. An equivalent alternative is to fix the README to say "when Q=0, line 2 may be omitted" and leave the tester untouched. Either is score-compatible with the original version.

## Limits

- 13/50 cases rely on a probabilistic bound under the assumption that the cases came from the published uniform generator. I did not find the exact seeds, and I have no SAT refutation for them (no SAT solver is installed locally).
- I did not review the separate graph-rule (path semantics) divergence that the earlier audit raised.
- Historical submissions were not examined.
