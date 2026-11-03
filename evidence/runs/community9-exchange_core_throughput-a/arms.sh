# Official setting: sforge eval, 4 CPUs, 8g. Real agent-12 unchanged, with the fee swap, without the maker-completed flag, and with a throwing shutdown. Three passes, judge order alternating.
for pass in 1 2 3; do o="old new"; [ $pass = 2 ] && o="new old"
  for sd in $o; do
    seval ctl-p$pass $sd agent12.tar.gz 170
    seval feeswap-p$pass $sd feeswap.tar.gz 150
    seval ordercomp-p$pass $sd ordercomp.tar.gz 150
    seval shutdownbusy-p$pass $sd shutdownbusy.tar.gz 170
  done
done
