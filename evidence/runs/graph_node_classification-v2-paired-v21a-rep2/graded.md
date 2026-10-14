| Submission | Image | harness valid | score (final) | normalized 0-100 | overall (quality) | macro_f1 | micro_f1 | bal_acc | one_minus_ece | checks / reason |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| baseline | v1 | True | 0.294020 | 29.4020 | 0.332624 | 0.238512 | 0.286840 | 0.293320 | 0.925034 | valid=true final_score=0.294020 overall_score=0.332624 macro_f1=0.238512 micro_f1=0.286840 balanced_accuracy=0 |
| baseline | v2prev | True | 0.294018 | 29.4018 | 0.332624 | 0.238512 | 0.286840 | 0.293320 | 0.925034 | valid=true final_score=0.294018 overall_score=0.332624 macro_f1=0.238512 micro_f1=0.286840 balanced_accuracy=0 |
| baseline | v2 | True | 0.294105 | 29.4105 | 0.332624 | 0.238512 | 0.286840 | 0.293320 | 0.925034 | valid=true final_score=0.294105 overall_score=0.332624 macro_f1=0.238512 micro_f1=0.286840 balanced_accuracy=0 |
| neighbor | v1 | True | 0.242314 | 24.2314 | 0.281108 | 0.221556 | 0.232853 | 0.233981 | 0.758336 | valid=true final_score=0.242314 overall_score=0.281108 macro_f1=0.221556 micro_f1=0.232853 balanced_accuracy=0 |
| neighbor | v2prev | True | 0.242197 | 24.2197 | 0.281108 | 0.221556 | 0.232853 | 0.233981 | 0.758336 | valid=true final_score=0.242197 overall_score=0.281108 macro_f1=0.221556 micro_f1=0.232853 balanced_accuracy=0 |
| neighbor | v2 | True | 0.242143 | 24.2143 | 0.281108 | 0.221556 | 0.232853 | 0.233981 | 0.758336 | valid=true final_score=0.242143 overall_score=0.281108 macro_f1=0.221556 micro_f1=0.232853 balanced_accuracy=0 |
| neighbor_intkeys | v1 | True | -0.039043 | 0.0000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | valid=true final_score=-0.039043 overall_score=0.000000 macro_f1=0.000000 micro_f1=0.000000 balanced_accuracy= |
| neighbor_intkeys | v2prev | False | 0.000000 | 0.0000 | - | - | - | - | - | runner failed before producing a valid result payload: return self.__get_result() / ^^^^^^^^^^^^^^^^^^^ / File |
| neighbor_intkeys | v2 | True | 0.242067 | 24.2067 | 0.281108 | 0.221556 | 0.232853 | 0.233981 | 0.758336 | valid=true final_score=0.242067 overall_score=0.281108 macro_f1=0.221556 micro_f1=0.232853 balanced_accuracy=0 |
| dupkeys_after_str | v1 | True | 0.200246 | 20.0246 | 0.239264 | 0.200000 | 0.200000 | 0.200000 | 0.592639 | valid=true final_score=0.200246 overall_score=0.239264 macro_f1=0.200000 micro_f1=0.200000 balanced_accuracy=0 |
| dupkeys_after_str | v2prev | False | 0.000000 | 0.0000 | - | - | - | - | - | runner failed before producing a valid result payload: return self.__get_result() / ^^^^^^^^^^^^^^^^^^^ / File |
| dupkeys_after_str | v2 | False | 0.000000 | 0.0000 | - | - | - | - | - | runner failed before producing a valid result payload: return self.__get_result() / ^^^^^^^^^^^^^^^^^^^ / File |
