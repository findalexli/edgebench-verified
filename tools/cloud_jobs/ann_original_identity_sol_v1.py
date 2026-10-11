"""Fixed-path ANN installed-source/runtime census; no original solver execution.

Run only in a root-admitted owned read-only image. Raw source, config, logs,
features and labels stay inside the container. This is a prerequisite check,
not original evaluator, nearest-neighbor corpus or benchmark performance evidence.
"""
from __future__ import annotations

import ast
import hashlib
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import resource
import signal
import stat
import sys

SOURCE_CAP = 65536
TOTAL_SOURCE_CAP = 1048576
SUMMARY_CAP = 32768
DATA = Path('/home/workspace/ann-benchmarks/data/sift-128-euclidean.hdf5')
OUTPUT = Path('/audit-output/native-summary.json')
DEPS = {'numpy': 'numpy', 'h5py': 'h5py', 'faiss': 'faiss-cpu',
        'docker': 'docker', 'psutil': 'psutil', 'colors': 'ansicolors', 'yaml': 'PyYAML'}
VERSION_RE = re.compile(r'[0-9A-Za-z.+_-]{1,80}\Z')


def bounded_read(path, cap=SOURCE_CAP):
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('linked_source')
    with path.open('rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > cap:
            raise ValueError('source_cap_or_type')
        raw = stream.read(cap + 1)
        after = os.fstat(stream.fileno())
    if len(raw) != info.st_size or (info.st_dev, info.st_ino, info.st_size,
            info.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError('source_changed')
    return raw


def summarize_source(raw, kind):
    """Only fixed structural flags; never execute acquired source/config."""
    out = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
    if kind == 'identity':
        return out
    try:
        text = raw.decode('utf-8')
    except UnicodeError:
        out['text_status'] = 'invalid_utf8'
        return out
    out['text_status'] = 'utf8'
    if kind == 'config':
        out['line_count'] = text.count('\n') + int(bool(text) and not text.endswith('\n'))
        out['custom_constructor_literal_present'] = bool(re.search(r'^\s*constructor:\s*Custom\s*$', text, re.M))
        out['custom_module_literal_present'] = bool(re.search(
            r'^\s*module:\s*ann_benchmarks\.algorithms\.custom\s*$', text, re.M))
        out['config_parsed_or_imported'] = False
        return out
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        out['syntax_status'] = 'invalid'
        return out
    nodes = list(ast.walk(tree))
    if len(nodes) > 4096:
        out['syntax_status'] = 'node_cap'
        return out
    classes = [x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == 'Custom']
    methods = {x.name for c in classes for x in c.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))}
    imports = []
    for node in nodes:
        if isinstance(node, ast.Import):
            imports.extend(x.name.split('.')[0] for x in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append((node.module or '').split('.')[0])
    known = {'numpy', 'faiss', 'ann_benchmarks', 'time', 'os', 'sys', 'h5py', 'scipy', 'sklearn'}
    out.update(syntax_status='valid', ast_node_count=len(nodes), custom_class_count=len(classes),
               fit_defined='fit' in methods, query_defined='query' in methods,
               known_imports={k: k in imports for k in sorted(known)},
               other_import_count=sum(x not in known for x in imports), acquired_code_executed=False)
    return out


def checkpoint(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode() + b'\n'
    if len(raw) > SUMMARY_CAP:
        raise ValueError('summary_cap')
    temporary = OUTPUT.with_suffix('.tmp')
    with temporary.open('wb') as stream:
        os.chmod(temporary, 0o600)
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, OUTPUT)


def failure_class(exc):
    allowed = {'ImportError', 'ModuleNotFoundError', 'MemoryError', 'OSError', 'ValueError', 'TimeoutError'}
    return type(exc).__name__ if type(exc).__name__ in allowed else 'other_error'


def main():
    resource.setrlimit(resource.RLIMIT_AS, (512 << 20,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (120,) * 2)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    def expired(_signum, _frame):
        raise TimeoutError('native_deadline')
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(180)
    value = {'schema_version': 1, 'complete': False, 'phase': 'startup', 'reason': None,
             'failure_class': None, 'source_records': {}, 'dependencies': {}, 'data_stat': {},
             'faiss_authored_control': None, 'raw_source_exported': False, 'raw_data_exported': False,
             'corpus_body_read': False, 'original_evaluator_executed': False,
             'original_solver_executed': False, 'private_custom_code_exported': False,
             'performance_measured': False, 'acquired_custom_code_executed': False}
    checkpoint(value)
    try:
        plan = json.loads(bounded_read(Path('/audit/identity-plan.json')))
        value['image_role'] = plan['image_role']
        value['python_version'] = '.'.join(map(str, sys.version_info[:3]))
        value['phase'] = 'source_census'
        total = 0
        for role, record in plan['source_paths'].items():
            path = Path(record['path'])
            try:
                raw = bounded_read(path)
                total += len(raw)
                if total > TOTAL_SOURCE_CAP:
                    raise ValueError('source_total_cap')
                row = {'status': 'read', **summarize_source(raw, record['kind'])}
                if 'expected_sha256' in record:
                    row['retained_source_matches'] = row['sha256'] == record['expected_sha256']
            except FileNotFoundError:
                row = {'status': 'missing'}
            except ValueError as exc:
                row = {'status': 'unsupported', 'reason': str(exc)}
            value['source_records'][role] = row
        value['source_bytes_read'] = total
        checkpoint(value)
        value['phase'] = 'data_stat'
        try:
            info = DATA.lstat()
            value['data_stat'] = {'present': True, 'regular': stat.S_ISREG(info.st_mode),
                                  'symlink': stat.S_ISLNK(info.st_mode), 'bytes': info.st_size,
                                  'prior_accepted_size_matches': info.st_size == 525128288,
                                  'body_read': False, 'sha256_measured': False}
        except FileNotFoundError:
            value['data_stat'] = {'present': False, 'body_read': False, 'sha256_measured': False}
        checkpoint(value)
        value['phase'] = 'dependencies'
        loaded = {}
        for module_name, distribution in DEPS.items():
            try:
                module = importlib.import_module(module_name)
                version = importlib.metadata.version(distribution)
                if not VERSION_RE.fullmatch(version):
                    raise ValueError('version_format')
                value['dependencies'][module_name] = {'imported': True, 'version': version}
                loaded[module_name] = module
            except Exception as exc:
                value['dependencies'][module_name] = {'imported': False, 'failure_class': failure_class(exc)}
            checkpoint(value)
        value['phase'] = 'authored_faiss_workload'
        if 'numpy' in loaded and 'faiss' in loaded:
            try:
                np, faiss = loaded['numpy'], loaded['faiss']
                faiss.omp_set_num_threads(1)
                index = faiss.IndexFlatL2(2)
                index.add(np.asarray([[0, 0], [3, 4], [6, 8]], dtype=np.float32))
                d, ids = index.search(np.asarray([[1, 0]], dtype=np.float32), 2)
                good = ids.tolist() == [[0, 1]] and d.tolist() == [[1.0, 20.0]]
                # An index omitting the nearer second point must fail the same fixed distance expectation.
                wrong = faiss.IndexFlatL2(2)
                wrong.add(np.asarray([[0, 0], [6, 8]], dtype=np.float32))
                wrong_d, _ = wrong.search(np.asarray([[1, 0]], dtype=np.float32), 2)
                wrong_rejected = wrong_d.tolist() == [[1.0, 89.0]] and wrong_d.tolist() != [[1.0, 20.0]]
                value['faiss_authored_control'] = {'started': True, 'completed': True,
                    'correct_ids_and_squared_distances': bool(good), 'farther_negative_rejected': bool(wrong_rejected),
                    'train_points': 3, 'queries': 1, 'dimension': 2, 'threads': 1,
                    'actual_dataset_used': False, 'performance_measured': False}
            except Exception as exc:
                value['faiss_authored_control'] = {'started': True, 'completed': False, 'failure_class': failure_class(exc)}
        else:
            value['faiss_authored_control'] = {'started': False, 'completed': False, 'reason': 'dependency_unavailable'}
        value.update(complete=True, phase='completed')
        checkpoint(value)
        return 0
    except Exception as exc:
        value['failure_class'] = failure_class(exc)
        reason = str(exc) if isinstance(exc, (ValueError, TimeoutError)) else None
        value['reason'] = reason if reason in {'linked_source', 'source_cap_or_type', 'source_changed',
            'source_total_cap', 'summary_cap', 'native_deadline', 'version_format'} else 'bounded_census_failed'
        checkpoint(value)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
