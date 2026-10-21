#!/bin/bash
# Probe: can the pfr work + judge images fit on the 30 GB worker with dockerd's classic overlay2 store
# (no retained compressed layers) instead of the containerd image store?
O=/job/out; mkdir -p $O
{ docker info 2>/dev/null | grep -i -E "storage driver|driver-type|containerd"; cat /etc/docker/daemon.json 2>/dev/null; ps aux | grep -E "[d]ockerd|[c]ontainerd" | cut -c1-200; df -h / | tail -1; } > $O/before.txt 2>&1
mkdir -p /etc/docker; python3 - <<'P'
import json, os
p = '/etc/docker/daemon.json'; d = json.load(open(p)) if os.path.exists(p) else {}
d.setdefault('features', {})['containerd-snapshotter'] = False
json.dump(d, open(p, 'w'))
P
cat /etc/docker/daemon.json > $O/daemon.json
(systemctl restart docker || service docker restart || { pkill dockerd; sleep 3; nohup dockerd > /tmp/dockerd.log 2>&1 & }) > $O/restart.log 2>&1
for i in $(seq 30); do docker info >/dev/null 2>&1 && break; sleep 2; done
docker info 2>/dev/null | grep -i -E "storage driver|driver-type" > $O/after.txt
for img in seededge/edgebench.judge.pfr_formalization:9ed39cf76869 seededge/edgebench.work.pfr_formalization:508bdc207859; do
  docker pull -q $img >> $O/pull.log 2>&1; echo "rc=$? $img" >> $O/pull.log; df -h / | tail -1 >> $O/pull.log
done
docker system df >> $O/after.txt 2>&1
