# sforge eval, so the archive filter runs. Three passes, order reversed each pass. cpus=4 from task.toml.
for pass in 1 2 3; do o="old new"; [ $pass = 2 ] && o="new old"
  for arm in helper_ok helper_check helper_test inline axiom scratch_broken; do for sd in $o; do seval $arm-p$pass $sd $arm.tar.gz 60; done; done
done
for sd in old new; do grade starter-p1 $sd empty 60; done
