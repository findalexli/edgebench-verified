tree_block_partitioning T2 alias re-check. Inputs come only from the original task bytes.
  run_direct.sh <T2 data dir> <outdir>   direct library harness (orig vs patched), output in direct-results.txt
  run_native.sh <scratch with tar/>      pinned judge image, original eval.py --task T2, 4 arms; output in native-results.txt
  make_alias_variant.py                  derives the alias-using T2 submission from the official std.cpp (not redistributed)
  patch_overlay.py                       derives the proposed patched library (swap c/d assignments)
TLA+ model: ../../formal/tla/tree_block_partitioning/run_tlc.sh
