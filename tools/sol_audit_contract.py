"""Pure, fail-closed contract for one reviewer-admitted autonomous audit job.

This module has no credential, network, provider or subprocess functionality.
The root controller alone materializes a job and supplies its admission receipt.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath
import re

OPERATION = 'sol-autonomous-audit-v1'
CONTROLLER = 'sol-audit-owned-close-v1'
MODEL = 'gpt-6.1-sol'
EFFORT = 'xhigh'
VERSION = '0.160.1'
ARCHIVE_SHA = '340801565906a7028f6baaa9ab6853addaef221f0016a1417a7c1ffdd96c21f0'
BINARY_SHA = 'f34a4d2301892ae96c90097786bfe5dc269f187b6f69faf42a7b357b8c081e35'
PAYLOAD_PREFIX = 'audit/evidence/sol-e2b-agent-runner-v1/'
PAYLOAD_FILES = frozenset({'runner.py', 'contract.py', 'task_tools.py', 'child_limits.py',
    'install_codex_runtime.py', 'runtime-lock.json', 'evidence-schema.json',
    'evidence_validator.py', 'schema_defs.py'})
DEADLINE = '2026-10-10T05:18:55+00:00'
HELD_TASKS = frozenset({'ad_placement_optimization',
    'ordinal_notation_well_foundedness', 'integer_compression_codec',
    'ffmpeg_swscale_reimplementation', 'grid_turing_robot',
    'warehouse_forklift_routing', 'smt_solver'})
HELD_FAMILIES = frozenset({'ad-overlap', 'coq-output', 'coq-tactic',
    'native-codec', 'cvc5', 'grid', 'warehouse'})
CAPS = {'operation_wall_seconds': 1200, 'preparation_wall_seconds': 600,
    'agent_wall_seconds': 420, 'agent_cpu_seconds': 300,
    'agent_cpu': 1, 'agent_memory_mib': 2048, 'agent_pids': 128,
    'max_cli_inference_invocations': 1, 'max_agent_tool_calls': 24,
    'native_wall_seconds': 30, 'native_cpu_seconds': 25,
    'native_cpu': 1, 'native_memory_mib': 1024, 'native_pids': 64,
    'max_native_calls': 6, 'native_output_bytes': 65536,
    'transcript_bytes': 1048576, 'event_line_bytes': 65536,
    'artifact_file_bytes': 1048576, 'artifact_total_bytes': 4194304,
    'artifact_files': 64, 'private_export_bytes': 8388608,
    'private_expanded_bytes': 12582912, 'cleanup_reserve_seconds': 60,
    'export_reserve_seconds': 60}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      allow_nan=False).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def name(value):
    if type(value) is not str or not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,95}', value):
        raise ValueError('simple_identity_required')
    return value


def relative(value):
    if type(value) is not str or not 1 <= len(value) <= 512:
        raise ValueError('relative_path_required')
    if (PurePosixPath(value).is_absolute() or '\\' in value or ':' in value
            or any(p in ('', '.', '..') for p in value.split('/'))):
        raise ValueError('noncanonical_path')
    return value


def digest_value(value):
    if type(value) is not str or not re.fullmatch(r'[a-f0-9]{64}', value):
        raise ValueError('sha256_required')
    return value


def validate_contract(job, admission=None):
    canonical(job)
    name(job.get('job_id')); name(job.get('task_id'))
    if (job.get('operation_id') != OPERATION or job.get('controller_id') != CONTROLLER
            or job.get('model') != MODEL or job.get('reasoning_effort') != EFFORT
            or job.get('runtime_version') != VERSION or job.get('caps') != CAPS
            or job.get('runtime_archive_sha256') != ARCHIVE_SHA
            or job.get('runtime_binary_sha256') != BINARY_SHA
            or job.get('payload_source_prefix') != PAYLOAD_PREFIX
            or job.get('status') != 'ready' or job.get('certification_effect') != 'none'
            or job.get('execution_class') != 'native_task_control'
            or job.get('network_class') != 'account_authenticated_model'
            or job.get('resource_profile') != 'small'
            or job.get('resource_envelope') != {'worker_cpu': 2, 'worker_memory_mib': 4096}
            or job.get('timeout_seconds') != 600
            or job.get('argv') != ['python3', 'runner.py', 'execute', '--job', 'job.json']
            or job.get('exports') != ['result.json', 'audit-artifacts.tar.gz']
            or job.get('private_exports') != ['audit-artifacts.tar.gz']
            or job.get('max_export_bytes') != 8519680
            or job.get('limited_audit_mode') is not True
            or job.get('audit_deadline_utc') != DEADLINE
            or job.get('maximum_attempts') != 1
            or job.get('api_fallback') is not False
            or job.get('usage_reset') is not False
            or job.get('automatic_retries') != 0):
        raise ValueError('frozen_sol_envelope_mismatch')
    if job['task_id'] in HELD_TASKS or set(job.get('families', [])) & HELD_FAMILIES:
        raise ValueError('held_task_or_branch')
    if job.get('held_probe') is not False or job.get('auditor_sees_task_data') is not True:
        raise ValueError('audit_scope_required')
    images = job.get('images')
    if type(images) is not dict or set(images) != {'work', 'judge'}:
        raise ValueError('both_task_images_required')
    for role, image in images.items():
        expected = r'seededge/edgebench\.' + role + r'\.' + re.escape(job['task_id']) + r'@sha256:[a-f0-9]{64}'
        if type(image) is not str or not re.fullmatch(expected, image):
            raise ValueError('exact_task_image_required')
    if job.get('agent_image_role') not in images:
        raise ValueError('agent_image_role_required')
    if not 1 <= len(job.get('originals', [])) <= 64:
        raise ValueError('original_source_bindings_required')
    targets = set()
    for ref in job['originals']:
        if set(ref) != {'path', 'bytes', 'sha256'}:
            raise ValueError('source_ref_schema')
        relative(ref['path']); digest_value(ref['sha256'])
        if ref['path'] in targets or not ref['path'].startswith('originals/'):
            raise ValueError('source_target_scope')
        if type(ref['bytes']) is not int or not 0 <= ref['bytes'] <= 1048576:
            raise ValueError('source_size_limit')
        targets.add(ref['path'])
    for field in ('source_revision', 'dataset_revision'):
        if type(job.get(field)) is not str or not re.fullmatch(r'[a-f0-9]{40}', job[field]):
            raise ValueError('revision_required')
    inputs = job.get('inputs')
    if type(inputs) is not list or not inputs:
        raise ValueError('source_payload_required')
    by_target = {}
    for ref in inputs:
        if type(ref) is not dict or set(ref) != {'path', 'target', 'bytes', 'sha256'}:
            raise ValueError('source_payload_ref_schema')
        relative(ref['path']); relative(ref['target']); digest_value(ref['sha256'])
        if (not ref['path'].startswith(PAYLOAD_PREFIX) or ref['target'] in by_target
                or type(ref['bytes']) is not int or not 0 <= ref['bytes'] <= 1048576):
            raise ValueError('source_payload_scope')
        by_target[ref['target']] = ref
    if set(by_target) != PAYLOAD_FILES | targets:
        raise ValueError('source_payload_exact_allowlist')
    for ref in job['originals']:
        actual = by_target[ref['path']]
        if any(actual[key] != ref[key] for key in ('bytes', 'sha256')):
            raise ValueError('original_payload_binding_mismatch')
    if not job.get('hypothesis') or not job.get('quality_scope') or not job.get('acceptance'):
        raise ValueError('meaningful_audit_plan_required')
    if job.get('native_python') not in ('/usr/local/bin/python3', '/usr/bin/python3'):
        raise ValueError('fixed_native_interpreter_required')
    if type(job.get('evidence_admission')) is not dict or type(job.get('evidence_binding')) is not dict:
        raise ValueError('root_bound_evidence_protocol_required')
    if admission is not None:
        canonical(admission)
        if (admission.get('job_sha256') != sha(canonical(job))
                or admission.get('task_id') != job['task_id']
                or admission.get('operation_id') != OPERATION
                or admission.get('model_requested') != MODEL
                or admission.get('reasoning_effort_requested') != EFFORT
                or admission.get('review_status') != 'approved_source_and_task_scope'
                or admission.get('auth_scope') != 'root_selected_authorized_chatgpt_cache_only'
                or admission.get('compute_reserve_usd') != 0.1656
                or admission.get('held_probe') is not False):
            raise ValueError('root_admission_mismatch')
        name(admission.get('run_id')); name(admission.get('worker_id'))
        name(admission.get('attempt_id')); digest_value(admission.get('source_review_sha256'))
    return True


def codex_config():
    # Reuses the accepted isolated-container/account trust boundary. No local
    # config, provider replacement, API credential, plugin or resume is imported.
    return (f'model = "{MODEL}"\nmodel_reasoning_effort = "{EFFORT}"\n'
        'cli_auth_credentials_store = "file"\nforced_login_method = "chatgpt"\n'
        'approval_policy = "never"\nsandbox_mode = "danger-full-access"\n'
        'web_search = "disabled"\n'
        '[model_providers.openai]\nrequest_max_retries = 0\nstream_max_retries = 0\n'
        '[features]\nmulti_agent = false\n').encode()
