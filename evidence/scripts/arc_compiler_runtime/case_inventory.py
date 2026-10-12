"""Static inventory of ARC hidden suites: per-file case counts vs score_hidden.sh TEST_SPECS,
literal-expectation check, and near-duplicate template count (digits normalized).
Usage: python3 -I case_inventory.py <evaluator-hidden dir>"""
import re, sys, pathlib, hashlib
root = pathlib.Path(sys.argv[1])
sh = (root / "score_hidden.sh").read_text()
specs = re.findall(r'"((?:strengthened|extra)/[\w-]+):(\d+):(\d+):(\w+):([\w-]+)"', sh)
tot = wtot = 0; alltemps = set(); allcases = 0
for name, n, w, tier, mod in specs:
    f = root / "tests" / f"{name}.test.ts"; t = f.read_text()
    ids = re.findall(r"""['"]case_id['"]\s*:\s*['"]([^'"]+)['"]""", t)
    tests = re.findall(r'^\s*test\(\s*"([^"]+)"', t, re.M)
    srcs = re.findall(r"""['"]src['"]\s*:\s*(".*?(?<!\\)"|'.*?(?<!\\)')""", t)
    temps = {re.sub(r"\d+", "N", s) for s in srcs}
    units = len(ids) if ids else len(tests)
    alltemps |= {(mod, x) for x in temps}; allcases += units
    tot += int(n); wtot += int(n) * int(w)
    print(f"{name:45s} spec={n:>3} units={units:>3} dup_ids={len(ids)-len(set(ids))} distinct_src_templates={len(temps) if srcs else '-'} sha={hashlib.sha256(t.encode()).hexdigest()[:12]}")
print("spec raw total", tot, "weighted", wtot, "units found", allcases, "distinct templates (data-driven files)", len(alltemps))
