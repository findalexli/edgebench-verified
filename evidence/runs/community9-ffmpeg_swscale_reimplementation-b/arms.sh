# judge_local with task.toml limits (cpus=4). Speedups are wall-clock ratios.
for pass in 2 3; do o="new old"; [ $((pass%2)) = 0 ] && o="old new"
  for arm in auto18 auto18_err auto18_noop agent7 agent7_err; do for sd in $o; do grade $arm-p$pass $sd $arm.tar.gz 240; done; done
done
