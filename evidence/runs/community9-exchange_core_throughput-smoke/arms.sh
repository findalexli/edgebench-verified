# Smoke: fixed judge on real agent-12, on fee-swapped and completion-flag variants; old judge on real and on the shutdown variant. sforge eval, 4 CPUs, 8g.
seval ctl-s1 new agent12.tar.gz 400
seval ordercomp-s1 new ordercomp.tar.gz 300
seval feeswap-s1 new feeswap.tar.gz 300
seval ctl-s1 old agent12.tar.gz 300
seval shutdownbusy-s1 old shutdownbusy.tar.gz 300
