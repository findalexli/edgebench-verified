#!/usr/bin/env python3
"""Recover jobs whose local tools/e2b_run.py controller died (e.g. a local network outage) while
the worker kept running. For every live worker whose metadata names a job, wait for /job/out/exit_code,
collect /job/out exactly like e2b_run.py, write result/worker.json (the failed controller's record is
kept as worker-controller-failed.json), append ledger events, and kill the worker by exact ID.
Usage: python3 tools/e2b_recover.py [JOB ...]   (default: every live worker with a job in evidence/runs)"""
import io, json, os, sys, tarfile, threading, time
from datetime import datetime, timezone
from pathlib import Path
from dotenv import dotenv_values
from e2b import Sandbox
ROOT = Path(__file__).resolve().parents[1]; LEDGER = ROOT / 'evidence/runs/ledger.jsonl'
KEY = os.environ.get('E2B_API_KEY') or dotenv_values(os.path.expanduser(
    os.environ.get('EBV_E2B_ENV') or (ROOT / '.internal/e2b-env-path').read_text().strip())).get('E2B_API_KEY')
lock = threading.Lock()
def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def record(e):
    with lock, LEDGER.open('a') as f: f.write(json.dumps(e) + '\n')
def run(sb, c, t=60): return sb.commands.run(c, user='root', timeout=t, request_timeout=30)
def recover(info):
    job = info.metadata['job']; jd = ROOT / 'evidence/runs' / job; out = jd / 'result'
    entry = {'job': job, 'sandbox_id': info.sandbox_id, 'recovered': True, 'recover_started_at': now()}
    status = 'expired'
    try:
        deadline = info.end_at.timestamp() - 150
        sb = Sandbox.connect(info.sandbox_id, api_key=KEY)
        while time.time() < deadline:
            try:
                r = run(sb, 'cat /job/out/exit_code 2>/dev/null || echo running', 20)
                if r.stdout.strip() != 'running': status = 'exit=' + r.stdout.strip(); break
            except Exception as e:
                time.sleep(10); sb = Sandbox.connect(info.sandbox_id, api_key=KEY); continue
            time.sleep(30)
        run(sb, 'tar -czf /tmp/out.tar.gz -C /job out', 120)
        raw = sb.files.read('/tmp/out.tar.gz', format='bytes', user='root', request_timeout=300)
        out.mkdir(exist_ok=True)
        if (out / 'worker.json').exists(): (out / 'worker.json').rename(out / 'worker-controller-failed.json')
        if (out / 'out').exists(): (out / 'out').rename(out / f'out-partial-{int(time.time())}')
        (out / 'out.tar.gz').write_bytes(raw)
        with tarfile.open(out / 'out.tar.gz') as tar: tar.extractall(out, filter='data')
        entry['status'] = status
    except BaseException as e:
        entry['status'] = 'error:' + type(e).__name__
    finally:
        try: Sandbox.connect(info.sandbox_id, api_key=KEY).kill(); entry['killed'] = True
        except Exception as e: entry['killed'] = 'failed:' + type(e).__name__
        entry['ended_at'] = now(); record({**entry, 'event': 'closed'})
        if out.exists(): (out / 'worker.json').write_text(json.dumps(entry, indent=2) + '\n')
        print(json.dumps(entry), flush=True)
want = set(sys.argv[1:])
p = Sandbox.list(api_key=KEY); items = p.next_items() if hasattr(p, 'next_items') else p
todo = [s for s in items if (s.metadata or {}).get('job') and (ROOT / 'evidence/runs' / s.metadata['job']).is_dir()
        and (not want or s.metadata['job'] in want)]
print(len(todo), 'workers to recover', flush=True)
ts = [threading.Thread(target=recover, args=(s,)) for s in todo]
for t in ts: t.start()
for t in ts: t.join()
