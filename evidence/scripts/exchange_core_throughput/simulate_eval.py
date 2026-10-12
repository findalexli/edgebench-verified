"""Feed synthetic Maven outputs through the original eval_exchange_core.py
(subprocess.run mocked) and the repo's score_sum parser / extract_score / log_max.
Run from repo root: python3 evidence/scripts/exchange_core_throughput/simulate_eval.py"""
import io, contextlib, importlib.util, math, os, subprocess, sys, types
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(here, "../../..")))
from sforge.harness.log_parsers.score_sum import parse_score_sum
from sforge.harness.grading import extract_score
spec = importlib.util.spec_from_file_location("ev", os.path.join(here, "eval_exchange_core.orig.py"))
ev = importlib.util.module_from_spec(spec); spec.loader.exec_module(ev)
B, E = 2090.634594076933, 6000.0
def log_max(r): return 0.0 if r <= 0 else max(0, min(100, 100*math.log(r/B)/math.log(E/B)))
TS = "2026-10-11/00:00:00.000/UTC [pool-1] INFO  e.c.t.u.ThroughputTestsModule - "
CASES = {
 "normal_pass": (0, "".join(f"{TS}{i}. 2.500 MT/s\n" for i in range(50)) + TS + "Average: 2.5 MT/s\n[INFO] BUILD SUCCESS"),
 "assert_fail_default_logback": (1, TS + "0. 9.000 MT/s\n[ERROR] AssertionFailedError\n[INFO] BUILD FAILURE"),
 "assert_fail_msgonly_logback": (1, "0. 9.000 MT/s\n[ERROR] AssertionFailedError\n[INFO] BUILD FAILURE"),
 "injected_static_println_then_pass": (0, "Average: 6.500 MT/s\n" + TS + "0. 2.000 MT/s\n" + TS + "Average: 2.0 MT/s\nBUILD SUCCESS"),
 "injected_println_compile_ok_tests_fail": (1, "Average: 6.500 MT/s\n[ERROR] Tests run: 1, Failures: 1\nBUILD FAILURE"),
}
os.chdir("/")
ev.os.chdir = lambda p: None
for name, (rc, out) in CASES.items():
    ev.subprocess.run = lambda *a, **k: types.SimpleNamespace(stdout=out, stderr="", returncode=rc)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): ev.main()
    o = buf.getvalue()
    res = parse_score_sum(o); sc = extract_score(o)
    pr = sum(r["status"] == "PASSED" for r in res) / len(res)
    print(f"{name:40s} rc={rc} case={[l for l in o.splitlines() if l.startswith('CASE')][0]!r} TOTAL={sc} pass_rate={pr} norm={log_max(sc):.2f}")
