# college_english_exam_bank v2: the grader rejects an assessment that omits, duplicates or
# invents rules, or that scores a deductive rule below max with no recorded deduction; only the
# last scores JSON is scored (an earlier block is used only if the last is truncated or
# unparseable); a plain decimal-string rule score with complete checkpoints is read as that
# number. It re-asks within the original --timeout budget and otherwise reports valid=false
# with score 0 (ranked as 0 by score_first; the run keeps its best other submission) instead
# of filling the gap with full marks.
# Only scoring/grade_with_codex.py changes; rubric, references and work image unchanged.
FROM --platform=linux/amd64 seededge/edgebench.judge.college_english_exam_bank@sha256:8e9eec1057c7ab1b9b48d95cb493aa336b3ec3cea84df5bd80ad04d3009d58a8
COPY files/home/workspace/scoring/grade_with_codex.py /home/workspace/scoring/grade_with_codex.py
