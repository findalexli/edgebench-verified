"""Source-only preparation; mixed workspace refs require root's exact rebinding.

No Docker/provider/SDK/authentication/queue execution. Private controls and all
generated evidence remain in ignored audit/, while Git contains authored code.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import signal

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def read(path,cap=1048576):
    raw=path.read_bytes()
    if len(raw)>cap:raise ValueError('preparation_read_cap')
    return raw

def prepare(canonical_root,workspace,output):
    canonical_root=canonical_root.resolve();workspace=workspace.resolve();output=output.resolve()
    if not output.is_relative_to(workspace/'audit/evidence') or (output/'freeze.json').exists():
        raise ValueError('fresh_ignored_author_packet')
    output.mkdir(parents=True,exist_ok=True)
    total=0
    def load(root,path):
        nonlocal total
        raw=read(root/path);total+=len(raw)
        if total>4*1048576:raise ValueError('preparation_batch_cap')
        return raw
    recipe=json.loads(load(canonical_root,Path('audit/evidence/order-helper-integrity-native-image-proposal-sol-v1/proposal.json')))
    previous=json.loads(load(canonical_root,Path('audit/evidence/order-declared-cli-finite-comparison-sol-v3/candidate-legal/controls.json')))
    old_sha=digest(canonical(previous['fixtures']['permutation']))
    controls=previous
    controls['driver']='order_built_image_fixture.py'
    controls.pop('expected');controls['cases']=[
        {'kind':'legal','expected':{'exit_code':0,'failed_tests':[],'score_presence':True}},
        {'kind':'wrong-cost','expected':{'exit_code':1,'failed_tests':['test_final_result_is_valid_permutation_and_cost'],'score_presence':False}}]
    controls['fixtures']['permutation']=[1+(997*i+113)%1000 for i in range(1000)]
    controls['fixtures']['prior_permutation_sha256']=[old_sha]
    controls['fixtures']['kind']='paired';controls['fixtures']['mode']='built-image'
    context=Path(recipe['build_recipe']['private_context']).resolve()
    roots={'workspace':str(workspace),'canonical':str(canonical_root),'private_context':str(context)}
    controls['build']={'context_inputs':[],'wall_seconds':120,'network':'none','pull':False,
                       'ownership_label_delta':'org.edgebenchverified.job_id=<32hex job token>'}
    inputs=[]
    def add(base,path,target,include=True):
        raw=load(Path(roots[base]),Path(path))
        row={'workspace':base,'path':str(path),'target':target,'bytes':len(raw),'sha256':digest(raw)}
        if include:inputs.append(row)
        return row
    for row in recipe['build_recipe']['private_context_files']:
        path=Path(row['path']).resolve()
        if not path.is_relative_to(context):raise ValueError('private_context_path')
        relative=str(path.relative_to(context));ref=add('private_context',relative,'build/'+relative)
        if ref['bytes']!=row['bytes'] or ref['sha256']!=row['sha256']:raise ValueError('frozen_context_source')
        controls['build']['context_inputs'].append({'relative':relative,'target':ref['target'],
                                                   'bytes':ref['bytes'],'sha256':ref['sha256']})
    installed={k:controls[k] for k in ('task_id','python_version')}
    installed.update(driver='order_built_image_identity.py',fixtures={'purpose':'derived_judge_installed_identity'},
                     installed_sources=[dict(x) for x in controls['installed_sources']],planned_observations=1)
    installed['installed_sources'][0]['sha256']=recipe['checker_overlay']['candidate_sha256']
    installed['installed_sources'].append({'path':'/home/workspace/complex_job_scheduling/cost_complex_cy.cpython-311-x86_64-linux-gnu.so',
        'bytes':86520,'sha256':controls['fixtures']['public_binary_sha256']})
    for filename,value in [('controls.json',controls),('installed-controls.json',installed)]:
        (output/filename).write_bytes(canonical(value))
        add('workspace',str((output/filename).relative_to(workspace)),filename)
    resource_refs=[]
    for filename,target in [
        ('order_built_image_worker.py','worker.py'),
        ('order_built_image_fixture.py','order_built_image_fixture.py'),
        ('order_built_image_projection.py','order_built_image_projection.py'),
        ('order_built_image_identity.py','order_built_image_identity.py')]:
        resource_refs.append(add('workspace','tools/cloud_jobs/'+filename,target))
    for path,target in [
        ('audit/evidence/order-whole-pytest-four-controls-sol-v2/native_entry.py','native_entry.py'),
        ('audit/evidence/graph-installed-data-inspection-controller-sol-v1/runtime/common.py','common.py'),
        ('audit/evidence/next-order-jagua-native-controls-sol-v1/oracles.py','oracles.py'),
        ('audit/evidence/order-declared-cli-finite-comparison-sol-v1/upstream_parser_component.py','upstream_parser_component.py')]:
        resource_refs.append(add('canonical',path,target))
    runner=add('canonical','audit/evidence/deterministic-experiment-coordinator-sol-v1/experiment_runner.py','experiment_runner.py',include=False)
    prereg={'schema':'order-owned-built-image-prereg-v1','status':'SOURCE_ONLY_UNEXECUTED',
        'base':recipe['original_judge'],'original_task':recipe['original_task'],
        'candidate_sha256':recipe['checker_overlay']['candidate_sha256'],
        'accepted_recipe':'729002531535ecb75fb892c8ec79a556a9fd5d7e576c5676e6b09f206d652922',
        'accepted_literal_CLI':'eb75aa25a179f3137999786306d37e6d3890029bbf6057137af0d111c8bf4e13',
        'prior_next_step':'32b46c357e5ba577e23976d01e98d596e98f4b574e6bcd4794b5ad43736bb7e8',
        'fresh_permutation_sha256':digest(canonical(controls['fixtures']['permutation'])),
        'prior_permutation_sha256':old_sha,'preparation_public_api_calls':1,'CLI_runs':2,
        'expected':['legal: exit0, five passes, exact .10f score','wrong-cost: exit1, only named validation failure, no score'],
        'scope':'Built image integration; full native submission/selection harness/corpus/version/domain/data/rights remain pending.',
        'operational_admission':False,'actual_native_provider_auth_build_model_calls':0}
    (output/'prereg.json').write_bytes(canonical(prereg))
    science={'bootstrap':'Exact readonly original judge pull; one frozen COPY build, no package installation',
        'capture_bytes':65536,'child_argv':['python3','-I','-S','-B','worker.py'],'child_as_bytes':None,
        'child_cpu_seconds':180,'child_file_bytes':1048576,'child_wall_seconds':1180,
        'control_file_sha256':digest(canonical(controls)),'hypothesis_freeze_sha256':digest(canonical(prereg)),
        'worker_input_sha256':{x['target']:x['sha256'] for x in inputs if x['target'] not in ('controls.json','experiment_runner.py')},
        'network':'owned_host_public_image_and_wheel_bootstrap','native_network':'none',
        'host_tool_vm_memory_boundary':{'worker_memory_mib':4096,'host_cpu_boundary':'inherited_180CPU_seconds_one_affinity_CPU',
            'inspector_limits':{'as_bytes':536870912,'cpu_seconds':120,'wall_seconds':180,'container_cpus':1,'container_memory_mib':1024},
            'source_refs':resource_refs},
        'task_native_limits':{'as_bytes':536870912,'cpu_seconds':25,'cpus':1,'memory_mib':1024,'output_bytes':65536,'pids':64,'wall_seconds':30},
        'build_limits':{'wall_seconds':120,'network':'none','context_files':3,'context_bytes':6665,
            'memory_boundary':'owned 4GiB VM; no separate daemon aggregate-memory guarantee','sampled_growth_stop_bytes':8*1024**3}}
    blueprint={'schema':'order-source-job-rebinding-blueprint-v1','status':'PENDING_ROOT_BYTE_PRESERVING_STAGING',
        'workspace_bases':roots,'inputs':inputs,'science':science,'timeout_seconds':1200,'resource_profile':'small',
        'automatic_retries':0,'exports':['result.json','execution.json'],'max_export_bytes':131072,
        'result_status':'native_finite_controls_completed_pending_review',
        'required_result_fields':['complete','native','original_judge_receipt','derived_judge_receipt','inspection_receipt',
            'image_cleanup','container_cleanup','storage_observations','controls_sha256'],
        'root_must_bind':['canonical relative paths after copying exact bytes','fresh job_id and controls_sha256',
            'science source_refs with canonical paths','maintained prepare adds wrapper_ref and experiment.json',
            'new deadline validator runtime pin','exact job hash and operational grant'],
        'wrapper_ref':runner,'operational_admission':False,'actual_calls':0}
    (output/'job-blueprint.json').write_bytes(canonical(blueprint))
    print(json.dumps({'payload_inputs':len(inputs),'payload_bytes':sum(x['bytes'] for x in inputs),
                      'preparation_source_bytes':total,'native_calls':0,'job_blueprint':str(output/'job-blueprint.json')}))

if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_AS,(134217728,134217728));resource.setrlimit(resource.RLIMIT_CPU,(5,5))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});signal.alarm(18)
    parser=argparse.ArgumentParser();parser.add_argument('--canonical-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=Path('audit/evidence/order-built-image-sol-v1'))
    args=parser.parse_args();prepare(args.canonical_root,Path(__file__).resolve().parents[2],args.output)
