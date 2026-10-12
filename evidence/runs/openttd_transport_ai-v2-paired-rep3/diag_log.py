# Logging diagnostic for one submission (EdgeBench Verified audit).
# Runs the ORIGINAL evaluator's own run_experiments call shape (same versions, seeds 0..N-1,
# 20 game years) with one change: OpenTTD gets `-d script=4` so AILog.Info lines reach the
# captured output. Then, per seed, compares the scorer's company_value (the original
# extract_company_value) with the AI's last logged GetQuarterlyCompanyValue(SELF, 1).
# Usage: python3 diag_log.py AI_DIR [N_SEEDS] [DAYS]
import json, os, re, subprocess, sys, time
from collections import defaultdict
sys.path.insert(0, "/tmp")
import openttd_original_eval as ev
import openttdlab
from openttdlab import run_experiments, local_folder

ai_dir = sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
days = int(sys.argv[3]) if len(sys.argv) > 3 else 365 * ev.GAME_YEARS

_orig = subprocess.check_output
def _patched(args, *a, **k):
    if isinstance(args, (tuple, list)) and '-g' in args and 'openttd' in os.path.basename(str(args[0])):
        args = (args[0], '-d', 'script=4') + tuple(args[1:])
    return _orig(args, *a, **k)
openttdlab.subprocess.check_output = _patched   # Pool forks, so workers inherit this

t = time.monotonic()
res = run_experiments(openttd_version=ev.OPENTTD_VERSION, opengfx_version=ev.OPENGFX_VERSION,
                      get_http_client=ev.get_http_client,
                      experiments=({"seed": s, "ais": (local_folder(ai_dir, ai_name="MyAI"),), "days": days}
                                   for s in range(n)),
                      max_workers=min(n, os.cpu_count() or 4))
print("rows", len(res), "elapsed_s", round(time.monotonic() - t, 1))
by_seed = defaultdict(list)
for r in res:
    by_seed[r["experiment"]["seed"]].append(r)
summary = []
for s in sorted(by_seed):
    rows = by_seed[s]
    out = rows[-1]["output"]
    info = ev.extract_company_value(rows)
    cv_lines = [l for l in out.splitlines() if "] CV " in l]
    probe = [l.split("[I] ", 1)[-1] for l in out.splitlines() if "PROBE" in l or "Company value:" in l][:4]
    errs = [l for l in out.splitlines() if "[S]" in l or "died" in l or "[E]" in l][:8]
    last = cv_lines[-1] if cv_lines else ""
    m = re.search(r"CV (\S+) cur=(-?\d+) q1=(-?\d+) bank=(-?\d+) loan=(-?\d+)", last)
    cv_series = [int(x) for x in re.findall(r"q1=(-?\d+)", "\n".join(cv_lines))]
    rec = {"seed": s, "saves": len(rows), "final_date": str(info["final_date"]), "error_flag": info["error"],
           "scorer_company_value": info["company_value"], "scorer_cv_date": str(info["cv_date"]),
           "money": info["money"], "loan": info["loan"],
           "n_cv_log_lines": len(cv_lines), "n_company_value_log_lines": out.count("Company value:"),
           "last_log": last.split("[I] ", 1)[-1],
           "last_logged_q1": int(m.group(3)) if m else None, "last_logged_cur": int(m.group(2)) if m else None,
           "q1_distinct": sorted(set(cv_series))[:6], "probe": probe, "script_errors": errs,
           "old_economy0_cv_final_save": ((rows[-1]["chunks"].get("PLYR", {}).get("0", {}).get("old_economy") or [{}])[0]
                                          .get("company_value"))}
    rec["scorer_equals_logged_q1"] = (rec["last_logged_q1"] == rec["old_economy0_cv_final_save"])
    summary.append(rec)
    print(json.dumps(rec, default=str))
print("SUMMARY " + json.dumps({"seeds": len(summary),
      "any_error": any(r["error_flag"] for r in summary),
      "mean_scorer_cv": sum(r["scorer_company_value"] for r in summary) / max(1, len(summary)),
      "all_logged_q1_equal_final_old_economy0": all(r["scorer_equals_logged_q1"] for r in summary)}))
