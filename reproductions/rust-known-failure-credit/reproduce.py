#!/usr/bin/env python3
"""Replay six Rust scorer component fixtures with explicitly simulated Cargo."""
import argparse
import ast
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time
import types
from typing import Optional

SOURCE_SHA256 = 'd725dd934a01e40948267131d8ae91a075b4217d8012b41468cc9b38bb782b35'
SOURCE_BYTES = 25616
CASES = [
    ('all_pass', True, ()),
    ('only_known_failure', True, (0,)),
    ('ordinary_failure_known_passes', True, (1,)),
    ('two_ordinary_failures_known_passes', True, (1, 2)),
    ('known_and_ordinary_failure', True, (0, 1)),
    ('ordinary_failure_known_absent', False, (1,)),
]


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def load_original(source):
    require(source.is_file() and source.stat().st_size == SOURCE_BYTES,
            'Expected the exact 25,616-byte original score.py.')
    body = source.read_bytes()
    require(len(body) == SOURCE_BYTES and hashlib.sha256(body).hexdigest() == SOURCE_SHA256,
            'Source SHA-256 mismatch; no scorer code was executed.')
    names = {'LAYER_CONFIG', 'CRATE_TO_PACKAGE', 'EXPECTED_TOTALS', 'KNOWN_FAILURES',
             'KNOWN_CRASH_CRATES', 'KNOWN_CRASH_SIGNATURES', 'HIDDEN_TESTS_BY_CRATE',
             'CrateResult', 'is_known_crash', 'run_crate_test', 'compute_score'}
    selected = []
    found = set()
    for node in ast.parse(body).body:
        key = node.name if isinstance(node, (ast.FunctionDef, ast.ClassDef)) else (
            node.targets[0].id if isinstance(node, ast.Assign) and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name) else None)
        if key in names:
            require(key not in found, 'Duplicate selected source name.')
            found.add(key)
            selected.append(node)
    require(found == names, 'Required original source definitions were not found.')
    env = {'dataclass': dataclasses.dataclass, 'Optional': Optional, 'os': os, 'time': time}
    exec(compile(ast.Module(body=selected, type_ignores=[]), '<pinned-original-score.py>', 'exec'), env)
    return env


def replay(env):
    rows = []
    for label, known_present, failed_indices in CASES:
        # Only the exemption name is taken from the original public constant.
        # Every other test identity and transcript is an authored fixture.
        known_name = env['KNOWN_FAILURES']['cas-pty'][0]
        test_names = [known_name if known_present else 'fixture::ordinary_zero'] + [
            'fixture::ordinary_{}'.format(i) for i in range(1, 11)]
        failed = set(failed_indices)
        listing = '\n'.join(name + ': test' for name in test_names) + '\n'
        output = '\n'.join('test {} ... {}'.format(name, 'FAILED' if i in failed else 'ok')
                           for i, name in enumerate(test_names))
        output += '\ntest result: {}. {} passed; {} failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s\n'.format(
            'FAILED' if failed else 'ok', 11-len(failed), len(failed))
        calls = []

        def simulated_cargo(argv, **kwargs):
            calls.append(argv)
            if len(calls) == 1:
                require(argv == ['cargo', 'test', '--frozen', '-p', 'cas-pty', '--', '--list'],
                        'Unexpected simulated discovery command.')
                return subprocess.CompletedProcess(argv, 0, listing, '')
            require(len(calls) == 2 and argv == [
                'cargo', 'test', '--frozen', '-p', 'cas-pty', '--', '--test-threads=4'],
                'Unexpected simulated test command.')
            return subprocess.CompletedProcess(argv, 101 if failed else 0, output, '')

        # This replacement is installed before any original function is called.
        # subprocess.run is never exposed to the original component.
        env['subprocess'] = types.SimpleNamespace(run=simulated_cargo,
                                                TimeoutExpired=subprocess.TimeoutExpired)
        actual = env['run_crate_test']('authored-fixture-unused-directory', 'cas-pty', 1800)
        require(len(calls) == 2, 'Expected exactly two simulated Cargo responses.')
        expected_failed = len(failed) - int(known_present and 0 in failed)
        expected = dataclasses.replace(actual, passed=11-expected_failed, failed=expected_failed,
                                       status='TEST_FAIL' if expected_failed else 'PASS')
        companions = [env['CrateResult'](crate, env['CRATE_TO_PACKAGE'][crate], 'PASS', total, 0,
                       total, total, 0, 0, 0, None, 0.0, None)
                      for crate, total in env['EXPECTED_TOTALS'].items() if crate != 'cas-pty']
        actual_score, _ = env['compute_score'](companions + [actual], env['LAYER_CONFIG'])
        expected_score, _ = env['compute_score'](companions + [expected], env['LAYER_CONFIG'])
        rows.append({'label': label, 'original_helper_calls': 1, 'original_score_calls': 2,
                     'simulated_cargo_calls': len(calls), 'raw_fixture_passed': 11-len(failed),
                     'raw_fixture_failed': len(failed), 'expected_passed': expected.passed,
                     'expected_failed': expected.failed, 'actual_passed': actual.passed,
                     'actual_failed': actual.failed, 'actual_status': actual.status,
                     'actual_public_passed': actual.public_passed,
                     'actual_public_failed': actual.public_failed,
                     'actual_score_for_synthetic_complete_result_set': actual_score,
                     'expected_score_for_synthetic_complete_result_set': expected_score,
                     'agrees': (actual.passed, actual.failed) == (expected.passed, expected.failed)})
    require([row['agrees'] for row in rows] == [True, True, False, False, True, True],
            'Observed outcomes differ from the confirmed six-case result.')
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('score_py', type=Path, help='Exact original scorer; checked by SHA-256.')
    parser.add_argument('output_dir', type=Path, help='Fresh output directory; must not exist.')
    args = parser.parse_args()
    require(hasattr(os, 'sched_setaffinity'), 'This bounded replay requires Linux CPU affinity.')
    resource.setrlimit(resource.RLIMIT_AS, (128*1024*1024,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
    resource.setrlimit(resource.RLIMIT_FSIZE, (65536, 65536))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    signal.alarm(18)
    require(not args.output_dir.exists(), 'Output directory already exists; choose a fresh one.')
    env = load_original(args.score_py)
    rows = replay(env)
    result = {'task_id': 'rust_multicrate_reconstruction', 'source_sha256': SOURCE_SHA256,
              'source_bytes': SOURCE_BYTES, 'python_version': sys.version.split()[0], 'cases': rows,
              'original_helper_calls': 6, 'original_score_calls': 12,
              'simulated_cargo_calls': 12, 'real_cargo_calls': 0, 'native_calls': 0,
              'disagreement_count': sum(not row['agrees'] for row in rows),
              'scope': 'Unmodified AST-selected original Python components with authored simulated Cargo responses; not native Rust, full CLI, corpus incidence or historical score impact.',
              'resource_limits': {'address_space_bytes': 134217728, 'logical_cpus': 1,
                                  'cpu_seconds': 5, 'wall_alarm_seconds': 18,
                                  'output_file_bytes': 65536}}
    encoded = (json.dumps(result, indent=2) + '\n').encode()
    require(len(encoded) <= 65536, 'Result exceeded its output bound.')
    args.output_dir.mkdir(parents=True, exist_ok=False)
    with (args.output_dir / 'result.json').open('xb') as handle:
        handle.write(encoded)
    print('Reproduced 6 cases: 2 outcome mismatches, 4 matching countercontrols. Cargo was simulated.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, SyntaxError) as exc:
        print('Replay failed: {}'.format(exc), file=sys.stderr)
        raise SystemExit(1)
