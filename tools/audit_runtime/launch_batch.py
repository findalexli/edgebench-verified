"""Launch root-admitted jobs with canonical operations and one owned source base.

CLI: launch_batch.py ADMISSION ADMISSION_SHA256 ADMISSION_BYTES CANONICAL_ROOT
The hashed admission selects operational_root, reference_base and validator_source.
All queue, policy, credential-helper and ownership operations stay canonical.
"""
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
from datetime import datetime,timezone
import hashlib,importlib.metadata,json,os,resource,runpy,signal,sys

VALIDATOR_SHA256='c96d3e7d78260ad754433edad19c5a324929f1857be7e35612ea18db2c6759c8'
VALIDATOR_BYTES=9848


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


def select_validator(root, reference, row, read, need):
    need(type(row) is dict and set(row)=={'path','sha256','bytes'} and
         row['sha256']==VALIDATOR_SHA256 and type(row['bytes']) is int and
         row['bytes']==VALIDATOR_BYTES,'exact_reviewed_validator_pin')
    path=reference_path(reference,row['path'],need)
    need(path==root/'tools/audit_runtime/job_validator.py','canonical_reviewed_validator')
    need('job_validator' not in sys.modules and 'coordinator' not in sys.modules,'fresh_runtime_selection')
    raw=read(path,row['sha256'],row['bytes'])
    module=type(sys)('job_validator')
    module.__file__=str(path)
    # Compile the exact checked bytes instead of re-reading or using a cached module.
    exec(compile(raw,str(path),'exec'),module.__dict__)
    sys.modules['job_validator']=module
    return module


def main():
    resource.setrlimit(resource.RLIMIT_AS,(268435456,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,)*2)
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.alarm(1530);os.umask(0o077)
    # Explicit canonical root prevents running a worktree's copied policy/state/key helper.
    ROOT=Path(sys.argv[4]);E=ROOT/'audit/evidence';R=E/'deterministic-experiment-startup-telemetry-sol-v1';STATE=ROOT.parent/'work/cloud-queue'
    h=runpy.run_path(str(E/'sol-cloud-authorization-v1/selected-source-root-review-20261009T1155.py'))
    read,need=h['read'],h['need']
    p=Path(sys.argv[1]);OUT=p.parent;admission=json.loads(read(p,sys.argv[2],int(sys.argv[3])))
    ROOT,REFERENCE=select_roots(sys.argv[4],admission,need)
    def frozen(p,value):
        b=(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
        with os.fdopen(os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb') as f:f.write(b)
    need(admission['decision']=='ADMIT_ONE_USEFUL_PARALLEL_DETERMINISTIC_BATCH','exact_root_batch')
    validator=select_validator(ROOT,REFERENCE,admission['validator_source'],read,need)
    need(importlib.metadata.version('e2b')=='2.19.0','supported_installed_SDK')
    sys.path.insert(0,str(R));sys.path.insert(1,str(E/'deterministic-experiment-coordinator-sol-v1'));sys.path.insert(2,str(ROOT/'tools'))
    import coordinator,run_cloud_audit as audit
    from cloud_queue import QueueStore
    from cloud_worker import SDKProvider,CloudWorkerManager,NotFound,OutcomeUnknown
    from cloud_dispatch_resources import StagingBudget
    need(coordinator.validate is validator.validate and coordinator.validate_result is validator.validate_result,'selected_validator_loaded')
    need(hashlib.sha256(read(R/'coordinator.py')).hexdigest()=='76dcfef04c1171f87615651590c3dd8f26759a183327c7e51a85eaae88138cd8','exact_loaded_startup_delta')
    c=admission['coordinator_source'];read(reference_path(REFERENCE,c['path'],need),c['sha256'],c['bytes'])
    bindings=[]
    for row in admission['jobs']:
        j=row['job'];g=row['grant'];job=json.loads(read(reference_path(REFERENCE,j['path'],need),j['sha256'],j['bytes']));body=read(reference_path(REFERENCE,g['path'],need),g['sha256'],g['bytes'])
        grant=json.loads(body)
        need(admission['validator_source'] in grant['runtime_refs'],'validator_grant_binding')
        for runtime in grant['runtime_refs']:read(reference_path(REFERENCE,runtime['path'],need),runtime['sha256'],runtime['bytes'])
        payload=coordinator.payload_for(REFERENCE,job,body,g['sha256']);payload.clear();bindings.append((job,body,g['sha256']))
    policy=audit.read_policy();need(policy['compute_ceiling_usd'] is None and policy['external_work_reserved_usd']==0,'no_agent_compute_ceiling')
    need(policy['audit_deadline_utc']==validator.DEADLINE.isoformat(),'renewed_window_matches_policy')
    audit.AUDIT_DEADLINE=validator.DEADLINE.isoformat()
    audit.require_audit_time(max(x[0]['timeout_seconds'] for x in bindings))
    need(hashlib.sha256(read(ROOT/'tools/cloud_queue.py')).hexdigest()=='8ae70740ab9ddc5e0691f6e86e05352c8ac867b79339cd387b1888510102ab36','fresh_current_queue')
    deps=SimpleNamespace(QueueStore=QueueStore,CloudWorkerManager=CloudWorkerManager,NotFound=NotFound,OutcomeUnknown=OutcomeUnknown,
      StagingBudget=StagingBudget,policy=policy,require_audit_time=audit.require_audit_time,lifecycle_lock=audit.lifecycle_lock,
      OWNER=audit.OWNER,OWNERS=audit.OWNERS,external_leases=audit.external_leases,save=audit.save)
    keyhelper=ROOT.parent/'work/runtime-diagnosis/e2b_pilot.py';read(keyhelper,'a76c0122e4507fd2b0561d911c70322a1316c7518a3259b60a132cb970ec8981',3775)
    frozen(OUT/'launch-handle.json',{'utc':datetime.now(timezone.utc).isoformat(),'job_ids':[x[0]['job_id'] for x in bindings],
      'pid':os.getpid(),'state':'STARTING_USEFUL_PARALLEL_NATIVE_BATCH','automatic_retries':0,'no_model_run':True,
      'operational_root':str(ROOT),'reference_base':str(REFERENCE),'validator_source':admission['validator_source']})
    provider=None;secret=None
    try:
        secret=runpy.run_path(str(keyhelper))['api_key']();provider=SDKProvider(api_key=secret,profile='small');secret=None
        result=coordinator.run_batch(bindings,root=REFERENCE,state_dir=STATE,deps=deps,provider=provider,max_workers=admission['max_workers'])
        frozen(OUT/'batch-result.json',result);print(json.dumps(result,separators=(',',':')),flush=True)
    finally:
        secret=None;os.environ.pop('E2B_API_KEY',None)
        if provider is not None:provider._key=None
if __name__=='__main__':main()
