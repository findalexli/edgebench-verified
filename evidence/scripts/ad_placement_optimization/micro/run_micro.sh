#!/bin/bash
# Runs the ORIGINAL judge-image tester binary on each micro fixture; compares with oracle.py.
IMG=seededge/edgebench.judge.ad_placement_optimization@sha256:997d10b59ba063f23429fb8eace84b0cb28ea22b0f9fe5243ef64a2310e19ba9
HERE=$(cd "$(dirname "$0")" && pwd)
timeout 300 docker run --rm --name adp-micro --network none --memory 2g --cpus 1 -v "$HERE":/m:ro "$IMG" bash -c '
  T=/home/workspace/ad-placement/tools/bin/tester
  while IFS=$'"'"'\t'"'"' read nm inp out; do
    e=$(timeout 10 $T /m/cases/$inp /m/cases/out_$nm.txt 2>&1 1>/dev/null); x=$?
    printf "%s\t%s\t%s\n" "$nm" "$x" "$e"
  done < /m/fixtures.tsv' > "$HERE/tester_results.tsv"
cat "$HERE/tester_results.tsv"
echo "---- oracle"
while IFS=$'\t' read nm inp out; do
  printf "%s\t%s\n" "$nm" "$(python3 -I "$HERE/../oracle.py" "$HERE/cases/$inp" "$HERE/cases/out_$nm.txt" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d["status"],d.get("score",""),d.get("reason",""),"orig_loop_rejects=%s"%d.get("original_loop_would_reject",""))')"
done < "$HERE/fixtures.tsv" | tee "$HERE/oracle_results.tsv"
