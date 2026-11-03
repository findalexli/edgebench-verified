# Same file, same settings, fresh judge container each time via sforge eval (official 4 CPUs, 8g). Smoke = rca-1, inspected before the repeats are trusted.
seval starter-1 old starter.tar.gz 150
seval rca-1 old rca.tar.gz 400
seval starter-2 old starter.tar.gz 150
for i in 2 3 4 5 6 7 8; do seval rca-$i old rca.tar.gz 400; done
