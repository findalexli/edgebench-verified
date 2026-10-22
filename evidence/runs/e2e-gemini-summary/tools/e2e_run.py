#!/usr/bin/env python3
"""Run one long job on one owned E2B worker past the 1-hour sandbox limit.

Like tools/e2b_run.py (one job, append-only ledger, exact kill), plus:
  * the worker is paused and resumed every --segment seconds, which resets
    E2B's runtime window while keeping every process and file;
  * /job/out is checkpointed to <job>/result/ckpt-<n>.tar.gz every --ckpt seconds;
  * secrets named with --secret NAME=LOCALFILE are written to /run/ebv/NAME
    (mode 600), never into the job tarball or the result.

Usage:
  python e2e_run.py --job DIR --budget SECONDS [--segment 2880] [--secret gemini_key=PATH]
"""
import argparse, io, json, os, tarfile, time
from datetime import datetime, timezone
from pathlib import Path
from dotenv import dotenv_values
from e2b import Sandbox

LEDGER = Path('/home/alex/edgebench-verified/evidence/runs/ledger.jsonl')
TEMPLATE = 'harbor-worker-v4'


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def log(msg):
    print(f'[{now()}] {msg}', flush=True)


def record(entry):
    with LEDGER.open('a') as f:
        f.write(json.dumps(entry) + '\n')


def pack(job):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz') as tar:
        tar.add(job, arcname='job', filter=lambda ti: None if ti.name.startswith('job/result') or ti.name.startswith('job/.') else ti)
    return buf.getvalue()


def run(sb, cmd, t=60):
    return sb.commands.run(cmd, user='root', timeout=t, request_timeout=30)


def collect(sb, out, name):
    # The run keeps writing while a checkpoint is taken; tar exits 1 for "file changed as we read it".
    run(sb, 'tar --warning=no-file-changed -czf /tmp/out.tar.gz -C /job out; [ $? -le 1 ]', 300)
    raw = sb.files.read('/tmp/out.tar.gz', format='bytes', user='root', request_timeout=600)
    (out / name).write_bytes(raw)
    return len(raw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--job', required=True, type=Path)
    ap.add_argument('--budget', type=int, required=True, help='seconds allowed for run.sh')
    ap.add_argument('--segment', type=int, default=2880, help='pause+resume after this many seconds')
    ap.add_argument('--ckpt', type=int, default=900)
    ap.add_argument('--secret', action='append', default=[])
    ap.add_argument('--env', default='/home/alex/agentsmd-rl/.env')
    ap.add_argument('--template', default=TEMPLATE)
    ap.add_argument('--poll-tolerance', type=int, default=900, help='seconds of failed polls before giving up')
    ap.add_argument('--attach', help='sandbox id of a running job whose controller died; resume control of it')
    a = ap.parse_args()
    job = a.job.resolve()
    assert (job / 'run.sh').is_file()
    key = os.environ.get('E2B_API_KEY') or dotenv_values(a.env).get('E2B_API_KEY')
    out = job / 'result'
    out.mkdir(exist_ok=bool(a.attach))
    entry = {'job': job.name, 'template': a.template, 'created_at': now(), 'budget_s': a.budget,
             'kind': 'e2e-long', 'segment_s': a.segment}
    if a.attach:
        # Controller recovery: the worker kept running; pause+resume at once to reset its window.
        sid = a.attach
        sb = Sandbox.connect(sid, timeout=3600, api_key=key)
        sb.pause(); time.sleep(5)
        sb = Sandbox.connect(sid, timeout=3600, api_key=key)
        entry.update(sandbox_id=sid, attached=True)
        record({**entry, 'event': 'attached'})
        log(f'attached {sid} (paused+resumed)')
    else:
        sb = Sandbox.create(template=a.template, timeout=3600, api_key=key, request_timeout=30,
                            metadata={'purpose': 'edgebench-verified-e2e', 'job': job.name})
        sid = sb.sandbox_id
        entry['sandbox_id'] = sid
        record({**entry, 'event': 'created'})
        log(f'created {sid}')
    t0 = time.monotonic()
    seg0 = t0
    last_ckpt = t0
    n_ckpt = len(list(out.glob('ckpt-*.tar.gz')))
    pauses = []
    try:
        if not a.attach:
            run(sb, 'mkdir -p /run/ebv && chmod 700 /run/ebv')
            for s in a.secret:
                name, path = s.split('=', 1)
                sb.files.write(f'/run/ebv/{name}', Path(path).read_text().strip() + '\n', user='root')
                run(sb, f'chmod 600 /run/ebv/{name}')
            sb.files.write('/tmp/job.tar.gz', pack(job), user='root', request_timeout=300)
            run(sb, 'mkdir -p /job && tar -xzf /tmp/job.tar.gz -C / && mkdir -p /job/out', 300)
            h = sb.commands.run(f'cd /job && timeout {a.budget} bash run.sh > /job/out/run.log 2>&1; '
                                'echo $? > /job/out/exit_code', user='root', background=True, timeout=0,
                                request_timeout=30)
            h.disconnect()
            log('started run.sh')
        # run.sh enforces the budget itself (timeout); an attached controller waits up to a full budget.
        deadline = t0 + a.budget + 120
        status = 'timeout'
        last_ok = time.monotonic()
        while time.monotonic() < deadline:
            time.sleep(30)
            try:
                r = run(sb, 'cat /job/out/exit_code 2>/dev/null || echo running', 30)
                last_ok = time.monotonic()
            except Exception as e:
                # A local network outage must not abandon a worker that keeps running.
                log(f'poll error {type(e).__name__}: {str(e)[:200]}; reconnecting')
                if time.monotonic() - last_ok > a.poll_tolerance:
                    raise
                try:
                    sb = Sandbox.connect(sid, timeout=3600, api_key=key)
                except Exception:
                    pass
                continue
            if r.stdout.strip() != 'running':
                status = 'exit=' + r.stdout.strip()
                break
            if time.monotonic() - last_ckpt > a.ckpt:
                last_ckpt = time.monotonic()
                try:
                    n_ckpt += 1
                    size = collect(sb, out, f'ckpt-{n_ckpt:03d}.tar.gz')
                    log(f'checkpoint {n_ckpt} ({size} bytes)')
                except Exception as e:
                    # A failed checkpoint must never end a run that is still going.
                    log(f'checkpoint {n_ckpt} failed: {type(e).__name__}: {str(e)[:200]}')
            if time.monotonic() - seg0 > a.segment:
                tp = time.monotonic()
                for attempt in range(6):
                    try:
                        sb.pause()
                        time.sleep(5)
                        sb = Sandbox.connect(sid, timeout=3600, api_key=key)
                        break
                    except Exception as e:
                        log(f'pause/resume attempt {attempt} failed: {type(e).__name__}: {str(e)[:200]}')
                        time.sleep(20)
                        try:
                            sb = Sandbox.connect(sid, timeout=3600, api_key=key)
                        except Exception:
                            pass
                seg0 = time.monotonic()
                pauses.append({'at_s': round(tp - t0), 'gap_s': round(seg0 - tp, 1)})
                record({**entry, 'event': 'paused-resumed', 'at': now(), 'gap_s': pauses[-1]['gap_s']})
                log(f'paused+resumed (gap {pauses[-1]["gap_s"]}s)')
        for attempt in range(4):
            # A multi-GB result download can be dropped by the server; the worker still holds the data.
            try:
                collect(sb, out, 'out.tar.gz'); break
            except Exception as e:
                log(f'final collect attempt {attempt} failed: {type(e).__name__}: {str(e)[:200]}')
                if attempt == 3: raise
                time.sleep(30)
                sb = Sandbox.connect(sid, timeout=3600, api_key=key)
        with tarfile.open(out / 'out.tar.gz') as tar:
            tar.extractall(out, filter='data')
        entry['status'] = status
    except BaseException as e:
        entry['status'] = 'error:' + type(e).__name__ + ':' + str(e)[:200]
        try:
            collect(sb, out, 'out-at-error.tar.gz')
        except Exception:
            pass
        raise
    finally:
        entry['elapsed_s'] = round(time.monotonic() - t0)
        entry['pauses'] = pauses
        try:
            Sandbox.connect(sid, api_key=key).kill()
            entry['killed'] = True
        except Exception as e:
            entry['killed'] = 'failed:' + type(e).__name__
        entry['ended_at'] = now()
        record({**entry, 'event': 'closed'})
        (out / 'worker.json').write_text(json.dumps(entry, indent=2) + '\n')
        log(json.dumps(entry))


if __name__ == '__main__':
    main()
