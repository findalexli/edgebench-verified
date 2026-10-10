"""Prepare one bounded diagnostic blueprint; no acquired module/tool execution."""
import argparse, ast, hashlib, json, os, resource, signal
from pathlib import Path

def sha(body):return hashlib.sha256(body).hexdigest()
def canonical(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def prepare(workspace,out):
    session=workspace.parents[2];canonical_root=session/'edgebenchverified'
    bases={'workspace':str(workspace),'canonical':str(canonical_root),'session':str(session)}
    def ref(base,path,target=None):
        p=Path(bases[base])/path;assert not p.is_symlink() and p.is_file() and p.stat().st_size<=1048576
        raw=p.read_bytes();value={'workspace':base,'path':path,'bytes':len(raw),'sha256':sha(raw)}
        if target:value['target']=target
        return value
    author=ref('session','work/reviews/jagua-policy-native-join-sol-v1/handoff-v2.json')
    peer=ref('session','work/reviews/jagua-policy-native-join-sol-v1-source-peer-v1/handoff.json')
    assert peer['sha256']=='88ff00dddb37418d2489bfd2e7d1cc56b0643b54f5233e0a4ff0840d937eb2a9'
    evidence=json.loads((session/'work/reviews/jagua-policy-native-join-sol-v1/source-evidence.json').read_bytes())
    installed=[]
    for row in evidence['Rust_source_joins']:
        assert ref('session',row['path'])['sha256']==row['sha256']
        path='/'+row['manifest_container_path']
        installed.extend({'path':p,'bytes':row['bytes'],'sha256':row['sha256']} for p in (path,path.replace('/jagua-rs/','/jagua-rs-ref/',1)))
    retained=session/'work/task-sources/cloud-exports/merged/jagua_nesting_optimization'
    for relative in ('Cargo.toml','Cargo.lock','lbf/Cargo.toml','jagua-rs/Cargo.toml','jagua-rs/src/entities/item.rs','jagua-rs/src/probs/spp/entities/problem.rs','jagua-rs/src/probs/spp/entities/solution.rs'):
        row=ref('session',str((retained/'home/workspace/jagua-rs'/relative).relative_to(session)))
        for root in ('jagua-rs','jagua-rs-ref'):
            p='/home/workspace/'+root+'/'+relative
            if p not in {r['path'] for r in installed}:installed.append({'path':p,'bytes':row['bytes'],'sha256':row['sha256']})
    original=ref('session','work/task-sources/cloud-exports/merged/jagua_nesting_optimization/home/workspace/jagua_task_scorer/evaluate.py')
    assert original['sha256']=='08159f8e3a59648460d8cd352ff3b71908763d9a521b41b95c90ba443f35cbe1'
    installed.append({'path':'/home/workspace/jagua_task_scorer/evaluate.py','bytes':original['bytes'],'sha256':original['sha256']})
    worker=ref('workspace','tools/cloud_jobs/jagua_rust_native_worker.py','worker.py')
    actor=ref('workspace','tools/cloud_jobs/jagua_rust_native_actor.py','native_entry.py')
    arm=ref('workspace','tools/cloud_jobs/jagua_native_optimizer_control.rs','optimizer-arm.rs')
    common=ref('canonical','audit/evidence/graph-installed-data-inspection-controller-sol-v1/runtime/common.py','common.py')
    candidate=ref('session','work/task-repairs/jagua-general-polygon-overlap-sol-v1/evaluate.py','candidate-evaluate.py')
    assert candidate['sha256']=='c12d0c18afb0359cb2a57e5b18475d1b2697f6637c609c0a15f2ca45ceeb805b'
    shape=[[0,.5],[.25,0],[.75,0],[1.00000003,.5],[.75,1],[.25,1],[0,.5]]
    image=json.loads((canonical_root/'audit/evidence/next-order-jagua-native-controls-sol-v1/jagua_nesting_optimization-controls.json').read_bytes())['image']
    controls={'schema':'jagua-rust-correspondence-controls-v1','task_id':'jagua_nesting_optimization','image':image,
        'instance':{'name':'audit_f32_contact_policy_v1','strip_height':4.0,'items':[{'id':0,'demand':2,'shape':{'type':'simple_polygon','data':shape}}]},
        'modes':['contact_decimal_0','gap_margin_0','overlap_margin_0','continuous37_gap'],
        'installed_sources':installed,'candidate_evaluate_sha256':candidate['sha256'],'optimizer_arm_sha256':arm['sha256'],
        'optimizer_original_sha256':'3379b7563cfc5af205d7d7b7fb4ab3cd1d40393b4cff0dde95366473ffa24c96',
        'original_functions':'run_lbf/build_project/write_config/evaluate_case and their subprocess transport remain original source; return observation only, distinct work dirs',
        'reference':'Authored gap-mode optimizer control in original reference project. This is a transport/geometry diagnostic, not the frozen ordinary optimizer benchmark baseline.',
        'expected':'Gap/clear overlap are contrary controls conditional on actual native exports. Decimal contact and37deg export correspondence remain exploratory; all scores/statuses measured, no forced pass.',
        'no_new_task_issue_count_gate_or_certification':True}
    (out/'controls.json').write_bytes(canonical(controls));control=ref('workspace',str((out/'controls.json').relative_to(workspace)),'controls.json')
    prereg={'schema':'jagua-rust-correspondence-prereg-v1','status':'SOURCE_ONLY_UNADMITTED','prior_author':author,'prior_different':peer,
        'fresh_native_family':controls['modes'],'old10native_pairs':'Reused, not rerun','hypothesis':'Original Rust loader/controlled native placements/save/main/export expose actual f32 contour/export differences from represented Python binary64 validation. Original/candidate evaluate_case bytes and caller transport are intact.',
        'falsifiers':['Any source/image identity mismatch','Missing/offline-incompatible installed Cargo or bounded target cache','Build/main/export failure before observed outputs','Gap rejected or clear overlap accepted after independent actual-byte geometry adjudication','Unstarted candidate counted as executed','Export/capture/file/count/storage/time/cancellation bound failure'],
        'geometry_policy':'Represented Python binary64 strict-positive-area versus original Rust f32 centering/simplification/composition/export. CDE feasibility retained separately; no transparent mathematical repair/domain policy approval.',
        'scope':'Three zero-angle modes plus one37-degree wide gap; finite simple hexagon only. No holes/corpus/optimizer performance/full score selection/task/domain/data/rights/version comparability approval.',
        'new_native_actor_regime':'Existing2CPU4GiBVM/180wall remains. New process-capable container1CPU3GiB/pids128, actor3GiBAS/110CPU/108wall,64MiBfile,256MiBexec tmpfs, ordinary bounded target metadata≤2001entries/2GiB perroot. Prior process-denying30s inspector is not reused as execution authority.',
        'capture_limit':'Original subprocess.run capture is preserved and allocated within actor AS; returned log≤64KiB is a post-capture acceptance bound, not a preallocation hard stream cap. Public native.json≤64KiB and exported aggregate≤128KiB. All emitted solution bytes/hash bound; complete actual bytes retained once per root/control family, all later actual solution objects retained with hashes and stable contours.',
        'calls_before_seal':{'native':0,'acquired_helper':0,'provider':0,'auth':0,'model':0},'all_five_gates':'pending'}
    (out/'prereg.json').write_bytes(canonical(prereg));preref=ref('workspace',str((out/'prereg.json').relative_to(workspace)),'prereg.json')
    inputs=[worker,actor,arm,common,candidate,control,preref]
    for row in (worker,actor):ast.parse((workspace/row['path']).read_bytes())
    runtime=[ref('canonical',path) for path in ('tools/audit_runtime/coordinator.py','tools/audit_runtime/job_validator.py','tools/cloud_worker.py','audit/evidence/deterministic-experiment-coordinator-sol-v1/experiment_runner.py')]
    policy=ref('canonical','audit/cloud/resource-policy.json')
    science={'child_argv':['python3','-I','-S','-B','worker.py'],'child_as_bytes':None,'child_cpu_seconds':180,'child_wall_seconds':175,'child_file_bytes':1048576,'capture_bytes':65536,
        'network':'owned_host_public_image_and_wheel_bootstrap','native_network':'none','bootstrap':'Pinned original judge image; no wheel/package/compiler/toolchain/cache installation',
        'control_file_sha256':control['sha256'],'worker_input_sha256':{row['target']:row['sha256'] for row in inputs},
        'host_tool_vm_memory_boundary':{'worker_memory_mib':4096,'source_refs':inputs,'host_cpu_boundary':'inherited180CPU_seconds_one_affinity_CPU','inspector_limits':{'container_cpus':1,'container_memory_mib':3072,'as_bytes':3221225472,'cpu_seconds':110,'wall_seconds':110}},
        'task_native_limits':{'cpus':1,'memory_mib':3072,'as_bytes':3221225472,'cpu_seconds':110,'wall_seconds':110,'pids':128,'output_bytes':65536,'file_bytes':67108864,'exec_tmpfs_bytes':268435456}}
    blueprint={'schema':'jagua-rust-correspondence-job-blueprint-v1','workspace_bases':bases,'operational_admission':False,'actual_calls':0,
        'task_id':'jagua_nesting_optimization','timeout_seconds':180,'exports':['result.json','execution.json'],'max_export_bytes':131072,
        'result_status':'native_finite_controls_completed_pending_review','required_result_fields':['complete','native','original_judge_receipt','container_cleanup','storage_observations','controls_sha256'],
        'inputs':inputs,'controls':[control,preref],'science':science,'runtime_refs':runtime,'policy_ref':policy,
        'root_must_bind':['Different source review and explicit new actor/process/resource/capture regime admission','Byte-preserving canonical staging and current exact runtime/policy','Maintained wrapper/experiment inputs and exact fresh deterministic-16hex job/control/grant identity before image contact','Owned VM close/settlement and unchanged result/export allowlist; no controller or private artifact transfer needed']}
    (out/'job-blueprint.json').write_bytes(canonical(blueprint))
    print(json.dumps({'inputs_before_wrapper':len(inputs),'payload_bytes':sum(row['bytes'] for row in inputs),'modes':4,'native_calls':0}))

if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_AS,(134217728,)*2);resource.setrlimit(resource.RLIMIT_CPU,(5,)*2)
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.alarm(18);os.umask(0o077)
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    workspace=Path(__file__).resolve().parents[2];args.output.mkdir(mode=0o700);prepare(workspace,args.output.resolve())
