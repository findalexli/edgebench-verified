#!/usr/bin/env python3
"""OpenRCT2: (A) repeat official gradings of real archives; (B) the same plugins run to the monitor's 992-day DONE, re-scored at every sample with the judge's own score_scenario."""
import glob, importlib.util, json, os, re, statistics as st, sys
JOB = "evidence/runs/community9-openrct2_theme_park_ai-reps"
LONG = "evidence/runs/community9-openrct2_theme_park_ai-long"
MONTH_DAYS = [31, 30, 31, 30, 31, 31, 30, 31]  # March to October

print("== A. official path: sforge eval, 120 s per scenario, 4 CPUs; final normalized score = raw/400")
rows = {}
for f in sorted(glob.glob(JOB + "/result/out/sf/runs/*/openrct2_theme_park_ai/submissions/manual-1/report.json")):
    label = f.split("/runs/")[-1].split("/")[0]
    m = re.match(r"(.+)-(\d+)-old", label)
    d = json.load(open(f))
    out = open(os.path.dirname(f) + "/judge_output.txt", errors="replace").read()
    samples = [int(x) for x in re.findall(r"judge diagnostics:.*samples (\d+)", out)]
    norm = re.findall(r"normalized = ([\d.]+)", out)
    rows.setdefault(m.group(1), []).append((int(m.group(2)), d["score"], d["score_0_100"], d["valid"], round(d["runtime_seconds"]), samples, norm))
for w, v in sorted(rows.items()):
    v.sort()
    s = [x[2] for x in v]
    print(f"{w} n={len(s)} normalized {s} spread={max(s)-min(s):.2f} mean={st.mean(s):.2f} all_valid={all(x[3] for x in v)}")
    for x in v:
        print(f"   run {x[0]} raw={x[1]:.0f} runtime={x[4]}s samples per scenario={x[5]} scenario norms={x[6]}")

if not os.path.exists(LONG + "/result/out/d/openrct2_original_eval.py"):
    sys.exit("long job not collected")
spec = importlib.util.spec_from_file_location("e", LONG + "/result/out/d/openrct2_original_eval.py")
e = importlib.util.module_from_spec(spec); spec.loader.exec_module(e)
print("== B. direct judge evaluate(), timeout 2000 s, one container per scenario")


def replay(raw, cut_s=None, cut_days=None, fname=None):
    """The accounting of run_scenario, stopped at a wall-clock or game-day cut, then the judge's own score_scenario."""
    tok = re.compile(r"__SEBENCH_MONITOR__[0-9a-f]+:(SCORE|DONE):(.*)")
    M = dict(value=0, max_rides=0, max_open_rides=0, max_managed_open_rides=0, max_expansion_rides=0, max_expansion_open_rides=0, max_staff=0, max_guests=0,
             total_samples=0, ride_samples=0, open_ride_samples=0, managed_open_ride_samples=0, expansion_ride_samples=0, expansion_open_ride_samples=0,
             staff_samples=0, seed_ready_samples=0, seed_failed=0, action_errors=0)
    first = last = None; done = False; t_last = None
    for line in raw:
        ts, _, rest = line.partition(" ")
        t = float(ts)
        if cut_s is not None and t > cut_s:
            break
        mm = tok.search(rest)
        if mm:
            F = e.parse_monitor_payload(mm.group(2).strip())
            y, mo, da = [int(x) for x in F["date"].split(",")]
            day = (y - 1) * 245 + sum(MONTH_DAYS[:mo]) + da
            first = day if first is None else first
            if cut_days is not None and day - first > cut_days:
                break
            last = day; t_last = t
            M["total_samples"] += 1
            M["value"] = e.int_field(F, "value")
            r, o, mg, x, xo, sf = [e.int_field(F, k) for k in ("rides", "openRides", "managedOpenRides", "expansionRides", "expansionOpenRides", "staff")]
            M["max_rides"] = max(M["max_rides"], r); M["max_open_rides"] = max(M["max_open_rides"], o); M["max_managed_open_rides"] = max(M["max_managed_open_rides"], mg)
            M["max_expansion_rides"] = max(M["max_expansion_rides"], x); M["max_expansion_open_rides"] = max(M["max_expansion_open_rides"], xo); M["max_staff"] = max(M["max_staff"], sf)
            M["max_guests"] = max(M["max_guests"], e.int_field(F, "guests")); M["seed_failed"] = max(M["seed_failed"], e.int_field(F, "seedFailed"))
            M["ride_samples"] += r >= e.MIN_MAX_RIDES; M["open_ride_samples"] += o >= e.MIN_MAX_OPEN_RIDES; M["managed_open_ride_samples"] += mg >= e.MIN_MAX_OPEN_RIDES
            M["expansion_ride_samples"] += x >= 1; M["expansion_open_ride_samples"] += xo >= e.MIN_MAX_EXPANSION_OPEN_RIDES; M["staff_samples"] += sf >= e.MIN_MAX_STAFF
            M["seed_ready_samples"] += bool(e.int_field(F, "seedReady"))
            if mm.group(1) == "DONE":
                done = True
                break
        elif "__ENGINE_" not in rest:
            tr = e.trim_plugin_log(rest)
            if tr is not None and M["total_samples"] > 0 and e.is_action_error_line(tr):
                M["action_errors"] += 1
    norm = e.score_scenario(fname, M)[0]
    return dict(norm=norm, value=M["value"], days=(last - first) if first is not None else 0, t=t_last, done=done, samples=M["total_samples"], errs=M["action_errors"])


agg = {}
for d in sorted(glob.glob(LONG + "/result/out/d/*-r[0-9]")):
    w = os.path.basename(d)
    for sc in ("large", "medium", "small"):
        fn = f"scenario_{sc}.park"
        p = f"{d}/raw-{sc}.txt"
        if not os.path.exists(p):
            print(w, sc, "missing"); continue
        raw = open(p, errors="replace").read().splitlines()
        rc = [l for l in raw if "__ENGINE_RC__" in l]
        at120 = replay(raw, cut_s=120, fname=fn)
        full = replay(raw, fname=fn)
        o = [json.loads(l[9:]) for l in open(f"{os.path.dirname(d)}/l-{w}-{sc}.out.txt", errors="replace") if l.startswith("LONG_ONE ")] if os.path.exists(f"{os.path.dirname(d)}/l-{w}-{sc}.out.txt") else []
        reported = o[0]["norm"] if o else None
        print(f"{w} {sc}: at 120 s days={at120['days']} samples={at120['samples']} value={at120['value']} norm={at120['norm']:.4f} | end days={full['days']} t={full['t']} DONE={full['done']} samples={full['samples']} value={full['value']} norm={full['norm']:.4f} judge_reported={reported} {rc[-1].split(' ',1)[1] if rc else 'no-rc'}")
        agg.setdefault(w, {})[sc] = (at120, full, reported)
for w, s in sorted(agg.items()):
    if len(s) == 3:
        a = sum(x[0]["norm"] for x in s.values()) / 3
        b = sum(x[1]["norm"] for x in s.values()) / 3
        print(f"{w}: final normalized at 120 s={round(a*10000)/400:.2f} at end of run={round(b*10000)/400:.2f} (raw {round(a*10000)} -> {round(b*10000)})")
