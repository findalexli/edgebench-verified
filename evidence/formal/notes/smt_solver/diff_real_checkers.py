# Differential check: run the real original and fixed WitnessChecker (evaluate.py, read from the
# local copies; see sha256 in ../smt_solver.md) on the cases encoded in Ebv/SmtWitness.lean.
# Usage: python3 -I diff_real_checkers.py
import importlib.util, sys, tempfile, os, json
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
R = (__import__('os').environ.get('EBV_REPO') or str(__import__('pathlib').Path(__file__).resolve().parents[4])) + "/"
v1 = load("v1", R + ".internal/evidence/scripts/smt_solver/evaluate_original.py")
v2 = load("v2", R + ".internal/repairs/smt_solver-v2/files/evaluate.py")
HDR = "(set-logic QF_UF)\n(declare-sort U 0)\n(declare-fun a () U)\n(declare-fun b () U)\n(declare-fun c () U)\n(declare-fun f (U) U)\n"
cases = {
 "scope_conflict": (["(distinct a b)", "(let ((x a)) (= (f x) a))", "(let ((x b)) (= (f x) b))"], {"a":"@a","b":"@b","(f a)":"@a","(f b)":"@b"}),
 "scope_conflict_textkeys": (["(distinct a b)", "(let ((x a)) (= (f x) a))", "(let ((x b)) (= (f x) b))"], {"a":"@a","b":"@b","(f a)":"@a","(f b)":"@b","(f x)":"@a"}),
 "scope_conflict_wrong": (["(distinct a b)", "(let ((x a)) (= (f x) a))", "(let ((x b)) (= (f x) b))"], {"a":"@a","b":"@b","(f a)":"@a","(f b)":"@a"}),
 "single_let": (["(distinct a b)", "(let ((x a)) (= (f x) b))"], {"a":"@a","b":"@b","(f a)":"@b"}),
 "single_let_textkey": (["(distinct a b)", "(let ((x a)) (= (f x) b))"], {"a":"@a","b":"@b","(f x)":"@b"}),
 "single_let_wrong": (["(distinct a b)", "(let ((x a)) (= (f x) b))"], {"a":"@a","b":"@b","(f a)":"@a"}),
 "ground_control": (["(distinct a b)", "(= (f a) a)", "(= (f b) b)"], {"a":"@a","b":"@b","(f a)":"@a","(f b)":"@b"}),
 "ground_control_wrong": (["(distinct a b)", "(= (f a) a)", "(= (f b) b)"], {"a":"@a","b":"@b","(f a)":"@a","(f b)":"@a"}),
 "alias_conflict": (["(distinct a b)", "(= a c)", "(= (f a) a)", "(= (f c) b)"], {"a":"@a","b":"@b","c":"@a","(f a)":"@a","(f c)":"@b"}),
 "alias_conflict_let": (["(distinct a b)", "(= a c)", "(= (f a) a)", "(let ((x c)) (= (f x) b))"], {"a":"@a","b":"@b","c":"@a","(f a)":"@a","(f c)":"@b"}),
 "unused_conflict": (["(= a c)", "(= (f a) a)"], {"a":"@a","c":"@a","(f a)":"@a","(f c)":"@b"}),
 # new: let-binder shadows the declared constant a; textual keys, genuine model (a=c=@a, b=@b, f=id)
 "shadow_textual": (["(distinct a b)", "(let ((a b)) (= (f a) a))", "(= (f c) c)"], {"a":"@a","b":"@b","c":"@a","(f a)":"@b","(f c)":"@a"}),
 "shadow_ground": (["(distinct a b)", "(let ((a b)) (= (f a) a))", "(= (f c) c)"], {"a":"@a","b":"@b","c":"@a","(f a)":"@a","(f b)":"@b"}),
 # coverage: nested argument value reached only through (f a)
 "nested_keys_flat": (["(distinct a b)", "(= (f a) b)", "(let ((x (f a))) (= (f x) a))"], {"a":"@a","b":"@b","(f a)":"@b"}),
 "nested_keys_deep": (["(distinct a b)", "(= (f a) b)", "(let ((x (f a))) (= (f x) a))"], {"a":"@a","b":"@b","(f a)":"@b","(f (f a))":"@a"}),
}
d = tempfile.mkdtemp()
for name, (asserts, vals) in cases.items():
    p = os.path.join(d, name + ".smt2")
    open(p, "w").write(HDR + "".join(f"(assert {a})\n" for a in asserts) + "(check-sat)\n")
    out = []
    for m in (v1, v2):
        try:
            m.WitnessChecker(p, {"values": vals}).validate(); out.append("accept")
        except m.ModelValidationError as e:
            out.append("reject: " + str(e)[:60])
    print(f"{name:26s} | v1 {out[0]:50s} | v2 {out[1]}")
