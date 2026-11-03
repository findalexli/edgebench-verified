#!/usr/bin/env python3
"""community9 git_rewrite_in_zig: scaffold and real auto-39, control / leftover main.o / test-only git call, old vs fixed test.sh."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from c9_table_lib import load, show, arms, mean
rows = load(["community9-git_rewrite_in_zig-smoke", "community9-git_rewrite_in_zig-old", "community9-git_rewrite_in_zig-new"])
show(rows)
for arm in sorted(rows):
    print(arm, [(r["result"].get("metrics") or {}).get("reason") for r in rows[arm]], [(r["result"].get("metrics") or {}).get("total_passed") for r in rows[arm]])
R = json.load(open(".internal/upstream-sweep/round3/git_rewrite_in_zig.json"))["claims"]
def claim(idx, sfx, verdict, what, note):
    c = R[idx]["claim"]
    a = arms(rows, [("old-scaf", "scaffold, current judge"), (f"old-scaf-{sfx}", f"scaffold + {what}, current judge"), (f"new-scaf-{sfx}", f"scaffold + {what}, fixed test.sh"),
                    ("old-real", "real auto-39, current judge"), (f"old-real-{sfx}", f"real auto-39 + {what}, current judge"), (f"new-real-{sfx}", f"real auto-39 + {what}, fixed test.sh"), ("new-real", "real auto-39, fixed test.sh"), ("new-scaf", "scaffold, fixed test.sh")])
    eff = mean(rows, f"old-real-{sfx}") - mean(rows, "old-real")
    return dict(claim=c, verdict=verdict, witness=f"real modified at the defect: auto-39 (sha 5b8e7a1c) plus only {what}; scaffold control",
                arms=a, effect_points=round(eff, 4),
                fix_tested=f"old vs fixed test.sh on the same archives: real+{what} {mean(rows, f'old-real-{sfx}'):.4f} -> {mean(rows, f'new-real-{sfx}'):.4f}; scaffold+{what} {mean(rows, f'old-scaf-{sfx}'):.4f} -> {mean(rows, f'new-scaf-{sfx}'):.4f}",
                correct_work_keeps_score=f"yes: real auto-39 {mean(rows, 'old-real'):.4f} -> {mean(rows, 'new-real'):.4f}, scaffold {mean(rows, 'old-scaf'):.4f} -> {mean(rows, 'new-scaf'):.4f}",
                job="evidence/runs/community9-git_rewrite_in_zig-old and -new", table_script="evidence/scripts/second_review/c9_git_rewrite_in_zig_table.py", note=note)
prev = "best real run 36.88 has no trigger, and 0 of 46 distinct real archives (26 Opus, 20 other model) contain a leftover object, a stray ELF or a git call on a Child line"
out = {"task": "git_rewrite_in_zig", "claims": [
    claim(0, "obj", "CONFIRMED_SMALL", "root main.o from `zig build-obj src/main.zig -lc -lz`", f"The whole score goes to 0 when the trigger is present, but {prev}, so this is real but unobserved; weakest point: no real solver has hit it."),
    claim(1, "test", "CONFIRMED_SMALL", "unimported src/oracle_test.zig with a one-line Child.init of git (zig test passes 1/1)", f"The whole score goes to 0 when the trigger is present, but {prev}, and the same call written across two lines escapes the check; weakest point: no real solver has hit it."),
]}
json.dump(out, open(".internal/upstream-sweep/container/git_rewrite_in_zig.json", "w"), indent=1)
