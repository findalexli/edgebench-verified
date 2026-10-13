| Fixed response | v1 valid | v1 score | v2 valid | v2 score | v2 model calls | v1==v2 structured output |
| --- | --- | ---: | --- | ---: | ---: | --- |
| A_complete_one_deduction_each | True | 77 | True | 77 | 1 | True |
| B_complete_all_zero | True | 0 | True | 0 | 1 | True |
| C_empty_scores | True | 100 | False | 0 | 2 | False |
| D_A_minus_R009 | True | 81 | False | 0 | 2 | False |
| E_B_minus_R009 | True | 15 | False | 0 | 2 | False |
| F_B_R009_rule_score_only | True | 0 | True | 0 | 1 | True |
| G_B_R009_no_score_no_checkpoints | True | 0 | False | 0 | 2 | False |
| H_no_json | False | 0 | False | 0 | 2 | True |
| I_B_R009_score0_zero_checkpoints | True | 15 | False | 0 | 2 | False |
| J_incomplete_then_complete | True | 81 | True | 77 | 2 | False |
| K_nojson_then_complete | False | 0 | True | 77 | 2 | False |
| L_A_without_rule_scores | True | 77 | True | 77 | 1 | True |

history ['A_complete_one_deduction_each', 'C_empty_scores'] v1 (score_first): best_round=C_empty_scores best_score=100.0 best_valid=True
history ['A_complete_one_deduction_each', 'C_empty_scores'] v2 (score_first): best_round=A_complete_one_deduction_each best_score=77.0 best_valid=True
history ['A_complete_one_deduction_each', 'D_A_minus_R009'] v1 (score_first): best_round=D_A_minus_R009 best_score=81.0 best_valid=True
history ['A_complete_one_deduction_each', 'D_A_minus_R009'] v2 (score_first): best_round=A_complete_one_deduction_each best_score=77.0 best_valid=True
history ['B_complete_all_zero', 'I_B_R009_score0_zero_checkpoints'] v1 (score_first): best_round=I_B_R009_score0_zero_checkpoints best_score=15.0 best_valid=True
history ['B_complete_all_zero', 'I_B_R009_score0_zero_checkpoints'] v2 (score_first): best_round=B_complete_all_zero best_score=0.0 best_valid=True
