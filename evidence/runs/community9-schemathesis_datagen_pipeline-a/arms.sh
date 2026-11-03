# Real agent-2 as submitted, with only the hidden test's names added (good control), and with a Sunday-first day table or independent date fields (triggers). Pass 1 is the smoke test.
for pass in 1; do o="old new"; [ $pass = 2 ] && o="new old"
  for sd in $o; do grade starter-p$pass $sd empty 30; for arm in agent2 agent2_named agent2_named_sunday agent2_named_indep; do grade $arm-p$pass $sd $arm.tar.gz 30; done; done
done
