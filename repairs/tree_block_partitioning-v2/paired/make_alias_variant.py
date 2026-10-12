"""Derive T2_alias.cpp from the official T2 reference (std.cpp) by one local change in
MergeBlock: when the two factors are bitwise-equal values, compute the product as an
in-place self-product (v *= v) instead of v *= copy. Under the statement's value
contract ("x*=y sets x to x*y", no distinct-object precondition) this is an
equivalent computation, so a correct library must give identical answers.
Usage: python3 -I make_alias_variant.py <std.cpp> <out T2.cpp>"""
import sys, hashlib
raw = open(sys.argv[1], 'rb').read()
assert hashlib.sha256(raw).hexdigest() == 'e5fc6e9ba50eb4019c4ca710720d04569b918909f6796f1fb9e2377bb74dc657'
s = raw.decode()
old = "\t\t\tTmp.info[tc] *= GetInfo (a, cxa, cya);\n\t\t\tTmp.info[tc] *= GetInfo (b, cxb, cyb);\n"
if old not in s:
    old = old.replace("\n", "\r\n")
assert s.count(old) == 1, 'context'
new = ("\t\t\t{ Data A = GetInfo (a, cxa, cya), Bv = GetInfo (b, cxb, cyb);\n"
       "\t\t\t  Tmp.info[tc] *= A;\n"
       "\t\t\t  if (A.a == Bv.a && A.b == Bv.b && A.c == Bv.c && A.d == Bv.d) { ++alias_calls; Tmp.info[tc] *= Tmp.info[tc]; }\n"
       "\t\t\t  else Tmp.info[tc] *= Bv; }\n")
s = s.replace(old, new, 1)
s = s.replace("int top;", "int top; static long alias_calls = 0; struct AliasReport { ~AliasReport(){ fprintf(stderr, \"alias_calls %ld\\n\", alias_calls); } } alias_report;", 1)
open(sys.argv[2], 'w').write(s)
