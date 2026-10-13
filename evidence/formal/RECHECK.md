# Formal re-check log

Recorded 2026-10-13T02:56Z by `python3 tools/check_formal.py`. TLA+ runs with TLC; each Lean file is recompiled one at a time in a `--memory 4g` container. A check passes only if TLC reproduces the published outcome (no error, or the expected violation for a counter-check), or if Lean compiles with no error and no `sorry` and prints the same axioms as the published output.

```
OK  TLA+ order_addition_permutation_optimization/claims: no-error (published: no-error)
OK  TLA+ order_addition_permutation_optimization/k1_orig_best_valid: violated (published: violated)
OK  TLA+ order_addition_permutation_optimization/k2_fixed_eq_scorefirst: violated (published: violated)
OK  TLA+ order_addition_permutation_optimization/k3_rate_as_score: violated (published: violated)
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
OK  Lean BipedalCap.lean: 10 theorems, axioms match published: True
OK  Lean BordenScale.lean: 8 theorems, axioms match published: True
OK  Lean CollegeEnglishGrader.lean: 24 theorems, axioms match published: True
OK  Lean CtaFxCheck.lean: 12 theorems, axioms match published: True
OK  Lean DatagenHttpDate.lean: 7 theorems, axioms match published: True
OK  Lean EquivClassCost.lean: 18 theorems, axioms match published: True
OK  Lean ExchangeGate.lean: 16 theorems, axioms match published: True
OK  Lean FfmpegTimedCredit.lean: 10 theorems, axioms match published: True
OK  Lean FinanceExcessFx.lean: 9 theorems, axioms match published: True
OK  Lean GraphNodeValidation.lean: 11 theorems, axioms match published: True
OK  Lean GridTuringBaseline.lean: 8 theorems, axioms match published: True
OK  Lean IntCodecScale.lean: 18 theorems, axioms match published: True
OK  Lean JaguaOverlap.lean: 18 theorems, axioms match published: True
OK  Lean LeanAnalysisLocal.lean: 5 theorems, axioms match published: True
OK  Lean PortfolioOrderRealExp.lean: 6 theorems, axioms match published: True
OK  Lean SchemathesisTests.lean: 16 theorems, axioms match published: True
OK  Lean SmtWitness.lean: 14 theorems, axioms match published: True
OK  Lean TimeBudgets.lean: 18 theorems, axioms match published: True
OK  Lean TreantRescale.lean: 21 theorems, axioms match published: True
OK  Lean TriangulationFlip.lean: 12 theorems, axioms match published: True
OK  Lean VibratingZeroHit.lean: 8 theorems, axioms match published: True
OK  Lean WarehouseBound.lean: 3 theorems, axioms match published: True
OK  Lean WarehouseCheck.lean: 3 theorems, axioms match published: True
OK  Lean WarehouseData.lean: 4 theorems, axioms match published: True
OK  Lean WirelessCeInvariance.lean: 9 theorems, axioms match published: True
45 formal checks, 0 mismatches
```

All 45 formal checks reproduce: 25 Lean files and 20 TLA+ runs over 3 models. The two `installed_*_inconsistent` theorems in LeanAnalysisLocal deliberately depend on `sorryAx`, because they apply the refutations to the task's installed, sorried constants; no other theorem does. What each result establishes, and where it stops: [SUMMARY.md](SUMMARY.md).
