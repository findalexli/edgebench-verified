#!/usr/bin/env python3
"""Bounded, ownership-scoped E2B transport; importing this module does no cloud work.

Use one shared state_dir for every coordinator process. reserve() durably counts
capacity before create_reserved() makes exactly one create request. An uncertain
request must be reconciled, never retried as a new creation. SDKProvider takes a
credential explicitly (or from one named environment variable); it never sends
that credential or the local environment to a sandbox. Jobs remain responsible
for their resource controls, network policy, evidence semantics and approval.

API: manager.reserve(owner, external_leases=...) -> reservation token;
manager.create_reserved(token)/recover_create(token) -> Worker;
worker.upload(job_id, files, expected_sha256, max_bytes=...);
worker.run(job_id, argv, timeout_seconds=..., export_margin_seconds=60);
worker.download(job_id, allowlist, destination, max_bytes=...);
worker.renew(seconds, checkpoint); worker.close(reason, allow_uncertain_job=False).
Only run() executes a caller-supplied command. No CLI or automatic creation exists.

Managers and SDK providers default to profile='small'. New reservations pin the
named profile, template and CPU/RAM allocation; reconnecting managers use that
saved contract. Legacy records without a profile retain the original small
contract. Large-profile deployment must wait for old small-only coordinators to
finish; this module does not launch or coordinate that operational transition.
"""
from __future__ import annotations
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from types import MappingProxyType
import fcntl
import hashlib
import io
import json
import math
import os
import re
import shlex
import stat
import uuid

from cloud_policy import provider_creation_gate

TEMPLATE_ID = 'l9vwx8ash6vvnhj9dnx7'
CPU_COUNT, MEMORY_MB, INITIAL_TTL_SECONDS = 2, 4096, 1800
MAX_CONFIGURED_WORKERS = 50
MAX_TRANSFER_BYTES = 256 * 1024 * 1024
MAX_FILE_COUNT = 256
REMOTE_ROOT = '/tmp/edgebenchverified-jobs'
TERMINAL = {'closed', 'cancelled_before_create'}
ENVIRONMENT = {'EDGEBENCH_EXECUTION_CONTEXT': 'e2b', 'OMP_NUM_THREADS': '1',
               'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1', 'NUMEXPR_NUM_THREADS': '1'}


class WorkerError(RuntimeError):
    """Deliberately compact; provider exception messages may contain credentials."""


class NotFound(WorkerError):
    pass


class OutcomeUnknown(WorkerError):
    pass


class CapacityUnavailable(WorkerError):
    """Known healthy inventory fills the configured worker capacity."""


@dataclass(frozen=True)
class ResourceProfile:
    name: str
    template_id: str
    cpu_count: int
    memory_mb: int


RESOURCE_PROFILES = MappingProxyType({
    'small': ResourceProfile('small', TEMPLATE_ID, CPU_COUNT, MEMORY_MB),
    # Build/resource provenance: audit/cloud/large-template-build.json.
    'large': ResourceProfile('large', 'dqr9oryio6litwrml3gd', 8, 8192),
})


def resource_profile(name):
    if type(name) is not str or name not in RESOURCE_PROFILES:
        raise ValueError('Resource profile must be small or large')
    return RESOURCE_PROFILES[name]


@dataclass(frozen=True)
class ExternalLease:
    owner: str
    sandbox_id: str
    status: str = 'running'


def utcnow():
    return datetime.now(timezone.utc)


def timestamp(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if value.tzinfo is None:
        raise WorkerError('Provider timestamp has no timezone')
    return value.astimezone(timezone.utc)


def digest(data):
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def relative_path(value):
    if not isinstance(value, str) or not value or len(value) > 512:
        raise ValueError('A nonempty relative path of at most 512 characters is required')
    path = PurePosixPath(value)
    if path.is_absolute() or any(p in ('', '.', '..') for p in value.split('/')) or '\\' in value or ':' in value or '\x00' in value:
        raise ValueError('Unsafe relative path')
    return str(path)


def job_name(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}', value):
        raise ValueError('Invalid job identifier')
    return value


def transfer_limit(value):
    if type(value) is not int or not 1 <= value <= MAX_TRANSFER_BYTES:
        raise ValueError('Transfer limit must be between 1 and 256 MiB')


class SDKProvider:
    """E2B SDK boundary, injectable in tests. It makes no request at construction."""
    def __init__(self, api_key=None, *, api_key_env='E2B_API_KEY', profile='small'):
        self.profile = resource_profile(profile).name
        self._key = api_key if api_key is not None else os.environ.get(api_key_env)
        if not self._key:
            raise ValueError('Missing explicitly named E2B credential')
        from e2b import Sandbox, SandboxNotFoundException
        from e2b.sandbox.sandbox_api import SandboxQuery
        from e2b.sandbox.commands.command_handle import CommandExitException
        self._sandbox, self._not_found = Sandbox, SandboxNotFoundException
        self._query, self._command_exit = SandboxQuery, CommandExitException
        self._connections = {}

    @staticmethod
    def _public(info):
        return {'sandbox_id': info.sandbox_id, 'metadata': dict(info.metadata or {}),
                'cpu_count': info.cpu_count, 'memory_mb': info.memory_mb,
                'template_id': info.template_id, 'state': str(info.state),
                'started_at': info.started_at.isoformat(), 'end_at': info.end_at.isoformat()}

    @staticmethod
    def inspection_diagnostic(exc):
        """Only bounded class and numeric attributes; never inspect error text."""
        cls = type(exc).__name__
        cls = cls if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,79}', cls) else 'ExceptionClassUnavailable'
        try: number = getattr(exc, 'errno', None)
        except Exception: number = None
        try: status = getattr(exc, 'status_code', None)
        except Exception: status = None
        if type(status) is not int or not 100 <= status <= 599:
            try: status = getattr(getattr(exc, 'response', None), 'status_code', None)
            except Exception: status = None
        return {'provider_inspection_error_class': cls,
                'provider_inspection_error_errno': number if type(number) is int and 0 <= number <= 4095 else None,
                'provider_inspection_http_status': status if type(status) is int and 100 <= status <= 599 else None}

    def info(self, sandbox_id):
        try:
            return self._public(self._sandbox.get_info(sandbox_id, api_key=self._key, request_timeout=20))
        except self._not_found:
            raise NotFound('Sandbox absent') from None
        except Exception as exc:
            error = OutcomeUnknown('Provider inspection failed')
            try: error.provider_inspection_diagnostic = self.inspection_diagnostic(exc)
            except Exception: pass
            raise error from None

    def list_owned(self, owner):
        try:
            pager = self._sandbox.list(query=self._query(metadata={'owner': owner}), limit=10,
                                      api_key=self._key, request_timeout=20)
            result = []
            while pager.has_next:
                result.extend(self._public(x) for x in pager.next_items())
                if len(result) > MAX_CONFIGURED_WORKERS:
                    raise WorkerError('Owned inventory exceeds the reviewed worker maximum')
            return result
        except WorkerError:
            raise
        except Exception as exc:
            error = OutcomeUnknown('Owned inventory query failed')
            try: error.provider_inspection_diagnostic = self.inspection_diagnostic(exc)
            except Exception: pass
            raise error from None

    def create(self, metadata, *, profile=None):
        selected = resource_profile(self.profile if profile is None else profile)
        try:
            sb = self._sandbox.create(template=selected.template_id, timeout=INITIAL_TTL_SECONDS,
                                      metadata=metadata, envs={}, secure=True,
                                      api_key=self._key, request_timeout=30)
            self._connections[sb.sandbox_id] = sb
            return sb.sandbox_id
        except Exception:
            raise OutcomeUnknown('Creation outcome unknown; reconcile reservation') from None

    def _connect(self, sandbox_id):
        if sandbox_id not in self._connections:
            self._connections[sandbox_id] = self._sandbox.connect(sandbox_id, api_key=self._key, request_timeout=20)
        return self._connections[sandbox_id]

    def renew(self, sandbox_id, seconds):
        self._sandbox.set_timeout(sandbox_id, timeout=seconds, api_key=self._key, request_timeout=20)

    def kill(self, sandbox_id):
        self._sandbox.kill(sandbox_id, api_key=self._key, request_timeout=20)

    def write(self, sandbox_id, path, source):
        try:
            self._connect(sandbox_id).files.write(path, source, user='root', request_timeout=30)
        except Exception:
            raise OutcomeUnknown('Upload outcome unknown; job remains in staging') from None

    def stat(self, sandbox_id, path):
        item = self._connect(sandbox_id).files.get_info(path, user='root', request_timeout=20)
        return {'size': item.size, 'type': item.type.value if item.type else None,
                'symlink_target': item.symlink_target}

    def read_chunks(self, sandbox_id, path):
        # E2B's current public read(format='stream') eagerly buffers HTTP .get().
        # Isolate this version-sensitive SDK transport detail to retain a true
        # bounded stream, including when a remote file changes after stat().
        client = getattr(self._connect(sandbox_id).files, '_envd_api', None)
        if client is None or not hasattr(client, 'stream'):
            raise WorkerError('Installed SDK does not expose bounded file streaming')
        with client.stream('GET', '/files', params={'path': path, 'username': 'root'}, timeout=20) as response:
            if response.status_code != 200:
                raise WorkerError('Export read failed')
            yield from response.iter_bytes(chunk_size=65536)

    def run(self, sandbox_id, command, timeout_seconds):
        try:
            result = self._connect(sandbox_id).commands.run(command, cwd='/tmp', user='root',
                envs=dict(ENVIRONMENT), timeout=timeout_seconds, request_timeout=timeout_seconds + 10)
        except self._command_exit as result:
            return {'exit_code': result.exit_code, 'pid': getattr(result, 'pid', None)}
        return {'exit_code': result.exit_code, 'pid': getattr(result, 'pid', None)}


class CloudWorkerManager:
    def __init__(self, provider, state_dir, owners, *, max_workers=1, second_worker_reason='', clock=utcnow,
                 profile='small'):
        self.profile = resource_profile(profile).name
        if type(max_workers) is not int or not 1 <= max_workers <= MAX_CONFIGURED_WORKERS:
            raise ValueError('Configured worker capacity must be an integer from 1 to 50')
        if max_workers > 1 and (not isinstance(second_worker_reason, str) or not second_worker_reason.strip()):
            raise ValueError('Multiple workers require a resource/cost assessment')
        if not owners or len(set(owners)) != len(owners) or any(not isinstance(o, str) or not o.strip() for o in owners):
            raise ValueError('Explicit unique audit owners are required')
        self.provider, self.owners, self.max_workers = provider, tuple(owners), max_workers
        self.clock, self.state_dir = clock, Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.state_dir / 'cloud-workers.json'
        self.assessment = second_worker_reason

    @contextmanager
    def _locked(self):
        with (self.state_dir / '.cloud-workers.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            data = json.loads(self.path.read_text()) if self.path.exists() else {'schema_version': 1, 'reservations': {}}
            yield data

    def _save(self, data):
        temporary = self.path.with_suffix('.tmp')
        with temporary.open('w') as output:
            json.dump(data, output, indent=2); output.write('\n'); output.flush(); os.fsync(output.fileno())
        temporary.replace(self.path)
        directory = os.open(self.state_dir, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)

    def _verify(self, info, owner, *, token=None, resources=True, running=True, profile=None):
        if owner not in self.owners or info.get('metadata', {}).get('owner') != owner:
            raise WorkerError('Provider ownership mismatch')
        if token is not None and info['metadata'].get('creation_token') != token:
            raise WorkerError('Provider creation token mismatch')
        if resources:
            expected = resource_profile(self.profile) if profile is None else profile
            if not self._matches_profile(info, expected):
                raise WorkerError('Worker differs from its reserved resource profile')
        if running and (info.get('state') != 'running' or timestamp(info['end_at']) <= self.clock()):
            raise WorkerError('Worker is not confirmed running before its provider deadline')
        return info

    @staticmethod
    def _matches_profile(info, profile):
        return (type(info.get('cpu_count')) is int and info['cpu_count'] == profile.cpu_count
                and type(info.get('memory_mb')) is int and info['memory_mb'] == profile.memory_mb
                and info.get('template_id') == profile.template_id)

    @classmethod
    def _bounded_allocation(cls, info):
        if not any(cls._matches_profile(info, profile) for profile in RESOURCE_PROFILES.values()):
            raise WorkerError('Existing audit worker does not match a reviewed resource profile')

    @staticmethod
    def _record_profile(record):
        # Schema-1 records originally pinned only the small template. Interpret
        # those records without rewriting them or inheriting a new default.
        legacy = 'resource_profile' not in record
        try:
            profile = resource_profile(record.get('resource_profile', 'small'))
        except ValueError:
            raise WorkerError('Reservation has an unknown resource profile') from None
        if record.get('template_id') != profile.template_id:
            raise WorkerError('Reservation template does not match its resource profile')
        for field in ('cpu_count', 'memory_mb'):
            if legacy and field not in record:
                continue
            if type(record.get(field)) is not int or record[field] != getattr(profile, field):
                raise WorkerError('Reservation allocation does not match its resource profile')
        return profile

    def _inventory(self, data, external_leases):
        actual = {}
        for owner in self.owners:
            for info in self.provider.list_owned(owner):
                self._verify(info, owner, resources=False, running=False)
                self._bounded_allocation(info)
                actual[info['sandbox_id']] = info
        for external in external_leases:
            if external.owner not in self.owners:
                raise WorkerError('External lease owner is outside this audit')
            try:
                info = self.provider.info(external.sandbox_id)
            except NotFound:
                continue
            self._verify(info, external.owner, resources=False, running=False)
            self._bounded_allocation(info)
            if info['sandbox_id'] != external.sandbox_id:
                raise WorkerError('External lease identifier mismatch')
            actual[info['sandbox_id']] = info
        count = len(actual)
        for token, record in data['reservations'].items():
            if record['status'] in TERMINAL:
                continue
            profile = self._record_profile(record)
            sid = record.get('sandbox_id')
            matching = [i for i in actual.values() if i['sandbox_id'] == sid
                        or i['metadata'].get('creation_token') == token]
            if matching:
                for info in matching:
                    self._verify(info, record['owner'], token=token, running=False, profile=profile)
                continue
            # Absent listings are not enough to free an uncertain reservation.
            count += 1
        return count

    def reserve(self, owner, *, external_leases=()):
        if owner not in self.owners:
            raise ValueError('Owner is outside this audit')
        with self._locked() as data:
            if any(r['status'] in {'create_outcome_unknown', 'created_unverified'} for r in data['reservations'].values()):
                raise WorkerError('Reconcile pending creation before reserving another worker')
            if self._inventory(data, external_leases) >= self.max_workers:
                raise CapacityUnavailable('Audit worker capacity is reserved or occupied')
            token = str(uuid.uuid4())
            profile = resource_profile(self.profile)
            data['reservations'][token] = {'owner': owner, 'creation_token': token, 'status': 'reserved',
                'requested_at': self.clock().isoformat(), 'resource_profile': profile.name,
                'template_id': profile.template_id, 'cpu_count': profile.cpu_count, 'memory_mb': profile.memory_mb,
                'requested_ttl_seconds': INITIAL_TTL_SECONDS, 'second_worker_assessment': self.assessment,
                'external_leases': [vars(e) for e in external_leases], 'jobs': {}}
            self._save(data)
        return token

    def cancel_reservation(self, token):
        with self._locked() as data:
            record = data['reservations'][token]
            if record['status'] != 'reserved':
                raise WorkerError('Only a reservation with no create request can be cancelled')
            record['status'] = 'cancelled_before_create'; self._save(data)

    def create_reserved(self, token):
        with self._locked() as data:
            record = data['reservations'][token]
            if record['status'] != 'reserved':
                raise WorkerError('Creation was already attempted; recover the same token')
            if any(k != token and r['status'] in {'create_outcome_unknown', 'created_unverified'} for k, r in data['reservations'].items()):
                raise WorkerError('Reconcile another pending creation before creating this worker')
            if self._inventory(data, [ExternalLease(**e) for e in record['external_leases']]) > self.max_workers:
                raise CapacityUnavailable('Audit capacity changed before creation')
            profile = self._record_profile(record)
            record['status'] = 'create_outcome_unknown'; self._save(data)
            try:
                with provider_creation_gate(self.state_dir):
                    sid = self.provider.create({'owner': record['owner'], 'creation_token': token,
                                                'project': 'edgebenchverified'}, profile=profile.name)
            except BaseException:
                raise OutcomeUnknown('Creation outcome unknown; reservation remains occupied') from None
            record['sandbox_id'] = sid; record['status'] = 'created_unverified'; self._save(data)
            try:
                info = self.provider.info(sid)
                self._verify(info, record['owner'], token=token, profile=profile)
                if info['sandbox_id'] != sid:
                    raise WorkerError('Provider sandbox identifier mismatch')
            except Exception:
                raise WorkerError('Created worker not verified; reconcile or close known owned worker') from None
            record['status'] = 'ready'; record['provider_info'] = info; self._save(data)
        return Worker(self, token)

    def recover_create(self, token):
        with self._locked() as data:
            record = data['reservations'][token]
            if record['status'] not in {'create_outcome_unknown', 'created_unverified'}:
                raise WorkerError('Reservation is not an uncertain creation')
            profile = self._record_profile(record)
            matches = []
            for info in self.provider.list_owned(record['owner']):
                self._verify(info, record['owner'], resources=False, running=False)
                if info['metadata'].get('creation_token') == token:
                    matches.append(info)
            if len(matches) != 1:
                raise OutcomeUnknown('Zero or ambiguous creation matches; reservation remains occupied')
            info = matches[0]
            if record.get('sandbox_id') and info['sandbox_id'] != record['sandbox_id']:
                raise WorkerError('Recovery sandbox identifier mismatch')
            record['sandbox_id'] = info['sandbox_id']; record['status'] = 'created_unverified'; self._save(data)
            self._verify(info, record['owner'], token=token, profile=profile)
            record['status'] = 'ready'; record['provider_info'] = info; self._save(data)
        return Worker(self, token)

    def inspect_reservation(self, token):
        with self._locked() as data:
            return json.loads(json.dumps(data['reservations'][token]))

    def close_reservation(self, token, reason, *, allow_uncertain_job=False):
        return Worker(self, token).close(reason, allow_uncertain_job=allow_uncertain_job)

    def worker(self, token):
        """Reconnect to a persisted reservation without creating or resuming it."""
        worker = Worker(self, token)
        worker.info()
        return worker


class Worker:
    def __init__(self, manager, token):
        self.manager, self.token = manager, token

    @property
    def sandbox_id(self):
        return self.manager.inspect_reservation(self.token).get('sandbox_id')

    def job_root(self, job_id):
        return self._remote(job_id)

    def _info(self, record, *, resources=True, running=True):
        sid = record.get('sandbox_id')
        if not sid:
            raise WorkerError('No known sandbox for this reservation')
        info = self.manager.provider.info(sid)
        if info['sandbox_id'] != sid:
            raise WorkerError('Provider sandbox identifier mismatch')
        profile = self.manager._record_profile(record) if resources else None
        return self.manager._verify(info, record['owner'], token=self.token, resources=resources,
                                    running=running, profile=profile)

    def info(self):
        with self.manager._locked() as data:
            record = data['reservations'][self.token]
            if record['status'] != 'ready':
                raise WorkerError('Worker is not in a verified ready state')
            info = self._info(record)
            record['provider_info'] = info; self.manager._save(data)
            return info

    def _remote(self, job_id, path=None):
        base = f'{REMOTE_ROOT}/{self.token}/{job_name(job_id)}'
        return base + '/' + relative_path(path) if path is not None else base

    def _safe_remote_file(self, sid, path):
        parts = PurePosixPath(path).parts
        for index in range(2, len(parts) + 1):
            item = self.manager.provider.stat(sid, str(PurePosixPath(*parts[:index])))
            if item.get('symlink_target') is not None:
                raise WorkerError('Remote export path includes a symlink')
            expected = 'file' if index == len(parts) else 'dir'
            if item.get('type') != expected:
                raise WorkerError('Remote export path is not an ordinary file path')
        return item

    def upload(self, job_id, files, expected_sha256, *, max_bytes=32 * 1024 * 1024):
        job_name(job_id); transfer_limit(max_bytes)
        if len(files) > MAX_FILE_COUNT or set(files) != set(expected_sha256):
            raise ValueError('Input allowlist and immutable hash manifest must agree')
        payloads, total = {}, 0
        for name, source in files.items():
            relative_path(name)
            if isinstance(source, Path):
                # O_NONBLOCK avoids hanging on a FIFO before fstat rejects it.
                fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                with os.fdopen(fd, 'rb') as stream:
                    metadata = os.fstat(stream.fileno())
                    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > max_bytes - total:
                        raise ValueError('Input must be a bounded regular file')
                    payload = stream.read(max_bytes - total + 1)
                    if len(payload) != metadata.st_size:
                        raise ValueError('Input changed while reading')
            elif isinstance(source, bytes):
                payload = source
            else:
                raise ValueError('Inputs must be explicit bytes or Path objects')
            total += len(payload)
            if total > max_bytes or digest(payload) != expected_sha256[name]:
                raise ValueError('Input hash mismatch or input byte budget exceeded')
            payloads[name] = payload
        with self.manager._locked() as data:
            record = data['reservations'][self.token]
            if record['status'] != 'ready' or record.get('active_job'):
                raise WorkerError('Worker is unavailable for staging')
            info = self._info(record); existing = record['jobs'].get(job_id)
            if existing and existing['status'] != 'staging':
                raise WorkerError('Job identifier has already been used')
            job = record['jobs'].setdefault(job_id, {'status': 'staging', 'inputs': {}})
            if job['inputs'] and job['inputs'] != expected_sha256:
                raise WorkerError('Cannot change an existing job input manifest')
            job['inputs'] = dict(expected_sha256); self.manager._save(data)
            for name, payload in payloads.items():
                remote = self._remote(job_id, name)
                self.manager.provider.write(info['sandbox_id'], remote, io.BytesIO(payload))
                metadata = self._safe_remote_file(info['sandbox_id'], remote)
                if metadata['size'] != len(payload):
                    raise WorkerError('Uploaded file size differs from its immutable input')
                observed, h = 0, hashlib.sha256()
                for chunk in self.manager.provider.read_chunks(info['sandbox_id'], remote):
                    observed += len(chunk)
                    if observed > len(payload):
                        raise WorkerError('Uploaded file grew beyond its immutable input')
                    h.update(chunk)
                if observed != len(payload) or 'sha256:' + h.hexdigest() != expected_sha256[name]:
                    raise WorkerError('Remote uploaded input hash mismatch')
            job.update({'status': 'prepared', 'input_bytes': total, 'remote_input_hashes_verified': True}); self.manager._save(data)
        return {'job_id': job_id, 'file_count': len(files), 'input_bytes': total,
                'input_sha256': dict(expected_sha256), 'remote_input_hashes_verified': True}

    def run(self, job_id, argv, *, timeout_seconds, export_margin_seconds=60):
        job_name(job_id)
        if not isinstance(argv, (list, tuple)) or not argv or any(not isinstance(a, str) or '\x00' in a for a in argv):
            raise ValueError('An explicit nonempty command argv is required')
        if type(timeout_seconds) is not int or timeout_seconds < 6 or type(export_margin_seconds) is not int or export_margin_seconds < 30:
            raise ValueError('Command requires >=6 seconds and >=30 seconds of export margin')
        with self.manager._locked() as data:
            record = data['reservations'][self.token]
            if record['status'] != 'ready' or record.get('active_job'):
                raise WorkerError('Worker has an active or uncertain command')
            info = self._info(record); remaining = math.floor((timestamp(info['end_at']) - self.manager.clock()).total_seconds())
            if timeout_seconds + export_margin_seconds > remaining:
                raise WorkerError('Command exceeds actual provider deadline minus export margin')
            job = record['jobs'].get(job_id)
            if not job or job['status'] != 'prepared':
                raise WorkerError('Stage this new job and its input manifest before running')
            job.update({'status': 'command_outcome_unknown', 'command_sha256': digest(json.dumps(list(argv)).encode()),
                        'started_at': self.manager.clock().isoformat(), 'timeout_seconds': timeout_seconds,
                        'provider_end_at': info['end_at'], 'export_margin_seconds': export_margin_seconds})
            record['active_job'] = job_id; self.manager._save(data)
            sid = info['sandbox_id']
        folder = shlex.quote(self._remote(job_id))
        # The trusted wrapper reaps the launched process group on normal exit as
        # well as timeout, so a background child cannot overlap the next phase.
        wrapper = ("import os,signal,subprocess,sys\n"
            "out=open('command.stdout','wb'); err=open('command.stderr','wb')\n"
            "p=subprocess.Popen(sys.argv[2:],stdout=out,stderr=err,start_new_session=True)\n"
            "try:\n"
            " try: code=p.wait(timeout=int(sys.argv[1]))\n"
            " except subprocess.TimeoutExpired: code=124\n"
            "finally:\n"
            " try: os.killpg(p.pid,signal.SIGKILL)\n"
            " except ProcessLookupError: pass\n"
            " p.wait(timeout=5); out.close(); err.close()\n"
            "sys.exit(code)\n")
        command = f'mkdir -p {folder} && cd {folder} && ' + shlex.join(
            ['python3', '-c', wrapper, str(timeout_seconds - 5), *argv])
        try:
            outcome = self.manager.provider.run(sid, command, timeout_seconds)
            if type(outcome.get('exit_code')) is not int:
                raise WorkerError('Missing terminal command exit status')
        except BaseException:
            raise OutcomeUnknown('Command outcome unknown; do not retry this or another job') from None
        with self.manager._locked() as data:
            record = data['reservations'][self.token]; job = record['jobs'][job_id]
            job.update({'status': 'command_completed', 'exit_code': outcome['exit_code'],
                        'finished_at': self.manager.clock().isoformat()})
            record.pop('active_job', None); self.manager._save(data)
        return {'job_id': job_id, 'status': 'command_completed', 'exit_code': outcome['exit_code'],
                'stdout_remote': self._remote(job_id, 'command.stdout'), 'stderr_remote': self._remote(job_id, 'command.stderr')}

    def download(self, job_id, allowlist, destination, *, max_bytes=32 * 1024 * 1024,
                 allow_incomplete=False):
        """Export exact regular paths, with receipts checkpointed after each file.

        Normal exports require a completed command. Explicit incomplete recovery
        is supported, but neither mode is an atomic remote snapshot: stat and
        streaming are separate operations. This is transport for owned trusted
        jobs, not an isolation boundary against adversarial root processes.
        """
        job_name(job_id); transfer_limit(max_bytes)
        names = [relative_path(p) for p in allowlist]
        if not names or len(names) != len(set(names)) or len(names) > MAX_FILE_COUNT:
            raise ValueError('Export allowlist must have nonempty unique bounded entries')
        batch_id = str(uuid.uuid4())
        with self.manager._locked() as data:
            record = data['reservations'][self.token]; job = record['jobs'].get(job_id)
            allowed = {'command_completed'} | ({'prepared', 'command_outcome_unknown'} if allow_incomplete else set())
            if not job or job['status'] not in allowed:
                raise WorkerError('Export requires a recorded terminal job or explicit incomplete recovery')
            if record['status'] != 'ready':
                raise WorkerError('Worker is unavailable for export')
            info = self._info(record)
            batch = {'batch_id': batch_id, 'job_id': job_id, 'status': 'exporting',
                     'observed_at': self.manager.clock().isoformat(), 'files': [], 'bytes': 0,
                     'allowlist': names, 'max_bytes': max_bytes, 'incomplete_recovery': allow_incomplete,
                     'containment_limit': 'Path checks and streamed reads are not an atomic remote snapshot.'}
            record.setdefault('exports', []).append(batch); self.manager._save(data)
        def checkpoint(status, error_type=None):
            with self.manager._locked() as data:
                saved = next(x for x in data['reservations'][self.token]['exports'] if x['batch_id'] == batch_id)
                saved.update({'status': status, 'files': list(receipts), 'bytes': total})
                if error_type is not None: saved['error_type'] = error_type
                self.manager._save(data)
        sid = info['sandbox_id']; base = Path(destination).resolve()
        receipts, total = [], 0
        try:
            base.mkdir(parents=True, exist_ok=True)
            for name in names:
                remote = self._remote(job_id, name); metadata = self._safe_remote_file(sid, remote)
                if type(metadata.get('size')) is not int or metadata['size'] < 0 or total + metadata['size'] > max_bytes:
                    raise WorkerError('Export byte budget exceeded before download')
                target = base / name
                if any(p.is_symlink() for p in [target, *target.parents] if p == base or base in p.parents):
                    raise WorkerError('Local export destination contains a symlink')
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = target.with_name(target.name + '.partial-' + uuid.uuid4().hex)
                h, size = hashlib.sha256(), 0
                try:
                    with temporary.open('xb') as output:
                        os.chmod(temporary, 0o600)
                        for chunk in self.manager.provider.read_chunks(sid, remote):
                            size += len(chunk)
                            if total + size > max_bytes or size > metadata['size']:
                                raise WorkerError('Export changed or exceeded byte budget during streaming')
                            h.update(chunk); output.write(chunk)
                    if size != metadata['size']:
                        raise WorkerError('Export size changed during streaming')
                    temporary.replace(target)
                finally:
                    temporary.unlink(missing_ok=True)
                total += size; receipts.append({'path': name, 'size': size, 'sha256': 'sha256:' + h.hexdigest()})
                checkpoint('exporting')
            checkpoint('completed')
        except BaseException as exc:
            checkpoint('failed_partial_exports_retained', type(exc).__name__)
            if isinstance(exc, (KeyboardInterrupt, SystemExit)): raise
            raise WorkerError('Export failed; checkpointed receipts and failure type retained') from None
        return {'job_id': job_id, 'batch_id': batch_id, 'file_count': len(receipts),
                'export_bytes': total, 'files': receipts, 'incomplete_recovery': allow_incomplete}

    def renew(self, seconds, checkpoint):
        if type(seconds) is not int or not 1 <= seconds <= INITIAL_TTL_SECONDS or not isinstance(checkpoint, str) or not checkpoint.strip():
            raise ValueError('Renewal needs useful progress and a TTL of 1–1800 seconds')
        with self.manager._locked() as data:
            record = data['reservations'][self.token]
            if record['status'] != 'ready' or record.get('active_job'):
                raise WorkerError('Renew between completed phases only')
            info = self._info(record)
            record['renewal_intent'] = {'seconds': seconds, 'checkpoint': checkpoint, 'observed_at': self.manager.clock().isoformat()}; self.manager._save(data)
            try:
                self.manager.provider.renew(info['sandbox_id'], seconds)
                updated = self._info(record)
            except Exception:
                raise OutcomeUnknown('Renewal outcome unknown; inspect actual provider deadline') from None
            record['provider_info'] = updated; record.setdefault('renewals', []).append(record.pop('renewal_intent')); self.manager._save(data)
        return updated

    def close(self, reason, *, allow_uncertain_job=False):
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError('An explicit cleanup reason is required')
        with self.manager._locked() as data:
            record = data['reservations'][self.token]
            if record['status'] in TERMINAL:
                return {'status': record['status'], 'absence_confirmed': record['status'] == 'closed'}
            if record.get('active_job') and not allow_uncertain_job:
                raise WorkerError('Explicitly acknowledge termination of the uncertain job')
            sid = record.get('sandbox_id')
            if not sid:
                raise OutcomeUnknown('Recover uncertain creation identity before cleanup')
            try:
                self._info(record, resources=False, running=False)
            except NotFound:
                record['status'] = 'closed'; record['closed_at'] = self.manager.clock().isoformat(); self.manager._save(data)
                return {'sandbox_id': sid, 'status': 'closed', 'absence_confirmed': True}
            record.update({'status': 'termination_outcome_unknown', 'cleanup_reason': reason}); self.manager._save(data)
            try:
                self.manager.provider.kill(sid)
                self.manager.provider.info(sid)
            except NotFound:
                record['status'] = 'closed'; record['closed_at'] = self.manager.clock().isoformat(); self.manager._save(data)
                return {'sandbox_id': sid, 'status': 'closed', 'absence_confirmed': True}
            except Exception:
                raise OutcomeUnknown('Termination outcome unknown; capacity remains occupied') from None
            raise OutcomeUnknown('Provider absence unconfirmed; capacity remains occupied')
