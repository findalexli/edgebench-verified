## What and why

Task finding: #39.

`score.py` subtracts 100 points if any submitted `.py` or `.sh` file contains the word `infer`, in any case, even in a comment. The README bans calling the Infer tool, but it also says "Infer external inputs". An Opus 5.5 analyzer had this docstring line and scored 0 instead of 79.59:

```
2. Infer the "bad" (attacker reachable) region of the program from the
```

The check now matches `infer --`, `infer run --`, `infer capture --`, `infer analyze --`, and a string `"infer"` (or a path ending in it) right after `(` or `[`. It is still a text pattern. Harmless text of those shapes, such as `stats["infer"]`, still scores 0. Some real calls, such as `infer -j 4 run`, no longer match, but Infer is not in the image and the judge is offline. Nothing newly matches, so scores can only rise, and only for submissions containing the word.

This fixes part of Known issue 3; other banned words in comments still zero a submission (last row).

## Checklist for task changes

- [x] `version` in `task.toml` is bumped (any change that can move scores).
- [x] `NOTES.md`: the change and its score effect are under **Changes**; Known issue 3 stays, with its example changed.
- [x] Old vs new judge on the same submissions, on the same host, results below.
- [x] New blobs: none.

## Old vs new judge

`tools/judge_local.py`, old judge built from 1187e2c, new judge from this branch. Six grades per judge per row: two on each of three workers, reversing judge order. Scores had zero spread. The added call lines are never executed; the ban is a text check.

| Submission | Old | New |
|------------|-----|-----|
| Opus 5.5 analyzer with the line above | 0 | 79.59 |
| Best analyzer from another Opus 5.5 run, no banned word | 90.70 | 90.70 |
| That analyzer + `# Infer external inputs from call facts.` | 0 | 90.70 |
| That analyzer + `# we infer the sink from the token facts` | 0 | 90.70 |
| That analyzer + `# infer run lengths from buffer sizes` | 0 | 90.70 |
| That analyzer + `subprocess.run(["infer", "run", "--", "gcc"])` | 0 | 0 |
| That analyzer + `subprocess.run(["/opt/infer/bin/infer", "run", "--", "gcc"])` | 0 | 0 |
| That analyzer + `scan.sh` containing `infer run -- gcc` | 0 | 0 |
| Empty starter | 10 | 10 |
| Crashing analyzer | 10 (invalid) | 10 (invalid) |
| That analyzer + `# does not use CodeQL` | 0 | 0 |


