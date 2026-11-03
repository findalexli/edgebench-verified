# Bad controls for the fix: model-space with np.linalg.det (the gate must keep failing it) and data-space with beta left alone.
for pass in 1 2; do o="old new"; [ $pass = 2 ] && o="new old"
  for arm in auto35_baddet auto35_dconst; do for sd in $o; do seval $arm-p$pass $sd $arm.tar.gz 600; done; done
done
