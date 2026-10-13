# How EdgeBench computes its published scores: sources

The description of EdgeBench's scoring used in IMPACT.md and on the website rests on these
passages, retrieved on 12 October 2026.

**EdgeBench technical report** (arXiv 2607.05155, HTML version):

- Appendix G.3: "Each cell schedules three runs and reports the mean score over valid runs."
- Appendix B: cells with fewer than three valid runs are marked, and "the reported scores still use
  only valid trajectories."
- On the per-run scale: "Each run score is first rescaled to the 0–100 task scale," and the ± term
  is "the sample standard deviation across these rescaled run scores."
- On time budgets: the learning curves plot "best-so-far performance," and a submission is
  effective when "it sets a new best-so-far score."

**EdgeBench evaluation platform** (https://dev.edge-bench.org/, leaderboard page):

- "Ranked by the mean score @12h — per task, runs are averaged on their best submission so far."

**EdgeBench dataset README** (`tasks/README.md`, from the Hugging Face release):

- The per-task table reports scores "at `@2h / @4h / @6h / @8h / @10h / @12h`", and "Missing valid
  results are shown as `—`."

Together these support three statements: each run is scored by its best submission so far at the
time budget; each run's score is converted to 0–100 before averaging; and a task's published score
is the mean over that model's valid runs. The documents do not say how "best" is chosen when
submissions differ in pass rate as well as score (see the Order Addition case).
