#!/usr/bin/env python3
"""Ordinal helper-name exclusions: sforge eval scores per arm and judge from community9-ordinal_notation_well_foundedness, the feedback a solver sees,
and the publisher's historical scores quoted from the task NOTES (no Opus run of this task exists). Usage: <table>.py [upstream tree]"""
import glob, json, os, re, sys
R = 'evidence/runs/community9-ordinal_notation_well_foundedness/result/out/'
rows = {}
for f in glob.glob(R + 's/*.report.json'):
    m = re.match(r'(.+)-p(\d)-(old|new)\.report\.json', os.path.basename(f))
    d = json.load(open(f))
    rows.setdefault((m.group(1), m.group(3)), []).append((d['score'], d['score_0_100'], d['valid'], d['details'][0]['message'].split('\n')[-1][:90]))
print('arm judge n raw score_0_100 task1_message')
for k in sorted(rows):
    v = rows[k]
    print(k[0], k[1], len(v), [x[0] for x in v], [round(x[1], 4) for x in v], v[0][3])
for f in sorted(glob.glob(R + 'g/starter*.json')):
    d = json.load(open(f)); print(os.path.basename(f), d['raw_score'], d['score_0_100'], d['valid'])
print('env', open(R + 'env.txt').read().split()[0], 'vCPU worker; task cpus=4; head', re.findall(r'^[0-9a-f]{40}$', open(R + 'env.txt').read(), re.M))
print('opus runs', len(glob.glob('evidence/runs/claude-opus-ordinal_notation_well_foundedness*/')))
if len(sys.argv) > 1:
    n = open(sys.argv[1] + '/edgebench/tasks/ordinal_notation_well_foundedness/NOTES.md').read()
    print('NOTES:', re.findall(r'\| historical [^\n]*', n))
