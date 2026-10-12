"""Derive an ordinary wrong T2 submission from the official std.cpp: MergeBlock drops the
second factor (Tmp.info[tc] *= GetInfo (b, ...)), so merged block values are wrong.
This is a plain logic error that the normal T2 tests should catch on both library versions.
Usage: python3 -I make_invalid_variant.py <std.cpp> <out T2.cpp>"""
import sys, hashlib
raw = open(sys.argv[1], 'rb').read()
assert hashlib.sha256(raw).hexdigest() == 'e5fc6e9ba50eb4019c4ca710720d04569b918909f6796f1fb9e2377bb74dc657'
s = raw.decode()
old = "\t\t\tTmp.info[tc] *= GetInfo (b, cxb, cyb);\n"
if old not in s:
    old = old.replace("\n", "\r\n")
assert s.count(old) == 1, 'context'
open(sys.argv[2], 'w').write(s.replace(old, "", 1))
