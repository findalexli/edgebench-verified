#!/usr/bin/env python3
"""Map raw TOTAL_SCORE values through the task's own rescale (harness code) and print anchors per file."""
import json, sys
REPO = __import__('os').environ.get('EBV_REPO') or str(__import__('pathlib').Path(__file__).resolve().parents[3])
sys.path.insert(0, REPO)
from sforge.harness.score_rescale import parse_rescale_spec, rescale_score
spec_d = json.load(open(REPO + '/tasks/warehouse_forklift_routing.json'))['judge']['rescale']
spec = parse_rescale_spec(spec_d)
for k in ('baseline', 'rank30', 'rank1', 'super_anchor'):
    v = spec_d[k]; print("%-12s %12.4f  per-file(/50) %9.4f  per-file(/18) %9.4f  per-file(/20) %9.4f" % (k, v, v / 50, v / 18, v / 20))
for raw in [float(x) for x in sys.argv[1:]]:
    print("raw %.4f -> normalized %.4f" % (raw, rescale_score(spec, raw)))
