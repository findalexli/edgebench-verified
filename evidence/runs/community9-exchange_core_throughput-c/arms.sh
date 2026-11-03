# Event half of the claim: results stage stops forwarding events (the proposed completion-flag edit already scores 0). 4 CPUs (official), old and fixed; 8 CPUs, old. Then more 8-CPU control runs with the judge order alternating, to see whether the gate lowers a correct engine's timed score.
for pass in 1 2 3; do seval dropevents-p$pass old dropevents.tar.gz 150; seval dropevents-p$pass new dropevents.tar.gz 60; done
export JCPU=8
for pass in 1 2 3; do seval dropevents8-p$pass old dropevents.tar.gz 120; done
for pass in 4 5 6; do o="new old"; [ $pass = 5 ] && o="old new"; for sd in $o; do seval ctl8-p$pass $sd agent12.tar.gz 120; done; done
