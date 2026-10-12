#!/usr/bin/env python3
"""Build the per-arm witness sets for the smt_solver v2 paired evaluation, and check them with
an independent oracle (z3 on the REAL formula, not on either checker).

Inputs: the 69 scoped expected-sat hidden files (extracted from the judge image's zip) and the
witnesses dumped by ../witness_roundtrip.py (DUMP_DIR): A = checker-model witness (textual keys,
exists for the 42 single-context files), B = z3 true model keyed by textual key (first
occurrence), C = z3 true model keyed by let-expanded ground term (what smtlib_spec.md describes).

Derived here: Cw = C with one UF ground-key value changed. The key is the first one (sorted by
length, then text) for which the oracle proves the changed witness is NOT a model, i.e.
F AND (every witness entry) is unsat with distinct labels standing for distinct elements.
The choice never consults the checker under test.

Also reports the oracle verdict for every C witness (expected: sat, a genuine model).

Usage (z3 venv python):
  make_witness_sets.py HB_DIR WIT_DIR FILES69 OUT_SUB_ROOT ORACLE_JSONL
Writes OUT_SUB_ROOT/<arm>/src/w/<normhash>.json for arms ground, textual, textual_true, ground_wrong.
"""
import hashlib
import json
import os
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import scan_corpus as sc_mod  # noqa: E402
import z3  # noqa: E402

sys.setrecursionlimit(10_000_000)


def norm_hash(text):
    keep = [l for l in text.splitlines()
            if l.strip() and "__sebench_" not in l and "se-bench perturbation" not in l]
    return hashlib.sha256("\n".join(keep).encode("utf-8", "surrogateescape")).hexdigest()


class Oracle:
    def __init__(self, path):
        text = open(path, encoding="utf-8", errors="ignore").read()
        forms, _ = sc_mod.parse(sc_mod.tokenize(text))
        self.sc = sc_mod.Scan(forms)
        self.asserts, _, _, self.funs = sc_mod.build_z3(self.sc, "true")
        self.logic = self.sc.logic

    def sort_of(self, name):
        return self.sc.decls[name][1]

    def value(self, raw, sort, labels):
        zs = self.funs_sort(sort)
        if sort == "Bool":
            return z3.BoolVal(raw == "true")
        if sort in ("Int", "Real") and self.logic != "QF_UF":
            t = sc_mod.parse(sc_mod.tokenize(raw))[0][0]
            return self.num_term(t, sort)
        lab = labels.setdefault(sort, {})
        if raw not in lab:
            lab[raw] = z3.Const("lbl_%d_%s" % (len(lab), sort), zs)
        return lab[raw]

    def num_term(self, t, sort):
        if isinstance(t, str):
            return z3.RealVal(t) if sort == "Real" else z3.IntVal(t)
        if t[0] == "-" and len(t) == 2:
            return -self.num_term(t[1], sort)
        if t[0] == "/":
            return self.num_term(t[1], "Real") / self.num_term(t[2], "Real")
        raise ValueError("bad numeral")

    def funs_sort(self, sort):
        return {"Bool": z3.BoolSort(), "Int": z3.IntSort(), "Real": z3.RealSort()}.get(sort) or z3.DeclareSort(sort)

    def ground(self, t):
        if isinstance(t, str):
            if t in self.funs:
                return self.funs[t]
            if t in self.sc.defines and not self.sc.defines[t][0]:
                return self.ground(self.sc.defines[t][2])
            return z3.RealVal(t) if self.logic in ("QF_LRA", "QF_UFLRA") else z3.IntVal(t)
        op, xs = t[0], [self.ground(a) for a in t[1:]]
        if op in self.funs:
            return self.funs[op](*xs)
        if op == "+": return z3.Sum(*xs)
        if op == "-": return -xs[0] if len(xs) == 1 else xs[0] - z3.Sum(*xs[1:])
        if op == "*":
            p = xs[0]
            for x in xs[1:]:
                p = p * x
            return p
        if op == "/": return xs[0] / xs[1]
        raise ValueError("unsupported op in ground key " + op)

    def is_model(self, values, timeout_ms=120000):
        labels = {}
        cons = []
        for k, raw in values.items():
            if k.startswith("__sebench_"):
                continue
            if not k.startswith("("):
                if k in self.funs:
                    cons.append(self.funs[k] == self.value(raw, self.sort_of(k), labels))
                continue
            t = sc_mod.parse(sc_mod.tokenize(k))[0][0]
            cons.append(self.ground(t) == self.value(raw, self.sort_of(t[0]), labels))
        for lab in labels.values():
            if len(lab) > 1:
                cons.append(z3.Distinct(*lab.values()))
        s = z3.Solver(); s.set("timeout", timeout_ms)
        s.add(*self.asserts); s.add(*cons)
        return str(s.check())


def corrupt(values, key, oracle):
    raw = values[key]
    t = sc_mod.parse(sc_mod.tokenize(key))[0][0]
    sort = oracle.sort_of(t[0])
    w = dict(values)
    if sort == "Bool":
        w[key] = "false" if raw == "true" else "true"
    elif sort in ("Int", "Real") and oracle.logic != "QF_UF":
        w[key] = "1" if raw in ("0", "0.0") else "0"
    else:
        others = sorted({v for k, v in values.items() if v != raw and v.startswith("@")
                         and (k.startswith("(") and oracle.sort_of(sc_mod.parse(sc_mod.tokenize(k))[0][0][0]) == sort
                              or (not k.startswith("(") and k in oracle.funs and oracle.sort_of(k) == sort))})
        w[key] = others[0] if others else "@ebv_fresh"
    return w


def main():
    hb, wit, files69, out, oracle_out = sys.argv[1:6]
    files = [l.strip() for l in open(files69) if l.strip()]
    dumps = {}
    for name in os.listdir(wit):
        for tag in "ABC":
            if name.endswith(f".{tag}.json"):
                dumps[(name[: -len(f".{tag}.json")], tag)] = os.path.join(wit, name)
    arms = {"ground": "C", "textual": "A", "textual_true": "B", "ground_wrong": "Cw"}
    for arm in arms:
        os.makedirs(os.path.join(out, arm, "src", "w"), exist_ok=True)
    rows = []
    for f in files:
        path = os.path.join(hb, f)
        stem = path.replace("/", "_")[-40:]
        h = norm_hash(open(path, encoding="utf-8", errors="ignore").read())
        row = {"file": f, "normhash": h}
        oracle = Oracle(path)
        for arm, tag in arms.items():
            if tag == "Cw":
                continue
            p = dumps.get((stem, tag))
            if p:
                vals = json.load(open(p))["values"]
                json.dump({"file": f, "values": vals}, open(os.path.join(out, arm, "src", "w", h + ".json"), "w"))
                row[tag] = "present"
        C = json.load(open(dumps[(stem, "C")]))["values"]
        row["oracle_C"] = oracle.is_model(C)
        ufkeys = sorted((k for k in C if k.startswith("(")), key=lambda k: (len(k), k))
        for k in ufkeys:
            w = corrupt(C, k, oracle)
            r = oracle.is_model(w)
            if r == "unsat":
                row["Cw_key"], row["Cw_old"], row["Cw_new"], row["oracle_Cw"] = k, C[k], w[k], r
                json.dump({"file": f, "values": w}, open(os.path.join(out, "ground_wrong", "src", "w", h + ".json"), "w"))
                break
        print(json.dumps(row), flush=True)
        rows.append(row)
    with open(oracle_out, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


if __name__ == "__main__":
    threading.stack_size(1 << 29)
    t = threading.Thread(target=main); t.start(); t.join()
