#!/bin/bash
# In-image exact convex-hull census for triangulation_coloring_optimization-v2 package v2.2 (issue #57).
# Builds the v2.1 (/job/pkgprev) and v2.2 (/job/pkg) judge and work images, then runs
# geom/v2/hull_check.py (exact integers and Fractions) with each image's own python3 on the cases or samples
# inside that image, and on the original images pulled by digest. Outputs: /job/out/geom/<tag>.jsonl.
set -uo pipefail
. /job/task.env
W1=seededge/edgebench.work.triangulation_coloring_optimization@sha256:618da32c3f4d3b8a79ba840ab7c5d3dc75b42e755ca61c575b784d3976c7cd1f
O=/job/out; mkdir -p $O/geom
pull() { for k in 1 2 3 4 5; do docker pull -q "$1" >> $O/pull.log 2>&1 && return 0; sleep 10; done; return 1; }
pull $V1 && pull $W1 || { echo pull-failed > $O/FAILED; exit 2; }
( cd /job/pkg && docker build -q -f Dockerfile -t ebv/tricol-judge:v22 . && docker build -q -f Dockerfile.work -t ebv/tricol-work:v22 . ) > $O/build.log 2>&1 || exit 3
( cd /job/pkgprev && docker build -q -f Dockerfile -t ebv/tricol-judge:v21 . && docker build -q -f Dockerfile.work -t ebv/tricol-work:v21 . ) >> $O/build.log 2>&1 || exit 3
for t in "v1|$V1|cases" "v21|ebv/tricol-judge:v21|cases" "v22|ebv/tricol-judge:v22|cases" "w1|$W1|sample_data" "w21|ebv/tricol-work:v21|sample_data" "w22|ebv/tricol-work:v22|sample_data"; do
  IFS='|' read -r tag im dir <<<"$t"
  timeout 1200 docker run --rm --network none --memory 2g -v /job/geom:/geom:ro "$im" bash -c "cd $WD && sha256sum $dir/*.txt && python3 -I /geom/v2/hull_check.py $dir/*.txt" > $O/geom/$tag.out 2> $O/geom/$tag.err
  echo "$tag exit=$?" >> $O/geom/status.txt
  grep '^{' $O/geom/$tag.out > $O/geom/$tag.jsonl; grep -v '^{' $O/geom/$tag.out > $O/geom/$tag.sha256
done
docker image rm ebv/tricol-judge:v21 ebv/tricol-judge:v22 ebv/tricol-work:v21 ebv/tricol-work:v22 > /dev/null 2>&1
echo done > $O/DONE
