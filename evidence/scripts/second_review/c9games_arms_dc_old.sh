# Same files, same settings, fresh judge container each time, sforge eval (official 900 s budget, 4 CPUs, 8g). Two gradings at a time on this 8-vCPU worker (4 CPUs each): fighter and the shipped starter.
SIDE=__SIDE__
for i in 1 2 3; do
  seval fighter-$i $SIDE fighter.tar.gz 1020 &
  seval starter-$i $SIDE starter.tar.gz 1020 &
  wait
done
