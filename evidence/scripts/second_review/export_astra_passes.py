#!/usr/bin/env python3
"""Export the Astra passes for publication: task, claim and verdict. Claims judged out of scope (deliberate gaming) stay
internal. Arguments: the internal sweep directory and the output directory."""
import collections, glob, json, os, sys
src, out = sys.argv[1:3]
for d, name in (('astra', 'pass1'), ('round2', 'pass2'), ('round3', 'pass3')):
    rows = []; n = collections.Counter()
    for f in sorted(glob.glob(f'{src}/{d}/*.json')):
        s = open(f).read()
        for c in json.loads(s[s.index('{'): s.rindex('}') + 1]).get('claims', []):
            n[c.get('verdict')] += 1
            if c.get('verdict') != 'OUT_OF_SCOPE':
                rows.append({'task': os.path.basename(f)[:-5], 'claim': c.get('claim'), 'verdict': c.get('verdict')})
    json.dump({'counts_including_withheld': n, 'claims': rows}, open(f'{out}/{name}.json', 'w'), indent=1, ensure_ascii=False)
    print(name, sum(n.values()), dict(n), 'published', len(rows))
