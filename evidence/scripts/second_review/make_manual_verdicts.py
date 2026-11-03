#!/usr/bin/env python3
"""Write the second-review verdicts of Arc and Borden from saved run results. Run from a checkout that holds
evidence/runs/, with the output directory as the argument."""
import glob, json, sys
out = sys.argv[1]
R = 'evidence/runs'
def best(job, task):
    return json.load(open(glob.glob(f'{R}/{job}/result/out/sforge-logs/runs/*/{task}/run_history.json')[0]))['best_score']
def scores(pattern):
    return [json.load(open(f))['raw_score'] for f in sorted(glob.glob(pattern))]
arc = {'task': 'arc_compiler_runtime', 'claims': [{
    'claim': 'Hidden tests require an undocumented analyze() return shape and diagnostic wording.',
    'verdict': 'CONFIRMED', 'witness': 'real modified at the defect: Opus agent-36, same analysis also returned as an array',
    'arms': [{'label': 'agent-36 as submitted, current judge', 'scores': scores(f'{R}/community8-arc_shape/result/out/g/agent36-p*-old.json')},
             {'label': 'agent-36 also returning an array, current judge', 'scores': scores(f'{R}/community8-arc_shape/result/out/g/array-p*-old.json')},
             {'label': 'real run, best on the original task', 'scores': [best('claude-opus-arc_compiler_runtime-v1', 'arc_compiler_runtime')]},
             {'label': 'real run, best with the shape documented', 'scores': [best('claude-opus-arc_compiler_runtime-v2', 'arc_compiler_runtime')]}],
    'job': 'evidence/runs/community8-arc_shape'}]}
bor = {'task': 'borden_source_inversion', 'claims': [{
    'claim': 'Undisclosed amplitude and source-plane conventions penalize a plausible good-faith transport model.',
    'verdict': 'NOT_CONFIRMED', 'witness': 'real run best-of-run',
    'arms': [{'label': 'real run, best raw on the original task', 'scores': [best('claude-opus-borden_source_inversion-v1', 'borden_source_inversion')]},
             {'label': 'real run, best raw with the model documented', 'scores': [best('claude-opus-borden_source_inversion-v2', 'borden_source_inversion')]}],
    'job': 'evidence/runs/claude-opus-borden_source_inversion-v1'}]}
for d in (arc, bor):
    json.dump(d, open(f"{out}/{d['task']}.json", 'w'), indent=1)
    print(d['task'], [(a['label'], a['scores']) for a in d['claims'][0]['arms']])
