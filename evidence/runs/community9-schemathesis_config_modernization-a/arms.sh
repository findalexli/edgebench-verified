# Real agent-16 (metric returns the same function) and a copy returning a functools.wraps forwarding wrapper. Pass 1 is the smoke test.
for pass in 1; do o="old new"; [ $pass = 2 ] && o="new old"
  for sd in $o; do grade starter-p$pass $sd empty 30; for arm in agent16 agent16_wrapper; do grade $arm-p$pass $sd $arm.tar.gz 30; done; done
done
