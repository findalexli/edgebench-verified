"""Prepare private source/job proposal only; no Docker, SDK, credentials or calls."""
import argparse, ast, hashlib, io, json, os, resource, signal, tarfile
from pathlib import Path

def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(x):return hashlib.sha256(x).hexdigest()

def prepare(root,workspace,out):
    out=out.resolve(); need=lambda v,n:None if v else (_ for _ in ()).throw(ValueError(n))
    need(out.is_relative_to(workspace/'audit/evidence') and not (out/'freeze.json').exists(),'fresh_owned_source_packet')
    out.mkdir(parents=True,exist_ok=True); total=0; inputs=[]
    bases={'workspace':str(workspace),'canonical':str(root)}
    def add(base,path,target):
        nonlocal total
        p=Path(bases[base])/path;need(not p.is_symlink() and p.stat().st_size<=1048576,'source_cap')
        raw=p.read_bytes();total+=len(raw);need(total<=4194304,'local_batch_cap')
        r={'workspace':base,'path':path,'target':target,'bytes':len(raw),'sha256':sha(raw)};inputs.append(r);return r
    previous=json.loads((workspace/'audit/evidence/order-built-image-sol-v1/controls.json').read_bytes())
    installed=json.loads((workspace/'audit/evidence/order-built-image-sol-v1/installed-controls.json').read_bytes())
    controls={'task_id':previous['task_id'],'image':previous['image'],'build':previous['build'],
        'fixtures':{'candidate_checker_sha256':'37e7bae613c314dc251129448f3d98429201ccd4d86278dec9de0de606577bd3'},
        'installed_sources':installed['installed_sources'],'cases':[],'runtime_sources':[],
        'public_oracle_calls_added':0,'regime':'owned-small-Order-native-release-compact-v1'}
    permutation=[1+(997*i+113)%1000 for i in range(1000)]
    for kind,cost,expected,passed,failed in [
        ('legal',924551283677.1221,'9c6418b255564cbe23535f1cad97c872af39013f74672a5d58d84105bb32cc75',5,[]),
        ('wrong-cost',936570450364.9246,'4f3c88fa5264b34f3250ea97ae989cc5d14fce3b074b95d986a9be709c4c6e16',4,['test_final_result_is_valid_permutation_and_cost'])]:
        raw=('final_pai='+','.join(map(str,permutation))+'\nfinal_cost='+repr(cost)+'\nfinal_num=1\n').encode()
        need(len(raw)==3944 and sha(raw)==expected,'accepted_V41_raw_reconstruction')
        (out/(kind+'.txt')).write_bytes(raw)
        add('workspace',str((out/(kind+'.txt')).relative_to(workspace)),kind+'.txt')
        controls['cases'].append({'kind':kind,'target':kind+'.txt','bytes':len(raw),'sha256':sha(raw),'passed':passed,'failed_tests':failed})
    # The exact original fork modules are copied without transformations.
    modules=['sforge/__init__.py','sforge/harness/__init__.py','sforge/harness/constants.py','sforge/harness/task_spec.py',
        'sforge/harness/benchmark.py','sforge/harness/config.py','sforge/harness/run_evaluation.py','sforge/harness/grading.py',
        'sforge/harness/score_rescale.py','sforge/harness/selection.py','sforge/harness/docker_build.py','sforge/harness/dockerfiles.py',
        'sforge/harness/backend/__init__.py','sforge/harness/backend/base.py','sforge/harness/backend/factory.py',
        'sforge/harness/backend/docker_backend.py','sforge/harness/log_parsers/__init__.py','sforge/harness/log_parsers/pytest_v.py',
        'sforge/harness/log_parsers/score_sum.py','sforge/harness/log_parsers/structured_json.py']
    output=io.BytesIO()
    with tarfile.open(fileobj=output,mode='w',format=tarfile.USTAR_FORMAT) as tar:
        for name in modules:
            raw=(workspace/name).read_bytes();total+=len(raw);need(len(raw)<=65536 and total<=4194304,'runtime_module_cap')
            ast.parse(raw); member=tarfile.TarInfo(name);member.size=len(raw);member.mode=0o600;member.mtime=0
            tar.addfile(member,io.BytesIO(raw));controls['runtime_sources'].append({'relative':name,'bytes':len(raw),'sha256':sha(raw)})
    (out/'runtime-sources.tar').write_bytes(output.getvalue())
    runtime=add('workspace',str((out/'runtime-sources.tar').relative_to(workspace)),'runtime-sources.tar')
    for path,target in [('repairs/order-helper-integrity-v1/native/BENCHMARK.yaml','native/BENCHMARK.yaml'),
        ('repairs/order-helper-integrity-v1/native/order_addition_permutation_optimization.json.in','native/task.json.in')]:add('workspace',path,target)
    sources=[]
    for name,target in [('order_native_release_worker.py','worker.py'),('order_release_delta.py','order_release_delta.py'),
        ('order_release_backend.py','order_release_backend.py'),('order_built_image_worker.py','order_built_image_worker.py'),
        ('order_built_image_projection.py','order_built_image_projection.py')]:sources.append(add('workspace','tools/cloud_jobs/'+name,target))
    sources.append(add('canonical','audit/evidence/graph-installed-data-inspection-controller-sol-v1/runtime/common.py','common.py'))
    add('canonical','audit/evidence/order-declared-cli-finite-comparison-sol-v1/upstream_parser_component.py','upstream_parser_component.py')
    generic='audit/evidence/graph-reproduction-preservation-runtime-v2/source/'
    for name in ('pack_delta.py','reconstruct.py','delta_contracts.py'):add('canonical',generic+name,name)
    recipe=json.loads((root/'audit/evidence/order-helper-integrity-native-image-proposal-sol-v1/proposal.json').read_bytes())
    context=Path(recipe['build_recipe']['private_context']);bases['private_context']=str(context)
    for r in controls['build']['context_inputs']:add('private_context',r['relative'],r['target'])
    (out/'controls.json').write_bytes(canonical(controls))
    control=add('workspace',str((out/'controls.json').relative_to(workspace)),'controls.json')
    prereg={'schema':'order-native-release-compact-prereg-v1','status':'SOURCE_ONLY_UNADMITTED','public_oracle_calls_added':0,
        'fixture_reuse':'Exact accepted V41 3944-byte legal/wrong-cost submissions, not fresh science or independent native reproduction.',
        'hypothesis':'The unchanged one-literal checker in a versioned image accepts legal and rejects wrong cost through native archive/grade/rescale/selection; exact same-tested-build config/layer can fit compact bounds and restore.',
        'artifact_limits':{'bundle_bytes':49152,'private_JSON_bytes':81920,'total_exports':131072,'save_stream_bytes':4294967296},
        'stop':'Missing installed tool package, source/pin mismatch, overcap/unsupported save layout, any control mismatch or unconfirmed owned cleanup; no automatic install/retry.',
        'rights':'Private audit artifact only; no publication/distribution authorization.', 'all_five_gates':'pending','actual_calls':0}
    (out/'prereg.json').write_bytes(canonical(prereg))
    prereg_ref=add('workspace',str((out/'prereg.json').relative_to(workspace)),'prereg.json')
    refs=sources+[runtime,control];need(len(refs)==8,'bounded_source_refs')
    science={'child_argv':['python3','-I','-B','worker.py'],'child_as_bytes':None,'child_cpu_seconds':180,'child_file_bytes':1048576,
        'child_wall_seconds':1180,'capture_bytes':65536,'control_file_sha256':control['sha256'],
        'hypothesis_freeze_sha256':prereg_ref['sha256'],
        'worker_input_sha256':{r['target']:r['sha256'] for r in inputs},'network':'owned_host_public_image_and_wheel_bootstrap',
        'native_network':'none','host_tool_vm_memory_boundary':{'worker_memory_mib':4096,'source_refs':refs,
            'host_cpu_boundary':'inherited_180CPU_seconds_one_affinity_CPU',
            'inspector_limits':{'as_bytes':536870912,'cpu_seconds':120,'wall_seconds':180,'container_cpus':1,'container_memory_mib':1024}},
        'task_native_limits':{'as_bytes':536870912,'cpu_seconds':25,'cpus':1,'memory_mib':1024,'pids':64,'wall_seconds':30,'output_bytes':65536},
        'compact_retention':{'bundle_bytes':49152,'private_JSON_bytes':81920,'result_bytes':32768,'execution_reserve_bytes':16384,
            'save_stream_bytes':4294967296,'full_image_or_parent_spool':False,'same_VM_restoration':True}}
    runtime_refs=[]
    for path in ['tools/audit_runtime/coordinator.py','tools/audit_runtime/job_validator.py','tools/cloud_worker.py',
                 'audit/evidence/deterministic-experiment-coordinator-sol-v1/experiment_runner.py']:
        body=(root/path).read_bytes();runtime_refs.append({'path':path,'bytes':len(body),'sha256':sha(body)})
    policy=(root/'audit/cloud/resource-policy.json').read_bytes()
    blueprint={'schema':'order-native-release-source-job-blueprint-v1','status':'UNADMITTED_MIXED_ROOT_SOURCE_TEMPLATE',
        'workspace_bases':bases,'inputs':inputs,'controls':[control,prereg_ref],'science':science,'timeout_seconds':1200,'resource_profile':'small',
        'exports':['result.json','execution.json','artifact.json'],'max_export_bytes':131072,
        'private_export':'artifact.json contains acquired config/checker-layer bodies. Root-admitted private collector must store outside Git/publishable audit, under owned work/task-repairs; public evidence contains hash/size/ref only.',
        'runtime_refs':runtime_refs,'policy_ref':{'path':'audit/cloud/resource-policy.json','bytes':len(policy),'sha256':sha(policy)},
        'expected':['legal native report5/5 score1e-9','wrong-cost4/5 named cost failure scoreNone','native pass_rate_first legal selection',
            'same-tested-build compact identity <=existing export caps','removed tested image absent; restored config/rootfs/installed sources exact'],
        'result_status':'native_finite_controls_completed_pending_review','required_result_fields':['complete','native','original_judge_receipt',
            'derived_judge_receipt','candidate_delta','candidate_delta_pins','restoration','selection','native_backend_events','container_cleanup','image_cleanup','native_alias_cleanup'],
        'automatic_retries':0,'operational_admission':False,'actual_calls':0,
        'root_must_bind':['byte-preserving canonical staging paths','current exact runtime/policy after staging','wrapper/experiment inputs and fresh job/control identity',
            'reviewed existing tool environment; missing Docker/PyYAML is typed setup failure, no automatic package install',
            'tiny separately reviewed private artifact.json collector addition before launch; existing terminal collector filename allowlist does not admit it',
            'fresh different source review and operational grant']}
    need(len(inputs)+2<=32 and sum(r['bytes'] for r in inputs)<=16777216,'maintained_payload_caps')
    (out/'job-blueprint.json').write_bytes(canonical(blueprint))
    print(json.dumps({'inputs_before_wrapper':len(inputs),'payload_bytes':sum(r['bytes'] for r in inputs),'source_read_bytes':total,'actual_calls':0}))

if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_AS,(134217728,)*2);resource.setrlimit(resource.RLIMIT_CPU,(5,)*2)
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.alarm(18);os.umask(0o077)
    parser=argparse.ArgumentParser();parser.add_argument('--canonical-root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();prepare(args.canonical_root.resolve(),Path(__file__).resolve().parents[2],args.output)
