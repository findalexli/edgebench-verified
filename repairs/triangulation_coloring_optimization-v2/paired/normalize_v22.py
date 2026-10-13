#!/usr/bin/env python3
"""Parse the v2.2 paired logs (evidence/runs/triangulation-v22-paired*/result/out/{A,X}) with EdgeBench's
score_sum parser and rescale with the task's (unchanged) anchors.
Run from the repo root: python3 <this> <result/out dir> <task.json>"""
import glob, json, os, re, sys
sys.path.insert(0, '.')
from sforge.harness.log_parsers.score_sum import parse_score_sum
from sforge.harness.grading import extract_score
from sforge.harness import score_rescale as sr
out, task = sys.argv[1], json.load(open(sys.argv[2]))
spec = sr.parse_rescale_spec(task['judge']['rescale'])
for path in sorted(glob.glob(f'{out}/A/*.log') + glob.glob(f'{out}/X/*.log')):
    txt = open(path).read()
    ok = re.search(r'^CASES_OK (\d+)', txt, re.M)
    exitc = re.search(r'^exit=(\d+)', txt, re.M)
    try:
        parse_score_sum(txt); raw = extract_score(txt); valid = raw is not None and raw != float('inf')
    except ValueError:
        raw, valid = None, False
    norm = sr.rescale_score(spec, raw) if valid else None
    print(json.dumps({'arm': os.path.basename(os.path.dirname(path)) + '/' + os.path.basename(path)[:-4],
                      'cases_ok': f'{ok.group(1)}/10' if ok else None, 'docker_exit': exitc.group(1) if exitc else None,
                      'scored': valid, 'raw': 'inf' if raw == float('inf') else raw, 'normalized': None if norm is None else round(norm, 3),
                      'wa': len(re.findall(r' WA ', txt))}))
