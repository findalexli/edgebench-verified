### Task

juliet_vulnerability_analyzer

### Claim

`scoring/score.py` subtracts 100 points if any submitted `.py` or `.sh` file contains the word `infer`, in any case, even in a comment. The ban targets the Infer tool, but the README itself says "Infer external inputs". This is part of Known issue 3.

### Impact

Measured, six grades per judge per row, no spread:

| Submission | Current judge | With the fix in #35 |
|------------|---------------|---------------------|
| Opus 5.5 analyzer whose docstring has `2. Infer the "bad" (attacker reachable) region of the program from the` | 0 | 79.59 |
| Another analyzer, no such word | 90.70 | 90.70 |
| The same analyzer plus `# Infer external inputs from call facts.` | 0 | 90.70 |

### Evidence and how to reproduce

Add that comment line to any submission's `analyzer.py`, then grade with and without it:

    python3 tools/judge_local.py --task-dir edgebench/tasks/juliet_vulnerability_analyzer --image <judge tag> --archive <submission.tar.gz> --out result.json

### Proposed fix

#35 matches command-like text only. Scores can only rise, and only for submissions containing the word.

### Limits

The check is still a text pattern, and other banned words in comments still zero a submission. Some real `infer` calls no longer match, but Infer is not in the image and the judge is offline.

Found during [EdgeBench Verified](https://lishengzhi.com/edgebench-verified/), our audit of EdgeBench's tasks. Its [page for this task](https://lishengzhi.com/edgebench-verified/tasks/juliet_vulnerability_analyzer.html) covers a different finding.
