#!/usr/bin/env bash
# Re-run every model configuration; writes tlc_<cfg>.out next to this file.
set -euo pipefail
cd "$(dirname "$0")"
J=../../../tools/tla2tools.jar
META=$(mktemp -d)
for c in *.cfg; do b=${c%.cfg}
  timeout 300 java -cp "$J" tlc2.TLC -workers 2 -metadir "$META/$b" -config "$c" KnownFailureCredit.tla > "tlc_$b.out" 2>&1 || true
  echo "$b: $(grep -E 'is violated|No error has been found|distinct states found' "tlc_$b.out" | tr '\n' ' ')"
done
rm -rf "$META"; rm -f KnownFailureCredit_TTrace_*.bin
