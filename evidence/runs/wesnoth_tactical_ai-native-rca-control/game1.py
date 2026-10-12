# Times original run_game() from /tmp/eval_wesnoth.py (unmodified evaluator module), recording raw engine output.
import json, os, subprocess, sys, time
sys.path.insert(0, "/tmp")
import eval_wesnoth as e
print("scan_for_hacks:", e.scan_for_hacks(), flush=True)
e.install_agent_ai()
print("installed to", e.USER_DATA_DIR, os.listdir(e.USER_DATA_DIR), flush=True)
orig = subprocess.run
cap = {}
def rec(cmd, **kw):
    cap.clear(); cap["cmd"] = cmd; t = time.monotonic()
    try:
        r = orig(cmd, **kw); cap["rc"] = r.returncode; cap["out"] = r.stdout + "\n" + r.stderr; return r
    except subprocess.TimeoutExpired as x:
        o = x.stdout or ""; o = o.decode(errors="replace") if isinstance(o, bytes) else o
        s = x.stderr or ""; s = s.decode(errors="replace") if isinstance(s, bytes) else s
        cap["rc"] = "timeout"; cap["out"] = o + "\n" + s; raise
    finally:
        cap["elapsed_s"] = round(time.monotonic() - t, 2)
e.subprocess.run = rec
tag = os.environ.get("TAG", "default")
for m in sys.argv[1:]:
    res = e.run_game(m, 0, 0)
    out = cap.get("out", "")
    with open(f"/out/game_{tag}_{m}.log", "w") as f: f.write(out)
    lines = [l for l in out.splitlines() if "WINNER" in l or "GAME_END_TURN" in l]
    print(json.dumps({"tag": tag, "map": m, "seed": 0, "run_game_return": res, "elapsed_s": cap.get("elapsed_s"),
                      "rc": cap.get("rc"), "marker_lines": lines[:10], "out_bytes": len(out)}), flush=True)
