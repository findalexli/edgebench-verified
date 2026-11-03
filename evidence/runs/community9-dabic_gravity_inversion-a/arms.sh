# sforge eval (timeouts matter): cpus=4, SFORGE_CPUS=4. Three passes, order reversed on the second.
for pass in 1 2 3; do o="old new"; [ $pass = 2 ] && o="new old"
  for arm in auto35 auto35_model auto35_const; do e=120; [ $arm != auto35 ] && e=600; for sd in $o; do seval $arm-p$pass $sd $arm.tar.gz $e; done; done
done
