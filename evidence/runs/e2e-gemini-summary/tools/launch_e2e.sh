#!/bin/bash
# launch_e2e.sh QUEUE MAX BUDGET: launch every e2e job in QUEUE (re-read as it grows), keeping < MAX sandboxes
# account-wide; stop at a line END. Uses the 30 GB-disk template (same 8 vCPU / 8 GiB).
Q=$1; MAX=${2:-18}; B=${3:-9600}; cd /home/alex/edgebench-verified; i=0
E=/home/alex/edgebench-verified/evidence/runs/e2e-gemini-summary/tools
K=$(grep -E '^E2B_API_KEY=' /home/alex/agentsmd-rl/.env | cut -d= -f2- | tr -d '"')
while true; do
  j=$(sed -n "$((i+1))p" $Q 2>/dev/null)
  if [ -z "$j" ]; then sleep 30; continue; fi
  [ "$j" = END ] && break
  while true; do n=$(curl -s https://api.e2b.dev/sandboxes -H "X-API-Key: $K" | python3 -c "import json,sys;print(len(json.load(sys.stdin)))" 2>/dev/null || echo 99); [ "$n" -lt "$MAX" ] && break; sleep 60; done
  if [ ! -e evidence/runs/$j/result ]; then
    setsid nohup /home/alex/agentsmd-rl/.venv/bin/python $E/e2e_run.py --job evidence/runs/$j --budget $B --segment 2880 --ckpt 900 \
      --template harbor-worker-v4-s99-25g-v4-20260921-9345d11f --secret gemini_key=/home/alex/edgebench-verified/.internal/gemini_key > evidence/runs/$j.launch.log 2>&1 &
    echo "$(date -u +%H:%M) launched $j (running before: $n)"; sleep 30
  fi
  i=$((i+1))
done; echo QUEUE-DONE
