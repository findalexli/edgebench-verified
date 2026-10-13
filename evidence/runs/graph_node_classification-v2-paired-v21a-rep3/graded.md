| Submission | Image | harness valid | score (final) | normalized 0-100 | overall (quality) | macro_f1 | micro_f1 | bal_acc | one_minus_ece | checks / reason |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| baseline | v1 | True | 0.291900 | 29.1900 | 0.332624 | 0.238512 | 0.286840 | 0.293320 | 0.925034 | valid=true final_score=0.291900 overall_score=0.332624 macro_f1=0.238512 micro_f1=0.286840 balanced_accuracy=0 |
| baseline | v2prev | True | 0.292316 | 29.2316 | 0.332624 | 0.238512 | 0.286840 | 0.293320 | 0.925034 | valid=true final_score=0.292316 overall_score=0.332624 macro_f1=0.238512 micro_f1=0.286840 balanced_accuracy=0 |
| baseline | v2 | True | 0.292185 | 29.2185 | 0.332624 | 0.238512 | 0.286840 | 0.293320 | 0.925034 | valid=true final_score=0.292185 overall_score=0.332624 macro_f1=0.238512 micro_f1=0.286840 balanced_accuracy=0 |
| neighbor | v1 | True | 0.240554 | 24.0554 | 0.281108 | 0.221556 | 0.232853 | 0.233981 | 0.758336 | valid=true final_score=0.240554 overall_score=0.281108 macro_f1=0.221556 micro_f1=0.232853 balanced_accuracy=0 |
| neighbor | v2prev | True | 0.240724 | 24.0724 | 0.281108 | 0.221556 | 0.232853 | 0.233981 | 0.758336 | valid=true final_score=0.240724 overall_score=0.281108 macro_f1=0.221556 micro_f1=0.232853 balanced_accuracy=0 |
| neighbor | v2 | True | 0.240832 | 24.0832 | 0.281108 | 0.221556 | 0.232853 | 0.233981 | 0.758336 | valid=true final_score=0.240832 overall_score=0.281108 macro_f1=0.221556 micro_f1=0.232853 balanced_accuracy=0 |
| neighbor_intkeys | v1 | True | -0.040355 | 0.0000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | valid=true final_score=-0.040355 overall_score=0.000000 macro_f1=0.000000 micro_f1=0.000000 balanced_accuracy= |
| neighbor_intkeys | v2prev | False | 0.000000 | 0.0000 | - | - | - | - | - | runner failed before producing a valid result payload: return self.__get_result() / ^^^^^^^^^^^^^^^^^^^ / File |
| neighbor_intkeys | v2 | True | 0.240619 | 24.0619 | 0.281108 | 0.221556 | 0.232853 | 0.233981 | 0.758336 | valid=true final_score=0.240619 overall_score=0.281108 macro_f1=0.221556 micro_f1=0.232853 balanced_accuracy=0 |
| dupkeys_after_str | v1 | True | 0.198731 | 19.8731 | 0.239264 | 0.200000 | 0.200000 | 0.200000 | 0.592639 | valid=true final_score=0.198731 overall_score=0.239264 macro_f1=0.200000 micro_f1=0.200000 balanced_accuracy=0 |
| dupkeys_after_str | v2prev | False | 0.000000 | 0.0000 | - | - | - | - | - | runner failed before producing a valid result payload: return self.__get_result() / ^^^^^^^^^^^^^^^^^^^ / File |
| dupkeys_after_str | v2 | False | 0.000000 | 0.0000 | - | - | - | - | - | runner failed before producing a valid result payload: return self.__get_result() / ^^^^^^^^^^^^^^^^^^^ / File |
