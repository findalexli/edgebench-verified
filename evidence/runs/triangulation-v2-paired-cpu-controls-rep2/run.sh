#!/bin/bash
# Re-run of the existing triangulation_coloring_optimization-v2 paired controls (run_original.sh = the package's
# paired/run.sh, unchanged except for --cpus and the output directory) against the CURRENT fixed version, which adds
# the CPU-quota parallelism cap to the flip-rule repair. Run at --cpus 8 (as originally) and at --cpus 4 (the
# publisher's leaderboard setting). Outputs: /job/out/c8/, /job/out/c4/.
set -u
for c in 8 4; do
  sed -e "s|--cpus 8|--cpus $c|" -e "s|^O=/job/out; mkdir -p \$O|O=/job/out/c$c; mkdir -p \$O|" /job/run_original.sh > /job/run_c$c.sh
  grep -q -- "--cpus $c" /job/run_c$c.sh && grep -q "O=/job/out/c$c" /job/run_c$c.sh || { echo "sed failed for $c"; exit 5; }
  bash /job/run_c$c.sh
done
mkdir -p /job/out; for c in 8 4; do ls /job/out/c$c/DONE >/dev/null && echo "c$c done"; done > /job/out/summary.txt
