Superseded: first run with a year >= 1900 floor; the final run is in evidence/runs/schemathesis_datagen_pipeline-v2-paired-b/result/out/.

| variant | v1 score | v2 score | delta | v1 pass_rate | v2 pass_rate | v1 phases | v2 phases | exits | secs |
|---|---|---|---|---|---|---|---|---|---|
| correct | 0.477350 | 0.477350 | +0.000000 | 0.125000 | 0.125000 | Phase 1:8/8; Phase 2:2/5; Phase 3:0/9; Phase 4:7/10; Phase 5:5/8; Phase 6:0/5; Phase 7:3/5; Phase 8:10/36 | Phase 1:8/8; Phase 2:2/5; Phase 3:0/9; Phase 4:7/10; Phase 5:5/8; Phase 6:0/5; Phase 7:3/5; Phase 8:10/36 | 0/0 | 22/22 |
| garbage_shape | 0.477350 | 0.467094 | -0.010256 | 0.125000 | 0.000000 | Phase 1:8/8; Phase 2:2/5; Phase 3:0/9; Phase 4:7/10; Phase 5:5/8; Phase 6:0/5; Phase 7:3/5; Phase 8:10/36 | Phase 1:14/15; Phase 2:2/5; Phase 3:0/9; Phase 4:7/10; Phase 5:5/8; Phase 6:0/5; Phase 7:3/5; Phase 8:10/36 | 0/0 | 20/21 |
| independent_fields | 0.477350 | 0.467094 | -0.010256 | 0.125000 | 0.000000 | Phase 1:8/8; Phase 2:2/5; Phase 3:0/9; Phase 4:7/10; Phase 5:5/8; Phase 6:0/5; Phase 7:3/5; Phase 8:10/36 | Phase 1:14/15; Phase 2:2/5; Phase 3:0/9; Phase 4:7/10; Phase 5:5/8; Phase 6:0/5; Phase 7:3/5; Phase 8:10/36 | 0/0 | 20/22 |
| off_by_one_clock | 0.477350 | 0.467094 | -0.010256 | 0.125000 | 0.000000 | Phase 1:8/8; Phase 2:2/5; Phase 3:0/9; Phase 4:7/10; Phase 5:5/8; Phase 6:0/5; Phase 7:3/5; Phase 8:10/36 | Phase 1:14/15; Phase 2:2/5; Phase 3:0/9; Phase 4:7/10; Phase 5:5/8; Phase 6:0/5; Phase 7:3/5; Phase 8:10/36 | 0/0 | 21/22 |
| rfc850 | 0.467094 | 0.467094 | +0.000000 | 0.000000 | 0.000000 | Phase 1:14/15; Phase 2:2/5; Phase 3:0/9; Phase 4:7/10; Phase 5:5/8; Phase 6:0/5; Phase 7:3/5; Phase 8:10/36 | Phase 1:14/15; Phase 2:2/5; Phase 3:0/9; Phase 4:7/10; Phase 5:5/8; Phase 6:0/5; Phase 7:3/5; Phase 8:10/36 | 0/0 | 22/21 |
| starter | 0.323504 | 0.323504 | +0.000000 | 0.000000 | 0.000000 | Phase 1:0/15; Phase 2:2/5; Phase 3:0/9; Phase 4:7/10; Phase 5:5/8; Phase 6:0/5; Phase 7:3/5; Phase 8:10/36 | Phase 1:0/15; Phase 2:2/5; Phase 3:0/9; Phase 4:7/10; Phase 5:5/8; Phase 6:0/5; Phase 7:3/5; Phase 8:10/36 | 0/0 | 21/20 |
| stdlib_1900 | 0.477350 | 0.477350 | +0.000000 | 0.125000 | 0.125000 | Phase 1:8/8; Phase 2:2/5; Phase 3:0/9; Phase 4:7/10; Phase 5:5/8; Phase 6:0/5; Phase 7:3/5; Phase 8:10/36 | Phase 1:8/8; Phase 2:2/5; Phase 3:0/9; Phase 4:7/10; Phase 5:5/8; Phase 6:0/5; Phase 7:3/5; Phase 8:10/36 | 0/0 | 21/22 |
| stdlib_any_year | 0.477350 | 0.467094 | -0.010256 | 0.125000 | 0.000000 | Phase 1:8/8; Phase 2:2/5; Phase 3:0/9; Phase 4:7/10; Phase 5:5/8; Phase 6:0/5; Phase 7:3/5; Phase 8:10/36 | Phase 1:14/15; Phase 2:2/5; Phase 3:0/9; Phase 4:7/10; Phase 5:5/8; Phase 6:0/5; Phase 7:3/5; Phase 8:10/36 | 0/0 | 21/21 |

## Per-test outcome differences v1 -> v2 (tests absent in one version shown as -)

- **correct**: 99 v1 items, 99 v2 items; no differences
- **garbage_shape**: 99 v1 items, 99 v2 items; `test_phase_1` PASSED->FAILED, `test_http_date_values_grammar` PASSED->FAILED
- **independent_fields**: 99 v1 items, 99 v2 items; `test_phase_1` PASSED->FAILED, `test_http_date_values_grammar` PASSED->FAILED
- **off_by_one_clock**: 99 v1 items, 99 v2 items; `test_phase_1` PASSED->FAILED, `test_http_date_values_grammar` PASSED->FAILED
- **rfc850**: 99 v1 items, 99 v2 items; no differences
- **starter**: 99 v1 items, 99 v2 items; no differences
- **stdlib_1900**: 99 v1 items, 99 v2 items; no differences
- **stdlib_any_year**: 99 v1 items, 99 v2 items; `test_phase_1` PASSED->FAILED, `test_http_date_values_grammar` PASSED->FAILED
