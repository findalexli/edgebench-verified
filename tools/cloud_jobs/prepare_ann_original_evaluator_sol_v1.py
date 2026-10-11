"""Freeze two fresh-container original ANN audit jobs; never launch them."""
from pathlib import Path
import ast
import copy
import hashlib
import json
import os
import resource
import signal

resource.setrlimit(resource.RLIMIT_AS,(128 << 20,)*2)
resource.setrlimit(resource.RLIMIT_CPU,(5,)*2)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))}); signal.alarm(18)
HERE = Path(__file__).resolve().parent
WORKTREE = HERE.parents[1]
WORKSPACE = WORKTREE.parents[2]
CANONICAL = WORKSPACE/'edgebenchverified'
OUT = WORKTREE/'audit/evidence/ann-original-evaluator-execution-sol-v1'
BASE = WORKTREE/'audit/evidence/ann-original-evaluator-sol-v1/judge'
total = 0


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path,cap=1048576):
    global total
    assert not any(p.is_symlink() for p in (path,*path.parents)) and path.stat().st_size <= cap
    raw = path.read_bytes(); total += len(raw); assert total <= 4194304
    return raw


def write(path,value):
    raw = value if isinstance(value,bytes) else value.encode() if isinstance(value,str) else canonical(value)+b'\n'
    assert len(raw) <= 1048576
    path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(raw)


def ref(path,target=None):
    raw = read(path)
    row = {'path':str(path.relative_to(WORKSPACE)),'bytes':len(raw),'sha256':sha(raw)}
    if target:
        row['target'] = target
    return row


def replace_function(source,name,replacement):
    node = next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name == name)
    lines = source.splitlines(keepends=True)
    return ''.join(lines[:node.lineno-1])+replacement.strip()+'\n'+''.join(lines[node.end_lineno:])


old_path = HERE/'ann_original_identity_worker_sol_v1.py'
old = read(old_path).decode()
assert sha(old.encode()) == '22c64ef335cc4ba6c68260bab1cadc69d24b045ac9f2e7f2faa64afa0ba5ac59'
worker = old.replace('Small ANN scientific worker','Original ANN evaluator scientific worker')
worker = worker.replace('ann_identity_token','ann_original_evaluator_token')
worker = worker.replace('ANN_INSTALLED_IDENTITY_CENSUS_COMPLETE_PENDING_TASK_REVIEW','ANN_ORIGINAL_EVALUATOR_AUDIT_COMPLETE_PENDING_TASK_REVIEW')
worker = worker.replace('inspect_identity.py','eval_original.py').replace('identity-plan.json','evaluator-plan.json')
worker = replace_function(worker,'native_args',r'''
def native_args(root,output,plan,token):
    for path in (root,output):
        need(not any(c in str(path) for c in (',','\n','\r')), 'mount_ambiguity')
    custom = '/home/workspace/ann-benchmarks/ann_benchmarks/algorithms/custom/'
    return ['create','--label',OWNER+'='+token,'--network','none','--cpus','1','--memory','2g','--memory-swap','2g',
            '--pids-limit','64','--user','0:0','--cap-drop','ALL','--security-opt','no-new-privileges',
            '--no-healthcheck','--log-driver','none','--ulimit','core=0','--ulimit','nofile=128:128',
            '--ulimit','fsize=1073741824:1073741824','--ulimit','cpu=900:900','--workdir','/audit',
            '--env','OMP_NUM_THREADS=1','--env','OPENBLAS_NUM_THREADS=1','--env','MKL_NUM_THREADS=1','--env','NUMEXPR_NUM_THREADS=1',
            '--env','PYTHONDONTWRITEBYTECODE=1','--env','HDF5_PLUGIN_PRELOAD=::','--env','HDF5_PLUGIN_PATH=/audit/no-plugins',
            '--mount','type=bind,source='+str(root/'eval_original.py')+',target=/audit/eval_original.py,readonly',
            '--mount','type=bind,source='+str(root/'evaluator-plan.json')+',target=/audit/evaluator-plan.json,readonly',
            '--mount','type=bind,source='+str(root/'declared-module.py')+',target='+custom+'module.py,readonly',
            '--mount','type=bind,source='+str(root/'declared-config.yml')+',target='+custom+'config.yml,readonly',
            '--mount','type=bind,source='+str(output)+',target=/audit-output',
            '--entrypoint','/usr/local/bin/python3',plan['image']['config_id'],'-I','-B','/audit/eval_original.py']
''')
worker = replace_function(worker,'native_projection','''
def native_projection(value):
    # Same pinned authored schema on host and native side; no acquired code import.
    from eval_original import project
    return project(value)
''')
worker = worker.replace("{'worker.py', 'common.py', 'eval_original.py', 'evaluator-plan.json'}",
                        "{'worker.py', 'common.py', 'eval_original.py', 'evaluator-plan.json', 'declared-module.py', 'declared-config.yml'}")
worker = worker.replace("common.DOCKER + ['start', '-a', cid], 185)","common.DOCKER + ['start', '-a', cid], 905)")
worker = worker.replace("result['status'] = STATUS\n", "result['original_evaluator_executed'] = True\n        result['status'] = STATUS\n",1)
worker = worker.replace("        result['elapsed_seconds'] = round(time.monotonic() - start, 6)",
    "        if result['native'] is not None:\n            result['original_evaluator_executed'] = result['native']['original_evaluator_executed']\n        result['elapsed_seconds'] = round(time.monotonic() - start, 6)")
assert '--read-only' not in worker and '--tmpfs' not in worker and 'eval_original.py' in worker
compile(worker,'authored_worker','exec')
write(HERE/'ann_original_evaluator_worker_sol_v1.py',worker)
for name in ('ann_original_evaluator_sol_v1.py','ann_declared_flat_control_sol_v1.py'):
    compile(read(HERE/name),name,'exec')

old_plan = json.loads(read(BASE/'identity-plan.json'))
old_job = json.loads(read(BASE/'packet/job.json'))
old_grant = json.loads(read(BASE/'packet/grant-template.json'))
workerref = ref(HERE/'ann_original_evaluator_worker_sol_v1.py','worker.py')
nativeref = ref(HERE/'ann_original_evaluator_sol_v1.py','eval_original.py')
moduleref = ref(HERE/'ann_declared_flat_control_sol_v1.py','declared-module.py')
configref = ref(HERE/'ann_declared_flat_control_sol_v1.yml','declared-config.yml')
common = next(row for row in old_job['inputs'] if row['target'] == 'common.py')
runtime = next(row for row in old_job['inputs'] if row['target'] == 'experiment_runner.py')
for row in (common,runtime):
    assert ref(WORKSPACE/row['path'])['sha256'] == row['sha256']
registry = [row for row in old_job['inputs'] if row['target'] in {'judge-manifest.json','judge-config.json'}]
source_evaluator = WORKSPACE/'work/task-sources/cloud-exports/merged/ann_vector_search_qps/tmp/eval_ann_search.py'
evraw = read(source_evaluator,65536)
assert sha(evraw) == 'cfc64011510f2a556f933b9e79de8d77788d4de48e68b9cfb61ead946a57249d'
prereg = {'schema_version':1,'experiment':'Two fresh-container repeats of unchanged original ANN evaluator with declared audit submission',
    'positive':'Authored Custom(flat): FAISS IndexFlatL2, one thread, actual train/test vectors, no labels or timer hooks; expect OK positive raw-times QPS and recall >=.95.',
    'negative':'Authored Custom(empty): real finite dot products then no candidates; full 10K padded output; expect WA0, recall0; no timer or truth access.',
    'counts':{'original_evaluator_commands_per_job':1,'configurations_per_job':2,'query_rows_per_configuration':10000,'fresh_container_jobs':2},
    'hypotheses':['Preserving pinned image /tmp reveals byte-identical original evaluator; no copied replacement.',
                  'Whole original command produces both full-shape artifacts, scores flat positive and empty negative, restores GT metadata and removes backup.',
                  'Two independent fresh containers yield same statuses/recall with naturally variable raw-times QPS; no predetermined QPS claim.'],
    'alternative_outcomes':{'source_or_initial_state':'Typed preparation failure; do not reconstruct evaluator or infer upstream defect.',
      'audit_timeout_or_oom':'Incomplete under stricter audit envelope; not original 7200s/7800s TLE and not benchmark invalidity.',
      'partial_or_missing_results':'Incomplete whole-evaluator observation; no full-query or task acceptance.',
      'flat_rejected_or_empty_accepted':'Actual contrary result retained for independent review, no code/timer/GT patch.'},
    'reused_evidence':{'accepted_labels_root_sha256':'fe48455c26f0d322125e6ed9ce146033b89ee0b99475e1188abeec371c23ed71',
      'v41_dependencies_and_11_sources_sha256':'364c7cc2dc65cee5cdaf7844d5f8cf258ff0f656599860e8f0d8f7af3a1a3fe6'},
    'mutations':'Original evaluator deletes/recreates HDF5 neighbors and writes /tmp backup; post-file byte identity is not asserted; reset by fresh pinned image container each job.',
    'privacy':'Native raw stdout/result HDF5/features/IDs/labels remain inside container; only fixed markers, shapes, raw-times aggregates and source identities exported.',
    'limits':'Private auditor authored control performance only, no installed original solver or holdout/model-performance/task certification; all five gates remain pending.',
    'operational_admission':False}
write(OUT/'hypotheses-before-controls.json',prereg)
preregref = ref(OUT/'hypotheses-before-controls.json','hypotheses-before-controls.json')
bindings = []
for repeat in (1,2):
    dest = OUT/('repeat-'+str(repeat))
    plan = {'schema_version':1,'task_id':'ann_vector_search_qps','repeat':repeat,'image':old_plan['image'],
      'eval_cmd':'cd /home/workspace/ann-benchmarks && python3 /tmp/eval_ann_search.py',
      'data_path':'/home/workspace/ann-benchmarks/data/sift-128-euclidean.hdf5','accepted_data_bytes':525128288,
      'source_bindings':{'evaluator':{'bytes':len(evraw),'sha256':sha(evraw)},
         'module':{'bytes':moduleref['bytes'],'sha256':moduleref['sha256']},'config':{'bytes':configref['bytes'],'sha256':configref['sha256']}},
      'caps':{'native_as_bytes':3221225472,'native_cpu_seconds':900,'native_wall_seconds':900,'command_audit_wall_seconds':850,
         'native_file_bytes':1073741824,'container_cpus':1,'container_memory_mib':2048,'native_network':'none','container_read_only':False,
         'original_inner_timeout_seconds':7200,'original_task_timeout_seconds':7800,'log_bytes':1048576,'summary_bytes':32768},
      'original_tmp_preserved':True,'fresh_container_per_repeat':True,'GT_content_reread_by_audit_driver':False,
      'operational_admission':False,'submission_kind':'declared_authored_audit_flat_and_empty'}
    write(dest/'evaluator-plan.json',plan)
    planref = ref(dest/'evaluator-plan.json','evaluator-plan.json')
    controls = [planref,preregref,nativeref,moduleref,configref]
    jobid = 'deterministic-ann-original-repeat'+str(repeat)+'-'+sha(canonical([workerref,nativeref,planref,moduleref,configref]))[:16]
    config = {'job_id':jobid,'run_token':sha(jobid.encode())[:32],'input_files':
      {row['target']:row['sha256'] for row in (workerref,nativeref,planref,moduleref,configref,common)},'private_auditor_access':True}
    write(dest/'worker-config.json',config)
    job = copy.deepcopy(old_job); job['job_id'] = jobid
    science = job['science']; science.update(job_id=jobid,controls_sha256=sha(canonical(controls)))
    boundary = science['host_tool_vm_memory_boundary']
    boundary.update(task_resource_regime='ann_original_evaluator_v1',
      scope='Unchanged original ANN evaluator with declared authored flat/empty controls, fresh pinned writable judge container; private auditor only.',
      inspector_limits={'as_bytes':3221225472,'cpu_seconds':900,'wall_seconds':900,'container_cpus':1,'container_memory_mib':2048,'native_file_bytes':1073741824},
      source_refs=[workerref,nativeref,planref,moduleref,configref]+registry)
    write(dest/'experiment.json',canonical(science))
    job['inputs'] = [workerref,nativeref,planref,moduleref,configref,preregref,common,ref(dest/'worker-config.json','worker-config.json')]+registry+[runtime,ref(dest/'experiment.json','experiment.json')]
    write(dest/'packet/job.json',job)
    grant = copy.deepcopy(old_grant)
    grant.update(job_id=jobid,job_sha256=sha(canonical(job)),controls=controls,host_tool_vm_memory_boundary=copy.deepcopy(boundary),
      task_resource_exception_job_sha256=sha(canonical(job)),result_status='ANN_ORIGINAL_EVALUATOR_AUDIT_COMPLETE_PENDING_TASK_REVIEW')
    grant['runtime_refs'] = [ref(CANONICAL/'audit/evidence/deterministic-experiment-startup-telemetry-sol-v1/coordinator.py'),
        ref(CANONICAL/'tools/audit_runtime/job_validator.py'),ref(CANONICAL/'audit/evidence/deterministic-experiment-coordinator-sol-v1/experiment_runner.py')]
    grant['runtime_upgrade_pending'] = 'Replace validator ref with differently reviewed exact ANN resource exception; no execution permission from this template.'
    write(dest/'packet/grant-template.json',grant)
    binding = {'job':ref(dest/'packet/job.json'),'job_id':jobid,'canonical_job_sha256':sha(canonical(job)),
      'payload_files':len(job['inputs']),'payload_bytes':sum(row['bytes'] for row in job['inputs']),
      'native_argv_function_source':workerref,'original_eval_cmd':plan['eval_cmd'],'operational_admission':False}
    write(dest/'bindings.json',binding); bindings.append(binding)
write(OUT/'freeze.json',{'schema_version':1,'safe_sources':[workerref,nativeref,moduleref,configref,ref(Path(__file__).resolve())],
    'base_worker':ref(old_path),'maintained_common':common,'maintained_runner':runtime,'jobs':bindings,'operational_admission':False,
    'new_native_calls':0,'work_job_retry':False,'canonical_runtime_mutation':False})
print(json.dumps({'prepared':True,'jobs':bindings,'new_native_calls':0},sort_keys=True))
