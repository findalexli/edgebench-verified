"""Launch root-admitted jobs with canonical operations and one owned source base.

CLI: launch_batch.py ADMISSION ADMISSION_SHA256 ADMISSION_BYTES CANONICAL_ROOT
The hashed admission selects canonical validator/coordinator/provider source pins.
All queue, policy, credential-helper and ownership operations stay canonical.
"""
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
from datetime import datetime,timezone
import hashlib,importlib.metadata,json,os,resource,runpy,signal,sys



def owned_root(path, need):
    need(type(path) is str and 0 < len(path) <= 1024 and '\x00' not in path,'owned_root_path')
    p=Path(path)
    need(p.is_absolute() and p.is_dir() and not any(x.is_symlink() for x in (p,*p.parents)),'owned_ordinary_root')
    resolved=p.resolve()
    need(p==resolved,'owned_normalized_root')
    return resolved


def reference_path(base, relative, need):
    need(type(relative) is str and 0 < len(relative) <= 256 and '\x00' not in relative,'reference_path')
    p=PurePosixPath(relative)
    need(not p.is_absolute() and all(x not in ('','.','..') for x in relative.split('/')),'relative_reference_path')
    return base/relative


def select_roots(canonical_root, admission, need):
    root=owned_root(canonical_root,need)
    need(root.name=='edgebenchverified' and admission.get('operational_root')==str(root),'canonical_operational_root')
    reference=owned_root(admission.get('reference_base'),need)
    need(reference in {root,root.parent},'owned_reference_base')
    return root,reference


def select_runtime_sources(root, reference, admission, read, need):
    """Load checked admission-selected bytes only at the three canonical roles."""
    roles = {
        'job_validator': ('validator_source', {root/'tools/audit_runtime/job_validator.py'}),
        'cloud_worker': ('provider_source', {root/'tools/cloud_worker.py'}),
        'coordinator': ('coordinator_source', {root/'tools/audit_runtime/coordinator.py',
            root/'audit/evidence/deterministic-experiment-startup-telemetry-sol-v1/coordinator.py'})}
    need(not any(name in sys.modules for name in roles),'fresh_runtime_selection')
    pins, paths, code = {}, {}, {}
    for name, (field, allowed) in roles.items():
        row = admission.get(field)
        need(type(row) is dict and set(row)=={'path','sha256','bytes'} and
             type(row['sha256']) is str and len(row['sha256'])==64 and
             all(c in '0123456789abcdef' for c in row['sha256']) and
             type(row['bytes']) is int and 1 <= row['bytes'] <= 1048576,'runtime_source_pin')
        path = reference_path(reference,row['path'],need)
        need(path in allowed and path==path.resolve() and
             not any(p.is_symlink() for p in (path,*path.parents)),'canonical_runtime_role')
        raw = read(path,row['sha256'],row['bytes'])
        need(type(raw) is bytes and len(raw)==row['bytes'] and
             hashlib.sha256(raw).hexdigest()==row['sha256'],'checked_runtime_identity')
        pins[name], paths[name] = dict(row), path
        code[name] = compile(raw,str(path),'exec')
    modules = {}
    try:
        for name in roles:
            need(name not in sys.modules,'fresh_selected_role_load')
            module = type(sys)(name)
            module.__file__ = str(paths[name])
            sys.modules[name] = module
            exec(code[name],module.__dict__)
            modules[name] = module
    except BaseException:
        for name in roles: sys.modules.pop(name,None)
        raise
    return modules,pins


def bind_runtime_sources(root, reference, grant, pins, read, need):
    """Each grant binds the actual selected role bytes, without alternate pins."""
    rows = grant.get('runtime_refs')
    need(type(rows) is list and 4 <= len(rows) <= 8,'runtime_grant_refs')
    need(all(pin in rows for pin in pins.values()),'selected_runtime_grant_binding')
    seen = set()
    for row in rows:
        need(type(row) is dict and set(row)=={'path','sha256','bytes'} and
             type(row['sha256']) is str and len(row['sha256'])==64 and
             all(c in '0123456789abcdef' for c in row['sha256']) and
             type(row['bytes']) is int and 1 <= row['bytes'] <= 1048576,'runtime_grant_pin')
        path = reference_path(reference,row['path'],need)
        need(path not in seen,'unique_runtime_grant_path'); seen.add(path)
        role = {'job_validator.py':'job_validator','coordinator.py':'coordinator','cloud_worker.py':'cloud_worker'}.get(path.name)
        if role is not None: need(row==pins[role],'no_conflicting_runtime_role')
        read(path,row['sha256'],row['bytes'])


def main():
    resource.setrlimit(resource.RLIMIT_AS,(536870912,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,)*2)
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.alarm(1530);os.umask(0o077)
    # Explicit canonical root prevents running a worktree's copied policy/state/key helper.
    ROOT=Path(sys.argv[4]);E=ROOT/'audit/evidence';STATE=ROOT.parent/'work/cloud-queue'
    h=runpy.run_path(str(E/'sol-cloud-authorization-v1/selected-source-root-review-20261009T1155.py'))
    read,need=h['read'],h['need']
    p=Path(sys.argv[1]);OUT=p.parent;admission=json.loads(read(p,sys.argv[2],int(sys.argv[3])))
    ROOT,REFERENCE=select_roots(sys.argv[4],admission,need)
    def frozen(p,value):
        b=(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
        with os.fdopen(os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb') as f:f.write(b)
    need(admission['decision']=='ADMIT_ONE_USEFUL_PARALLEL_DETERMINISTIC_BATCH','exact_root_batch')
    need(importlib.metadata.version('e2b')=='2.19.0','supported_installed_SDK')
    sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(1,str(E/'deterministic-experiment-coordinator-sol-v1'))
    modules,runtime_pins=select_runtime_sources(ROOT,REFERENCE,admission,read,need)
    validator,coordinator=modules['job_validator'],modules['coordinator']
    import run_cloud_audit as audit
    from cloud_queue import QueueStore
    from cloud_worker import SDKProvider,CloudWorkerManager,NotFound,OutcomeUnknown
    from cloud_dispatch_resources import StagingBudget
    need(coordinator.validate is validator.validate and coordinator.validate_result is validator.validate_result,'selected_validator_loaded')
    bindings=[]
    for row in admission['jobs']:
        j=row['job'];g=row['grant'];job=json.loads(read(reference_path(REFERENCE,j['path'],need),j['sha256'],j['bytes']));body=read(reference_path(REFERENCE,g['path'],need),g['sha256'],g['bytes'])
        grant=json.loads(body)
        bind_runtime_sources(ROOT,REFERENCE,grant,runtime_pins,read,need)
        payload=coordinator.payload_for(REFERENCE,job,body,g['sha256']);payload.clear();bindings.append((job,body,g['sha256']))
    batch_profile=coordinator.select_batch_profile([binding[0] for binding in bindings])
    policy=audit.read_policy();need(policy['compute_ceiling_usd'] is None and policy['external_work_reserved_usd']==0,'no_agent_compute_ceiling')
    need(policy['audit_deadline_utc']==validator.DEADLINE.isoformat(),'renewed_window_matches_policy')
    audit.AUDIT_DEADLINE=validator.DEADLINE.isoformat()
    audit.require_audit_time(max(x[0]['timeout_seconds'] for x in bindings))
    need(hashlib.sha256(read(ROOT/'tools/cloud_queue.py')).hexdigest()=='3e938a43240969ef50d0de0edac2d0d358a3ac97a17aa50583a26b3cf42808a1','fresh_current_queue')
    deps=SimpleNamespace(QueueStore=QueueStore,CloudWorkerManager=CloudWorkerManager,NotFound=NotFound,OutcomeUnknown=OutcomeUnknown,
      StagingBudget=StagingBudget,policy=policy,require_audit_time=audit.require_audit_time,lifecycle_lock=audit.lifecycle_lock,
      OWNER=audit.OWNER,OWNERS=audit.OWNERS,external_leases=audit.external_leases,save=audit.save)
    keyhelper=ROOT.parent/'work/runtime-diagnosis/e2b_pilot.py';read(keyhelper,'a76c0122e4507fd2b0561d911c70322a1316c7518a3259b60a132cb970ec8981',3775)
    frozen(OUT/'launch-handle.json',{'utc':datetime.now(timezone.utc).isoformat(),'job_ids':[x[0]['job_id'] for x in bindings],
      'pid':os.getpid(),'state':'STARTING_USEFUL_PARALLEL_NATIVE_BATCH','automatic_retries':0,'no_model_run':True,
      'operational_root':str(ROOT),'reference_base':str(REFERENCE),
      'validator_source':runtime_pins['job_validator'],'coordinator_source':runtime_pins['coordinator'],
      'provider_source':runtime_pins['cloud_worker']})
    provider=None;secret=None
    try:
        secret=runpy.run_path(str(keyhelper))['api_key']();provider=SDKProvider(api_key=secret,profile=batch_profile);secret=None
        result=coordinator.run_batch(bindings,root=REFERENCE,state_dir=STATE,deps=deps,provider=provider,max_workers=admission['max_workers'])
        frozen(OUT/'batch-result.json',result);print(json.dumps(result,separators=(',',':')),flush=True)
    finally:
        secret=None;os.environ.pop('E2B_API_KEY',None)
        if provider is not None:provider._key=None
if __name__=='__main__':main()
