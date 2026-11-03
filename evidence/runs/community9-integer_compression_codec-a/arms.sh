
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
grade old-flipA-p1 $IMGOLD $TD $S/flipA.tar.gz 60
grade new-flipA-p1 c9/int-new $TDN $S/flipA.tar.gz 60
grade old-flipB-p1 $IMGOLD $TD $S/flipB.tar.gz 60
grade new-flipB-p1 c9/int-new $TDN $S/flipB.tar.gz 60
grade old-top-p1 $IMGOLD $TD $S/top.tar.gz 60
grade new-top-p1 c9/int-new $TDN $S/top.tar.gz 60
grade old-starter-p1 $IMGOLD $TD $S/starter.tar.gz 60
grade new-starter-p1 c9/int-new $TDN $S/starter.tar.gz 60
grade old-bad-p1 $IMGOLD $TD $S/bad.tar.gz 60
grade new-bad-p1 c9/int-new $TDN $S/bad.tar.gz 60
grade new-flipA-p2 c9/int-new $TDN $S/flipA.tar.gz 60
grade old-flipA-p2 $IMGOLD $TD $S/flipA.tar.gz 60
grade new-flipB-p2 c9/int-new $TDN $S/flipB.tar.gz 60
grade old-flipB-p2 $IMGOLD $TD $S/flipB.tar.gz 60
grade new-top-p2 c9/int-new $TDN $S/top.tar.gz 60
grade old-top-p2 $IMGOLD $TD $S/top.tar.gz 60
grade new-starter-p2 c9/int-new $TDN $S/starter.tar.gz 60
grade old-starter-p2 $IMGOLD $TD $S/starter.tar.gz 60
grade new-bad-p2 c9/int-new $TDN $S/bad.tar.gz 60
grade old-bad-p2 $IMGOLD $TD $S/bad.tar.gz 60
grade old-flipA-p3 $IMGOLD $TD $S/flipA.tar.gz 60
grade new-flipA-p3 c9/int-new $TDN $S/flipA.tar.gz 60
grade old-flipB-p3 $IMGOLD $TD $S/flipB.tar.gz 60
grade new-flipB-p3 c9/int-new $TDN $S/flipB.tar.gz 60
grade old-top-p3 $IMGOLD $TD $S/top.tar.gz 60
grade new-top-p3 c9/int-new $TDN $S/top.tar.gz 60
grade old-starter-p3 $IMGOLD $TD $S/starter.tar.gz 60
grade new-starter-p3 c9/int-new $TDN $S/starter.tar.gz 60
grade old-bad-p3 $IMGOLD $TD $S/bad.tar.gz 60
grade new-bad-p3 c9/int-new $TDN $S/bad.tar.gz 60
grade new-flipA-p4 c9/int-new $TDN $S/flipA.tar.gz 60
grade old-flipA-p4 $IMGOLD $TD $S/flipA.tar.gz 60
grade new-flipB-p4 c9/int-new $TDN $S/flipB.tar.gz 60
grade old-flipB-p4 $IMGOLD $TD $S/flipB.tar.gz 60
grade old-flipA-p5 $IMGOLD $TD $S/flipA.tar.gz 60
grade new-flipA-p5 c9/int-new $TDN $S/flipA.tar.gz 60
grade old-flipB-p5 $IMGOLD $TD $S/flipB.tar.gz 60
grade new-flipB-p5 c9/int-new $TDN $S/flipB.tar.gz 60
