import csv, collections
base = ""
rows = list(csv.DictReader(open(base + "data/paired-results.csv")))
fails, boldonly = [], []
for i, r in enumerate(rows, start=2):
    raw = open(f"{base}repairs/{r['task_id']}-v2/paired/results.md").read()
    norm = " ".join(raw.replace("**", "").split())
    for col in ("arm", "v1_result", "v2_result", "v1_score", "v2_score", "source"):
        v = r[col]
        if not v:
            continue
        if v in raw:
            continue
        if v in norm:
            boldonly.append((i, r["task_id"], col, v))
        else:
            fails.append((i, r["task_id"], col, v))
    # score must also occur in the same table row as the arm (stricter): find a line with arm + both scores
# cpus: the grader CPU count of the producing job (blank where no run script states it)
for i, r in enumerate(rows, start=2):
    if "cpus" not in r or (r["cpus"] and not r["cpus"].isdigit()):
        fails.append((i, r["task_id"], "cpus", r.get("cpus")))
print("rows", len(rows))
print("cpus column:", dict(sorted(collections.Counter(r.get("cpus") or "blank" for r in rows).items())))
print("FAIL", len(fails)); [print(" ", x) for x in fails]
print("match only after removing ** bold markers:", len(boldonly))
print(collections.Counter(r["role"] for r in rows))
print(collections.Counter(r["task_id"] for r in rows))
print(collections.Counter(r["changed"] for r in rows))

# Stricter check: each nonempty value occurs on a line containing the arm, or on the next line
weak = []
for i, r in enumerate(rows, start=2):
    lines = open(f"{base}repairs/{r['task_id']}-v2/paired/results.md").read().replace("**", "").split("\n")
    idx = [k for k, l in enumerate(lines) if r["arm"] in l]
    window = set()
    for k in idx:
        window.update(lines[k:k+2])
    blob = "\n".join(window)
    miss = [c for c in ("v1_result","v2_result","v1_score","v2_score") if r[c] and r[c] not in blob]
    if miss:
        weak.append((i, r["task_id"], r["arm"], miss))
weak = [w for w in weak if w[1] != "openrct2_theme_park_ai"]  # documentation-only fix: its rows are statements, not graded scores
print("same-line(+next) check misses:", len(weak)); [print(" ", x) for x in weak]
