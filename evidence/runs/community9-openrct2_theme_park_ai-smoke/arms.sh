# Direct judge evaluate() in one container per scenario, 150 s, two witnesses at once, with CPU sampling; one official grade of a crash-prone real submission.
docker run --rm --network none --entrypoint sh $IMGOLD -c 'cat /judge/openrct2_original_eval.py' >$O/d/openrct2_original_eval.py
for w in agent-1 agent-10; do mkdir -p /job/plug/$w $O/d/$w; tar xzf /job/subs/$w.tar.gz -C /job/plug/$w; done
for w in agent-1 agent-10; do for sc in large medium small; do
  docker run -d --rm --name l-$w-$sc --network none -v /job:/job -v $O/d/$w:/o --entrypoint python3 $IMGOLD /job/long_one.py /job/plug/$w/my_plugin.js /home/workspace/openrct2/scenarios/scenario_$sc.park 150 /o/raw-$sc.txt >/dev/null
  ( docker logs -f l-$w-$sc >$O/d/$w/out-$sc.txt 2>&1 ) &
done; done
for i in 1 2 3 4 5; do sleep 25; docker stats --no-stream --format '{{.Name}} {{.CPUPerc}} {{.MemUsage}}' >>$O/d/stats.txt; echo --- >>$O/d/stats.txt; done
wait
seval auto-30-1 old auto-30.tar.gz 200
seval auto-30-2 old auto-30.tar.gz 200
