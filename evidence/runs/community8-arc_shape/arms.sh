# Real Opus submission agent-36 on the current judge, as submitted and with analyze() also returning its own diagnostics as an array. Two passes.
for pass in 1 2; do grade agent36-p$pass old agent36.tar.gz 400; grade array-p$pass old agent36_array.tar.gz 400; done
