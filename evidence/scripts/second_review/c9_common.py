"""Shared reader for the community9 tables: judge_local JSON (g/) and sforge reports (sf/)."""
import collections, glob, json, os, re, statistics


def read_grades(jobs):
    """Return {(arm, side): [(score, phases, failed_tests, job)]} from judge_local outputs."""
    rows = collections.defaultdict(list)
    for job in jobs:
        for f in sorted(glob.glob(f"evidence/runs/{job}/result/out/g/*.json")):
            d = json.load(open(f))
            m = re.match(r"(.+)-p\d+-(old|new)\.json$", os.path.basename(f))
            log = d.get("log_tail") or ""
            phases = re.findall(r"^Phase (\d+): (\d+/\d+) passed", log, re.M)
            failed = sorted(set(re.findall(r"::(\S+) (?:FAILED|ERROR)", log)))
            rows[m.group(1), m.group(2)].append((d.get("score_0_100"), " ".join(p for _, p in phases), failed, job))
    return rows


def print_grades(jobs, order):
    rows = read_grades(jobs)
    print("| arm | judge | n | scores | phases (last run) | tests that failed (last run, excluded when also failing on the unchanged control) |")
    print("|---|---|---|---|---|---|")
    for arm in order:
        for side in ("old", "new"):
            r = rows.get((arm, side), [])
            if not r:
                continue
            s = [x[0] for x in r]
            print(f"| {arm} | {side} | {len(s)} | {', '.join(str(round(v, 4)) if v is not None else 'None' for v in s)} | {r[-1][1]} | {', '.join(r[-1][2][:8])} |")
    return rows


def mean(xs):
    return round(statistics.mean(xs), 4)
