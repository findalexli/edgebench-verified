"""Good-faith scoring arithmetic for the ten game tasks (stdlib only; < 1 s).

Usage: python3 check_arith.py <treant_cases_dir>
Uses the repo's rescale (sforge/harness/score_rescale.py) and the ORIGINAL Bipedal
scoring functions (pure functions, imported from the hash-pinned triage copy).
Every constant below is quoted from an original evaluator; file:line in the review.
"""
import glob, importlib.util, json, math, os, sys
from fractions import Fraction as F

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from sforge.harness.score_rescale import parse_rescale_spec, rescale_score  # noqa: E402

def spec(t):
    return parse_rescale_spec(json.load(open(f"{ROOT}/tasks/{t}.json"))["judge"]["rescale"])

out = {}

# Treant: tester max_turns = 2*N*N (tester:63,140) -> per-case cap; sum over shipped cases.
cases = sorted(glob.glob(os.path.join(sys.argv[1], "*.txt")))
cap = sum(2 * int(open(c).readline().split()[0]) ** 2 for c in cases)
out["treant"] = {"cases": len(cases), "raw_cap_sum_2N2": cap,
                 "rescaled_cap": rescale_score(spec("treant_forest"), cap),
                 "shipped_baseline_raw_observed": 3418,
                 "shipped_baseline_rescaled": rescale_score(spec("treant_forest"), 3418),
                 "rank1_over_cap": 330195 / cap,
                 "worst_case_eval_s_8_workers_120s": math.ceil(50 / 8) * 120,
                 "worst_case_eval_s_at_README_60s": math.ceil(50 / 8) * 60, "eval_timeout": 870}

# Apple: one-step-lookahead greedy (triage/apple/greedy_lookahead.py) observed sum 237,518,875.
a = spec("apple_incremental_game")
out["apple"] = {"greedy_sum": 237518875, "greedy_rescaled": rescale_score(a, 237518875),
                "shipped_do_nothing_raw": 0, "shipped_rescaled": rescale_score(a, 0),
                "worst_case_eval_s": math.ceil(50 / 8) * 30, "eval_timeout": 600}

# DCSS: log1p_max; per-game wall-clock schedule from eval_dcss.py.
d = spec("dcss_dungeon_ai")
setup = 5 + 1 + 1 + 1 + 2 + 5 * 0.2                              # :119-124
suicide = 12 * 0.2 + 8 * 0.15 + 0.6 + 8 * 0.25 + 2.0 + 0.2 + 0.6 + 0.5  # :44-62
normal = setup + 900 + 3.0 + suicide + 18 + 1 + 3 + 1 + 1        # :141-157, morgue wait <=18
worst = setup + 900 + 90 + 2 + 3 + 1 + 1                         # hard_timeout = TIMEOUT+90 (:131)
out["dcss"] = {"rescaled": {x: round(rescale_score(d, x), 3) for x in (0, 12.4, 400, 5000, 20000, 50000)},
               "per_game_sleep_schedule_s": {"setup": setup, "suicide_once": suicide,
                                             "normal_upper": normal, "hard_timeout_path": worst},
               "eval_timeout": 1100, "observed_idle_whole_eval_s": 962.091}

# NetHack: 20 sequential subprocesses x GAME_TIMEOUT 120 s; MAX_STEPS 5000 (eval_nethack.py:19-22).
out["nethack"] = {"games": 10 * 2, "worst_case_s": 20 * 120, "eval_timeout": 3600,
                  "per_step_budget_ms_if_5000_steps": 120 / 5000 * 1000,
                  "rescaled_mean_1000": rescale_score(spec("nethack_dungeon_agent"), 1000)}

# Wesnoth: 3 maps x 10 seeds x 2 repeats sequential, TIMEOUT 180 s each (eval_wesnoth.py:21-30,145-151).
g = 3 * 10 * 2
out["wesnoth"] = {"games": g, "eval_timeout": 900, "mean_s_per_game_to_fit": 900 / g,
                  "worst_case_s": g * 180,
                  "total_s_if_game_takes": {s: g * s for s in (10, 15, 20, 30, 60)}}

# OpenTTD: 20 years of days; OpenTTD runs 74 ticks/day. 5 seeds (eval_cmd) in parallel.
ticks = 365 * 20 * 74
out["openttd"] = {"ticks_per_seed": ticks, "min_ticks_per_s_to_fit_3600s_parallel": ticks / 3600,
                  "rescaled": {x: rescale_score(spec("openttd_transport_ai"), x) for x in (1, 1e5, 1e6, 1e7, 1e8, 1e9)}}

# Bipedal: ORIGINAL sebench_eval.py scoring functions.
p = os.path.join(os.path.dirname(__file__), "..", "_game-tasks-triage", "bipedal", "orig_sebench_eval.py")
sp = importlib.util.spec_from_file_location("orig_sebench_eval", p); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
def bip(n_eng, normal_r, hard_r):
    raw = m.compute_final_score(m.compute_normal_score(normal_r), m.compute_hardcore_score(hard_r))
    s, _ = m.strict_score(n_eng, raw)
    return {"raw_loco": round(raw, 3), "task_score": s,
            "rescaled": rescale_score(spec("bipedalwalker_locomotion_rl"), s)}
out["bipedal"] = {"loadable_untrained(-100,-110)": bip(4, -100, -110),
                  "solves_normal_only(300,-100)": bip(4, 300, -100),
                  "perfect(320,320)": bip(4, 320, 320),
                  "missing_checkpoint": bip(1, -200, -200),
                  "worst_case_eval_s": 2 * 300, "eval_timeout": 900}

# Text adventures: linear 0..upper equals Jericho max_score (anchor.c:84, trinity.c:71, tryst.c:97).
out["text"] = {t: {"upper": spec(t).upper, "rescaled_observed": rescale_score(spec(t), v)}
               for t, v in (("anchorhead_text_adventure", 99), ("trinity_text_adventure", 100),
                            ("tryst_text_adventure", 350))}

print(json.dumps(out, indent=1, default=str))
