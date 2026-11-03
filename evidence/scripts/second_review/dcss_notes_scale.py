#!/usr/bin/env python3
"""Upstream's recorded raw range for one DCSS bot on the 0-100 scale, using EdgeBench's own rescale.
Arguments: a checkout of EdgeBench community @ 1187e2c, and the output JSON path."""
import json, sys, tomllib
from pathlib import Path
root = Path(sys.argv[1]); sys.path.insert(0, str(root))
from sforge.harness.score_rescale import RescaleSpec, rescale_score
task = root / 'edgebench/tasks/dcss_dungeon_ai'
s = tomllib.loads((task / 'task.toml').read_text())['score']['rescale']
spec = RescaleSpec(**s)
row = [l for l in (task / 'NOTES.md').read_text().splitlines() if '5211.2' in l][0]
out = {'source': 'edgebench/tasks/dcss_dungeon_ai/NOTES.md', 'row': row, 'rescale': s,
       'scores': {str(r): rescale_score(spec, r) for r in (1556.0, 5211.2)}}
json.dump(out, open(sys.argv[2], 'w'), indent=1, ensure_ascii=False); print(out)
