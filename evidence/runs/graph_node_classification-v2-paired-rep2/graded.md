| Submission | Image | harness valid | score (final) | normalized 0-100 | overall (quality) | macro_f1 | micro_f1 | bal_acc | one_minus_ece | checks / reason |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| baseline | v1 | True | 0.292413 | 29.2413 | 0.332624 | 0.238512 | 0.286840 | 0.293320 | 0.925034 | valid=true final_score=0.292413 overall_score=0.332624 macro_f1=0.238512 micro_f1=0.286840 balanced_accuracy=0 |
| baseline | v2 | True | 0.292710 | 29.2710 | 0.332624 | 0.238512 | 0.286840 | 0.293320 | 0.925034 | valid=true final_score=0.292710 overall_score=0.332624 macro_f1=0.238512 micro_f1=0.286840 balanced_accuracy=0 |
| neighbor | v1 | True | 0.241102 | 24.1102 | 0.281108 | 0.221556 | 0.232853 | 0.233981 | 0.758336 | valid=true final_score=0.241102 overall_score=0.281108 macro_f1=0.221556 micro_f1=0.232853 balanced_accuracy=0 |
| neighbor | v2 | True | 0.240848 | 24.0848 | 0.281108 | 0.221556 | 0.232853 | 0.233981 | 0.758336 | valid=true final_score=0.240848 overall_score=0.281108 macro_f1=0.221556 micro_f1=0.232853 balanced_accuracy=0 |
| nanconf | v1 | True | 0.271669 | 27.1669 | 0.311437 | 0.238512 | 0.286840 | 0.293320 | 0.713160 | valid=true final_score=0.271669 overall_score=0.311437 macro_f1=0.238512 micro_f1=0.286840 balanced_accuracy=0 |
| nanconf | v2 | True | 0.271394 | 27.1394 | 0.311437 | 0.238512 | 0.286840 | 0.293320 | 0.713160 | valid=true final_score=0.271394 overall_score=0.311437 macro_f1=0.238512 micro_f1=0.286840 balanced_accuracy=0 |
| shrink | v1 | True | 0.159852 | 15.9852 | 0.200000 | 0.200000 | 0.200000 | 0.200000 | 0.200000 | valid=true final_score=0.159852 overall_score=0.200000 macro_f1=0.200000 micro_f1=0.200000 balanced_accuracy=0 |
| shrink | v2 | False | 0.000000 | 0.0000 | - | - | - | - | - | runner failed before producing a valid result payload: return self.__get_result() / ^^^^^^^^^^^^^^^^^^^ / File |
| missing_half | v1 | False | 0.289583 | 28.9583 | 0.329924 | 0.234931 | 0.284615 | 0.289286 | 0.927092 | valid=false final_score=0.289583 overall_score=0.329924 macro_f1=0.234931 micro_f1=0.284615 balanced_accuracy= |
| missing_half | v2 | False | 0.000000 | 0.0000 | - | - | - | - | - | runner failed before producing a valid result payload: return self.__get_result() / ^^^^^^^^^^^^^^^^^^^ / File |
