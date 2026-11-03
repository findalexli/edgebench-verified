
cp -r base new; ( cd new && git apply /job/pr.patch ) || { echo patch-failed; exit 3; }
TDN=/job/new/edgebench/tasks/$T
# Measurement arm only: the tester with the undocumented 2*N*N stop removed (one line), nothing else.
mkdir -p nocap; cat > nocap/Dockerfile <<DF
FROM $IMGOLD
RUN sed -i 's/max_turns = N \* N \* 2$/max_turns = N * N * 2000/' /home/workspace/treants_forest/tools/bin/tester && grep -n 'max_turns = N' /home/workspace/treants_forest/tools/bin/tester
DF
docker build -q -t c9/treant-nocap nocap >$O/build-nocap.log 2>&1 || { echo nocap-build-failed; exit 6; }
docker run --rm --entrypoint grep c9/treant-nocap -n 'max_turns' /home/workspace/treants_forest/tools/bin/tester >>$O/tags.txt
docker run --rm --entrypoint sh $IMGOLD -c 'sha256sum /judge/* /home/workspace/treants_forest/tools/bin/tester; python3 -c "
import glob
s=0
for f in sorted(glob.glob(\"/home/workspace/treants_forest/cases/*\")):
    s+=2*int(open(f).readline().split()[0])**2
print(\"sum2NN\",s)"' >$O/judge.sha 2>&1
S=/job/subs
grade old-agent10-p1 $IMGOLD $TD $S/agent10.tar.gz 100
grade nocap-agent10-p1 c9/treant-nocap $TD $S/agent10.tar.gz 150
grade old-agent40-p1 $IMGOLD $TD $S/agent40.tar.gz 100
grade nocap-agent40-p1 c9/treant-nocap $TD $S/agent40.tar.gz 150
grade old-agent33-p1 $IMGOLD $TD $S/agent33.tar.gz 100
grade nocap-agent33-p1 c9/treant-nocap $TD $S/agent33.tar.gz 150
grade old-agent1-p1 $IMGOLD $TD $S/agent1.tar.gz 100
grade nocap-agent1-p1 c9/treant-nocap $TD $S/agent1.tar.gz 150
grade old-greedy-p1 $IMGOLD $TD $S/greedy.tar.gz 100
grade nocap-greedy-p1 c9/treant-nocap $TD $S/greedy.tar.gz 150
grade new-agent10-p1 $IMGOLD $TDN $S/agent10.tar.gz 100
grade new-agent33-p1 $IMGOLD $TDN $S/agent33.tar.gz 100
grade new-greedy-p1 $IMGOLD $TDN $S/greedy.tar.gz 100
grade old-invalid-p1 $IMGOLD $TD $S/invalid.tar.gz 30
grade new-invalid-p1 $IMGOLD $TDN $S/invalid.tar.gz 30
grade old-starter-p1 $IMGOLD $TD empty 30
grade new-starter-p1 $IMGOLD $TDN empty 30
grade nocap-starter-p1 c9/treant-nocap $TD empty 30
grade old-agent10-p2 $IMGOLD $TD $S/agent10.tar.gz 100
grade nocap-agent10-p2 c9/treant-nocap $TD $S/agent10.tar.gz 150
grade old-agent40-p2 $IMGOLD $TD $S/agent40.tar.gz 100
grade nocap-agent40-p2 c9/treant-nocap $TD $S/agent40.tar.gz 150
grade old-agent33-p2 $IMGOLD $TD $S/agent33.tar.gz 100
grade nocap-agent33-p2 c9/treant-nocap $TD $S/agent33.tar.gz 150
grade old-agent1-p2 $IMGOLD $TD $S/agent1.tar.gz 100
grade nocap-agent1-p2 c9/treant-nocap $TD $S/agent1.tar.gz 150
grade old-greedy-p2 $IMGOLD $TD $S/greedy.tar.gz 100
grade nocap-greedy-p2 c9/treant-nocap $TD $S/greedy.tar.gz 150
grade new-agent10-p2 $IMGOLD $TDN $S/agent10.tar.gz 100
grade new-agent33-p2 $IMGOLD $TDN $S/agent33.tar.gz 100
grade new-greedy-p2 $IMGOLD $TDN $S/greedy.tar.gz 100
grade old-invalid-p2 $IMGOLD $TD $S/invalid.tar.gz 30
grade new-invalid-p2 $IMGOLD $TDN $S/invalid.tar.gz 30
grade old-starter-p2 $IMGOLD $TD empty 30
grade new-starter-p2 $IMGOLD $TDN empty 30
grade nocap-starter-p2 c9/treant-nocap $TD empty 30
