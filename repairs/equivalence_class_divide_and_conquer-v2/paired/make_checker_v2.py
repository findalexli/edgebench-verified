"""Write the v2 T3 checker: include the last created state t[tt] in the final cost sweep.
Usage: python3 -I make_checker_v2.py <original checker.cpp> <out checker.cpp>"""
import sys, hashlib
raw = open(sys.argv[1], 'rb').read()
assert hashlib.sha256(raw).hexdigest() == 'f92b52cc37615e28e906d461cf9607ad42e8ea7bdac2a56fd215fc070edd4145'
s = raw
for old, new in [(b'std::iota(oq, oq+tt, 0), std::sort(oq, oq+tt, ', b'std::iota(oq, oq+tt+1, 0), std::sort(oq, oq+tt+1, '),
                 (b'for (int i=0, j=0; i<tt; w+=', b'for (int i=0, j=0; i<=tt; w+=')]:
    assert s.count(old) == 1, old
    s = s.replace(old, new, 1)
open(sys.argv[2], 'wb').write(s)
print('v2 checker sha256', hashlib.sha256(s).hexdigest())
