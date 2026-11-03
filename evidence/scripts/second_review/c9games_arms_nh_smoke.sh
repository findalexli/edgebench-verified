# one arm of each, plus a direct seed check of the fix
docker run --rm --network none --entrypoint sh $IMGNEW -c 'cd /home/nethack_agent && for i in 1 2 3; do python3 /judge/eval_nethack.py --run-seed 0 | tail -1; done' >$O/d/fix-seed0-starter.txt 2>&1
seval bot-1 old bot.tar.gz 300
seval bot-1 new bot.tar.gz 300
seval starter-1 old starter.tar.gz 120
