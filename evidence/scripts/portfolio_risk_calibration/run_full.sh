#!/bin/sh
# Full original harness with the image's shipped example optimizer as the submission, then post-hoc.
set -e
cp /home/workspace/scoring/portfolio_optimizer.py /home/workspace/portfolio_optimizer.py
cd /home/workspace
cp scoring/etf_prices_test.csv scoring/etf_info.csv scoring/macro_indicators_test.csv scoring/test_period.txt scoring/true_risk_events.json .
python3 /home/workspace/scoring/eval_script.py > /tmp/eval.log 2>&1 || true
grep -n -i "excess\|Information Ratio\|Sortino\|Final total score" /tmp/eval.log | tail -20
python3 /s/posthoc.py
