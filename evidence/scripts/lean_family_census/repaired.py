#!/usr/bin/env python3
"""Print repaired / type_changed / disappeared target names from eval_lean.py report files (stdout incl. build log)."""
import json, sys
for p in sys.argv[1:]:
    s = open(p, encoding='utf-8').read(); i = s.find('>>>>> Start Structured Result'); j = s.find('{', i)
    r = json.loads(s[j:s.rfind('}') + 1]); m = r['metrics']
    print(p, 'score', r['score'], r['summary'])
    for k in ('repaired', 'type_changed', 'disappeared'):
        for n in m[k]: print('  ', k.upper(), n)
