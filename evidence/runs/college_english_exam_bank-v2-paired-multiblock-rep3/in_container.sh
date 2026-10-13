#!/bin/bash
# Runs inside a judge container (v1 original or v2). Runs the ORIGINAL eval_cmd via the
# TaskSpec-generated eval.sh, with only the `codex` executable replaced by fake_codex.sh.
# Usage: in_container.sh <label> ; inputs in /p, outputs in /o
set -u
L=$1
cd /home/workspace
sha256sum scoring/grade_with_codex.py scoring/rubrics.json > /o/$L.pins.txt
python3 /p/make_responses.py scoring/rubrics.json /tmp/resp > /dev/null; python3 /p/make_responses_v2.py /tmp/resp; python3 /p/make_responses_gaps.py /tmp/resp; python3 /p/make_responses_multiblock.py /tmp/resp
mkdir -p /tmp/bin; cp /p/fake_codex.sh /tmp/bin/codex
# placeholder deliverable (the fixed responses do not read the submission)
echo "placeholder deliverable" > "/home/workspace/A卷原卷.docx"
while read -r name seq; do
  files=$(echo "$seq" | tr ':' '\n' | sed 's#^#/tmp/resp/#; s#$#.txt#' | paste -sd: -)
  H=/tmp/home_$name; mkdir -p $H
  HOME=$H PATH=/tmp/bin:$PATH OPENROUTER_API_KEY=dummy SFORGE_JUDGE_API_KEY=dummy SEBENCH_JUDGE_MODEL=fixed SFORGE_JUDGE_MODEL=fixed FAKE_CODEX_RESPONSE="$files" \
    timeout 900 bash /p/eval.sh > /o/$L.$name.raw.txt 2>&1
  echo "$(cat $H/fake_codex_calls 2>/dev/null || echo 0)" > /o/$L.$name.calls.txt
done < /p/cases.txt
