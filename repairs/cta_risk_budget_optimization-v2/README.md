# cta_risk_budget_optimization v2: the overseas-ratio check uses CNY-equivalent notionals

**Defect** ([review](../../evidence/reviews/cta_risk_budget_optimization.md)). The cross-border sub-check
in `eval_script.py` (40% overseas limit, about lines 1012–1040) adds `lots × multiplier × close`
across tickers without currency conversion. Overseas closes are in USD and domestic closes in CNY.
`risk_policy_doc.docx` requires "所有境外品种的仓位计算必须使用实时汇率折算为人民币等值". The same
evaluator converts with USDCNY elsewhere, in its PnL replay and in `_compute_exposure_stats`. As a
result, overseas exposure is undercounted about sevenfold, and only in the lenient direction.

**Change.** One file, `/home/workspace/scoring/eval_script.py` (`repair.patch`, +11/−1 lines).
Inside the cross-border block, USD-denominated tickers (per `contract_specs.currency`) are
multiplied by USDCNY from `raw_data['fx']`, looked up with `asof`. The fallback is 7.0 when no
rate exists, which is exactly the series and fallback the evaluator's own `fx_for` helper uses.
Nothing else changes:
- not the 40% threshold, the day-count rules or the `cb_checks` mapping;
- not the separate "% of NAV vs % of gross notional" question.

The task JSON changes only `judge.image_tag`.

**Why minimal.** The conversion is applied at the single place where the notional is formed for
this check. Same-currency portfolios are numerically unchanged, because the factor for CNY tickers
is 1.0.

**Score compatibility.** v2 is not comparable with v1 for any submission that holds overseas
(USD) contracts, if converting at USDCNY pushes the overseas share above 40% on at least one day.
Such a submission loses cross-border ratio credit in v2: up to 4 of 80 raw points, or 5
normalized points. Only the `cross_border` component (inside M3 risk constraints) can change, and
only downward.

**Paired evaluation:** [paired/results.md](paired/results.md). Accepted at component level. No
complete shipped submission reaches the changed block through the full scorer; see there.

**Limits.**
- The trigger was exercised through the installed evaluator's `_evaluate_risk_constraints`, with
  the participation gate stubbed and NAV omitted, not through the full `score.py`.
- The only complete submission in the image is the standard answer. It is vetoed before the
  cross-border block (annual vol 1.3%), so the full scorer cannot show the change.
- The work image was not inspected for a copy of `eval_script.py`.

## Build

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
