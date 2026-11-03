# Same file, same settings, fresh judge container each time, sforge eval (official 4 CPUs, 8g). old = current judge; new = same judge with reset_env seeding the core.
docker run --rm --network none --entrypoint sh $IMGNEW -c 'cd /home/nethack_agent && for i in 1 2 3; do python3 /judge/eval_nethack.py --run-seed 0 | tail -1; done' >$O/d/fix-seed0-starter.txt 2>&1
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do for sd in old new; do seval bot-$i $sd bot.tar.gz 150; done; done
for i in 1 2 3 4 5 6; do for sd in old new; do seval starter-$i $sd starter.tar.gz 100; done; done
