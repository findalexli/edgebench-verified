"""Bind a small ANN prerequisite job to the maintained runner; never launch it."""
from pathlib import Path
import ast
import copy
import hashlib
import json
import os
import resource
import signal

resource.setrlimit(resource.RLIMIT_AS, (128 << 20,) * 2)
resource.setrlimit(resource.RLIMIT_CPU, (5,) * 2)
os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
signal.alarm(18)

HERE = Path(__file__).resolve().parent
WORKTREE = HERE.parents[1]
WORKSPACE = WORKTREE.parents[2]
CANONICAL = WORKSPACE / 'edgebenchverified'
OUT = WORKTREE / 'audit/evidence/ann-original-evaluator-sol-v1'
BASE = CANONICAL / 'audit/evidence/ann-installed-data-inspection-sol-v2'
RETAINED = WORKSPACE / 'work/task-sources/cloud-exports/merged/ann_vector_search_qps'
total = 0


def read(path, cap=1048576):
    global total
    assert not path.is_symlink() and path.stat().st_size <= cap
    value = path.read_bytes()
    total += len(value)
    assert total <= 4194304
    return value


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = value if isinstance(value, bytes) else value.encode() if isinstance(value, str) else canon(value) + b'\n'
    assert len(raw) <= 1048576
    path.write_bytes(raw)


def ref(path, target=None):
    raw = read(path)
    # Coordinator path validation requires relative paths beneath one explicit workspace base.
    row = {'path': str(path.relative_to(WORKSPACE)), 'bytes': len(raw), 'sha256': sha(raw)}
    if target:
        row['target'] = target
    return row


def replace_function(source, name, replacement):
    tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    lines = source.splitlines(keepends=True)
    return ''.join(lines[:node.lineno - 1]) + replacement.strip() + '\n' + ''.join(lines[node.end_lineno:])


old_worker = read(BASE / 'worker.py').decode()
assert sha(old_worker.encode()) == '7e8706f0e88957fc43f44680d17b6a600f24c9ce8f2504af3246456f94b12728'
worker = old_worker.replace("OWNER = 'org.edgebenchverified.ann_data_token'", "OWNER = 'org.edgebenchverified.ann_identity_token'")
worker = worker.replace("STATUS = 'ANN_INSTALLED_DATA_INSPECTION_COMPLETE_PENDING_TASK_REVIEW'",
                        "STATUS = 'ANN_INSTALLED_IDENTITY_CENSUS_COMPLETE_PENDING_TASK_REVIEW'")
worker = worker.replace('inspect_data.py', 'inspect_identity.py').replace('inspection-plan.json', 'identity-plan.json')
worker = worker.replace("plan['judge']", "plan['image']")
worker = worker.replace("value['default_user'] == '',", "value['default_user'] == plan['image']['default_user'],")
worker = worker.replace("'default_user': ''}", "'default_user': plan['image']['default_user']}")
worker = worker.replace("plan['image']['config_id'], '-I', '-S', '-B'", "plan['image']['config_id'], '-I', '-B'")
worker = worker.replace("'--mount', 'type=bind,source=' + str(output) + ',target=/audit-output',",
                        "'--mount', 'type=bind,source=' + str(root / 'identity-plan.json') + ',target=/audit/identity-plan.json,readonly',\n            '--mount', 'type=bind,source=' + str(output) + ',target=/audit-output',")
worker = worker.replace("'solver_holdout_performance': False, 'all_five_gates'", "'solver_holdout_performance': False, 'original_evaluator_executed': False, 'all_five_gates'")
projection = '''
def native_projection(value):
    allowed = {'schema_version','complete','phase','reason','failure_class','source_records','dependencies','data_stat',
               'faiss_authored_control','raw_source_exported','raw_data_exported','corpus_body_read','original_evaluator_executed',
               'original_solver_executed','private_custom_code_exported','performance_measured','acquired_custom_code_executed',
               'image_role','python_version','source_bytes_read'}
    flags = {'raw_source_exported','raw_data_exported','corpus_body_read','original_evaluator_executed','original_solver_executed',
             'private_custom_code_exported','performance_measured','acquired_custom_code_executed'}
    need(type(value) is dict and set(value) <= allowed and len(canonical(value)) <= CAP and
         type(value.get('schema_version')) is int and value['schema_version'] == 1 and type(value.get('complete')) is bool and
         all(value.get(k) is False for k in flags), 'native_scope')
    need(value.get('phase') in {'startup','source_census','data_stat','dependencies','authored_faiss_workload','completed'} and
         value.get('reason') in {None,'linked_source','source_cap_or_type','source_changed','source_total_cap','summary_cap',
                                'native_deadline','version_format','bounded_census_failed'} and
         value.get('failure_class') in {None,'ImportError','ModuleNotFoundError','MemoryError','OSError','ValueError','TimeoutError','other_error'}, 'native_failure')
    need('image_role' not in value or value['image_role'] in {'work','judge'}, 'native_role')
    need('python_version' not in value or type(value['python_version']) is str and re.fullmatch(r'[0-9]+\\.[0-9]+\\.[0-9]+',value['python_version']), 'native_python')
    need('source_bytes_read' not in value or type(value['source_bytes_read']) is int and 0 <= value['source_bytes_read'] <= 1048576, 'native_source_bytes')
    roles = {'evaluator','run','main','runner','definitions','results','datasets','distance','base','constants','logging',
             'custom_module','custom_config','custom_init'}
    records = value.get('source_records')
    need(type(records) is dict and set(records) <= roles, 'native_records')
    row_keys = {'status','bytes','sha256','retained_source_matches','reason','text_status','line_count','custom_constructor_literal_present',
                'custom_module_literal_present','config_parsed_or_imported','syntax_status','ast_node_count','custom_class_count',
                'fit_defined','query_defined','known_imports','other_import_count','acquired_code_executed'}
    booleans = {'retained_source_matches','custom_constructor_literal_present','custom_module_literal_present','fit_defined','query_defined'}
    integers = {'bytes','line_count','ast_node_count','custom_class_count','other_import_count'}
    for role,row in records.items():
        need(type(row) is dict and set(row) <= row_keys and row.get('status') in {'read','missing','unsupported'}, 'native_record')
        need(all(type(v) is bool for k,v in row.items() if k in booleans) and
             all(type(v) is int and 0 <= v <= 65536 for k,v in row.items() if k in integers), 'native_record_scalars')
        need('sha256' not in row or type(row['sha256']) is str and re.fullmatch(r'[0-9a-f]{64}',row['sha256']), 'native_source_hash')
        need('acquired_code_executed' not in row or row['acquired_code_executed'] is False, 'native_unexecuted_source')
        need('config_parsed_or_imported' not in row or row['config_parsed_or_imported'] is False, 'native_unparsed_config')
        need(row.get('text_status') in {None,'utf8','invalid_utf8'} and row.get('syntax_status') in {None,'valid','invalid','node_cap'} and
             row.get('reason') in {None,'linked_source','source_cap_or_type','source_changed','source_total_cap'}, 'native_record_codes')
        if row['status'] == 'read':
            need({'bytes','sha256'} <= set(row), 'native_read_identity')
        elif row['status'] == 'missing':
            need(set(row) == {'status'}, 'native_missing')
        else:
            need(set(row) == {'status','reason'} and row['reason'] is not None, 'native_unsupported')
        if 'known_imports' in row:
            known = {'numpy','faiss','ann_benchmarks','time','os','sys','h5py','scipy','sklearn'}
            need(type(row['known_imports']) is dict and set(row['known_imports']) == known and
                 all(type(v) is bool for v in row['known_imports'].values()), 'native_import_flags')
    deps = value.get('dependencies')
    need(type(deps) is dict and set(deps) <= {'numpy','h5py','faiss','docker','psutil','colors','yaml'}, 'native_dependencies')
    for row in deps.values():
        need(type(row) is dict and type(row.get('imported')) is bool and
             (set(row) == {'imported','version'} and row['imported'] and type(row['version']) is str and
              re.fullmatch(r'[0-9A-Za-z.+_-]{1,80}',row['version']) or
              set(row) == {'imported','failure_class'} and not row['imported'] and
              row['failure_class'] in {'ImportError','ModuleNotFoundError','MemoryError','OSError','ValueError','TimeoutError','other_error'}), 'native_dependency')
    data = value.get('data_stat')
    need(type(data) is dict and set(data) <= {'present','regular','symlink','bytes','prior_accepted_size_matches','body_read','sha256_measured'} and
         all(type(v) is bool for k,v in data.items() if k != 'bytes') and
         ('bytes' not in data or type(data['bytes']) is int and 0 <= data['bytes'] < 2**63) and
         data.get('body_read',False) is False and data.get('sha256_measured',False) is False, 'native_data_stat')
    control = value.get('faiss_authored_control')
    if control is not None:
        need(type(control) is dict and type(control.get('started')) is bool and type(control.get('completed')) is bool, 'native_control')
        if control['completed']:
            need(set(control) == {'started','completed','correct_ids_and_squared_distances','farther_negative_rejected','train_points',
                 'queries','dimension','threads','actual_dataset_used','performance_measured'} and control['started'] is True and
                 type(control['correct_ids_and_squared_distances']) is bool and type(control['farther_negative_rejected']) is bool and
                 all(type(control[k]) is int for k in ('train_points','queries','dimension','threads')) and
                 [control[k] for k in ('train_points','queries','dimension','threads')] == [3,1,2,1] and
                 control['actual_dataset_used'] is False and control['performance_measured'] is False, 'native_control_complete')
        elif control['started']:
            need(set(control) == {'started','completed','failure_class'} and control['failure_class'] in
                 {'ImportError','ModuleNotFoundError','MemoryError','OSError','ValueError','TimeoutError','other_error'}, 'native_control_failure')
        else:
            need(set(control) == {'started','completed','reason'} and control['reason'] == 'dependency_unavailable', 'native_control_unstarted')
    if value['complete']:
        need(value['phase'] == 'completed' and value['reason'] is None and value['failure_class'] is None and
             set(records) == roles and set(deps) == {'numpy','h5py','faiss','docker','psutil','colors','yaml'} and
             {'image_role','python_version','source_bytes_read'} <= set(value) and data.get('present') in {True,False} and
             control is not None, 'native_census_complete')
    return value
'''
worker = replace_function(worker, 'native_projection', projection)
assert "plan['judge']" not in worker and '-I\', \'-S' not in worker
write(HERE / 'ann_original_identity_worker_sol_v1.py', worker)
compile(worker, 'authored_worker', 'exec')
native = HERE / 'ann_original_identity_sol_v1.py'
compile(read(native), 'authored_native', 'exec')

source_names = {'evaluator': 'tmp/eval_ann_search.py', 'run': 'home/workspace/ann-benchmarks/run.py',
    **{role: 'home/workspace/ann-benchmarks/ann_benchmarks/' + filename for role,filename in {
      'main':'main.py','runner':'runner.py','definitions':'definitions.py','results':'results.py','datasets':'datasets.py',
      'distance':'distance.py','base':'algorithms/base/module.py','constants':'constants.py',
      'custom_module':'algorithms/custom/module.py','custom_config':'algorithms/custom/config.yml',
      'custom_init':'algorithms/custom/__init__.py'}.items()}, 'logging':'home/workspace/ann-benchmarks/logging.conf'}
paths = {}
for role,relative in source_names.items():
    record = {'path': '/' + relative, 'kind': 'python' if role == 'custom_module' else 'config' if role == 'custom_config' else 'identity'}
    path = RETAINED / relative
    if path.is_file():
        record['expected_sha256'] = sha(read(path,65536))
    paths[role] = record

prior_plan = json.loads(read(CANONICAL / 'audit/evidence/ann-installed-data-inspection-sol-v1/inspection-plan.json'))
prior_job = json.loads(read(BASE / 'job-proposal/job.json'))
prior_grant = json.loads(read(BASE / 'job-proposal/grant-template.json'))
common = next(x for x in prior_job['inputs'] if x['target'] == 'common.py')
runtime = next(x for x in prior_job['inputs'] if x['target'] == 'experiment_runner.py')
for row in (common,runtime):
    path = CANONICAL / row['path']
    assert ref(path)['sha256'] == row['sha256']
    row['path'] = str(path.relative_to(WORKSPACE))

for role in ('judge','work'):
    dest = OUT / role
    image = prior_plan['judge'] if role == 'judge' else prior_plan['work_context_only']
    plan = {'schema_version':1,'task_id':'ann_vector_search_qps','image_role':role,
        'image':{k:image[k] for k in ('reference','config_id','default_user')}, 'source_paths':paths,
        'data_path':str(Path('/home/workspace/ann-benchmarks/data/sift-128-euclidean.hdf5')),
        'privacy':'Fixed source identities/structural flags, versions, file stat and authored tiny-control Booleans only. No custom code/config, raw logs, features, IDs or labels.',
        'operational_admission':False,'corpus_body_read':False,'original_evaluator_executed':False,
        'caps':{'source_file_bytes':65536,'total_source_bytes':1048576,'summary_bytes':32768,
                'native_wall_seconds':180,'native_cpu_seconds':120,'native_as_bytes':536870912,
                'container_cpus':1,'container_memory_mib':1024,'container_read_only':True,'native_network':'none'}}
    write(dest / 'identity-plan.json',plan)
    prereg = {'schema_version':1,'image_role':role,'experiment':'Fixed installed original-command dependency census only',
        'questions':['Are fixed original command/framework sources byte-identical to retained selected sources?',
                    'Are Custom module/config installed, and do literal/AST structural prerequisites exist?',
                    'Do installed numerical/I/O/runner dependencies import and does FAISS perform an independent tiny exact search?'],
        'hypotheses':['Custom source/config may be installed despite filtered retained-export gap.',
                      'A failed import or source mismatch is a preparation observation, not an upstream defect.',
                      'Completed census may include missing or unavailable prerequisites; it is not a passing whole-task gate.'],
        'contrary_controls':['Omitting nearer authored FAISS point produces squared distance89 rather than20.',
                            'Authored missing/malformed/over-cap source census records do not assert installed global absence.'],
        'counts':'Zero original evaluator, solver, real query or corpus label calls; one tiny authored query if installed FAISS works.',
        'reused_accepted_full10k_labels':{'path':str(CANONICAL/'audit/evidence/ann-gemm-label-full10k-sol-v1-root-result-review/root-result-review.json'),
            'sha256':'fe48455c26f0d322125e6ed9ce146033b89ee0b99475e1188abeec371c23ed71'},
        'follow_up':'Separate source-informed legitimate authored FAISS IndexFlatL2 submission; unchanged original evaluator full1M/10K; repeatability jobs frozen separately with reviewed memory/time envelopes.',
        'operational_admission':False}
    write(dest/'hypotheses-before-controls.json',prereg)
    workerref = ref(HERE/'ann_original_identity_worker_sol_v1.py','worker.py')
    nativeref = ref(native,'inspect_identity.py')
    planref = ref(dest/'identity-plan.json','identity-plan.json')
    controlref = ref(dest/'hypotheses-before-controls.json','hypotheses-before-controls.json')
    controls = [planref,controlref,nativeref]
    jobid = 'deterministic-ann-identity-'+role+'-'+sha(canon([workerref,nativeref,planref]))[:16]
    config = {'input_files':{r['target']:r['sha256'] for r in (workerref,nativeref,planref,common)},
              'job_id':jobid,'run_token':sha(jobid.encode())[:32],'private_auditor_access':True}
    write(dest/'worker-config.json',config)
    job = copy.deepcopy(prior_job)
    job.update(job_id=jobid)
    science = job['science']
    science.update(job_id=jobid,controls_sha256=sha(canon(controls)))
    boundary = science['host_tool_vm_memory_boundary']
    boundary['scope'] = 'Fixed ANN '+role+' source/runtime prerequisite census only; no original evaluator/solver or corpus bodies.'
    boundary['source_refs'] = [workerref,nativeref,planref] + [
        {**r,'path':str((CANONICAL/r['path']).relative_to(WORKSPACE))} for r in prior_job['inputs'] if r['target'] in
        {'judge-manifest.json','judge-config.json','work-manifest.json','work-config.json'}]
    write(dest/'experiment.json',canon(science))
    job['inputs'] = [workerref,nativeref,planref,controlref,common,ref(dest/'worker-config.json','worker-config.json')] + \
        [{**r,'path':str((CANONICAL/r['path']).relative_to(WORKSPACE))} for r in prior_job['inputs'] if r['target'] in
         {'judge-manifest.json','judge-config.json','work-manifest.json','work-config.json'}] + [runtime,ref(dest/'experiment.json','experiment.json')]
    write(dest/'packet/job.json',job)
    grant = copy.deepcopy(prior_grant)
    grant.update(job_id=jobid,job_sha256=sha(canon(job)),controls=controls,
                 host_tool_vm_memory_boundary=copy.deepcopy(boundary),
                 result_status='ANN_INSTALLED_IDENTITY_CENSUS_COMPLETE_PENDING_TASK_REVIEW',
                 expires_at_utc='2026-10-12T05:52:16+00:00')
    for row in grant['runtime_refs']:
        if Path(row['path']).name == 'coordinator.py':
            row.update(ref(CANONICAL/'audit/evidence/deterministic-experiment-startup-telemetry-sol-v1/coordinator.py'))
        else:
            row['path'] = str((CANONICAL / row['path']).relative_to(WORKSPACE))
    write(dest/'packet/grant-template.json',grant)
    write(dest/'bindings.json',{'job':ref(dest/'packet/job.json'),'job_id':jobid,'image':plan['image'],
            'source_bindings_base':str(WORKSPACE),
            'payload_files':len(job['inputs']),'payload_bytes':sum(r['bytes'] for r in job['inputs']),
            'private_native_outputs':'Inside owned container only; exported summary fixed allowlist.',
            'public_exports':['result.json','execution.json'],'operational_admission':False,'new_native_calls':0})

write(OUT/'source-delta.json',{'base_worker':ref(BASE/'worker.py'),
    'worker':ref(HERE/'ann_original_identity_worker_sol_v1.py'),'native':ref(native),
    'maintained_common':common,'maintained_experiment_runner':runtime,
    'preserved':'Original accepted host pull/identity/CommandRunner cancellation/resource/owned cleanup lifecycle.',
    'changed':'Work-or-judge image selector/default user, census summary projection, mounted plan and inspect_identity filename; inherited512MiB/120CPU/180wall unchanged.',
    'controller_or_sdk_changes':0,'cloud_or_model_calls':0,'native_calls':0,
    'private_data_bodies_read':0,'new_accounting_registry':False})
print(json.dumps({'source_bytes_read':total,'output':str(OUT),'jobs':2,'native_calls':0}))
