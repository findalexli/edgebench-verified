# Runs the UNMODIFIED /tmp/eval_wesnoth.py as __main__, with a shim on subprocess.run that appends
# per-game wall time and marker lines to /out/<tag>_games.jsonl (flushed, so partial data survives a timeout).
import json, os, re, runpy, subprocess, sys, time
orig = subprocess.run
tag = os.environ.get("TAG", "x")
log = open(f"/out/{tag}_games.jsonl", "a", buffering=1)
def rec(cmd, **kw):
    t = time.monotonic(); rc = None; out = ""
    try:
        r = orig(cmd, **kw); rc = r.returncode; out = r.stdout + "\n" + r.stderr; return r
    except subprocess.TimeoutExpired:
        rc = "timeout"; raise
    finally:
        m = cmd[cmd.index("--scenario") + 1] if "--scenario" in cmd else "?"
        s = cmd[cmd.index("--rng-seed") + 1] if "--rng-seed" in cmd else "?"
        w = re.search(r"WINNER:\s*(\d+)", out); g = re.search(r"GAME_END_TURN:\s*(\d+)", out)
        log.write(json.dumps({"map": m, "seed": s, "elapsed_s": round(time.monotonic() - t, 2), "rc": rc,
                              "winner": w.group(1) if w else None, "end_turn": g.group(1) if g else None,
                              "unknown_ca": len(re.findall(r"UNKNOWN candidate_action", out))}) + "\n")
subprocess.run = rec
runpy.run_path("/tmp/eval_wesnoth.py", run_name="__main__")
