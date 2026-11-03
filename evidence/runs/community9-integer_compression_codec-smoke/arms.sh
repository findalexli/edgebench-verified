
cp -r base new; ( cd new && git apply /job/pr.patch ) || { echo patch-failed; exit 3; }
TDN=/job/new/edgebench/tasks/$T
# new judge = old judge + the one data file the patch changes (the dataset generation layer is not repeated).
mkdir -p nj; cp new/edgebench/tasks/$T/judge/workspace/internal/baseline/baseline_results.json nj/; cat > nj/Dockerfile <<DF
FROM $IMGOLD
COPY baseline_results.json /home/workspace/integer-compression-codec/internal/baseline/baseline_results.json
DF
docker build -q -t c9/int-new nj >$O/build-new.log 2>&1 || { echo new-build-failed; exit 6; }
docker run --rm --entrypoint sh c9/int-new -c 'cd /home/workspace/integer-compression-codec; grep -n "bpi" internal/baseline/baseline_results.json' >>$O/tags.txt
S=/job/subs
grade s-old-top $IMGOLD $TD $S/top.tar.gz 150
grade s-new-top c9/int-new $TDN $S/top.tar.gz 150
grade s-old-starter $IMGOLD $TD $S/starter.tar.gz 150
grade s-new-starter c9/int-new $TDN $S/starter.tar.gz 150
grade s-old-bad $IMGOLD $TD $S/bad.tar.gz 150
