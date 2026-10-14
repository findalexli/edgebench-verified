| Submission | Image | harness valid | score (final) | normalized 0-100 | overall (quality) | macro_f1 | micro_f1 | bal_acc | one_minus_ece | checks / reason |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| nanconf | v1 | True | 0.271422 | 27.1422 | 0.311437 | 0.238512 | 0.286840 | 0.293320 | 0.713160 | valid=true final_score=0.271422 overall_score=0.311437 macro_f1=0.238512 micro_f1=0.286840 balanced_accuracy=0 |
| nanconf | v2prev | True | 0.271400 | 27.1400 | 0.311437 | 0.238512 | 0.286840 | 0.293320 | 0.713160 | valid=true final_score=0.271400 overall_score=0.311437 macro_f1=0.238512 micro_f1=0.286840 balanced_accuracy=0 |
| nanconf | v2 | True | 0.271509 | 27.1509 | 0.311437 | 0.238512 | 0.286840 | 0.293320 | 0.713160 | valid=true final_score=0.271509 overall_score=0.311437 macro_f1=0.238512 micro_f1=0.286840 balanced_accuracy=0 |
| shrink | v1 | True | 0.159914 | 15.9914 | 0.200000 | 0.200000 | 0.200000 | 0.200000 | 0.200000 | valid=true final_score=0.159914 overall_score=0.200000 macro_f1=0.200000 micro_f1=0.200000 balanced_accuracy=0 |
| shrink | v2prev | False | 0.000000 | 0.0000 | - | - | - | - | - | runner failed before producing a valid result payload: return self.__get_result() / ^^^^^^^^^^^^^^^^^^^ / File |
| shrink | v2 | False | 0.000000 | 0.0000 | - | - | - | - | - | runner failed before producing a valid result payload: return self.__get_result() / ^^^^^^^^^^^^^^^^^^^ / File |
| missing_half | v1 | False | 0.289915 | 28.9915 | 0.329924 | 0.234931 | 0.284615 | 0.289286 | 0.927092 | valid=false final_score=0.289915 overall_score=0.329924 macro_f1=0.234931 micro_f1=0.284615 balanced_accuracy= |
| missing_half | v2prev | False | 0.000000 | 0.0000 | - | - | - | - | - | runner failed before producing a valid result payload: return self.__get_result() / ^^^^^^^^^^^^^^^^^^^ / File |
| missing_half | v2 | False | 0.000000 | 0.0000 | - | - | - | - | - | runner failed before producing a valid result payload: return self.__get_result() / ^^^^^^^^^^^^^^^^^^^ / File |
