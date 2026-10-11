"""Pure actual-environment gates for one future reviewed VRPTW component run.

No filesystem, process, provider or credential operations occur in this module.
Reported metadata is a necessary gate; it does not attest benchmark science.
"""
import re

NATIVE_UID = 65534
NATIVE_GID = 65534
TMPFS_BYTES = 268435456
COMPILED_FILE_BYTES = 4194304
WRITE_PROBE_BYTES = 32
WRITE_PROBE_SHA256 = 'b4ce0c24655fbe87f8630df83aa3dfa853470737374bbc33f55b89615c9f383d'

def require(ok, label):
    if not ok:
        raise ValueError(label)

def exact(value, keys, label):
    require(type(value) is dict and set(value) == set(keys), label)

def integer(value, lo, hi, label):
    require(type(value) is int and lo <= value <= hi, label)

def observed(value, label):
    exact(value, ('status', 'value'), label)
    require(value['status'] == 'observed' and type(value['value']) is dict, label)
    return value['value']

def validate_work_metadata(value):
    exact(value, ('logical_path', 'probe_before_first_capture', 'euid', 'egid', 'observations'), 'environment_work_schema')
    require(value['logical_path'] == 'native_work_tmpfs' and value['probe_before_first_capture'] is True, 'environment_work_scope')
    integer(value['euid'], NATIVE_UID, NATIVE_UID, 'environment_native_uid')
    integer(value['egid'], NATIVE_GID, NATIVE_GID, 'environment_native_gid')
    observations = value['observations']
    exact(observations, ('directory_mode', 'vfs_flags', 'effective_access_predicate', 'exact_mount_flags', 'tmpfs_capacity'), 'environment_observation_inventory')
    mode = observed(observations['directory_mode'], 'environment_directory_observation')
    exact(mode, ('mode_bits', 'uid', 'gid', 'is_directory'), 'environment_directory_schema')
    integer(mode['mode_bits'], 0, 0o7777, 'environment_mode_type')
    integer(mode['uid'], NATIVE_UID, NATIVE_UID, 'environment_work_owner')
    integer(mode['gid'], NATIVE_GID, NATIVE_GID, 'environment_work_group')
    require(mode['is_directory'] is True and mode['mode_bits'] & 0o700 == 0o700 and mode['mode_bits'] & 0o6000 == 0, 'environment_owner_mode')
    # The actual effective mode is checked; equality to a requested CLI mode
    # is deliberately not assumed. Owner rwx suffices within this single-user
    # owned mount, while the existing requested sticky mode is preserved.
    access = observed(observations['effective_access_predicate'], 'environment_access_observation')
    exact(access, ('write', 'search'), 'environment_access_schema')
    require(access['write'] is True and access['search'] is True, 'environment_effective_access')
    vfs = observed(observations['vfs_flags'], 'environment_vfs_observation')
    exact(vfs, ('vfs_flags', 'readonly', 'noexec', 'noexec_flag_available'), 'environment_vfs_schema')
    integer(vfs['vfs_flags'], 0, 2147483647, 'environment_vfs_type')
    require(vfs['readonly'] is False and vfs['noexec'] is False and vfs['noexec_flag_available'] is True, 'environment_vfs_predicates')
    # Fixed Linux ST_RDONLY/NOSUID/NODEV/NOEXEC bits in the pinned Linux image.
    require(vfs['vfs_flags'] & 1 == 0 and vfs['vfs_flags'] & 8 == 0 and vfs['vfs_flags'] & 2 != 0 and vfs['vfs_flags'] & 4 != 0, 'environment_vfs_flags')
    mount = observed(observations['exact_mount_flags'], 'environment_mount_observation')
    exact(mount, ('filesystem', 'rw', 'ro', 'noexec', 'nosuid', 'nodev'), 'environment_mount_schema')
    require(mount['filesystem'] == 'tmpfs' and mount['rw'] is True and mount['ro'] is False and mount['noexec'] is False and mount['nosuid'] is True and mount['nodev'] is True, 'environment_mount_policy')
    capacity = observed(observations['tmpfs_capacity'], 'environment_capacity_observation')
    exact(capacity, ('capacity_bytes', 'available_bytes'), 'environment_capacity_schema')
    integer(capacity['capacity_bytes'], 1, TMPFS_BYTES, 'environment_capacity_bound')
    integer(capacity['available_bytes'], 1, capacity['capacity_bytes'], 'environment_available_bound')

def validate_write_probe(value):
    exact(value, ('logical_path', 'status', 'created', 'regular_single_link_owned', 'read_back_equal', 'removed', 'bytes', 'sha256', 'failure'), 'environment_write_probe_schema')
    require(value['logical_path'] == 'owned_preflight_write_probe' and value['status'] == 'validated' and value['created'] is True and value['regular_single_link_owned'] is True and value['read_back_equal'] is True and value['removed'] is True and value['failure'] is None, 'environment_write_probe_not_successful')
    integer(value['bytes'], WRITE_PROBE_BYTES, WRITE_PROBE_BYTES, 'environment_write_probe_bytes')
    require(value['sha256'] == WRITE_PROBE_SHA256, 'environment_write_probe_hash')

def validate_compiled_metadata(value, work_metadata, expected_sha256, expected_bytes):
    validate_work_metadata(work_metadata)
    exact(value, ('logical_path', 'is_regular', 'single_link', 'uid', 'gid', 'mode_bits', 'bytes', 'sha256', 'effective_execute'), 'environment_compiled_schema')
    require(value['logical_path'] == 'compiled_original_checker' and value['is_regular'] is True and value['single_link'] is True and value['effective_execute'] is True, 'environment_compiled_access')
    integer(value['uid'], NATIVE_UID, NATIVE_UID, 'environment_compiled_owner')
    integer(value['gid'], NATIVE_GID, NATIVE_GID, 'environment_compiled_group')
    integer(value['mode_bits'], 0, 0o7777, 'environment_compiled_mode_type')
    require(value['mode_bits'] & 0o100 != 0 and value['mode_bits'] & 0o6000 == 0, 'environment_compiled_mode')
    integer(value['bytes'], 1, COMPILED_FILE_BYTES, 'environment_compiled_size')
    integer(expected_bytes, 1, COMPILED_FILE_BYTES, 'environment_expected_compiled_size')
    require(type(expected_sha256) is str and re.fullmatch(r'[0-9a-f]{64}', expected_sha256) is not None and type(value['sha256']) is str and value['sha256'] == expected_sha256 and value['bytes'] == expected_bytes, 'environment_compiled_identity')

def validate_completed_preflight(native):
    require(type(native) is dict, 'environment_native_schema')
    value = native.get('environment_preflight')
    exact(value, ('work_status', 'write_probe', 'compiled_status', 'compiled_observation', 'postcompile_work_metadata'), 'environment_completed_preflight_schema')
    require(value['work_status'] == value['compiled_status'] == 'validated', 'environment_completed_preflight_status')
    validate_work_metadata(native.get('work_metadata_before_first_call'))
    validate_write_probe(value['write_probe'])
    validate_compiled_metadata(value['compiled_observation'], value['postcompile_work_metadata'], native.get('compiled_checker_sha256'), native.get('compiled_checker_bytes'))

# Additive transport checks accept failed predicates as observed diagnostics;
# only validate_completed_preflight can establish completed environment gates.
import hashlib
import json

SAFE_ERROR_CLASSES = {'PermissionError', 'FileExistsError', 'FileNotFoundError',
    'NotADirectoryError', 'IsADirectoryError', 'OSError', 'InterruptedError',
    'TimeoutError', 'KeyboardInterrupt', 'SystemExit', 'ValueError', 'RuntimeError',
    'TimeoutExpired', 'unlisted_exception'}

def receipt_failure(value, label):
    exact(value, ('exception_class', 'errno'), label)
    require(value['exception_class'] in SAFE_ERROR_CLASSES, label)
    require(value['errno'] is None or type(value['errno']) is int and 0 <= value['errno'] <= 4095, label)

def bounded_work_receipt(value):
    exact(value, ('logical_path', 'probe_before_first_capture', 'euid', 'egid', 'observations'), 'environment_receipt_work_schema')
    require(value['logical_path'] == 'native_work_tmpfs' and value['probe_before_first_capture'] is True, 'environment_receipt_work_scope')
    for field in ('euid', 'egid'):
        integer(value[field], 0, 4294967295, 'environment_receipt_native_id_type')
    observations = value['observations']
    exact(observations, ('directory_mode', 'vfs_flags', 'effective_access_predicate', 'exact_mount_flags', 'tmpfs_capacity'), 'environment_receipt_observation_inventory')
    for name, wrapper in observations.items():
        require(type(wrapper) is dict, 'environment_receipt_observation_type')
        if wrapper.get('status') == 'unavailable':
            exact(wrapper, ('status', 'error_class', 'errno'), 'environment_receipt_unavailable_schema')
            receipt_failure({'exception_class': wrapper['error_class'], 'errno': wrapper['errno']}, 'environment_receipt_unavailable_failure')
            continue
        row = observed(wrapper, 'environment_receipt_observed_schema')
        if name == 'directory_mode':
            exact(row, ('mode_bits', 'uid', 'gid', 'is_directory'), 'environment_receipt_directory_schema')
            integer(row['mode_bits'], 0, 0o7777, 'environment_receipt_mode_type')
            for field in ('uid', 'gid'):
                integer(row[field], 0, 4294967295, 'environment_receipt_owner_type')
            require(type(row['is_directory']) is bool, 'environment_receipt_directory_type')
        elif name == 'vfs_flags':
            exact(row, ('vfs_flags', 'readonly', 'noexec', 'noexec_flag_available'), 'environment_receipt_vfs_schema')
            integer(row['vfs_flags'], 0, 2147483647, 'environment_receipt_vfs_type')
            require(type(row['readonly']) is type(row['noexec_flag_available']) is bool and
                (type(row['noexec']) is bool if row['noexec_flag_available'] else row['noexec'] is None), 'environment_receipt_vfs_predicate_types')
        elif name == 'effective_access_predicate':
            exact(row, ('write', 'search'), 'environment_receipt_access_schema')
            require(type(row['write']) is type(row['search']) is bool, 'environment_receipt_access_types')
        elif name == 'exact_mount_flags':
            exact(row, ('filesystem', 'rw', 'ro', 'noexec', 'nosuid', 'nodev'), 'environment_receipt_mount_schema')
            require(type(row['filesystem']) is str and re.fullmatch(r'[A-Za-z0-9_.-]{1,32}', row['filesystem']) is not None, 'environment_receipt_filesystem_type')
            require(all(type(row[field]) is bool for field in ('rw', 'ro', 'noexec', 'nosuid', 'nodev')), 'environment_receipt_mount_types')
        elif name == 'tmpfs_capacity':
            exact(row, ('capacity_bytes', 'available_bytes'), 'environment_receipt_capacity_schema')
            # Failed oversized/non-tmpfs observations remain finite metadata;
            # the completed gate retains the exact256MiB admission limit.
            integer(row['capacity_bytes'], 0, 9223372036854775807, 'environment_receipt_capacity_type')
            integer(row['available_bytes'], 0, row['capacity_bytes'], 'environment_receipt_available_type')

def bounded_write_receipt(value):
    exact(value, ('logical_path', 'status', 'created', 'regular_single_link_owned', 'read_back_equal', 'removed', 'bytes', 'sha256', 'failure'), 'environment_receipt_write_schema')
    require(value['logical_path'] == 'owned_preflight_write_probe' and value['status'] in {'pending', 'failed', 'validated'}, 'environment_receipt_write_scope')
    require(all(type(value[field]) is bool for field in ('created', 'regular_single_link_owned', 'read_back_equal', 'removed')), 'environment_receipt_write_types')
    require(value['bytes'] is None or type(value['bytes']) is int and 0 <= value['bytes'] <= WRITE_PROBE_BYTES + 1, 'environment_receipt_write_bound')
    require(value['sha256'] is None or type(value['sha256']) is str and re.fullmatch(r'[0-9a-f]{64}', value['sha256']) is not None, 'environment_receipt_write_hash_type')
    if value['failure'] is not None:
        receipt_failure(value['failure'], 'environment_receipt_write_failure')
    if value['status'] == 'validated':
        validate_write_probe(value)

def bounded_compiled_receipt(value):
    exact(value, ('logical_path', 'is_regular', 'single_link', 'uid', 'gid', 'mode_bits', 'bytes', 'sha256', 'effective_execute'), 'environment_receipt_compiled_schema')
    require(value['logical_path'] == 'compiled_original_checker', 'environment_receipt_compiled_scope')
    require(all(type(value[field]) is bool for field in ('is_regular', 'single_link', 'effective_execute')), 'environment_receipt_compiled_types')
    for field in ('uid', 'gid'):
        integer(value[field], 0, 4294967295, 'environment_receipt_compiled_owner_type')
    integer(value['mode_bits'], 0, 0o7777, 'environment_receipt_compiled_mode_type')
    integer(value['bytes'], 1, COMPILED_FILE_BYTES, 'environment_receipt_compiled_size')
    require(type(value['sha256']) is str and re.fullmatch(r'[0-9a-f]{64}', value['sha256']) is not None, 'environment_receipt_compiled_hash_type')

def environment_public_receipt(public):
    present = [field for field in ('native', 'native_partial') if field in public]
    require(len(present) <= 1, 'environment_receipt_single_native_role')
    if not present:
        return {'status': 'not_available', 'native_role': None, 'native_calls': None,
                'work_status': None, 'compiled_status': None, 'certification_effect': 'none'}
    role = present[0]
    native = public[role]
    require(type(native) is dict, 'environment_receipt_native_type')
    integer(native.get('calls'), 0, 26, 'environment_receipt_calls_type')
    preflight = native.get('environment_preflight')
    exact(preflight, ('work_status', 'write_probe', 'compiled_status', 'compiled_observation', 'postcompile_work_metadata'), 'environment_receipt_preflight_schema')
    require(preflight['work_status'] in {'pending', 'validated'} and preflight['compiled_status'] in {'pending', 'validated'}, 'environment_receipt_preflight_status')
    bounded = {'work_metadata_before_first_call': native.get('work_metadata_before_first_call'), 'environment_preflight': preflight}
    require(len(json.dumps(bounded, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()) <= 16384, 'environment_receipt_nested_bound')
    for value in (native.get('work_metadata_before_first_call'), preflight['postcompile_work_metadata']):
        if value is not None:
            bounded_work_receipt(value)
    if preflight['write_probe'] is not None:
        bounded_write_receipt(preflight['write_probe'])
    if preflight['compiled_observation'] is not None:
        bounded_compiled_receipt(preflight['compiled_observation'])
    if preflight['work_status'] == 'validated':
        validate_work_metadata(native.get('work_metadata_before_first_call'))
        validate_write_probe(preflight['write_probe'])
    else:
        require(native['calls'] == 0 and preflight['compiled_status'] == 'pending' and
                preflight['compiled_observation'] is preflight['postcompile_work_metadata'] is None, 'environment_receipt_prework_zero_calls')
    if preflight['compiled_status'] == 'validated':
        require(preflight['work_status'] == 'validated' and native['calls'] >= 3, 'environment_receipt_compiled_prefix')
        validate_compiled_metadata(preflight['compiled_observation'], preflight['postcompile_work_metadata'], native.get('compiled_checker_sha256'), native.get('compiled_checker_bytes'))
    else:
        require(native['calls'] <= 3, 'environment_receipt_no_checker_before_compiled_gate')
    completed = native.get('status') == 'component_observations_complete_pending_independent_review'
    if completed:
        require(role == 'native' and native['calls'] == 26, 'environment_receipt_completed_role_calls')
        validate_completed_preflight(native)
    return {'status': 'validated_completed' if completed else 'bounded_partial', 'native_role': role,
            'native_calls': native['calls'], 'work_status': preflight['work_status'],
            'compiled_status': preflight['compiled_status'], 'certification_effect': 'none'}

CONTROLLER = 'vrptw-environment-correction-owned-close-sol-v4'
OPERATION = 'vrptw-environment-correction-sol-v4'
JOB_ID = 'vrptw-env-correction-71ad33683a514d40'
ENVELOPE_CANONICAL_SHA256 = 'c73d19646c72ebf14cbd3c309d27b40cec9a319e7b927c999a3822d230438faa'
def validate_contract(job):
    require(type(job) is dict, "environment_exact_envelope_object")
    raw = json.dumps(job, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    require(hashlib.sha256(raw).hexdigest() == ENVELOPE_CANONICAL_SHA256, "environment_frozen_full_envelope_required")
