# Direct judge evaluate() with a timeout long enough to reach the monitor's 992-day DONE, one container per scenario so the three fit one worker.
# The engine is real-time capped, so this does not slow it: smoke showed about 0.1-0.55 CPU per engine. CPU is sampled to check.
docker run --rm --network none --entrypoint sh $IMGOLD -c 'cat /judge/openrct2_original_eval.py' >$O/d/openrct2_original_eval.py
for w in agent-1 v2-auto-26; do mkdir -p /job/plug/$w; tar xzf /job/subs/$w.tar.gz -C /job/plug/$w; done
for r in 1 2; do for w in agent-1 v2-auto-26; do mkdir -p $O/d/$w-r$r; for sc in large medium small; do
  docker run -d --name l-$w-r$r-$sc --network none -v /job:/job -v $O/d/$w-r$r:/o --entrypoint python3 $IMGOLD /job/long_one.py /job/plug/$w/my_plugin.js /home/workspace/openrct2/scenarios/scenario_$sc.park 2000 /o/raw-$sc.txt >/dev/null
done; done; done
while [ -n "$(docker ps -q --filter name=l-)" ]; do docker stats --no-stream --format '{{.Name}} {{.CPUPerc}} {{.MemUsage}}' >>$O/d/stats.txt; echo --- >>$O/d/stats.txt; [ $(( $(date +%s)-START )) -gt $LIMIT ] && break; for i in 1 2 3 4 5 6; do sleep 10; done; done
for c in $(docker ps -aq --filter name=l-); do n=$(docker inspect --format '{{.Name}}' $c | tr -d /); docker logs $c >$O/d/$n.out.txt 2>&1; done
docker rm -f $(docker ps -aq --filter name=l-) >/dev/null
