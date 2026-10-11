"""One maintained new-experiment route; existing cloud tools remain unchanged.

Root imports this in a bounded dedicated launcher, supplies its pinned grants,
the supported SDKProvider object LAST, and uses the existing shared state_dir.
This module has no automatic CLI, credential lookup or provider construction.
"""
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import resource
import re
import uuid
import stat
import threading
import time

from job_validator import OPERATION, HELD_TASKS, canonical, sha, validate, validate_result, need, name

COLLECTION_STATUS = 'experiment_collection_completed_pending_review'

# These are entered phases. Method-return booleans are separate evidence.
STARTUP_PHASES = frozenset({'staging','audit_time','register','lifecycle_time',
    'reserve','claim','create','upload','mark_running','run','collect',
    'validate_result','completed','cleanup_worker','cleanup_reservation',
    'finish','settle'})
STARTUP_FIELDS = ('job_id','attempt_id','root_grant_sha256','phase','failure_phase',
    'error_class','error_errno','registration_returned','reserve_returned',
    'claim_returned','create_returned','reservation_cancel_returned',
    'worker_reservation','worker_termination_confirmed','exports_verified',
    'scientific_identity_verified','cleanup_error_class','cleanup_error_errno',
    'finalization_error_class','finalization_error_errno','finalization_phase',
    'provider_inspection_error_class','provider_inspection_error_errno','provider_inspection_http_status')

def safe_exception(exc):
    cls = type(exc).__name__
    cls = cls if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,79}',cls) else 'ExceptionClassUnavailable'
    try: number = getattr(exc,'errno',None)
    except Exception: number = None
    result = {'error_class':cls,'error_errno':number if type(number) is int and 0 <= number <= 4095 else None}
    try: detail = getattr(exc,'provider_inspection_diagnostic',None)
    except Exception: detail = None
    if type(detail) is dict:
        cause = detail.get('provider_inspection_error_class')
        number = detail.get('provider_inspection_error_errno')
        status = detail.get('provider_inspection_http_status')
        result.update(provider_inspection_error_class=cause if type(cause) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,79}',cause) else None,
            provider_inspection_error_errno=number if type(number) is int and 0 <= number <= 4095 else None,
            provider_inspection_http_status=status if type(status) is int and 100 <= status <= 599 else None)
    return result

def atomic_startup_receipt(state_dir, diagnostic_id, receipt):
    """Bounded immutable receipt plus atomic live view; no error text.

    Existing ancestors are root's storage/admission boundary. Only the state
    directory and our child are opened here, without following symlinks.
    The receipt is an observation prefix, not proof of a provider transaction.
    """
    need(re.fullmatch('[0-9a-f]{32}',diagnostic_id) is not None,'diagnostic identity')
    need(receipt.get('phase') in STARTUP_PHASES,'fixed entered phase')
    projection = {key:receipt[key] for key in STARTUP_FIELDS if key in receipt}
    projection.update(schema='deterministic-experiment-startup-receipt-v1',
        diagnostic_id=diagnostic_id,recorded_at_utc=datetime.now(timezone.utc).isoformat(),
        scope='entered_phase_and_method_returns_only',certification_effect='none')
    body = canonical(projection)
    need(len(body) <= 16384,'startup receipt bytes')
    parent = os.open(state_dir,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    snapshot = diagnostic_id+'.'+uuid.uuid4().hex+'.json'
    directory = None; temporary = snapshot+'.tmp'
    try:
        try: os.mkdir('startup-receipts',0o700,dir_fd=parent)
        except FileExistsError: pass
        directory = os.open('startup-receipts',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=parent)
        fd = os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=directory)
        with os.fdopen(fd,'wb') as stream:
            stream.write(body); stream.flush(); os.fsync(stream.fileno())
        # Exclusive immutable name retains these bytes after the live view moves.
        os.link(temporary,snapshot,src_dir_fd=directory,dst_dir_fd=directory,follow_symlinks=False)
        os.replace(temporary,diagnostic_id+'.json',src_dir_fd=directory,dst_dir_fd=directory)
        os.fsync(directory)
    finally:
        if directory is not None:
            try: os.unlink(temporary,dir_fd=directory)
            except FileNotFoundError: pass
            os.close(directory)
        os.close(parent)
    return {'path':'startup-receipts/'+snapshot,'bytes':len(body),'sha256':sha(body)}


def bounded_read(root, relative, limit):
    name(relative)
    root = root.resolve()
    path = root / relative
    need(path.is_relative_to(root) and not any(x.is_symlink() for x in (path,*path.parents)), 'source path/symlink')
    fd = os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        s = os.fstat(stream.fileno())
        need(stat.S_ISREG(s.st_mode) and s.st_size <= limit, 'regular source cap')
        data = stream.read(limit+1)
    need(len(data) == s.st_size, 'source changed while reading')
    return data

def payload_for(root, job, grant_bytes, grant_sha):
    need(sha(grant_bytes) == grant_sha and len(grant_bytes) <= 65536, 'root grant before source read')
    grant = json.loads(grant_bytes)
    need(grant.get('schema') == 'deterministic-experiment-grant-v1' and grant.get('issued_by') == '/root' and grant.get('authorization_status') == 'ROOT_OPERATIONALLY_GRANTED', 'operational grant before source read')
    need(grant.get('job_sha256') == sha(canonical(job)) and job.get('operation_id') == OPERATION and job.get('task_id') not in HELD_TASKS, 'admitted job before source read')
    need(type(grant.get('runtime_refs')) is list and 3 <= len(grant['runtime_refs']) <= 8, 'runtime refs before source read')
    for row in grant['runtime_refs']:
        body = bounded_read(root,row['path'],1048576)
        need(len(body) == row['bytes'] and sha(body) == row['sha256'], 'maintained runtime source binding')
    need(type(job.get('inputs')) is list and 3 <= len(job['inputs']) <= 32, 'input count before source read')
    total = 0; payload = {}
    for row in job['inputs']:
        name(row['path']); name(row['target'])
        # Bound before reading; all local inputs are explicit repository paths.
        need(type(row.get('bytes')) is int and 0 <= row['bytes'] <= 1048576 and total + row['bytes'] <= 16777216, 'input admission bytes')
        body = bounded_read(root,row['path'],row['bytes'])
        payload[row['target']] = body; total += len(body)
    validate(job,grant_bytes,grant_sha,payload)
    return payload

def experiment_store(BaseStore, path, ceiling, admitted):
    """Inherited accounting; root may explicitly reuse only an unattempted pending ID."""
    class Store(BaseStore):
        def register(self, job):
            need(job['operation_id'] == OPERATION and admitted.get(job['job_id'],{}).get('job_sha256') == sha(canonical(job)), 'only admitted new experiments')
            # No attempt is retried. A hashed root grant may admit an unchanged
            # pending registration with no current or historical attempt.
            with self.transaction() as db:
                old = db.execute('SELECT state,attempt_id,manifest,manifest_sha FROM jobs WHERE job_id=?',(job['job_id'],)).fetchone()
                if old is not None:
                    need(admitted[job['job_id']].get('resume_registered_pending_without_attempt') is True,'explicit root pending-resume grant')
                    need(old['state'] == 'pending' and old['attempt_id'] is None,'unattempted pending registration only')
                    need(old['manifest_sha'] == admitted[job['job_id']]['job_sha256'] and sha(canonical(json.loads(old['manifest']))) == old['manifest_sha'],'unchanged pending manifest')
                    need(db.execute('SELECT attempt_id FROM attempts WHERE job_id=? LIMIT 1',(job['job_id'],)).fetchone() is None,'no historical attempt')
                    return old['manifest_sha']
            return super().register(job)

        def finish(self, job_id, attempt_id, state, result):
            if state != 'completed':
                return super().finish(job_id,attempt_id,state,result)
            grant = admitted.get(job_id,{})
            need(result.get('root_grant_sha256') == grant.get('grant_sha256') and result.get('scientific_identity_verified') is True and result.get('job_status') == COLLECTION_STATUS, 'grant collection proof')
            need(result.get('exports_verified') is True and result.get('worker_termination_confirmed') is True, 'completion exports and owned close')
            # Exact installed completed transaction, with only its operation/status
            # allowlist replaced by this grant-bound operation. Failure paths inherit.
            with self.transaction() as db:
                old = db.execute('SELECT state,attempt_id,manifest FROM jobs WHERE job_id=?',(job_id,)).fetchone()
                need(old is not None and old['attempt_id'] == attempt_id and old['state'] == 'running', 'valid completed transition')
                manifest = json.loads(old['manifest'])
                need(manifest['operation_id'] == OPERATION and sha(canonical(manifest)) == grant['job_sha256'], 'immutable registered experiment')
                db.execute('UPDATE jobs SET state=? WHERE job_id=?',(state,job_id))
                db.execute('UPDATE attempts SET state=?,result=? WHERE attempt_id=?',(state,canonical(result).decode(),attempt_id))
                self.event(db,job_id,attempt_id,state,result)
    return Store(path,ceiling_usd=ceiling)

class DeadlineProvider:
    """Retain SDKProvider identity; bound collection/close API request timeouts.

    This uses the same installed 2.19 SDK calls and streaming API as CloudWorker.
    It does not export the key or forward it to an owned worker.
    """
    def __init__(self, provider, NotFound, OutcomeUnknown, clock=time.monotonic):
        self.base,self.NotFound,self.OutcomeUnknown,self.clock = provider,NotFound,OutcomeUnknown,clock
        self.local = threading.local()
    def __getattr__(self,key): return getattr(self.base,key)
    @contextmanager
    def phase(self,seconds, *, deadline=None):
        self.local.deadline = self.clock()+seconds if deadline is None else deadline
        try: yield
        finally: self.local.deadline = None
    def remaining(self):
        end = getattr(self.local,'deadline',None)
        remaining = 20 if end is None else min(20,end-self.clock())
        if remaining <= 0: raise TimeoutError('phase_deadline')
        return remaining
    def info(self,sid):
        try:
            return self.base._public(self.base._sandbox.get_info(sid,api_key=self.base._key,request_timeout=self.remaining()))
        except self.base._not_found: raise self.NotFound('Sandbox absent') from None
        except Exception as exc:
            error = self.OutcomeUnknown('Bounded inspection failed')
            try: error.provider_inspection_diagnostic = self.base.inspection_diagnostic(exc)
            except Exception: pass
            raise error from None
    def kill(self,sid):
        return self.base._sandbox.kill(sid,api_key=self.base._key,request_timeout=self.remaining())
    def stat(self,sid,path):
        item = self.base._connect(sid).files.get_info(path,user='root',request_timeout=self.remaining())
        return {'size':item.size,'type':item.type.value if item.type else None,'symlink_target':item.symlink_target}
    def read_chunks(self,sid,path):
        client = getattr(self.base._connect(sid).files,'_envd_api',None)
        need(client is not None and hasattr(client,'stream'), 'installed bounded stream')
        with client.stream('GET','/files',params={'path':path,'username':'root'},timeout=self.remaining()) as response:
            need(response.status_code == 200, 'export HTTP status')
            for chunk in response.iter_bytes(chunk_size=65536):
                self.remaining(); yield chunk

def execute_one(job, grant_bytes, grant_sha, *, root, state_dir, store, deps, manager, staging, proxy):
    attempt = token = worker = None
    receipt = {'job_id':job['job_id'],'attempt_id':None,'execution_class':job['execution_class'],'certification_effect':'none','root_grant_sha256':grant_sha,'exports_verified':False,'worker_termination_confirmed':False,'scientific_identity_verified':False}
    terminal = 'needs_reconciliation'
    destination = None; collection_deadline = None
    diagnostic_id = uuid.uuid4().hex
    receipt.update(registration_returned=False,reserve_returned=False,claim_returned=False,create_returned=False,reservation_cancel_returned=False)
    def phase(value, *, durable=False):
        need(value in STARTUP_PHASES,'fixed phase')
        receipt['phase'] = value
        if durable:
            receipt['startup_receipt'] = atomic_startup_receipt(state_dir,diagnostic_id,receipt)
    try:
        phase('staging',durable=True)
        with staging.load(lambda:payload_for(root,job,grant_bytes,grant_sha),max_payload_bytes=16777216,timeout_seconds=20) as staged:
            grant = json.loads(grant_bytes)
            phase('audit_time',durable=True)
            deps.require_audit_time(job['timeout_seconds'])
            phase('register',durable=True)
            store.register(job)
            receipt['registration_returned'] = True
            with deps.lifecycle_lock():
                phase('lifecycle_time',durable=True)
                deps.require_audit_time(job['timeout_seconds'])
                phase('reserve',durable=True)
                token = manager.reserve(deps.OWNER,external_leases=deps.external_leases())
                receipt.update(worker_reservation=token,reserve_returned=True)
                phase('claim',durable=True)
                try: attempt = store.claim(job['job_id'],deps.policy['external_work_reserved_usd'])
                except Exception:
                    manager.cancel_reservation(token)
                    receipt['reservation_cancel_returned'] = True
                    token = None; raise
                receipt.update(attempt_id=attempt,claim_returned=True)
                phase('create',durable=True)
                worker = manager.create_reserved(token)
                receipt['create_returned'] = True
            receipt['sandbox_id'] = worker.sandbox_id
            phase('upload')
            uploaded = worker.upload(job['job_id'],staged.payload,staged.expected_sha256,max_bytes=16777216)
            staged.verified_upload(uploaded,job_id=job['job_id'])
        phase('mark_running')
        store.mark_running(job['job_id'],attempt,worker.sandbox_id)
        phase('run')
        run = worker.run(job['job_id'],job['argv'],timeout_seconds=job['timeout_seconds'],export_margin_seconds=90)
        receipt['command_exit_code'] = run['exit_code']
        destination = state_dir/'exports'/job['job_id']/attempt
        collection_deadline = time.monotonic()+20
        phase('collect')
        with proxy.phase(20,deadline=collection_deadline):
            receipt['exports'] = worker.download(job['job_id'],job['exports'],destination,max_bytes=job['max_export_bytes'])
            def reject_constant(value): raise ValueError('non_RFC_JSON_number')
            values = {name:json.loads(bounded_read(destination,name,job['max_export_bytes']),parse_constant=reject_constant) for name in job['exports']}
            need(all(type(value) is dict for value in values.values()), 'export JSON object shape')
            value,execution = values['result.json'],values['execution.json']
            phase('validate_result')
            validate_result(value,execution,job,grant)
        receipt['scientific_identity_verified'] = True
        receipt['exports_verified'] = True
        receipt['job_status'] = COLLECTION_STATUS
        terminal = 'completed' if run['exit_code'] == 0 else 'failed'
        phase('completed')
    except Exception as exc:
        receipt.update(safe_exception(exc),failure_phase=receipt.get('phase','staging'))
        if type(receipt.get('command_exit_code')) is int: terminal = 'failed'
    finally:
        if worker is not None:
            if destination is None and attempt: destination = state_dir/'exports'/job['job_id']/attempt
            if not receipt['exports_verified']:
                try:
                    if collection_deadline is None: collection_deadline = time.monotonic()+20
                    with proxy.phase(20,deadline=collection_deadline):
                        receipt['partial_exports'] = worker.download(job['job_id'],job['exports'],destination,max_bytes=job['max_export_bytes'],allow_incomplete=True)
                except Exception as exc: receipt['partial_export_error_class'] = type(exc).__name__
            try:
                phase('cleanup_worker')
                with proxy.phase(90):
                    closed = worker.close('One new deterministic experiment finished; preserve bounded outputs',allow_uncertain_job=True)
                    receipt['worker_termination_confirmed'] = closed.get('absence_confirmed') is True
            except Exception as exc:
                error = safe_exception(exc)
                receipt.update(cleanup_error_class=error['error_class'],cleanup_error_errno=error['error_errno'])
        elif manager is not None and token is not None:
            try:
                phase('cleanup_reservation')
                with proxy.phase(90):
                    closed = manager.close_reservation(token,'Close exact new-experiment creation; no retry',allow_uncertain_job=True)
                    receipt['worker_termination_confirmed'] = closed.get('absence_confirmed') is True
            except Exception as exc:
                error = safe_exception(exc)
                receipt.update(cleanup_error_class=error['error_class'],cleanup_error_errno=error['error_errno'])
        if not receipt['worker_termination_confirmed'] and attempt: terminal = 'needs_reconciliation'
        try:
            if attempt is not None:
                phase('finish')
                store.finish(job['job_id'],attempt,terminal,receipt)
                deps.save(state_dir/'attempts'/f'{attempt}.json',receipt)
                if terminal in {'completed','failed'} and receipt['worker_termination_confirmed']:
                    try:
                        phase('settle')
                        settlement = store.settle_closed_attempt(attempt,expected_owner=deps.OWNER)
                        deps.save(state_dir/'settlements'/f'{attempt}.json',settlement)
                    except Exception as exc:
                        deps.save(state_dir/'settlements'/f'{attempt}.json',{'attempt_id':attempt,'settlement_error_class':safe_exception(exc)['error_class'],'reservation_released':False})
        except Exception as exc:
            error = safe_exception(exc)
            receipt.update(finalization_error_class=error['error_class'],finalization_error_errno=error['error_errno'],finalization_phase=receipt['phase'])
            terminal = 'coordinator_error'
        finally:
            try: receipt['startup_receipt'] = atomic_startup_receipt(state_dir,diagnostic_id,receipt)
            except Exception as exc:
                error = safe_exception(exc)
                receipt.update(startup_receipt_error_class=error['error_class'],startup_receipt_error_errno=error['error_errno'])
    return {'job_id':job['job_id'],'attempt_id':attempt,'state':terminal,'worker_termination_confirmed':receipt['worker_termination_confirmed'],'certified_tasks':0,
        'phase':receipt.get('failure_phase',receipt.get('finalization_phase',receipt.get('phase'))),
        'last_phase':receipt.get('phase'),'error_class':receipt.get('error_class'),
        'error_errno':receipt.get('error_errno'),'worker_reservation':receipt.get('worker_reservation'),
        'registration_returned':receipt['registration_returned'],'reserve_returned':receipt['reserve_returned'],
        'claim_returned':receipt['claim_returned'],'create_returned':receipt['create_returned'],
        'reservation_cancel_returned':receipt['reservation_cancel_returned'],
        'startup_receipt':receipt.get('startup_receipt'),
        'startup_receipt_error_class':receipt.get('startup_receipt_error_class'),
        'startup_receipt_error_errno':receipt.get('startup_receipt_error_errno'),
        'finalization_error_class':receipt.get('finalization_error_class'),
        'finalization_error_errno':receipt.get('finalization_error_errno'),
        **{key:receipt[key] for key in ('provider_inspection_error_class','provider_inspection_error_errno','provider_inspection_http_status') if key in receipt}}

def select_batch_profile(jobs):
    need(type(jobs) is list and jobs, 'finite profile batch')
    profiles = {job.get('resource_profile') for job in jobs}
    need(len(profiles) == 1 and profiles <= {'small','large'}, 'homogeneous reviewed profile')
    profile = next(iter(profiles))
    if profile == 'large':
        expected = {'e771c8308e359a38e86429182fb2d0efd485cd24e77088476ca65e0de94212a0': 'flt_regular_formalization', '1952baec0f3394afcb344d83f7ee5c73f3794c237af038f5b6a50cb39ad6c45d': 'sphere_eversion_formalization'}
        need(all(job.get('task_id') in expected.values() and expected.get(sha(canonical(job))) == job.get('task_id') for job in jobs), 'only two exact FS large jobs')
    return profile

def run_batch(packets, *, root, state_dir, deps, provider, max_workers=10):
    """Packets are (job dict, exact root grant bytes, externally selected hash).

    deps supplies the unchanged installed QueueStore/CloudWorkerManager/time,
    locking, policy, ownership and save functions. Root checks current source,
    supported SDK version and storage before constructing provider; no auth here.
    """
    need(1 <= max_workers <= 50 and type(max_workers) is int and 1 <= len(packets) <= 50, 'useful finite batch')
    need(len({p[0]['job_id'] for p in packets}) == len(packets), 'batch duplicate IDs')
    need(0 < resource.getrlimit(resource.RLIMIT_AS)[0] <= 536870912 and 0 < resource.getrlimit(resource.RLIMIT_CPU)[0] <= 60 and len(os.sched_getaffinity(0)) == 1, 'dedicated bounded coordinator')
    admitted = {}
    for job,body,expected in packets:
        need(sha(body) == expected, 'caller-selected root grant')
        grant = json.loads(body)
        need(grant.get('job_sha256') == sha(canonical(job)) and grant.get('job_id') == job['job_id'], 'job admission hash')
        resume = grant.get('resume_registered_pending_without_attempt',False)
        need(type(resume) is bool,'typed root pending-resume flag')
        admitted[job['job_id']] = {'job_sha256':grant['job_sha256'],'grant_sha256':expected,'resume_registered_pending_without_attempt':resume}
    store = experiment_store(deps.QueueStore,state_dir/'queue.sqlite3',deps.policy['compute_ceiling_usd'],admitted)
    proxy = DeadlineProvider(provider,deps.NotFound,deps.OutcomeUnknown)
    profile = select_batch_profile([packet[0] for packet in packets])
    need(getattr(provider,'profile',None) == profile, 'provider manager profile consensus')
    reason = 'Root granted a finite useful batch, with small-profile hourly reservations, four staging slots and exact owned close; no idle fanout.' if profile == 'small' else 'Root granted only exact FS original-helper pilots, pinned8CPU8GiB large template, .5328 conservative hourly reservations, four staging slots and exact owned close; no fallback.'
    manager = deps.CloudWorkerManager(proxy,state_dir/'provider',deps.OWNERS,max_workers=deps.policy['max_workers'],profile=profile,second_worker_reason=reason)
    staging = deps.StagingBudget(max_stages=4,max_bytes=67108864)
    threading.stack_size(262144)
    results = []; pending = iter(packets); stopped = False
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        active = {}
        while active or not stopped:
            while not stopped and len(active) < max_workers:
                packet = next(pending,None)
                if packet is None: stopped = True; break
                job,body,expected = packet
                active[pool.submit(execute_one,job,body,expected,root=root,state_dir=state_dir,store=store,deps=deps,manager=manager,staging=staging,proxy=proxy)] = job['job_id']
            if not active: break
            done,_ = wait(active,timeout=1,return_when=FIRST_COMPLETED)
            for future in done:
                jid = active.pop(future)
                try: outcome = future.result()
                except Exception as exc: outcome = {'job_id':jid,'state':'coordinator_error','error_class':type(exc).__name__}
                results.append(outcome)
                if outcome['state'] in {'needs_reconciliation','coordinator_error'}:
                    stopped = True; staging.stop()
    return {'results':results,'staging':staging.snapshot(),'submitted_jobs':len(results),'remaining_jobs_admitted':False,'certified_tasks':0}
