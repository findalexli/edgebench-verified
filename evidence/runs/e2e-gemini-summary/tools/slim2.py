#!/usr/bin/env python3
"""slim2.py JOB...: keep only compact evidence of an e2e / cross-grade job in the repository.

Writes result/out/reports.jsonl (one line per submission: round, score, valid, pass_rate, passed, total, summary)
for e2e runs, then moves every file outside the allow-list to .internal/e2e-artifacts/<job>/ (same relative
path) and appends sha256, bytes and path of each moved file to artifacts-manifest.tsv.
"""
import fnmatch, hashlib, json, shutil, sys
from pathlib import Path

REPO = Path('/home/alex/edgebench-verified'); RUNS = REPO / 'evidence/runs'; DEST = REPO / '.internal/e2e-artifacts'
KEEP = ['params.env', 'plan.txt', 'run.sh', 'artifacts-manifest.tsv', 'README.md',
        'result/worker.json', 'result/worker-controller-failed.json', 'result/summary.json',
        'result/out/env.txt', 'result/out/images.txt', 'result/out/v2_images.txt', 'result/out/run_exit.txt',
        'result/out/exit_code', 'result/out/proxy.jsonl', 'result/out/proxy_selftest.txt', 'result/out/reports.jsonl',
        'result/out/v2_cleanup.log', 'result/out/derived.json', 'result/out/progress.txt', 'result/out/logs/*.log',
        'result/out/before.txt', 'result/out/after.txt', 'result/out/pull.log', 'result/out/daemon.json',
        'result*/worker.json', 'result*/out/run_exit.txt']


def reports(job):
    out = job / 'result/out'
    rs = []
    for f in sorted(out.glob('sforge-logs/runs/*/*/submissions/*/report.json')):
        r = json.load(open(f))
        rs.append({'round': f.parent.name, 'score': r.get('score'), 'score_0_100': r.get('score_0_100'), 'valid': r.get('valid'),
                   'pass_rate': r.get('pass_rate'), 'passed': r.get('passed'), 'total': r.get('total_tests'),
                   'timed_out': r.get('timed_out'), 'runtime_s': r.get('runtime_seconds'), 'summary': (r.get('summary') or '')[:400]})
    if rs:
        (out / 'reports.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in rs))


for name in sys.argv[1:]:
    job = RUNS / name
    if (job / 'result/out/sforge-logs').exists():
        reports(job)
    rows = []
    for f in sorted(p for p in job.rglob('*') if p.is_file()):
        rel = str(f.relative_to(job))
        if any(fnmatch.fnmatch(rel, k) for k in KEEP) and f.stat().st_size < 20 * 1024 * 1024:
            continue
        h = hashlib.sha256()
        with open(f, 'rb') as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b''): h.update(chunk)
        rows.append(f'{h.hexdigest()}\t{f.stat().st_size}\t{rel}')
        d = DEST / name / rel; d.parent.mkdir(parents=True, exist_ok=True); shutil.move(str(f), d)
    if rows:
        m = job / 'artifacts-manifest.tsv'
        old = m.read_text().splitlines() if m.exists() else []
        m.write_text('\n'.join(old + rows) + '\n')
    for d in sorted((p for p in job.rglob('*') if p.is_dir()), key=lambda p: -len(p.parts)):
        if not any(d.iterdir()): d.rmdir()
    print(name, 'moved', len(rows))
