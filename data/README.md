# Data

Machine-readable results. The tables and website are generated from these files.

| File | Contents |
| --- | --- |
| [`decisions.json`](decisions.json) | The authoritative outcome for each of the 51 tasks (`retain-with-note`, `repair-v2` for fixed, `exclude` for removed), with the technical finding and its largest effect |
| [`decisions.csv`](decisions.csv) | The same outcomes with the plain-language summary of each task |
| [`paired-results.csv`](paired-results.csv) | Every side-by-side test: one test submission graded by the original grader (`v1_*` columns) and the fixed grader (`v2_*` columns). [`paired-results-summary.md`](paired-results-summary.md) explains how it was built. |
| [`paired-repeatability.csv`](paired-repeatability.csv) | Each side-by-side test repeated three times; [`paired-repeatability.md`](paired-repeatability.md) is the report |
| [`impact.csv`](impact.csv) | Effect on the published leaderboard averages, per model; explained in [`../IMPACT.md`](../IMPACT.md) |
