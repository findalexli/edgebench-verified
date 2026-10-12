"""Independent brute-force oracle for T3 operation cost.
gen  OUTDIR K : write K random small cases (tree n<=7) + legal outputs + oracle.json
check OUTDIR RESULTS : compare checker results with the oracle.
Oracle semantics (from the statement): |N(x,y)| = #{v in subtree(x): dist(x,v) < y};
op1 cost = |new| - |old|; ops 2,3 free. Moves are generated to satisfy the checker's own
legality predicate so that only the cost computation is under test."""
import sys, os, json, random

def tree(n, rng):
    par = [None, None] + [rng.randint(1, i - 1) for i in range(2, n + 1)]
    depth = {1: 0}
    for v in range(2, n + 1): depth[v] = depth[par[v]] + 1
    def anc(v, x):  # is x ancestor-or-self of v
        while v is not None:
            if v == x: return True
            v = par[v]
        return False
    return par, depth, anc

def nset(x, yrel, n, depth, anc):
    return frozenset(v for v in range(1, n + 1) if anc(v, x) and depth[v] - depth[x] < yrel)

def gen(out, K):
    rng = random.Random(12345); os.makedirs(out, exist_ok=True); oracle = {}
    for k in range(K):
        n = rng.randint(1, 7); par, depth, anc = tree(n, rng)
        def legal(cur, new):  # checker predicate: cur empty-by-y, or cur.x in subtree(new.x) and abs y <= abs y'
            (x, yr), (x2, yr2) = cur, new
            return yr == 0 or (anc(x, x2) and depth[x] + yr <= depth[x2] + yr2)
        stack = [(1, 0)]; ops = []; marks = []; true_cost = 0; last = None
        for _ in range(rng.randint(1, 25)):
            r = rng.random()
            if r < 0.5:
                cands = [(x2, y2) for x2 in range(1, n + 1) for y2 in range(0, n + 1) if legal(stack[-1], (x2, y2))]
                new = rng.choice(cands)
                true_cost += len(nset(*new, n, depth, anc)) - len(nset(*stack[-1], n, depth, anc))
                stack.append(new); ops.append(f"1 {new[0]} {new[1]}"); last = new
            elif r < 0.75 and len(stack) > 1:
                stack.pop(); ops.append("2")
            else:
                marks.append((len(ops), stack[-1])); ops.append(None)
        if not marks: marks.append((len(ops), stack[-1])); ops.append(None)
        m = len(marks); perm = list(range(1, m + 1)); rng.shuffle(perm)
        queries = [None] * m
        for (pos, st), idx in zip(marks, perm):
            ops[pos] = f"3 {idx}"; queries[idx - 1] = st
        if len(ops) > 5 * m: continue
        name = f"r{k:04d}"
        with open(f"{out}/{name}.in", "w") as f:
            f.write(f"{n} {m}\n" + " ".join(str(par[v]) for v in range(2, n + 1)) + "\n")
            f.write("".join(f"{x} {y}\n" for x, y in queries))
        with open(f"{out}/{name}.out", "w") as f: f.write(f"{len(ops)}\n" + "\n".join(ops) + "\n")
        open(f"{out}/{name}.ans", "w").close()
        last_size = len(nset(*last, n, depth, anc)) if last else 0
        oracle[name] = {"true_cost": true_cost, "last_target_size": last_size, "predicted_original_count": true_cost - last_size}
    json.dump(oracle, open(f"{out}/oracle.json", "w"), indent=0)
    print(len(oracle), "cases")

def check(out, results):
    oracle = json.load(open(f"{out}/oracle.json")); bad = 0; over_accepted = 0; rows = 0
    for line in open(results):
        name, true_c, acc_at_pred, acc_below_pred, acc_at_truem1 = line.split()
        o = oracle[name]; rows += 1
        ok = int(true_c) == o["true_cost"] and acc_at_pred == "0" and acc_below_pred == "1"
        if not ok: bad += 1; print("MISMATCH", name, line.strip(), o)
        if o["last_target_size"] > 0 and acc_at_truem1 == "0": over_accepted += 1
    print(f"cases={rows} mismatches={bad}; cases where original accepts with W=true_cost-1 (over limit): {over_accepted}")

if __name__ == "__main__":
    {"gen": lambda: gen(sys.argv[2], int(sys.argv[3])), "check": lambda: check(sys.argv[2], sys.argv[3])}[sys.argv[1]]()
