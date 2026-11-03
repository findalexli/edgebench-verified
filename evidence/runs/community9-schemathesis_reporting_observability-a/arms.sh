# Real agent-12 (BODY present, real JUnit writer) and real agent-1 (BODY missing) and variants changed only at the defect, on the old and fixed judge. Pass 1 is the smoke test; both passes reverse the judge order.
for pass in 1; do o="old new"; [ $pass = 2 ] && o="new old"
  for sd in $o; do grade starter-p$pass $sd empty 30; for arm in agent12 agent12_trunc agent12_noerr agent12_brand agent12_nobody agent1 agent1_body; do grade $arm-p$pass $sd $arm.tar.gz 30; done; done
done
