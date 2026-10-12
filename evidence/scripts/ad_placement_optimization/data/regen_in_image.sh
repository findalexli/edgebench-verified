#!/bin/bash
# Regenerates seeds 0..49 with the judge image's own tools/bin/gen and byte-compares to cases/.
IMG=seededge/edgebench.judge.ad_placement_optimization@sha256:997d10b59ba063f23429fb8eace84b0cb28ea22b0f9fe5243ef64a2310e19ba9
timeout 120 docker run --rm --name adp-regen --network none --memory 1g --cpus 1 "$IMG" bash -c '
  cd /home/workspace/ad-placement; seq 0 49 > /tmp/s.txt; ./tools/bin/gen /tmp/s.txt -d /tmp/g >/dev/null 2>&1
  same=0; diff=0; for f in cases/*.txt; do if cmp -s $f /tmp/g/$(basename $f); then same=$((same+1)); else diff=$((diff+1)); echo DIFF $f; fi; done
  echo "identical=$same differing=$diff"; ls cases | wc -l'
