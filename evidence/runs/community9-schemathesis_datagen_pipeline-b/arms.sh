# Real agent-2; with the hidden names only; with names and hidden range patterns (agent2_full, control); plus a Sunday-first table or independent date fields (triggers). Three passes, judge order alternating.
for pass in 1 2 3; do o="old new"; [ $pass = 2 ] && o="new old"
  for sd in $o; do for arm in agent2 agent2_named agent2_full agent2_full_sunday agent2_full_indep; do grade $arm-p$pass $sd $arm.tar.gz 30; done; done
done
