"""One declared public call prepares two fresh built-image CLI submissions."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import stat
import sys

ROOT = Path('/home/workspace/complex_job_scheduling')
DIAGNOSTIC_CHECKPOINT = {'phase': 'not_entered', 'public_calls': 0}

def need(value, reason):
    if not value:
        DIAGNOSTIC_CHECKPOINT['authored_guard_reason'] = reason
        raise ValueError(reason)

def read(path, cap=1048576):
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= cap, 'fixture_regular_cap')
    raw = path.read_bytes()
    after = path.lstat()
    need(len(raw) == before.st_size and (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns) ==
         (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns), 'fixture_stable_complete')
    return raw

def run(fixtures):
    DIAGNOSTIC_CHECKPOINT['phase'] = 'exact_source_guards'
    for row in fixtures['source_guards']:
        raw = read(ROOT / row['relative'])
        need(len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'], 'fixture_source_identity')
    binary = ROOT / 'cost_complex_cy.cpython-311-x86_64-linux-gnu.so'
    binary_raw = read(binary)
    need(hashlib.sha256(binary_raw).hexdigest() == fixtures['public_binary_sha256'], 'actual_public_binary_identity')
    original = read(ROOT / 'tests/test_final_result.py')
    candidate = fixtures['candidate_checker'].encode()
    need(hashlib.sha256(original).hexdigest() == fixtures['original_checker_sha256'] and
         hashlib.sha256(candidate).hexdigest() == fixtures['candidate_checker_sha256'] and
         candidate.replace(fixtures['final_helper_sha256'].encode(), fixtures['old_helper_sha256'].encode(), 1) == original,
         'frozen_one_literal_candidate')
    permutation = [1 + (997*i + 113) % 1000 for i in range(1000)]
    need(permutation == fixtures['permutation'] and sorted(permutation) == list(range(1,1001)), 'fresh_affine_membership')
    permutation_sha = hashlib.sha256(json.dumps(permutation,separators=(',',':')).encode()).hexdigest()
    need(permutation_sha not in fixtures['prior_permutation_sha256'], 'fresh_not_prior_fixture')
    DIAGNOSTIC_CHECKPOINT['phase'] = 'public_black_box_call'
    spec = importlib.util.spec_from_file_location('cost_complex_cy', binary)
    need(spec is not None and spec.loader is not None, 'public_extension_loader')
    module = importlib.util.module_from_spec(spec)
    sys.modules['cost_complex_cy'] = module
    spec.loader.exec_module(module)
    DIAGNOSTIC_CHECKPOINT['public_calls'] += 1
    cost = module.cost_complex_with_builtin_data(permutation, m=1000, seed=1)
    need(type(cost) is float and math.isfinite(cost) and cost > 0, 'finite_positive_public_response')
    submissions=[]
    for kind,reported in [('legal',cost),('wrong-cost',cost*1.013)]:
        need(math.isfinite(reported), 'fixed_submission_kind')
        if kind == 'wrong-cost':
            need(not math.isclose(cost, reported, rel_tol=1e-10, abs_tol=1e-3), 'independent_wrong_cost_distance')
        raw = ('final_pai=' + ','.join(map(str,permutation)) + '\nfinal_cost=' + repr(reported) + '\nfinal_num=1\n').encode()
        need(len(raw) <= 8192, 'final_result_cap')
        filename=kind+'.txt'
        with Path('/audit-output',filename).open('xb') as output:output.write(raw)
        submissions.append({'kind':kind,'reported_cost':reported,'filename':filename,'bytes':len(raw),
                            'sha256':hashlib.sha256(raw).hexdigest()})
    DIAGNOSTIC_CHECKPOINT['phase'] = 'fixture_ready'
    return [{'component':'fresh_public_api_paired_fixture','public_calls':1,
        'public_cost':cost,'submitted_final_num':1,'submissions':submissions,
        'independent_expected_score':100*min(1,200690260.6677975/cost)**3,
        'permutation_sha256':permutation_sha,
        'checker_sha256':fixtures['checker_sha256'],
        'scope':'one declared public black-box call; no search/private data/pytest/full-task claim'}]
