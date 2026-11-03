#!/usr/bin/env python3
"""Create the community9 job directories: run.sh from the template, witness archives with plain member names, comment-only or fix patches."""
import difflib, hashlib, io, os, pathlib, shutil, sys, tarfile
ROOT = pathlib.Path("/home/alex/edgebench-verified")
UP = pathlib.Path("/tmp/claude-1000/-home-alex-edgebench-verified/b902f0c3-094f-4474-9624-5f20b9cfe806/scratchpad/up-all")
HERE = ROOT / "evidence/scripts/second_review"
TPL = (HERE / "c9games_run_template.sh").read_text()
OPUS = ROOT / "evidence/runs/claude-opus-openrct2_theme_park_ai-v1/result/out/sforge-logs/runs/opus-v1/openrct2_theme_park_ai/submissions"

def tar(path, members):
    with tarfile.open(path, "w:gz") as t:
        for name, data in members.items():
            ti = tarfile.TarInfo(name); ti.size = len(data); ti.mode = 0o644; ti.mtime = 1700000000
            t.addfile(ti, io.BytesIO(data))

def patch(task, rel, new_text):
    old_path = UP / "edgebench/tasks" / task / rel
    old = old_path.read_text()
    p = f"edgebench/tasks/{task}/{rel}"
    return "".join(difflib.unified_diff(old.splitlines(True), new_text.splitlines(True), f"a/{p}", f"b/{p}"))

def comment_patch(task):
    old = (UP / "edgebench/tasks" / task / "NOTES.md").read_text()
    return patch(task, "NOTES.md", old + "\n<!-- no fix tested in this job -->\n")

def job(name, task, sides, limit, arms, pr, subs, extra=None):
    d = ROOT / "evidence/runs" / name
    assert not (d / "result").exists(), name
    (d / "subs").mkdir(parents=True, exist_ok=True)
    (d / "run.sh").write_text(TPL.replace("__TASK__", task))
    (d / "arms.sh").write_text(arms)
    (d / "pr.patch").write_text(pr)
    (d / "sides").write_text(sides + "\n")
    (d / "limit").write_text(str(limit) + "\n")
    for k, v in subs.items():
        if isinstance(v, pathlib.Path):
            shutil.copyfile(v, d / "subs" / k)
        else:
            tar(d / "subs" / k, v)
    for k, v in (extra or {}).items():
        (d / k).write_text(v)
    print(name, sorted(os.listdir(d / "subs")))

def task_file(t, rel):
    return (UP / "edgebench/tasks" / t / rel).read_bytes()

# --- nethack
NH = "nethack_dungeon_agent"
nh_old = (UP / "edgebench/tasks" / NH / "judge/eval_nethack.py").read_text()
nh_new = nh_old.replace("""    try:
        env.seed(seed)
    except Exception:
        pass
    reset_result = env.reset()""", """    seed_value = EVAL_SEED_BASE + int(seed)
    env.unwrapped.nethack._pynethack.set_initial_seeds(seed_value, seed_value, False, None)
    reset_result = env.reset()""")
assert nh_new != nh_old
nh_pr = patch(NH, "judge/eval_nethack.py", nh_new)
nh_subs = {"bot.tar.gz": {"agent.py": (HERE / "c9games_nethack_bot.py").read_bytes()},
           "starter.tar.gz": {"agent.py": task_file(NH, "environment/workspace/agent.py")}}

# --- dcss
DC = "dcss_dungeon_ai"
dc_old = (UP / "edgebench/tasks" / DC / "judge/eval_dcss.py").read_text()
a = dc_old.index("def _dismiss_loop(session, stop):")
b = dc_old.index("def _alive(session):")
dc_new = dc_old[:a] + "def _dismiss_loop(session, stop):\n    stop.wait()\n\n" + dc_old[b:]
dc_pr = patch(DC, "judge/eval_dcss.py", dc_new)
rc = task_file(DC, "environment/workspace/my_bot.rc")
inc = task_file(DC, "environment/workspace/my_bot_include.rc")
dc_subs = {"starter.tar.gz": {"my_bot.rc": rc, "my_bot_include.rc": inc},
           "diver.tar.gz": {"my_bot.rc": rc, "my_bot_include.rc": (HERE / "c9games_dcss_diver_include.rc").read_bytes()}}

# --- wesnoth
WS = "wesnoth_tactical_ai"
ws_subs = {"rca.tar.gz": {"my_custom_ai.cfg": (ROOT / "evidence/runs/wesnoth_tactical_ai-native-rca-control/result/out/control_my_custom_ai.cfg").read_bytes()},
           "starter.tar.gz": {"my_custom_ai.cfg": task_file(WS, "environment/workspace/my_custom_ai.cfg")}}

# --- openrct2: real submissions, unchanged archives
RC = "openrct2_theme_park_ai"
rc_subs = {f"{n}.tar.gz": OPUS / n / "submission.tar.gz" for n in ["agent-1", "agent-10", "auto-6", "auto-30", "auto-45", "agent-11"]}
LONG = (HERE / "c9games_openrct2_long_one.py").read_text()

ARMS = {k: (HERE / f"c9games_arms_{k}.sh").read_text() for k in sys.argv[2:]}
which = sys.argv[1]
if which == "smoke":
    job("community9-nethack_dungeon_agent-smoke", NH, "base new", 800, ARMS["nh_smoke"], nh_pr, nh_subs)
    job("community9-dcss_dungeon_ai-smoke", DC, "base", 800, ARMS["dc_smoke"], comment_patch(DC), dc_subs)
    job("community9-openrct2_theme_park_ai-smoke", RC, "base", 900, ARMS["rc_smoke"], comment_patch(RC), rc_subs, {"long_one.py": LONG})
if which == "ws":
    job("community9-wesnoth_tactical_ai", WS, "base", 3200, ARMS["ws_full"], comment_patch(WS), ws_subs)
if which == "nh":
    job("community9-nethack_dungeon_agent", NH, "base new", 2400, ARMS["nh_full"], nh_pr, nh_subs)
if which == "rc_reps":
    job("community9-openrct2_theme_park_ai-reps", RC, "base", 3150, ARMS["rc_reps"], comment_patch(RC), rc_subs)
if which == "rc_long":
    OPUS2 = ROOT / "evidence/runs/claude-opus-openrct2_theme_park_ai-v2/result/out/sforge-logs/runs/opus-v2/openrct2_theme_park_ai/submissions"
    job("community9-openrct2_theme_park_ai-long", RC, "base", 2500, ARMS["rc_long"], comment_patch(RC),
        {"agent-1.tar.gz": OPUS / "agent-1/submission.tar.gz", "v2-auto-26.tar.gz": OPUS2 / "auto-26/submission.tar.gz"}, {"long_one.py": LONG})
if which == "dc_smoke2":
    job("community9-dcss_dungeon_ai-smoke3", DC, "base new", 800, ARMS["dc_smoke2"], dc_pr, dc_subs)
rc_stop = rc + b"autofight_stop = 0\n"
dc_subs["fighter.tar.gz"] = {"my_bot.rc": rc_stop, "my_bot_include.rc": (HERE / "c9games_dcss_diver_include.rc").read_bytes()}
dc_subs["diver2.tar.gz"] = {"my_bot.rc": rc_stop, "my_bot_include.rc": (HERE / "c9games_dcss_diver2_include.rc").read_bytes()}
if which == "dc_smoke4":
    job("community9-dcss_dungeon_ai-smoke4", DC, "base", 800, ARMS["dc_smoke4"], comment_patch(DC), {k: dc_subs[k] for k in ["fighter.tar.gz", "diver2.tar.gz"]})
if which == "dc_full":
    arms = ARMS["dc_old"]
    subs = {k: dc_subs[k] for k in ["fighter.tar.gz", "starter.tar.gz"]}
    job("community9-dcss_dungeon_ai-old", DC, "base", 3150, arms.replace("__SIDE__", "old"), comment_patch(DC), subs)
    job("community9-dcss_dungeon_ai-nokeys", DC, "base new", 3150, arms.replace("__SIDE__", "new"), dc_pr, subs)
