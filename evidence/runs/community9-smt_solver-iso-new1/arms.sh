mkdir -p $O/iso
img=$IMGOLD; [ new = new ] && img=$IMGNEW
mkdir -p /job/w/real; tar xzf /job/subs/real.tar.gz -C /job/w/real
t0=$(date +%s)
timeout 3000 docker run --name iso --network none --cpus 8 --memory 7g -v /job/w/real:/sub:ro -v /job/driver.py:/driver.py:ro -v $O/iso:/out --entrypoint bash $img -c '
cp -r /sub /home/workspace/smt_solver_x && cd /home/workspace/smt_solver_x && chmod +x build.sh solve && ./build.sh >/out/build.out 2>&1
python3 /driver.py ./solve /out/res.json > /out/driver.out 2> /out/driver.err; echo driver_rc=$?
cat /sys/fs/cgroup/memory.events; cat /sys/fs/cgroup/memory.peak
' > $O/iso/run.log 2>&1
echo "iso iso-new1 new rc=$? wall=$(( $(date +%s)-t0 ))" >>$O/summary.txt
docker inspect iso --format 'exit={{.State.ExitCode}} oom={{.State.OOMKilled}}' >>$O/summary.txt
