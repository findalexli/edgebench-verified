#!/usr/bin/env python3
"""Generate evidence/formal/SUMMARY.md (every formal result, one row per task) from evidence/formal/summary.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from names import names  # noqa: E402

rows = json.loads((ROOT / 'evidence/formal/summary.json').read_text())['rows']
n = names()
L = ['# Formal results', '',
     'Every task with a Lean 4 or TLA+ result. Each row links to a note that states the claim, the model and its link to '
     'the grader code, the counter-check that must fail, and the limits. All results rerun with '
     '`python3 tools/check_formal.py` (log: [RECHECK.md](RECHECK.md)).', '',
     '| Task | Tool | Result | Covers | What is proved or checked | Limit |', '| --- | --- | --- | --- | --- | --- |']
for r in rows:
    L.append(f"| [{n[r['task']]}](notes/{r['task']}.md) | {r['tool']} | {r['result']} | {r['covers']} | {r['what']} | {r['limit']} |")
(ROOT / 'evidence/formal/SUMMARY.md').write_text('\n'.join(L) + '\n')
print(len(rows), 'rows')
