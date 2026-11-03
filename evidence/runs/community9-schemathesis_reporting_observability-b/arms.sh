# Same arms as job -a; passes 2 and 3 with the judge order reversed in one of them.
for pass in 2 3; do o="old new"; [ $pass = 2 ] && o="new old"
  for sd in $o; do grade starter-p$pass $sd empty 30; for arm in agent12 agent12_trunc agent12_noerr agent12_brand agent12_nobody agent1 agent1_body; do grade $arm-p$pass $sd $arm.tar.gz 30; done; done
done
