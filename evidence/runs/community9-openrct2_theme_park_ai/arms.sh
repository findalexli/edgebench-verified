# Same real archive, same settings, fresh judge container each time, sforge eval (official: 120 s per scenario, 4 CPUs, 8g).
docker run --rm --network none --entrypoint sh $IMGOLD -c 'cat /judge/openrct2_original_eval.py' >$O/d/openrct2_original_eval.py
for pass in 1 2 3; do for w in auto-30 auto-6 agent-11 auto-45 agent-10; do seval $w-$pass old $w.tar.gz 370; done; done
for pass in 1 2 3; do seval agent-1-$pass old agent-1.tar.gz 370; done
for pass in 4 5; do for w in auto-30 auto-6 agent-11 auto-45 agent-10; do seval $w-$pass old $w.tar.gz 370; done; done
