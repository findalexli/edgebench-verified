#!/usr/bin/env python3
"""Prevalence in the archived Opus git_rewrite_in_zig runs: leftover objects, stray ELF, `Child` lines naming git, and git argv on nearby lines."""
import glob, hashlib, json, re, tarfile, collections
T = "git_rewrite_in_zig"; seen = {}
import sys, os
pats = {"opus": f"evidence/runs/claude-opus-{T}*/result/out/sforge-logs/runs/*/{T}/submissions/*/submission.tar.gz", "other (.internal e2e)": f".internal/e2e-artifacts/*{T}*/**/submission.tar.gz"}
pat = pats[sys.argv[1]] if len(sys.argv) > 1 else pats["opus"]
for a in sorted(glob.glob(pat, recursive=True)):
    if not os.path.exists(a.replace("submission.tar.gz", "report.json")): continue
    sha = hashlib.sha256(open(a, "rb").read()).hexdigest()
    sc = json.load(open(a.replace("submission.tar.gz", "report.json"))).get("score_0_100")
    if sha in seen:
        seen[sha]["n"] += 1; seen[sha]["score"] = max(seen[sha]["score"] or 0, sc or 0); continue
    r = dict(sub=a.split("/")[-2], run=a.split("/")[2], n=1, obj=[], elf=[], oneline=[], nearby=[], testgit=[], score=json.load(open(a.replace("submission.tar.gz", "report.json"))).get("score_0_100"))
    with tarfile.open(a) as t:
        for m in t:
            if not m.isfile() or re.search(r"(zig-cache|zig-out)/", m.name): continue
            if re.search(r"\.(o|a|so|dylib)$|\.so\.", m.name): r["obj"].append(m.name)
            f = t.extractfile(m); head = f.read(4)
            if head == b"\x7fELF": r["elf"].append(m.name)
            if m.name.endswith(".zig") and "/src/" in "/" + m.name:
                f.seek(0); L = f.read().decode("utf8", "replace").splitlines()
                for i, l in enumerate(L):
                    if re.search(r"std\.process\.Child|std\.posix\.execve|std\.os\.execve", l):
                        if re.search(r'"git"|"/usr/bin/git"', l, re.I): r["oneline"].append((m.name, i + 1))
                        elif any(re.search(r'"git"|"/usr/bin/git"', x, re.I) for x in L[max(0, i - 3):i + 6]): r["nearby"].append((m.name, i + 1))
                    if re.search(r'^\s*test\s+"', l) and any(re.search(r'"git"', x) for x in L[i:i + 15]): r["testgit"].append((m.name, i + 1))
    seen[sha] = r
rows = list(seen.values())
print("reports", sum(r["n"] for r in rows), "unique", len(rows))
for k in ["obj", "elf", "oneline", "nearby", "testgit"]:
    hit = [(r["sub"], r[k][:2]) for r in rows if r[k]]
    print(k, "files with a hit:", len(hit), hit[:4])
print("best real", max(r["score"] or 0 for r in rows))
