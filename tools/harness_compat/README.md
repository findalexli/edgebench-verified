# Earlier audit's grading patch (not EdgeBench's behaviour)

The earlier automated audit changed five files of EdgeBench's grading software in place
(`sforge/harness/grading.py`, `selection.py`, and `log_parsers/{pytest_v,score_sum,structured_json}.py`),
calling the result a "Verified compatibility change". This repository now ships those files exactly as
published by EdgeBench (GitHub ByteDance-Seed/EdgeBench at `6e4e5f4`; checked by `tools/check_upstream.py`).
The changed version is kept here only as a record.

**It is not EdgeBench's behaviour, and no published score, decision, table or proof uses it.**
All findings are stated for EdgeBench's original harness.

- `verified-harness.patch`: the change, as a unified diff from the original files to the earlier audit's version.
  Apply it with `patch -p1` in a scratch copy, never in this tree.
- `test_grading_contract.py`: the earlier audit's tests for the patched version. They fail on the original files.

What the patch does differently, in short:

- A result marked `valid: false`, or one whose evaluation hit the harness timeout, loses its score and is left out of
  every selection rule. In EdgeBench only `valid_then_score` drops `valid: false`, and nothing checks the timeout flag.
- A non-finite score (`inf`), a duplicate or malformed `CASE` line, a missing `TOTAL_SCORE`, more than one
  `TOTAL_SCORE`, or `CASES_TOTAL`/`CASES_OK` that disagree with the `CASE` lines make the result invalid.
  EdgeBench accepts `inf`, reads the first `TOTAL_SCORE`, and ignores the `CASES_*` lines.
- An incomplete pytest session, and a structured result that is missing, ambiguous or malformed, make the result
  invalid. EdgeBench grades what it finds.
- `pass_rate_first` takes the first entry even at pass rate 0, and reports `best_valid: false` when nothing qualifies.

The earlier audit's full working state is preserved at Git tag `earlier-audit-final`.
