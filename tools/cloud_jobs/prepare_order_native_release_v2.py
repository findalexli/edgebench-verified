"""Rebind only the V2 capture adapter in the immutable, unadmitted V1 template."""
import argparse, ast, hashlib, json, os, resource, signal
from pathlib import Path

def body(x):return (json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def prepare(workspace,out):
    original=workspace/'audit/evidence/order-native-release-compact-sol-v1'
    handoff=(original/'handoff.json').read_bytes()
    assert sha(handoff)=='8a0ccf350e593d7547a3abe11135db275d8cd7601f410e0e917fd319c9a7e0fd'
    h=json.loads(handoff);f=(workspace/h['freeze']['path']).read_bytes()
    assert sha(f)==h['freeze']['sha256'] and len(f)==h['freeze']['bytes']
    blueprint_body=(workspace/h['job_blueprint']['path']).read_bytes()
    assert sha(blueprint_body)==h['job_blueprint']['sha256'] and len(blueprint_body)==h['job_blueprint']['bytes']
    blue=json.loads(blueprint_body)
    out=out.resolve();assert out.is_relative_to(workspace/'audit/evidence') and not out.exists()
    out.mkdir(mode=0o700)
    def ref(path):
        p=workspace/path;assert not p.is_symlink() and p.stat().st_size<=1048576
        b=p.read_bytes();return {'path':path,'bytes':len(b),'sha256':sha(b)}
    new=ref('tools/cloud_jobs/order_release_backend_v2.py');ast.parse((workspace/new['path']).read_bytes())
    old=next(r for r in blue['inputs'] if r['target']=='order_release_backend.py')
    assert old['sha256']=='9ed30c21b364e599ccda34d901dc6ed8a4300230dcebdbfec25ad469a0a46bf8'
    replacement=dict(old,path=new['path'],bytes=new['bytes'],sha256=new['sha256'])
    blue['inputs']=[replacement if r['target']=='order_release_backend.py' else r for r in blue['inputs']]
    refs=blue['science']['host_tool_vm_memory_boundary']['source_refs']
    blue['science']['host_tool_vm_memory_boundary']['source_refs']=[replacement if r['target']=='order_release_backend.py' else r for r in refs]
    blue['science']['worker_input_sha256']['order_release_backend.py']=new['sha256']
    worker=dict(ref('tools/cloud_jobs/order_native_release_worker_v2.py'),workspace='workspace',target='worker.py')
    blue['inputs']=[worker if r['target']=='worker.py' else r for r in blue['inputs']]
    blue['science']['host_tool_vm_memory_boundary']['source_refs']=[worker if r['target']=='worker.py' else r for r in blue['science']['host_tool_vm_memory_boundary']['source_refs']]
    blue['science']['worker_input_sha256']['worker.py']=worker['sha256']
    prereg={'schema':'order-native-release-compact-prereg-v2','status':'SOURCE_ONLY_UNADMITTED',
        'v1_handoff_sha256':sha(handoff),'counterevidence':'V1 on_chunk overflow was swallowed after append by the pinned inherited method; 131072 bytes retained under claimed65536. V1 stays NO_GO and immutable.',
        'hypothesis':'Reject a chunk before native retention/log/callback if cumulative raw bytes would exceed65536; close the stream and confirm reader termination plus exact owned-container retirement on exception/timeout. Native archive/filter/grade/rescale/selection and V41 controls remain unchanged.',
        'capture_limits':{'retained_raw_bytes':65536,'delivered_UTF8_bytes':65536,'nonempty_chunk_count_max':65536,'reader_join_after_owned_stop_seconds':1},
        'limitations':['The SDK allocates the next received chunk before this check; SDK/socket/kernel transient buffers are bounded by the existing VM envelope, not this retained-byte cap.',
            'Thirty-second execution deadline plus the existing ten-second SDK timeout for each exact-owned cleanup call and one-second reader join; not an absolute thirty-second bound on cleanup.',
            'A non-closeable stream, close failure, remaining reader or unconfirmed owned close fails typed and cannot pass the controls; outer owned-VM closure remains mandatory.',
            'Compact size/installed SDK stream behavior/restoration/collector fit remain unmeasured; no full-image spool, model, query, provider or native call.'],
        'public_oracle_calls_added':0,'all_five_gates':'pending','actual_calls':0}
    (out/'prereg.json').write_bytes(body(prereg));prereg_ref=dict(ref(str((out/'prereg.json').relative_to(workspace))),workspace='workspace',target='prereg.json')
    blue['inputs']=[prereg_ref if r['target']=='prereg.json' else r for r in blue['inputs']]
    blue['controls']=[prereg_ref if r['target']=='prereg.json' else r for r in blue['controls']]
    blue['science']['hypothesis_freeze_sha256']=prereg_ref['sha256']
    blue['science']['worker_input_sha256']['prereg.json']=prereg_ref['sha256']
    blue['science']['native_capture_contract']=prereg['capture_limits']
    blue['schema']='order-native-release-source-job-blueprint-v2';blue['source_correction']='V2 cap before native append; V1 immutable NO_GO retained'
    # Fresh role hashes are metadata only; adoption and grant are root actions.
    root=Path(blue['workspace_bases']['canonical'])
    for row in blue['runtime_refs']+[blue['policy_ref']]:
        p=root/row['path'];assert not p.is_symlink() and p.stat().st_size<=1048576
        b=p.read_bytes();row.update(bytes=len(b),sha256=sha(b))
    assert len(blue['inputs'])==20 and len(blue['science']['host_tool_vm_memory_boundary']['source_refs'])==8
    assert all(blue['science']['worker_input_sha256'][r['target']]==r['sha256'] for r in blue['inputs'])
    (out/'job-blueprint.json').write_bytes(body(blue))
    correction={'schema':'order-native-release-compact-correction-v2','old_backend':old,'new_backend':replacement,'new_worker':worker,
        'unchanged':'Every other payload except prereg.json and one worker insertion binding live backend events before the controls; original TaskSpec/20 fork modules, commands/archives/filter/parser/grade/rescale/selection, controls, worker, delta helpers and resource/retention/export caps.',
        'staging':'New source file is staged as order_release_backend.py; worker imports that exact target; its only insertion retains live receipts in failure checkpoints. Root must create new byte-bound wrapper/experiment/job/grant identities.',
        'source_only':True,'operational_admission':False,'actual_calls':0}
    (out/'correction.json').write_bytes(body(correction))
    print(json.dumps({'inputs_before_wrapper':len(blue['inputs']),'payload_bytes':sum(r['bytes'] for r in blue['inputs']), 'actual_calls':0}))

if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_AS,(134217728,)*2);resource.setrlimit(resource.RLIMIT_CPU,(5,)*2)
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.alarm(18);os.umask(0o077)
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    prepare(Path(__file__).resolve().parents[2],a.output)
