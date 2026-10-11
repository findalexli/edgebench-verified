"""Small ANN scientific worker for the maintained deterministic coordinator.

Reuses the unchanged accepted CommandRunner for owned CLI polling/cancellation.
No SDK/provider/model, queue access, image build or task/generator invocation.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import time

HERE = Path(__file__).resolve().parent
OWNER = 'org.edgebenchverified.ann_identity_token'
STATUS = 'ANN_INSTALLED_IDENTITY_CENSUS_COMPLETE_PENDING_TASK_REVIEW'
MAX_GROWTH = 8 * 1024**3
MIN_FREE = 5 * 1024**3
CAP = 32768


def need(value, reason):
    if not value:
        raise ValueError(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def read(path, cap):
    need(not any(p.is_symlink() for p in (path, *path.parents)), 'linked_input')
    with path.open('rb') as stream:
        info = os.fstat(stream.fileno())
        need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size <= cap, 'input_cap')
        raw = stream.read(cap + 1)
    need(len(raw) == info.st_size, 'input_changed')
    return raw


def write(path, value):
    raw = canonical(value) + b'\n'; need(len(raw) <= CAP, 'result_cap')
    tmp = path.with_name(path.name + '.tmp')
    with tmp.open('wb') as stream:
        os.chmod(tmp, 0o600); stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    os.replace(tmp, path)


def image_receipt(value, plan):
    need(type(value) is dict and set(value) == {'image_id', 'os', 'architecture', 'repo_digests', 'default_user'}, 'image_shape')
    need(value['image_id'] == plan['image']['config_id'] and value['os'] == 'linux' and value['architecture'] == 'amd64' and
         type(value['repo_digests']) is list and plan['image']['reference'] in value['repo_digests'] and value['default_user'] == plan['image']['default_user'], 'original_image_identity')
    return {'reference': plan['image']['reference'], 'config_id': value['image_id'], 'default_user': plan['image']['default_user']}


def native_args(root, output, plan, token):
    for path in (root, output):
        need(not any(c in str(path) for c in (',', '\n', '\r')), 'mount_ambiguity')
    return ['create', '--label', OWNER + '=' + token, '--network', 'none', '--cpus', '1', '--memory', '1g', '--memory-swap', '1g',
            '--pids-limit', '64', '--read-only', '--user', '0:0', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
            '--no-healthcheck', '--log-driver', 'none', '--ulimit', 'core=0', '--ulimit', 'nofile=128:128',
            '--tmpfs', '/tmp:rw,nosuid,nodev,noexec,size=16777216,mode=1777', '--workdir', '/audit',
            '--env', 'OMP_NUM_THREADS=1', '--env', 'OPENBLAS_NUM_THREADS=1', '--env', 'MKL_NUM_THREADS=1', '--env', 'NUMEXPR_NUM_THREADS=1',
            '--env', 'HDF5_PLUGIN_PRELOAD=::', '--env', 'HDF5_PLUGIN_PATH=/audit/no-plugins',
            '--mount', 'type=bind,source=' + str(root / 'inspect_identity.py') + ',target=/audit/inspect_identity.py,readonly',
            '--mount', 'type=bind,source=' + str(root / 'identity-plan.json') + ',target=/audit/identity-plan.json,readonly',
            '--mount', 'type=bind,source=' + str(output) + ',target=/audit-output',
            '--entrypoint', '/usr/local/bin/python3', plan['image']['config_id'], '-I', '-B', '/audit/inspect_identity.py']


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
    need('python_version' not in value or type(value['python_version']) is str and re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+',value['python_version']), 'native_python')
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


def run(config):
    # Actual imports/use are entrypoint-only; source tests never call run().
    need(type(config) is dict and type(config.get('input_files')) is dict and
         hashlib.sha256(read(HERE / 'common.py', 1048576)).hexdigest() == config['input_files'].get('common.py'), 'common_identity')
    sys.path.insert(0, str(HERE))
    import common
    start = time.monotonic(); phase = 'input'; cid = None; attempted = False; runner = cleanup = None
    result = {'schema_version': 1, 'job_id': config.get('job_id'), 'task_id': 'ann_vector_search_qps', 'status': 'INCOMPLETE',
              'phase': phase, 'native': None, 'container_cleanup_confirmed': False, 'raw_data_exported': False,
              'private_auditor_access': True, 'solver_holdout_performance': False, 'original_evaluator_executed': False, 'all_five_gates': 'pending',
              'certification_effect': 'none', 'requires_worker_termination': True}
    def checkpoint(step):
        result['phase'] = step
        if runner:
            result['storage'] = runner.storage
            result['commands'] = [{k: v for k, v in row.items() if k in {'step', 'returncode', 'timed_out', 'elapsed_seconds', 'log_sha256', 'log_bytes'}} for row in runner.records]
        write(HERE / 'result.json', result)

    class Runner(common.CommandRunner):
        def __init__(self, *args):
            super().__init__(*args); self.initial = {}; self.storage = {}
        def check_resources(self):
            super().check_resources()
            for path in self.storage_paths:
                free = shutil.disk_usage(path).free; base = self.initial.setdefault(str(path), free)
                growth = max(0, base - free)
                key = 'private' if path == self.private_dir else 'docker'
                self.storage[key] = {'latest_free_bytes': free, 'growth_bytes': growth, 'growth_cap_bytes': MAX_GROWTH}
                need(growth <= MAX_GROWTH, 'aggregate_growth_cap')
            total = count = 0
            for base, dirs, files in os.walk(self.private_dir, followlinks=False):
                need(not any((Path(base) / n).is_symlink() for n in dirs), 'linked_private_directory')
                for name in files:
                    info = (Path(base) / name).lstat()
                    need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size <= 1048576, 'private_file_cap')
                    total += info.st_size; count += 1
                    need(total <= 8 * 1024**2 and count <= 128, 'private_total_cap')

    try:
        need(type(config) is dict and set(config) == {'job_id', 'run_token', 'input_files', 'private_auditor_access'} and
             config['private_auditor_access'] is True and re.fullmatch(r'deterministic-[a-z0-9-]{8,64}', config['job_id']) and
             re.fullmatch(r'[0-9a-f]{32}', config['run_token']), 'worker_config')
        need(set(config['input_files']) == {'worker.py', 'common.py', 'inspect_identity.py', 'identity-plan.json'}, 'input_map')
        for name, digest in config['input_files'].items():
            need(hashlib.sha256(read(HERE / name, 1048576)).hexdigest() == digest, 'input_identity')
        plan = json.loads(read(HERE / 'identity-plan.json', 65536))
        need(plan['data_path'] == '/home/workspace/ann-benchmarks/data/sift-128-euclidean.hdf5', 'fixed_data_path')
        private = HERE / 'private'; private.mkdir(mode=0o700)
        env = {'PATH': '/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8',
               'DOCKER_HOST': 'unix:///var/run/docker.sock', 'PYTHONDONTWRITEBYTECODE': '1', 'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1'}
        for key, name in [('HOME', 'home'), ('TMPDIR', 'tmp'), ('DOCKER_CONFIG', 'docker-config')]:
            path = private / name; path.mkdir(mode=0o700); env[key] = str(path)
        os.environ.clear(); os.environ.update(env)
        runner = Runner(private, start + 1100, MIN_FREE); runner.on_command = checkpoint
        cleanup_dir = private / 'cleanup'; cleanup_dir.mkdir(mode=0o700)
        cleanup = Runner(cleanup_dir, start + 1190, 0)
        checkpoint('prepared')
        phase = 'docker_root'; raw = runner.run(phase, common.DOCKER + ['info', '--format', '{{json .DockerRootDir}}'], 20)
        docker_root = Path(json.loads(read(raw, 4096))); need(docker_root.is_absolute() and docker_root.is_dir(), 'docker_root')
        runner.storage_paths.append(docker_root); runner.check_resources()
        phase = 'exclusive_worker'; raw = runner.run(phase, common.DOCKER + ['ps', '-aq'], 15)
        need(read(raw, 65536).strip() == b'', 'preexisting_container')
        phase = 'pull_judge'; runner.run(phase, common.DOCKER + ['pull', '--platform', 'linux/amd64', plan['image']['reference']], 600)
        phase = 'image_identity'
        fmt = '{"image_id":{{json .Id}},"os":{{json .Os}},"architecture":{{json .Architecture}},"repo_digests":{{json .RepoDigests}},"default_user":{{json .Config.User}}}'
        raw = runner.run(phase, common.DOCKER + ['image', 'inspect', '--format', fmt, plan['image']['reference']], 20)
        result['image'] = image_receipt(json.loads(read(raw, 8192)), plan)
        native_output = private / 'native'; native_output.mkdir(mode=0o700)
        phase = 'create'; attempted = True; checkpoint(phase)
        raw = runner.run(phase, common.DOCKER + native_args(HERE, native_output, plan, config['run_token']), 20)
        cid = read(raw, 128).decode('ascii').strip(); need(re.fullmatch(r'[0-9a-f]{64}', cid), 'container_id')
        result['container_id'] = cid; phase = 'native'; checkpoint(phase)
        try:
            runner.run(phase, common.DOCKER + ['start', '-a', cid], 185)
        except common.JobFailure as exc:
            if exc.code != 'command_nonzero':
                raise
        phase = 'state'; raw = runner.run(phase, common.DOCKER + ['inspect', '--format', '{{json .State}}', cid], 15)
        state = json.loads(read(raw, 8192))
        result['native_state'] = {'running': state.get('Running'), 'exit_code': state.get('ExitCode'), 'oom_killed': state.get('OOMKilled')}
        native = native_output / 'native-summary.json'
        if native.is_file():
            result['native'] = native_projection(json.loads(read(native, CAP)))
        need(state.get('Running') is False and type(state.get('ExitCode')) is int and state['ExitCode'] == 0 and state.get('OOMKilled') is False and result['native'] is not None and result['native']['complete'], 'native_incomplete')
        result['status'] = STATUS
    except Exception as exc:
        result['failure'] = {'phase': phase, 'class': type(exc).__name__ if type(exc).__name__ in {'ValueError', 'OSError', 'JobFailure'} else 'other_error'}
        code = exc.code if isinstance(exc, common.JobFailure) else str(exc) if isinstance(exc, ValueError) else ''
        if re.fullmatch(r'[a-z0-9_]{1,80}', code):
            result['failure']['reason_code'] = code
    finally:
        if attempted and cleanup:
            try:
                raw = cleanup.run('owned_list', common.DOCKER + ['ps', '-a', '--no-trunc', '--filter', 'label=' + OWNER + '=' + config['run_token'], '--format', '{{.ID}}'], 15)
                ids = read(raw, 512).decode('ascii').splitlines()
                need(len(ids) <= 1 and all(re.fullmatch(r'[0-9a-f]{64}', x) for x in ids) and (cid is None or not ids or ids == [cid]), 'owned_cleanup_identity')
                for saved in ids:
                    raw = cleanup.run('owned_label', common.DOCKER + ['inspect', '--format', '{{json .Config.Labels}}', saved], 15)
                    need(json.loads(read(raw, 4096)).get(OWNER) == config['run_token'], 'owned_cleanup_label')
                    cleanup.run('owned_remove', common.DOCKER + ['rm', '-f', saved], 15)
                raw = cleanup.run('owned_absence', common.DOCKER + ['ps', '-a', '--no-trunc', '--filter', 'label=' + OWNER + '=' + config['run_token'], '--format', '{{.ID}}'], 15)
                result['container_cleanup_confirmed'] = read(raw, 512).strip() == b''
            except Exception:
                result['container_cleanup_confirmed'] = False
        elif not attempted:
            result['container_cleanup_confirmed'] = True
        if runner:
            result['daemon_cancellation_unconfirmed'] = runner.cancellation_unconfirmed
            if runner.cancellation_unconfirmed:
                result['status'] = 'INCOMPLETE'
        if not result['container_cleanup_confirmed']:
            result['status'] = 'INCOMPLETE'
        if result['native'] is None and (HERE / 'private/native/native-summary.json').is_file():
            try:
                result['native'] = native_projection(json.loads(read(HERE / 'private/native/native-summary.json', CAP)))
            except Exception:
                pass
        result['elapsed_seconds'] = round(time.monotonic() - start, 6)
        checkpoint('terminal')
    return 0 if result['status'] == STATUS else 1


if __name__ == '__main__':
    raise SystemExit(run(json.loads(read(HERE / 'worker-config.json', 65536))))
