
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
grade s-old-agent10 $IMGOLD $TD $S/agent10.tar.gz 200
grade s-new-agent10 $IMGOLD $TDN $S/agent10.tar.gz 200
grade s-nocap-agent10 c9/treant-nocap $TD $S/agent10.tar.gz 300
