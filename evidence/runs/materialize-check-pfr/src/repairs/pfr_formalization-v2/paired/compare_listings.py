#!/usr/bin/env python3
"""Compare two ListDeclAxiom listings (v1 baseline vs v2 baseline) by declaration name.

Type text is compared after collapsing runs of whitespace (the pretty-printer re-wraps lines when
a name gets longer). Prints: SUMMARY and HASH lines, BAD (scored) sets, every declaration whose line differs, and whether each differing type
becomes identical once the autoParam argument (`sorry` in v1, `<lemma>._auto_N` in v2) is replaced
by a placeholder. Auto-param helper declarations (`*._auto_N`, `_private.*._auto_N`) are reported
separately: they are tactic syntax constants, never scored (axioms=[]).
"""
import re
import sys

LINE = re.compile(r'^(?:info: ListDeclAxiom\.lean:\d+:\d+: )?(OK|BAD) (\S+) : type=(.*?); (axioms|unexpected)=(.*)$')
HASH = re.compile(r'(?:info: ListDeclAxiom\.lean:\d+:\d+: )?(HASH .*|SUMMARY .*)$')
AUTO_ARG = re.compile(r'(autoParam \([^()]*(?:\([^()]*\))?[^()]*\)) (sorry|[\w.\']+\._auto_\d+)')


def load(p):
    out = {}
    for ln in open(p, encoding='utf-8'):
        m = LINE.match(ln.rstrip('\n'))
        if m:
            out[m.group(2)] = (m.group(1), ' '.join(m.group(3).split()), m.group(4) + '=' + m.group(5))
    return out


def tail(p):
    return [m.group(1) for ln in open(p, encoding='utf-8') if (m := HASH.match(ln.rstrip('\n')))]


def is_helper(n):
    return re.search(r'\._auto_\d+$', n) is not None


a, b = load(sys.argv[1]), load(sys.argv[2])
print('v1:', '; '.join(tail(sys.argv[1])))
print('v2:', '; '.join(tail(sys.argv[2])))
bad_a = {n for n, v in a.items() if v[0] == 'BAD'}
bad_b = {n for n, v in b.items() if v[0] == 'BAD'}
print(f'declarations: v1={len(a)} v2={len(b)}; BAD: v1={len(bad_a)} v2={len(bad_b)}; same BAD names: {bad_a == bad_b}')
ha = sorted(n for n in a if is_helper(n)); hb = sorted(n for n in b if is_helper(n))
print(f'auto-param helpers: v1={len(ha)} v2={len(hb)} (all OK, axioms=[]: '
      f'{all(a[n][0] == "OK" for n in ha) and all(b[n][0] == "OK" for n in hb)})')
others = sorted((set(a) | set(b)) - set(ha) - set(hb))
diff = [n for n in others if a.get(n) != b.get(n)]
print(f'non-helper declarations whose line differs: {len(diff)}')
for n in diff:
    va, vb = a.get(n), b.get(n)
    if va is None or vb is None:
        print(f'  {n}: only in {"v2" if va is None else "v1"}')
        continue
    na = AUTO_ARG.sub(r'\1 <AUTO>', va[1]); nb = AUTO_ARG.sub(r'\1 <AUTO>', vb[1])
    args_a = [m.group(2) for m in AUTO_ARG.finditer(va[1])]
    args_b = [m.group(2) for m in AUTO_ARG.finditer(vb[1])]
    print(f'  {n}: status {va[0]}->{vb[0]}; axioms {va[2]} -> {vb[2]}; '
          f'type identical apart from autoParam argument: {na == nb}; v1 args {args_a}; v2 args {args_b}')
