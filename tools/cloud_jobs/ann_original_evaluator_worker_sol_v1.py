"""Original ANN evaluator scientific worker for the maintained deterministic coordinator.

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
OWNER = 'org.edgebenchverified.ann_original_evaluator_token'
STATUS = 'ANN_ORIGINAL_EVALUATOR_AUDIT_COMPLETE_PENDING_TASK_REVIEW'
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


def native_projection(value):
    # Same pinned authored schema on host and native side; no acquired code import.
    from eval_original import project
    return project(value)


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
        need(set(config['input_files']) == {'worker.py', 'common.py', 'eval_original.py', 'evaluator-plan.json', 'declared-module.py', 'declared-config.yml'}, 'input_map')
        for name, digest in config['input_files'].items():
            need(hashlib.sha256(read(HERE / name, 1048576)).hexdigest() == digest, 'input_identity')
        plan = json.loads(read(HERE / 'evaluator-plan.json', 65536))
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
            runner.run(phase, common.DOCKER + ['start', '-a', cid], 905)
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
        result['original_evaluator_executed'] = True
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
        if result['native'] is not None:
            result['original_evaluator_executed'] = result['native']['original_evaluator_executed']
        result['elapsed_seconds'] = round(time.monotonic() - start, 6)
        checkpoint('terminal')
    return 0 if result['status'] == STATUS else 1


if __name__ == '__main__':
    raise SystemExit(run(json.loads(read(HERE / 'worker-config.json', 65536))))
