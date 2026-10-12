#!/bin/bash
# Regenerates cases/out_*.txt from fixtures.tsv (non_utf8 is written separately).
HERE=$(cd "$(dirname "$0")" && pwd); cd "$HERE"
while IFS=$'\t' read -r nm inp out; do [ "$nm" = non_utf8 ] && continue; printf -- "$out" > cases/out_$nm.txt; done < fixtures.tsv
printf '0 0 10 10\n10 0 20 \xff\n' > cases/out_non_utf8.txt
