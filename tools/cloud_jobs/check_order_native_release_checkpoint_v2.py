"""Changed early-failure checkpoint and final source-pin projections only."""
import os,resource,signal
resource.setrlimit(resource.RLIMIT_AS,(134217728,)*2);resource.setrlimit(resource.RLIMIT_CPU,(5,)*2)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.alarm(18)
import argparse,ast,hashlib,importlib.util,json,types
from pathlib import Path
WT=Path(__file__).resolve().parents[2]
def sha(b):return hashlib.sha256(b).hexdigest()
def raw(p):assert not p.is_symlink() and p.stat().st_size<=1048576;return p.read_bytes()
def check(out):
    rows=[]
    def ok(name,value,**extra):assert value,name;rows.append(dict(name=name,status='PASS',**extra))
    old=raw(WT/'tools/cloud_jobs/order_native_release_worker.py');new=raw(WT/'tools/cloud_jobs/order_native_release_worker_v2.py')
    inserted=b"        result['native_backend_events']=backend.events\n"
    ok('one insertion inverse equals exact frozen V1 worker',new.count(inserted)==old.count(inserted)+1 and new.replace(inserted,b'',1)==old and sha(old)=='f0119bd156d9039349071709a2b44907f4fa2e8e9606d93802fa7b4a75154897')
    tree=ast.parse(new);run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run')
    factory=next(n for n in run.body if isinstance(n,ast.Try))
    binding=next(n for n in factory.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Subscript) and isinstance(n.targets[0].slice,ast.Constant) and n.targets[0].slice.value=='native_backend_events')
    make=next(n for n in factory.body if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='make_backend')
    loop=next(n for n in factory.body if isinstance(n,ast.For))
    ok('live capture list bound immediately after backend before first control',binding.lineno==make.lineno+1 and binding.lineno<loop.lineno)
    checkpoint=next(n for n in run.body if isinstance(n,ast.FunctionDef) and n.name=='checkpoint')
    old_run=next(n for n in ast.parse(old).body if isinstance(n,ast.FunctionDef) and n.name=='run')
    old_cp=next(n for n in old_run.body if isinstance(n,ast.FunctionDef) and n.name=='checkpoint')
    ok('native checkpoint function itself unchanged',ast.dump(checkpoint,include_attributes=False)==ast.dump(old_cp,include_attributes=False))
    result={'complete':False};backend=types.SimpleNamespace(events=[]);captures=[]
    ns={'result':result,'backend':backend,'phase':'native_archives','runner':types.SimpleNamespace(observations=[],records=[]),
        'HERE':out,'json_write':lambda p,x:captures.append(json.loads(json.dumps(x)))}
    module=ast.Module(body=[binding,checkpoint],type_ignores=[]);ast.fix_missing_locations(module);exec(compile(module,'extracted-live-checkpoint','exec'),ns)
    ns['checkpoint']()
    ok('initial incomplete checkpoint retains explicit empty backend receipts',captures[-1]['native_backend_events']==[] and captures[-1]['complete'] is False)
    receipt={'kind':'capture','bytes':65536,'cap_bytes':65536,'reader_terminated':True,'owned_close_confirmed':True}
    backend.events.append(receipt);ns['checkpoint']()
    ok('later failed control preserves appended cap and closure receipt',captures[-1]['native_backend_events']==[receipt] and captures[-1]['phase']=='native_archives')
    ok('checkpoint uses the live list rather than an early empty copy',result['native_backend_events'] is backend.events)
    blue=json.loads(raw(out/'job-blueprint.json'));prior=json.loads(raw(WT/'audit/evidence/order-native-release-compact-sol-v1/job-blueprint.json'))
    changed=[];total=0
    for r in blue['inputs']:
        b=raw(Path(blue['workspace_bases'][r['workspace']])/r['path']);total+=len(b)
        assert len(b)==r['bytes'] and sha(b)==r['sha256']
        if r!=next(q for q in prior['inputs'] if q['target']==r['target']):changed.append(r['target'])
    ok('final20 exact payload refs bind under source-read cap',len(blue['inputs'])==20 and total<4194304,payload_bytes=total)
    ok('only backend worker and prereg inputs differ',set(changed)=={'order_release_backend.py','worker.py','prereg.json'})
    ok('all eight source refs and worker input hashes rebind',len(blue['science']['host_tool_vm_memory_boundary']['source_refs'])==8 and all(next(q for q in blue['inputs'] if q['target']==r['target'])==r for r in blue['science']['host_tool_vm_memory_boundary']['source_refs']) and all(blue['science']['worker_input_sha256'][r['target']]==r['sha256'] for r in blue['inputs']))
    ok('native limits/retention/exports/controls/scientific predictions unchanged',blue['science']['task_native_limits']==prior['science']['task_native_limits'] and blue['science']['compact_retention']==prior['science']['compact_retention'] and blue['exports']==prior['exports'] and blue['max_export_bytes']==prior['max_export_bytes'] and blue['expected']==prior['expected'] and blue['controls'][0]==prior['controls'][0])
    for r in blue['runtime_refs']+[blue['policy_ref']]:
        b=raw(Path(blue['workspace_bases']['canonical'])/r['path']);assert sha(b)==r['sha256'] and len(b)==r['bytes']
    ok('four current runtime roles and policy hash bind without loading',len(blue['runtime_refs'])==4)
    for name in ('order_release_backend_v2.py','order_native_release_worker_v2.py','prepare_order_native_release_v2.py','check_order_native_release_capture_v2.py','check_order_native_release_checkpoint_v2.py'):ast.parse(raw(WT/'tools/cloud_jobs'/name))
    ok('five safe changed source files syntax valid',True)
    spec=importlib.util.spec_from_file_location('inert_source_prepare',WT/'tools/cloud_jobs/prepare_order_native_release_v2.py');prep=importlib.util.module_from_spec(spec);spec.loader.exec_module(prep)
    fresh=out/'check-fixtures/reprepared';prep.prepare(WT,fresh)
    projected=json.loads(raw(fresh/'job-blueprint.json'))
    for r in projected['inputs']+projected['controls']:
        if r['target']=='prereg.json':r['path']=str((out/'prereg.json').relative_to(WT))
    ok('new source-only preparer reproduces exact final blueprint',projected==blue)
    ok('no execution/adoption and all five gates pending',blue['operational_admission'] is False and blue['actual_calls']==0 and json.loads(raw(out/'prereg.json'))['all_five_gates']=='pending')
    with (out/'checkpoint-and-final-joins.json').open('x') as f:f.write(json.dumps({'status':'PASS','count':len(rows),'checks':rows,'actual_calls':0,'prior_reader_checks':'33 first-run actual-method checks reused; final five metadata assertions superseded by these joins after one worker insertion. Reader source unchanged.','limits':{'as_bytes':134217728,'cpu_seconds':5,'wall_seconds':18,'affinity_cpus':1}},sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':'PASS','count':len(rows),'actual_calls':0}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--packet',type=Path,required=True);a=p.parse_args();check(a.packet.resolve())
