# Two bot variants, direct judge script, 300 s budget, morgues kept.
for b in fighter diver2; do
  mkdir -p $O/d/$b/morgue $O/d/$b/w; tar xzf /job/subs/$b.tar.gz -C $O/d/$b/w
  ( docker run --rm --network none -e DCSS_TIMEOUT=300 -v $O/d/$b/w/my_bot.rc:/home/dcss_agent/my_bot.rc -v $O/d/$b/w/my_bot_include.rc:/home/dcss_agent/my_bot_include.rc -v $O/d/$b/morgue:/opt/tiger/game/DCSS/morgue --entrypoint python3 $IMGOLD /judge/eval_dcss.py >$O/d/$b/out.txt 2>&1 ; echo "$b rc=$? t=$(( $(date +%s)-START ))" >>$O/summary.txt ) &
done
wait
