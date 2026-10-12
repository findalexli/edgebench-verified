| Submission | Image | Tests passed | pass_rate | valid | raw TOTAL_SCORE | normalized (0-100) | eval exit |
| --- | --- | --- | ---: | --- | ---: | ---: | --- |
| identity | v1 | 4/5 | 0.80 | True | 3.3e-09 | 3.3e-09 | rc=0 |
| identity | v2 | 5/5 | 1.00 | True | 3.3e-09 | 3.3e-09 | rc=0 |
| search | v1 | 4/5 | 0.80 | True | 0.0093733018 | 0.0093733018 | rc=0 |
| search | v2 | 5/5 | 1.00 | True | 0.0093733018 | 0.0093733018 | rc=0 |
| badcost | v1 | 3/5 | 0.60 | True | None | None | rc=0 |
| badcost | v2 | 4/5 | 0.80 | True | None | None | rc=0 |
| dup | v1 | 3/5 | 0.60 | True | None | None | rc=0 |
| dup | v2 | 4/5 | 0.80 | True | None | None | rc=0 |

history ['identity', 'search'] v1 (pass_rate_first): best_round=identity best_score=3.3e-09 best_pass_rate=0.8
history ['identity', 'search'] v2 (pass_rate_first): best_round=search best_score=0.0093733018 best_pass_rate=1.0
history ['search', 'identity'] v1 (pass_rate_first): best_round=search best_score=0.0093733018 best_pass_rate=0.8
history ['search', 'identity'] v2 (pass_rate_first): best_round=search best_score=0.0093733018 best_pass_rate=1.0
history ['dup', 'identity', 'search'] v1 (pass_rate_first): best_round=identity best_score=3.3e-09 best_pass_rate=0.8
history ['dup', 'identity', 'search'] v2 (pass_rate_first): best_round=search best_score=0.0093733018 best_pass_rate=1.0
history ['badcost', 'identity', 'search'] v1 (pass_rate_first): best_round=identity best_score=3.3e-09 best_pass_rate=0.8
history ['badcost', 'identity', 'search'] v2 (pass_rate_first): best_round=search best_score=0.0093733018 best_pass_rate=1.0
