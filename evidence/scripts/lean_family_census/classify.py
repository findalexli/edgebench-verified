#!/usr/bin/env python3
"""Census of baseline targets for one Lean task. Same target rule as eval_lean.py (BAD with sorryAx)
and same auxiliary-name regex as scripts/lean_aux_names/classify_baseline.py.
Usage: classify.py <baseline-ListDeclAxiom.out> [weights.json]"""
import re, sys, json, collections
from fractions import Fraction as F
pat = re.compile(r'BAD (\S+) : type=(.*); unexpected=\[(.*?)\]; all=\[(.*?)\]$')
okp = re.compile(r'OK (\S+) : type=(.*); axioms=\[(.*?)\]$')
AUX = re.compile(r'^(.*?)\.(_proof_\d+|_simp_\d+|_sunfold|_unsafe_rec|match_\d+|_sizeOf_\d+|congr_simp|eq_\d+|eq_def|_eq_\d+|proof_\d+)(\..*)?$')
ARGS = [a for a in sys.argv[1:] if not a.startswith('-')]
T, OKS = {}, {}
for line in open(ARGS[0], encoding='utf-8'):
    line = line.rstrip('\n')
    m = pat.search(line)
    if m and 'sorryAx' in m.group(4): T[m.group(1)] = m.group(2); continue
    m = okp.search(line)
    if m: OKS[m.group(1)] = m.group(2)
W = None
if len(ARGS) > 1:
    d = json.load(open(ARGS[1]))
    items = d if isinstance(d, list) else d.get('declarations', d)
    W = {}
    if isinstance(items, dict):
        for k, v in items.items(): W[k] = (F(str(v['weight'] if isinstance(v, dict) else v)), v.get('type') if isinstance(v, dict) else None)
    else:
        for it in items: W[it['decl']] = (F(str(it['weight'])), it.get('type'))
targets = {k: v[1] for k, v in W.items()} if W else T
wt = {k: (W[k][0] if W else F(1)) for k in targets}
tot = sum(wt.values())
aux = {n: AUX.match(n) for n in targets if AUX.match(n)}
kinds = collections.Counter(re.sub(r'\d+', 'N', m.group(2)) for m in aux.values())
print('listing BAD+sorryAx targets', len(T), ' OK decls', len(OKS))
print('scored targets', len(targets), ' total weight', tot)
print('aux targets', len(aux), ' weight', sum(wt[n] for n in aux), f'= {float(sum(wt[n] for n in aux)/tot):.4%}' if tot else '')
print('aux kinds', dict(kinds))
print('aux whose parent is itself a target', sum(1 for m in aux.values() if m.group(1) in targets))
# `autoParam (T) sorry` is how the printer shows an auto-param tactic (e.g. `by volume_tac`): not a hole.
AUTOP = re.compile(r'autoParam \((?:[^()]|\((?:[^()]|\([^()]*\))*\))*\) sorry')
sty = [n for n, t in targets.items() if t and re.search(r'\bsorry\b', AUTOP.sub('autoParam _', t))]
print('targets whose type has `sorry` only as an autoParam tactic (printer artefact, stable):',
      sum(1 for n, t in targets.items() if t and n not in sty and re.search(r'\bsorry\b', t)))
print('targets with `sorry` in type', len(sty), ' (aux', sum(1 for n in sty if n in aux), ')  weight', sum(wt[n] for n in sty))
# lexical class B: P / not P pairs among aux of same parent
by_par = collections.defaultdict(list)
for n, m in aux.items(): by_par[m.group(1)].append(n)
contra, dups = set(), set()
def body(t):
    return re.match(r'^((?:∀ [^,]*, )*)(.*)$', re.sub(r'\s+', ' ', t)).group(2)
for p, ns in by_par.items():
    seen = {}
    for n in sorted((x for x in ns if re.search(r'\._proof_\d+$', x)), key=lambda s: int(s.rsplit('_', 1)[1])):
        if targets[n] in seen: dups.add(n)
        else: seen[targets[n]] = n
    for a in ns:
        for b in ns:
            if a != b and targets[a] and targets[b]:
                ba, bb = body(targets[a]), body(targets[b])
                if ba == '¬' + bb or ba == '¬(' + bb + ')': contra |= {a, b}
print('class B lexical P/¬P aux pairs', len(contra)); print('class C duplicate-type aux copies', len(dups))
if W:
    mism = [k for k in W if k in T and W[k][1] is not None and W[k][1] != T[k]]
    absent = [k for k in W if k not in T]
    print('weights entries not BAD+sorry in listing', len(absent), absent[:30])
    print('weights entries whose type != listing type', len(mism), mism[:30])
    for k in sorted(W): print(f'  W {W[k][0]} {k}{"  [AUX]" if k in aux else ""}')
lostA = set(sty) | contra
print('lower-bound unattainable (A sorry-type + B lexical):', len(lostA), 'weight', sum(wt[n] for n in lostA), f'= {float(sum(wt[n] for n in lostA)/tot):.4%}' if tot else '')
lostC = lostA | dups
print('likely unattainable (+C dups):', len(lostC), 'weight', sum(wt[n] for n in lostC), f'= {float(sum(wt[n] for n in lostC)/tot):.4%}' if tot else '')
if '-v' in sys.argv:
    for n in sty: print('  SORRYTYPE', n, ':', targets[n][:200])
    for n in sorted(contra): print('  CONTRA', n, ':', targets[n][:200])
    for n in sorted(aux): print('  AUX', n)
