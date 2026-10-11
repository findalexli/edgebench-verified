#!/usr/bin/env python3
"""Resource guard for trusted, non-daemonizing local jobs (not a sandbox).

Example: python3 tools/run_bounded.py --timeout-seconds 30 -- python3 script.py
No job starts on WSL unless Windows physical AND commit headroom and Linux
MemAvailable are each at least 4 GiB. See audit/reviews/resource_guard.txt.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import time


MIB = 1024**2
GIB = 1024**3
MIN_HEADROOM = 4 * GIB
MAX_MEMORY = GIB
POLL_SECONDS = 0.25
HEADROOM_SECONDS = 2.0
PROBE_TIMEOUT = 3.0
ROOT = Path(__file__).resolve().parents[1]
TASK_ID = hashlib.sha256(str(ROOT).encode()).hexdigest()[:20]
# Never unlink a flock file: doing so allows simultaneous locks on two inodes.
LOCK_PATH = Path('/tmp') / f'edgebenchverified-{os.getuid()}-{TASK_ID}.lock'
SUMMARY_LOG = ROOT / 'audit' / 'resource_guard_runs.jsonl'
THREAD_ENV = {
    'OMP_NUM_THREADS': '1', 'OMP_THREAD_LIMIT': '1', 'MKL_NUM_THREADS': '1',
    'OPENBLAS_NUM_THREADS': '1', 'NUMEXPR_NUM_THREADS': '1',
    'VECLIB_MAXIMUM_THREADS': '1', 'BLIS_NUM_THREADS': '1',
}
WINDOWS_QUERY = """$ErrorActionPreference = 'Stop'
$m = Get-CimInstance -ClassName Win32_PerfFormattedData_PerfOS_Memory
@{free_physical_bytes = [long]$m.AvailableBytes;
  free_commit_bytes = ([long]$m.CommitLimit - [long]$m.CommittedBytes)} |
    ConvertTo-Json -Compress
"""


class GuardError(Exception):
    """A stable reason code, never command text or host error output."""


class EngineError(Exception):
    """Placeholder until the fixed, hash-checked local Engine module is loaded."""


local_session = None
FROZEN_RUNTIME = 'audit/evidence/local-docker-t3-proposal-v2'
FROZEN_MANIFEST_SHA = 'bcc16c0cb7f5de9891890caa1a9c4b38381f93947ae9cea328170aa2ca7ff5c6'
INTEGRATION_BINDING = 'audit/evidence/local-docker-t3-guard-integration-v1/integration.json'


def bounded_json_file(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 131072:
        raise GuardError('local_binding_or_lease_unavailable')
    return json.loads(path.read_bytes())


def refuse_local_unresolved():
    path = ROOT / 'audit/local-state/local-heavy-lease.json'
    if path.exists() or path.is_symlink():
        value = bounded_json_file(path)
        if type(value) is not dict or value.get('state') != 'closed':
            raise GuardError('previous_local_container_unresolved')


def load_local_runtime():
    """Only this frozen T3 package; normal trusted-process jobs do not import it."""
    global local_session, EngineError
    runtime_dir = ROOT / FROZEN_RUNTIME
    binding = bounded_json_file(ROOT / INTEGRATION_BINDING)
    actual_guard = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if (Path(__file__).resolve() != (ROOT / 'tools/run_bounded.py').resolve()
            or binding.get('guard_path') != 'tools/run_bounded.py'
            or binding.get('guard_sha256') != actual_guard
            or binding.get('runtime_path') != FROZEN_RUNTIME
            or binding.get('runtime_manifest_sha256') != FROZEN_MANIFEST_SHA):
        raise GuardError('integrated_guard_identity_mismatch')
    manifest_path = runtime_dir / 'manifest.json'
    manifest = bounded_json_file(manifest_path)
    if hashlib.sha256(manifest_path.read_bytes()).hexdigest() != FROZEN_MANIFEST_SHA:
        raise GuardError('frozen_local_runtime_manifest_mismatch')
    expected = {'worker.py', 'runner.py', 'dcss_build.py', 'native_fixture.py', 'source_recipe.py',
                'expected.json', 'engine.py', 'local_session.py', 'child.py', 'candidate_guard.py', 'launch.py'}
    if set(manifest.get('files', {})) != expected:
        raise GuardError('frozen_local_runtime_file_set')
    for name, sha in manifest['files'].items():
        path = runtime_dir / name
        if path.is_symlink() or path.stat().st_size > 1048576 or hashlib.sha256(path.read_bytes()).hexdigest() != sha:
            raise GuardError('frozen_local_runtime_file_mismatch')
    if local_session is None:
        import importlib
        sys.path.insert(0, str(runtime_dir))
        try:
            engine_module = importlib.import_module('engine')
            session_module = importlib.import_module('local_session')
            child_module = importlib.import_module('child')
        finally:
            sys.path.pop(0)
        for module, name in ((engine_module, 'engine.py'), (session_module, 'local_session.py'), (child_module, 'child.py')):
            if Path(module.__file__).resolve() != (runtime_dir / name).resolve():
                raise GuardError('frozen_local_module_origin')
        EngineError = engine_module.EngineError
        local_session = session_module
    return local_session, {'integrated_guard_sha256': actual_guard,
                           'runtime_manifest_sha256': FROZEN_MANIFEST_SHA,
                           'integration_binding_sha256': hashlib.sha256((ROOT / INTEGRATION_BINDING).read_bytes()).hexdigest()}


def local_t3_main():
    import uuid
    session_module, identity = load_local_runtime()
    affinity = set(sorted(os.sched_getaffinity(0))[:2])
    child_limits(128 * MIB, affinity)
    os.environ.update(THREAD_ENV)
    session = session_module.LocalT3Session(Path('/tmp/edgebenchverified-local') / str(uuid.uuid4()))
    result = run_job([], 480, 128 * MIB, 128 * MIB, local_t3=session)
    result['execution_identity'] = identity
    if session.root.exists():
        session_module.durable(session.root / 'guard-result.json', result)
    print(json.dumps({'job_root': str(session.root), 'guard': result}, sort_keys=True))
    return result['exit_code']


class GuardInterrupted(Exception):
    def __init__(self, signum):
        self.signum = signum


def is_wsl():
    try:
        release = Path('/proc/sys/kernel/osrelease').read_text().lower()
    except OSError as exc:
        raise GuardError('linux_identity_unavailable') from exc
    return bool('microsoft' in release or 'wsl' in release
                or os.environ.get('WSL_INTEROP') or os.environ.get('WSL_DISTRO_NAME'))


def linux_available_bytes():
    try:
        for line in Path('/proc/meminfo').read_text().splitlines():
            if line.startswith('MemAvailable:'):
                fields = line.split()
                if len(fields) != 3 or fields[2] != 'kB':
                    break
                value = int(fields[1]) * 1024
                if value >= 0:
                    return value
    except (OSError, ValueError):
        pass
    raise GuardError('linux_headroom_unavailable')


def windows_headroom_bytes(timeout=PROBE_TIMEOUT):
    executable = Path('/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe')
    executable = str(executable) if executable.is_file() else shutil.which('powershell.exe')
    if not executable:
        raise GuardError('windows_headroom_unavailable')
    try:
        probe = subprocess.run(
            [executable, '-NoLogo', '-NoProfile', '-NonInteractive', '-Command', WINDOWS_QUERY],
            stdin=subprocess.DEVNULL, capture_output=True, text=True,
            encoding='utf-8-sig', timeout=timeout, check=False,
        )
        if probe.returncode != 0:
            raise ValueError('query failed')
        data = json.loads(probe.stdout)
        values = {key: data[key] for key in ('free_physical_bytes', 'free_commit_bytes')}
        if any(type(value) is not int or value < 0 for value in values.values()):
            raise ValueError('invalid metrics')
        return values
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError):
        raise GuardError('windows_headroom_unavailable') from None


def host_snapshot(windows_required, timeout=PROBE_TIMEOUT):
    # Read Linux after the potentially slower Windows query, keeping it fresh.
    values = windows_headroom_bytes(timeout) if windows_required else {}
    values['linux_available_bytes'] = linux_available_bytes()
    return values


def require_headroom(snapshot, windows_required):
    keys = ['linux_available_bytes']
    if windows_required:
        keys += ['free_physical_bytes', 'free_commit_bytes']
    for key in keys:
        value = snapshot.get(key)
        if type(value) is not int or value < 0:
            raise GuardError('host_headroom_unavailable')
        if value < MIN_HEADROOM:
            raise GuardError(f'low_{key}')


@contextmanager
def singleton_lock():
    try:
        fd = os.open(LOCK_PATH, os.O_CREAT | os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    except OSError as exc:
        raise GuardError('lock_unavailable') from exc
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise GuardError('another_guarded_job_is_running') from exc
        except OSError as exc:
            raise GuardError('lock_unavailable') from exc
        yield
    finally:
        os.close(fd)


def group_rss_bytes(pgid):
    """Sum resident pages of current group members, including forked children.

    Shared pages can be counted more than once. Fast spikes and processes that
    leave the group are not covered; this is not kernel aggregate accounting.
    """
    total = 0
    try:
        entries = list(Path('/proc').iterdir())
        page_size = os.sysconf('SC_PAGE_SIZE')
        for entry in entries:
            if not entry.name.isdigit():
                continue
            try:
                raw = (entry / 'stat').read_text()
            except (FileNotFoundError, ProcessLookupError):
                continue  # The process exited during this sample.
            # comm (field 2) can contain whitespace and closing parentheses.
            fields = raw[raw.rfind(')') + 2:].split()
            if int(fields[2]) == pgid:
                total += max(0, int(fields[21])) * page_size
    except (OSError, ValueError, IndexError) as exc:
        raise GuardError('process_rss_unavailable') from exc
    return total


def child_limits(memory_bytes, affinity):
    os.sched_setaffinity(0, affinity)
    os.setpriority(os.PRIO_PROCESS, 0, max(10, os.getpriority(os.PRIO_PROCESS, 0)))
    _, inherited_hard = resource.getrlimit(resource.RLIMIT_AS)
    limit = memory_bytes if inherited_hard == resource.RLIM_INFINITY else min(memory_bytes, inherited_hard)
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def kill_group(process):
    # SIGKILL is deliberate: resource exhaustion must not wait for job handlers.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=2)
        return True
    except subprocess.TimeoutExpired:
        return False  # A task in uninterruptible kernel sleep may remain.


@contextmanager
def interrupt_handlers():
    def interrupted(signum, _frame):
        raise GuardInterrupted(signum)
    old = {signum: signal.signal(signum, interrupted) for signum in (signal.SIGINT, signal.SIGTERM)}
    try:
        yield
    finally:
        for signum, handler in old.items():
            signal.signal(signum, handler)


def run_job(command, timeout_seconds, memory_bytes=MAX_MEMORY, rss_bytes=MAX_MEMORY, *, local_t3=None):
    """Run from the main thread. Host metrics are test seams, not CLI bypasses."""
    if local_t3 is not None:
        load_local_runtime()
        if (type(local_t3) is not local_session.LocalT3Session or command
                or timeout_seconds != 480 or memory_bytes != 128 * MIB or rss_bytes != 128 * MIB):
            raise ValueError('fixed local T3 envelope required')
    if (not command and local_t3 is None) or not math.isfinite(timeout_seconds) or not 0 < timeout_seconds <= 600:
        raise ValueError('a command and a finite timeout in (0, 600] are required')
    if not 0 < memory_bytes <= MAX_MEMORY or not 0 < rss_bytes <= MAX_MEMORY:
        raise ValueError('memory limits must be in (0, 1 GiB]')
    started = time.monotonic()
    process = None
    result = {
        'started_at_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'refused', 'reason': None, 'exit_code': 125, 'child_exit_code': None,
        'windows_headroom_required': None, 'minimum_observed_headroom_bytes': {},
        'host_samples': 0, 'peak_observed_group_rss_bytes': 0,
        'limits': {'minimum_host_headroom_bytes': MIN_HEADROOM, 'max_cpu_affinity': 2,
                   'minimum_nice': 10, 'per_process_address_space_bytes': memory_bytes,
                   'group_rss_bytes': rss_bytes, 'timeout_seconds': timeout_seconds,
                   'math_library_threads': 1},
        'aggregate_cgroup_limits': False,
    }

    def sample_host(timeout):
        snapshot = host_snapshot(result['windows_headroom_required'], timeout)
        result['host_samples'] += 1
        for key, value in snapshot.items():
            if type(value) is int:
                minimum = result['minimum_observed_headroom_bytes']
                minimum[key] = min(minimum.get(key, value), value)
        require_headroom(snapshot, result['windows_headroom_required'])

    try:
        with singleton_lock(), interrupt_handlers():
            refuse_local_unresolved()
            result['windows_headroom_required'] = is_wsl()
            if local_t3 is not None and not result['windows_headroom_required']:
                raise GuardError('desktop_wsl_host_required')
            sample_host(PROBE_TIMEOUT)
            affinity = set(sorted(os.sched_getaffinity(0))[:2])
            if not affinity:
                raise GuardError('cpu_affinity_unavailable')
            env = os.environ.copy()
            env.update(THREAD_ENV)
            launched = time.monotonic()
            deadline = launched + timeout_seconds
            try:
                if local_t3 is not None:
                    command = local_t3.prepare(affinity, started)
                    deadline = min(deadline, local_t3.work_deadline)
                    result['local_container_limits'] = {'memory_bytes': 768 * MIB, 'nano_cpus': 2000000000,
                        'work_seconds': 480, 'cleanup_reserve_seconds': 60, 'cached_image_only': True}
                    sample_host(min(PROBE_TIMEOUT, max(0.001, deadline - time.monotonic())))
                    if time.monotonic() >= deadline:
                        raise GuardError('local_preparation_deadline')
                try:
                    process = subprocess.Popen(
                        command, stdin=subprocess.DEVNULL, env=env, start_new_session=True,
                        preexec_fn=lambda: child_limits(memory_bytes, affinity),
                    )
                except (OSError, subprocess.SubprocessError):
                    raise GuardError('launch_failed') from None
                result['status'] = 'running'
                next_host_check = launched + HEADROOM_SECONDS
                while True:
                    now = time.monotonic()
                    if now >= deadline:
                        result.update(status='stopped', reason='wall_timeout', exit_code=124)
                        break
                    rss = group_rss_bytes(process.pid)
                    result['peak_observed_group_rss_bytes'] = max(result['peak_observed_group_rss_bytes'], rss)
                    if rss > rss_bytes:
                        raise GuardError('group_rss_limit_exceeded')
                    child_status = process.poll()
                    if child_status is not None:
                        result.update(status='completed', reason='child_exited',
                                      exit_code=child_status if child_status >= 0 else 128 - child_status)
                        break
                    if now >= next_host_check:
                        sample_host(min(PROBE_TIMEOUT, max(0.001, deadline - now)))
                        if local_t3 is not None:
                            local_t3.monitor()
                        next_host_check = time.monotonic() + HEADROOM_SECONDS
                    time.sleep(min(POLL_SECONDS, max(0, deadline - time.monotonic())))
            finally:
                # Also remove background children after a normal leader exit.
                # Prevent a second Ctrl-C/SIGTERM from skipping this cleanup.
                old = {s: signal.signal(s, signal.SIG_IGN) for s in (signal.SIGINT, signal.SIGTERM)}
                try:
                    if process is not None:
                        try:
                            result['leader_reaped_after_cleanup'] = kill_group(process)
                        except (OSError, subprocess.SubprocessError):
                            result['leader_reaped_after_cleanup'] = False
                        result['child_exit_code'] = process.returncode
                    if local_t3 is not None:
                        result['container_cleanup'] = local_t3.cleanup()
                        result['local_observations'] = local_t3.observations
                finally:
                    for signum, handler in old.items():
                        signal.signal(signum, handler)
    except GuardInterrupted as exc:
        result.update(status='stopped' if process else 'refused', reason='interrupted', exit_code=128 + exc.signum)
    except (GuardError, EngineError) as exc:
        result.update(status='stopped' if process else 'refused', reason=str(exc), exit_code=125 if process else 75)
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError):
        result.update(status='stopped' if process else 'refused', reason='guard_unavailable', exit_code=125 if process else 75)
    result['wall_seconds'] = round(time.monotonic() - started, 3)
    if result.get('leader_reaped_after_cleanup') is False:
        result.update(status='stopped', reason='cleanup_incomplete', exit_code=125)
    if result.get('container_cleanup', {}).get('status') == 'unconfirmed':
        result.update(status='stopped', reason='container_cleanup_unconfirmed', exit_code=125)
    return result


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments == ['--local-t3']:
        return local_t3_main()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout-seconds', type=float, required=True)
    parser.add_argument('--memory-mib', type=int, default=1024, help='Per-process address space; may only lower the 1024 MiB cap')
    parser.add_argument('--rss-mib', type=int, default=1024, help='Sampled aggregate process-group RSS; may only lower the 1024 MiB cap')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args(arguments)
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('a command is required after --')
    if not math.isfinite(args.timeout_seconds) or not 0 < args.timeout_seconds <= 600:
        parser.error('--timeout-seconds must be finite and in (0, 600]')
    if not 0 < args.memory_mib <= 1024 or not 0 < args.rss_mib <= 1024:
        parser.error('memory limits must be in 1..1024 MiB')
    result = run_job(command, args.timeout_seconds, args.memory_mib * MIB, args.rss_mib * MIB)
    line = json.dumps(result, sort_keys=True) + '\n'
    # No argv, environment, child output, raw probe output or exception messages.
    sys.stderr.write(line)
    try:
        SUMMARY_LOG.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(SUMMARY_LOG, os.O_CREAT | os.O_APPEND | os.O_WRONLY | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'a') as log:
            log.write(line)
    except OSError:
        sys.stderr.write('resource_guard: summary_file_unavailable\n')
        return result['exit_code'] or 125
    return result['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
