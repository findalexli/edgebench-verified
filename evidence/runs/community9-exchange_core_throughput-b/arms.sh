# Not the official setting: 8 CPUs, so the scores sit well above the log_max floor and the old-judge credit is clear of it. Same arms as -a; old judge, plus the fixed judge on the two arms that pass the gate.
export JCPU=8
for pass in 1 2 3; do
  seval ctl-p$pass old agent12.tar.gz 150
  seval feeswap-p$pass old feeswap.tar.gz 150
  seval ordercomp-p$pass old ordercomp.tar.gz 150
  seval shutdownbusy-p$pass old shutdownbusy.tar.gz 150
  seval ctl-p$pass new agent12.tar.gz 150
  seval shutdownbusy-p$pass new shutdownbusy.tar.gz 150
done
