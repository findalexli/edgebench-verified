# One seed through the original evaluator's own run_experiments call shape; dump save count, dates, error flags.
import json, sys, time, inspect
sys.path.insert(0, "/tmp")
import openttd_original_eval as ev
import openttdlab
from openttdlab import run_experiments, local_folder
t = time.monotonic()
res = run_experiments(openttd_version=ev.OPENTTD_VERSION, opengfx_version=ev.OPENGFX_VERSION,
                      get_http_client=ev.get_http_client,
                      experiments=[{"seed": 0, "ais": (local_folder("/home/workspace/openttd_ai/my_ai", ai_name="MyAI"),), "days": 365 * ev.GAME_YEARS}],
                      max_workers=1)
el = time.monotonic() - t
print("rows", len(res), "elapsed_s", round(el, 1))
if res:
    print("row keys", sorted(res[0].keys()))
    def brief(r):
        p = r["chunks"].get("PLYR", {}).get("0", {})
        oe = p.get("old_economy", [])
        return {"date": str(r.get("date")), "error": r.get("error"), "money": p.get("money"), "loan": p.get("current_loan"),
                "cv0": oe[0].get("company_value") if oe else None, "n_old_eco": len(oe)}
    for r in res[:3] + res[-3:]:
        print(json.dumps(brief(r)))
    print("error flags:", sum(1 for r in res if r.get("error")), "of", len(res))
    print("cv>1 count:", sum(1 for r in res if (r['chunks'].get('PLYR',{}).get('0',{}).get('old_economy') or [{}])[0].get('company_value',0) > 1))
    for k in res[-1]:
        if k not in ("chunks",):
            v = res[-1][k]; print("last", k, str(v)[:1500])
    print(json.dumps(ev.extract_company_value(res), default=str))
