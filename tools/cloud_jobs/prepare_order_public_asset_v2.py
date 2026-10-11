"""Source-only packaging correction; prior worker/native/runtime remain fixed."""
import argparse, hashlib, json, os, resource, signal
from pathlib import Path

def sha(body):return hashlib.sha256(body).hexdigest()
def canonical(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def prepare(workspace,out):
    prior=workspace/'audit/evidence/order-native-release-runtime-overlay-sol-v1'
    assert sha((prior/'handoff.json').read_bytes())=='3ce7fc45b4862ff5818f2379ce507bf155f1349b88168a1a89f227d095cb514e'
    body=(prior/'job-blueprint.json').read_bytes()
    assert sha(body)=='451f1c2809ecb020977343b3ba8bd251096e87af86a91ab64239a625cc1811ff'
    blue=json.loads(body)
    assert out.resolve().is_relative_to(workspace/'audit/evidence') and not (out/'freeze.json').exists()
    def ref(path,target):
        p=workspace/path;assert not p.is_symlink() and p.stat().st_size<=1048576
        body=p.read_bytes();return {'workspace':'workspace','path':path,'target':target,'bytes':len(body),'sha256':sha(body)}
    helper=ref('tools/cloud_jobs/order_public_runtime_v2.py','order_public_runtime.py')
    prereg={'schema':'order-native-release-public-asset-prereg-v2','status':'SOURCE_ONLY_UNADMITTED',
        'hypothesis':'The exact3677B ordinary JavaScript source asset in pinned urllib3 is the sole additional body allowance; the corrected real public source ZIP/import closure may then reach unchanged native paired archive/retention controls.',
        'asset':{'wheel_name':'urllib3','wheel_sha256':'0cf3cae568d36aa9576b28dfb35f11328f1cb974ca7647d9475ebb86c75ac6e3','path':'urllib3/contrib/emscripten/emscripten_fetch_worker.js','bytes':3677},
        'scope':'Packaging only. WorkerV3, wheel URLs/hashes, no-site argv, timer/read/path/count/source/ZIP/import/capture/score/native/retention/export caps unchanged; no broad suffix, resolver or dependency fallback.',
        'historical_limit':'V46 did not retain the offending member. Current exact pinned packaging incompatibility and correction do not manufacture that historical observation.',
        'local_probe':'Clean isolated/no-site Python3.12 actual public cached source import only, no DockerClient/native/private helper/task/auth/network calls. Does not establish remote family import compatibility.',
        'reuse':'All accepted V1/V2 reader/science/core controls and earlier overlay checks reused by exact one-region inverse, not rerun.',
        'all_five_gates':'pending','actual_native_provider_auth_model_calls':0}
    (out/'prereg.json').write_bytes(canonical(prereg));pref=ref(str((out/'prereg.json').relative_to(workspace)),'prereg.json')
    blue['inputs']=[helper if row['target']=='order_public_runtime.py' else pref if row['target']=='prereg.json' else row for row in blue['inputs']]
    blue['controls']=[pref if row['target']=='prereg.json' else row for row in blue['controls']]
    for row in (helper,pref):blue['science']['worker_input_sha256'][row['target']]=row['sha256']
    blue['science']['hypothesis_freeze_sha256']=pref['sha256']
    blue['schema']='order-native-release-public-asset-job-blueprint-v2'
    blue['source_correction']='One exact wheel-bound3677B JS source asset; helper one-region inverse, workerV3 unchanged'
    assert len(blue['inputs'])==22 and len(blue['science']['host_tool_vm_memory_boundary']['source_refs'])==8
    assert blue['science']['child_argv']==['python3','-I','-S','-B','worker.py']
    assert all(blue['science']['worker_input_sha256'][row['target']]==row['sha256'] for row in blue['inputs'])
    (out/'job-blueprint.json').write_bytes(canonical(blue))
    print(json.dumps({'inputs_before_wrapper':22,'payload_bytes':sum(row['bytes'] for row in blue['inputs']),'actual_calls':0}))

if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_AS,(134217728,)*2);resource.setrlimit(resource.RLIMIT_CPU,(5,)*2)
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.alarm(18);os.umask(0o077)
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    prepare(Path(__file__).resolve().parents[2],args.output.resolve())
