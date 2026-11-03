# Same arms as job -a; passes 2 and 3 with the judge order reversed in one of them. One sforge eval pair for the real harness path.
for pass in 2 3; do o="old new"; [ $pass = 2 ] && o="new old"
  for sd in $o; do grade starter-p$pass $sd empty 30; for arm in agent16 agent16_wrapper; do grade $arm-p$pass $sd $arm.tar.gz 30; done; done
done
for sd in old new; do seval wrapper-s1 $sd agent16_wrapper.tar.gz 60; done
