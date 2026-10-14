# cta_risk_budget_optimization, fixed version: the overseas-share check uses yuan-equivalent values

## What this fixes

The grader's 40% overseas-exposure check adds US-dollar and Chinese-yuan position values without converting currency, so overseas positions count about seven times too little. A portfolio that breaches the limit can pass, but a compliant one is never penalized. The fixed version converts dollar positions to yuan at that day's exchange rate before the 40% check.

### The problem in detail

See the [review](../../evidence/reviews/cta_risk_budget_optimization.md). The cross-border sub-check
in `eval_script.py` (40% overseas limit, about lines 1012–1040) adds `lots × multiplier × close`
(each position's notional value) across tickers without currency conversion. Overseas closes are in USD and domestic closes in CNY.
`risk_policy_doc.docx` requires "所有境外品种的仓位计算必须使用实时汇率折算为人民币等值" (every overseas position must be converted to its yuan equivalent at the live exchange rate). The same
grader converts with USDCNY elsewhere, in its profit-and-loss replay and in `_compute_exposure_stats`. As a
result, overseas exposure is undercounted about sevenfold, and only in the generous direction.

## What changes

One file, `/home/workspace/scoring/eval_script.py` (`repair.patch`, +11/−1 lines).
Inside the cross-border block, USD-priced tickers (per `contract_specs.currency`) are
multiplied by USDCNY from `raw_data['fx']`, looked up with `asof` (the latest rate on or before the date). The fallback is 7.0 when no
rate exists. This is exactly the series and fallback the grader's own `fx_for` helper uses.
Nothing else changes:
- not the 40% threshold, the day-count rules or the `cb_checks` mapping;
- not the separate "% of NAV vs % of gross notional" question.

The task JSON changes only `judge.image_tag`.

**Why minimal.** The conversion is applied at the single place where the notional value is formed for
this check. Same-currency portfolios are numerically unchanged, because the factor for CNY tickers
is 1.0.

**Score compatibility.** Fixed-version scores are not comparable with original scores for any submission that holds overseas
(USD) contracts, if converting at USDCNY pushes the overseas share above 40% on at least one day.
Such a submission loses cross-border ratio credit in the fixed version: up to 4 of 80 raw points, or 5
points out of 100. Only the `cross_border` part (inside the M3 risk constraints) can change, and
only downward.

## How it was checked

A side-by-side run of the original and fixed graders on the same test submissions: [paired/results.md](paired/results.md). The fix is accepted on this check alone. No
complete shipped submission reaches the changed block through the full grader; see the results file.

## Limits

- The test submission that shows the problem was run through the installed grader's `_evaluate_risk_constraints`, with
  the participation check stubbed and NAV left out, not through the full `score.py`.
- The only complete submission in the image is the standard answer. The full grader cancels its risk part before the
  cross-border block (annual vol 1.3%), so the full grader cannot show the change.
- The agent's working image was not inspected for a copy of `eval_script.py`.

## Build and use

Git does not contain any file copied from the EdgeBench images. It holds only our diff (`repair.patch`) and the recipe for rebuilding the full files. Regenerate them, then build:

```bash
./materialize.sh && docker build -t ebv/cta_risk_budget_optimization-judge:v2 .
```

`materialize.sh` takes the following steps:

1. Pull the pinned image(s) by digest, unless already present.
2. Extract the original files with `docker create` and `docker cp`. No container runs in this step.
3. Check each original against `source-lock.json`.
4. Apply `repair.patch` with `patch -p1`.
5. Verify the sha256 of every file under `files/` (and `orig/`) against `source-lock.json` → `materialize.outputs`. Any mismatch fails loudly.

After that, the `Dockerfile` builds without changes. Regenerated files keep the file mode they have in the image.
See `../MATERIALIZE-CHECK.md` for how each package was verified.
