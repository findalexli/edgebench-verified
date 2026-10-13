#!/usr/bin/env python3
"""Run one bounded native job on one owned E2B worker, then kill it.

Usage (an interpreter with the e2b SDK and python-dotenv):
  python3 tools/e2b_run.py \
      --job evidence/runs/<name> [--lifetime 3600] [--budget 3000]

A job directory contains `run.sh` (executed as root in /job inside the worker, which has
Docker) plus any small inputs. `run.sh` must write everything worth keeping under /job/out/.
The E2B key is read locally ($E2B_API_KEY, or the .env file named by $EBV_E2B_ENV or by the one-line
file .internal/e2b-env-path) and never sent to the worker.
Every worker is recorded in evidence/runs/ledger.jsonl and killed by exact ID.
"""
import argparse
import io
import os
import json
import tarfile
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import dotenv_values
from e2b import Sandbox

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'evidence' / 'runs' / 'ledger.jsonl'
TEMPLATE = 'harbor-worker-v4'


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def record(entry):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open('a') as f:
        f.write(json.dumps(entry) + '\n')


def pack(job):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz') as tar:
        tar.add(job, arcname='job')
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--job', required=True, type=Path)
    ap.add_argument('--lifetime', type=int, default=3600)
    ap.add_argument('--budget', type=int, default=3000, help='seconds allowed for run.sh')
    a = ap.parse_args()
    job = a.job.resolve()
    assert (job / 'run.sh').is_file(), 'job needs run.sh'
    assert a.budget + 300 <= a.lifetime <= 3600, 'budget must leave 5 min for collection'
    env = os.environ.get('EBV_E2B_ENV')
    cfg = ROOT / '.internal' / 'e2b-env-path'
    if not env and cfg.exists():
        env = cfg.read_text().strip()
    key = os.environ.get('E2B_API_KEY') or (dotenv_values(os.path.expanduser(env)).get('E2B_API_KEY') if env else None)
    assert key, 'no E2B key: set E2B_API_KEY or EBV_E2B_ENV, or write .internal/e2b-env-path'
    out = job / 'result'
    out.mkdir(exist_ok=False)
    entry = {'job': job.name, 'template': TEMPLATE, 'created_at': now(), 'budget_s': a.budget}
    sb = Sandbox.create(template=TEMPLATE, timeout=a.lifetime, api_key=key, request_timeout=30,
                        metadata={'purpose': 'edgebench-verified-native', 'job': job.name})
    entry['sandbox_id'] = sb.sandbox_id
    record({**entry, 'event': 'created'})
    t0 = time.monotonic()
    try:
        sb.files.write('/tmp/job.tar.gz', pack(job), user='root', request_timeout=120)
        sb.commands.run('mkdir -p /job && tar -xzf /tmp/job.tar.gz -C / && mkdir -p /job/out',
                        user='root', timeout=120, request_timeout=30)
        cmd = (f'cd /job && timeout {a.budget} bash run.sh > /job/out/run.log 2>&1; '
               'echo $? > /job/out/exit_code')
        h = sb.commands.run(cmd, user='root', background=True, timeout=0, request_timeout=30)
        h.disconnect()
        deadline = time.monotonic() + a.budget + 60
        status = 'timeout'
        while time.monotonic() < deadline:
            r = sb.commands.run('cat /job/out/exit_code 2>/dev/null || echo running',
                                user='root', timeout=20, request_timeout=30)
            if r.stdout.strip() != 'running':
                status = 'exit=' + r.stdout.strip()
                break
            time.sleep(20)
        sb.commands.run('tar -czf /tmp/out.tar.gz -C /job out', user='root', timeout=120,
                        request_timeout=30)
        raw = sb.files.read('/tmp/out.tar.gz', format='bytes', user='root', request_timeout=300)
        (out / 'out.tar.gz').write_bytes(raw)
        with tarfile.open(out / 'out.tar.gz') as tar:
            tar.extractall(out, filter='data')
        entry['status'] = status
    except BaseException as e:
        entry['status'] = 'error:' + type(e).__name__
        raise
    finally:
        entry['elapsed_s'] = round(time.monotonic() - t0)
        try:
            sb.kill()
            entry['killed'] = True
        except Exception as e:
            entry['killed'] = 'failed:' + type(e).__name__
        entry['ended_at'] = now()
        record({**entry, 'event': 'closed'})
        (out / 'worker.json').write_text(json.dumps(entry, indent=2) + '\n')
        print(json.dumps(entry))


if __name__ == '__main__':
    main()
