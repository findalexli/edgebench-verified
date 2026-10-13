#!/usr/bin/env python3
"""Cross-check the z3 encoding against the ORIGINAL WitnessChecker (evaluate_original.py,
sha256 f4be8e8d...).  For each benchmark:

  A. checker-model witness: solve the checker-semantics encoding with z3; if sat, emit a
     JSON witness keyed exactly as the checker looks values up (symbols + textual UF keys)
     and run the original WitnessChecker on it.  Expect: accepted.
  B. true-model, textual keys: solve the real formula with z3, then key every UF
     occurrence by its textual key using the value of its FIRST occurrence.
  C. true-model, ground keys (what the spec text describes: "canonical ground terms"):
     key every UF application by the ground term obtained by substituting let/define
     bindings, i.e. f applied to the model values of its arguments rendered as terms.
     (Only the textual lookups matter to the checker, so this witness is rejected whenever
     a scoped key exists.)
Run with the z3 venv python:  witness_roundtrip.py FILE.smt2 ...
"""
import json
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import scan_corpus as sc_mod  # noqa: E402
import evaluate_original as ev  # noqa: E402
import z3  # noqa: E402

sys.setrecursionlimit(10_000_000)


def lit(v):
    if z3.is_true(v):
        return "true"
    if z3.is_false(v):
        return "false"
    if z3.is_int_value(v):
        return str(v.as_long())
    if z3.is_rational_value(v):
        n, d = v.numerator_as_long(), v.denominator_as_long()
        return str(n) if d == 1 else f"(/ {n} {d})"
    if z3.is_algebraic_value(v):
        raise ValueError("algebraic")
    return "@" + str(v).replace("!", "_")  # uninterpreted-sort element label


def check(path, witness, tag=None):
    import os
    dump = os.environ.get("DUMP_DIR")
    if dump and tag:
        os.makedirs(dump, exist_ok=True)
        stem = path.replace("/", "_")[-40:]
        with open(os.path.join(dump, f"{stem}.{tag}.json"), "w") as f:
            json.dump({"values": witness["values"]}, f)
    try:
        ev.validate_sat_witness(path, witness)
        return "accepted"
    except Exception as exc:
        return "rejected: " + str(exc)[:120]


def smt_text(e):
    """Render a z3 ground term in the checker's canonical SMT-LIB text (lets expanded)."""
    if z3.is_int_value(e) or z3.is_rational_value(e):
        return lit(e)
    if e.num_args() == 0:
        return e.decl().name()
    return "(" + " ".join([e.decl().name()] + [smt_text(c) for c in e.children()]) + ")"


def run(path):
    text = open(path, encoding="utf-8", errors="ignore").read()
    forms, _ = sc_mod.parse(sc_mod.tokenize(text))
    sc = sc_mod.Scan(forms)
    out = {"file": "/".join(path.split("/")[-2:])}
    zero_ary = {n: s for n, (a, s) in sc.decls.items() if not a}

    # A: checker-semantics model
    asserts, side, keyconst, funs = sc_mod.build_z3(sc, "checker")
    s = z3.Solver(); s.set("timeout", 300000); s.add(*asserts); s.add(*side)
    r = s.check(); out["checker_encoding"] = str(r)
    if r == z3.sat:
        m = s.model()
        vals = {n: lit(m.eval(funs[n], model_completion=True)) for n in zero_ary}
        for k, c in keyconst.items():
            vals[k] = lit(m.eval(c, model_completion=True))
        out["A_checker_model_witness"] = check(path, {"values": vals}, "A")

    # B/C: true model
    asserts, occ, _, funs = sc_mod.build_z3(sc, "true")
    s = z3.Solver(); s.set("timeout", 300000); s.add(*asserts)
    r = s.check(); out["true_formula"] = str(r)
    if r == z3.sat:
        m = s.model()
        base = {n: lit(m.eval(funs[n], model_completion=True)) for n in zero_ary}
        textual, ground = dict(base), dict(base)
        for key, real in occ:                 # evaluation order; first occurrence wins
            v = lit(m.eval(real, model_completion=True))
            textual.setdefault(key, v)
            ground.setdefault(smt_text(real), v)
        out["B_true_model_textual_keys"] = check(path, {"values": textual}, "B")
        out["C_true_model_ground_keys"] = check(path, {"values": ground}, "C")
    return out


def main():
    for p in sys.argv[1:]:
        try:
            print(json.dumps(run(p)), flush=True)
        except Exception as exc:
            print(json.dumps({"file": p, "error": repr(exc)[:300]}), flush=True)


if __name__ == "__main__":
    threading.stack_size(1 << 29)
    t = threading.Thread(target=main); t.start(); t.join()
