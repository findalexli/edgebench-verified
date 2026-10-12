"""Run the ORIGINAL and CORRECTED judge/tools/score.py run_crate_test() against a
real Cargo fixture crate named cas-pty whose 11 tests carry the real cas-pty test
names. Each scenario selects failing tests via env FIXTURE_FAIL.

usage: python3 -I run_fixture_scenarios.py ORIGINAL_score.py CORRECTED_score.py FIXTURE_WS
"""
import importlib.util, json, os, sys

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

orig, corr, ws = sys.argv[1], sys.argv[2], sys.argv[3]
mods = {"original": load(orig, "score_orig"), "corrected": load(corr, "score_corr")}
EX = "test_pty_config_claude_with_teams"
scen = {
  "S1_all_pass": [],
  "S2_only_exempt_fails": [EX],
  "S3_exempt_passes_one_other_fails": ["test_pty_config_default"],
  "S4_exempt_passes_two_others_fail": ["test_pty_config_default", "test_pty_config_claude"],
  "S5_exempt_and_one_other_fail": [EX, "test_pty_config_default"],
  "S6_only_lead_fails_collision_name": ["test_pty_config_claude_with_teams_lead"],
}
out = {}
for s, fails in scen.items():
    os.environ["FIXTURE_FAIL"] = ",".join(fails)
    for k, m in mods.items():
        m.HIDDEN_TESTS_BY_CRATE = {}
        r = m.run_crate_test(ws, "cas-pty", 300)
        out[f"{s}/{k}"] = {"status": r.status, "passed": r.passed, "failed": r.failed, "total": r.total,
                           "true_failures": len(fails),
                           "L3_points_from_cas_pty_if_recording_29_of_29": round(4 * (r.passed + 29) / (r.total + 29), 4)}
        print(f"{s:40s} {k:9s} status={r.status:9s} passed={r.passed:2d} failed={r.failed:2d} total={r.total:2d} (true failures={len(fails)})")
json.dump(out, open(os.environ.get("OUT_JSON", "/dev/stdout"), "w"), indent=1)
