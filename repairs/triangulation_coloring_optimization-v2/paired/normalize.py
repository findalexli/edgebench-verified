#!/usr/bin/env python3
"""Parse paired E2B logs with EdgeBench's score_sum parser (sforge 6e4e5f4) and rescale with the
task's (unchanged) anchors. Run from the repo root: python3 <this> <result/out dir> <task.json>"""
import json, re, sys
sys.path.insert(0, '.')
from sforge.harness.log_parsers.score_sum import parse_score_sum
from sforge.harness.grading import extract_score
from sforge.harness import score_rescale as sr
out, task = sys.argv[1], json.load(open(sys.argv[2]))
spec = task['judge']['rescale']
def rescale(raw):
    return None if raw is None else sr.rescale_score(sr.parse_rescale_spec(spec), raw)
for sol in ('donothing', 'greedy', 'nonconvex_flip', 'wrong_count'):
    for v in ('v1', 'v2'):
        txt = open(f'{out}/judge_{v}_{sol}.log').read()
        ok = re.search(r'^CASES_OK (\d+)', txt, re.M).group(1)
        exitc = re.search(r'^exit=(\d+)', txt, re.M).group(1)
        try:
            parse_score_sum(txt); raw = extract_score(txt); valid = raw is not None
        except ValueError as e:
            raw, valid = None, False
        print(json.dumps({'solution': sol, 'version': v, 'cases_ok': f'{ok}/10', 'docker_exit': exitc,
                          'valid': valid, 'raw': raw, 'normalized': rescale(raw) if valid else 0.0}))
