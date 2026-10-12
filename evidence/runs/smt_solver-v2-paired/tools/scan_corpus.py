#!/usr/bin/env python3
"""Corpus scan for the SMT witness-key scoping question.

For each hidden benchmark this reports
  * operator heads that the original WitnessChecker.eval does not implement
    (any sat witness would then be rejected),
  * uninterpreted-function (UF) applications whose arguments mention a
    let-bound variable or a define-fun parameter ("scoped" applications: the
    checker looks them up by their *textual* key, e.g. "(f ?v_3)", not by a
    ground term),
  * textual keys that occur under more than one distinct binding context
    ("multi-context" keys: the checker forces all such occurrences to share one
    model value),
  * maximum parenthesis depth (the checker parses/evaluates recursively).

Optionally (--z3) it decides with z3 whether any witness accepted by the
checker exists for an expected-sat benchmark (exact encoding: every UF
occurrence is replaced by one constant per textual key, plus
f(args)=c_key for every occurrence, which also captures the checker's
congruence check).  F itself is also checked (sanity: should be sat).

Usage: scan_corpus.py [--z3 --z3-timeout-ms N] FILE.smt2 ...   (JSON lines on stdout)
"""
import json
import sys
import threading
import time

sys.setrecursionlimit(10_000_000)

SUPPORTED = {"!", "let", "not", "and", "or", "=>", "ite", "=", "distinct",
             "+", "-", "*", "/", "<", ">", "<=", ">="}


def tokenize(text):
    # identical token rules to evaluate.py tokenize_smt2
    tokens = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
            continue
        if ch == ";":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if ch in "()":
            tokens.append(ch)
            i += 1
            continue
        if ch == "|":
            j = text.index("|", i + 1)
            tokens.append(text[i:j + 1])
            i = j + 1
            continue
        j = i
        while j < n and (not text[j].isspace()) and text[j] not in "();":
            j += 1
        tokens.append(text[i:j])
        i = j
    return tokens


def parse(tokens):
    forms, stack, maxdepth = [], [], 0
    for tok in tokens:
        if tok == "(":
            stack.append([])
            maxdepth = max(maxdepth, len(stack))
        elif tok == ")":
            done = stack.pop()
            (stack[-1] if stack else forms).append(done)
        else:
            (stack[-1] if stack else forms).append(tok)
    return forms, maxdepth


def canon(term):
    if isinstance(term, list):
        return "(" + " ".join(canon(p) for p in term) + ")"
    return term


class Scan:
    def __init__(self, forms):
        self.decls, self.defines, self.asserts, self.logic = {}, {}, [], "QF_UF"
        self.sorts = set()
        for f in forms:
            if not isinstance(f, list) or not f:
                continue
            c = f[0]
            if c == "set-logic":
                self.logic = f[1]
            elif c == "declare-sort":
                self.sorts.add(f[1])
            elif c == "declare-const" and len(f) == 3:
                self.decls[f[1]] = ([], f[2])
            elif c == "declare-fun" and len(f) == 4:
                self.decls[f[1]] = (f[2] if isinstance(f[2], list) else [], f[3])
            elif c == "define-fun" and len(f) == 5:
                self.defines[f[1]] = (f[2] if isinstance(f[2], list) else [], f[3], f[4])
            elif c == "assert" and len(f) == 2:
                self.asserts.append(f[1])
        self.unsupported = {}
        self.uf_apps = 0
        self.scoped_apps = 0
        self.key_ctx = {}      # textual key -> set of context ids (only scoped keys)
        self.next_id = 0

    # env: symbol -> binding id (let instance or define call site)
    def walk(self, term, env):
        if isinstance(term, str):
            return
        if not term:
            return
        op = term[0]
        args = term[1:]
        if isinstance(op, list):
            self.unsupported["<compound head>"] = self.unsupported.get("<compound head>", 0) + 1
            return
        if op == "let":
            new = dict(env)
            for b in args[0]:
                self.walk(b[1], env)
                self.next_id += 1
                new[b[0]] = self.next_id
            self.walk(args[1], new)
            return
        if op == "!":
            self.walk(args[0], env)
            return
        if op in SUPPORTED:
            for a in args:
                self.walk(a, env)
            return
        if op in self.defines:
            params, _, body = self.defines[op]
            for a in args:
                self.walk(a, env)
            if params:
                self.next_id += 1
                new = dict(env)
                for p in params:
                    new[p[0]] = self.next_id
                self.walk(body, new)
            return
        if op in self.decls and self.decls[op][0]:
            self.uf_apps += 1
            for a in args:
                self.walk(a, env)
            free = set()
            stack = list(args)
            while stack:
                t = stack.pop()
                if isinstance(t, str):
                    if t in env:
                        free.add((t, env[t]))
                else:
                    stack.extend(t)
            if free:
                self.scoped_apps += 1
                key = canon(term)
                self.key_ctx.setdefault(key, set()).add(tuple(sorted(free)))
            return
        self.unsupported[op] = self.unsupported.get(op, 0) + 1
        for a in args:
            self.walk(a, env)

    def run(self):
        for a in self.asserts:
            self.walk(a, {})
        multi = [k for k, v in self.key_ctx.items() if len(v) > 1]
        return {
            "logic": self.logic,
            "n_asserts": len(self.asserts),
            "uf_decls": sum(1 for v in self.decls.values() if v[0]),
            "param_defines": sum(1 for v in self.defines.values() if v[0]),
            "uf_apps": self.uf_apps,
            "scoped_uf_apps": self.scoped_apps,
            "scoped_keys": len(self.key_ctx),
            "multi_context_keys": len(multi),
            "multi_context_examples": sorted(multi)[:3],
            "unsupported_ops": self.unsupported,
        }


def build_z3(sc, mode):
    """Return (assertions, side_constraints, keyconst, funs) for mode 'true' or 'checker'."""
    import z3
    sorts = {"Bool": z3.BoolSort(), "Int": z3.IntSort(), "Real": z3.RealSort()}
    for s in sc.sorts:
        sorts[s] = z3.DeclareSort(s)
    funs = {}
    for name, (args, ret) in sc.decls.items():
        funs[name] = z3.Function(name, *[sorts[a] for a in args], sorts[ret]) if args else z3.Const(name, sorts[ret])
    intlogic = sc.logic == "QF_LIA"

    def num(tok):
        if "." in tok:
            return z3.RealVal(tok)
        return z3.IntVal(tok) if intlogic or sc.logic == "QF_UF" else z3.RealVal(tok)

    def build(term, env, mode, side, keyconst):
        if isinstance(term, str):
            if term in env:
                return env[term]
            if term == "true":
                return z3.BoolVal(True)
            if term == "false":
                return z3.BoolVal(False)
            if term.lstrip("-").replace(".", "", 1).isdigit():
                return num(term)
            if term in funs:
                return funs[term]
            if term in sc.defines:
                return build(sc.defines[term][2], env, mode, side, keyconst)
            raise ValueError("unknown symbol " + term)
        op, args = term[0], term[1:]
        B = lambda t: build(t, env, mode, side, keyconst)
        if op == "let":
            new = dict(env)
            for b in args[0]:
                new[b[0]] = B(b[1])
            return build(args[1], new, mode, side, keyconst)
        if op == "!":
            return B(args[0])
        xs = [B(a) for a in args] if op != "ite" else None
        if op == "not": return z3.Not(xs[0])
        if op == "and": return z3.And(*xs) if xs else z3.BoolVal(True)
        if op == "or": return z3.Or(*xs) if xs else z3.BoolVal(False)
        if op == "=>": return z3.Implies(xs[0], xs[1])
        if op == "ite": return z3.If(B(args[0]), B(args[1]), B(args[2]))
        if op == "=": return z3.And(*[xs[0] == x for x in xs[1:]])
        if op == "distinct": return z3.Distinct(*xs)
        if op == "+": return z3.Sum(*xs)
        if op == "-": return -xs[0] if len(xs) == 1 else xs[0] - z3.Sum(*xs[1:])
        if op == "*":
            p = xs[0]
            for x in xs[1:]:
                p = p * x
            return p
        if op == "/": return xs[0] / xs[1]
        if op == "<": return xs[0] < xs[1]
        if op == ">": return xs[0] > xs[1]
        if op == "<=": return xs[0] <= xs[1]
        if op == ">=": return xs[0] >= xs[1]
        if op in sc.defines:
            params, _, body = sc.defines[op]
            new = dict(env)
            for p, x in zip(params, xs):
                new[p[0]] = x
            return build(body, new, mode, side, keyconst)
        f = funs[op]
        real = f(*xs)
        key = canon(term)
        if mode == "true":
            side.append((key, real))   # occurrence record only (not a constraint)
            return real
        c = keyconst.get(key)
        if c is None:
            c = z3.FreshConst(f.range(), "k")
            keyconst[key] = c
        side.append(real == c)
        return c

    side, keyconst = [], {}
    asserts = [build(a, {}, mode, side, keyconst) for a in sc.asserts]
    return asserts, side, keyconst, funs


def z3_check(sc, timeout_ms):
    import z3
    out = {}
    for mode in ("true", "checker"):
        t0 = time.time()
        asserts, side, _, _ = build_z3(sc, mode)
        s = z3.Solver()
        s.set("timeout", timeout_ms)
        s.add(*asserts)
        if mode == "checker":
            s.add(*side)
        out[mode] = str(s.check())
        out[mode + "_seconds"] = round(time.time() - t0, 2)
    return out


def main():
    argv = sys.argv[1:]
    use_z3 = "--z3" in argv
    tmo = 120000
    if "--z3-timeout-ms" in argv:
        tmo = int(argv[argv.index("--z3-timeout-ms") + 1])
    files = [a for a in argv if a.endswith(".smt2")]
    for path in files:
        rec = {"file": "/".join(path.split("/")[-2:])}
        try:
            text = open(path, encoding="utf-8", errors="ignore").read()
            forms, depth = parse(tokenize(text))
            sc = Scan(forms)
            rec.update(sc.run())
            rec["max_paren_depth"] = depth
            if use_z3 and (rec["multi_context_keys"] or rec["scoped_uf_apps"]):
                rec["z3"] = z3_check(sc, tmo)
        except Exception as exc:  # report, keep going
            rec["error"] = repr(exc)[:300]
        print(json.dumps(rec), flush=True)


if __name__ == "__main__":
    threading.stack_size(1 << 29)
    t = threading.Thread(target=main)
    t.start()
    t.join()
