"""Source-only narrow rebind of the accepted V2 template and public overlay."""
import argparse,ast,hashlib,json,os,resource,signal
from pathlib import Path

def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(x):return (json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def prepare(workspace,out):
    prior=workspace/'audit/evidence/order-native-release-compact-sol-v2'
    h=json.loads((prior/'handoff.json').read_bytes());assert sha((prior/'handoff.json').read_bytes())=='75b5e4964d6b27e1cf6787031e1a3f050b40a5b09db7c5615a3309886c3386b6'
    b=(workspace/h['job_blueprint']['path']).read_bytes();assert sha(b)==h['job_blueprint']['sha256'];blue=json.loads(b)
    assert out.resolve().is_relative_to(workspace/'audit/evidence') and (out/'public-runtime-lock.json').is_file() and not (out/'freeze.json').exists()
    def ref(path,target):
        p=workspace/path;assert not p.is_symlink() and p.stat().st_size<=1048576
        b=p.read_bytes();return {'workspace':'workspace','path':path,'target':target,'bytes':len(b),'sha256':sha(b)}
    worker=ref('tools/cloud_jobs/order_native_release_worker_v3.py','worker.py');helper=ref('tools/cloud_jobs/order_public_runtime.py','order_public_runtime.py')
    lock=ref(str((out/'public-runtime-lock.json').relative_to(workspace)),'public-runtime-lock.json')
    for r in (worker,helper):ast.parse((workspace/r['path']).read_bytes())
    blue['inputs']=[worker if r['target']=='worker.py' else r for r in blue['inputs']]+[helper,lock]
    refs=blue['science']['host_tool_vm_memory_boundary']['source_refs'];blue['science']['host_tool_vm_memory_boundary']['source_refs']=[worker if r['target']=='worker.py' else r for r in refs]
    blue['science']['worker_input_sha256'].update({r['target']:r['sha256'] for r in (worker,helper,lock)})
    blue['science']['child_argv']=['python3','-I','-S','-B','worker.py']
    declaration={'lock_sha256':lock['sha256'],'wheel_count':8,'download_total_bytes':4194304,'wheel_bytes':1048576,
        'selected_bytes':4194304,'selected_files':512,'overlay_bytes':1048576,'wall_seconds':160,
        'regime':'prefrozen_public_pure_source_zip_no_site_no_resolver_no_compiled_accelerators'}
    blue['science']['public_runtime_overlay']=declaration
    prereg={'schema':'order-native-release-runtime-overlay-prereg-v1','status':'SOURCE_ONLY_UNADMITTED','V2_kept':True,
        'change':'Declare eight exact public wheels from retained Graph receipt; select only unchanged Python/data/dist metadata into one capped ZIP. Only three named cp311 accelerators are deliberately omitted. -I-S-B plus explicit ZIP startup prevents ambient site dependencies.',
        'hypothesis':'Measured pure overlay imports let the same native control/retention attempt reach unchanged judge_submission; any wheel/import/origin/cap/deadline mismatch remains incomplete before Docker client creation.',
        'dependency_declaration':declaration,'root_grant_controls':'The public-runtime-lock is an exact extra grant control. The existing host-tool exception/network scope carries the phase; do not use unrelated four-wheel dependency_bootstrap branch or change validator/caps.',
        'reuse':'V2 hard reader, installed checker/base/TaskSpec/source pins, V41 retained controls, archive/parser/grade/rescale/selection, retention and collector contracts unchanged.',
        'all_five_gates':'pending','actual_native_provider_auth_model_calls':0}
    (out/'prereg.json').write_bytes(canonical(prereg));preref=ref(str((out/'prereg.json').relative_to(workspace)),'prereg.json')
    blue['inputs']=[preref if r['target']=='prereg.json' else r for r in blue['inputs']]
    blue['controls']=[preref if r['target']=='prereg.json' else r for r in blue['controls']]+[lock]
    blue['science']['hypothesis_freeze_sha256']=preref['sha256'];blue['science']['worker_input_sha256']['prereg.json']=preref['sha256']
    blue['schema']='order-native-release-public-overlay-job-blueprint-v1';blue['source_correction']='Exact declared public pure-source ZIP startup; V2 source preserved and only import setup amended'
    blue['root_must_bind']=[x for x in blue['root_must_bind'] if not x.startswith('reviewed existing tool environment')]
    blue['root_must_bind']+=['Explicit root-selected public_runtime_overlay and exact eight-wheel-lock grant control before any fetch; actual no-site child argv, all byte-bound source inputs and existing max8 host source refs unchanged in count','Saved overlay identity/count/bytes plus eight import origins/versions and declared pure YAML/charset before Docker client creation; stop typed on incompatibility, no resolver/package fallback']
    root=Path(blue['workspace_bases']['canonical'])
    for r in blue['runtime_refs']+[blue['policy_ref']]:
        p=root/r['path'];b=p.read_bytes();assert len(b)<=1048576 and not p.is_symlink();r.update(bytes=len(b),sha256=sha(b))
    assert len(blue['inputs'])==22 and len(blue['science']['host_tool_vm_memory_boundary']['source_refs'])==8
    assert all(blue['science']['worker_input_sha256'][r['target']]==r['sha256'] for r in blue['inputs'])
    (out/'job-blueprint.json').write_bytes(canonical(blue))
    print(json.dumps({'inputs_before_wrapper':22,'payload_bytes':sum(r['bytes'] for r in blue['inputs']),'actual_calls':0}))
if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_AS,(134217728,)*2);resource.setrlimit(resource.RLIMIT_CPU,(5,)*2)
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.alarm(18);os.umask(0o077)
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(Path(__file__).resolve().parents[2],a.output.resolve())
