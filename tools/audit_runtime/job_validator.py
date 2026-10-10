"""Finite new-experiment admission; no process, SDK, credential or queue calls."""
import hashlib
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import PurePosixPath

OPERATION = 'deterministic-experiment-v1'
HELD_TASKS = frozenset({'ad_placement_optimization', 'ordinal_notation_well_foundedness', 'integer_compression_codec', 'ffmpeg_swscale_reimplementation', 'smt_solver', 'grid_turing_robot', 'warehouse_forklift_routing'})
DEADLINE = datetime.fromisoformat('2026-10-12T05:52:16+00:00')

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

def sha(data):
    return hashlib.sha256(data).hexdigest()

def need(condition, reason):
    if not condition:
        raise ValueError(reason)

def integer(value, lower, upper):
    return type(value) is int and lower <= value <= upper

def name(value):
    need(type(value) is str and 1 <= len(value) <= 256 and '\x00' not in value, 'path')
    p = PurePosixPath(value)
    need(not p.is_absolute() and all(x not in ('', '.', '..') for x in value.split('/')), 'relative path')
    return value

def validate(job, grant_bytes, expected_grant_sha256, payload, *, now=None):
    """Root selects the grant hash outside this package; issued_by is descriptive."""
    need(type(grant_bytes) is bytes and len(grant_bytes) <= 65536 and sha(grant_bytes) == expected_grant_sha256, 'root grant hash')
    grant = json.loads(grant_bytes)
    need(grant.get('schema') == 'deterministic-experiment-grant-v1' and grant.get('issued_by') == '/root' and grant.get('authorization_status') == 'ROOT_OPERATIONALLY_GRANTED', 'root grant shape')
    runtime = grant.get('runtime_refs')
    need(type(runtime) is list and 3 <= len(runtime) <= 8 and {'coordinator.py','job_validator.py','experiment_runner.py'} <= {PurePosixPath(r['path']).name for r in runtime}, 'reviewed maintained runtime refs')
    for row in runtime:
        name(row['path']); need(integer(row.get('bytes'),1,1048576) and type(row.get('sha256')) is str and re.fullmatch('[0-9a-f]{64}',row['sha256']), 'runtime ref shape')
    need(job.get('schema') == 'deterministic-experiment-job-v1' and job.get('operation_id') == OPERATION, 'new experiment operation only')
    need(type(job.get('job_id')) is str and re.fullmatch(r'deterministic-[a-z0-9-]{8,64}', job['job_id']) and job['job_id'] == grant.get('job_id'), 'fresh deterministic namespace identity')
    need(type(job.get('task_id')) is str and job['task_id'] == grant.get('task_id') and job['task_id'] not in HELD_TASKS, 'task identity or hold')
    need(sha(canonical(job)) == grant.get('job_sha256'), 'immutable job hash')
    need(job.get('resource_profile') == 'small' and job.get('execution_class') == 'native_task_control' and job.get('automatic_retries') == 0 and type(job.get('automatic_retries')) is int, 'small profile and zero retries')
    exception = job.get('science', {}).get('host_tool_vm_memory_boundary')
    ceiling = 1200 if exception is not None else 600
    need(integer(job.get('timeout_seconds'), 10, ceiling), 'job wall cap')
    current = now or datetime.now(timezone.utc)
    expiry = datetime.fromisoformat(grant['expires_at_utc'])
    need(expiry.tzinfo is not None and current.tzinfo is not None and current + timedelta(seconds=job['timeout_seconds'] + 300) <= min(expiry, DEADLINE), 'deadline reserves collection and close')
    science = job.get('science', {})
    bootstrap = science.get('dependency_bootstrap')
    need(not (bootstrap is not None and exception is not None), 'separate explicit resource exceptions')
    need(science.get('job_id') == job['job_id'], 'wrapper job identity')
    need(integer(science.get('child_wall_seconds'), 1, job['timeout_seconds'] - (0 if exception else 6)), 'child wall')
    need(integer(science.get('capture_bytes'), 1024, 65536), 'capture cap')
    need(integer(science.get('child_file_bytes'), 262144, 67108864 if bootstrap else 1048576), 'file growth cap')
    if bootstrap is not None:
        need(type(bootstrap) is dict and grant.get('dependency_bootstrap') == bootstrap and science.get('network') == 'owned_host_public_image_and_wheel_bootstrap', 'root-granted dependency bootstrap')
        need(science.get('child_as_bytes') == 536870912 and science.get('child_cpu_seconds') == 90 and science.get('child_wall_seconds') == 180 and science.get('child_file_bytes') == 67108864, 'finite bootstrap process caps')
        need(canonical(bootstrap.get('scientific_limits')) == canonical({'as_bytes':536870912,'affinity_cpus':1,'cpu_seconds':5,'wall_seconds':20}) and bootstrap.get('owned_dependency_bytes') == 268435456, 'preserved science and owned dependency cap')
        wheels = bootstrap.get('wheels')
        need(type(wheels) is list and len(wheels) == 4 and len({r['name'] for r in wheels}) == 4, 'four-wheel allowlist')
        for row in wheels:
            need(type(row.get('name')) is str and row['name'].endswith('.whl') and type(row.get('sha256')) is str and re.fullmatch('[0-9a-f]{64}',row['sha256']) and integer(row.get('bytes'),1,67108864) and type(row.get('version')) is str and type(row.get('url')) is str and row['url'].startswith('https://files.pythonhosted.org/'), 'exact public wheel pin')
        need(sum(r['bytes'] for r in wheels) <= 268435456, 'dependency input cap')
    elif exception is None:
        need(integer(science.get('child_cpu_seconds'), 1, 300) and integer(science.get('child_as_bytes'), 134217728, 2147483648), 'standard child CPU memory caps')
    else:
        need(science.get('child_as_bytes') is None and grant.get('host_tool_vm_memory_boundary') == exception, 'explicit root-selected VM AS exception')
        need(type(exception) is dict and exception.get('worker_memory_mib') == 4096 and canonical(exception.get('inspector_limits')) == canonical({'as_bytes':536870912,'cpu_seconds':120,'wall_seconds':180,'container_cpus':1,'container_memory_mib':1024}), 'inherited native resource regime')
        need(science.get('child_cpu_seconds') == 180 and type(science.get('child_cpu_seconds')) is int and science.get('child_file_bytes') == 1048576 and exception.get('host_cpu_boundary') == 'inherited_180CPU_seconds_one_affinity_CPU', 'inherited host CPU/file regime')
    need(science.get('network') in {'no_network_requested', 'owned_host_public_image_and_wheel_bootstrap'}, 'explicit network scope')
    argv = science.get('child_argv')
    need(type(argv) is list and 1 <= len(argv) <= 32 and all(type(x) is str and 0 < len(x) <= 512 and '\x00' not in x for x in argv), 'exact child argv')
    need(job.get('argv') == ['python3', '-I', '-S', '-B', 'experiment_runner.py', 'experiment.json'], 'fixed trusted wrapper argv')
    inputs = job.get('inputs')
    need(type(inputs) is list and 3 <= len(inputs) <= 32 and type(payload) is dict and set(payload) == {r['target'] for r in inputs}, 'exact payload')
    need(len({r['target'] for r in inputs}) == len(inputs) and len({r['path'] for r in inputs}) == len(inputs), 'unique inputs')
    total = 0
    for row in inputs:
        name(row['path']); name(row['target'])
        b = payload[row['target']]
        need(type(b) is bytes and integer(row.get('bytes'), 0, 1048576) and len(b) == row['bytes'] and sha(b) == row['sha256'], 'input byte hash')
        total += len(b)
    need(0 < total <= 16777216, 'payload cap')
    need(payload['experiment.json'] == canonical(science), 'exact experiment configuration')
    need(sha(payload['experiment_runner.py']) == grant.get('remote_runner_sha256'), 'reviewed remote runner')
    controls = grant.get('controls')
    need(type(controls) is list and 1 <= len(controls) <= 32, 'control preregistration refs')
    for row in controls:
        need(row in inputs and row['target'] not in {'experiment.json','experiment_runner.py'}, 'controls bound to payload')
    need(science.get('controls_sha256') == sha(canonical(controls)), 'control identity')
    if exception is not None:
        refs = exception.get('source_refs')
        need(type(refs) is list and 1 <= len(refs) <= 8 and all(row in inputs for row in refs), 'accepted host exception source pins')
    if bootstrap is not None:
        refs = bootstrap.get('source_refs')
        need(type(refs) is list and 1 <= len(refs) <= 8 and all(row in inputs for row in refs), 'bootstrap worker/control source pins')
    exports = job.get('exports')
    need(type(exports) is list and 2 <= len(exports) <= 4 and exports[0] == 'result.json' and 'execution.json' in exports and len(set(exports)) == len(exports), 'explicit JSON exports')
    need(all(name(x).endswith('.json') for x in exports) and integer(job.get('max_export_bytes'), 1024, 262144), 'JSON export cap')
    need(type(grant.get('result_status')) is str and 1 <= len(grant['result_status']) <= 128, 'exact task result status')
    need(type(grant.get('required_result_fields')) is list and 1 <= len(grant['required_result_fields']) <= 32 and all(type(x) is str and x for x in grant['required_result_fields']), 'result field contract')
    return grant

def validate_result(value, execution, job, grant):
    need(type(value) is dict and value.get('job_id') == job['job_id'] and value.get('task_id') == job['task_id'] and value.get('status') == grant['result_status'], 'scientific result identity/status')
    need(all(k in value for k in grant['required_result_fields']), 'required scientific fields')
    need(type(execution) is dict and execution.get('job_id') == job['job_id'] and type(execution.get('exit_code')) is int and execution['exit_code'] == 0 and execution.get('capture_complete') is True and execution.get('owned_child_reaped') is True and execution.get('group_kill_sent_or_absent') is True, 'trusted wrapper completion')
    need(execution.get('controls_sha256') == job['science']['controls_sha256'], 'control execution identity')
    return True
