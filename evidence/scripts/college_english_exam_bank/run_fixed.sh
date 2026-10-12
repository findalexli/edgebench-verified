#!/bin/sh
# Usage: run_fixed.sh <grade_with_codex.py> <scoring_dir> <input_dir> <responses_dir> <workdir>
# Runs the ORIGINAL grader main() end to end, with the Codex CLI replaced by fake_codex.sh.
set -e
G="$1"; SC="$2"; IN="$3"; R="$4"; WD="$5"
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$WD/bin" "$WD/sub"; cp "$HERE/fake_codex.sh" "$WD/bin/codex"
echo "placeholder deliverable" > "$WD/sub/A卷原卷.docx.txt"
for f in "$R"/*.txt; do
  n=$(basename "$f" .txt); mkdir -p "$WD/run_$n"; cd "$WD/run_$n"
  HOME="$WD/run_$n" PATH="$WD/bin:$PATH" OPENROUTER_API_KEY=dummy SFORGE_JUDGE_API_KEY=dummy SEBENCH_JUDGE_MODEL=fixed SFORGE_JUDGE_MODEL=fixed FAKE_CODEX_RESPONSE="$f" \
    timeout 60 python3 -I "$G" --report "$WD/sub" --scoring-dir "$SC" --task-id college_english_exam_bank --input-dir "$IN" --timeout 30 \
    > out.txt 2> err.txt || true
  printf '%s\t' "$n"; python3 -c "
import json,sys
t=open('out.txt').read(); s=t.split('>>>>> Start Structured Result')[-1].split('>>>>> End Structured Result')[0]
j=json.loads(s); print('valid=%s score=%s raw=%s/%s' % (j['valid'], j['score'], j['metrics'].get('raw_total'), j['metrics'].get('max_total')))
r=json.load(open('grading_result.json')) if __import__('os').path.exists('grading_result.json') else {}
for x in r.get('scores',[]):
  if x['rule_id']=='R009': print('    R009 ->', x['score'], '/', x['max_score'], '|', x['reason'][-90:])
"
  cd "$WD"
done
