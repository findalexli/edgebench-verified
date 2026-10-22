# Triangulation: the same diagnosis for the Qwen3.8 Flash Next 12-hour run

`run.sh` fetches only `harness/triangulation_coloring_optimization/final_archive.tar.gz` from the third-party
dataset (`adafadaq/edgebench-opus-5-5-xhigh-rollouts`, `qwen3.8-flash-next/`; Codex scaffold, 12 h, recorded best
163731 raw at round agent-169 of 198). The archive is not redistributed; `result/out/final_archive.sha256` records it.
The final archive is the workspace at the end of the run, which is not necessarily the selected round. The method
is the 2x2 of `../qwen35-diag-triangulation/`: the original or fixed tester, on the original or regenerated inputs,
one case at a time, 30 s per case.

| Final solution | Original rule, original inputs | Original rule, new inputs | Fixed rule, original inputs | Fixed rule, new inputs |
|---|---|---|---|---|
| Qwen3.8 Flash Next, 12 h | 10/10 scored | 10/10 scored | 0/10 (Invalid flip) | 0/10 (Invalid flip) |

As with Qwen3.5-122B, the flip rule causes the failures, and the inputs do not. On every case the solver makes
at least one flip that the README forbids.

The local controller lost its connection during a local network outage. The worker kept running and was collected
by `tools/e2b_recover.py`, so `result/worker.json` has `status: exit=0, recovered: true`.
