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
    fs = job.get('science', {}).get('flt_sphere_selected_original_component')
    need(job.get('resource_profile') == ('large' if fs is not None else 'small') and job.get('execution_class') == 'native_task_control' and job.get('automatic_retries') == 0 and type(job.get('automatic_retries')) is int, 'small profile and zero retries')
    exception = job.get('science', {}).get('host_tool_vm_memory_boundary')
    nf = job.get('science', {}).get('nf_selective_original_component')
    cp = job.get('science', {}).get('carleson_pfr_selected_original_component')
    nf_docker = job.get('science', {}).get('nf_original_docker_component')
    ceiling = 1200 if cp is not None or fs is not None else (1200 if nf_docker is not None else (1200 if nf is not None else (1200 if exception is not None else 600)))
    need(integer(job.get('timeout_seconds'), 10, ceiling), 'job wall cap')
    current = now or datetime.now(timezone.utc)
    expiry = datetime.fromisoformat(grant['expires_at_utc'])
    need(expiry.tzinfo is not None and current.tzinfo is not None and current + timedelta(seconds=job['timeout_seconds'] + 300) <= min(expiry, DEADLINE), 'deadline reserves collection and close')
    science = job.get('science', {})
    bootstrap = science.get('dependency_bootstrap')
    need(sum(x is not None for x in (bootstrap, exception, nf, nf_docker, cp, fs)) <= 1, 'separate explicit resource exceptions')
    need(science.get('job_id') == job['job_id'], 'wrapper job identity')
    need(integer(science.get('child_wall_seconds'), 1, job['timeout_seconds'] - (0 if exception else 6)), 'child wall')
    need(integer(science.get('capture_bytes'), 1024, 65536), 'capture cap')
    need(integer(science.get('child_file_bytes'), 262144, 536870912 if cp is not None or fs is not None else (12884901888 if nf_docker is not None else (268435456 if nf is not None else (67108864 if bootstrap else 1048576)))), 'file growth cap')
    if bootstrap is not None:
        need(type(bootstrap) is dict and grant.get('dependency_bootstrap') == bootstrap and science.get('network') == 'owned_host_public_image_and_wheel_bootstrap', 'root-granted dependency bootstrap')
        need(science.get('child_as_bytes') == 536870912 and science.get('child_cpu_seconds') == 90 and science.get('child_wall_seconds') == 180 and science.get('child_file_bytes') == 67108864, 'finite bootstrap process caps')
        need(canonical(bootstrap.get('scientific_limits')) == canonical({'as_bytes':536870912,'affinity_cpus':1,'cpu_seconds':5,'wall_seconds':20}) and bootstrap.get('owned_dependency_bytes') == 268435456, 'preserved science and owned dependency cap')
        wheels = bootstrap.get('wheels')
        need(type(wheels) is list and len(wheels) == 4 and len({r['name'] for r in wheels}) == 4, 'four-wheel allowlist')
        for row in wheels:
            need(type(row.get('name')) is str and row['name'].endswith('.whl') and type(row.get('sha256')) is str and re.fullmatch('[0-9a-f]{64}',row['sha256']) and integer(row.get('bytes'),1,67108864) and type(row.get('version')) is str and type(row.get('url')) is str and row['url'].startswith('https://files.pythonhosted.org/'), 'exact public wheel pin')
        need(sum(r['bytes'] for r in wheels) <= 268435456, 'dependency input cap')
    elif type(nf_docker) is dict and nf_docker.get('regime') == 'nf_original_docker_preimage_diagnostic_v4':
        need(job['task_id'] == 'new_foundations_consistency' and grant.get('nf_original_docker_component') == nf_docker, 'explicit NF preimage observer grant')
        need(sha(canonical(job)) == 'f5a5290af4437ccfe7fa2d485249cd011915458f33ca415b724d19abd56de9d3' and grant.get('task_resource_exception_job_sha256') == sha(canonical(job)), 'only exact frozen NF preimage observer job')
        need(canonical(nf_docker) == canonical({'container_cpus': 2, 'container_memory_mib': 3072, 'container_tmpfs_bytes': 536870912, 'engine_root_before_bytes': 18790481920, 'engine_root_floor_bytes': 5368709120, 'engine_volume_bytes': 12884901888, 'native_as_bytes': 2147483648, 'native_cpu_soft_hard': [55, 56], 'native_file_bytes': 67108864, 'native_log_bytes': 65536, 'native_nproc': 64, 'outside_allowance_bytes': 536870912, 'regime': 'nf_original_docker_preimage_diagnostic_v4', 'source_refs': [{'path': 'work/packets/nf-docker-preimage-diagnostic-sol-v4/worker.py', 'bytes': 5287, 'sha256': '846aa74223716360957429176d00137a9038eb2e7ddc9da7cd912c57abeed64a', 'target': 'worker.py'}, {'bytes': 7905, 'path': 'work/packets/nf-original-docker-component-sol-v3/driver/lean_native.py', 'sha256': '74205f42449e69948be89f1e76bf2de13bebcfa2f97faef06eace9b45e37042e', 'target': 'driver/lean_native.py'}, {'path': 'work/packets/nf-docker-preimage-diagnostic-sol-v4/capped_docker_binfmt.py', 'bytes': 43821, 'sha256': '3171a8b6b47ae0493336f0d3d598e9f505aba1b7ba2ce8acdf6b15e58cf8a90c', 'target': 'capped_docker_binfmt.py'}, {'bytes': 23190, 'path': 'edgebenchverified/tools/cloud_jobs/lean_disk_preflight.py', 'sha256': '545844b2b550f1b0210318f12eef8e1d8bb1d5a47c46f904dd7b1aa42ea80c79', 'target': 'lean_disk_preflight.py'}, {'bytes': 14790, 'path': 'work/packets/nf-selective-original-component-sol-v2/nf_original_component_actor.py', 'sha256': 'a8bbec72d06bb1cc076b00c4b97e9e8d1cec85173c7d2e641978275beef2a09a', 'target': 'nf_original_component_actor.py'}], 'worker_memory_mib': 4096, 'readonly_bind_failure_receipt': {'schema': 'readonly-bind-failure-v1', 'optional_failure_observation': True, 'max_encoded_bytes': 1536, 'max_log_read_bytes': 4096, 'raw_body_or_path_exported': False, 'printed_message_is_not_syscall_errno_or_cause': True, 'underlying_cause': 'UNKNOWN'}}), 'exact NF preimage observer source receipt and original bounds')
        need(job['timeout_seconds'] == 1200 and science['child_wall_seconds'] == 1190 and science['capture_bytes'] == 4096 and science['child_as_bytes'] == 2147483648 and science['child_cpu_seconds'] == 600 and science['child_file_bytes'] == 12884901888 and science['child_argv'] == ['python3','-I','-S','-B','worker.py'] and science.get('network') == 'owned_host_public_image_and_wheel_bootstrap', 'exact NF preimage observer original outer envelope')
    elif nf_docker is not None:
        need(type(nf_docker) is dict and job['task_id'] == 'new_foundations_consistency' and grant.get('nf_original_docker_component') == nf_docker, 'explicit NF original Docker grant')
        need(sha(canonical(job)) == 'ae15f6aa7333413451283b7a390484cfdc301231cd2a1cd6c1344590dfbee7ad' and grant.get('task_resource_exception_job_sha256') == sha(canonical(job)), 'only exact frozen NF original Docker job')
        need(canonical(nf_docker) == canonical({'regime': 'nf_original_docker_component_v3', 'worker_memory_mib': 4096, 'native_as_bytes': 2147483648, 'native_cpu_soft_hard': [55, 56], 'native_file_bytes': 67108864, 'native_log_bytes': 65536, 'native_nproc': 64, 'container_cpus': 2, 'container_memory_mib': 3072, 'container_tmpfs_bytes': 536870912, 'engine_volume_bytes': 12884901888, 'engine_root_before_bytes': 18790481920, 'engine_root_floor_bytes': 5368709120, 'outside_allowance_bytes': 536870912, 'source_refs': [{'path': 'work/packets/nf-original-docker-component-sol-v3/worker.py', 'sha256': 'd42e9395dadc6e2ef5e1752e98c9138edfdd860a24926d91137f798d3f5d003b', 'bytes': 5250, 'target': 'worker.py'}, {'path': 'work/packets/nf-original-docker-component-sol-v3/driver/lean_native.py', 'sha256': '74205f42449e69948be89f1e76bf2de13bebcfa2f97faef06eace9b45e37042e', 'bytes': 7905, 'target': 'driver/lean_native.py'}, {'path': 'edgebenchverified/tools/cloud_jobs/capped_docker_binfmt.py', 'sha256': '29a1509a92195a49c04f2880d970b9ab2b2467a80e2e3a1a57c2741b7ce1a7c2', 'bytes': 35656, 'target': 'capped_docker_binfmt.py'}, {'path': 'edgebenchverified/tools/cloud_jobs/lean_disk_preflight.py', 'sha256': '545844b2b550f1b0210318f12eef8e1d8bb1d5a47c46f904dd7b1aa42ea80c79', 'bytes': 23190, 'target': 'lean_disk_preflight.py'}, {'path': 'work/packets/nf-selective-original-component-sol-v2/nf_original_component_actor.py', 'sha256': 'a8bbec72d06bb1cc076b00c4b97e9e8d1cec85173c7d2e641978275beef2a09a', 'bytes': 14790, 'target': 'nf_original_component_actor.py'}]}), 'exact NF original Docker engine actor and bounds')
        need(job['timeout_seconds'] == 1200 and science['child_wall_seconds'] == 1190 and science['capture_bytes'] == 4096 and science['child_as_bytes'] == 2147483648 and science['child_cpu_seconds'] == 600 and science['child_file_bytes'] == 12884901888 and science['child_argv'] == ['python3','-I','-S','-B','worker.py'] and science.get('network') == 'owned_host_public_image_and_wheel_bootstrap', 'exact NF original Docker outer envelope')
    elif cp is not None:
        expected_cp = {'f7f26f2934efc363f1de8552033f6f29ba3ac6d650111a9a7c440e451ff8674c': {'task_id': 'carleson_formalization', 'exception': {'actor_final_json_bytes': 16384, 'native_as_bytes': 2147483648, 'native_cpu_soft_hard': [55, 56], 'native_full_log_bytes': 16777216, 'native_nproc': 64, 'regime': 'carleson_pfr_selected_original_component_v1', 'source_refs': [{'path': 'work/packets/carleson-pfr-selected-original-component-sol-v2/worker.py', 'bytes': 25030, 'sha256': '9569e2c72047eedaa7f0128cd689627cd64a2d80e1b6a193e7a8db8017d74f1d', 'target': 'worker.py'}, {'path': 'work/packets/carleson-pfr-selected-original-component-sol-v2/entry.py', 'bytes': 11541, 'sha256': '9a634dd81102131f3b253e4fe12ba1acc6781f38c247aca379a3e37b28ca8525', 'target': 'entry.py'}, {'bytes': 17257, 'path': 'work/packets/carleson-pfr-selected-original-component-sol-v1/inputs/actor.py', 'sha256': '0975410bba14bd14bcf531aba00805a1361e4e7941597f9b36f823e251047fc5', 'target': 'actor.py'}, {'bytes': 22158, 'path': 'work/packets/carleson-pfr-selected-original-component-sol-v1/carleson/census_restore.py', 'sha256': '30d625e4dd66eac89d10ab2ada3192595852085a804305d3557b7f88c55253b0', 'target': 'census_restore.py'}, {'bytes': 2312, 'path': 'work/packets/carleson-pfr-selected-original-component-sol-v1/carleson/case.json', 'sha256': 'ad52b5fc292e508ff11cb2415430c94b062aa3ce9149443b6395d2c8bc9c8a50', 'target': 'case.json'}], 'worker_memory_mib': 4096}}, '590f1b6806eb4fe0ee26628db21dc0bcb692fa125ed33e3abfc732512f05f01e': {'task_id': 'pfr_formalization', 'exception': {'actor_final_json_bytes': 16384, 'native_as_bytes': 2147483648, 'native_cpu_soft_hard': [55, 56], 'native_full_log_bytes': 16777216, 'native_nproc': 64, 'regime': 'carleson_pfr_selected_original_component_v1', 'source_refs': [{'path': 'work/packets/carleson-pfr-selected-original-component-sol-v2/worker.py', 'bytes': 25030, 'sha256': '9569e2c72047eedaa7f0128cd689627cd64a2d80e1b6a193e7a8db8017d74f1d', 'target': 'worker.py'}, {'path': 'work/packets/carleson-pfr-selected-original-component-sol-v2/entry.py', 'bytes': 11541, 'sha256': '9a634dd81102131f3b253e4fe12ba1acc6781f38c247aca379a3e37b28ca8525', 'target': 'entry.py'}, {'bytes': 17257, 'path': 'work/packets/carleson-pfr-selected-original-component-sol-v1/inputs/actor.py', 'sha256': '0975410bba14bd14bcf531aba00805a1361e4e7941597f9b36f823e251047fc5', 'target': 'actor.py'}, {'bytes': 22109, 'path': 'work/packets/carleson-pfr-selected-original-component-sol-v1/pfr/census_restore.py', 'sha256': 'e709b0120fecac74da130cfd01d01707892ba9a4ce24d462af78b3b7d935fb53', 'target': 'census_restore.py'}, {'bytes': 2235, 'path': 'work/packets/carleson-pfr-selected-original-component-sol-v1/pfr/case.json', 'sha256': 'd5caef6be31aea89422be0d12aaa54f7a16d656a24bde740b2e19f08a802aa9c', 'target': 'case.json'}], 'worker_memory_mib': 4096}}}.get(sha(canonical(job)))
        need(expected_cp is not None and job['task_id'] == expected_cp['task_id'] and grant.get('task_resource_exception_job_sha256') == sha(canonical(job)), 'only two exact C/P component jobs')
        need(type(cp) is dict and canonical(cp) == canonical(expected_cp['exception']) and grant.get('carleson_pfr_selected_original_component') == cp, 'exact C/P source/native contract')
        need(job['timeout_seconds'] == 1200 and science['child_wall_seconds'] == 1190 and science['capture_bytes'] == 4096 and science['child_as_bytes'] == 2147483648 and science['child_cpu_seconds'] == 600 and science['child_file_bytes'] == 536870912 and science['child_argv'] == ['python3','-I','-S','-B','worker.py'] and science.get('network') == 'owned_host_public_image_and_wheel_bootstrap', 'exact C/P outer envelope')
    elif fs is not None:
        expected_fs = {'1952baec0f3394afcb344d83f7ee5c73f3794c237af038f5b6a50cb39ad6c45d': {'task_id': 'sphere_eversion_formalization', 'exception': {'actor_final_json_bytes': 16384, 'native_as_bytes': 4294967296, 'native_cpu_soft_hard': [55, 56], 'native_full_log_bytes': 67108864, 'native_nproc': 64, 'regime': 'flt_sphere_selected_original_component_v1', 'source_refs': [{'bytes': 24242, 'path': 'work/packets/flt-sphere-selected-original-component-sol-v2/implemented-v1/worker.py', 'sha256': '45a0e90d358f64a0e663aa2f9c7e4ddfe7a96c6b9c9cc9783377070858eb96b6', 'target': 'worker.py'}, {'bytes': 11568, 'path': 'work/packets/flt-sphere-selected-original-component-sol-v2/implemented-v1/entry.py', 'sha256': 'afdc06162df5577e0ee767e6ea3fce71bad8d0efe1259d39053cf3eb332d7883', 'target': 'entry.py'}, {'bytes': 16512, 'path': 'work/packets/flt-sphere-selected-original-component-sol-v1/sphere/actor.py', 'sha256': '6064930db617e10d4ef0560f9fc3c32fcda667f132b342cb85a043acc7bf241e', 'target': 'actor.py'}, {'bytes': 22179, 'path': 'work/packets/flt-sphere-selected-original-component-sol-v1/sphere/census_restore.py', 'sha256': 'b08d9f9488863561f7aaff11524272e0c2062409012b39b52061a9e600ebc4ff', 'target': 'census_restore.py'}, {'bytes': 2995, 'path': 'work/packets/flt-sphere-selected-original-component-sol-v1/sphere/case.json', 'sha256': '02a3c764f2e65419e40400844eef145427f2324393ab8218026afd7c8c37ee82', 'target': 'case.json'}], 'worker_memory_mib': 8192}}, 'e771c8308e359a38e86429182fb2d0efd485cd24e77088476ca65e0de94212a0': {'task_id': 'flt_regular_formalization', 'exception': {'actor_final_json_bytes': 16384, 'native_as_bytes': 4294967296, 'native_cpu_soft_hard': [55, 56], 'native_full_log_bytes': 67108864, 'native_nproc': 64, 'regime': 'flt_sphere_selected_original_component_v1', 'source_refs': [{'bytes': 25261, 'path': 'work/packets/flt-sphere-restoration-identity-allowance-sol-v3/candidate/worker.py', 'sha256': '4a21ec7fa91bac971039bee57de47ef97bd53378ee50bf7e68b21c727687a4eb', 'target': 'worker.py'}, {'bytes': 11568, 'path': 'work/packets/flt-sphere-selected-original-component-sol-v2/implemented-v1/entry.py', 'sha256': 'afdc06162df5577e0ee767e6ea3fce71bad8d0efe1259d39053cf3eb332d7883', 'target': 'entry.py'}, {'bytes': 16530, 'path': 'work/packets/flt-sphere-selected-original-component-sol-v1/flt/actor.py', 'sha256': '844547e138e6adf9b6a5e9beb298f30a52cbc9539f21f77aba97ea7c243a4b3a', 'target': 'actor.py'}, {'bytes': 22146, 'path': 'work/packets/flt-sphere-selected-original-component-sol-v1/flt/census_restore.py', 'sha256': '6e02e22036419f6eda6f1577d3af7be1e0ac83889994fc0f467366fb9d43cdcb', 'target': 'census_restore.py'}, {'bytes': 2972, 'path': 'work/packets/flt-sphere-selected-original-component-sol-v1/flt/case.json', 'sha256': '19b340fd8327366ccb714aa80dc8fc6384426141226c75c2ba4c6bf0476486b9', 'target': 'case.json'}], 'worker_memory_mib': 8192}}}.get(sha(canonical(job)))
        need(expected_fs is not None and job['task_id'] == expected_fs['task_id'] and grant.get('task_resource_exception_job_sha256') == sha(canonical(job)), 'only two exact FS component jobs')
        need(type(fs) is dict and canonical(fs) == canonical(expected_fs['exception']) and grant.get('flt_sphere_selected_original_component') == fs, 'exact FS source/native contract')
        need(job['timeout_seconds'] == 1200 and science['child_wall_seconds'] == 1190 and science['capture_bytes'] == 4096 and science['child_as_bytes'] == 4294967296 and science['child_cpu_seconds'] == 600 and science['child_file_bytes'] == 536870912 and science['child_argv'] == ['python3','-I','-S','-B','worker.py'] and science.get('network') == 'owned_host_public_image_and_wheel_bootstrap', 'exact FS outer envelope')
    elif nf is not None:
        need(type(nf) is dict and job['task_id'] == 'new_foundations_consistency' and grant.get('nf_selective_original_component') == nf, 'explicit NF selected component grant')
        need(sha(canonical(job)) in ('88b61825f53959437833ea4ba2ffa39413ae6a806b04a6d851968cdfa38873ae', 'bf65b0f8b83f2601d82a5c4de11b6f668b7bd45d5c68f8a9c034c3b488f8d721', '5376ad0a51724a7c593c64c343e018ac9d560b03e55ef06b8781b571d5c24721') and grant.get('task_resource_exception_job_sha256') == sha(canonical(job)), 'only exact frozen NF component job')
        expected_nf = {'native_as_bytes': 2147483648, 'native_cpu_soft_hard': [55, 56], 'native_file_bytes': 67108864, 'native_log_bytes': 65536, 'native_nproc': 64, 'regime': 'nf_selective_original_component_v1', 'source_refs': [{'path': 'work/packets/nf-selective-original-component-sol-v5-corrected-v1/worker.py', 'sha256': '285c7cc6c3ff0afb198b812d84727527bebe615e87de61a138c9777a64fbd5d2', 'bytes': 23018, 'target': 'worker.py'}, {'bytes': 19774, 'path': 'work/packets/nf-selective-original-component-sol-v1/census_restore.py', 'sha256': '04d9942e23a0e3859785edf81c8ffb3af5120a02bfbe237b05171534d366596f', 'target': 'census_restore.py'}, {'bytes': 3316, 'path': 'work/packets/nf-selective-original-component-sol-v1/command_entry.py', 'sha256': '1234651cfd331ddf05a752cdc72cb3b5048a553ec3b79c657902dc1d6200c160', 'target': 'command_entry.py'}, {'bytes': 14790, 'path': 'work/packets/nf-selective-original-component-sol-v2/nf_original_component_actor.py', 'sha256': 'a8bbec72d06bb1cc076b00c4b97e9e8d1cec85173c7d2e641978275beef2a09a', 'target': 'nf_original_component_actor.py'}], 'worker_memory_mib': 4096} if sha(canonical(job)) == 'bf65b0f8b83f2601d82a5c4de11b6f668b7bd45d5c68f8a9c034c3b488f8d721' else None
        expected_nf = {'native_as_bytes': 2147483648, 'native_cpu_soft_hard': [55, 56], 'native_file_bytes': 67108864, 'native_log_bytes': 65536, 'native_nproc': 64, 'regime': 'nf_selective_original_component_v1', 'source_refs': [{'bytes': 27894, 'path': 'work/packets/nf-selective-original-component-sol-v6/worker.py', 'sha256': 'fded4b9c0f64be7b2c5065448b67496534d79e6f0cb3c8fb1bcae39a34cca836', 'target': 'worker.py'}, {'bytes': 19774, 'path': 'work/packets/nf-selective-original-component-sol-v1/census_restore.py', 'sha256': '04d9942e23a0e3859785edf81c8ffb3af5120a02bfbe237b05171534d366596f', 'target': 'census_restore.py'}, {'bytes': 7133, 'path': 'work/packets/nf-selective-original-component-sol-v6/command_entry.py', 'sha256': '5ec68d3b8891f9e0d9d820e9ff44b308cae8f979f887f5806a6f550d03a13832', 'target': 'command_entry.py'}, {'bytes': 14790, 'path': 'work/packets/nf-selective-original-component-sol-v2/nf_original_component_actor.py', 'sha256': 'a8bbec72d06bb1cc076b00c4b97e9e8d1cec85173c7d2e641978275beef2a09a', 'target': 'nf_original_component_actor.py'}], 'worker_memory_mib': 4096} if sha(canonical(job)) == '5376ad0a51724a7c593c64c343e018ac9d560b03e55ef06b8781b571d5c24721' else expected_nf
        need(canonical(nf) == canonical(expected_nf if expected_nf is not None else {'native_as_bytes': 2147483648, 'native_cpu_soft_hard': [55, 56], 'native_file_bytes': 67108864, 'native_log_bytes': 65536, 'native_nproc': 64, 'regime': 'nf_selective_original_component_v1', 'source_refs': [{'path': 'work/packets/nf-selective-original-component-sol-v4/worker.py', 'sha256': 'd84696f78bd0d46abc070b9543c93fdbcac0936c671e7a3416f7053e802fba7b', 'bytes': 22277, 'target': 'worker.py'}, {'bytes': 19774, 'path': 'work/packets/nf-selective-original-component-sol-v1/census_restore.py', 'sha256': '04d9942e23a0e3859785edf81c8ffb3af5120a02bfbe237b05171534d366596f', 'target': 'census_restore.py'}, {'bytes': 3316, 'path': 'work/packets/nf-selective-original-component-sol-v1/command_entry.py', 'sha256': '1234651cfd331ddf05a752cdc72cb3b5048a553ec3b79c657902dc1d6200c160', 'target': 'command_entry.py'}, {'bytes': 14790, 'path': 'work/packets/nf-selective-original-component-sol-v2/nf_original_component_actor.py', 'sha256': 'a8bbec72d06bb1cc076b00c4b97e9e8d1cec85173c7d2e641978275beef2a09a', 'target': 'nf_original_component_actor.py'}], 'worker_memory_mib': 4096}), 'exact NF selected component source and native bounds')
        need(job['timeout_seconds'] == 1200 and science['child_wall_seconds'] == 1190 and science['capture_bytes'] == 4096 and science['child_as_bytes'] == 2147483648 and science['child_cpu_seconds'] == 600 and science['child_file_bytes'] == 268435456 and science['child_argv'] == ['python3','-I','-S','-B','worker.py'] and science.get('network') == 'owned_host_public_image_and_wheel_bootstrap', 'exact NF selected outer envelope')
    elif exception is None:
        need(integer(science.get('child_cpu_seconds'), 1, 300) and integer(science.get('child_as_bytes'), 134217728, 2147483648), 'standard child CPU memory caps')
    else:
        need(science.get('child_as_bytes') is None and grant.get('host_tool_vm_memory_boundary') == exception, 'explicit root-selected VM AS exception')
        need(type(exception) is dict and exception.get('worker_memory_mib') == 4096, 'inherited physical VM regime')
        if exception.get('task_resource_regime') == 'jagua_rust_main_export_v1':
            need(job['task_id'] == 'jagua_nesting_optimization' and grant.get('task_resource_exception_job_sha256') == sha(canonical(job)), 'exact root-selected Jagua Rust resource exception')
            native_limits = {'as_bytes':3221225472,'cpu_seconds':110,'wall_seconds':110,'container_cpus':1,'container_memory_mib':3072}
            need(canonical(science.get('task_native_limits')) == canonical({'cpus':1,'memory_mib':3072,'as_bytes':3221225472,'cpu_seconds':110,'wall_seconds':110,'pids':128,'output_bytes':65536,'file_bytes':67108864,'exec_tmpfs_bytes':268435456}), 'exact Jagua native declared limits')
            need(job['timeout_seconds'] == 180 and science['child_wall_seconds'] == 175 and science['capture_bytes'] == 65536 and science['child_argv'] == ['python3','-I','-S','-B','worker.py'], 'exact Jagua host declared limits')
        elif exception.get('task_resource_regime') == 'equivalence_original_evaluator_scratch_v1':
            need(job['task_id'] == 'equivalence_class_divide_and_conquer' and grant.get('task_resource_exception_job_sha256') == sha(canonical(job)), 'exact root-selected Equivalence scratch resource exception')
            native_limits = {'as_bytes': 536870912, 'cpu_seconds': 120, 'wall_seconds': 180, 'container_cpus': 1, 'container_memory_mib': 2048, 'native_file_bytes': 16777216, 'native_tmpfs_bytes': 1073741824}
            need(canonical(science.get('task_native_limits')) == canonical({'as_bytes': 536870912, 'file_bytes': 16777216, 'grader_stdout_stderr_stop_bytes_each': 1048576, 'grader_wall_seconds': 150, 'installed_metadata_total_bytes': 1342177280, 'legacy_corpus_bodyhash_guard_bytes': 536870912, 'memory_mib': 2048, 'native_cpu_seconds': 120, 'native_cpus': 1, 'native_wall_seconds': 180, 'one_container_at_a_time': True, 'raw_body_exports': False, 'tmpfs_bytes': 1073741824, 'tmpfs_exec': True}), 'exact Equivalence scratch native declared limits')
            need(job['timeout_seconds'] == 900 and science['child_wall_seconds'] == 890 and science['capture_bytes'] == 65536 and science['child_argv'] == ['python3','-I','-S','-B','worker.py'], 'exact Equivalence scratch host declared limits')
            need(type(science.get('native_containers')) is int and science['native_containers'] == 2 and science.get('sequential_only') is True and science.get('native_network') == 'none', 'paired sequential Equivalence scratch actors')
        elif exception.get('task_resource_regime') == 'equivalence_one_case_re_baseline_v1':
            need(job['task_id'] == 'equivalence_class_divide_and_conquer' and grant.get('task_resource_exception_job_sha256') == sha(canonical(job)), 'exact root-selected Equivalence one-case baseline exception')
            need(sha(canonical(job)) == '1b7a69b76cd95be5ba0e43733cbbd348287c777e37de0e4b6f28ad988fa0e455' and science.get('experiment_shape') == 'equivalence_one_case_re_baseline_v1', 'only frozen one-case baseline job and science')
            native_limits = {'as_bytes': 536870912, 'cpu_seconds': 120, 'wall_seconds': 550, 'container_cpus': 1, 'container_memory_mib': 2048, 'native_file_bytes': 16777216, 'native_tmpfs_bytes': 1073741824}
            need(canonical(science.get('task_native_limits')) == canonical({'as_bytes': 536870912, 'file_bytes': 16777216, 'grader_stdout_stderr_stop_bytes_each': 1048576, 'grader_wall_seconds': 525, 'installed_metadata_total_bytes': 1342177280, 'legacy_corpus_bodyhash_guard_bytes': 536870912, 'memory_mib': 2048, 'native_cpu_seconds': 120, 'native_cpus': 1, 'native_wall_seconds': 550, 'one_container_at_a_time': True, 'raw_body_exports': False, 'tmpfs_bytes': 1073741824, 'tmpfs_exec': True}), 'exact Equivalence wall-only native declared limits')
            need(job['timeout_seconds'] == 1200 and science['child_wall_seconds'] == 1190 and science['capture_bytes'] == 65536 and science['child_argv'] == ['python3','-I','-S','-B','worker.py'], 'exact Equivalence wall-only host declared limits')
            need(type(science.get('native_containers')) is int and science['native_containers'] == 1 and science.get('sequential_only') is True and science.get('native_network') == 'none', 'one exact sequential Equivalence baseline actor')
        elif exception.get('task_resource_regime') == 'equivalence_original_evaluator_wall_v1':
            need(job['task_id'] == 'equivalence_class_divide_and_conquer' and grant.get('task_resource_exception_job_sha256') == sha(canonical(job)), 'exact root-selected Equivalence wall-only exception')
            native_limits = {'as_bytes': 536870912, 'cpu_seconds': 120, 'wall_seconds': 550, 'container_cpus': 1, 'container_memory_mib': 2048, 'native_file_bytes': 16777216, 'native_tmpfs_bytes': 1073741824}
            need(canonical(science.get('task_native_limits')) == canonical({'as_bytes': 536870912, 'file_bytes': 16777216, 'grader_stdout_stderr_stop_bytes_each': 1048576, 'grader_wall_seconds': 525, 'installed_metadata_total_bytes': 1342177280, 'legacy_corpus_bodyhash_guard_bytes': 536870912, 'memory_mib': 2048, 'native_cpu_seconds': 120, 'native_cpus': 1, 'native_wall_seconds': 550, 'one_container_at_a_time': True, 'raw_body_exports': False, 'tmpfs_bytes': 1073741824, 'tmpfs_exec': True}), 'exact Equivalence wall-only native declared limits')
            need(job['timeout_seconds'] == 1200 and science['child_wall_seconds'] == 1190 and science['capture_bytes'] == 65536 and science['child_argv'] == ['python3','-I','-S','-B','worker.py'], 'exact Equivalence wall-only host declared limits')
            need(type(science.get('native_containers')) is int and science['native_containers'] == 2 and science.get('sequential_only') is True and science.get('native_network') == 'none', 'paired sequential Equivalence wall-only actors')
        elif exception.get('task_resource_regime') == 'bipedal_original_ten_episode_v1':
            need(job['task_id'] == 'bipedalwalker_locomotion_rl' and grant.get('task_resource_exception_job_sha256') == sha(canonical(job)), 'exact root-selected Bipedal resource exception')
            need(sha(canonical(job)) == '151ef6a488416ec04da149b0d8b4a6f5b8306b69b1d7c4d61ca64bfba69cf04e' and science.get('experiment_shape') == 'bipedal_original_ten_episode_v1', 'only frozen Bipedal ten-episode job')
            native_limits = {'as_bytes':3221225472,'container_cpus':1,'container_memory_mib':2048,'cpu_seconds':120,'wall_seconds':180}
            need(canonical(science.get('task_native_limits')) == canonical({'as_bytes': 3221225472, 'native_cpu_seconds_per_process': 120, 'native_cpus': 1, 'native_wall_seconds': 180, 'caller_wall_seconds': 150, 'memory_mib': 2048, 'memory_swap_mib': 2048, 'pids': 64, 'file_bytes': 1048576, 'output_bytes_each': 65536, 'tmpfs_bytes': 268435456, 'submission_tmpfs_bytes': 4194304, 'observer_bytes': 32768, 'observer_max_episode_steps': 10000, 'original_episodes_per_environment': 10, 'native_network': 'none'}), 'exact Bipedal native declared limits')
            need(job['timeout_seconds'] == 1200 and science['child_wall_seconds'] == 1190 and science['capture_bytes'] == 65536 and science['child_argv'] == ['python3','-I','-S','-B','worker.py'], 'exact Bipedal host limits')
            need(type(science.get('native_containers')) is int and science['native_containers'] == 1 and science.get('sequential_only') is True and science.get('native_network') == 'none' and science.get('original_cli_called_once') is True, 'one original Bipedal CLI actor')
        elif 'task_resource_regime' in exception:
            need(exception['task_resource_regime'] == 'ann_original_evaluator_v1' and job['task_id'] == 'ann_vector_search_qps' and grant.get('task_resource_exception_job_sha256') == sha(canonical(job)), 'exact root-selected ANN evaluator resource exception')
            native_limits = {'as_bytes':3221225472,'cpu_seconds':900,'wall_seconds':900,'container_cpus':1,'container_memory_mib':2048,'native_file_bytes':1073741824}
        else:
            native_limits = {'as_bytes':536870912,'cpu_seconds':120,'wall_seconds':180,'container_cpus':1,'container_memory_mib':1024}
        need(canonical(exception.get('inspector_limits')) == canonical(native_limits), 'inherited native resource regime')
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
    if nf_docker is not None:
        refs = nf_docker.get('source_refs')
        need(type(refs) is list and 1 <= len(refs) <= 8 and all(row in inputs for row in refs), 'NF original Docker source pins')
    if cp is not None:
        refs = cp.get('source_refs')
        need(type(refs) is list and len(refs) == 5 and all(row in inputs for row in refs), 'exact C/P source refs')
    if fs is not None:
        refs = fs.get('source_refs')
        need(type(refs) is list and len(refs) == 5 and all(row in inputs for row in refs), 'exact FS source refs')
    if nf is not None:
        refs = nf.get('source_refs')
        need(type(refs) is list and 1 <= len(refs) <= 8 and all(row in inputs for row in refs), 'NF selected component source pins')
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
