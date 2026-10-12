# Scan an extracted hidden corpus for let-binders or define-fun parameters named like a declared
# symbol (the shadowing pattern of SmtWitness.shadow_textual_regression).
# Usage: python3 -I shadow_scan.py <dir with QF_*/ subfolders>
import importlib.util, sys, glob, os
spec = importlib.util.spec_from_file_location("v1", "/home/alex/edgebench-verified/.internal/evidence/scripts/smt_solver/evaluate_original.py")
v1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v1)
root = sys.argv[1]; hits = 0; n = 0
def walk(t, decl, acc):
    stack = [t]
    while stack:
        t = stack.pop()
        if isinstance(t, list) and t:
            if t[0] == "let" and len(t) == 3 and isinstance(t[1], list):
                for bnd in t[1]:
                    if isinstance(bnd, list) and bnd and bnd[0] in decl: acc.add(bnd[0])
            stack.extend(t)
for p in sorted(glob.glob(os.path.join(root, "*", "*.smt2"))):
    n += 1
    forms = v1.parse_smt2(open(p, encoding="utf-8", errors="ignore").read())
    decl = set(); acc = set()
    for f in forms:
        if isinstance(f, list) and f and f[0] in ("declare-fun", "declare-const", "define-fun") and len(f) > 1: decl.add(f[1])
    for f in forms:
        if isinstance(f, list) and f and f[0] == "define-fun" and len(f) == 5 and isinstance(f[2], list):
            for prm in f[2]:
                if isinstance(prm, list) and prm and prm[0] in decl: acc.add("param:" + prm[0])
        if isinstance(f, list) and f and f[0] in ("assert", "define-fun"): walk(f, decl, acc)
    if acc: hits += 1; print(p, sorted(acc)[:5])
print("files", n, "with let/param names shadowing a declared symbol:", hits)
