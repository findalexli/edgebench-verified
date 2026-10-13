| Submission | Image | harness valid | score (final) | normalized 0-100 | overall (quality) | macro_f1 | micro_f1 | bal_acc | one_minus_ece | checks / reason |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| baseline | v1 | True | 0.292783 | 29.2783 | 0.332624 | 0.238512 | 0.286840 | 0.293320 | 0.925034 | valid=true final_score=0.292783 overall_score=0.332624 macro_f1=0.238512 micro_f1=0.286840 balanced_accuracy=0 |
| baseline | v2 | True | 0.292702 | 29.2702 | 0.332624 | 0.238512 | 0.286840 | 0.293320 | 0.925034 | valid=true final_score=0.292702 overall_score=0.332624 macro_f1=0.238512 micro_f1=0.286840 balanced_accuracy=0 |
| neighbor | v1 | True | 0.241002 | 24.1002 | 0.281108 | 0.221556 | 0.232853 | 0.233981 | 0.758336 | valid=true final_score=0.241002 overall_score=0.281108 macro_f1=0.221556 micro_f1=0.232853 balanced_accuracy=0 |
| neighbor | v2 | True | 0.241044 | 24.1044 | 0.281108 | 0.221556 | 0.232853 | 0.233981 | 0.758336 | valid=true final_score=0.241044 overall_score=0.281108 macro_f1=0.221556 micro_f1=0.232853 balanced_accuracy=0 |
| nanconf | v1 | True | 0.271465 | 27.1465 | 0.311437 | 0.238512 | 0.286840 | 0.293320 | 0.713160 | valid=true final_score=0.271465 overall_score=0.311437 macro_f1=0.238512 micro_f1=0.286840 balanced_accuracy=0 |
| nanconf | v2 | True | 0.271431 | 27.1431 | 0.311437 | 0.238512 | 0.286840 | 0.293320 | 0.713160 | valid=true final_score=0.271431 overall_score=0.311437 macro_f1=0.238512 micro_f1=0.286840 balanced_accuracy=0 |
| shrink | v1 | True | 0.160264 | 16.0264 | 0.200000 | 0.200000 | 0.200000 | 0.200000 | 0.200000 | valid=true final_score=0.160264 overall_score=0.200000 macro_f1=0.200000 micro_f1=0.200000 balanced_accuracy=0 |
| shrink | v2 | False | 0.000000 | 0.0000 | - | - | - | - | - | runner failed before producing a valid result payload: return self.__get_result() / ^^^^^^^^^^^^^^^^^^^ / File |
| missing_half | v1 | False | 0.289886 | 28.9886 | 0.329924 | 0.234931 | 0.284615 | 0.289286 | 0.927092 | valid=false final_score=0.289886 overall_score=0.329924 macro_f1=0.234931 micro_f1=0.284615 balanced_accuracy= |
| missing_half | v2 | False | 0.000000 | 0.0000 | - | - | - | - | - | runner failed before producing a valid result payload: return self.__get_result() / ^^^^^^^^^^^^^^^^^^^ / File |
