#!/bin/bash
# wait_slot.sh [MAX]: block until the account runs fewer than MAX (default 20) sandboxes.
MAX=${1:-20}; K=$(grep -E '^E2B_API_KEY=' /home/alex/agentsmd-rl/.env | cut -d= -f2- | tr -d '"')
until n=$(curl -s https://api.e2b.dev/sandboxes -H "X-API-Key: $K" | python3 -c "import json,sys;print(len(json.load(sys.stdin)))" 2>/dev/null) && [ "$n" -lt "$MAX" ]; do sleep 60; done
