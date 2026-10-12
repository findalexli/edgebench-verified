# Formal re-check log

Recorded 2026-10-12T08:30Z by `python3 tools/check_formal.py` (TLA+ via TLC; Lean files recompiled in a --memory 4g container).

```
OK  Lean FinanceExcessFx.lean: 9 theorems, axioms match published: True
OK  Lean LeanAnalysisLocal.lean: 5 theorems, axioms match published: True
OK  Lean WarehouseBound.lean: 3 theorems, axioms match published: True
OK  Lean WarehouseCheck.lean: 3 theorems, axioms match published: True
OK  Lean WarehouseData.lean: 3 theorems, axioms match published: True
5 formal checks, 0 mismatches
OK  TLA+ rust_multicrate_reconstruction/corrected_ex1_CreditSound: no-error (published: no-error)
OK  TLA+ rust_multicrate_reconstruction/corrected_ex1_PassSound: no-error (published: no-error)
OK  TLA+ rust_multicrate_reconstruction/corrected_ex1_PassSoundExemptSilent: no-error (published: no-error)
OK  TLA+ rust_multicrate_reconstruction/corrected_ex1_PassSoundExemptSilent_expected3: violated (published: violated)
OK  TLA+ rust_multicrate_reconstruction/corrected_ex2_CreditSound: no-error (published: no-error)
OK  TLA+ rust_multicrate_reconstruction/corrected_ex2_PassSound: no-error (published: no-error)
OK  TLA+ rust_multicrate_reconstruction/original_ex1_CreditSound: violated (published: violated)
OK  TLA+ rust_multicrate_reconstruction/original_ex1_PassSound: violated (published: violated)
OK  TLA+ rust_multicrate_reconstruction/original_ex1_PassSoundExemptSilent: no-error (published: no-error)
OK  TLA+ rust_multicrate_reconstruction/original_ex1_PassSoundExemptSilent_expected3: violated (published: violated)
OK  TLA+ rust_multicrate_reconstruction/original_ex2_CreditSound: violated (published: violated)
OK  TLA+ rust_multicrate_reconstruction/original_ex2_PassSound: violated (published: violated)
OK  TLA+ tree_block_partitioning/alias_orig: violated (published: violated)
OK  TLA+ tree_block_partitioning/alias_patched: no-error (published: no-error)
OK  TLA+ tree_block_partitioning/noalias_orig: no-error (published: no-error)
OK  TLA+ tree_block_partitioning/noalias_patched: no-error (published: no-error)
16 formal checks, 0 mismatches
```

All 21 formal results (16 TLA+ configurations, 5 Lean files) reproduce their published outcomes. The two `installed_*_inconsistent` theorems in LeanAnalysisLocal deliberately depend on `sorryAx` (they apply the refutations to the task's installed, sorried constants); no other theorem does. `Refute.lean` (evidence/scripts/lean_analysis_proofs/) needs the 33 GB task image and is not part of this routine check.
