| variant | v1 score | v2 score | delta | v1 pass_rate | v2 pass_rate | v1 phases | v2 phases | exits | secs |
|---|---|---|---|---|---|---|---|---|---|
| identity | 0.135313 | 0.135313 | +0.000000 | 0.166667 | 0.166667 | Phase 1:0/30; Phase 2:5/26; Phase 3:15/15; Phase 4:1/19; Phase 5:0/18; Phase 6:1/18 | Phase 1:0/30; Phase 2:5/26; Phase 3:16/16; Phase 4:1/19; Phase 5:0/18; Phase 6:1/18 | 0/0 | 15/15 |
| no_register | 0.115313 | 0.110313 | -0.005000 | 0.000000 | 0.000000 | Phase 1:0/30; Phase 2:5/26; Phase 3:12/15; Phase 4:1/19; Phase 5:0/18; Phase 6:1/18 | Phase 1:0/30; Phase 2:5/26; Phase 3:12/16; Phase 4:1/19; Phase 5:0/18; Phase 6:1/18 | 0/0 | 15/15 |
| starter | 0.031466 | 0.031466 | +0.000000 | 0.000000 | 0.000000 | Phase 1:0/30; Phase 2:4/26; Phase 3:0/15; Phase 4:1/19; Phase 5:0/18; Phase 6:1/18 | Phase 1:0/30; Phase 2:4/26; Phase 3:0/16; Phase 4:1/19; Phase 5:0/18; Phase 6:1/18 | 0/0 | 15/15 |
| wrapper | 0.135313 | 0.129063 | -0.006250 | 0.166667 | 0.000000 | Phase 1:0/30; Phase 2:5/26; Phase 3:15/15; Phase 4:1/19; Phase 5:0/18; Phase 6:1/18 | Phase 1:0/30; Phase 2:5/26; Phase 3:15/16; Phase 4:1/19; Phase 5:0/18; Phase 6:1/18 | 0/0 | 15/15 |

## Per-test outcome differences v1 -> v2 (tests absent in one version shown as -)

- **identity**: 132 v1 items, 133 v2 items; `test_metric_decorator_preserves_exact_function_identity` -->PASSED
- **no_register**: 132 v1 items, 133 v2 items; `test_metric_decorator_preserves_exact_function_identity` -->FAILED
- **starter**: 132 v1 items, 133 v2 items; `test_metric_decorator_preserves_exact_function_identity` -->FAILED
- **wrapper**: 132 v1 items, 133 v2 items; `test_phase_3` PASSED->FAILED, `test_metric_decorator_preserves_exact_function_identity` -->FAILED
