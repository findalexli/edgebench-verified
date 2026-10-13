| Fixed response | v1 valid | v1 score | v2prev valid | v2prev score | v2 valid | v2 score | v2prev model calls | v2 model calls | v1==v2 structured output |
| --- | --- | ---: | --- | ---: | --- | ---: | ---: | ---: | --- |
| A_complete_one_deduction_each | True | 77 | True | 77 | True | 77 | 1 | 1 | True |
| B_complete_all_zero | True | 0 | True | 0 | True | 0 | 1 | 1 | True |
| C_empty_scores | True | 100 | False | 0 | False | 0 | 2 | 2 | False |
| D_A_minus_R009 | True | 81 | False | 0 | False | 0 | 2 | 2 | False |
| E_B_minus_R009 | True | 15 | False | 0 | False | 0 | 2 | 2 | False |
| F_B_R009_rule_score_only | True | 0 | True | 0 | True | 0 | 1 | 1 | True |
| G_B_R009_no_score_no_checkpoints | True | 0 | False | 0 | False | 0 | 2 | 2 | False |
| H_no_json | False | 0 | False | 0 | False | 0 | 2 | 2 | True |
| I_B_R009_score0_zero_checkpoints | True | 15 | False | 0 | False | 0 | 2 | 2 | False |
| J_incomplete_then_complete | True | 81 | True | 77 | True | 77 | 2 | 2 | False |
| K_nojson_then_complete | False | 0 | True | 77 | True | 77 | 2 | 2 | False |
| L_A_without_rule_scores | True | 77 | True | 77 | True | 77 | 1 | 1 | True |
| GA_R001_veto_reason_only | True | 3 | False | 0 | False | 0 | 2 | 2 | False |
| GB_R009_extra_checkpoint | True | 15 | False | 0 | False | 0 | 2 | 2 | False |
| GC_R009_flag_without_veto_conditions | True | 15 | False | 0 | False | 0 | 2 | 2 | False |
| GD_R009_floor_after_200_chars | True | 15 | False | 0 | False | 0 | 2 | 2 | False |
| M_R001_negative_checkpoint_veto_marker | True | 0 | True | 0 | True | 0 | 1 | 1 | True |
| N_A_block_then_D_block_one_output | True | 81 | True | 77 | False | 0 | 1 | 2 | False |
| O_D_block_then_A_block_one_output | True | 77 | True | 77 | True | 77 | 1 | 1 | True |
| P_A_block_then_truncated_block_one_output | True | 77 | True | 77 | True | 77 | 1 | 1 | True |
| NA_N_then_A_on_reask | True | 81 | True | 77 | True | 77 | 1 | 2 | False |
| NZ_full_marks_block_then_D_block_one_output | True | 81 | True | 100 | False | 0 | 1 | 2 | False |
| NU_A_then_D_unfenced_one_output | True | 81 | True | 77 | False | 0 | 1 | 2 | False |
| QA_A_R009_score_numeric_string | True | 77 | False | 0 | True | 77 | 2 | 1 | True |
| QB_A_all_scores_padded_decimal_strings | True | 77 | False | 0 | True | 77 | 2 | 1 | True |
| QC_A_R009_score_bool | True | 77 | False | 0 | False | 0 | 2 | 2 | False |
| QD_A_R009_score_word | True | 77 | False | 0 | False | 0 | 2 | 2 | False |
| QE_I_R009_score_string0_zero_checkpoints | True | 15 | False | 0 | False | 0 | 2 | 2 | False |
| QF_F_R009_score_string0_no_checkpoints | True | 0 | False | 0 | False | 0 | 2 | 2 | False |

history ['A_complete_one_deduction_each', 'C_empty_scores'] v1 (score_first): best_round=C_empty_scores best_score=100.0 best_valid=True
history ['A_complete_one_deduction_each', 'C_empty_scores'] v2prev (score_first): best_round=A_complete_one_deduction_each best_score=77.0 best_valid=True
history ['A_complete_one_deduction_each', 'C_empty_scores'] v2 (score_first): best_round=A_complete_one_deduction_each best_score=77.0 best_valid=True
history ['A_complete_one_deduction_each', 'D_A_minus_R009'] v1 (score_first): best_round=D_A_minus_R009 best_score=81.0 best_valid=True
history ['A_complete_one_deduction_each', 'D_A_minus_R009'] v2prev (score_first): best_round=A_complete_one_deduction_each best_score=77.0 best_valid=True
history ['A_complete_one_deduction_each', 'D_A_minus_R009'] v2 (score_first): best_round=A_complete_one_deduction_each best_score=77.0 best_valid=True
history ['B_complete_all_zero', 'I_B_R009_score0_zero_checkpoints'] v1 (score_first): best_round=I_B_R009_score0_zero_checkpoints best_score=15.0 best_valid=True
history ['B_complete_all_zero', 'I_B_R009_score0_zero_checkpoints'] v2prev (score_first): best_round=B_complete_all_zero best_score=0.0 best_valid=True
history ['B_complete_all_zero', 'I_B_R009_score0_zero_checkpoints'] v2 (score_first): best_round=B_complete_all_zero best_score=0.0 best_valid=True
history ['B_complete_all_zero', 'GA_R001_veto_reason_only'] v1 (score_first): best_round=GA_R001_veto_reason_only best_score=3.0 best_valid=True
history ['B_complete_all_zero', 'GA_R001_veto_reason_only'] v2prev (score_first): best_round=B_complete_all_zero best_score=0.0 best_valid=True
history ['B_complete_all_zero', 'GA_R001_veto_reason_only'] v2 (score_first): best_round=B_complete_all_zero best_score=0.0 best_valid=True
history ['A_complete_one_deduction_each', 'NZ_full_marks_block_then_D_block_one_output'] v1 (score_first): best_round=NZ_full_marks_block_then_D_block_one_output best_score=81.0 best_valid=True
history ['A_complete_one_deduction_each', 'NZ_full_marks_block_then_D_block_one_output'] v2prev (score_first): best_round=NZ_full_marks_block_then_D_block_one_output best_score=100.0 best_valid=True
history ['A_complete_one_deduction_each', 'NZ_full_marks_block_then_D_block_one_output'] v2 (score_first): best_round=A_complete_one_deduction_each best_score=77.0 best_valid=True
